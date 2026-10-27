"""Unit tests for ai_admin/confirmation_store.py."""

import os
import time
import pytest
from ai_admin.confirmation_store import ConfirmationStore, compute_action_hash


@pytest.fixture
def store(tmp_path):
    db_file = tmp_path / "test_confirmations.sqlite"
    return ConfirmationStore(str(db_file))


def test_create_and_consume_confirmation(store):
    params = {"item_id": "item123", "candidate_id": "cand_abc"}
    token_id, action_hash = store.create_confirmation(
        user_id=1001,
        chat_id=1001,
        tool_name="set_item_image",
        params=params,
        ttl_seconds=60,
    )
    assert len(token_id) == 32
    assert len(action_hash) == 64

    # Consume successfully
    ok, payload, reason = store.consume_confirmation(
        confirmation_id=token_id,
        user_id=1001,
        chat_id=1001,
        expected_action_hash=action_hash,
    )
    assert ok is True
    assert payload["tool"] == "set_item_image"
    assert payload["params"]["item_id"] == "item123"
    assert reason == "consumed_successfully"


def test_replay_rejected(store):
    params = {"item_id": "item123"}
    token_id, action_hash = store.create_confirmation(
        user_id=1001, chat_id=1001, tool_name="test_tool", params=params
    )

    # First consume
    ok1, _, _ = store.consume_confirmation(token_id, 1001, 1001, action_hash)
    assert ok1 is True

    # Replay attempt
    ok2, payload2, reason2 = store.consume_confirmation(token_id, 1001, 1001, action_hash)
    assert ok2 is False
    assert payload2 is None
    assert "replay rejected" in reason2


def test_wrong_user_rejected(store):
    token_id, action_hash = store.create_confirmation(
        user_id=1001, chat_id=1001, tool_name="test_tool", params={"a": 1}
    )

    # Different user attempts to click
    ok, _, reason = store.consume_confirmation(token_id, user_id=9999, chat_id=1001)
    assert ok is False
    assert "Authorization mismatch" in reason


def test_wrong_chat_rejected(store):
    token_id, action_hash = store.create_confirmation(
        user_id=1001, chat_id=1001, tool_name="test_tool", params={"a": 1}
    )

    # Same user, but forwarded / clicked from different chat
    ok, _, reason = store.consume_confirmation(token_id, user_id=1001, chat_id=5555)
    assert ok is False
    assert "Authorization mismatch" in reason


def test_expired_token_rejected(store):
    # 0 TTL -> already expired
    token_id, action_hash = store.create_confirmation(
        user_id=1001, chat_id=1001, tool_name="test_tool", params={"a": 1}, ttl_seconds=-5
    )

    ok, _, reason = store.consume_confirmation(token_id, 1001, 1001, action_hash)
    assert ok is False
    assert "expired" in reason


def test_altered_action_hash_rejected(store):
    params = {"item_id": "item123"}
    token_id, original_hash = store.create_confirmation(
        user_id=1001, chat_id=1001, tool_name="test_tool", params=params
    )

    altered_hash = compute_action_hash("test_tool", {"item_id": "item999"})
    ok, _, reason = store.consume_confirmation(
        confirmation_id=token_id,
        user_id=1001,
        chat_id=1001,
        expected_action_hash=altered_hash,
    )
    assert ok is False
    assert "Action payload has changed" in reason
