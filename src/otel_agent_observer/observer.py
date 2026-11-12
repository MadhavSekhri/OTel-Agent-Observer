"""Privacy-conscious, fail-open instrumentation for agent steps.

Never captures arguments, prompt contents or exception messages by default.
Exporters/sinks are controlled explicitly by the calling application.
"""
from __future__ import annotations

import inspect
import json
import math
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from itertools import islice
from typing import Callable

MAX_ATTRIBUTE_COUNT = 32
MAX_ATTRIBUTE_STRING = 256
MAX_ATTRIBUTE_DEPTH = 6

SENSITIVE_KEYS = (
    "password", "passwd", "api_key", "apikey", "token",
    "secret", "authorization", "cookie", "credential",
    "prompt", "response", "completion", "message", "payload",
    "body", "input", "output", "error", "exception", "traceback", "content",
)
NUMERIC_USAGE_KEYS = frozenset({
    "tokens", "input_tokens", "output_tokens", "total_tokens",
    "cached_tokens", "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens",
})
SAFE_ATTRIBUTE_KEYS = frozenset({
    "model", "provider", "operation", "framework", "tool_name",
    "attempt", "retry_count", "input_tokens", "output_tokens",
    "total_tokens", "cached_tokens", "tokens",
    "gen_ai.operation.name", "gen_ai.provider.name", "gen_ai.request.model",
    "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens",
})
TOKEN_SHAPE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|(?:AKIA|ASIA)[A-Z0-9]{16})\b")


def redact(value, key="", depth=0):
    """Best-effort bounded sanitizer; not a comprehensive data-loss prevention filter."""
    if depth > MAX_ATTRIBUTE_DEPTH:
        return "[DEPTH_LIMIT]"
    normalized = str(key).lower()
    if normalized in NUMERIC_USAGE_KEYS and isinstance(value, (int, float)) and not isinstance(value, bool):
        return value if math.isfinite(value) and value >= 0 else "[REDACTED]"
    if any(word in normalized for word in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        result = {}
        for k, v in islice(value.items(), MAX_ATTRIBUTE_COUNT):
            if not isinstance(k, str):
                continue
            result[k[:64]] = redact(v, k, depth + 1)
        return result
    if isinstance(value, (tuple, list)):
        return [redact(v, key, depth + 1) for v in islice(value, MAX_ATTRIBUTE_COUNT)]
    if isinstance(value, str):
        return TOKEN_SHAPE.sub("[REDACTED]", value)[:MAX_ATTRIBUTE_STRING]
    if isinstance(value, bool) or value is None or isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else "[REDACTED]"
    return "[UNSUPPORTED_VALUE]"


def sanitize_attributes(attributes):
    """Allowlist telemetry-safe attribute names, denying arbitrary payload fields."""
    if attributes is None:
        return {}
    if not isinstance(attributes, dict):
        raise ValueError("attributes must be a mapping or None")
    safe = {}
    for name, value in islice(attributes.items(), MAX_ATTRIBUTE_COUNT):
        if not isinstance(name, str) or not name or len(name) > 128:
            continue
        if name in SAFE_ATTRIBUTE_KEYS:
            sanitized = redact(value, name)
            # OpenTelemetry attributes are scalars; avoid passing opaque objects.
            safe[name] = sanitized if isinstance(sanitized, (str, int, float, bool)) else "[REDACTED]"
        else:
            safe[name] = "[REDACTED]"
    return safe


class AgentObserver:
    def __init__(self, sink: Callable[[dict], None] | None = None, enable_otel=True):
        self.sink = sink if sink is not None else lambda event: None
        self._tracer = None
        if enable_otel:
            try:
                from opentelemetry import trace
                self._tracer = trace.get_tracer("otel_agent_observer", "0.1.0")
            except ImportError:
                pass

    @contextmanager
    def span(self, name: str, attributes: dict | None = None):
        """Time a step without observing its inputs, outputs or exception details.

        Telemetry is best-effort; no sink/exporter exception can change the
        application's return value or original exception.
        """
        if not isinstance(name, str) or not name or len(name) > 128:
            raise ValueError("span name must be a nonempty string of <=128 chars")
        safe = sanitize_attributes(attributes)
        started = time.perf_counter()
        stamp = datetime.now(timezone.utc).isoformat()
        exception_type = None
        scope = None
        otel_span = None
        if self._tracer is not None:
            try:
                scope = self._tracer.start_as_current_span(
                    name, record_exception=False, set_status_on_exception=False
                )
                otel_span = scope.__enter__()
            except Exception:
                scope = None
                otel_span = None
        if otel_span is not None:
            for key, value in safe.items():
                try:
                    otel_span.set_attribute(key, value)
                except Exception:
                    # Exporter faults must never interrupt business logic.
                    pass
        try:
            yield
        except BaseException as exc:
            exception_type = type(exc).__name__
            if otel_span is not None:
                try:
                    otel_span.set_attribute("agent.exception_type", exception_type)
                except Exception:
                    pass
            raise
        finally:
            # Deliberately do not pass the original exception to the OTel scope:
            # downstream SDKs may otherwise auto-capture message/stack text.
            if scope is not None:
                try:
                    scope.__exit__(None, None, None)
                except Exception:
                    pass
            event = {
                "name": name,
                "started_at": stamp,
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                "status": "error" if exception_type else "ok",
                "attributes": safe,
            }
            if exception_type:
                event["exception_type"] = exception_type
            try:
                self.sink(event)
            except Exception:
                # Observability is intentionally fail-open. Consumers can wrap
                # their sinks to monitor exporter delivery failures separately.
                pass

    def genai_span(self, *, operation, model, provider, input_tokens=None,
                   output_tokens=None):
        """Start an opt-in metadata-only GenAI operation span.

        Returns a context manager. Usage counts are caller-supplied; this
        instrumentation never reads prompts or model API responses.
        """
        from .genai import genai_attributes

        attributes = genai_attributes(
            operation=operation, model=model, provider=provider,
            input_tokens=input_tokens, output_tokens=output_tokens,
        )
        return self.span("gen_ai." + operation, attributes)

    def traced(self, name: str, attributes: dict | None = None):
        """Wrap a synchronous or asynchronous function without capturing its arguments."""
        def decorate(func):
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    with self.span(name, attributes):
                        return await func(*args, **kwargs)
                return async_wrapper

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.span(name, attributes):
                    return func(*args, **kwargs)
            return wrapper
        return decorate


def jsonl_sink(stream):
    """Build a JSON-lines writer; invalid non-finite values are never emitted."""
    def sink(event):
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
    return sink
