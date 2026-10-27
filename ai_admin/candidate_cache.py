"""Opaque candidate ID cache for images, subtitles, and provider matches with user/chat isolation."""

import secrets
import time
from typing import Any, Dict, Optional


class CandidateCache:
    def __init__(self, ttl_seconds: int = 900, max_entries: int = 200):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        # candidate_id -> {"data": {...}, "user_id": int, "chat_id": int, "operation": str, "created_at": float}
        self._cache: Dict[str, Dict[str, Any]] = {}

    def register_candidate(
        self,
        candidate_data: Dict[str, Any],
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        operation: str = "generic",
    ) -> str:
        """Register candidate payload and issue an opaque server-side handle.

        Binds candidate to user_id, chat_id, and operation type.
        Returns candidate_id formatted as cand_<hex32>.
        """
        self._prune_if_needed()
        cand_id = f"cand_{secrets.token_hex(16)}"
        self._cache[cand_id] = {
            "data": dict(candidate_data),
            "user_id": user_id,
            "chat_id": chat_id,
            "operation": operation,
            "created_at": time.time(),
        }
        return cand_id

    def resolve_candidate(
        self,
        candidate_id: str,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        expected_operation: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve original candidate payload given opaque candidate ID.

        Enforces user isolation, chat isolation, and operation binding.
        Fails closed (returns None) on expiry, unknown handle, or isolation mismatch.
        """
        if not candidate_id:
            return None
        entry = self._cache.get(candidate_id.strip())
        if not entry:
            return None
        now = time.time()
        if now - entry["created_at"] > self.ttl_seconds:
            del self._cache[candidate_id.strip()]
            return None

        # User and Chat isolation: cross-user or cross-chat access fails closed
        if user_id is not None and entry["user_id"] is not None and entry["user_id"] != user_id:
            return None
        if chat_id is not None and entry["chat_id"] is not None and entry["chat_id"] != chat_id:
            return None

        # Operation binding: e.g. candidate registered as 'image_artwork' cannot be used for 'subtitle_track'
        if expected_operation is not None and entry["operation"] != expected_operation:
            return None

        return dict(entry["data"])

    def _prune_if_needed(self) -> None:
        now = time.time()
        # Clean expired
        expired = [cid for cid, v in self._cache.items() if now - v["created_at"] > self.ttl_seconds]
        for cid in expired:
            del self._cache[cid]

        # Enforce max entries cap (evict oldest)
        if len(self._cache) >= self.max_entries:
            sorted_by_age = sorted(self._cache.items(), key=lambda kv: kv[1]["created_at"])
            to_remove = sorted_by_age[: len(self._cache) - self.max_entries + 1]
            for cid, _ in to_remove:
                del self._cache[cid]
