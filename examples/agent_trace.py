"""Run a synthetic agent workflow with an in-memory OpenTelemetry exporter."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from otel_agent_observer.observer import AgentObserver


def main():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    observer = AgentObserver()
    tracer = provider.get_tracer(__name__)

    try:
        with tracer.start_as_current_span("agent.request") as request:
            with observer.genai_span(
                operation="chat",
                model="fixture-model",
                provider="local-demo",
                input_tokens=12,
                output_tokens=4,
            ):
                pass

        parent_context = request.get_span_context()
        child, root = exporter.get_finished_spans()
        assert root.context == parent_context
        assert child.parent.span_id == parent_context.span_id
        assert child.context.trace_id == parent_context.trace_id
        assert child.attributes["gen_ai.usage.input_tokens"] == 12
        assert child.attributes["gen_ai.usage.output_tokens"] == 4
        print(f"{root.name} -> {child.name}")
    finally:
        provider.shutdown()


if __name__ == "__main__":
    main()
