#!/bin/bash
set -euo pipefail

FILETOLINK_PID="${1:-}"
JELLYFIN_PID=""
FASTAPI_PID=""
NGINX_PID=""
TG_STREAMER_PID=""
SYNC_PID=""
export HOSTNAME="Apex"

echo "[BOOT] Starting Gateway..."
mkdir -p /data/jellyfin/data /data/jellyfin/config /data/jellyfin/cache /data/jellyfin/log /data/cache 2>/dev/null || true
PERSISTENCE_MARKER=/data/.apex-persistence-marker
if [ -f "$PERSISTENCE_MARKER" ]; then
    echo "[PERSISTENCE] Persistent /data marker found; restoring durable state."
else
    if printf '%s\n' "created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$PERSISTENCE_MARKER" 2>/dev/null; then
        echo "[PERSISTENCE] No prior marker found. If this reappears after a restart, attach HF Persistent Storage."
    else
        echo "[PERSISTENCE] WARNING: /data is not writable; Jellyfin state cannot survive this container restart."
    fi
fi

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
    mkdir -p "$LOCAL_ROOT/data/data" "$LOCAL_ROOT/config" "$LOCAL_ROOT/cache/transcodes" "$LOCAL_ROOT/log"
    # Restore durable data/config snapshot from the persistent volume if present.
    # Exclude the metadata tree: it is handled via snapshot below and its old
    # absolute DB path is redirected to the fast local datadir.
    if [ -f "/data/jellyfin/data/data/jellyfin.db" ]; then
        echo "[JELLYFIN] Restoring database + metadata from persistent volume..."
        find /data/jellyfin/data -mindepth 1 -maxdepth 1 \
            \( -name metadata -o -name metadata.snapshot \) -prune -o \
            -exec cp -a -f {} "$LOCAL_ROOT/data/" \; 2>/dev/null || true
        echo "[PERSISTENCE] Jellyfin database snapshot found ($(stat -c '%s' /data/jellyfin/data/data/jellyfin.db 2>/dev/null || echo unknown) bytes)."
        sqlite3 "$LOCAL_ROOT/data/data/jellyfin.db" "PRAGMA journal_mode=WAL; PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null || true
    else
        echo "[PERSISTENCE] No Jellyfin database snapshot found; Jellyfin will run first-time initialization."
    fi
    if [ -d "/data/jellyfin/config" ]; then
        cp -a -f /data/jellyfin/config/. "$LOCAL_ROOT/config/" 2>/dev/null || true
    fi
    if [ -d "/data/jellyfin/cache" ]; then
        cp -a -f /data/jellyfin/cache/. "$LOCAL_ROOT/cache/" 2>/dev/null || true
    fi

    # Scrub corrupted directories from media and metadata snapshot BEFORE library repair
    rm -rf "/data/jellyfin/media/TV Shows/English" "/opt/jellyfin-local/media/TV Shows/English" 2>/dev/null || true
    find /data/jellyfin/media /opt/jellyfin-local/media /data/movies /data/tvshows -iname "*summer*turned*pretty*" -exec rm -rf {} + 2>/dev/null || true
    find /data/jellyfin/media /opt/jellyfin-local/media /data/movies /data/tvshows -iname "*what*if*(2024)*" -exec rm -rf {} + 2>/dev/null || true
    find /data/jellyfin/data/metadata /data/jellyfin/data/metadata.snapshot "$LOCAL_ROOT/data/metadata" -iname "*summer*pretty*" -o -iname "*tt194766*" -o -iname "*194766*" -exec rm -rf {} + 2>/dev/null || true

    # Run library and auth repair after restoring both database and config
    if [ -f "$LOCAL_ROOT/data/data/jellyfin.db" ] || [ -f "/data/jellyfin/data/data/jellyfin.db" ]; then
        python3 /opt/apex/repair_jellyfin_libraries.py || python3 "$(dirname "$0")/repair_jellyfin_libraries.py" || true
    fi

    # Permanently delete blacklisted demo episodes from media paths
    find /data/jellyfin/media /data/movies /data/tvshows /data /opt/jellyfin-local -iname "*mot*test*servicing*" -exec rm -rf {} + 2>/dev/null || true
    find /data/jellyfin/media /data/movies /data/tvshows /data /opt/jellyfin-local -iname "*rose*cane*" -o -iname "*ms.rose*" -o -iname "*ms rose*" -exec rm -rf {} + 2>/dev/null || true
    find /data/jellyfin/media/Movies/Telugu /data/movies/Telugu /opt/jellyfin-local -iname "*kattalan*" -exec rm -rf {} + 2>/dev/null || true
    # Clean up empty movie directories or orphaned folders left behind after moves
    find /data/jellyfin/media/Movies -mindepth 2 -type d -empty -delete 2>/dev/null || true
    if [ -d "/data/jellyfin/media/Movies/English" ]; then
        find "/data/jellyfin/media/Movies/English" -mindepth 1 -maxdepth 1 -type d -exec bash -c 'for d; do [ -z "$(find "$d" -name "*.strm" 2>/dev/null)" ] && rm -rf "$d"; done' _ {} + 2>/dev/null || true
    fi

    # Clean up corrupt, 0-byte, or broken suffix subtitle files that cause ffprobe failure
    find /data/jellyfin/media /opt/jellyfin-local/media /data/movies /data/tvshows -type f \( -name "*.srt" -o -name "*.vtt" -o -name "*.ass" \) -size 0 -delete 2>/dev/null || true
    find /data/jellyfin/media /opt/jellyfin-local/media /data/movies /data/tvshows -type f \( -name "*.srt" -o -name "*.vtt" -o -name "*.ass" \) -size -50c -delete 2>/dev/null || true
    find /data/jellyfin/media /opt/jellyfin-local/media /data/movies /data/tvshows -type f -name "*.0.srt" -delete 2>/dev/null || true

    # Purge old low-res Jellyfin image cache so newly fetched HD/4K artwork is displayed immediately
    rm -rf "$LOCAL_ROOT/cache/images"/* /data/jellyfin/cache/images/* 2>/dev/null || true

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


    # Install Abyss Theme & Spotlight Add-on
    mkdir -p /usr/share/jellyfin/web/ui
    if [ -d "/opt/apex/ui" ]; then
        cp -a -f /opt/apex/ui/. /usr/share/jellyfin/web/ui/ 2>/dev/null || true
    fi

    INDEX_FILE="/usr/share/jellyfin/web/index.html"
    if [ -f "$INDEX_FILE" ]; then
        # Ensure <html> has data-theme="dark"
        if ! grep -q 'data-theme="dark"' "$INDEX_FILE"; then
            sed -i 's|<html|<html data-theme="dark"|g' "$INDEX_FILE" 2>/dev/null || true
        fi

        # Remove any old css/spotlight injections to avoid duplicates
        sed -i 's|<link [^>]*data-abyss-theme[^>]*>||g' "$INDEX_FILE" 2>/dev/null || true
        sed -i 's|<link [^>]*href="ui/abyss.css"[^>]*>||g' "$INDEX_FILE" 2>/dev/null || true
        sed -i 's|<script [^>]*data-abyss-spotlight[^>]*></script>||g' "$INDEX_FILE" 2>/dev/null || true
        sed -i 's|<script [^>]*src="ui/spotlight-loader.js"[^>]*></script>||g' "$INDEX_FILE" 2>/dev/null || true

        # Clean legacy CSS if present
        rm -f /usr/share/jellyfin/web/netflix-dark.css /usr/share/jellyfin/web/pitch-black.css 2>/dev/null || true
        sed -i 's|<link rel="stylesheet" href="[^"]*netflix-dark.css"></head>|</head>|g' "$INDEX_FILE" 2>/dev/null || true
        sed -i 's|<link rel="stylesheet" href="[^"]*pitch-black.css"></head>|</head>|g' "$INDEX_FILE" 2>/dev/null || true

        # Inject Abyss CSS into <head>
        sed -i 's|</head>|<link rel="stylesheet" href="ui/abyss.css" data-abyss-theme></head>|g' "$INDEX_FILE" 2>/dev/null || true

        # Inject Spotlight loader before </body>
        sed -i 's|</body>|<script src="ui/spotlight-loader.js" data-abyss-spotlight></script></body>|g' "$INDEX_FILE" 2>/dev/null || true

        echo "[JELLYFIN] Abyss theme & Spotlight hero banner installed into web assets."
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
                echo "[PERSISTENCE] WARNING: Jellyfin database snapshot failed."
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
    # Jellyfin logs its complete environment at Information level on startup.
    # Filter only that line while preserving the Jellyfin process PID and all
    # other operational messages.
    redact_jellyfin_environment() {
        sed -E 's/Environment Variables:.*/Environment Variables: [redacted]/'
    }
    if command -v jellyfin >/dev/null 2>&1; then
        jellyfin $JELLYFIN_OPTS \
            > >(redact_jellyfin_environment) \
            2> >(redact_jellyfin_environment >&2) &
    elif [ -f "/usr/bin/jellyfin" ]; then
        /usr/bin/jellyfin $JELLYFIN_OPTS \
            > >(redact_jellyfin_environment) \
            2> >(redact_jellyfin_environment >&2) &
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

