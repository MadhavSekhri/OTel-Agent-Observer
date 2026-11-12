# Ecosystem review and positioning

Review date: 2026-11-12.

## Existing ecosystem
- OpenLLMetry: https://github.com/traceloop/openllmetry — extensive OpenTelemetry-based GenAI instrumentation across providers, frameworks and vector databases.
- Arize Phoenix: https://github.com/Arize-ai/phoenix — OTel/OpenInference-based tracing, datasets, experiments and evaluations.
- OpenTelemetry GenAI semantic conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/ — interoperability vocabulary; check stability before pinning implementation.

## Strategic choice
Do **not** build a hosted APM or a new dashboard. Our differentiated role is a very small, *explicitly opt-in* metadata-only Python instrumentation helper that does not capture prompts, outputs or exception text by default and stays out of application control flow even when instrumentation fails.

## Reviewer acceptance demo
A nested sync/async operation is visible in an OTel in-memory exporter with the expected operation and model metadata, token counts and valid trace context. Inject a failing sink and a business exception: the application must raise its original error, with no secret string in telemetry.

## Quality and integration direction
Use the OpenTelemetry API/SDK as the authoritative core, not proprietary spans. Avoid auto-instrumentation or sampling 'innovation' until evidence shows an unsolved niche. For actual upstream impact, propose specific improvements to OTel or established SDK projects with test evidence rather than attempting to manufacture a CNCF maintainer role.

## Limits
No official OpenTelemetry/CNCF endorsement; no claim of complete redaction. Multiple other SDKs may add telemetry elsewhere in the application.
