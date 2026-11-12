# Telemetry API: privacy and failure policy

The observer is opt-in, best-effort instrumentation for local Python processes. Installing OpenTelemetry API alone does not configure an exporter; applications must explicitly configure a tracer provider and export pipeline.

## Defaults
- No prompt, response, argument, secret or exception message capture.
- Numeric token counters may be recorded if explicitly passed.
- Safe attributes: model, provider, operation, framework, tool_name, attempt, retry_count, tokens, input_tokens, output_tokens, total_tokens, cached_tokens and known gen_ai.* model/provider/operation/usage keys.
- Any unknown top-level attribute key: reported as [REDACTED]; this is not a guarantee that a misleadingly named field cannot contain private information.
- Maximum 32 top-level attributes, string values truncated to 256 chars, sanitizer depth at most 6.
- The instrumentation swallows sink/exporter failures, keeping the original application error/return. Capture delivery failures in a separately controlled sink if needed.
- OTel automatic exception recording and status capture are disabled to avoid exporting exception messages.

## Supported conventions
Do not infer compatibility with every unstable OpenTelemetry GenAI semantic convention yet. Future versions will pin and document supported semantic conventions and integration tests.

## Test
`python -m unittest discover -s tests -v`

## Security limitations
PII in an allowlisted `model` or `operation` string may still appear; callers must keep those fields structured and non-sensitive. Telemetry pipelines installed elsewhere in the application can capture other attributes independently. No request/network export occurs unless the application explicitly configures it.
