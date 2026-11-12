import unittest
import asyncio
from otel_agent_observer.observer import AgentObserver, redact


class ObserverTests(unittest.TestCase):
    def test_redact_sensitive_fields(self):
        r = redact({
            "api_key": "abc",
            "nested": {"authorization": "Bearer secret", "model": "demo"},
            "content": "sk-abcdefghijklmnopqrstuvwxyz",
        })
        self.assertEqual(r["api_key"], "[REDACTED]")
        self.assertEqual(r["nested"]["authorization"], "[REDACTED]")
        self.assertNotIn("sk-abc", r["content"])

    def test_numeric_token_counters_are_preserved(self):
        self.assertEqual(
            redact({"input_tokens": 12, "token": "secret"}),
            {"input_tokens": 12, "token": "[REDACTED]"},
        )

    def test_success_event(self):
        events = []
        obs = AgentObserver(events.append, enable_otel=False)
        with obs.span("a", {"model": "demo", "token": "sensitive"}):
            pass
        self.assertEqual(events[0]["status"], "ok")
        self.assertEqual(events[0]["attributes"]["token"], "[REDACTED]")
        self.assertGreaterEqual(events[0]["duration_ms"], 0)

    def test_prompt_and_payload_redacted(self):
        fields = {
            "system_prompt": "This contains private instructions",
            "response_body": "A secret answer",
            "nested": {"request_payload": "private"},
            "input_tokens": 42,
        }
        value = redact(fields)
        self.assertEqual(value["system_prompt"], "[REDACTED]")
        self.assertEqual(value["response_body"], "[REDACTED]")
        self.assertEqual(value["nested"]["request_payload"], "[REDACTED]")
        self.assertEqual(value["input_tokens"], 42)

    def test_sync_and_async_decorators(self):
        events = []
        observer = AgentObserver(events.append, enable_otel=False)

        @observer.traced("sync", {"api_key": "private"})
        def add(a, b):
            return a + b

        @observer.traced("async")
        async def multiply(a, b):
            return a * b

        self.assertEqual(add(2, 3), 5)
        self.assertEqual(asyncio.run(multiply(3, 4)), 12)
        self.assertEqual([event["name"] for event in events], ["sync", "async"])
        self.assertEqual(events[0]["attributes"]["api_key"], "[REDACTED]")

    def test_otel_scope_disables_exception_recording(self):
        events = []
        settings = []
        class FakeSpan:
            def set_attribute(self, key, value):
                settings.append((key, value))
        class Scope:
            def __enter__(self):
                return FakeSpan()
            def __exit__(self, *_):
                return False
        class FakeTracer:
            def start_as_current_span(self, name, **kwargs):
                settings.append(("options", kwargs))
                return Scope()
        observer = AgentObserver(events.append, enable_otel=False)
        observer._tracer = FakeTracer()
        with self.assertRaisesRegex(ValueError, "secret"):
            with observer.span("step"):
                raise ValueError("secret")
        opts = next(value for key, value in settings if key == "options")
        self.assertFalse(opts["record_exception"])
        self.assertFalse(opts["set_status_on_exception"])
        self.assertNotIn("secret", str(events))
        self.assertIn(("agent.exception_type", "ValueError"), settings)

    def test_failure_event_and_raise(self):
        events = []
        obs = AgentObserver(events.append, enable_otel=False)
        with self.assertRaises(ValueError):
            with obs.span("f"):
                raise ValueError("do not emit this text")
        self.assertEqual(events[0]["exception_type"], "ValueError")
        self.assertEqual(events[0]["status"], "error")
        self.assertNotIn("do not emit this text", str(events))


if __name__ == "__main__":
    unittest.main()
