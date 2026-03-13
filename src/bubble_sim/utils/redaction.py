from __future__ import annotations

import re

# Patterns for secrets and identifiers
_API_KEY_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{20,}|" r"[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,})",
)
_EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)
_AUTH_HEADER_PATTERN = re.compile(
    r"(Bearer\s+)[a-zA-Z0-9._\-]+",
)

REDACTED = "[REDACTED]"


def redact_secrets(text: str) -> str:
    """Strips API keys, auth tokens, and email-like strings."""
    text = _API_KEY_PATTERN.sub(REDACTED, text)
    text = _EMAIL_PATTERN.sub(REDACTED, text)
    text = _AUTH_HEADER_PATTERN.sub(rf"\1{REDACTED}", text)
    return text


def redact_trace_row(row: dict) -> dict:
    """Applies redaction to string values in a trace dict."""
    out = {}
    for key, val in row.items():
        if isinstance(val, str):
            out[key] = redact_secrets(val)
        else:
            out[key] = val
    return out
