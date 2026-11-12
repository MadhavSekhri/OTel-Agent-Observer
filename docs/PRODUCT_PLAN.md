# OTel Agent Observer — Product & Engineering RFC

## Mission and reviewer test
A small, privacy-first instrumentation layer for Python agent workflows, compatible with standard OpenTelemetry SDKs. Reviewer demo: nested synchronous and async functions emit meaningful spans and safe numeric usage metrics to an in-memory/exporter test, without prompts, credentials or exception text.

## Wide view
Existing APM covers network requests and infrastructure; generative AI applications add tool transitions, retries, token cost and agent handoffs. Compatibility with OpenTelemetry semantic conventions matters more than inventing a proprietary dashboard. A useful product makes safe defaults effortless and preserves application behavior even if instrumentation fails.

## Users and workflows
Audience: Python agent developers and platform observability engineers. Minimal SDK to annotate work stages, propagate context, add explicitly safe attributes, and configure provider SDK/exporter in app. No hosted storage and no secret credentials needed.

## Architecture
Instrumented app call -> bounded allowlisted metadata -> active tracing context via OTel API when installed -> configured SDK/exporter; optional local sanitized event sink. Separate adapters for framework-specific agents; keep core provider-neutral and with no required dependencies. Use current, versioned OTel GenAI conventions for model/provider/operation/tokens when they stabilize, and test compatibility with known versions.

## Safe defaults and non-goals
Never record prompts, completions, requests, responses, raw tool arguments or exception messages by default. This is not an infallible DLP filter or OTel collector. No external IO unless a caller explicitly sets an exporter or sink. Unexpected sinks should not override application return values or original exceptions.

## Security and correctness principles
- Privacy by construction: explicit allowlisting of safe numeric/string metadata; no arbitrary nested content.
- Cardinality and data budgets: maximum count, key/name lengths, list depth and string lengths.
- Real context propagation: nested spans and async jobs with fake and real SDK tests.
- Fail-open observation for sink exceptions; never allow log/export diagnostics to expose secrets.
- Correctness: no double-end spans, maintain context during exceptions; do not mask application failures.
- Configurable usage metrics only, no content opt-in until retention/privacy guidance is audited.

## Roadmap
**P0 (initial PR):** bounded safe metadata, sink error isolation, redaction edge cases, error-propagation tests.
**P1:** documented GenAI semantic-convention adapter with version tests and SDK exporter example.
**P2:** async stress and context tests, low-overhead benchmarks, policy-controlled metric sampling.
**P3:** selectively maintained adapters for agent frameworks with semver, interoperability and signed releases.

## Release quality gate
Unit and integration tests with optional OTel on Python 3.10/3.12, lint and types, benchmarks with no synthetic secret leakage, clear privacy policy, no network default, and example exporting a successful nested trace to an in-memory SDK.

## Adoption proof
Another genuinely independent project can instrument agents in minutes, use a standard collector, and confirm no sensitive payload is exported by default. Seek upstream compatibility feedback before claiming CNCF affiliation or maintainer status.

## Integration and scope
Use in PolicyTrace ingest, Agent Audit Kit evaluations and OSS Readiness scanning, entirely optionally. No runtime package interdependency. Do not turn on prompt capture just for a demo.

## Open design questions
Which exact OpenTelemetry GenAI semantic-convention version? Are attributes provider-specific? How to represent failures without exception messages? What sampling and retention constraints matter? Track and verify against upstream specifications before implementation.
