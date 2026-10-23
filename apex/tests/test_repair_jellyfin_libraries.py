import sqlite3
import os
import shutil
import tempfile
import pytest

from repair_jellyfin_libraries import repair_database, cleanup_empty_media_folders, repair_system_xml


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
