"""Append-only structured action history with secret redaction."""

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional
from ai_admin.redaction import redact_data, redact_text


class AuditLog:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "audit_log.sqlite")
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    tool TEXT NOT NULL,
                    item_id TEXT,
                    item_type TEXT,
                    params_summary TEXT,
                    candidate_source TEXT,
                    approval_required INTEGER NOT NULL,
                    approval_id TEXT,
                    outcome TEXT NOT NULL, -- success | denied | failed
                    verification_result TEXT, -- verified | unverified | failed
                    error_category TEXT,
                    snapshot_ref TEXT
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp DESC);"
            )

    def record_action(
        self,
        action_id: str,
        user_id: int,
        chat_id: int,
        tool: str,
        item_id: Optional[str] = None,
        item_type: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        candidate_source: Optional[str] = None,
        approval_required: bool = False,
        approval_id: Optional[str] = None,
        outcome: str = "success",
        verification_result: Optional[str] = None,
        error_category: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
    ) -> int:
        """Append an action outcome to the audit log with automatic secret redaction."""
        now = int(time.time())

        # Redact parameters
        clean_params = redact_data(params) if params else {}
        params_summary = redact_text(json.dumps(clean_params, sort_keys=True)[:400])

        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO audit_log
                (action_id, timestamp, user_id, chat_id, tool, item_id, item_type,
                 params_summary, candidate_source, approval_required, approval_id,
                 outcome, verification_result, error_category, snapshot_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    action_id,
                    now,
                    user_id,
                    chat_id,
                    tool,
                    item_id,
                    item_type,
                    params_summary,
                    candidate_source,
                    1 if approval_required else 0,
                    approval_id,
                    outcome,
                    verification_result,
                    error_category,
                    snapshot_ref,
                ),
            )
            return cur.lastrowid

    def get_recent_actions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent audit entries."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """
                SELECT action_id, timestamp, user_id, chat_id, tool, item_id, item_type,
                       params_summary, candidate_source, approval_required, outcome,
                       verification_result, error_category, snapshot_ref
                FROM audit_log
                ORDER BY timestamp DESC LIMIT ?;
                """,
                (max(1, min(limit, 100)),),
            )
            return [dict(row) for row in cur.fetchall()]
