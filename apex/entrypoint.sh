#!/bin/bash
set -e

echo "[BOOT] Starting Gateway..."
mkdir -p /data/jellyfin/data /data/jellyfin/config /data/jellyfin/cache /data/jellyfin/log /data/cache 2>/dev/null || true

# ---------------------------------------------------------------------------
# Jellyfin local datadir strategy (HF Spaces persistent /data is network-backed
# and does not honor SQLite file locking; concurrent reads from the web client
# intermittently fail with "SQLite Error 10: disk I/O error").
#
# We run Jellyfin against a LOCAL datadir (reliable locking, fast reads) and
# periodically write a safe online snapshot (sqlite .backup) back to /data so
# the database + config survive container restarts. Media stays on /data.
# ---------------------------------------------------------------------------
LOCAL_ROOT=/opt/jellyfin-local

JELLYFIN_OPTS="--datadir $LOCAL_ROOT/data --configdir $LOCAL_ROOT/config --cachedir $LOCAL_ROOT/cache --logdir $LOCAL_ROOT/log --webdir /usr/share/jellyfin/web"

restore_jellyfin_local() {
    echo "[JELLYFIN] Preparing local datadir at $LOCAL_ROOT ..."
    mkdir -p "$LOCAL_ROOT/data/data" "$LOCAL_ROOT/config" "$LOCAL_ROOT/cache" "$LOCAL_ROOT/log"
    # Restore durable data/config snapshot from the persistent volume if present.
    # Exclude the metadata tree: it is handled via snapshot below and its old
    # absolute DB path is redirected to the fast local datadir.
    if [ -f "/data/jellyfin/data/data/jellyfin.db" ]; then
        echo "[JELLYFIN] Restoring database + metadata from persistent volume..."
        find /data/jellyfin/data -mindepth 1 -maxdepth 1 \
            \( -name metadata -o -name metadata.snapshot \) -prune -o \
            -exec cp -a -f {} "$LOCAL_ROOT/data/" \; 2>/dev/null || true
        sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" "PRAGMA journal_mode=WAL; PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
    fi
    if [ -d "/data/jellyfin/config" ]; then
        cp -a -f /data/jellyfin/config/. "$LOCAL_ROOT/config/" 2>/dev/null || true
    fi
    if [ -d "/data/jellyfin/cache" ]; then
        cp -a -f /data/jellyfin/cache/. "$LOCAL_ROOT/cache/" 2>/dev/null || true
    fi

    # Run library and auth repair after restoring both database and config
    if [ -f "$LOCAL_ROOT/data/data/jellyfin.db" ] || [ -f "/data/jellyfin/data/data/jellyfin.db" ]; then
        python3 /repair_jellyfin_libraries.py 2>/dev/null || python3 /opt/apex/repair_jellyfin_libraries.py 2>/dev/null || python3 "$(dirname "$0")/repair_jellyfin_libraries.py" 2>/dev/null || true
    fi

    # Jellyfin's item DB bakes absolute metadata paths (e.g. .../Data/metadata/People/x/folder.jpg)
    # into its rows. Redirect that whole path onto the fast local disk so Skia reads
    # don't hit the flaky network volume. Keep a durable snapshot for restart recovery.
    mkdir -p "$LOCAL_ROOT/data/metadata"
    if [ -d "/data/jellyfin/data/metadata.snapshot" ]; then
        cp -a -f /data/jellyfin/data/metadata.snapshot/. "$LOCAL_ROOT/data/metadata/" 2>/dev/null || true
    elif [ -d "/data/jellyfin/data/metadata" ] && [ ! -L "/data/jellyfin/data/metadata" ]; then
        cp -a -f /data/jellyfin/data/metadata/. "$LOCAL_ROOT/data/metadata/" 2>/dev/null || true
    fi
    rm -rf /data/jellyfin/data/metadata 2>/dev/null || true
    ln -s "$LOCAL_ROOT/data/metadata" /data/jellyfin/data/metadata 2>/dev/null || true
    if [ -d "$LOCAL_ROOT/data/metadata" ]; then
        mkdir -p /data/jellyfin/data/metadata.snapshot
    fi

    # Clean up any custom css files and restore stock index.html
    rm -f /usr/share/jellyfin/web/netflix-dark.css /usr/share/jellyfin/web/pitch-black.css 2>/dev/null || true
    if [ -f "/usr/share/jellyfin/web/index.html" ]; then
        sed -i 's|<link rel="stylesheet" href="[^"]*css"></head>|</head>|g' /usr/share/jellyfin/web/index.html 2>/dev/null || true
    fi

    echo "[JELLYFIN] Local datadir ready. Metadata redirected to fast local disk."
}

