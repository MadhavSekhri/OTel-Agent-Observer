"""Validated opt-in metadata for OpenTelemetry GenAI spans.

Semantic-convention attribute names are drawn from published GenAI conventions.
Only non-sensitive model/provider identifiers and numeric usage are permitted.
"""
import re

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
MAX_TOKENS = 10**12


def _name(label, value):
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a safe, nonempty identifier (max 128 chars)")
    return value


def _tokens(label, value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_TOKENS:
        raise ValueError(f"{label} must be a nonnegative bounded integer")
    return value


def genai_attributes(*, operation, model, provider, input_tokens=None,
                     output_tokens=None):
    """Build a minimal set of non-content GenAI attributes for explicit spans.

    No prompt, completion, agent argument, endpoint URL or user identity is
    accepted. Usage counters may be omitted when unavailable.
    """
    attrs = {
        "gen_ai.operation.name": _name("operation", operation),
        "gen_ai.request.model": _name("model", model),
        "gen_ai.provider.name": _name("provider", provider),
    }
    if input_tokens is not None:
        attrs["gen_ai.usage.input_tokens"] = _tokens("input_tokens", input_tokens)
    if output_tokens is not None:
        attrs["gen_ai.usage.output_tokens"] = _tokens("output_tokens", output_tokens)
    return attrs
