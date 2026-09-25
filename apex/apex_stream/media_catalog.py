"""Small SQLite catalog for Telegram-backed media.

The catalog deliberately uses only the Python standard library.  It stores the
Telegram source identity separately from the application's canonical key so a
message can be found using either identity.
"""

from __future__ import annotations

import sqlite3
import threading
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS media_records (
    id INTEGER PRIMARY KEY,
    source_chat_id INTEGER NOT NULL,
    source_message_id INTEGER NOT NULL,
    canonical_key TEXT NOT NULL UNIQUE,
    file_id TEXT,
    file_name TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    published INTEGER NOT NULL DEFAULT 0 CHECK (published IN (0, 1)),
    deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (source_chat_id, source_message_id)
);
CREATE INDEX IF NOT EXISTS idx_media_records_source
    ON media_records (source_chat_id, source_message_id);
CREATE INDEX IF NOT EXISTS idx_media_records_published
    ON media_records (published, deleted);
CREATE TABLE IF NOT EXISTS media_jobs (
    id INTEGER PRIMARY KEY,
    source_chat_id INTEGER NOT NULL,
    source_message_id INTEGER NOT NULL,
    canonical_key TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    confidence REAL NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    next_retry_at TEXT,
    last_error TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (source_chat_id, source_message_id)
);
CREATE INDEX IF NOT EXISTS idx_media_jobs_review
    ON media_jobs (status, confidence, updated_at);
CREATE TABLE IF NOT EXISTS episode_identities (
    id INTEGER PRIMARY KEY,
    show_canonical_key TEXT NOT NULL,
    season INTEGER NOT NULL CHECK (season >= 0),
    episode INTEGER NOT NULL CHECK (episode >= 0),
    title TEXT,
    air_date TEXT,
    runtime_minutes INTEGER,
    source_chat_id INTEGER NOT NULL,
    source_message_id INTEGER NOT NULL,
    source_file_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (source_chat_id, source_message_id)
);
CREATE INDEX IF NOT EXISTS idx_episode_identity_key
    ON episode_identities (show_canonical_key, season, episode);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class MediaRecord:
    source_chat_id: int
    source_message_id: int
    canonical_key: str
    file_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    published: bool = False
    deleted: bool = False
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True, slots=True)
class MediaJob:
    source_chat_id: int
    source_message_id: int
    canonical_key: str | None = None
    status: str = "pending"
    confidence: float = 0.0
    retry_count: int = 0
    next_retry_at: str | None = None
    last_error: str | None = None
    payload: dict | None = None
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True, slots=True)
class EpisodeIdentity:
    show_canonical_key: str
    season: int
    episode: int
    title: str | None = None
    air_date: str | None = None
    runtime_minutes: int | None = None
    source_chat_id: int = 0
    source_message_id: int = 0
    source_file_id: str | None = None
    id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @property
    def canonical_key(self) -> str:
        """Compatibility spelling for callers that use the catalog key name."""
        return self.show_canonical_key

    @property
    def runtime(self) -> int | None:
        return self.runtime_minutes


