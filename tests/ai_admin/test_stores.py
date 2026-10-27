"""Unit tests for stores (ContextStore, CandidateCache, SnapshotStore, AuditLog)."""

import time
import pytest
from ai_admin.audit_log import AuditLog
from ai_admin.candidate_cache import CandidateCache
from ai_admin.context_store import ContextStore
from ai_admin.snapshot_store import SnapshotStore


def test_context_store_target_item_and_turns():
    ctx = ContextStore(ttl_seconds=60, max_history_turns=3)
    ctx.set_selected_item(user_id=1, chat_id=1, item_id="item_abc", title="Inception")

    item_id, title = ctx.get_selected_item(1, 1)
    assert item_id == "item_abc"
    assert title == "Inception"

    # Context isolation between users
    item_id2, title2 = ctx.get_selected_item(2, 2)
    assert item_id2 is None

    # History capping
    ctx.add_turn(1, 1, "user", "turn 1")
    ctx.add_turn(1, 1, "assistant", "turn 2")
    ctx.add_turn(1, 1, "user", "turn 3")
    ctx.add_turn(1, 1, "assistant", "turn 4")

    history = ctx.get_history(1, 1)
    assert len(history) == 3
    assert history[0]["content"] == "turn 2"
    assert history[-1]["content"] == "turn 4"


def test_candidate_cache_opaque_handles():
    cache = CandidateCache(ttl_seconds=60, max_entries=5)
    real_data = {"provider": "tmdb", "id": 550, "url": "https://image.tmdb.org/t/p/original/test.jpg"}

    cand_id = cache.register_candidate(real_data)
    assert cand_id.startswith("cand_")
    assert "tmdb.org" not in cand_id

    resolved = cache.resolve_candidate(cand_id)
    assert resolved == real_data

    # Invalid / unregistered handle
    assert cache.resolve_candidate("cand_nonexistent") is None


def test_snapshot_store_and_latest(tmp_path):
    store = SnapshotStore(str(tmp_path))
    metadata = {"field": "overview", "previous": "An old plot summary"}
    blob = b"\xff\xd8\xff\xe0\x00\x10JFIF"

    snap_id = store.save_snapshot(
        snapshot_id="snap_123",
        action_id="act_456",
        user_id=1001,
        chat_id=1001,
        item_id="item_789",
        snapshot_type="artwork",
        metadata=metadata,
        binary_blob=blob,
    )
    assert snap_id == "snap_123"

    loaded_meta, loaded_blob = store.get_snapshot("snap_123")
    assert loaded_meta == metadata
    assert loaded_blob == blob

    # Latest snapshot query for undo
    latest_id, latest_meta, latest_blob = store.get_latest_snapshot(1001, 1001)
    assert latest_id == "snap_123"
    assert latest_meta == metadata
