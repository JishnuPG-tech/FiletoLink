FROM debian:bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    XDG_DATA_HOME=/data/share \
    XDG_CONFIG_HOME=/data/config \
    XDG_CACHE_HOME=/root/.cache \
    XDG_STATE_HOME=/data/state \
    HOME=/root

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        libssl-dev \
        python3-pip \
        curl \
        ca-certificates \
        nginx \
        gnupg \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://repo.jellyfin.org/jellyfin_team.gpg.key | gpg --dearmor -o /etc/apt/keyrings/jellyfin.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/jellyfin.gpg arch=amd64] https://repo.jellyfin.org/debian bookworm main" > /etc/apt/sources.list.d/jellyfin.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends jellyfin-server jellyfin-web ffmpeg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip --break-system-packages && \
    python3 -m pip install --no-cache-dir -r requirements.txt --break-system-packages

COPY . .
COPY apex /opt/apex

RUN chmod +x /app/combined-entrypoint.sh /opt/apex/health_doctor.py /opt/apex/combined-entrypoint.sh

EXPOSE 7860

ENTRYPOINT ["/app/combined-entrypoint.sh"]