class MediaCatalog:
    """A synchronous, small-footprint media catalog.

    A connection is kept per catalog instance.  Calls are serialized by
    SQLite's transactions, and writes use short ``BEGIN IMMEDIATE`` blocks.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self.initialize()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def initialize(self) -> None:
        """Create the schema in one atomic transaction (safe to call repeatedly)."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                for statement in SCHEMA.split(";"):
                    if statement.strip():
                        self._connection.execute(statement)
                self._connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> MediaCatalog:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def upsert(
        self,
        record: MediaRecord | None = None,
        *,
        source_chat_id: int | None = None,
        source_message_id: int | None = None,
        canonical_key: str | None = None,
        file_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        size_bytes: int | None = None,
        published: bool = False,
        deleted: bool = False,
    ) -> MediaRecord:
        """Insert or replace the descriptive fields for one media record.

        Existing publication/deletion state is intentionally preserved when the
        shorthand arguments are used, preventing a re-index from republishing
        or resurrecting a deleted item.  Passing a ``MediaRecord`` explicitly
        sets its complete state.
        """
        explicit_state = record is not None
        if record is not None:
            values = record
        else:
            if source_chat_id is None or source_message_id is None or canonical_key is None:
                raise TypeError("source_chat_id, source_message_id, and canonical_key are required")
            values = MediaRecord(
                source_chat_id, source_message_id, canonical_key, file_id, file_name,
                mime_type, size_bytes, published, deleted,
            )
        now = _now()
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                existing = self._connection.execute(
                "SELECT created_at, published, deleted FROM media_records "
                "WHERE source_chat_id = ? AND source_message_id = ?",
                (values.source_chat_id, values.source_message_id),
                ).fetchone()
                if existing and not explicit_state:
                    published, deleted = bool(existing["published"]), bool(existing["deleted"])
                else:
                    published, deleted = values.published, values.deleted
                created = existing["created_at"] if existing else (values.created_at or now)
                canonical_key = values.canonical_key
                collision = self._connection.execute(
                    "SELECT source_chat_id, source_message_id FROM media_records "
                    "WHERE canonical_key = ? AND NOT (source_chat_id = ? AND source_message_id = ?)",
                    (canonical_key, values.source_chat_id, values.source_message_id),
                ).fetchone()
                if collision:
                    canonical_key = (
                        f"{canonical_key}:variant-{values.source_chat_id}-{values.source_message_id}"
                    )
                self._connection.execute(
                """
                INSERT INTO media_records
                    (source_chat_id, source_message_id, canonical_key, file_id,
                     file_name, mime_type, size_bytes, published, deleted,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_chat_id, source_message_id) DO UPDATE SET
                    canonical_key=excluded.canonical_key, file_id=excluded.file_id,
                    file_name=excluded.file_name, mime_type=excluded.mime_type,
                    size_bytes=excluded.size_bytes, published=excluded.published,
                    deleted=excluded.deleted, updated_at=excluded.updated_at
                """,
                (values.source_chat_id, values.source_message_id, canonical_key,
                 values.file_id, values.file_name, values.mime_type, values.size_bytes,
                 int(published), int(deleted), created, now),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
        return self.find_by_source(values.source_chat_id, values.source_message_id)  # type: ignore[return-value]

    def find_by_source(self, source_chat_id: int, source_message_id: int) -> MediaRecord | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM media_records WHERE source_chat_id = ? AND source_message_id = ?",
                (source_chat_id, source_message_id),
            ).fetchone()
            return self._record(row)

    def find_by_canonical_key(self, canonical_key: str) -> MediaRecord | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM media_records WHERE canonical_key = ?", (canonical_key,)
            ).fetchone()
            return self._record(row)

    def mark_deleted(self, *, source_chat_id: int | None = None,
                     source_message_id: int | None = None,
                     canonical_key: str | None = None) -> bool:
        return self._set_state(source_chat_id, source_message_id, canonical_key, deleted=True, published=False)

    def unpublish(self, *, source_chat_id: int | None = None,
                  source_message_id: int | None = None,
                  canonical_key: str | None = None) -> bool:
        return self._set_state(source_chat_id, source_message_id, canonical_key, published=False)

    def mark_published(self, *, source_chat_id: int | None = None,
                       source_message_id: int | None = None,
                       canonical_key: str | None = None) -> bool:
        return self._set_state(source_chat_id, source_message_id, canonical_key, published=True)

    def _set_state(self, chat: int | None, message: int | None, key: str | None, **state: bool) -> bool:
        if key is None and (chat is None or message is None):
            raise TypeError("provide canonical_key or both source identifiers")
        column = next(iter(state))
        value = int(next(iter(state.values())))
        where, args = (("canonical_key = ?", (key,)) if key is not None else
                        ("source_chat_id = ? AND source_message_id = ?", (chat, message)))
        updates = f"{column} = ?, updated_at = ?"
        if column == "deleted" and value:
            updates += ", published = 0"
        with self._lock:
            cursor = self._connection.execute(
                f"UPDATE media_records SET {updates} WHERE {where}", (value, _now(), *args)
            )
            self._connection.commit()
            return cursor.rowcount > 0

    def list_records(self, *, include_deleted: bool = False,
                     published_only: bool = False) -> list[MediaRecord]:
        query = "SELECT * FROM media_records"
        clauses: list[str] = []
        if not include_deleted:
            clauses.append("deleted = 0")
        if published_only:
            clauses.append("published = 1")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id"
        with self._lock:
            return [self._record(row) for row in self._connection.execute(query)]  # type: ignore[misc]

    def record_episode(self, identity: EpisodeIdentity | None = None, *,
                       show_canonical_key: str | None = None,
                       canonical_key: str | None = None,
                       season: int | None = None, episode_number: int | None = None,
                       episode: int | None = None, title: str | None = None,
                       air_date: str | None = None, runtime_minutes: int | None = None,
                       source_chat_id: int | None = None,
                       source_message_id: int | None = None,
                       source_file_id: str | None = None) -> EpisodeIdentity:
        """Record an episode, preserving multiple sources for one episode key."""
        if isinstance(episode, EpisodeIdentity):
            identity = episode
        if isinstance(identity, EpisodeIdentity):
            values = identity
        else:
            key = show_canonical_key or canonical_key
            number = episode_number if episode_number is not None else episode
            if key is None or season is None or number is None:
                raise TypeError("show_canonical_key, season, and episode are required")
            if source_chat_id is None or source_message_id is None:
                raise TypeError("source_chat_id and source_message_id are required")
            values = EpisodeIdentity(
                key, int(season), int(number), title, air_date, runtime_minutes,
                int(source_chat_id), int(source_message_id), source_file_id,
            )
        if values.season < 0 or values.episode < 0:
            raise ValueError("season and episode must be non-negative")
        now = _now()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO episode_identities
                    (show_canonical_key, season, episode, title, air_date,
                     runtime_minutes, source_chat_id, source_message_id,
                     source_file_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_chat_id, source_message_id) DO UPDATE SET
                    show_canonical_key=excluded.show_canonical_key, season=excluded.season,
                    episode=excluded.episode, title=excluded.title, air_date=excluded.air_date,
                    runtime_minutes=excluded.runtime_minutes, source_file_id=excluded.source_file_id,
                    updated_at=excluded.updated_at
                """,
                (values.show_canonical_key, values.season, values.episode, values.title,
                 values.air_date, values.runtime_minutes, values.source_chat_id,
                 values.source_message_id, values.source_file_id, values.created_at or now, now),
            )
            self._connection.commit()
        return self._episode_by_source(values.source_chat_id, values.source_message_id)  # type: ignore[return-value]

    def list_episodes(self, *, show_canonical_key: str | None = None,
                      canonical_key: str | None = None, season: int | None = None) -> list[EpisodeIdentity]:
        clauses, args = [], []
        key = show_canonical_key or canonical_key
        if key is not None:
            clauses.append("show_canonical_key = ?")
            args.append(key)
        if season is not None:
            clauses.append("season = ?")
            args.append(season)
        query = "SELECT * FROM episode_identities"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY show_canonical_key, season, episode, id"
        with self._lock:
            return [self._episode(row) for row in self._connection.execute(query, args)]

    def episode_report(self, show_canonical_key: str, *, season: int | None = None,
                       expected: Any = None) -> dict[str, Any]:
        """Return episode identities grouped into duplicate keys and missing numbers.

        ``expected`` may be an iterable of episode numbers, or a mapping of season
        numbers to iterables.  Without it, missing episodes are intentionally empty:
        a catalog cannot infer whether an unrecorded episode exists.
        """
        rows = self.list_episodes(show_canonical_key=show_canonical_key, season=season)
        groups: dict[tuple[int, int], list[EpisodeIdentity]] = {}
        for row in rows:
            groups.setdefault((row.season, row.episode), []).append(row)
        duplicates = [
            {"season": s, "episode": e, "identities": identities}
            for (s, e), identities in groups.items() if len(identities) > 1
        ]
        missing: list[dict[str, int]] = []
        if expected is not None:
            expected_by_season = expected if isinstance(expected, dict) else {season if season is not None else 1: expected}
            for s, numbers in expected_by_season.items():
                for e in numbers:
                    if (int(s), int(e)) not in groups:
                        missing.append({"season": int(s), "episode": int(e)})
        return {"show_canonical_key": show_canonical_key, "episodes": rows,
                "missing": missing, "duplicates": duplicates}

    report_episode_completeness = episode_report
    record_episode_identity = record_episode
    list_episode_identities = list_episodes

    def _episode_by_source(self, source_chat_id: int, source_message_id: int) -> EpisodeIdentity | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM episode_identities WHERE source_chat_id = ? AND source_message_id = ?",
                (source_chat_id, source_message_id),
            ).fetchone()
            return self._episode(row)

    def upsert_job(self, job: MediaJob | None = None, *,
                   source_chat_id: int | None = None,
                   source_message_id: int | None = None,
                   canonical_key: str | None = None,
                   status: str = "pending",
                   confidence: float = 0.0,
                   retry_count: int = 0,
                   next_retry_at: str | None = None,
                   last_error: str | None = None,
                   payload: dict | None = None) -> MediaJob:
        """Create or update an idempotent ingestion/review job."""
        values = job or MediaJob(
            source_chat_id=source_chat_id if source_chat_id is not None else 0,
            source_message_id=source_message_id if source_message_id is not None else 0,
            canonical_key=canonical_key,
            status=status,
            confidence=confidence,
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            last_error=last_error,
            payload=payload,
        )
        if source_chat_id is None and job is None:
            raise TypeError("source_chat_id and source_message_id are required")
        if values.source_message_id is None:
            raise TypeError("source_chat_id and source_message_id are required")
        if not 0 <= float(values.confidence) <= 1:
            raise ValueError("confidence must be between 0 and 1")
        now = _now()
        payload_json = json.dumps(values.payload, sort_keys=True) if values.payload is not None else None
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO media_jobs
                    (source_chat_id, source_message_id, canonical_key, status,
                     confidence, retry_count, next_retry_at, last_error, payload_json,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_chat_id, source_message_id) DO UPDATE SET
                    canonical_key=excluded.canonical_key, status=excluded.status,
                    confidence=excluded.confidence, retry_count=excluded.retry_count,
                    next_retry_at=excluded.next_retry_at, last_error=excluded.last_error,
                    payload_json=excluded.payload_json, updated_at=excluded.updated_at
                """,
                (values.source_chat_id, values.source_message_id, values.canonical_key,
                 values.status, float(values.confidence), int(values.retry_count),
                 values.next_retry_at, values.last_error, payload_json,
                 values.created_at or now, now),
            )
            self._connection.commit()
        return self.find_job(values.source_chat_id, values.source_message_id)  # type: ignore[return-value]

    def find_job(self, source_chat_id: int, source_message_id: int) -> MediaJob | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT * FROM media_jobs WHERE source_chat_id = ? AND source_message_id = ?",
                (source_chat_id, source_message_id),
            ).fetchone()
            return self._job(row)

    def list_jobs(self, *, statuses: tuple[str, ...] = ("review",),
                  limit: int = 100) -> list[MediaJob]:
        if limit < 1:
            return []
        placeholders = ",".join("?" for _ in statuses)
        query = "SELECT * FROM media_jobs"
        args: list = []
        if statuses:
            query += f" WHERE status IN ({placeholders})"
            args.extend(statuses)
        query += " ORDER BY updated_at DESC LIMIT ?"
        args.append(min(limit, 1000))
        with self._lock:
            return [self._job(row) for row in self._connection.execute(query, args)]  # type: ignore[misc]

    def update_job(self, source_chat_id: int, source_message_id: int, *,
                   status: str | None = None, retry_count: int | None = None,
                   next_retry_at: str | None = None, last_error: str | None = None) -> bool:
        changes = {"updated_at": _now()}
        if status is not None:
            changes["status"] = status
        if retry_count is not None:
            changes["retry_count"] = retry_count
        if next_retry_at is not None:
            changes["next_retry_at"] = next_retry_at
        if last_error is not None:
            changes["last_error"] = last_error
        assignments = ", ".join(f"{key} = ?" for key in changes)
        with self._lock:
            cursor = self._connection.execute(
                f"UPDATE media_jobs SET {assignments} WHERE source_chat_id = ? AND source_message_id = ?",
                (*changes.values(), source_chat_id, source_message_id),
            )
            self._connection.commit()
            return cursor.rowcount > 0

    @staticmethod
    def _record(row: sqlite3.Row | None) -> MediaRecord | None:
        if row is None:
            return None
        return MediaRecord(
            row["source_chat_id"], row["source_message_id"], row["canonical_key"],
            row["file_id"], row["file_name"], row["mime_type"], row["size_bytes"],
            bool(row["published"]), bool(row["deleted"]), row["created_at"], row["updated_at"],
        )

    @staticmethod
    def _job(row: sqlite3.Row | None) -> MediaJob | None:
        if row is None:
            return None
        return MediaJob(
            row["source_chat_id"], row["source_message_id"], row["canonical_key"],
            row["status"], row["confidence"], row["retry_count"],
            row["next_retry_at"], row["last_error"],
            json.loads(row["payload_json"]) if row["payload_json"] else None,
            row["id"], row["created_at"], row["updated_at"],
        )

    @staticmethod
    def _episode(row: sqlite3.Row | None) -> EpisodeIdentity | None:
        if row is None:
            return None
        return EpisodeIdentity(
            row["show_canonical_key"], row["season"], row["episode"],
            row["title"], row["air_date"], row["runtime_minutes"],
            row["source_chat_id"], row["source_message_id"], row["source_file_id"],
            row["id"], row["created_at"], row["updated_at"],
        )
