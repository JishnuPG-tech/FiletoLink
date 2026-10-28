#!/usr/bin/env python3
"""
Automatically repair and verify Jellyfin CollectionFolder (library) rows in jellyfin.db.
Runs before Jellyfin starts to ensure ItemId / LibraryOptions resolve and
PhysicalLocationsList points directly to /data/jellyfin/media/... locations.
"""

import os
import sys
import json
import re
import shutil
import sqlite3
import datetime

TARGET_DATABASES = [
    "/opt/jellyfin-local/data/data/jellyfin.db",
    "/data/jellyfin/data/data/jellyfin.db",
]

PASSWORD_RESET_MARKERS = [
    "/data/jellyfin/.password_reset_done",
    "/opt/jellyfin-local/data/.password_reset_done",
]

MANUAL_RESET_TRIGGERS = [
    "/data/jellyfin/reset_password",
    "/opt/jellyfin-local/data/reset_password",
]

# name -> (item_id, views_dir_path, real_media_location, physical_folder_item_id)
#
# ItemId/LibraryOptions in /Library/VirtualFolders only resolve when the
# CollectionFolder row's Path EXACTLY matches the DefaultUserViewsPath
# subdirectory that Jellyfin enumerates on disk (~/root/default/<Name>),
# where the .mblink shortcut + options.xml live.
LIBRARIES = {
    "Movies": (
        "F137A2DD-21BB-C1B9-9AA5-C0F6BF02A805",
        "/opt/jellyfin-local/data/root/default/Movies",
        "/data/jellyfin/media/Movies",
        "4A909B35-F30D-3CD1-2E3B-26D3F8381922",
    ),
    "TV Shows": (
        "767BFFE4-F11C-93EF-34B8-05451A696A4E",
        "/opt/jellyfin-local/data/root/default/TV Shows",
        "/data/jellyfin/media/TV Shows",
        "0FDE567D-59EF-5D9F-D289-2A9F7CF53918",
    ),
}


def _download_art_sync(url: str, dest_path: str) -> bool:
    """Download authentic artwork synchronously with user-agent and size validation."""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status == 200:
                data = resp.read()
                if len(data) >= 5000:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    return True
    except Exception as e:
        print(f"[REPAIR] Note downloading art {url} -> {dest_path}: {e}")
    return False


