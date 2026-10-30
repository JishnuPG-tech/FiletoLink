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

        # Safe structural check: clean legacy flat TV collection folder row only if the legacy directory no longer exists on disk
        legacy_flat_paths = ('/data/jellyfin/media/TV Shows/English', '/opt/jellyfin-local/media/TV Shows/English')
        for lp in legacy_flat_paths:
            if not os.path.exists(lp):
                cur.execute(
                    "DELETE FROM BaseItems WHERE Path = ? AND type LIKE '%CollectionFolder%'",
                    (lp,)
                )

        # Clean up orphaned rows whose media files do not exist on disk (prevents duplicate ghost items).
        # Safeguard: strictly verify that path is a managed media file path (within library roots with media extensions)
        # to ensure external pointers, virtual views, and unmanaged paths are never pruned.
        managed_roots = [
            "/data/jellyfin/media",
            "/opt/jellyfin-local/media",
            "/data/movies",
            "/data/tvshows",
        ]
        db_parent = os.path.dirname(os.path.abspath(db_path))
        test_media = os.path.join(db_parent, "media")
        if os.path.isdir(test_media):
            managed_roots.append(test_media)

        norm_managed_roots = tuple(os.path.normpath(r).lower() + os.sep for r in managed_roots)
        media_exts = (".strm", ".mp4", ".mkv", ".avi", ".ts", ".mov", ".wmv", ".m4v", ".webm")

        cur.execute(
            "SELECT Id, Path, Name, type FROM BaseItems "
            "WHERE Path IS NOT NULL AND Path NOT LIKE 'http://%' AND Path NOT LIKE 'https://%' AND Path NOT LIKE 'plugin://%' "
            "AND (type LIKE '%Movie%' OR type LIKE '%Episode%')"
        )
        orphaned = []
        for row_id, item_path, item_name, itype in cur.fetchall():
            if not item_path or not (item_path.startswith("/") or os.path.isabs(item_path)):
                continue
            norm_item = os.path.normpath(item_path).lower()
            if not any(norm_item.startswith(r) for r in norm_managed_roots):
                continue
            if not norm_item.endswith(media_exts):
                continue
            if not os.path.exists(item_path):
                orphaned.append(row_id)

        if orphaned:
            cur.executemany("DELETE FROM BaseItems WHERE Id = ?", [(oid,) for oid in orphaned])
            print(f"[REPAIR] Removed {len(orphaned)} orphaned item row(s) whose files no longer exist on disk.")

        # Deduplicate identical database rows pointing to the exact same file path on disk
        # Restricted strictly to playable media items (Movies and Episodes) so structural,
        # CollectionFolder, and library entities are preserved.
        cur.execute(
            "SELECT Id, Path, type FROM BaseItems "
            "WHERE Path IS NOT NULL AND (type LIKE '%Movie%' OR type LIKE '%Episode%')"
        )
        seen_paths = set()
        dup_to_delete = []
        for row_id, item_path, itype in cur.fetchall():
            if not item_path:
                continue
            norm_p = os.path.normpath(item_path).lower()
            if not norm_p.endswith(media_exts):
                continue
            if norm_p in seen_paths:
                dup_to_delete.append(row_id)
            else:
                seen_paths.add(norm_p)
        if dup_to_delete:
            cur.executemany("DELETE FROM BaseItems WHERE Id = ?", [(did,) for did in dup_to_delete])
            print(f"[REPAIR] Removed {len(dup_to_delete)} duplicate row(s) pointing to identical paths from {db_path}.")

        # Permanent disk + DB deduplication for Movie directories
        movies_dir = "/data/jellyfin/media/Movies"
        if os.path.isdir(movies_dir):
            seen_movie_keys = {}
            for lang in os.listdir(movies_dir):
                lang_path = os.path.join(movies_dir, lang)
                if not os.path.isdir(lang_path):
                    continue
                for movie_folder in sorted(os.listdir(lang_path)):
                    folder_path = os.path.join(lang_path, movie_folder)
                    if not os.path.isdir(folder_path):
                        continue
                    strm_files = [f for f in os.listdir(folder_path) if f.endswith('.strm')]
                    strm_url = None
                    if strm_files:
                        try:
                            with open(os.path.join(folder_path, strm_files[0]), 'r', encoding='utf-8', errors='ignore') as sf:
                                strm_url = sf.read().strip()
                        except Exception:
                            pass
                    norm_k = re.sub(r'^(linkz|the)', '', movie_folder, flags=re.I)
                    norm_k = re.sub(r'\(\d{4}\)', '', norm_k)
                    norm_k = re.sub(r'[^a-zA-Z0-9]', '', norm_k).lower()

                    key = strm_url if strm_url else (norm_k if norm_k else None)
                    if key:
                        if key in seen_movie_keys:
                            existing_folder = seen_movie_keys[key]
                            is_curr_worse = 'linkz' in movie_folder.lower() or 'man brand' in movie_folder.lower()
                            to_delete = folder_path if is_curr_worse else existing_folder
                            to_keep = existing_folder if is_curr_worse else folder_path
                            print(f"[REPAIR] Duplicate movie detected: keeping '{to_keep}', deleting duplicate '{to_delete}'")
                            shutil.rmtree(to_delete, ignore_errors=True)
                            cur.execute("DELETE FROM BaseItems WHERE Path LIKE ?", (to_delete + '%',))
                            seen_movie_keys[key] = to_keep
                        else:
                            seen_movie_keys[key] = folder_path

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
                if marker_file:
                    markers = [marker_file]
                elif any(db_path.startswith(p) for p in ("/data/jellyfin", "/opt/jellyfin-local")):
                    markers = list(PASSWORD_RESET_MARKERS)
                    if db_dir:
                        markers.append(os.path.join(db_dir, ".password_reset_done"))
                else:
                    markers = [os.path.join(db_dir, ".password_reset_done")] if db_dir else []

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
    """Safely remove genuinely empty movie/show directories using os.rmdir (non-recursive).
    Restricts metadata cleanup strictly to confirmed application-generated NFOs (movie.nfo, tvshow.nfo)
    in managed directories; user files (.txt, .xml, etc.) are never deleted."""
    search_roots = roots or ["/data/jellyfin/media/Movies", "/data/jellyfin/media/TV Shows", "/opt/jellyfin-local/media"]
    all_media_exts = (
        ".strm", ".mp4", ".mkv", ".avi", ".ts", ".mov", ".wmv",
        ".m4v", ".webm", ".flv", ".iso", ".mpg", ".mpeg", ".m2ts"
    )
    known_app_nfo = {"movie.nfo", "tvshow.nfo"}

    for root_dir in search_roots:
        if not os.path.exists(root_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
            if dirpath == root_dir:
                continue
            has_media = any(f.lower().endswith(all_media_exts) for f in filenames)
            if not has_media and not dirnames:
                # If directory has ONLY confirmed application-generated NFO metadata, clean those
                if filenames and all(f.lower() in known_app_nfo for f in filenames):
                    for sf in filenames:
                        try:
                            os.remove(os.path.join(dirpath, sf))
                        except Exception:
                            pass
                # Prefer safe os.rmdir() when the directory is actually empty (never recursive)
                try:
                    os.rmdir(dirpath)
                except OSError:
                    pass

    # Clean up empty metadata library cache entries
    meta_roots = ["/opt/jellyfin-local/data/metadata/library", "/data/jellyfin/data/metadata/library"]
    for mroot in meta_roots:
        if not os.path.exists(mroot):
            continue
        for dirpath, dirnames, filenames in os.walk(mroot, topdown=False):
            if dirpath == mroot:
                continue
            if not dirnames and not filenames:
                try:
                    os.rmdir(dirpath)
                except Exception:
                    pass


def purge_plugin_databases():
    """No-op safety stub: title-based plugin database purges have been completely eliminated."""
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


CHANNEL_PREFIX_RE = re.compile(
    r"(?i)^(?:@(?:[a-z0-9]+)(?:[._-](?:movies|cinema|films|channel|linkz|official|hub|club|media|drive|hd|store|flim))?[._\s-]*|@[a-z0-9_]+\s*|(?:wmr|wm|mm\s*linkz|tamilmv|tamilblasters|1tamilmv)\s+)"
)


def _sanitize_media_title(text: str) -> str:
    """Strip channel prefixes, handles, and clean duplicate years."""
    if not text:
        return ""
    s = text.strip()
    while True:
        m = CHANNEL_PREFIX_RE.match(s)
        if not m:
            break
        s = s[m.end():].strip()
    s = re.sub(r"(?i)\b(?:wmr|wm|mm\s*linkz|tamilmv|tamilblasters|1tamilmv)\b[._\s-]*", "", s).strip()
    s = re.sub(r"^[^\w]+", "", s).strip()
    # Normalize multiple years like "Title (2008) (2016)" -> "Title (2008)"
    years = re.findall(r"\((\d{4})\)", s)
    if len(years) >= 2:
        y = years[0]
        s = re.sub(r"\s*\(\d{4}\)", "", s).strip()
        s = f"{s} ({y})"
    return s.strip()


def _heal_nfo_file(nfo_path: str):
    """Clean corrupted/channel-prefixed <title> and <originaltitle> in NFO files."""
    if not os.path.isfile(nfo_path):
        return
    try:
        with open(nfo_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        changed = False
        tm = re.search(r"<title>(.*?)</title>", content)
        if tm:
            t_val = tm.group(1)
            clean_t = _sanitize_media_title(t_val)
            clean_t = re.sub(r"\s*\(\d{4}\)$", "", clean_t).strip()
            if clean_t and clean_t != t_val:
                content = content.replace(f"<title>{t_val}</title>", f"<title>{clean_t}</title>")
                changed = True
        om = re.search(r"<originaltitle>(.*?)</originaltitle>", content)
        if om:
            o_val = om.group(1)
            clean_o = _sanitize_media_title(o_val)
            clean_o = re.sub(r"\s*\(\d{4}\)$", "", clean_o).strip()
            if clean_o and clean_o != o_val:
                content = content.replace(f"<originaltitle>{o_val}</originaltitle>", f"<originaltitle>{clean_o}</originaltitle>")
                changed = True
        if changed:
            with open(nfo_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[REPAIR] Healed titles in NFO: {nfo_path}")
    except Exception as e:
        print(f"[REPAIR] Note healing NFO {nfo_path}: {e}")


def heal_mismatched_media(roots=None, databases=None):
    """Clean folder/file release-size noise and channel prefixes non-destructively and update DB paths."""
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

            # 1. Rename directories containing release-size or channel prefix noise
            clean_name = dirname
            if size_re.search(clean_name):
                clean_name = size_re.sub("", clean_name)
            clean_name = _sanitize_media_title(clean_name)
            clean_name = re.sub(r"\s+", " ", clean_name).strip(" -_.")
            if clean_name and clean_name != dirname:
                parent_dir = os.path.dirname(dirpath)
                new_dirpath = os.path.join(parent_dir, clean_name)
                if not os.path.exists(new_dirpath):
                    try:
                        os.rename(dirpath, new_dirpath)
                        print(f"[REPAIR] Cleaned folder name: '{dirpath}' -> '{new_dirpath}'")
                        for db_p in db_list:
                            if os.path.exists(db_p):
                                try:
                                    conn = sqlite3.connect(db_p, timeout=5)
                                    cur = conn.cursor()
                                    cur.execute("SELECT Id, Path FROM BaseItems WHERE Path LIKE ?", (dirpath + "%",))
                                    for row_id, p in cur.fetchall():
                                        updated_p = new_dirpath + p[len(dirpath):]
                                        conn.execute("UPDATE BaseItems SET Path = ? WHERE Id = ?", (updated_p, row_id))
                                    conn.commit()
                                    conn.close()
                                except Exception:
                                    pass
                        dirpath = new_dirpath
                        dirname = clean_name
                        try:
                            filenames = os.listdir(new_dirpath)
                        except Exception:
                            pass
                    except Exception as ren_err:
                        print(f"[REPAIR] Note renaming folder {dirpath}: {ren_err}")
                else:
                    # Destination folder already exists; merge non-conflicting files and clean empty legacy folder
                    try:
                        for f in os.listdir(dirpath):
                            src_f = os.path.join(dirpath, f)
                            dst_f = os.path.join(new_dirpath, f)
                            if not os.path.exists(dst_f):
                                shutil.move(src_f, dst_f)
                                for db_p in db_list:
                                    if os.path.exists(db_p):
                                        try:
                                            conn = sqlite3.connect(db_p, timeout=5)
                                            conn.execute("UPDATE BaseItems SET Path = ? WHERE Path = ?", (dst_f, src_f))
                                            conn.commit()
                                            conn.close()
                                        except Exception:
                                            pass
                            elif f.endswith(".strm"):
                                try:
                                    if not os.path.exists(dst_f):
                                        shutil.copy2(src_f, dst_f)
                                    elif not os.path.exists(src_f):
                                        try:
                                            os.link(dst_f, src_f)
                                        except OSError:
                                            shutil.copy2(dst_f, src_f)
                                except Exception:
                                    pass
                        try:
                            os.rmdir(dirpath)
                            print(f"[REPAIR] Merged legacy duplicate folder: '{dirpath}' -> '{new_dirpath}'")
                        except OSError:
                            pass
                    except Exception as merge_err:
                        print(f"[REPAIR] Note merging duplicate folder {dirpath}: {merge_err}")

            # 2. Rename .strm files inside directory and heal NFOs
            for fn in list(filenames):
                if fn.endswith(".strm"):
                    base_no_ext, ext = os.path.splitext(fn)
                    clean_strm_base = base_no_ext
                    if size_re.search(clean_strm_base):
                        clean_strm_base = size_re.sub("", clean_strm_base)
                    clean_strm_base = _sanitize_media_title(clean_strm_base)
                    clean_strm_base = re.sub(r"\s+", " ", clean_strm_base).strip(" -_.")
                    if clean_strm_base and clean_strm_base != base_no_ext:
                        old_strm = os.path.join(dirpath, fn)
                        new_strm = os.path.join(dirpath, f"{clean_strm_base}{ext}")
                        if not os.path.exists(new_strm):
                            try:
                                try:
                                    os.link(old_strm, new_strm)
                                except OSError:
                                    shutil.copy2(old_strm, new_strm)
                                print(f"[REPAIR] Created clean alias strm: '{fn}' -> '{clean_strm_base}{ext}'")
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
                                print(f"[REPAIR] Note creating strm alias {old_strm}: {strm_err}")
                elif fn.lower() in ("movie.nfo", "tvshow.nfo"):
                    _heal_nfo_file(os.path.join(dirpath, fn))


def heal_channel_and_db_names(databases=None):
    """Directly sanitize BaseItems.Name and CleanName in Jellyfin databases."""
    db_list = databases or TARGET_DATABASES
    for db_p in db_list:
        if not os.path.exists(db_p):
            continue
        try:
            conn = sqlite3.connect(db_p, timeout=10)
            conn.isolation_level = None
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='BaseItems'")
            if not cur.fetchone():
                conn.close()
                continue

            cur.execute(
                "SELECT Id, Name, Path, type FROM BaseItems "
                "WHERE (type LIKE '%Movie%' OR type LIKE '%Episode%' OR type LIKE '%Series%')"
            )
            rows = cur.fetchall()
            updated = 0
            for row_id, name, path, itype in rows:
                if not name:
                    continue
                name_str = str(name).strip()
                needs_clean = (
                    name_str.startswith("@")
                    or name_str.lower().startswith("wmr")
                    or name_str.lower().startswith("wm ")
                    or name_str.lower().startswith("mm linkz")
                    or bool(re.search(r"\(\d{4}\)\s*\(\d{4}\)", name_str))
                )
                if needs_clean:
                    candidate = name_str
                    if "..." in name_str and path:
                        parts = [p for p in path.replace("\\", "/").split("/") if p]
                        for part in reversed(parts):
                            p_clean = os.path.splitext(part)[0]
                            if not p_clean.lower().endswith((".strm", ".mkv", ".mp4", ".avi")):
                                candidate = p_clean
                                break
                    clean_name = _sanitize_media_title(candidate)
                    clean_name = re.sub(r"\s*\(\d{4}\)$", "", clean_name).strip()
                    if clean_name and clean_name != name_str:
                        cur.execute("UPDATE BaseItems SET Name = ? WHERE Id = ?", (clean_name, row_id))
                        try:
                            cur.execute("UPDATE BaseItems SET CleanName = ? WHERE Id = ?", (clean_name, row_id))
                        except Exception:
                            pass
                        updated += 1
                        print(f"[REPAIR] Healed BaseItems.Name: '{name_str}' -> '{clean_name}' (Id={row_id})")
            conn.close()
            if updated:
                print(f"[REPAIR] Healed {updated} BaseItems name(s) in {db_p}")
        except Exception as e:
            print(f"[REPAIR] Error healing BaseItems names in {db_p}: {e}")


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
            import re
            if "<ServerName>" in content:
                if not re.search(r"<ServerName>Apex</ServerName>", content):
                    content = re.sub(r"<ServerName>[^<]*</ServerName>", "<ServerName>Apex</ServerName>", content)
                    changed = True
            elif "</SystemConfiguration>" in content:
                content = content.replace(
                    "</SystemConfiguration>",
                    "  <ServerName>Apex</ServerName>\n</SystemConfiguration>"
                )
                changed = True

            if changed:
                with open(cfg, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"[REPAIR] Ensured IsStartupWizardCompleted=true in {cfg}")
        except Exception as e:
            print(f"[REPAIR] Note repairing {cfg}: {e}")



def heal_missing_db_strm_paths(databases=None):
    """Ensures every single .strm path recorded in Jellyfin BaseItems actually exists on disk.
    If a file is missing due to prior pruning or dot/dash naming differences, reconstructs
    or hardlinks it immediately from matching media on disk."""
    db_list = databases or TARGET_DATABASES
    for db_p in db_list:
        if not os.path.exists(db_p):
            continue
        try:
            conn = sqlite3.connect(db_p, timeout=10)
            cur = conn.cursor()
            cur.execute("SELECT Id, Path, Name FROM BaseItems WHERE Path LIKE '%.strm'")
            rows = cur.fetchall()
            repaired = 0
            for row_id, path, name in rows:
                if not path or os.path.exists(path):
                    continue
                parent_dir = os.path.dirname(path)
                file_name = os.path.basename(path)
                found_src = None

                # 1. Search in the same parent directory for any .strm
                if os.path.isdir(parent_dir):
                    candidates = [os.path.join(parent_dir, f) for f in os.listdir(parent_dir) if f.lower().endswith(".strm")]
                    if candidates:
                        found_src = candidates[0]

                # 2. If parent_dir doesn't exist, search grandparent directory for a matching folder
                if not found_src:
                    grandparent = os.path.dirname(parent_dir)
                    parent_name = os.path.basename(parent_dir)
                    if os.path.isdir(grandparent):
                        norm_parent = re.sub(r"[^a-zA-Z0-9]", "", parent_name).lower()
                        for sib in os.listdir(grandparent):
                            sib_path = os.path.join(grandparent, sib)
                            if os.path.isdir(sib_path):
                                if re.sub(r"[^a-zA-Z0-9]", "", sib).lower() == norm_parent:
                                    cands = [os.path.join(sib_path, f) for f in os.listdir(sib_path) if f.lower().endswith(".strm")]
                                    if cands:
                                        found_src = cands[0]
                                        break

                if found_src and os.path.exists(found_src):
                    os.makedirs(parent_dir, exist_ok=True)
                    try:
                        os.link(found_src, path)
                    except OSError:
                        shutil.copy2(found_src, path)
                    repaired += 1
                    print(f"[REPAIR] Healed missing DB STRM: '{path}' <- '{found_src}'")
            conn.close()
            if repaired:
                print(f"[REPAIR] Successfully healed {repaired} missing STRM file(s) for DB {db_p}")
        except Exception as e:
            print(f"[REPAIR] Note healing missing DB STRMs: {e}")


def deduplicate_media_strms(roots=None, databases=None):
    """
    Deduplicates .strm files and folders on disk, and removes duplicate rows from Jellyfin BaseItems.
    When multiple folders or .strm files point to the exact same stream URL, or share the exact same
    normalized movie/show title, picks the canonical version, deletes duplicate folders/files from disk,
    and removes redundant rows from BaseItems in jellyfin.db.
    """
    media_roots = roots or [
        "/data/jellyfin/media/Movies",
        "/data/jellyfin/media/TV Shows",
        "/opt/jellyfin-local/media/Movies",
        "/opt/jellyfin-local/media/TV Shows",
    ]
    db_list = databases or TARGET_DATABASES

    def normalize_title(s: str) -> str:
        cleaned = re.sub(r"\s*\(\s*\d{4}\s*\)\s*", "", s or "")
        return re.sub(r"[^a-z0-9]", "", cleaned.lower())

    def score_path(p: str) -> int:
        score = 0
        bname = os.path.basename(p)
        parent = os.path.basename(os.path.dirname(p))
        lower_p = p.lower()
        for bad in ("linkz", "www.", "t.me", "telegram", "sample", "trailer"):
            if bad in lower_p:
                score -= 50
        if re.search(r"\(\d{4}\)", parent) or re.search(r"\(\d{4}\)", bname):
            score += 20
        if "-" in parent:
            score += 10
        if "." in parent or "," in parent:
            score += 5
        if re.search(r"\bIT\b", p):
            score += 15
        score += min(len(parent), 30)
        return score

    all_deleted_paths = []
    all_deleted_dirs = []

    for root_dir in media_roots:
        if not os.path.isdir(root_dir):
            continue

        # 1. Deduplicate by identical stream URL inside .strm files
        url_map = {}
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                if fn.lower().endswith(".strm"):
                    fp = os.path.join(dirpath, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            url = f.read().strip()
                        if url:
                            url_map.setdefault(url, []).append(fp)
                    except Exception:
                        pass

        for url, filepaths in url_map.items():
            if len(filepaths) <= 1:
                continue
            filepaths.sort(key=score_path, reverse=True)
            canonical = filepaths[0]
            duplicates = filepaths[1:]

            for dup in duplicates:
                dup_dir = os.path.dirname(dup)
                canon_dir = os.path.dirname(canonical)
                if dup_dir != canon_dir and dup_dir != root_dir:
                    print(f"[DEDUP] Removing duplicate media folder: '{dup_dir}' (retaining '{canon_dir}')")
                    try:
                        shutil.rmtree(dup_dir, ignore_errors=True)
                        all_deleted_dirs.append(dup_dir)
                    except Exception as e:
                        print(f"[DEDUP] Error removing folder {dup_dir}: {e}")
                else:
                    print(f"[DEDUP] Removing duplicate media file: '{dup}' (retaining '{canonical}')")
                    try:
                        if os.path.exists(dup):
                            os.remove(dup)
                    except Exception as e:
                        print(f"[DEDUP] Error removing file {dup}: {e}")
                all_deleted_paths.append(dup)

        # 2. Deduplicate media folders matching the same normalized title (strictly for Movies)
        if "movie" in root_dir.lower():
            folder_groups = {}
            try:
                for dirpath, dirnames, filenames in os.walk(root_dir):
                    if dirpath == root_dir:
                        continue
                    bname = os.path.basename(dirpath)
                    # Ignore language top-level categories
                    if bname.lower() in ("english", "malayalam", "tamil", "telugu", "hindi", "kannada", "korean", "chinese", "japanese"):
                        continue
                    # Match leaf movie directories or folders containing media files
                    if any(fn.lower().endswith((".strm", ".nfo", ".mp4", ".mkv", ".avi")) for fn in filenames) or not dirnames:
                        norm_k = normalize_title(bname)
                        if norm_k:
                            folder_groups.setdefault(norm_k, []).append(dirpath)
            except Exception:
                pass

            for norm_k, fpaths in folder_groups.items():
                if len(fpaths) <= 1:
                    continue
                def score_folder(p: str) -> int:
                    s = score_path(p)
                    try:
                        for sub_f in os.listdir(p):
                            if sub_f.lower().endswith(".strm") and os.path.getsize(os.path.join(p, sub_f)) > 0:
                                s += 100
                                break
                    except Exception:
                        pass
                    return s
                fpaths.sort(key=score_folder, reverse=True)
                canon_folder = fpaths[0]
                for dup_folder in fpaths[1:]:
                    if dup_folder in all_deleted_dirs:
                        continue
                    print(f"[DEDUP] Removing duplicate media folder by title: '{dup_folder}' (retaining '{canon_folder}')")
                    try:
                        shutil.rmtree(dup_folder, ignore_errors=True)
                        all_deleted_dirs.append(dup_folder)
                    except Exception as e:
                        print(f"[DEDUP] Error removing folder {dup_folder}: {e}")

        # 3. Detect duplicate episodes in the same Season folder matching SxxExx
        ep_map = {}
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                if fn.lower().endswith(".strm"):
                    m = re.search(r"(?i)S(\d+)E(\d+)", fn)
                    if m:
                        key = (os.path.normpath(dirpath), m.group(1), m.group(2))
                        fp = os.path.join(dirpath, fn)
                        ep_map.setdefault(key, []).append(fp)

        for key, filepaths in ep_map.items():
            if len(filepaths) <= 1:
                continue
            filepaths.sort(key=score_path, reverse=True)
            canonical = filepaths[0]
            for dup in filepaths[1:]:
                if dup in all_deleted_paths:
                    continue
                print(f"[DEDUP] Removing duplicate episode file: '{dup}' (retaining '{canonical}')")
                try:
                    if os.path.exists(dup):
                        os.remove(dup)
                except Exception as e:
                    print(f"[DEDUP] Error removing episode file {dup}: {e}")
                all_deleted_paths.append(dup)

    for db_p in db_list:
        if not os.path.exists(db_p):
            continue
        try:
            conn = sqlite3.connect(db_p, timeout=10)
            cur = conn.cursor()
            del_count = 0
            for d in all_deleted_dirs:
                cur.execute("DELETE FROM BaseItems WHERE Path = ? OR Path LIKE ?", (d, f"{d}/%"))
                del_count += cur.rowcount
            for p in all_deleted_paths:
                cur.execute("DELETE FROM BaseItems WHERE Path = ?", (p,))
                del_count += cur.rowcount
            cur.execute("""
                DELETE FROM BaseItems
                WHERE Id NOT IN (
                    SELECT MIN(Id)
                    FROM BaseItems
                    GROUP BY Path
                )
                AND Path IS NOT NULL AND Path != ''
            """)
            del_count += cur.rowcount

            # Remove duplicate BaseItems rows matching same normalized name and type
            cur.execute("""
                SELECT Id, Name, Path, type
                FROM BaseItems
                WHERE type LIKE '%Movie' OR type LIKE '%Series'
            """)
            all_media_items = cur.fetchall()
            title_groups = {}
            for item_id, item_name, item_path, item_type in all_media_items:
                if not item_name:
                    continue
                norm_key = (normalize_title(item_name), item_type)
                title_groups.setdefault(norm_key, []).append((item_id, item_name, item_path))

            for (norm_title, itype), candidates in title_groups.items():
                if len(candidates) <= 1:
                    continue
                def score_db_row(r):
                    p = (r[2] or "").lower()
                    name = (r[1] or "")
                    s = 0
                    if os.path.exists(r[2] or ""): s += 200
                    if re.search(r"\(\d{4}\)", name): s += 30
                    if "-" in name: s += 10
                    if "spider-man" in p: s += 50
                    if "shang-chi" in p: s += 50
                    if "china-town" in p: s += 50
                    if "," in p or "." in p: s += 10
                    s += len(p)
                    return s
                candidates.sort(key=score_db_row, reverse=True)
                for redundant in candidates[1:]:
                    print(f"[DEDUP] Removing duplicate BaseItems row by normalized name: '{redundant[1]}' (Id={redundant[0]}, Path={redundant[2]})")
                    cur.execute("DELETE FROM BaseItems WHERE Id = ?", (redundant[0],))
                    del_count += 1
            conn.commit()
            conn.close()
            if del_count > 0:
                print(f"[DEDUP] Cleaned {del_count} redundant BaseItems database row(s) in {db_p}")
        except Exception as e:
            print(f"[DEDUP] Note cleaning database {db_p}: {e}")

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
    heal_channel_and_db_names()
    heal_missing_db_strm_paths()
    deduplicate_media_strms()
    repair_user_subtitle_preferences()
    repair_user_policy_preferences()
    repair_system_xml()


if __name__ == "__main__":
    main()
