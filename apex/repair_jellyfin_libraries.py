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
            "OR (Name = 'English' AND type LIKE '%Series%')"
        )
        purged = cur.rowcount
        if purged > 0:
            print(f"[REPAIR] Purged {purged} blacklisted / stale item rows from {db_path}.")

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


def main():
    for db in TARGET_DATABASES:
        repair_database(db)


if __name__ == "__main__":
    main()
