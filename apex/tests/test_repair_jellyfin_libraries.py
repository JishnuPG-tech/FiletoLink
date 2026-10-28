import sqlite3
import os
import shutil
import tempfile
import pytest

from repair_jellyfin_libraries import (
    repair_database,
    cleanup_empty_media_folders,
    heal_subtitle_files,
    heal_mismatched_media,
    repair_user_subtitle_preferences,
    repair_user_policy_preferences,
    repair_system_xml,
)


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


def test_repair_database_resets_user_password_and_unlocks(tmp_path, monkeypatch):
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
    cur.execute("""
        CREATE TABLE Users (
            Id TEXT PRIMARY KEY,
            Username TEXT,
            Password TEXT,
            InvalidLoginAttemptCount INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE Permissions (
            UserId TEXT,
            Kind INTEGER,
            Value INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE ApiKeys (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            AccessToken TEXT,
            Name TEXT,
            DateCreated TEXT,
            DateLastActivity TEXT
        )
    """)
    cur.execute(
        "INSERT INTO Users VALUES (?, ?, ?, ?)",
        ("user-1", "admin", "$PBKDF2$hash123", 5)
    )
    cur.execute(
        "INSERT INTO Permissions VALUES (?, ?, ?)",
        ("user-1", 2, 1)
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("APEX_JELLYFIN_API_KEY", "test-api-token-xyz")
    repair_database(str(db_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Username, Password, InvalidLoginAttemptCount FROM Users")
    u_row = cur.fetchone()
    assert u_row[0] == "admin"
    assert u_row[1] is None  # Blank password
    assert u_row[2] == 0  # Lockout cleared

    cur.execute("SELECT Value FROM Permissions WHERE Kind = 2")
    p_row = cur.fetchone()
    assert p_row[0] == 0  # Unlocked

    cur.execute("SELECT AccessToken, Name FROM ApiKeys")
    ak_row = cur.fetchone()
    assert ak_row[0] == "test-api-token-xyz"
    assert ak_row[1] == "Apex Gateway"
    conn.close()


def test_repair_database_subsequent_boot_preserves_password(tmp_path):
    db_file = tmp_path / "jellyfin.db"
    marker_file = tmp_path / ".password_reset_done"
    marker_file.write_text("2026-10-23T00:00:00Z")

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
    cur.execute("""
        CREATE TABLE Users (
            Id TEXT PRIMARY KEY,
            Username TEXT,
            Password TEXT,
            InvalidLoginAttemptCount INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE Permissions (
            UserId TEXT,
            Kind INTEGER,
            Value INTEGER
        )
    """)
    cur.execute(
        "INSERT INTO Users VALUES (?, ?, ?, ?)",
        ("user-1", "admin", "$PBKDF2$custom_password_hash", 3)
    )
    cur.execute(
        "INSERT INTO Permissions VALUES (?, ?, ?)",
        ("user-1", 2, 1)
    )
    conn.commit()
    conn.close()

    # Repair with existing marker: password must be preserved, lockout cleared, unlocked
    repair_database(str(db_file), marker_file=str(marker_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Username, Password, InvalidLoginAttemptCount FROM Users")
    u_row = cur.fetchone()
    assert u_row[0] == "admin"
    assert u_row[1] == "$PBKDF2$custom_password_hash"  # Preserved!
    assert u_row[2] == 0  # Lockout cleared

    cur.execute("SELECT Value FROM Permissions WHERE Kind = 2")
    p_row = cur.fetchone()
    assert p_row[0] == 0  # Unlocked
    conn.close()


def test_repair_database_manual_force_reset_env(tmp_path, monkeypatch):
    db_file = tmp_path / "jellyfin.db"
    marker_file = tmp_path / ".password_reset_done"
    marker_file.write_text("2026-10-23T00:00:00Z")

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE BaseItems (Id TEXT, Path TEXT, Name TEXT, type TEXT, Data TEXT, DateModified TEXT)")
    cur.execute("CREATE TABLE Users (Id TEXT, Username TEXT, Password TEXT, InvalidLoginAttemptCount INTEGER)")
    cur.execute("CREATE TABLE Permissions (UserId TEXT, Kind INTEGER, Value INTEGER)")
    cur.execute("INSERT INTO Users VALUES ('user-1', 'admin', '$PBKDF2$somehash', 2)")
    conn.commit()
    conn.close()

    monkeypatch.setenv("RESET_JELLYFIN_PASSWORD", "true")
    repair_database(str(db_file), marker_file=str(marker_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Username, Password, InvalidLoginAttemptCount FROM Users")
    u_row = cur.fetchone()
    assert u_row[1] is None  # Reset to blank because force env was set
    conn.close()


def test_repair_system_xml(tmp_path):
    cfg_file = tmp_path / "system.xml"
    cfg_file.write_text("<SystemConfiguration><IsStartupWizardCompleted>false</IsStartupWizardCompleted></SystemConfiguration>")

    repair_system_xml(configs=[str(cfg_file)])

    content = cfg_file.read_text()
    assert "<IsStartupWizardCompleted>true</IsStartupWizardCompleted>" in content


def test_heal_subtitle_files_purges_corrupt_files(tmp_path):
    movie_dir = tmp_path / "Iron Man (2008)"
    movie_dir.mkdir()

    # 0-byte broken file
    f0 = movie_dir / "Iron Man (2008).eng.0.srt"
    f0.write_text("")
    # corrupt forced file
    ff = movie_dir / "Iron Man (2008).eng.forced.srt"
    ff.write_text("broken content without timestamp")
    # valid file
    fv = movie_dir / "Iron Man (2008).eng.srt"
    fv.write_text("1\n00:00:01,000 --> 00:00:03,000\nValid line\n")

    heal_subtitle_files(roots=[str(tmp_path)])

    assert not f0.exists()
    assert not ff.exists()
    assert fv.exists()


def test_repair_user_subtitle_preferences(tmp_path):
    user_dir = tmp_path / "users" / "admin"
    user_dir.mkdir(parents=True)
    cfg_file = user_dir / "config.xml"
    cfg_file.write_text("<UserConfiguration><SubtitleMode>Default</SubtitleMode></UserConfiguration>")

    repair_user_subtitle_preferences(configs=[str(tmp_path / "users")])

    content = cfg_file.read_text()
    assert "<SubtitleMode>Always</SubtitleMode>" in content
    assert "<SubtitleLanguagePreference>en</SubtitleLanguagePreference>" in content


def test_repair_user_policy_preferences(tmp_path):
    user_dir = tmp_path / "users" / "admin"
    user_dir.mkdir(parents=True)
    policy_file = user_dir / "policy.xml"
    policy_file.write_text("<UserPolicy><EnableVideoPlaybackTranscoding>true</EnableVideoPlaybackTranscoding></UserPolicy>")

    repair_user_policy_preferences(configs=[str(tmp_path / "users")])

    content = policy_file.read_text()
    assert "<EnableVideoPlaybackTranscoding>false</EnableVideoPlaybackTranscoding>" in content
    assert "<EnablePlaybackRemuxing>true</EnablePlaybackRemuxing>" in content
    assert "<EnableAudioPlaybackTranscoding>true</EnableAudioPlaybackTranscoding>" in content


def test_heal_mismatched_media_cleans_noise_and_updates_db_path(tmp_path):
    movies_dir = tmp_path / "media" / "Movies" / "English"
    movies_dir.mkdir(parents=True)

    # 1. Directory with size noise: "Iron Man 3 780Mb (2013)"
    im3_dir = movies_dir / "Iron Man 3 780Mb (2013)"
    im3_dir.mkdir()
    strm_file = im3_dir / "Iron Man 3 780Mb (2013).strm"
    strm_file.write_text("http://localhost:8080/stream/123")
    nfo_file = im3_dir / "movie.nfo"
    nfo_file.write_text("<movie><title>Iron Man 3</title><tmdbid>68721</tmdbid></movie>")
    poster_file = im3_dir / "poster.jpg"
    poster_file.write_bytes(b"poster bytes")

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
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("im3-id", str(strm_file), "Iron Man 3", "MediaBrowser.Controller.Entities.Movies.Movie", '{"tmdb_id": 68721}', "2026-10-24T00:00:00Z")
    )
    conn.commit()
    conn.close()

    # Run heal_mismatched_media
    heal_mismatched_media(roots=[str(movies_dir)], databases=[str(db_file)])

    # Directory and strm must be cleaned of size noise
    clean_dir = movies_dir / "Iron Man 3 (2013)"
    assert clean_dir.exists()
    assert not im3_dir.exists()
    clean_strm = clean_dir / "Iron Man 3 (2013).strm"
    assert clean_strm.exists()
    assert clean_strm.read_text() == "http://localhost:8080/stream/123"

    # Sidecars are preserved non-destructively
    assert (clean_dir / "movie.nfo").exists()
    assert (clean_dir / "poster.jpg").exists()

    # In database, the item must be preserved and its Path updated to the cleaned .strm path
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id, Name, Path FROM BaseItems")
    rows = cur.fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == "im3-id"
    assert rows[0][1] == "Iron Man 3"
    assert rows[0][2] == str(clean_strm)


def test_legitimate_media_preserved_during_repair(tmp_path):
    """Ensure legitimate titles like Generation Iron, What If, The Summer I Turned Pretty,
    It: Welcome to Derry, and Aadu 3 are never purged by repair routines."""
    media_root = tmp_path / "media"
    movies_dir = media_root / "Movies"
    tv_dir = media_root / "TV Shows"
    movies_dir.mkdir(parents=True)
    tv_dir.mkdir(parents=True)

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

    test_titles = [
        ("gen-iron-id", movies_dir / "Generation Iron (2013)", "Generation Iron (2013).strm", "Generation Iron", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("what-if-id", movies_dir / "What If (2024)", "What If (2024).strm", "What If", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("summer-id", tv_dir / "The Summer I Turned Pretty (2022)" / "Season 1", "The Summer I Turned Pretty - S01E01.strm", "The Summer I Turned Pretty", "MediaBrowser.Controller.Entities.TV.Episode"),
        ("derry-id", tv_dir / "It Welcome to Derry (2025)" / "Season 1", "It Welcome to Derry - S01E01.strm", "It: Welcome to Derry", "MediaBrowser.Controller.Entities.TV.Episode"),
        ("aadu3-id", movies_dir / "Aadu 3 (2026)", "Aadu 3 (2026).strm", "Aadu 3", "MediaBrowser.Controller.Entities.Movies.Movie"),
    ]

    for item_id, folder, strm_name, name, itype in test_titles:
        folder.mkdir(parents=True, exist_ok=True)
        strm_path = folder / strm_name
        strm_path.write_text("http://stream/" + item_id)
        nfo_path = folder / "movie.nfo"
        nfo_path.write_text(f"<item><title>{name}</title></item>")
        poster_path = folder / "poster.jpg"
        poster_path.write_bytes(b"dummy poster")

        cur.execute(
            "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, str(strm_path), name, itype, "{}", "2026-10-28T00:00:00Z")
        )

    conn.commit()
    conn.close()

    # Execute all repair procedures
    heal_mismatched_media(roots=[str(media_root)], databases=[str(db_file)])
    cleanup_empty_media_folders(roots=[str(movies_dir), str(tv_dir)])
    repair_database(str(db_file))

    # Verify that all media files, sidecars, and database rows are 100% intact
    for item_id, folder, strm_name, name, itype in test_titles:
        strm_path = folder / strm_name
        assert strm_path.exists(), f"STRM file missing for {name}: {strm_path}"
        assert (folder / "movie.nfo").exists(), f"NFO missing for {name}"
        assert (folder / "poster.jpg").exists(), f"Poster missing for {name}"

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id, Name FROM BaseItems")
    db_items = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    for item_id, _, _, name, _ in test_titles:
        assert item_id in db_items, f"BaseItems row was unexpectedly purged for {name} ({item_id})"
        assert db_items[item_id] == name



