"""Integration tests use a real in-memory OpenTelemetry SDK exporter."""
import asyncio
import unittest

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from otel_agent_observer.genai import genai_attributes
from otel_agent_observer.observer import AgentObserver


class OTelSDKIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.provider = TracerProvider()
        self.exporter = InMemorySpanExporter()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.events = []
        self.observer = AgentObserver(self.events.append, enable_otel=False)
        self.observer._tracer = self.provider.get_tracer("otel_agent_observer.tests")

    def tearDown(self):
        self.provider.shutdown()

    def test_nested_spans_propagate_context(self):
        with self.observer.genai_span(
            operation="chat", provider="openai", model="test-model",
            input_tokens=21, output_tokens=9,
        ):
            with self.observer.span("tool.search", {"tool_name": "search"}):
                pass
        spans = self.exporter.get_finished_spans()
        self.assertEqual(len(spans), 2)
        child, parent = spans
        self.assertEqual(child.parent.span_id, parent.context.span_id)
        self.assertEqual(child.context.trace_id, parent.context.trace_id)
        self.assertEqual(parent.attributes["gen_ai.operation.name"], "chat")
        self.assertEqual(parent.attributes["gen_ai.usage.input_tokens"], 21)
        self.assertEqual(parent.attributes["gen_ai.usage.output_tokens"], 9)

    def test_exception_text_not_exported(self):
        with self.assertRaisesRegex(ValueError, "PRIVATE_SYNTHETIC_SECRET"):
            with self.observer.genai_span(
                operation="chat", provider="test", model="small",
            ):
                raise ValueError("PRIVATE_SYNTHETIC_SECRET")
        spans = self.exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].events, ())
        self.assertNotIn("PRIVATE_SYNTHETIC_SECRET", str(spans[0].attributes))
        self.assertEqual(spans[0].attributes["agent.exception_type"], "ValueError")
        self.assertEqual(self.events[0]["status"], "error")

    def test_async_instrumentation_with_sdk(self):
        @self.observer.traced("agent.async", {"operation": "demo"})
        async def run():
            with self.observer.genai_span(
                operation="chat", provider="test", model="local",
            ):
                return 42
        self.assertEqual(asyncio.run(run()), 42)
        spans = self.exporter.get_finished_spans()
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0].parent.span_id, spans[1].context.span_id)

    def test_reject_sensitive_identifiers_and_bad_counters(self):
        with self.assertRaises(ValueError):
            genai_attributes(operation="chat", provider="test",
                             model="user@email.test")
        with self.assertRaises(ValueError):
            genai_attributes(operation="chat", provider="test",
                             model="demo", input_tokens=-1)
        with self.assertRaises(ValueError):
            genai_attributes(operation="chat", provider="test",
                             model="demo", output_tokens=True)
        valid = genai_attributes(operation="chat", provider="test", model="demo")
        self.assertNotIn("gen_ai.usage.input_tokens", valid)


if __name__ == "__main__":
    unittest.main()