def repair_database(db_path: str, marker_file: str | None = None, force_reset_password: bool | None = None) -> bool:
    if not os.path.exists(db_path):
        return False

    print(f"[REPAIR] Checking library collection paths in {db_path}...")
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.isolation_level = None
        cur = conn.cursor()

        # Check if BaseItems table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='BaseItems'")
        if not cur.fetchone():
            conn.close()
            return False

        repaired = 0
        conn.execute("BEGIN IMMEDIATE")
        for name, (item_id, views_path, media_path, folder_id) in LIBRARIES.items():
            cur.execute("SELECT Id, Path, Data FROM BaseItems WHERE Id = ?", (item_id,))
            row = cur.fetchone()
            if not row:
                # Fallback to search by Name
                cur.execute("SELECT Id, Path, Data FROM BaseItems WHERE Name = ? AND type LIKE '%CollectionFolder%'", (name,))
                row = cur.fetchone()
            if not row:
                print(f"[REPAIR] CollectionFolder '{name}' not found in {db_path}")
                continue

            row_id, current_path, row_data = row
            data = {}
            if row_data:
                try:
                    data = json.loads(row_data)
                except Exception:
                    data = {}

            locs = [ln for ln in (data.get("PhysicalLocationsList") or []) if "/data/root/" not in ln]
            needs_update = False

            if current_path != views_path:
                needs_update = True

            if media_path not in locs:
                locs.insert(0, media_path)
                needs_update = True

            if data.get("PhysicalFolderIds") != [folder_id]:
                data["PhysicalFolderIds"] = [folder_id]
                needs_update = True

            if needs_update:
                data["PhysicalLocationsList"] = locs
                now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
                data["DateLastSaved"] = now
                cur.execute(
                    "UPDATE BaseItems SET Path = ?, Data = ?, DateModified = ? WHERE Id = ?",
                    (views_path, json.dumps(data), now, row_id),
                )
                print(f"[REPAIR] Healed '{name}' ({row_id}): Path -> '{views_path}', Locations -> {locs}")
                repaired += 1

        # Purge invalid structural entries (e.g. legacy flat TV folder that breaks series resolution)
        cur.execute(
            "DELETE FROM BaseItems WHERE Path LIKE '%/TV Shows/English%' "
            "OR (Name = 'English' AND type LIKE '%Series%')"
        )
        purged = cur.rowcount
        if purged > 0:
            print(f"[REPAIR] Purged {purged} invalid structural item rows from {db_path}.")

        # Clean up orphaned rows whose media files do not exist on disk (prevents duplicate ghost items)
        cur.execute(
            "SELECT Id, Path, Name, type FROM BaseItems "
            "WHERE (Path LIKE '/data/jellyfin/media/%' OR Path LIKE '/opt/jellyfin-local/%' OR Path LIKE '/data/movies/%' OR Path LIKE '/data/tvshows/%') "
            "AND (type LIKE '%Movie%' OR type LIKE '%Episode%' OR type LIKE '%Series%' OR type LIKE '%Season%')"
        )
        orphaned = []
        for row_id, item_path, item_name, itype in cur.fetchall():
            if item_path and not os.path.exists(item_path):
                orphaned.append(row_id)
        if orphaned:
            cur.executemany("DELETE FROM BaseItems WHERE Id = ?", [(oid,) for oid in orphaned])
            print(f"[REPAIR] Removed {len(orphaned)} orphaned item row(s) whose files no longer exist on disk.")

        # Clean up duplicate Movie titles if any exist in BaseItems (e.g. duplicate Ne Zha 2)
        cur.execute(
            "SELECT Id, Path, Name FROM BaseItems WHERE type LIKE '%Movie%' AND Path IS NOT NULL"
        )
        seen_names = {}
        dup_to_delete = []
        for row_id, item_path, item_name in cur.fetchall():
            if not item_name:
                continue
            clean_name = item_name.strip().lower()
            exists = os.path.exists(item_path) if item_path else False
            if clean_name in seen_names:
                prev_id, prev_path, prev_exists = seen_names[clean_name]
                if not exists:
                    dup_to_delete.append(row_id)
                elif not prev_exists:
                    dup_to_delete.append(prev_id)
                    seen_names[clean_name] = (row_id, item_path, exists)
            else:
                seen_names[clean_name] = (row_id, item_path, exists)
        if dup_to_delete:
            cur.executemany("DELETE FROM BaseItems WHERE Id = ?", [(did,) for did in dup_to_delete])
            print(f"[REPAIR] Removed {len(dup_to_delete)} duplicate movie row(s) from {db_path}.")

        # Check and repair Users table: clear password and login attempt lockouts
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'")
        if cur.fetchone():
            cur.execute("PRAGMA table_info('Users')")
            user_cols = [c[1] for c in cur.fetchall()]
            if "Username" in user_cols and "Password" in user_cols:
                cur.execute("SELECT Id, Username, InvalidLoginAttemptCount, Password FROM Users")
                user_rows = cur.fetchall()
                for u_id, u_name, u_attempts, u_pwd in user_rows:
                    print(f"[AUTH] Found Jellyfin user '{u_name}' (locked_attempts={u_attempts}, has_password={bool(u_pwd)}) in {db_path}")

                db_dir = os.path.dirname(db_path)
                markers = [marker_file] if marker_file else list(PASSWORD_RESET_MARKERS)
                if not marker_file and db_dir:
                    markers.append(os.path.join(db_dir, ".password_reset_done"))

                marker_exists = any(os.path.exists(m) for m in markers)
                env_force = os.environ.get("RESET_JELLYFIN_PASSWORD", "").strip().lower() in ("1", "true", "yes")
                manual_trigger = any(os.path.exists(p) for p in MANUAL_RESET_TRIGGERS)

                if force_reset_password is not None:
                    should_reset = force_reset_password
                else:
                    should_reset = env_force or manual_trigger or (not marker_exists)

                if should_reset:
                    cur.execute("UPDATE Users SET Password = NULL, InvalidLoginAttemptCount = 0")
                    if user_rows:
                        print(f"[AUTH] Executed one-time password reset to blank for {len(user_rows)} user(s) in {db_path}. Sign in with a blank password is enabled.")
                    if marker_file:
                        try:
                            os.makedirs(os.path.dirname(marker_file), exist_ok=True)
                            with open(marker_file, "w", encoding="utf-8") as f:
                                f.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
                        except Exception:
                            pass
                else:
                    cur.execute("UPDATE Users SET InvalidLoginAttemptCount = 0")
                    print(f"[AUTH] Preserved user password(s); cleared failed attempt lockouts in {db_path}.")

            if "Data" in user_cols:
                cur.execute("SELECT Id, Data FROM Users")
                for u_id, u_data in cur.fetchall():
                    cfg = {}
                    if u_data:
                        try:
                            cfg = json.loads(u_data)
                        except Exception:
                            cfg = {}
                    user_cfg = cfg.setdefault("Configuration", {})
                    user_cfg["SubtitleMode"] = "Always"
                    user_cfg["SubtitleLanguagePreference"] = "en"
                    user_cfg["PlayDefaultAudioTrack"] = True

                    # Direct-Play Zero-Transcode Optimization
                    policy = cfg.setdefault("Policy", {})
                    policy["EnablePlaybackRemuxing"] = True
                    policy["EnableAudioPlaybackTranscoding"] = True
                    policy["EnableVideoPlaybackTranscoding"] = False

                    cfg["Configuration"] = user_cfg
                    cfg["Policy"] = policy
                    cur.execute("UPDATE Users SET Data = ? WHERE Id = ?", (json.dumps(cfg), u_id))
                    print(f"[AUTH] Configured direct play & subtitles (Zero-Transcode, SubtitleMode=Always) in DB for user Id={u_id}")

            # Unlock permissions if locked
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Permissions'")
            if cur.fetchone():
                try:
                    cur.execute("UPDATE Permissions SET Value = 0 WHERE Kind = 2")
                except Exception:
                    pass

        # Synchronize APEX_JELLYFIN_API_KEY into ApiKeys table if present
        api_key = os.environ.get("APEX_JELLYFIN_API_KEY", "").strip().strip('"')
        if api_key:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ApiKeys'")
            if cur.fetchone():
                try:
                    cur.execute("SELECT Id FROM ApiKeys WHERE AccessToken = ?", (api_key,))
                    if not cur.fetchone():
                        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
                        cur.execute(
                            "INSERT INTO ApiKeys (AccessToken, Name, DateCreated, DateLastActivity) VALUES (?, ?, ?, ?)",
                            (api_key, "Apex Gateway", now, now)
                        )
                        print(f"[AUTH] Registered APEX_JELLYFIN_API_KEY into ApiKeys table in {db_path}.")
                except Exception as ak_err:
                    print(f"[AUTH] Note inserting ApiKey: {ak_err}")

        conn.execute("COMMIT")
        conn.close()
        if repaired:
            print(f"[REPAIR] Successfully repaired {repaired} collection folder(s) in {db_path}.")
        else:
            print(f"[REPAIR] All collection folder paths in {db_path} are already correctly mapped.")
        return True
    except Exception as exc:
        print(f"[REPAIR] Error checking/repairing {db_path}: {exc}", file=sys.stderr)
        return False


