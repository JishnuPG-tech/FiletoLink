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