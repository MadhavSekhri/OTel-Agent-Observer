# Real OpenTelemetry SDK integration — P1

The package supports an optional OpenTelemetry SDK. The core package
remains dependency-free. Install with python -m pip install -e '.[otel-test]'.

Configure an OTel tracer provider in the application, or inject a tracer
into AgentObserver._tracer for isolated integration tests. The project does
not configure exporters or transmit traces by default.

Example with the real SDK:

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, InMemorySpanExporter
    from otel_agent_observer.observer import AgentObserver
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    observer = AgentObserver()
    with observer.genai_span(operation='chat', model='demo', provider='test',
                             input_tokens=5, output_tokens=3):
        pass
    spans = exporter.get_finished_spans()

All model/provider/operation identifiers must be bounded, safe strings with
no spaces, email syntax or control characters; token usage must be a
nonnegative bounded integer. This validation is not a comprehensive PII
filter: callers must never put sensitive identifiers into allowed fields.

The observed semantic keys currently include gen_ai.operation.name,
gen_ai.provider.name, gen_ai.request.model, gen_ai.usage.input_tokens and
gen_ai.usage.output_tokens. Exact OTel conventions can evolve; this helper
is minimal and not a statement of full semantic-convention compliance.

SDK tests verify nested context correlation, async instrumentation,
metadata values, and that exception messages are not exported as OTel events.