def cleanup_empty_media_folders(roots=None):
    """Remove abandoned movie/show directories that contain no playable media files."""
    search_roots = roots or ["/data/jellyfin/media/Movies", "/data/jellyfin/media/TV Shows", "/opt/jellyfin-local/media"]
    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
            if dirpath == root_dir:
                continue
            media_files = [f for f in filenames if f.endswith((".strm", ".mp4", ".mkv", ".avi", ".ts"))]
            if not media_files and not dirnames:
                try:
                    shutil.rmtree(dirpath, ignore_errors=True)
                except Exception:
                    pass

    # Purge corrupt metadata library cache entries
    meta_roots = ["/opt/jellyfin-local/data/metadata/library", "/data/jellyfin/data/metadata/library"]
    for mroot in meta_roots:
        if not os.path.exists(mroot):
            continue
        for dirpath, _, _ in list(os.walk(mroot)):
            dir_l = os.path.basename(dirpath).lower()
            if "summer i turned pretty" in dir_l or "the summer i turned pretty" in dir_l or "what if (2024)" in dir_l:
                try:
                    shutil.rmtree(dirpath, ignore_errors=True)
                    print(f"[REPAIR] Purged stale metadata cache folder: {dirpath}")
                except Exception:
                    pass


def purge_plugin_databases():
    """Scan Jellyfin local and persistent data dirs for all plugin SQLite databases
    (e.g., IntroSkipper.db, SkipMe.db) and purge any queued or metadata rows referencing
    blacklisted items like Ms.Rose & Mr.Cane."""
    search_dirs = [
        "/opt/jellyfin-local/data",
        "/data/jellyfin/data",
    ]
    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        for root, _, files in os.walk(sdir):
            for f in files:
                if not f.endswith(".db"):
                    continue
                db_file = os.path.join(root, f)
                try:
                    conn = sqlite3.connect(db_file, timeout=5)
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [r[0] for r in cur.fetchall() if r[0] not in ("BaseItems", "sqlite_sequence")]
                    for tbl in tables:
                        cur.execute(f"PRAGMA table_info('{tbl}')")
                        cols = cur.fetchall()
                        text_cols = [
                            c[1] for c in cols
                            if any(t in str(c[2]).upper() for t in ("TEXT", "CHAR", "VARCHAR", "CLOB", "BLOB"))
                            or c[1].lower() in ("path", "name", "title", "itemname")
                        ]
                        for col in text_cols:
                            try:
                                cur.execute(
                                    f"DELETE FROM '{tbl}' WHERE \"{col}\" LIKE '%rose%cane%' "
                                    f"OR \"{col}\" LIKE '%ms.rose%' OR \"{col}\" LIKE '%ms rose%'"
                                )
                            except Exception:
                                pass
                    conn.commit()
                    conn.close()
                except Exception:
                    pass


def heal_subtitle_files(roots=None):
    """Purge 0-byte, corrupt, or invalid subtitle files that break Jellyfin SubtitleResolver."""
    search_roots = roots or [
        "/data/jellyfin/media/Movies",
        "/data/jellyfin/media/TV Shows",
        "/data/movies",
        "/data/tvshows",
        "/opt/jellyfin-local/media",
    ]
    purged = 0
    timestamp_re = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}")
    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                lower = fn.lower()
                if lower.endswith((".srt", ".vtt", ".sub", ".ass")):
                    full_p = os.path.join(dirpath, fn)
                    try:
                        sz = os.path.getsize(full_p)
                        is_broken_suffix = ".eng.0.srt" in lower or ".0.srt" in lower
                        is_invalid = False
                        if sz < 20 or is_broken_suffix:
                            is_invalid = True
                        else:
                            with open(full_p, "r", encoding="utf-8", errors="ignore") as sf:
                                sample = sf.read(4096)
                            if not timestamp_re.search(sample):
                                is_invalid = True
                            elif any(tag in sample.lower() for tag in ("<html", "<body", "cloudflare", "502 bad gateway", "404 not found")):
                                is_invalid = True
                        if is_invalid:
                            os.remove(full_p)
                            purged += 1
                            print(f"[REPAIR] Purged corrupt/empty subtitle file: {full_p}")
                    except Exception as err:
                        print(f"[REPAIR] Note cleaning subtitle {full_p}: {err}")
    if purged:
        print(f"[REPAIR] Purged {purged} corrupt/broken subtitle files across media directories.")


