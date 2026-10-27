"""SQLite-backed bound, expiring, single-use confirmation store."""

import hashlib
import json
import os
import secrets
import sqlite3
import time
from typing import Any, Dict, Optional, Tuple


def compute_action_hash(tool_name: str, params: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash of canonical action parameters."""
    canonical_json = json.dumps(
        {"tool": tool_name, "params": params},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class ConfirmationStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS confirmations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    action_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    consumed_at INTEGER
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_confirmations_expiry ON confirmations(expires_at, consumed_at);"
            )

    def create_confirmation(
        self,
        user_id: int,
        chat_id: int,
        tool_name: str,
        params: Dict[str, Any],
        ttl_seconds: int = 120,
    ) -> Tuple[str, str]:
        """Create a new expiring confirmation token.

        Returns (confirmation_id, action_hash).
        """
        # Short token safe for Telegram callback data (<= 32 chars)
        token_id = secrets.token_hex(16)
        action_hash = compute_action_hash(tool_name, params)
        payload_data = {"tool": tool_name, "params": params}
        payload_json = json.dumps(payload_data, sort_keys=True)

        now = int(time.time())
        expires_at = now + ttl_seconds

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO confirmations
                (id, user_id, chat_id, action_hash, payload_json, created_at, expires_at, consumed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL);
                """,
                (token_id, user_id, chat_id, action_hash, payload_json, now, expires_at),
            )

        return token_id, action_hash

    def consume_confirmation(
        self,
        confirmation_id: str,
        user_id: int,
        chat_id: int,
        expected_action_hash: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Atomically consume confirmation token.

        Returns (success, payload_dict, reason).
        """
        now = int(time.time())

        with self._get_connection() as conn:
            # Check existence and current status
            cur = conn.execute(
                """
                SELECT user_id, chat_id, action_hash, payload_json, expires_at, consumed_at
                FROM confirmations WHERE id = ?;
                """,
                (confirmation_id,),
            )
            row = cur.fetchone()
            if not row:
                return False, None, "Confirmation token not found."

            db_user, db_chat, action_hash, payload_json, expires_at, consumed_at = row

            if db_user != user_id or db_chat != chat_id:
                return False, None, "Authorization mismatch: token belongs to different user or chat."

            if consumed_at is not None:
                return False, None, "Token already used (replay rejected)."

            if now > expires_at:
                return False, None, "Confirmation token has expired."

            if expected_action_hash and expected_action_hash != action_hash:
                return False, None, "Action payload has changed since preview (hash mismatch)."

            # Atomic single-use consumption update
            cur = conn.execute(
                """
                UPDATE confirmations
                SET consumed_at = ?
                WHERE id = ? AND user_id = ? AND chat_id = ? AND consumed_at IS NULL AND expires_at >= ?;
                """,
                (now, confirmation_id, user_id, chat_id, now),
            )
            if cur.rowcount != 1:
                return False, None, "Concurrent consumption collision or token expired."

            payload = json.loads(payload_json)
            return True, payload, "consumed_successfully"

    def prune_expired(self) -> int:
        """Prune expired and old consumed records."""
        now = int(time.time())
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM confirmations WHERE expires_at < ?;", (now - 3600,))
            return cur.rowcount
