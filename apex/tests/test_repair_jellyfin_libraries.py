import sqlite3
import os
import shutil
import tempfile
import pytest

from repair_jellyfin_libraries import repair_database, cleanup_empty_media_folders


def test_repair_database_removes_orphans_and_duplicates(tmp_path):
    db_file = tmp_path / "jellyfin.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE BaseItems (
            Id TEXT PRIMARY KEY,
            Path TEXT,
            Name TEXT,
            type TEXT,
            Data TEXT,
            DateModified TEXT
        )
    """)

    # Valid media file
    media_dir = tmp_path / "media" / "Movies" / "Ne Zha 2 (2025)"
    media_dir.mkdir(parents=True)
    valid_file = media_dir / "Ne Zha 2 (2025).strm"
    valid_file.write_text("http://stream")

    # Stale/orphaned media path (does not exist on disk)
    stale_path = str(tmp_path / "media" / "Movies" / "English" / "Ne Zha 2 (2025)" / "Ne Zha 2 (2025).strm")

    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("item-valid", str(valid_file), "Ne Zha 2", "MediaBrowser.Controller.Entities.Movies.Movie", "{}", "2026-09-27T00:00:00Z")
    )
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("item-stale", stale_path, "Ne Zha 2", "MediaBrowser.Controller.Entities.Movies.Movie", "{}", "2026-09-27T00:00:00Z")
    )
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("item-blacklisted", "/data/jellyfin/media/Movies/Rose and Cane.strm", "Ms.Rose & Mr.Cane", "MediaBrowser.Controller.Entities.Movies.Movie", "{}", "2026-09-27T00:00:00Z")
    )
    conn.commit()
    conn.close()

    # Run repair
    repair_database(str(db_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id, Name, Path FROM BaseItems")
    remaining = cur.fetchall()
    conn.close()

    # Only the valid file remains; stale orphan and blacklisted must be purged
    assert len(remaining) == 1
    assert remaining[0][0] == "item-valid"
    assert remaining[0][1] == "Ne Zha 2"


def test_cleanup_empty_media_folders(tmp_path):
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Empty movie dir
    empty_movie = movies_root / "English" / "Ne Zha 2 (2025)"
    empty_movie.mkdir(parents=True)
    (empty_movie / "movie.nfo").write_text("<movie/>")  # sidecar only, no video

    # Valid movie dir with .strm
    valid_movie = movies_root / "Chinese" / "Ne Zha 2 (2025)"
    valid_movie.mkdir(parents=True)
    (valid_movie / "Ne Zha 2 (2025).strm").write_text("http://stream")

    # Run cleanup
    cleanup_empty_media_folders(roots=[str(movies_root)])

    assert not empty_movie.exists()
    assert valid_movie.exists()