def heal_mismatched_media(roots=None, databases=None):
    """Clean folder/file release-size noise and purge misidentified metadata (e.g. Generation Iron on Iron Man 3)."""
    search_roots = roots or [
        "/data/jellyfin/media/Movies",
        "/data/jellyfin/media/TV Shows",
        "/data/movies",
        "/data/tvshows",
        "/opt/jellyfin-local/media",
    ]
    db_list = databases or TARGET_DATABASES
    size_re = re.compile(r"(?i)\b\d+(?:\.\d+)?\s*(?:mb|gb|kib|mib|gib|tb)\b")

    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue

        for dirpath, dirnames, filenames in list(os.walk(root_dir, topdown=True)):
            dirname = os.path.basename(dirpath)
            if not dirname or dirpath == root_dir:
                continue

            # 1. Rename directories containing release-size noise: "Iron Man 3 780Mb (2013)" -> "Iron Man 3 (2013)"
            if size_re.search(dirname):
                clean_name = size_re.sub("", dirname)
                clean_name = re.sub(r"\s+", " ", clean_name).strip(" -_.")
                if clean_name and clean_name != dirname:
                    parent_dir = os.path.dirname(dirpath)
                    new_dirpath = os.path.join(parent_dir, clean_name)
                    if not os.path.exists(new_dirpath):
                        try:
                            os.rename(dirpath, new_dirpath)
                            print(f"[REPAIR] Cleaned folder name: '{dirpath}' -> '{new_dirpath}'")
                            dirpath = new_dirpath
                            dirname = clean_name
                            try:
                                filenames = os.listdir(new_dirpath)
                            except Exception:
                                pass
                        except Exception as ren_err:
                            print(f"[REPAIR] Note renaming folder {dirpath}: {ren_err}")

            # 2. Rename .strm files inside directory that contain release-size noise
            for fn in list(filenames):
                if fn.endswith(".strm") and size_re.search(fn):
                    base_no_ext, ext = os.path.splitext(fn)
                    clean_strm_base = size_re.sub("", base_no_ext)
                    clean_strm_base = re.sub(r"\s+", " ", clean_strm_base).strip(" -_.")
                    if clean_strm_base and clean_strm_base != base_no_ext:
                        old_strm = os.path.join(dirpath, fn)
                        new_strm = os.path.join(dirpath, f"{clean_strm_base}{ext}")
                        if not os.path.exists(new_strm):
                            try:
                                os.rename(old_strm, new_strm)
                                print(f"[REPAIR] Cleaned strm file: '{fn}' -> '{clean_strm_base}{ext}'")
                                for db_p in db_list:
                                    if os.path.exists(db_p):
                                        try:
                                            conn = sqlite3.connect(db_p, timeout=5)
                                            conn.execute("UPDATE BaseItems SET Path = ? WHERE Path = ?", (new_strm, old_strm))
                                            conn.commit()
                                            conn.close()
                                        except Exception:
                                            pass
                            except Exception as strm_err:
                                print(f"[REPAIR] Note renaming strm {old_strm}: {strm_err}")

            # 3. Purge Generation Iron misidentification
            dir_lower = dirname.lower()
            is_gen_iron_folder = "generation iron" in dir_lower
            is_iron_man_folder = "iron" in dir_lower and "man" in dir_lower
            has_gen_iron = is_gen_iron_folder

            if is_iron_man_folder or is_gen_iron_folder:
                try:
                    curr_files = os.listdir(dirpath)
                except Exception:
                    curr_files = []
                for fn in curr_files:
                    if fn.lower().endswith(".nfo"):
                        nfo_p = os.path.join(dirpath, fn)
                        try:
                            with open(nfo_p, "r", encoding="utf-8", errors="ignore") as nf:
                                content = nf.read()
                            if "210879" in content or "generation iron" in content.lower() or "tt2205904" in content:
                                has_gen_iron = True
                                break
                        except Exception:
                            pass
                if has_gen_iron:
                    print(f"[REPAIR] Purging mismatched 'Generation Iron' metadata from '{dirpath}'...")
                    # If the folder on disk was named Generation Iron, rename to Iron Man 3 (2013)
                    if is_gen_iron_folder:
                        parent_d = os.path.dirname(dirpath)
                        im3_dir = os.path.join(parent_d, "Iron Man 3 (2013)")
                        for fn in list(curr_files):
                            if fn.lower().endswith(".strm"):
                                old_s = os.path.join(dirpath, fn)
                                new_s = os.path.join(dirpath, "Iron Man 3 (2013).strm")
                                if not os.path.exists(new_s):
                                    try:
                                        os.rename(old_s, new_s)
                                    except Exception:
                                        pass
                        if not os.path.exists(im3_dir):
                            try:
                                os.rename(dirpath, im3_dir)
                                dirpath = im3_dir
                                curr_files = os.listdir(dirpath)
                            except Exception:
                                pass

                    for fn in curr_files:
                        fn_l = fn.lower()
                        if fn_l.endswith((".nfo", ".srt", ".vtt", ".ass")) or fn_l in ("poster.jpg", "folder.jpg", "backdrop.jpg", "fanart.jpg", "landscape.jpg", "thumb.jpg", "logo.png", "clearlogo.png"):
                            try:
                                os.remove(os.path.join(dirpath, fn))
                            except Exception:
                                pass
                    for db_p in db_list:
                        if os.path.exists(db_p):
                            try:
                                conn = sqlite3.connect(db_p, timeout=5)
                                conn.execute("DELETE FROM BaseItems WHERE Name LIKE '%Generation Iron%' OR Data LIKE '%210879%' OR Path LIKE '%Generation Iron%'")
                                conn.commit()
                                try:
                                    conn.execute("UPDATE BaseItems SET Images = NULL WHERE Path LIKE '%Iron Man%'")
                                    conn.commit()
                                except Exception:
                                    pass
                                conn.close()
                            except Exception:
                                pass

                # If this is Iron Man 3 folder, ensure stale Generation Iron logo is purged so official Iron Man 3 logo is downloaded
                is_im3 = "iron" in dir_lower and "man" in dir_lower and ("3" in dir_lower or "2013" in dir_lower)
                if is_im3:
                    for fn in curr_files:
                        if fn.lower() in ("logo.png", "clearlogo.png"):
                            try:
                                os.remove(os.path.join(dirpath, fn))
                                print(f"[REPAIR] Purged stale logo from '{dirpath}' to force clean Iron Man 3 logo fetch.")
                            except Exception:
                                pass
                    for db_p in db_list:
                        if os.path.exists(db_p):
                            try:
                                conn = sqlite3.connect(db_p, timeout=5)
                                conn.execute("DELETE FROM BaseItems WHERE Name LIKE '%Generation Iron%' OR Data LIKE '%210879%'")
                                conn.commit()
                                try:
                                    conn.execute("UPDATE BaseItems SET Images = NULL WHERE Path LIKE '%Iron Man 3%'")
                                    conn.commit()
                                except Exception:
                                    pass
                                conn.close()
                            except Exception:
                                pass

            # 4. Heal Aadu 3 misidentification (e.g. wrongly identified as Aadu 1 or placed in Aadu (2015))
            has_aadu_3 = False
            for f in curr_files:
                fl = f.lower()
                if fl.endswith(".strm") and "aadu" in fl and ("3" in fl or "part" in fl):
                    has_aadu_3 = True
                    break
            if "aadu" in dir_lower and ("3" in dir_lower or "part" in dir_lower):
                has_aadu_3 = True

            if has_aadu_3:
                mismatched_aadu = False
                for fn in curr_files:
                    if fn.lower().endswith(".nfo"):
                        nfo_p = os.path.join(dirpath, fn)
                        try:
                            with open(nfo_p, "r", encoding="utf-8", errors="ignore") as nf:
                                content = nf.read()
                            if "324976" in content or "489709" in content or ("<title>Aadu</title>" in content and "<title>Aadu 3" not in content):
                                mismatched_aadu = True
                                break
                        except Exception:
                            pass
                is_wrong_dir = dirname in ("Aadu (2015)", "Aadu", "Aadu 2") or "/Movies/English" in dirpath
                if mismatched_aadu or is_wrong_dir:
                    print(f"[REPAIR] Healing Aadu 3 media from '{dirpath}'...")
                    target_aadu_dir = "/data/jellyfin/media/Movies/Malayalam/Aadu 3 Part 1 (2026)"
                    os.makedirs(target_aadu_dir, exist_ok=True)
                    for fn in list(curr_files):
                        if fn.lower().endswith(".strm"):
                            old_s = os.path.join(dirpath, fn)
                            new_s = os.path.join(target_aadu_dir, "Aadu 3 Part 1 (2026).strm")
                            if old_s != new_s:
                                try:
                                    if not os.path.exists(new_s):
                                        os.rename(old_s, new_s)
                                    else:
                                        os.remove(old_s)
                                    print(f"[REPAIR] Relocated Aadu 3 strm: '{old_s}' -> '{new_s}'")
                                except Exception as mv_err:
                                    print(f"[REPAIR] Error moving Aadu 3 strm: {mv_err}")
                    # Remove mismatched artwork/nfo from old directory
                    for fn in curr_files:
                        fn_l = fn.lower()
                        if fn_l.endswith((".nfo", ".srt", ".vtt", ".ass")) or fn_l in ("poster.jpg", "folder.jpg", "backdrop.jpg", "fanart.jpg", "landscape.jpg", "thumb.jpg"):
                            try:
                                os.remove(os.path.join(dirpath, fn))
                            except Exception:
                                pass
                    for db_p in db_list:
                        if os.path.exists(db_p):
                            try:
                                conn = sqlite3.connect(db_p, timeout=5)
                                conn.execute("DELETE FROM BaseItems WHERE Path LIKE '%Aadu 3%' OR (Path LIKE '%Aadu%' AND (Data LIKE '%324976%' OR Data LIKE '%489709%'))")
                                conn.commit()
                                conn.close()
                            except Exception:
                                pass

            # 5. Heal It: Welcome to Derry and purge accidental "The Summer I Turned Pretty" misidentification
            has_derry_strm = any("derry" in f.lower() for f in curr_files if f.lower().endswith(".strm"))
            is_summer_folder = "summer i turned pretty" in dir_lower or "the summer i turned pretty" in dir_lower
            is_derry_folder = "derry" in dir_lower or "welcome to derry" in dir_lower

            if is_summer_folder or has_derry_strm or (is_derry_folder and any("summer" in f.lower() for f in curr_files)):
                print(f"[REPAIR] Healing Derry / Summer I Turned Pretty from '{dirpath}'...")
                target_derry_root = "/data/jellyfin/media/TV Shows/It Welcome to Derry (2025)"
                target_derry_s1 = os.path.join(target_derry_root, "Season 01")
                os.makedirs(target_derry_s1, exist_ok=True)

                for fn in list(curr_files):
                    if fn.lower().endswith(".strm"):
                        old_s = os.path.join(dirpath, fn)
                        new_s = os.path.join(target_derry_s1, "It Welcome to Derry S01E01.strm")
                        if old_s != new_s:
                            try:
                                if not os.path.exists(new_s):
                                    os.rename(old_s, new_s)
                                else:
                                    os.remove(old_s)
                                print(f"[REPAIR] Relocated Derry strm: '{old_s}' -> '{new_s}'")
                            except Exception as mv_err:
                                print(f"[REPAIR] Error relocating Derry strm: {mv_err}")

                if is_summer_folder:
                    try:
                        shutil.rmtree(dirpath, ignore_errors=True)
                        print(f"[REPAIR] Removed corrupt 'The Summer I Turned Pretty' directory: {dirpath}")
                    except Exception as rm_err:
                        print(f"[REPAIR] Error removing corrupt Summer folder: {rm_err}")
                # Remove ANY stale artwork / logo / nfo from Derry show root and season dir to force clean fetch
                for clean_dir in (dirpath, target_derry_root, target_derry_s1):
                    if os.path.exists(clean_dir):
                        try:
                            for fn in os.listdir(clean_dir):
                                fn_l = fn.lower()
                                if fn_l.endswith((".nfo", ".srt", ".vtt", ".ass")) or fn_l.startswith("backdrop") or fn_l in ("poster.jpg", "folder.jpg", "fanart.jpg", "landscape.jpg", "thumb.jpg", "logo.png", "clearlogo.png"):
                                    try:
                                        os.remove(os.path.join(clean_dir, fn))
                                        print(f"[REPAIR] Purged stale Derry art/nfo: {fn} from {clean_dir}")
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                for db_p in db_list:
                    if os.path.exists(db_p):
                        try:
                            conn = sqlite3.connect(db_p, timeout=5)
                            conn.execute("DELETE FROM BaseItems WHERE Name LIKE '%Summer I Turned Pretty%' OR Path LIKE '%Summer I Turned Pretty%'")
                            conn.execute("DELETE FROM BaseItems WHERE Name LIKE '%Welcome to Derry%' OR Path LIKE '%Derry%'")
                            conn.execute("DELETE FROM BaseItems WHERE Path LIKE '%194766%' OR Data LIKE '%194766%'")
                            conn.commit()
                            conn.close()
                        except Exception as dbe:
                            print(f"[REPAIR] DB cleanup notice for Derry/Summer: {dbe}")

                # Atomically write authentic Derry tvshow.nfo
                derry_nfo_path = os.path.join(target_derry_root, "tvshow.nfo")
                derry_nfo_content = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<tvshow>
  <title>It: Welcome to Derry</title>
  <originaltitle>It: Welcome to Derry</originaltitle>
  <showtitle>It: Welcome to Derry</showtitle>
  <year>2025</year>
  <premiered>2025-10-01</premiered>
  <plot>Set in the world of Stephen King's IT, the prequel series expands the vision established in the feature films.</plot>
  <uniqueid type="imdb" default="true">tt19244304</uniqueid>
  <uniqueid type="tmdb">200875</uniqueid>
  <imdbid>tt19244304</imdbid>
  <tmdbid>200875</tmdbid>
  <genre>Drama</genre>
  <genre>Mystery</genre>
  <genre>Sci-Fi &amp; Fantasy</genre>
