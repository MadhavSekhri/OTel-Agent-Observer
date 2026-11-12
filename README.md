# OTel Agent Observer

Privacy-minded events for instrumenting LLM/agent operations, with optional OpenTelemetry API spans.

**Status:** early prototype, not a security boundary, OTLP exporter, or production observability service. Designed to be extended by open-source contributors.

## Install

    python -m pip install -e .

Optionally install the OpenTelemetry API/SDK/exporter separately and configure them in your application.

## Example

```python
from otel_agent_observer.observer import AgentObserver

observer = AgentObserver(sink=print)
with observer.span("llm.request", {"model": "local-demo", "api_key": "private"}):
    pass
```

To instrument regular or asynchronous functions without capturing their inputs:

```python
observer = AgentObserver(sink=print, enable_otel=False)

@observer.traced("calculate")
def calculate(x):
    return x * 2
```

For OpenTelemetry exporters, install and configure the OpenTelemetry SDK in the application. The observer uses an active span context when available. **By default it does not auto-record exception messages or stack traces**; it only records exception class names. Avoid attaching sensitive information to custom span attributes.

Or run `otel-agent-demo` to emit a simulated JSONL event.

The observer does not record prompts or responses by default. It uses an explicit set of safe attribute names (for example model, provider, operation and numeric token counts). Unknown attribute keys are redacted by default. String values and metadata counts are bounded. This is intentionally not a complete PII/DLP solution. These heuristics **do not guarantee privacy**. An application must configure a trustworthy sink/exporter. Without an installed OpenTelemetry SDK/exporter, traces are not exported.

## Real OpenTelemetry SDK integration (P1)

Install the optional SDK integration for local tests:

    python -m pip install -e '.[otel-test]'

Then configure a TracerProvider and span processor in your application.
Call observer.genai_span(operation='chat', model='local', provider='test',
input_tokens=12, output_tokens=8) to record opt-in metadata only.

Integration tests use a real OpenTelemetry in-memory exporter and assert
nested context propagation, sync/async behavior and absence of exception text.
The library does not configure an OTLP endpoint or send any data itself.
See [SDK guide](docs/OTEL_SDK_INTEGRATION.md).

## Tests

    python -m unittest discover -s tests -v

## Community

See CONTRIBUTING.md and SECURITY.md. Apache OpenTelemetry is a separate upstream project; no CNCF endorsement or maintainer status is implied.

## License

MIT; see LICENSE.

## Architecture and security

This is an actively developed prototype, not a certification or completed production service. Review the [product design and acceptance gates](docs/PRODUCT_PLAN.md), [threat model](docs/THREAT_MODEL.md), and [implementation contract](docs/TELEMETRY_POLICY.md) before depending on it. Changes are proposed through draft pull requests with automated tests and security-focused code review.