sync_jellyfin_back() {
    # Periodic durable snapshot of the live Jellyfin datadir back to /data.
    # Uses sqlite online backup for the DB; plain copy for config/log/metadata.
    echo "[JELLYFIN] Durable write-back loop started (every 20s)."
    while :; do
        sleep 20
        if [ -f "$LOCAL_ROOT/data/data/jellyfin.db" ]; then
            sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
            mkdir -p /data/jellyfin/data/data
            snapshot="/data/jellyfin/data/data/jellyfin.db.tmp"
            if sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" ".backup '$snapshot'" 2>/dev/null; then
                mv -f "$snapshot" /data/jellyfin/data/data/jellyfin.db
            elif cp -f "$LOCAL_ROOT/data/data/jellyfin.db" "$snapshot" 2>/dev/null; then
                mv -f "$snapshot" /data/jellyfin/data/data/jellyfin.db
            else
                rm -f "$snapshot" 2>/dev/null || true
            fi
        fi
        if [ -d "$LOCAL_ROOT/data" ]; then
            find "$LOCAL_ROOT/data" -mindepth 1 -maxdepth 1 \
                -not -name data \
                -not -name metadata \
                -exec cp -a -f {} /data/jellyfin/data/ \; 2>/dev/null || true
        fi
        # Metadata lives on fast local disk; keep a durable snapshot for restarts.
        if [ -d "$LOCAL_ROOT/data/metadata" ]; then
            mkdir -p /data/jellyfin/data/metadata.snapshot
            cp -a -f "$LOCAL_ROOT/data/metadata/." /data/jellyfin/data/metadata.snapshot/ 2>/dev/null || true
        fi
        cp -a -f "$LOCAL_ROOT/config/." /data/jellyfin/config/ 2>/dev/null || true
        cp -a -f "$LOCAL_ROOT/log/." /data/jellyfin/log/ 2>/dev/null || true
    done
}

launch_jellyfin() {
    if command -v jellyfin >/dev/null 2>&1; then
        jellyfin $JELLYFIN_OPTS &
    elif [ -f "/usr/bin/jellyfin" ]; then
        /usr/bin/jellyfin $JELLYFIN_OPTS &
    else
        echo "[CRITICAL] jellyfin binary not found!"
        JELLYFIN_PID=""
        return 1
    fi
    JELLYFIN_PID=$!
}

restore_jellyfin_local

# Keep Jellyfin's public server identity stable across container restarts.
# Browsers persist credentials under this ID; regenerating it makes the web
# client fail before login with an undefined server entry.
SERVER_ID_FILE=/data/jellyfin/server_id
SYSTEM_XML="$LOCAL_ROOT/config/system.xml"
if [ -s "$SERVER_ID_FILE" ]; then
    JELLYFIN_SERVER_ID="$(tr -d '[:space:]' < "$SERVER_ID_FILE")"
else
    JELLYFIN_SERVER_ID="$(python3 - "$SYSTEM_XML" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
match = re.search(r"<ServerId>([^<]+)</ServerId>", text)
print(match.group(1).strip() if match else "")
PY
)"
    if [ -z "$JELLYFIN_SERVER_ID" ]; then
        JELLYFIN_SERVER_ID="$(printf '%s' 'ApexSpace-Jellyfin' | sha256sum | cut -c1-32)"
    fi
    printf '%s\n' "$JELLYFIN_SERVER_ID" > "$SERVER_ID_FILE"
fi

if [ -f "$SYSTEM_XML" ] && [ -n "$JELLYFIN_SERVER_ID" ]; then
    python3 - "$SYSTEM_XML" "$JELLYFIN_SERVER_ID" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
server_id = sys.argv[2]
text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
replacement = f"<ServerId>{server_id}</ServerId>"
if re.search(r"<ServerId>[^<]*</ServerId>", text):
    text = re.sub(r"<ServerId>[^<]*</ServerId>", replacement, text, count=1)
elif "</SystemConfiguration>" in text:
    text = text.replace("</SystemConfiguration>", f"  {replacement}\n</SystemConfiguration>", 1)
else:
    text = f"<SystemConfiguration>\n  {replacement}\n</SystemConfiguration>\n"
path.write_text(text, encoding="utf-8")
PY
fi

echo "[HEALTH] Jellyfin starting in background (local datadir)..."
launch_jellyfin

if [ -f "/health_doctor.py" ]; then
    echo "[HEALTH] Starting Database & Disk Health Doctor daemon..."
    python3 /health_doctor.py &
fi

sync_jellyfin_back &
SYNC_PID=$!