</tvshow>
"""
                try:
                    with open(derry_nfo_path, "w", encoding="utf-8") as f:
                        f.write(derry_nfo_content)
                    print(f"[REPAIR] Wrote authentic Derry tvshow.nfo: {derry_nfo_path}")
                except Exception as we:
                    print(f"[REPAIR] Error writing Derry tvshow.nfo: {we}")

                # Download authentic Derry poster and backdrop immediately
                derry_poster_url = "https://m.media-amazon.com/images/M/MV5BZWE0ZWM1MjUtNmYzYS00NzU3LTkxYmQtNmI3NTc0ZTY1NmVlXkEyXkFqcGc@._V1_.jpg"
                derry_backdrop_url = "https://images.metahub.space/background/medium/tt19244304/img"
                derry_p = os.path.join(target_derry_root, "poster.jpg")
                derry_b = os.path.join(target_derry_root, "backdrop.jpg")

                if _download_art_sync(derry_poster_url, derry_p):
                    for cp in ("folder.jpg", "thumb.jpg", "season01-poster.jpg", "season-all-poster.jpg"):
                        try:
                            shutil.copyfile(derry_p, os.path.join(target_derry_root, cp))
                        except Exception:
                            pass
                    try:
                        shutil.copyfile(derry_p, os.path.join(target_derry_s1, "folder.jpg"))
                        shutil.copyfile(derry_p, os.path.join(target_derry_s1, "poster.jpg"))
                    except Exception:
                        pass
                    print(f"[REPAIR] Downloaded authentic Derry poster to {derry_p}")

                if _download_art_sync(derry_backdrop_url, derry_b):
                    for cp in ("fanart.jpg", "landscape.jpg", "thumb.jpg"):
                        try:
                            shutil.copyfile(derry_b, os.path.join(target_derry_root, cp))
                        except Exception:
                            pass
                    print(f"[REPAIR] Downloaded authentic Derry backdrop to {derry_b}")

            # 6. Heal What If...? (2021) Marvel and purge Chinese Romance drama (2024, tt27122945)
            has_whatif_strm = any("what" in f.lower() and "if" in f.lower() for f in curr_files if f.lower().endswith(".strm"))
            is_whatif_2024 = "what if (2024)" in dir_lower or (("what if" in dir_lower or "what.if" in dir_lower) and "2024" in dirpath)
            is_whatif_folder = ("what if" in dir_lower or "what.if" in dir_lower) and "christmas" not in dir_lower

            has_chinese_meta = False
            for fn in curr_files:
                if fn.lower().endswith(".nfo"):
                    try:
                        with open(os.path.join(dirpath, fn), "r", encoding="utf-8", errors="ignore") as nff:
                            nfc = nff.read()
                        if "27122945" in nfc or "2024" in nfc or "xia guo" in nfc.lower():
                            has_chinese_meta = True
                            break
                    except Exception:
                        pass

            if is_whatif_2024 or has_chinese_meta or (is_whatif_folder and has_whatif_strm):
                print(f"[REPAIR] Healing What If...? media from '{dirpath}'...")
                target_whatif_root = "/data/jellyfin/media/TV Shows/What If (2021)"
                target_whatif_s1 = os.path.join(target_whatif_root, "Season 01")
                os.makedirs(target_whatif_s1, exist_ok=True)

                for fn in list(curr_files):
                    if fn.lower().endswith(".strm"):
                        old_s = os.path.join(dirpath, fn)
                        new_s = os.path.join(target_whatif_s1, "What If S01E01.strm")
                        if old_s != new_s:
                            try:
                                if not os.path.exists(new_s):
                                    os.rename(old_s, new_s)
                                else:
                                    os.remove(old_s)
                                print(f"[REPAIR] Relocated What If strm: '{old_s}' -> '{new_s}'")
                            except Exception as mv_err:
                                print(f"[REPAIR] Error relocating What If strm: {mv_err}")

                if is_whatif_2024 or has_chinese_meta:
                    for clean_dir in (dirpath, target_whatif_root, target_whatif_s1):
                        if os.path.exists(clean_dir):
                            try:
                                for fn in os.listdir(clean_dir):
                                    fn_l = fn.lower()
                                    if fn_l.endswith((".nfo", ".srt", ".vtt", ".ass")) or fn_l.startswith("backdrop") or fn_l in ("poster.jpg", "folder.jpg", "fanart.jpg", "landscape.jpg", "thumb.jpg", "logo.png", "clearlogo.png"):
                                        try:
                                            os.remove(os.path.join(clean_dir, fn))
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                    if is_whatif_2024:
                        try:
                            shutil.rmtree(dirpath, ignore_errors=True)
                            print(f"[REPAIR] Removed corrupt 'What If (2024)' folder: {dirpath}")
                        except Exception:
                            pass

                for db_p in db_list:
                    if os.path.exists(db_p):
                        try:
                            conn = sqlite3.connect(db_p, timeout=5)
                            conn.execute("DELETE FROM BaseItems WHERE (Name LIKE '%What If%' AND (Path LIKE '%2024%' OR Data LIKE '%27122945%'))")
                            conn.execute("DELETE FROM BaseItems WHERE Name LIKE '%What If%' OR Path LIKE '%What If%'")
                            conn.commit()
                            conn.close()
                        except Exception as dbe:
                            print(f"[REPAIR] DB cleanup notice for What If: {dbe}")

                # Atomically write authentic Marvel What If...? tvshow.nfo
                whatif_nfo_path = os.path.join(target_whatif_root, "tvshow.nfo")
                whatif_nfo_content = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<tvshow>
  <title>What If...?</title>
  <originaltitle>What If...?</originaltitle>
  <showtitle>What If...?</showtitle>
  <year>2021</year>
  <premiered>2021-08-11</premiered>
  <plot>Exploring pivotal moments from the Marvel Cinematic Universe and turning them on their head, leading the audience into uncharted territory.</plot>
  <uniqueid type="imdb" default="true">tt10168312</uniqueid>
  <uniqueid type="tmdb">91363</uniqueid>
  <imdbid>tt10168312</imdbid>
  <tmdbid>91363</tmdbid>
  <genre>Animation</genre>
  <genre>Action &amp; Adventure</genre>
  <genre>Sci-Fi &amp; Fantasy</genre>
</tvshow>
"""
                try:
                    with open(whatif_nfo_path, "w", encoding="utf-8") as f:
                        f.write(whatif_nfo_content)
                    print(f"[REPAIR] Wrote authentic What If tvshow.nfo: {whatif_nfo_path}")
                except Exception as we:
                    print(f"[REPAIR] Error writing What If tvshow.nfo: {we}")

                # Download authentic Marvel What If...? poster and backdrop immediately
                whatif_poster_url = "https://m.media-amazon.com/images/M/MV5BYWFiOTcwNzItMTg5Mi00ZTU4LThkZWYtYWNmZWQ1ODE5ZTVmXkEyXkFqcGc@._V1_.jpg"
                whatif_backdrop_url = "https://images.metahub.space/background/medium/tt10168312/img"
                whatif_p = os.path.join(target_whatif_root, "poster.jpg")
                whatif_b = os.path.join(target_whatif_root, "backdrop.jpg")

                if _download_art_sync(whatif_poster_url, whatif_p):
                    for cp in ("folder.jpg", "thumb.jpg", "season01-poster.jpg", "season-all-poster.jpg"):
                        try:
                            shutil.copyfile(whatif_p, os.path.join(target_whatif_root, cp))
                        except Exception:
                            pass
                    try:
                        shutil.copyfile(whatif_p, os.path.join(target_whatif_s1, "folder.jpg"))
                        shutil.copyfile(whatif_p, os.path.join(target_whatif_s1, "poster.jpg"))
                    except Exception:
                        pass
                    print(f"[REPAIR] Downloaded authentic What If poster to {whatif_p}")

                if _download_art_sync(whatif_backdrop_url, whatif_b):
                    for cp in ("fanart.jpg", "landscape.jpg", "thumb.jpg"):
                        try:
                            shutil.copyfile(whatif_b, os.path.join(target_whatif_root, cp))
                        except Exception:
                            pass
                    print(f"[REPAIR] Downloaded authentic What If backdrop to {whatif_b}")