if [ -f "$SYSTEM_XML" ]; then
    python3 - "$SYSTEM_XML" "$JELLYFIN_SERVER_ID" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
server_id = sys.argv[2]
text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

# Ensure stable ServerId
id_replacement = f"<ServerId>{server_id}</ServerId>"
if re.search(r"<ServerId>[^<]*</ServerId>", text):
    text = re.sub(r"<ServerId>[^<]*</ServerId>", id_replacement, text, count=1)
elif "</SystemConfiguration>" in text:
    text = text.replace("</SystemConfiguration>", f"  {id_replacement}\n</SystemConfiguration>", 1)
else:
    text = f"<SystemConfiguration>\n  {id_replacement}\n</SystemConfiguration>\n"

# Ensure clean ServerName as Apex
name_replacement = "<ServerName>Apex</ServerName>"
if re.search(r"<ServerName>[^<]*</ServerName>", text):
    text = re.sub(r"<ServerName>[^<]*</ServerName>", name_replacement, text, count=1)
elif "</SystemConfiguration>" in text:
    text = text.replace("</SystemConfiguration>", f"  {name_replacement}\n</SystemConfiguration>", 1)

# Ensure startup wizard is completed so Jellyfin goes straight to login
wizard_replacement = "<IsStartupWizardCompleted>true</IsStartupWizardCompleted>"
if re.search(r"<IsStartupWizardCompleted>[^<]*</IsStartupWizardCompleted>", text):
    text = re.sub(r"<IsStartupWizardCompleted>[^<]*</IsStartupWizardCompleted>", wizard_replacement, text, count=1)
