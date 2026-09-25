#!/bin/bash
set -euo pipefail

export FILETOLINK_PORT="${FILETOLINK_PORT:-8081}"
export TG_LISTEN_PORT="${TG_LISTEN_PORT:-8082}"
export PYTHONPATH="/opt/apex:/app${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p /data/jellyfin /data/cache /data/apex /opt/jellyfin-local

echo "[BOOT] Starting FileToLink on port ${FILETOLINK_PORT}..."
PORT="$FILETOLINK_PORT" python3 -m Thunder &
FILETOLINK_PID=$!

echo "[BOOT] Starting combined Apex/Jellyfin supervisor..."
cd /opt/apex
exec /opt/apex/combined-entrypoint.sh "$FILETOLINK_PID"