def repair_user_subtitle_preferences(configs=None):
    """Ensure user profile config XML files have SubtitleMode set to Always so
    subtitles automatically appear when playing any video."""
    search_dirs = configs or [
        "/opt/jellyfin-local/config/users",
        "/data/jellyfin/config/users",
    ]
    for udir in search_dirs:
        if not os.path.exists(udir):
            continue
        for root, _, files in os.walk(udir):
            for fn in files:
                if fn.lower() == "config.xml":
                    cfg_p = os.path.join(root, fn)
                    try:
                        with open(cfg_p, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        changed = False
                        if "<SubtitleMode>" in content:
                            new_content = re.sub(
                                r"<SubtitleMode>.*?</SubtitleMode>",
                                "<SubtitleMode>Always</SubtitleMode>",
                                content
                            )
                            if new_content != content:
                                content = new_content
                                changed = True
                        elif "</UserConfiguration>" in content:
                            content = content.replace(
                                "</UserConfiguration>",
                                "  <SubtitleMode>Always</SubtitleMode>\n</UserConfiguration>"
                            )
                            changed = True

                        if "<SubtitleLanguagePreference>" in content:
                            new_content = re.sub(
                                r"<SubtitleLanguagePreference>.*?</SubtitleLanguagePreference>",
                                "<SubtitleLanguagePreference>en</SubtitleLanguagePreference>",
                                content
                            )
                            if new_content != content:
                                content = new_content
                                changed = True
                        elif "</UserConfiguration>" in content:
                            content = content.replace(
                                "</UserConfiguration>",
                                "  <SubtitleLanguagePreference>en</SubtitleLanguagePreference>\n</UserConfiguration>"
                            )
                            changed = True

                        if changed:
                            with open(cfg_p, "w", encoding="utf-8") as f:
                                f.write(content)
                            print(f"[REPAIR] Enabled SubtitleMode=Always in {cfg_p}")
                    except Exception as e:
                        print(f"[REPAIR] Note configuring user subtitles in {cfg_p}: {e}")


def repair_user_policy_preferences(configs=None):
    """Ensure user policy.xml prioritizes direct-play and stream remuxing over heavy CPU video transcoding."""
    search_dirs = configs or [
        "/opt/jellyfin-local/config/users",
        "/data/jellyfin/config/users",
    ]
    for udir in search_dirs:
        if not os.path.exists(udir):
            continue
        for root, _, files in os.walk(udir):
            for fn in files:
                if fn.lower() == "policy.xml":
                    p_path = os.path.join(root, fn)
                    try:
                        with open(p_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        changed = False
                        if "<EnablePlaybackRemuxing>" in content:
                            new_content = re.sub(r"<EnablePlaybackRemuxing>.*?</EnablePlaybackRemuxing>", "<EnablePlaybackRemuxing>true</EnablePlaybackRemuxing>", content)
                            if new_content != content: content = new_content; changed = True
                        elif "</UserPolicy>" in content:
                            content = content.replace("</UserPolicy>", "  <EnablePlaybackRemuxing>true</EnablePlaybackRemuxing>\n</UserPolicy>")
                            changed = True

                        if "<EnableAudioPlaybackTranscoding>" in content:
                            new_content = re.sub(r"<EnableAudioPlaybackTranscoding>.*?</EnableAudioPlaybackTranscoding>", "<EnableAudioPlaybackTranscoding>true</EnableAudioPlaybackTranscoding>", content)
                            if new_content != content: content = new_content; changed = True
                        elif "</UserPolicy>" in content:
                            content = content.replace("</UserPolicy>", "  <EnableAudioPlaybackTranscoding>true</EnableAudioPlaybackTranscoding>\n</UserPolicy>")
                            changed = True

                        if "<EnableVideoPlaybackTranscoding>" in content:
                            new_content = re.sub(r"<EnableVideoPlaybackTranscoding>.*?</EnableVideoPlaybackTranscoding>", "<EnableVideoPlaybackTranscoding>false</EnableVideoPlaybackTranscoding>", content)
                            if new_content != content: content = new_content; changed = True
                        elif "</UserPolicy>" in content:
                            content = content.replace("</UserPolicy>", "  <EnableVideoPlaybackTranscoding>false</EnableVideoPlaybackTranscoding>\n</UserPolicy>")
                            changed = True

                        if changed:
                            with open(p_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            print(f"[REPAIR] Optimized direct-play policy in {p_path}")
                    except Exception as e:
                        print(f"[REPAIR] Note configuring user policy in {p_path}: {e}")


def repair_system_xml(configs=None):
    """Ensure system.xml has IsStartupWizardCompleted set to true so Jellyfin never
    redirects to first-time setup or blocks user login."""
    targets = configs or [
        "/opt/jellyfin-local/config/system.xml",
        "/data/jellyfin/config/system.xml",
    ]
    for cfg in targets:
        if not os.path.exists(cfg):
            continue
        try:
            with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            changed = False
            if "<IsStartupWizardCompleted>" in content:
                if "<IsStartupWizardCompleted>false</IsStartupWizardCompleted>" in content:
                    content = content.replace(
                        "<IsStartupWizardCompleted>false</IsStartupWizardCompleted>",
                        "<IsStartupWizardCompleted>true</IsStartupWizardCompleted>"
                    )
                    changed = True
            elif "</SystemConfiguration>" in content:
                content = content.replace(
                    "</SystemConfiguration>",
                    "  <IsStartupWizardCompleted>true</IsStartupWizardCompleted>\n</SystemConfiguration>"
                )
                changed = True
            if changed:
                with open(cfg, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[REPAIR] Ensured IsStartupWizardCompleted=true in {cfg}")
        except Exception as e:
            print(f"[REPAIR] Note repairing {cfg}: {e}")


def main():
    env_force = os.environ.get("RESET_JELLYFIN_PASSWORD", "").strip().lower() in ("1", "true", "yes")
    manual_trigger = any(os.path.exists(p) for p in MANUAL_RESET_TRIGGERS)
    marker_exists = any(os.path.exists(m) for m in PASSWORD_RESET_MARKERS)
    should_reset = env_force or manual_trigger or (not marker_exists)

    for db in TARGET_DATABASES:
        repair_database(db, force_reset_password=should_reset)

    if should_reset:
        for m in PASSWORD_RESET_MARKERS:
            try:
                os.makedirs(os.path.dirname(m), exist_ok=True)
                with open(m, "w", encoding="utf-8") as f:
                    f.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
            except Exception:
                pass
        for manual_file in MANUAL_RESET_TRIGGERS:
            try:
                if os.path.exists(manual_file):
                    os.remove(manual_file)
            except Exception:
                pass

    purge_plugin_databases()
    cleanup_empty_media_folders()
    heal_subtitle_files()
    heal_mismatched_media()
    repair_user_subtitle_preferences()
    repair_user_policy_preferences()
    repair_system_xml()


if __name__ == "__main__":
    main()
