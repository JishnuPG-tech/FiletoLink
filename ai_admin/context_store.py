"""Per-user/chat bounded conversation and target resolution context store."""

import time
from typing import Any, Dict, List, Optional, Tuple


class ContextStore:
    def __init__(self, ttl_seconds: int = 900, max_history_turns: int = 6):
        self.ttl_seconds = ttl_seconds
        self.max_history_turns = max_history_turns
        # Key: (user_id, chat_id) -> Dict
        self._store: Dict[Tuple[int, int], Dict[str, Any]] = {}

    def _get_entry(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        key = (user_id, chat_id)
        now = time.time()
        entry = self._store.get(key)
        if entry:
            if now - entry.get("last_updated", 0) > self.ttl_seconds:
                # Expired
                entry = {
                    "selected_item_id": None,
                    "selected_item_title": None,
                    "last_search_results": [],
                    "history": [],
                    "last_updated": now,
                }
                self._store[key] = entry
        else:
            entry = {
                "selected_item_id": None,
                "selected_item_title": None,
                "last_search_results": [],
                "history": [],
                "last_updated": now,
            }
            self._store[key] = entry
        return entry

    def set_selected_item(self, user_id: int, chat_id: int, item_id: Optional[str], title: Optional[str] = None) -> None:
        """Set the currently focused Jellyfin item ID."""
        entry = self._get_entry(user_id, chat_id)
        entry["selected_item_id"] = str(item_id).strip() if item_id else None
        entry["selected_item_title"] = title.strip() if title else None
        entry["last_updated"] = time.time()

    def get_selected_item(self, user_id: int, chat_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Return (selected_item_id, selected_item_title)."""
        entry = self._get_entry(user_id, chat_id)
        return entry.get("selected_item_id"), entry.get("selected_item_title")

    def set_search_results(self, user_id: int, chat_id: int, items: List[Dict[str, Any]]) -> None:
        """Save a bounded list of recent search candidates."""
        entry = self._get_entry(user_id, chat_id)
        # Bounded to at most 10 items
        bounded = []
        for it in items[:10]:
            bounded.append({
                "id": str(it.get("id") or it.get("Id") or ""),
                "name": str(it.get("name") or it.get("Name") or ""),
                "year": it.get("year") or it.get("ProductionYear"),
                "type": it.get("type") or it.get("Type"),
            })
        entry["last_search_results"] = bounded
        entry["last_updated"] = time.time()

    def get_search_results(self, user_id: int, chat_id: int) -> List[Dict[str, Any]]:
        entry = self._get_entry(user_id, chat_id)
        return list(entry.get("last_search_results") or [])

    def add_turn(self, user_id: int, chat_id: int, role: str, content: str) -> None:
        """Append a bounded conversation turn."""
        entry = self._get_entry(user_id, chat_id)
        history: List[Dict[str, str]] = entry.setdefault("history", [])
        # Cap content length per turn to 400 chars
        truncated_content = (content or "").strip()[:400]
        history.append({"role": role, "content": truncated_content})
        if len(history) > self.max_history_turns:
            entry["history"] = history[-self.max_history_turns:]
        entry["last_updated"] = time.time()

    def get_history(self, user_id: int, chat_id: int) -> List[Dict[str, str]]:
        entry = self._get_entry(user_id, chat_id)
        return list(entry.get("history") or [])

    def clear(self, user_id: int, chat_id: int) -> None:
        """Clear conversation context."""
        key = (user_id, chat_id)
        if key in self._store:
            del self._store[key]