elif "</SystemConfiguration>" in text:
    text = text.replace("</SystemConfiguration>", f"  {wizard_replacement}\n</SystemConfiguration>", 1)

path.write_text(text, encoding="utf-8")
PY
    cp -f "$SYSTEM_XML" "/data/jellyfin/config/system.xml" 2>/dev/null || true
    echo "[JELLYFIN] Configured server name as Apex in $SYSTEM_XML"
fi

# Ensure custom CSS in branding.xml does not force theme into admin pages
for bcfg in "$LOCAL_ROOT/config/branding.xml" "/data/jellyfin/config/branding.xml"; do
    if [ -f "$bcfg" ]; then
        sed -i 's|<CustomCss>[^<]*abyss[^<]*</CustomCss>|<CustomCss></CustomCss>|g' "$bcfg" 2>/dev/null || true
        sed -i 's|<CustomCss>[^<]*ElegantFin[^<]*</CustomCss>|<CustomCss></CustomCss>|g' "$bcfg" 2>/dev/null || true
    fi
done

# Configure encoding.xml for direct play / stream remuxing and video playback
ENCODING_XML="$LOCAL_ROOT/config/encoding.xml"
python3 - "$ENCODING_XML" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
content = """<?xml version="1.0" encoding="utf-8"?>
<EncodingOptions xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <EncodingThreadCount>0</EncodingThreadCount>
  <TranscodingTempPath>/opt/jellyfin-local/cache/transcodes</TranscodingTempPath>
  <DownMixAudioBoost>2</DownMixAudioBoost>
  <EnableThrottling>true</EnableThrottling>
  <ThrottleDelaySeconds>180</ThrottleDelaySeconds>
  <HardwareAccelerationType>none</HardwareAccelerationType>
  <EnableVideoEncoding>true</EnableVideoEncoding>
  <EnableAudioEncoding>true</EnableAudioEncoding>
  <AllowVideoStreamCopy>true</AllowVideoStreamCopy>
  <AllowAudioStreamCopy>true</AllowAudioStreamCopy>
</EncodingOptions>
"""
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(content.strip(), encoding="utf-8")
PY
cp -f "$ENCODING_XML" "/data/jellyfin/config/encoding.xml" 2>/dev/null || true
sed -i 's|<EnableVideoEncoding>false</EnableVideoEncoding>|<EnableVideoEncoding>true</EnableVideoEncoding>|g' "$ENCODING_XML" "/data/jellyfin/config/encoding.xml" 2>/dev/null || true
echo "[JELLYFIN] Configured high-performance video encoding & direct stream remux in $ENCODING_XML"

