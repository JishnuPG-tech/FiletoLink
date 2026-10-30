import sqlite3
import os
import shutil
import tempfile
import pytest

from repair_jellyfin_libraries import (
    deduplicate_media_strms,
    repair_database,
    cleanup_empty_media_folders,
    heal_subtitle_files,
    heal_mismatched_media,
    heal_channel_and_db_names,
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


def test_orphan_cleanup_safeguards_unmanaged_and_virtual_paths(tmp_path):
    """Ensure orphan cleanup strictly targets managed media paths that are missing,
    and NEVER purges virtual views, plugin streams, or unmanaged paths."""
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

    managed_media = tmp_path / "media" / "Movies" / "Existent (2025)"
    managed_media.mkdir(parents=True)
    valid_file = managed_media / "Existent (2025).strm"
    valid_file.write_text("http://stream/1")

    missing_managed = str(tmp_path / "media" / "Movies" / "Missing (2025)" / "Missing (2025).strm")

    test_items = [
        ("id-valid", str(valid_file), "Existent Movie", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("id-missing", missing_managed, "Missing Movie", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("id-virtual-col", "/data/jellyfin/data/collections/Movies", "Movies", "MediaBrowser.Controller.Entities.CollectionFolder"),
        ("id-http-stream", "http://external.stream/movie.m3u8", "External Stream", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("id-plugin-stream", "plugin://plugin.video.youtube/play/?video_id=xyz", "Plugin Stream", "MediaBrowser.Controller.Entities.Movies.Movie"),
        ("id-unmanaged-file", "/etc/jellyfin/system.xml", "System Config", "MediaBrowser.Controller.Entities.Movies.Movie"),
    ]

    for item_id, path, name, itype in test_items:
        cur.execute(
            "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, path, name, itype, "{}", "2026-10-28T00:00:00Z")
        )
    conn.commit()
    conn.close()

    # Run repair database
    repair_database(str(db_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id, Path FROM BaseItems")
    remaining_ids = {row[0] for row in cur.fetchall()}
    conn.close()

    # The missing managed media item must be pruned
    assert "id-missing" not in remaining_ids

    # All virtual, external, plugin, unmanaged, and existing media items MUST be preserved
    for item_id in ("id-valid", "id-virtual-col", "id-http-stream", "id-plugin-stream", "id-unmanaged-file"):
        assert item_id in remaining_ids, f"Item {item_id} was unexpectedly purged!"


def test_cleanup_empty_media_folders_preserves_legitimate_metadata_cache(tmp_path):
    """Ensure metadata cache folders for titles like Summer I Turned Pretty or What If (2024)
    are preserved when they contain valid cache files."""
    meta_root = tmp_path / "metadata" / "library"
    summer_cache = meta_root / "The Summer I Turned Pretty (2022)"
    whatif_cache = meta_root / "What If (2024)"
    empty_cache = meta_root / "Empty Abandoned"
    summer_cache.mkdir(parents=True)
    whatif_cache.mkdir(parents=True)
    empty_cache.mkdir(parents=True)

    (summer_cache / "poster.jpg").write_bytes(b"summer art")
    (whatif_cache / "backdrop.jpg").write_bytes(b"whatif art")

    # Mock TARGET_DATABASES and run cleanup
    cleanup_empty_media_folders(roots=[str(tmp_path / "media")])

    # Summer I Turned Pretty and What If metadata caches MUST be preserved
    assert summer_cache.exists()
    assert (summer_cache / "poster.jpg").exists()
    assert whatif_cache.exists()
    assert (whatif_cache / "backdrop.jpg").exists()


def test_duplicate_path_cleanup_preserves_structural_and_collection_rows(tmp_path):
    """Ensure duplicate path cleanup strictly deduplicates playable media items,
    and preserves structural and collection folder entries."""
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

    shared_media_dir = tmp_path / "media" / "Movies" / "Movie A (2025)"
    shared_media_dir.mkdir(parents=True)
    shared_strm = shared_media_dir / "Movie A (2025).strm"
    shared_strm.write_text("http://stream/a")

    # Insert two duplicates pointing to the same strm file
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("mov-dup-1", str(shared_strm), "Movie A", "MediaBrowser.Controller.Entities.Movies.Movie", "{}", "2026-10-28T00:00:00Z")
    )
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("mov-dup-2", str(shared_strm), "Movie A", "MediaBrowser.Controller.Entities.Movies.Movie", "{}", "2026-10-28T00:00:00Z")
    )

    # Insert structural CollectionFolder and Series folder
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("col-folder", "/data/jellyfin/data/collections/Movies", "Movies", "MediaBrowser.Controller.Entities.CollectionFolder", "{}", "2026-10-28T00:00:00Z")
    )
    cur.execute(
        "INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?, ?)",
        ("series-english", str(tmp_path / "media" / "TV Shows" / "English (2022)"), "English", "MediaBrowser.Controller.Entities.TV.Series", "{}", "2026-10-28T00:00:00Z")
    )
    conn.commit()
    conn.close()

    # Create the series directory so it is existent on disk
    (tmp_path / "media" / "TV Shows" / "English (2022)").mkdir(parents=True)

    repair_database(str(db_file))

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id, Name FROM BaseItems")
    items = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    # Structural CollectionFolder must be preserved
    assert "col-folder" in items
    # Series named English must NOT be purged
    assert "series-english" in items
    assert items["series-english"] == "English"
    # Exactly one Movie A duplicate must be retained
    assert ("mov-dup-1" in items) ^ ("mov-dup-2" in items)


def test_cleanup_empty_media_folders_never_deletes_non_empty_unrecognized_formats(tmp_path):
    """Ensure cleanup_empty_media_folders never deletes a folder that contains user files (.txt, .xml, .bin)."""
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Folder with unrecognized media format or download artifact
    folder_with_unrecognized = movies_root / "Unknown Format Movie"
    folder_with_unrecognized.mkdir()
    (folder_with_unrecognized / "movie.bin").write_bytes(b"arbitrary binary media")

    # Folder with user text notes (e.g. info.txt)
    folder_with_txt = movies_root / "User Notes Movie"
    folder_with_txt.mkdir()
    (folder_with_txt / "notes.txt").write_text("personal user notes")

    # Folder with xml data (e.g. custom.xml)
    folder_with_xml = movies_root / "Custom XML Movie"
    folder_with_xml.mkdir()
    (folder_with_xml / "data.xml").write_text("<data>user xml</data>")

    cleanup_empty_media_folders(roots=[str(movies_root)])

    # All folders and their files MUST be preserved
    assert folder_with_unrecognized.exists()
    assert (folder_with_unrecognized / "movie.bin").exists()
    assert folder_with_txt.exists()
    assert (folder_with_txt / "notes.txt").exists()
    assert folder_with_xml.exists()
    assert (folder_with_xml / "data.xml").exists()


def test_heal_channel_names_and_database(tmp_path):
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Create folder and strm with WMR and double-year
    folder = movies_root / "WMR Iron Man (2008) (2008)"
    folder.mkdir()
    strm = folder / "WMR Iron Man (2008) (2008).strm"
    strm.write_text("http://stream/1")
    nfo = folder / "movie.nfo"
    nfo.write_text("<movie><title>@WMR Iron Man (2008)</title><originaltitle>@WMR Iron Man</originaltitle></movie>")

    db_file = tmp_path / "jellyfin.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE BaseItems (
            Id TEXT PRIMARY KEY,
            Path TEXT,
            Name TEXT,
            CleanName TEXT,
            type TEXT
        )
    """)
    cur.execute("INSERT INTO BaseItems VALUES (?, ?, ?, ?, ?)", (
        "item-ironman", str(strm), "@WM...", "@WM...", "MediaBrowser.Controller.Entities.Movies.Movie"
    ))
    conn.commit()
    conn.close()

    heal_mismatched_media(roots=[str(movies_root)], databases=[str(db_file)])
    heal_channel_and_db_names(databases=[str(db_file)])

    # Directory was renamed
    healed_folder = movies_root / "Iron Man (2008)"
    assert healed_folder.exists()
    assert not folder.exists()
    assert (healed_folder / "Iron Man (2008).strm").exists()

    # NFO was healed
    healed_nfo_text = (healed_folder / "movie.nfo").read_text()
    assert "<title>Iron Man</title>" in healed_nfo_text
    assert "@" not in healed_nfo_text
    assert "WMR" not in healed_nfo_text

    # Database name was healed
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Name, CleanName, Path FROM BaseItems WHERE Id = ?", ("item-ironman",))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "Iron Man"
    assert "@" not in row[0]
    assert "WMR" not in row[0]


def test_heal_mismatched_media_merges_into_existing_destination(tmp_path):
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Existing clean folder
    clean_folder = movies_root / "Iron Man (2008)"
    clean_folder.mkdir()
    clean_strm = clean_folder / "Iron Man (2008).strm"
    clean_strm.write_text("http://stream/clean")

    # Legacy folder with different year drift: "Iron Man (2008) (2016)"
    drift_folder = movies_root / "Iron Man (2008) (2016)"
    drift_folder.mkdir()
    drift_sub = drift_folder / "Iron Man (2008).eng.srt"
    drift_sub.write_text("1\n00:00:01,000 --> 00:00:02,000\nSubtitle\n")

    heal_mismatched_media(roots=[str(movies_root)], databases=[])

    # Drift folder must be merged into clean_folder and rmdir'd
    assert clean_folder.exists()
    assert clean_strm.exists()
    assert (clean_folder / "Iron Man (2008).eng.srt").exists()
    assert not drift_folder.exists()









def test_deduplicate_media_strms_removes_duplicate_folders_and_db_rows(tmp_path):
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Canonical movie
    canon_dir = movies_root / "Spider-Man Brand New Day (2026)"
    canon_dir.mkdir()
    canon_strm = canon_dir / "Spider-Man Brand New Day (2026).strm"
    canon_strm.write_text("http://stream/119/video.mp4")

    # Duplicate movie with noisy prefix
    dup_dir = movies_root / "Man Brand New Day (2026)"
    dup_dir.mkdir()
    dup_strm = dup_dir / "Man Brand New Day (2026).strm"
    dup_strm.write_text("http://stream/119/video.mp4")

    # Setup test DB
    db_file = tmp_path / "jellyfin.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE BaseItems (
            Id TEXT PRIMARY KEY,
            Path TEXT,
            Name TEXT,
            type TEXT
        )
    """)
    cur.execute("INSERT INTO BaseItems VALUES ('id1', ?, 'Spider-Man', 'Movie')", (str(canon_strm),))
    cur.execute("INSERT INTO BaseItems VALUES ('id2', ?, 'Spider-Man', 'Movie')", (str(canon_dir),))
    cur.execute("INSERT INTO BaseItems VALUES ('id3', ?, 'Man', 'Movie')", (str(dup_strm),))
    cur.execute("INSERT INTO BaseItems VALUES ('id4', ?, 'Man', 'Movie')", (str(dup_dir),))
    conn.commit()
    conn.close()

    deduplicate_media_strms(roots=[str(movies_root)], databases=[str(db_file)])

    assert canon_dir.exists()
    assert canon_strm.exists()
    assert not dup_dir.exists()
    assert not dup_strm.exists()

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Path FROM BaseItems")
    paths = [r[0] for r in cur.fetchall()]
    conn.close()

    assert str(canon_strm) in paths
    assert str(dup_strm) not in paths
    assert str(dup_dir) not in paths

def test_deduplicate_media_strms_normalizes_title_variants(tmp_path):
    """Ensure duplicate movie folders with differing punctuation, case, or year are deduplicated."""
    movies_root = tmp_path / "Movies"
    movies_root.mkdir()

    # Folder 1: Spider-Man Far From Home (2019)
    dir1 = movies_root / "Spider-Man Far From Home (2019)"
    dir1.mkdir()
    strm1 = dir1 / "Spider-Man Far From Home (2019).strm"
    strm1.write_text("http://127.0.0.1:8082/stream/111", encoding="utf-8")

    # Folder 2: Spider-Man: Far from Home
    dir2 = movies_root / "Spider-Man: Far from Home"
    dir2.mkdir()
    strm2 = dir2 / "Spider-Man Far from Home.strm"
    strm2.write_text("http://127.0.0.1:8082/stream/222", encoding="utf-8")

    # DB with both rows
    db_file = tmp_path / "jellyfin.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE BaseItems (
            Id TEXT PRIMARY KEY,
            Path TEXT,
            Name TEXT,
            type TEXT
        )
    """)
    cur.execute("INSERT INTO BaseItems VALUES ('id_canon', ?, 'Spider-Man: Far From Home', 'MediaBrowser.Controller.Entities.Movies.Movie')", (str(strm1),))
    cur.execute("INSERT INTO BaseItems VALUES ('id_dup', ?, 'Spider-Man: Far from Home', 'MediaBrowser.Controller.Entities.Movies.Movie')", (str(strm2),))
    conn.commit()
    conn.close()

    deduplicate_media_strms(roots=[str(movies_root)], databases=[str(db_file)])

    # Exactly one folder and one DB item should remain
    assert dir1.exists() != dir2.exists()

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT Id FROM BaseItems")
    remaining_ids = [r[0] for r in cur.fetchall()]
    conn.close()

    assert len(remaining_ids) == 1
    assert 'id_canon' in remaining_ids

