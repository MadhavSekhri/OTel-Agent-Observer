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

Or run `otel-agent-demo` to emit a simulated JSONL event.

The observer does not record prompts or responses by default. It redacts keys matching common credential names and token-like substrings. These heuristics **do not guarantee privacy**. An application must configure a trustworthy sink/exporter. Without an installed OpenTelemetry SDK/exporter, traces are not exported.

## Tests

    python -m unittest discover -s tests -v

## Community

See CONTRIBUTING.md and SECURITY.md. Apache OpenTelemetry is a separate upstream project; no CNCF endorsement or maintainer status is implied.

## License

MIT; see LICENSE.
