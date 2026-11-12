# OTel Agent Observer — Threat Model

Assets: user prompts, credentials, PII, application error/return semantics, span integrity and downstream collector privacy.
Trust boundary: application-supplied attributes -> privacy filter -> third-party sink / OTel exporter.

| Threat | Failure mode | Control |
|---|---|---|
| Unknown sensitive attributes | accidental secret in telemetry | default-deny risky keys, explicit allowable typed attributes |
| Exception capture | secret in exception messages or stack | disable automatic OTel exception recording; emit error class only |
| Sink failure | telemetry error hides original exception | suppress sink failures while retaining original app outcome |
| Cardinality explosion | unbounded attributes, expensive export | finite key count, key/value/depth budgets |
| Nested/cyclic data | infinite traversal or crash | depth and cycle detection with fallback redaction |
| Cross-trace context loss | incorrect correlation | nested and concurrent async tests |
| Unstable semantic conventions | invalid downstream attributes | pinned mapping and compatibility test |
| Untrusted content logging | prompt/response exported by default | metadata-only default; no raw content auto-capture |

Do not claim comprehensive privacy/PII detection; a caller-installed collector may add other instrumentation outside this library.
