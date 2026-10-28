"""Regression tests for tg_streamer._prune_orphan_strms (layout-migration dedup).

tg_streamer imports pyrogram which isn't installed locally, so the helper is
extracted from the source AST and executed against temp directories.
"""

import ast
import asyncio
import os
import re
import shutil
from typing import Optional
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "tg_streamer.py"

STREAMER_URL = "http://127.0.0.1:8080/stream/-100:9/video.mp4"
OTHER_URL = "http://example.com/file.strm"


def _helper():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    node = next(
        n for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "_prune_orphan_strms"
    )
    ns = {"logger": type("_Sink", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(), "os": os, "shutil": shutil}
    exec(compile(ast.Module([node], []), "<ast>", "exec"), ns)
    return ns["_prune_orphan_strms"]


def _write(root, rel, content):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def _run(prune, movies, shows, keep):
    return asyncio.run(prune(movies, shows, keep))


def test_prune_removes_orphan_keeps_expected(tmp_path):
    prune = _helper()
    movies = tmp_path / "Movies"
    shows = tmp_path / "TV Shows"
    # New per-title layout (expected).
    keep_dir = movies / "English" / "Spiderman Homecoming (2017)"
    keep_dir.mkdir(parents=True)
    keep_strm = keep_dir / "Spiderman Homecoming (2017).strm"
    keep_strm.write_text(STREAMER_URL)
    keep_path = str(keep_strm.resolve())
    # Old flat layout orphan -> must be pruned.
    old_strm = _write(movies, "English/SpiderMan.Homecoming.2017.720p.BluRay.x264.strm", STREAMER_URL)
    # Unrelated strm (not ours) -> must survive.
    external = _write(movies, "English/someone-elses.strm", OTHER_URL)
    # TV flat-layout orphan in wrong (no-year) folder.
    tv_orphan = _write(shows, "English/Breaking Bad/Season 01/Breaking Bad - S01E01.strm", STREAMER_URL)

    pruned = _run(prune, str(movies), str(shows), {keep_path})
    assert pruned == 2
    assert keep_strm.exists()
    assert external.exists()
    assert not old_strm.exists()
    assert not tv_orphan.exists()


def test_prune_keeps_everything_when_all_expected(tmp_path):
    prune = _helper()
    movies = tmp_path / "Movies"
    keep_dir = movies / "English" / "Dune (2021)"
    keep_dir.mkdir(parents=True)
    s = keep_dir / "Dune (2021).strm"
    s.write_text(STREAMER_URL)
    pruned = _run(prune, str(movies), str(tmp_path / "TV Shows"), {str(s.resolve())})
    assert pruned == 0
    assert s.exists()


def test_purge_media_item_by_title_and_msg_id(tmp_path):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    node = next(
        n for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "purge_media_item"
    )
    cache = {}
    catalog_deleted = []

    class MockCatalog:
        def mark_deleted(self, source_chat_id, source_message_id):
            catalog_deleted.append((source_chat_id, source_message_id))
            return True

    movie_dir = tmp_path / "Movie (2026)"
    movie_dir.mkdir()
    strm_file = movie_dir / "Movie (2026).strm"
    strm_file.write_text("http://127.0.0.1:8080/stream/1:100/video.mp4")

    cache["-100:100"] = {
        "chat_id": -100,
        "msg_id": 100,
        "title": "Movie (2026)",
        "clean_title": "Movie",
        "strm_path": str(strm_file),
        "target_dir": str(movie_dir),
    }

    async def mock_save():
        pass

    async def mock_scan():
        pass

    ns = {
        "logger": type("_Sink", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(),
        "os": os,
        "re": re,
        "shutil": shutil,
        "Optional": Optional,
        "_split_cache_key": lambda k: (int(k.split(":")[0]), int(k.split(":")[1])),
        "FILE_ID_CACHE": cache,
        "MEDIA_CATALOG": MockCatalog(),
        "save_cache_async": mock_save,
        "trigger_jellyfin_scan": mock_scan,
    }
    exec(compile(ast.Module([node], []), "<ast>", "exec"), ns)
    purge = ns["purge_media_item"]

    purged = asyncio.run(purge(title_query="Movie"))
    assert purged == ["Movie (2026)"]
    assert not strm_file.exists()
    assert not movie_dir.exists()
    assert len(cache) == 0
    assert catalog_deleted == [(-100, 100)]


def test_deduplicate_jellyfin_items_preserves_blacklisted_media(tmp_path):
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    node = next(
        n for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "deduplicate_jellyfin_items"
    )

    deleted_item_ids = []
    recorded_reviews = []

    class MockResponse:
        def __init__(self, data=None, status=200):
            self.data = data or {}
            self.status = status

        async def json(self):
            return self.data

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockSession:
        def __init__(self, items):
            self.items = items

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def get(self, url, **kwargs):
            return MockResponse({"Items": self.items}, status=200)

        def delete(self, url, **kwargs):
            item_id = url.rsplit("/", 1)[-1]
            deleted_item_ids.append(item_id)
            return MockResponse(status=204)

    class MockAiohttp:
        def __init__(self, items):
            self.items = items

        def ClientSession(self, *args, **kwargs):
            return MockSession(self.items)

    movies_dir = tmp_path / "Movies"
    shows_dir = tmp_path / "TV Shows"
    movies_dir.mkdir(parents=True)
    shows_dir.mkdir(parents=True)

    # Physical strm file for blacklisted movie
    blacklisted_folder = movies_dir / "Ms.Rose & Mr.Cane (2026)"
    blacklisted_folder.mkdir()
    blacklisted_strm = blacklisted_folder / "Ms.Rose & Mr.Cane (2026).strm"
    blacklisted_strm.write_text("http://127.0.0.1:8080/stream/1:200/video.mp4")

    # Physical dir for blacklisted series
    blacklisted_series = shows_dir / "WWE Money in the Bank"
    blacklisted_series.mkdir()

    # Physical strm for legitimate duplicates
    legit_folder = movies_dir / "Legit Movie (2025)"
    legit_folder.mkdir()
    legit_strm = legit_folder / "Legit Movie (2025).strm"
    legit_strm.write_text("http://127.0.0.1:8080/stream/1:300/video.mp4")

    items = [
        {
            "Id": "blacklisted-movie-id",
            "Name": "Ms.Rose & Mr.Cane",
            "Type": "Movie",
            "Path": str(blacklisted_strm),
            "ProviderIds": {},
        },
        {
            "Id": "blacklisted-series-id",
            "Name": "WWE Money in the Bank",
            "Type": "Series",
            "Path": str(blacklisted_series),
            "ProviderIds": {},
        },
        {
            "Id": "legit-dup-1",
            "Name": "Legit Movie",
            "Type": "Movie",
            "Path": str(legit_strm),
            "ProviderIds": {"Tmdb": "9999"},
        },
        {
            "Id": "legit-dup-2",
            "Name": "Legit Movie",
            "Type": "Movie",
            "Path": str(legit_strm),
            "ProviderIds": {"Tmdb": "9999"},
        },
        {
            "Id": "ghost-orphan-id",
            "Name": "Deleted Media",
            "Type": "Movie",
            "Path": str(movies_dir / "nonexistent.strm"),
            "ProviderIds": {},
        },
    ]

    # Extract is_blacklisted via AST to avoid importing pyrogram
    patterns_node = next(
        n for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_BLACKLIST_PATTERNS" for t in n.targets)
    )
    is_bl_node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "is_blacklisted"
    )
    bl_ns = {"re": re, "Optional": Optional}
    exec(compile(ast.Module([patterns_node, is_bl_node], []), "<ast>", "exec"), bl_ns)
    is_blacklisted = bl_ns["is_blacklisted"]

    ns = {
        "logger": type("_Sink", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(),
        "os": os,
        "re": re,
        "aiohttp": MockAiohttp(items),
        "_jellyfin_auth_header": lambda: {"X-Emby-Token": "test-token"},
        "_read_jellyfin_api_key": lambda: "test-token",
        "MOVIES_DIR": str(movies_dir),
        "SHOWS_DIR": str(shows_dir),
        "FILE_ID_CACHE": {},
        "is_blacklisted": is_blacklisted,
        "_record_review_job": lambda data, confidence=0.0, reason="": recorded_reviews.append((data, confidence, reason)),
        "parse_media_meta": lambda name: {"title": name, "clean_title": name},
        "_canonical_media_key": lambda e: "tmdb:9999",
        "DEFAULT_LANGUAGE": "English",
    }
    exec(compile(ast.Module([node], []), "<ast>", "exec"), ns)
    dedup = ns["deduplicate_jellyfin_items"]

    res = asyncio.run(dedup())

    # Blacklisted items MUST NEVER be deleted from Jellyfin
    assert "blacklisted-movie-id" not in deleted_item_ids
    assert "blacklisted-series-id" not in deleted_item_ids

    # Both blacklisted media on disk MUST be preserved
    assert blacklisted_strm.exists()
    assert blacklisted_series.exists()

    # Blacklisted items MUST be routed to the review queue
    review_reasons = [r[2] for r in recorded_reviews]
    assert any("blacklisted_jellyfin_item:Ms.Rose & Mr.Cane" in r for r in review_reasons)
    assert any("blacklisted_jellyfin_item:WWE Money in the Bank" in r for r in review_reasons)

    # Genuine orphan item (nonexistent file) must be deleted
    assert "ghost-orphan-id" in deleted_item_ids

    # Exactly one duplicate of the legitimate movie must be deleted
    assert ("legit-dup-1" in deleted_item_ids) ^ ("legit-dup-2" in deleted_item_ids)


def test_reindex_all_with_imdb_preserves_untracked_strm_and_directories(tmp_path):
    """Execute the real reindex_all_with_imdb function and verify that both untracked .strm files
    and directories with unrecognized formats are preserved and sent to review.
    """
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    node = next(
        n for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "reindex_all_with_imdb"
    )

    movies_dir = tmp_path / "Movies"
    shows_dir = tmp_path / "TV Shows"
    movies_dir.mkdir(parents=True)
    shows_dir.mkdir(parents=True)

    # 1. Tracked media folder & strm
    tracked_folder = movies_dir / "English" / "Tracked Title (2025)"
    tracked_folder.mkdir(parents=True)
    tracked_strm = tracked_folder / "Tracked Title (2025).strm"
    tracked_strm.write_text("http://127.0.0.1:8080/stream/1:100/video.mp4")

    # 2. Untracked directory containing an unrecognized binary file (.bin)
    untracked_unknown_dir = movies_dir / "English" / "Unknown Format Title"
    untracked_unknown_dir.mkdir(parents=True)
    bin_file = untracked_unknown_dir / "payload.bin"
    bin_file.write_bytes(b"valuable media payload")

    # 3. Untracked .strm file in another directory
    untracked_strm_dir = movies_dir / "English" / "Untracked Stream Title"
    untracked_strm_dir.mkdir(parents=True)
    untracked_strm = untracked_strm_dir / "untracked.strm"
    untracked_strm.write_text("http://127.0.0.1:8080/stream/1:999/video.mp4")

    # 4. Untracked directory with sidecar files (.nfo, .txt)
    sidecar_dir = movies_dir / "English" / "Sidecar Title"
    sidecar_dir.mkdir(parents=True)
    (sidecar_dir / "movie.nfo").write_text("<movie></movie>")
    (sidecar_dir / "notes.txt").write_text("user notes")

    # 5. Genuinely empty directory (no files, no subdirectories)
    truly_empty = movies_dir / "English" / "Truly Empty Folder"
    truly_empty.mkdir(parents=True)

    recorded_reviews = []

    class MockJob:
        payload = {
            "strm_path": str(tracked_strm),
            "target_dir": str(tracked_folder),
        }

    class MockRecord:
        source_chat_id = -100
        source_message_id = 100

    class MockCatalog:
        def list_records(self, include_deleted=False):
            return [MockRecord()]

        def find_job(self, chat_id, msg_id):
            return MockJob()

    class MockSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    class MockAiohttp:
        class TCPConnector:
            def __init__(self, *args, **kwargs):
                pass
        def ClientSession(self, *args, **kwargs):
            return MockSession()

    async def mock_async_noop(*args, **kwargs):
        pass

    import socket
    ns = {
        "logger": type("_Sink", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(),
        "os": os,
        "socket": socket,
        "aiohttp": MockAiohttp(),
        "asyncio": asyncio,
        "MOVIES_DIR": str(movies_dir),
        "SHOWS_DIR": str(shows_dir),
        "FILE_ID_CACHE": {},
        "MEDIA_CATALOG": MockCatalog(),
        "save_cache_async": mock_async_noop,
        "deduplicate_jellyfin_items": mock_async_noop,
        "refresh_jellyfin_item_by_path": mock_async_noop,
        "request_jellyfin_scan": mock_async_noop,
        "_record_review_job": lambda data, confidence=0.0, reason="": recorded_reviews.append((data, confidence, reason)),
    }
    exec(compile(ast.Module([node], []), "<ast>", "exec"), ns)
    reindex_func = ns["reindex_all_with_imdb"]

    # Execute the actual reindex_all_with_imdb function
    res = asyncio.run(reindex_func(force_all=False))

    # Untracked directory containing unrecognized file MUST survive!
    assert untracked_unknown_dir.exists()
    assert bin_file.exists()

    # Untracked .strm file and its directory MUST survive!
    assert untracked_strm_dir.exists()
    assert untracked_strm.exists()

    # Tracked media must remain untouched
    assert tracked_folder.exists()
    assert tracked_strm.exists()

    # Sidecar directory MUST survive and be routed to review
    assert sidecar_dir.exists()
    assert (sidecar_dir / "movie.nfo").exists()
    assert (sidecar_dir / "notes.txt").exists()

    # Truly empty directory MUST be cleaned via os.rmdir
    assert not truly_empty.exists()

    # Review queue must have recorded both untracked directories and untracked strm
    reasons = [r[2] for r in recorded_reviews]
    assert any("untracked_directory:Unknown Format Title" in r for r in reasons)
    assert any("untracked_directory:Sidecar Title" in r for r in reasons)
    assert any("untracked_strm_file:untracked.strm" in r for r in reasons)


def test_reconciliation_end_to_end_library_behavior(tmp_path):
    """End-to-end integration test verifying that:
    1. Tracked media survives.
    2. Untracked movie .strm and its directory survive and are routed to review.
    3. Duplicate Jellyfin items are deduplicated safely.
    4. Missing .strm target (genuine orphan) is cleaned from Jellyfin API.
    5. User-created sidecars (notes.txt, custom.xml, cover_backup.png) survive intact.
    6. Unknown / uncertain media entries are preserved and sent to review.
    """
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    dedup_node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "deduplicate_jellyfin_items")
    reindex_node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "reindex_all_with_imdb")

    movies_dir = tmp_path / "Movies"
    shows_dir = tmp_path / "TV Shows"
    movies_dir.mkdir(parents=True)
    shows_dir.mkdir(parents=True)

    # 1. Tracked Movie
    tracked_dir = movies_dir / "English" / "Inception (2010)"
    tracked_dir.mkdir(parents=True)
    tracked_strm = tracked_dir / "Inception (2010).strm"
    tracked_strm.write_text("http://127.0.0.1:8080/stream/1:100/video.mp4")

    # 2. Untracked Movie
    untracked_dir = movies_dir / "English" / "Untracked Indie Film (2024)"
    untracked_dir.mkdir(parents=True)
    untracked_strm = untracked_dir / "Untracked Indie Film (2024).strm"
    untracked_strm.write_text("http://127.0.0.1:8080/stream/1:200/video.mp4")

    # 3. User-created sidecars (notes.txt, custom.xml, cover_backup.png)
    user_sidecar_dir = movies_dir / "English" / "User Curated Title (2023)"
    user_sidecar_dir.mkdir(parents=True)
    user_txt = user_sidecar_dir / "notes.txt"
    user_txt.write_text("personal user notes")
    user_xml = user_sidecar_dir / "custom.xml"
    user_xml.write_text("<metadata>personal</metadata>")
    user_png = user_sidecar_dir / "cover_backup.png"
    user_png.write_bytes(b"image bytes")

    # Missing file path (genuine orphan)
    orphan_strm_path = str(movies_dir / "English" / "Ghost (1990)" / "Ghost (1990).strm")

    deleted_item_ids = []
    recorded_reviews = []

    class MockResponse:
        def __init__(self, data=None, status=200):
            self.data = data or {}
            self.status = status
        async def json(self):
            return self.data
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    jellyfin_items = [
        # Tracked movie duplicate 1
        {"Id": "dup-item-1", "Name": "Inception", "Type": "Movie", "Path": str(tracked_strm), "ProviderIds": {"Tmdb": "27205"}},
        # Tracked movie duplicate 2
        {"Id": "dup-item-2", "Name": "Inception", "Type": "Movie", "Path": str(tracked_strm), "ProviderIds": {"Tmdb": "27205"}},
        # Untracked movie item in Jellyfin
        {"Id": "untracked-item-1", "Name": "Untracked Indie Film", "Type": "Movie", "Path": str(untracked_strm), "ProviderIds": {}},
        # Genuine orphan item (missing from disk)
        {"Id": "orphan-item-ghost", "Name": "Ghost", "Type": "Movie", "Path": orphan_strm_path, "ProviderIds": {}},
    ]

    class MockSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        def get(self, url, **kwargs):
            return MockResponse({"Items": jellyfin_items}, status=200)
        def delete(self, url, **kwargs):
            item_id = url.rsplit("/", 1)[-1]
            deleted_item_ids.append(item_id)
            return MockResponse(status=204)

    class MockAiohttp:
        class TCPConnector:
            def __init__(self, *args, **kwargs):
                pass
        def ClientSession(self, *args, **kwargs):
            return MockSession()

    class MockJob:
        payload = {"strm_path": str(tracked_strm), "target_dir": str(tracked_dir)}

    class MockRecord:
        source_chat_id = -100
        source_message_id = 100

    class MockCatalog:
        def list_records(self, include_deleted=False):
            return [MockRecord()]
        def find_job(self, chat_id, msg_id):
            return MockJob()

    async def mock_async_noop(*args, **kwargs):
        pass

    import socket
    ns = {
        "logger": type("_Sink", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})(),
        "os": os,
        "re": re,
        "socket": socket,
        "aiohttp": MockAiohttp(),
        "asyncio": asyncio,
        "_jellyfin_auth_header": lambda: {"X-Emby-Token": "test-token"},
        "_read_jellyfin_api_key": lambda: "test-token",
        "MOVIES_DIR": str(movies_dir),
        "SHOWS_DIR": str(shows_dir),
        "FILE_ID_CACHE": {},
        "MEDIA_CATALOG": MockCatalog(),
        "is_blacklisted": lambda text: False,
        "_record_review_job": lambda data, confidence=0.0, reason="": recorded_reviews.append((data, confidence, reason)),
        "save_cache_async": mock_async_noop,
        "deduplicate_jellyfin_items": mock_async_noop,
        "refresh_jellyfin_item_by_path": mock_async_noop,
        "request_jellyfin_scan": mock_async_noop,
        "parse_media_meta": lambda name: {"title": name, "clean_title": name},
        "_canonical_media_key": lambda e: f"name:{e.get('title') or e.get('clean_title') or 'unknown'}",
        "DEFAULT_LANGUAGE": "English",
    }

    # Step A: Run deduplicate_jellyfin_items
    exec(compile(ast.Module([dedup_node], []), "<ast>", "exec"), ns)
    dedup_func = ns["deduplicate_jellyfin_items"]
    asyncio.run(dedup_func())

    # Verify deduplication results:
    # 1. Genuine orphan is deleted
    assert "orphan-item-ghost" in deleted_item_ids
    # 2. Exactly one Inception duplicate is deleted
    assert ("dup-item-1" in deleted_item_ids) ^ ("dup-item-2" in deleted_item_ids)
    # 3. Untracked indie film (exists on disk) is NOT deleted
    assert "untracked-item-1" not in deleted_item_ids

    # Step B: Run reindex_all_with_imdb
    exec(compile(ast.Module([reindex_node], []), "<ast>", "exec"), ns)
    reindex_func = ns["reindex_all_with_imdb"]
    asyncio.run(reindex_func(force_all=False))

    # Verify filesystem and review queue results:
    # 1. Tracked movie survives
    assert tracked_dir.exists()
    assert tracked_strm.exists()

    # 2. Untracked movie survives on disk and is queued for review
    assert untracked_dir.exists()
    assert untracked_strm.exists()

    # 3. User sidecars survive on disk and are queued for review
    assert user_sidecar_dir.exists()
    assert user_txt.exists()
    assert user_xml.exists()
    assert user_png.exists()

    reasons = [r[2] for r in recorded_reviews]
    assert any("untracked_strm_file:Untracked Indie Film (2024).strm" in r for r in reasons)
    assert any("untracked_directory:User Curated Title (2023)" in r for r in reasons)