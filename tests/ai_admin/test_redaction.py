"""Unit tests for ai_admin/redaction.py (secret scrubbing)."""

import logging
from ai_admin.redaction import (
    RedactingFilter,
    redact_data,
    redact_text,
    register_secret_string,
)


def test_telegram_bot_token_redaction():
    text = "Started bot with token 123456789:ABCDefghIJklmnOPqrstUVwxyz123456789 and listening."
    cleaned = redact_text(text)
    assert "123456789:ABC" not in cleaned
    assert "[REDACTED_BOT_TOKEN]" in cleaned


def test_bearer_token_redaction():
    text = "Headers: {'Authorization': 'Bearer sk-abcdef1234567890abcdef1234567890'}"
    cleaned = redact_text(text)
    assert "sk-abcdef" not in cleaned
    assert "[REDACTED_BEARER_TOKEN]" in cleaned


def test_url_secret_redaction():
    url = "https://example.com/api?api_key=secret_api_key_123456&mode=fast"
    cleaned = redact_text(url)
    assert "secret_api_key_123456" not in cleaned
    assert "api_key=[REDACTED]" in cleaned


def test_registered_dynamic_secret():
    secret_key = "super_secret_dynamic_omniroute_token_999"
    register_secret_string(secret_key)
    log_msg = f"Failed to contact proxy using {secret_key} at endpoint"
    cleaned = redact_text(log_msg)
    assert secret_key not in cleaned
    assert "[REDACTED]" in cleaned


def test_redact_dict_structures():
    data = {
        "user_id": 1234,
        "api_key": "top_secret_token",
        "bot_token": "987654321:abcdefg",
        "nested": {"password": "mypassword123", "normal": "hello"},
    }
    cleaned = redact_data(data)
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["bot_token"] == "[REDACTED]"
    assert cleaned["nested"]["password"] == "[REDACTED]"
    assert cleaned["nested"]["normal"] == "hello"


def test_logging_filter_integration():
    logger = logging.getLogger("TestRedactionLogger")
    logger.setLevel(logging.INFO)
    records = []

    class CapturingHandler(logging.Handler):
        def emit(self, record):
            records.append(self.format(record))

    handler = CapturingHandler()
    handler.addFilter(RedactingFilter())
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    test_token = "999888777:ABCDefghIJklmnOPqrstUVwxyz123456789"
    logger.info(f"Connecting to Telegram with token {test_token}")

    assert len(records) == 1
    assert test_token not in records[0]
    assert "[REDACTED_BOT_TOKEN]" in records[0]
