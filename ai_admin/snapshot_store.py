"""Prior state snapshot store for verified undo operations."""

import json
import os
import sqlite3
import time
from typing import Any, Dict, Optional, Tuple


class SnapshotStore:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "snapshots.sqlite")
        self.blob_dir = os.path.join(data_dir, "snapshot_blobs")
        os.makedirs(self.blob_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    snapshot_type TEXT NOT NULL, -- artwork | metadata | subtitle
                    metadata_json TEXT NOT NULL,
                    blob_filename TEXT,
                    created_at INTEGER NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_user_chat ON snapshots(user_id, chat_id, created_at);"
            )

    def save_snapshot(
        self,
        snapshot_id: str,
        action_id: str,
        user_id: int,
        chat_id: int,
        item_id: str,
        snapshot_type: str,
        metadata: Dict[str, Any],
        binary_blob: Optional[bytes] = None,
    ) -> str:
        """Store prior state snapshot and return snapshot reference."""
        blob_fn = None
        if binary_blob:
            blob_fn = f"{snapshot_id}.bin"
            blob_path = os.path.join(self.blob_dir, blob_fn)
            with open(blob_path, "wb") as f:
                f.write(binary_blob)

        now = int(time.time())
        meta_json = json.dumps(metadata, sort_keys=True)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO snapshots
                (snapshot_id, action_id, user_id, chat_id, item_id, snapshot_type, metadata_json, blob_filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (snapshot_id, action_id, user_id, chat_id, item_id, snapshot_type, meta_json, blob_fn, now),
            )

        return snapshot_id

    def get_snapshot(self, snapshot_id: str) -> Optional[Tuple[Dict[str, Any], Optional[bytes]]]:
        """Retrieve snapshot metadata and binary blob by ID."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT metadata_json, blob_filename FROM snapshots WHERE snapshot_id = ?;",
                (snapshot_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            meta_json, blob_fn = row
            blob_bytes = None
            if blob_fn:
                blob_path = os.path.join(self.blob_dir, blob_fn)
                if os.path.exists(blob_path):
                    with open(blob_path, "rb") as f:
                        blob_bytes = f.read()

            return json.loads(meta_json), blob_bytes

    def get_latest_snapshot(self, user_id: int, chat_id: int) -> Optional[Tuple[str, Dict[str, Any], Optional[bytes]]]:
        """Retrieve the most recent snapshot for the user and chat for undo operations."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT snapshot_id, metadata_json, blob_filename
                FROM snapshots
                WHERE user_id = ? AND chat_id = ?
                ORDER BY created_at DESC LIMIT 1;
                """,
                (user_id, chat_id),
            )
            row = cur.fetchone()
            if not row:
                return None

            snap_id, meta_json, blob_fn = row
            blob_bytes = None
            if blob_fn:
                blob_path = os.path.join(self.blob_dir, blob_fn)
                if os.path.exists(blob_path):
                    with open(blob_path, "rb") as f:
                        blob_bytes = f.read()

            return snap_id, json.loads(meta_json), blob_bytes
