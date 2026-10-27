"""Unit tests for ai_admin/permissions.py (authorization safety controls)."""

import pytest
from ai_admin.config import AIAdminConfig
from ai_admin.permissions import PermissionChecker


@pytest.fixture
def base_config():
    return AIAdminConfig(
        enabled=True,
        mutations_enabled=False,
        admin_telegram_ids={1001, 1002},
        allowed_chat_ids=set(),  # default: private chats of admins only
    )


def test_authorized_admin_private_chat(base_config):
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(user_id=1001, chat_id=1001)
    assert ok is True
    assert reason == "authorized"


def test_rejection_unauthorized_user(base_config):
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(user_id=9999, chat_id=9999)
    assert ok is False
    assert "unauthorized user" in reason


def test_rejection_channel_post(base_config):
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(
        user_id=1001, chat_id=-100123, is_channel=True
    )
    assert ok is False
    assert "channel posts" in reason


def test_rejection_anonymous_admin(base_config):
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(
        user_id=1001, chat_id=-100123, is_anonymous_admin=True
    )
    assert ok is False
    assert "anonymous admin" in reason


def test_rejection_group_chat_under_default_private_policy(base_config):
    checker = PermissionChecker(base_config)
    # Admin user, but sent in a group chat (chat_id != user_id)
    ok, reason = checker.check_authorization(user_id=1001, chat_id=-100555)
    assert ok is False
    assert "restricted to private" in reason


def test_explicit_group_allowlist(base_config):
    base_config.allowed_chat_ids = {-100555}
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(user_id=1001, chat_id=-100555)
    assert ok is True

    # Unauthorized group
    ok2, reason2 = checker.check_authorization(user_id=1001, chat_id=-100999)
    assert ok2 is False
    assert "not permitted in this chat" in reason2


def test_master_switch_disabled(base_config):
    base_config.enabled = False
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_authorization(user_id=1001, chat_id=1001)
    assert ok is False
    assert "disabled" in reason


def test_mutations_allowed_check(base_config):
    checker = PermissionChecker(base_config)
    ok, reason = checker.check_mutation_allowed()
    assert ok is False
    assert "read-only mode" in reason

    base_config.mutations_enabled = True
    ok2, reason2 = checker.check_mutation_allowed()
    assert ok2 is True
