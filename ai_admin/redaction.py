"""Secret scrubbing and redaction utilities for AI Admin."""

import re
import logging
from typing import Any, Dict, List, Set, Union

# Matches Telegram Bot Tokens: 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
_TELEGRAM_TOKEN_RE = re.compile(r"\b\d{8,10}:[a-zA-Z0-9_-]{35}\b")

# Matches Bearer tokens and Authorization headers
_BEARER_TOKEN_RE = re.compile(r"(?i)\b(bearer\s+)([a-zA-Z0-9_\-\.]{12,})")

# Matches sensitive query parameters or URL params: api_key=..., token=...
_URL_SECRET_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|access[_-]?token)=([a-zA-Z0-9_\-\.]{6,})")

# Generic patterns for high-entropy secret assignments: API_KEY = "...", etc.
_ASSIGN_SECRET_RE = re.compile(r"(?i)(api[_-]?key|bot[_-]?token|api[_-]?hash|password|secret|database[_-]?url)\s*[:=]\s*['\"]?([^'\"\s,]{6,})['\"]?")

_EXTRA_SECRET_STRINGS: Set[str] = set()


def register_secret_string(secret: str) -> None:
    """Register a runtime secret string to be scrubbed verbatim."""
    if secret and len(secret.strip()) >= 5:
        _EXTRA_SECRET_STRINGS.add(secret.strip())


def redact_text(text: str) -> str:
    """Scrub known tokens, authorization headers, and secrets from string."""
    if not isinstance(text, str):
        return text

    redacted = text
    # 1. Registered dynamic secrets
    for sec in _EXTRA_SECRET_STRINGS:
        if sec in redacted:
            redacted = redacted.replace(sec, "[REDACTED]")

    # 2. Telegram Bot tokens
    redacted = _TELEGRAM_TOKEN_RE.sub("[REDACTED_BOT_TOKEN]", redacted)

    # 3. Bearer tokens
    redacted = _BEARER_TOKEN_RE.sub(r"\1[REDACTED_BEARER_TOKEN]", redacted)

    # 4. URL secrets
    redacted = _URL_SECRET_RE.sub(r"\1=[REDACTED]", redacted)

    # 5. Key-value assignments
    redacted = _ASSIGN_SECRET_RE.sub(r"\1=[REDACTED]", redacted)

    return redacted


def redact_data(data: Any) -> Any:
    """Recursively scrub secrets from strings, dictionaries, lists, and tuples."""
    if isinstance(data, str):
        return redact_text(data)
    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(term in k_lower for term in ("key", "token", "secret", "password", "hash", "auth")):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_data(v)
        return cleaned
    if isinstance(data, list):
        return [redact_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(redact_data(item) for item in data)
    return data


class RedactingFilter(logging.Filter):
    """Logging filter that scrubs sensitive secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_data(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(redact_data(arg) for arg in record.args)
        return True