echo "[HEALTH] Jellyfin starting in background (local datadir)..."
launch_jellyfin

if [ -f "/opt/apex/health_doctor.py" ]; then
    echo "[HEALTH] Starting Database & Disk Health Doctor daemon..."
    python3 /opt/apex/health_doctor.py &
fi

sync_jellyfin_back &
SYNC_PID=$!

echo "[HEALTH] Telegram streamer starting in background..."
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python3 /opt/apex/tg_streamer.py &
TG_STREAMER_PID=$!

echo "[HEALTH] FastAPI Gateway starting..."
python3 -m uvicorn proxy:app --host 127.0.0.1 --port 8000 --workers 1 &
FASTAPI_PID=$!

echo "[HEALTH] Nginx starting..."
nginx -g 'daemon off;' -c /app/combined-nginx.conf &
NGINX_PID=$!

perform_final_sync() {
    echo "[PERSISTENCE] Graceful shutdown initiated. Syncing durable Jellyfin state..."
    if [ -n "$JELLYFIN_PID" ] && kill -0 "$JELLYFIN_PID" 2>/dev/null; then
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

    for pid in "$FASTAPI_PID" "$NGINX_PID" "$TG_STREAMER_PID" "$SYNC_PID" "$FILETOLINK_PID"; do
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
        python3 -m uvicorn proxy:app --host 127.0.0.1 --port 8000 --workers 1 &
        FASTAPI_PID=$!
    fi

    if [ -n "$NGINX_PID" ] && ! kill -0 $NGINX_PID 2>/dev/null; then
        echo "[CRITICAL] Nginx process died! Restarting..."
        nginx -g 'daemon off;' -c /app/combined-nginx.conf &
        NGINX_PID=$!
    fi

    if [ -n "$TG_STREAMER_PID" ] && ! kill -0 $TG_STREAMER_PID 2>/dev/null; then
        echo "[CRITICAL] TG Streamer process died! Restarting..."
        PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python3 /opt/apex/tg_streamer.py &
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

    if [ -n "$FILETOLINK_PID" ] && ! kill -0 "$FILETOLINK_PID" 2>/dev/null; then
        echo "[CRITICAL] FileToLink process died! Restarting..."
        cd /app
        PORT="$FILETOLINK_PORT" python3 -m Thunder &
        FILETOLINK_PID=$!
        cd /opt/apex
    fi

    sleep 10 &
    wait $! 2>/dev/null || true
done