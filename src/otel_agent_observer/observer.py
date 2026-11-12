"""Agent step events with optional OpenTelemetry API integration."""
from __future__ import annotations

import json
import re
import time
import inspect
from functools import wraps
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from typing import Callable

SENSITIVE_KEYS = (
    "password", "passwd", "api_key", "apikey", "token",
    "secret", "authorization", "cookie", "credential",
    "prompt", "response", "completion", "message", "payload",
    "body", "input", "output", "error", "exception", "traceback", "content",
)
TOKEN_SHAPE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{16})\b")


def redact(value, key="", depth=0):
    """Best-effort redaction; not a guarantee or general-purpose DLP filter."""
    if key.lower() in ("tokens", "input_tokens", "output_tokens", "total_tokens") and isinstance(value, (int, float)):
        return value
    if any(word in key.lower() for word in SENSITIVE_KEYS):
        return "[REDACTED]"
    if depth > 8:
        return "[DEPTH_LIMIT]"
    if isinstance(value, dict):
        return {str(k): redact(v, str(k), depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, key, depth + 1) for v in value]
    if isinstance(value, str):
        return TOKEN_SHAPE.sub("[REDACTED]", value)[:2000]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return "[UNSUPPORTED_VALUE]"


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
        """Instrument a step without recording exception messages or arguments.

        OpenTelemetry exceptions are deliberately NOT auto-recorded because
        exception messages and stack traces may contain prompts or credentials.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("span name must be nonempty string")
        if attributes is not None and not isinstance(attributes, dict):
            raise ValueError("attributes must be a mapping or None")
        safe = redact(attributes or {})
        started = time.perf_counter()
        stamp = datetime.now(timezone.utc).isoformat()
        exception_type = None
        # Use active scope so child spans inherit the trace context. Disable
        # OTel's default record_exception and status-on-exception behavior.
        scope = (
            self._tracer.start_as_current_span(
                name, record_exception=False, set_status_on_exception=False
            ) if self._tracer is not None else nullcontext()
        )
        with scope as otel_span:
            if otel_span is not None:
                for key, value in safe.items():
                    if isinstance(value, (bool, int, float, str)):
                        otel_span.set_attribute(key, value)
            try:
                yield
            except Exception as exc:
                exception_type = type(exc).__name__
                if otel_span is not None:
                    otel_span.set_attribute("agent.exception_type", exception_type)
                raise
            finally:
                event = {
                    "name": name,
                    "started_at": stamp,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "status": "error" if exception_type else "ok",
                    "attributes": safe,
                }
                if exception_type:
                    event["exception_type"] = exception_type
                self.sink(event)

    def traced(self, name: str, attributes: dict | None = None):
        """Decorate synchronous or asynchronous functions (never captures arguments)."""
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
    """Build a JSON-lines sink for one event per line."""
    def sink(event):
        stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
    return sink
