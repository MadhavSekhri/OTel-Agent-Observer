import unittest
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