echo "[HEALTH] Telegram streamer starting in background..."
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python3 /tg_streamer.py &
TG_STREAMER_PID=$!

echo "[HEALTH] FastAPI Gateway starting..."
python3 -m uvicorn proxy:app --host 127.0.0.1 --port 8000 --workers 2 &
FASTAPI_PID=$!

echo "[HEALTH] Nginx starting..."
nginx -g 'daemon off;' -c /nginx.conf &
NGINX_PID=$!

perform_final_sync() {
    echo "[PERSISTENCE] Graceful shutdown initiated. Syncing durable Jellyfin state..."
    if [ -n "${JELLYFIN_PID:-}" ] && kill -0 "$JELLYFIN_PID" 2>/dev/null; then
        echo "[JELLYFIN] Sending SIGTERM to Jellyfin (PID $JELLYFIN_PID)..."
        kill -TERM "$JELLYFIN_PID" 2>/dev/null || true
        for i in {1..10}; do
            if ! kill -0 "$JELLYFIN_PID" 2>/dev/null; then
                break
            fi
            sleep 0.5
        done
        kill -9 "$JELLYFIN_PID" 2>/dev/null || true
    fi

    if [ -f "$LOCAL_ROOT/data/data/jellyfin.db" ]; then
        sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
        mkdir -p /data/jellyfin/data/data
        if sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" ".backup '/data/jellyfin/data/data/jellyfin.db'" 2>/dev/null; then
            echo "[PERSISTENCE] Successfully backed up jellyfin.db to persistent volume."
        else
            cp -f "$LOCAL_ROOT/data/data/jellyfin.db" /data/jellyfin/data/data/jellyfin.db 2>/dev/null || true
        fi
    fi

    if [ -d "$LOCAL_ROOT/data" ]; then
        find "$LOCAL_ROOT/data" -mindepth 1 -maxdepth 1 \
            -not -name data \
            -not -name metadata \
            -exec cp -a -f {} /data/jellyfin/data/ \; 2>/dev/null || true
    fi

    if [ -d "$LOCAL_ROOT/data/metadata" ]; then
        mkdir -p /data/jellyfin/data/metadata.snapshot
        cp -a -f "$LOCAL_ROOT/data/metadata/." /data/jellyfin/data/metadata.snapshot/ 2>/dev/null || true
    fi

    if [ -d "$LOCAL_ROOT/config" ]; then
        cp -a -f "$LOCAL_ROOT/config/." /data/jellyfin/config/ 2>/dev/null || true
    fi
    if [ -d "$LOCAL_ROOT/log" ]; then
        cp -a -f "$LOCAL_ROOT/log/." /data/jellyfin/log/ 2>/dev/null || true
    fi

    for pid in "${FASTAPI_PID:-}" "${NGINX_PID:-}" "${TG_STREAMER_PID:-}" "${SYNC_PID:-}"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done

    echo "[PERSISTENCE] Durable state successfully synced to /data. Exiting."
    exit 0
}

trap perform_final_sync SIGTERM SIGINT SIGHUP

echo "[BOOT] All services dispatched. Process Supervisor active."

while true; do
    if [ -n "$FASTAPI_PID" ] && ! kill -0 $FASTAPI_PID 2>/dev/null; then
        echo "[CRITICAL] FastAPI Gateway process died! Restarting..."
        python3 -m uvicorn proxy:app --host 127.0.0.1 --port 8000 --workers 2 &
        FASTAPI_PID=$!
    fi

    if [ -n "$NGINX_PID" ] && ! kill -0 $NGINX_PID 2>/dev/null; then
        echo "[CRITICAL] Nginx process died! Restarting..."
        nginx -g 'daemon off;' -c /nginx.conf &
        NGINX_PID=$!
    fi

    if [ -n "$TG_STREAMER_PID" ] && ! kill -0 $TG_STREAMER_PID 2>/dev/null; then
        echo "[CRITICAL] TG Streamer process died! Restarting..."
        PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python3 /tg_streamer.py &
        TG_STREAMER_PID=$!
    fi

    if [ -n "$JELLYFIN_PID" ] && ! kill -0 $JELLYFIN_PID 2>/dev/null; then
        echo "[CRITICAL] Jellyfin process died! Restarting..."
        launch_jellyfin
    fi

    if [ -n "$SYNC_PID" ] && ! kill -0 $SYNC_PID 2>/dev/null; then
        echo "[CRITICAL] Jellyfin write-back loop died! Restarting..."
        sync_jellyfin_back &
        SYNC_PID=$!
    fi

    sleep 10 &
    wait $! 2>/dev/null || true
done
