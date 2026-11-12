"""Pure GenAI metadata validation does not require OpenTelemetry SDK."""
import unittest
from otel_agent_observer.genai import genai_attributes


class GenAIUnitTests(unittest.TestCase):
    def test_model_fields_and_usage(self):
        result = genai_attributes(operation="chat", provider="openai",
                                  model="gpt-4o-mini", input_tokens=5)
        self.assertEqual(result["gen_ai.request.model"], "gpt-4o-mini")
        self.assertEqual(result["gen_ai.usage.input_tokens"], 5)
        self.assertNotIn("gen_ai.usage.output_tokens", result)

    def test_reject_secrets_and_unsafe_metadata(self):
        for identifier in ("name with spaces", "foo@example.com", "",
                           "\nESCAPE", "x" * 129):
            with self.subTest(value=identifier), self.assertRaises(ValueError):
                genai_attributes(operation="chat", provider="test",
                                 model=identifier)
        for count in (-1, True, 1.2, 10**12 + 1):
            with self.subTest(count=count), self.assertRaises(ValueError):
                genai_attributes(operation="chat", provider="test",
                                 model="sample", input_tokens=count)


if __name__ == "__main__":
    unittest.main()
