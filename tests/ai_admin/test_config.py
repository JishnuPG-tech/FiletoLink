"""Unit tests for ai_admin/config.py."""

import os
import pytest
from ai_admin.config import AIAdminConfig


def test_config_fail_closed_defaults(monkeypatch):
    """Ensure default config is completely disabled and fail-closed."""
    for key in list(os.environ.keys()):
        if key.startswith("AI_") or key in ("OWNER_ID", "OMNIROUTE_API_KEY", "OMNIROUTE_API_URL"):
            monkeypatch.delenv(key, raising=False)

    cfg = AIAdminConfig.from_env()
    assert cfg.enabled is False
    assert cfg.mutations_enabled is False
    assert len(cfg.admin_telegram_ids) == 0
    assert len(cfg.allowed_chat_ids) == 0
    assert cfg.confirm_ttl_seconds == 120
    assert cfg.context_ttl_seconds == 900
    assert cfg.max_bulk_items == 50


def test_config_empty_admins_disables_enabled_mode(monkeypatch):
    """If AI_ENABLED=true but no admin IDs are provided, config disables AI fail-closed."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.delenv("AI_ADMIN_TELEGRAM_IDS", raising=False)
    monkeypatch.delenv("OWNER_ID", raising=False)

    cfg = AIAdminConfig.from_env()
    assert cfg.enabled is False  # Automatically disabled fail-closed
    assert cfg.is_valid is False
    assert "deny-all" in cfg.validation_error


def test_config_valid_environment(monkeypatch):
    """Verify parsing of valid configuration with numeric admin IDs."""
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_MUTATIONS_ENABLED", "true")
    monkeypatch.setenv("AI_ADMIN_TELEGRAM_IDS", "12345, 67890")
    monkeypatch.setenv("AI_ALLOWED_CHAT_IDS", "-100123")
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_CONFIRM_TTL_SECONDS", "300")

    cfg = AIAdminConfig.from_env()
    assert cfg.enabled is True
    assert cfg.mutations_enabled is True
    assert cfg.admin_telegram_ids == {12345, 67890}
    assert cfg.allowed_chat_ids == {-100123}
    assert cfg.ai_model == "gpt-4o-mini"
    assert cfg.confirm_ttl_seconds == 300
    assert cfg.is_valid is True
