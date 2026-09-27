#!/usr/bin/env python3
"""
Automatically repair and verify Jellyfin CollectionFolder (library) rows in jellyfin.db.
Runs before Jellyfin starts to ensure ItemId / LibraryOptions resolve and
PhysicalLocationsList points directly to /data/jellyfin/media/... locations.
"""

import os
import sys
import json
import sqlite3
import datetime

TARGET_DATABASES = [
    "/opt/jellyfin-local/data/data/jellyfin.db",
    "/data/jellyfin/data/data/jellyfin.db",
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


def repair_database(db_path: str) -> bool:
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

        # Permanently purge blacklisted demo items, Ms.Rose & Mr.Cane, and invalid TV Shows/English items
        cur.execute(
            "DELETE FROM BaseItems WHERE Path LIKE '%/TV Shows/English%' "
            "OR Path LIKE '%Mot test servicing%' "
            "OR Name LIKE '%Mot test servicing%' "
            "OR Path LIKE '%Rose%Cane%' "
            "OR Name LIKE '%Rose%Cane%' "
            "OR Name LIKE '%Ms.Rose%' "
            "OR Name LIKE '%Ms Rose%' "
            "OR Path LIKE '%Ms.Rose%' "
            "OR Path LIKE '%Ms Rose%' "
            "OR (Path LIKE '%kattalan%' AND Path LIKE '%Telugu%') "
            "OR (Name LIKE '%kattalan%' AND Path LIKE '%Telugu%') "
            "OR (Name = 'English' AND type LIKE '%Series%')"
        )
        purged = cur.rowcount
        if purged > 0:
            print(f"[REPAIR] Purged {purged} blacklisted / stale item rows from {db_path}.")

        # Clean up orphaned rows whose media files do not exist on disk (prevents duplicate ghost items)
        cur.execute(
            "SELECT Id, Path, Name FROM BaseItems "
            "WHERE (Path LIKE '/data/jellyfin/media/%' OR Path LIKE '/opt/jellyfin-local/%' OR Path LIKE '/data/movies/%') "
            "AND (type LIKE '%Movie%' OR type LIKE '%Episode%')"
        )
        orphaned = []
        for row_id, item_path, item_name in cur.fetchall():
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
                    import shutil
                    shutil.rmtree(dirpath, ignore_errors=True)
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


def main():
    for db in TARGET_DATABASES:
        repair_database(db)
    purge_plugin_databases()
    cleanup_empty_media_folders()


if __name__ == "__main__":
    main()
