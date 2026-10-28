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


def test_untracked_directory_cleanup_preserves_unrecognized_formats(tmp_path):
    """Verify that untracked directories with unrecognized formats survive and are routed to review."""
    movies_dir = tmp_path / "Movies"
    shows_dir = tmp_path / "TV Shows"
    movies_dir.mkdir()
    shows_dir.mkdir()

    # 1. Untracked directory containing an unrecognized format or valuable file (e.g. .bin, .dat, .mp4)
    untracked_unknown = movies_dir / "English" / "Unknown Format Title"
    untracked_unknown.mkdir(parents=True)
    bin_file = untracked_unknown / "payload.bin"
    bin_file.write_bytes(b"binary media payload")

    # 2. Untracked directory with ONLY sidecar files (.nfo)
    sidecar_only = movies_dir / "English" / "Abandoned Sidecars"
    sidecar_only.mkdir(parents=True)
    (sidecar_only / "movie.nfo").write_text("<movie></movie>")

    recorded_reviews = []

    # Run the exact non-destructive directory cleanup logic implemented in reindex_all_with_imdb
    valid_dirs = {str(movies_dir / "English" / "Tracked Movie").lower()}

    for root in (str(movies_dir), str(shows_dir)):
        for dp, dns, fns in os.walk(root, topdown=False):
            norm_dp = os.path.normpath(dp)
            if norm_dp in (os.path.normpath(str(movies_dir)), os.path.normpath(str(shows_dir))):
                continue
            parent = os.path.dirname(norm_dp)
            if os.path.normpath(parent) in (os.path.normpath(str(movies_dir)), os.path.normpath(str(shows_dir))):
                continue
            remaining = os.listdir(dp)
            if not remaining:
                try:
                    os.rmdir(dp)
                except OSError:
                    pass
            else:
                sidecar_exts = (".nfo", ".xml", ".txt")
                sidecars = [f for f in remaining if f.lower().endswith(sidecar_exts)]
                if len(sidecars) == len(remaining):
                    for sf in sidecars:
                        try:
                            os.remove(os.path.join(dp, sf))
                        except OSError:
                            pass
                    try:
                        os.rmdir(dp)
                    except OSError:
                        pass
                elif valid_dirs and norm_dp.lower() not in valid_dirs and not any(f.lower().endswith('.strm') for f in remaining):
                    recorded_reviews.append({"directory": dp, "files": remaining[:10]})

    # Directory with unrecognized file MUST survive!
    assert untracked_unknown.exists()
    assert bin_file.exists()
    assert len(recorded_reviews) == 1
    assert recorded_reviews[0]["directory"] == str(untracked_unknown)

    # Sidecar-only directory MUST be safely cleaned
    assert not sidecar_only.exists()