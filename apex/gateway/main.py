import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from gateway.utils import get_http_client, proxy_http_request, proxy_websocket_stream
from gateway.ops import router as ops_router, _jellyfin_auth_header, _JELLYFIN_BASE

logger = logging.getLogger("gateway.main")
logging.basicConfig(level=logging.INFO)

# Default plugin catalog repository, guaranteed at startup so online plugins
# always show up in the web UI after every boot/rebuild (Jellyfin reads the
# repo list into memory at startup; the live config is mirrored to /data by
# the write-back loop, so an API-set repo also survives restarts).
DEFAULT_PLUGIN_REPO = {
    "Name": "Jellyfin Stable",
    "Url": "https://repo.jellyfin.org/files/plugin/manifest.json",
    "Enabled": True,
}

async def ensure_jellyfin_plugin_repository() -> None:
    """Idempotently configure the plugin repository on the live Jellyfin server."""
    import aiohttp

    for attempt in range(1, 61):
        await asyncio.sleep(2)
        headers = _jellyfin_auth_header()
        if not headers:
            continue
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{_JELLYFIN_BASE}/Repositories", headers=headers, timeout=5
                ) as resp:
                    if resp.status != 200:
                        continue
                    repos = await resp.json()
                    if isinstance(repos, list) and any(
                        isinstance(r, dict) and str(r.get("Url")) == DEFAULT_PLUGIN_REPO["Url"]
                        for r in repos
                    ):
                        logger.info("[PLUGINS] Repository already configured.")
                        return
                async with session.post(
                    f"{_JELLYFIN_BASE}/Repositories", headers=headers, json=[DEFAULT_PLUGIN_REPO], timeout=10
                ) as resp:
                    if resp.status in (200, 204):
                        logger.info("[PLUGINS] Plugin repository configured via API (attempt %s).", attempt)
                        return
        except Exception:
            continue
    logger.warning("[PLUGINS] Could not ensure plugin repository during startup window.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(ensure_jellyfin_plugin_repository())
    yield

app = FastAPI(title="OpenCode Space Gateway", docs_url=None, redoc_url=None, lifespan=lifespan)

app.include_router(ops_router)

JELLYFIN_PORT = int(os.environ.get("JELLYFIN_PORT", "8096"))
TG_PORT = int(os.environ.get("TG_LISTEN_PORT", "8082"))
FILETOLINK_PORT = int(os.environ.get("FILETOLINK_PORT", "8081"))

@app.get("/ping")
@app.get("/keepalive")
@app.get("/heartbeat")
async def keepalive_ping():
    """Fast, zero-overhead heartbeat endpoint for UptimeRobot / cron pings to prevent Space sleep."""
    return JSONResponse({"status": "ok", "service": "Apex-Jellyfin", "alive": True})

@app.get("/health")
@app.get("/debug/status")
async def health_check():
    client = get_http_client()
    services = {
        "jellyfin":  f"http://127.0.0.1:{JELLYFIN_PORT}/System/Info/Public",
        "tg_stream": f"http://127.0.0.1:{TG_PORT}/health",
        "filetolink": f"http://127.0.0.1:{FILETOLINK_PORT}/status",
    }
    results = {}
    for name, url in services.items():
        try:
            r = await client.get(url, timeout=2.0)
            results[name] = {"status": "ok", "code": r.status_code}
        except Exception as exc:
            results[name] = {"status": "starting", "message": str(exc)}
    return {"gateway": "healthy", "upstreams": results}

@app.get("/")
@app.get("/index.html")
async def root_portal(request: Request):
    return await proxy_http_request(
        f"http://127.0.0.1:{FILETOLINK_PORT}{request.url.path}",
        request,
        default_prefix="",
    )

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def route_catch_all(path: str, request: Request):
    raw_path = request.url.path
    req_path = raw_path.lower()
    
    # Brand logo interception: serve Apex Delta vector glyph & PNG directly for any Jellyfin logo/icon request
    if any(icon_kw in req_path for icon_kw in ("icon-transparent", "apex-logo", "touchicon", "notificationicon")):
        for logo_cand in ("/opt/apex/ui/icon-transparent.png", "/opt/apex/ui/apex-logo.png", "apex/ui/apex-logo.png"):
            if os.path.isfile(logo_cand):
                logo_png = logo_cand
                break
        else:
            logo_png = None
        logo_svg = "/opt/apex/ui/apex-logo.svg" if os.path.isfile("/opt/apex/ui/apex-logo.svg") else "apex/ui/apex-logo.svg"
        if req_path.endswith(".svg") and os.path.isfile(logo_svg):
            return FileResponse(logo_svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})
        elif logo_png and os.path.isfile(logo_png):
            return FileResponse(logo_png, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})

    if req_path in ("/", "/index.html"):
        return await root_portal(request)
    
    if req_path == "/jellyfin" or req_path.startswith("/jellyfin/"):
        logger.info(f"[ROUTER] {req_path} -> Jellyfin ({JELLYFIN_PORT})")
        sub_p = "/" if req_path == "/jellyfin" else raw_path[len("/jellyfin"):]
        if sub_p.startswith("/ui/"):
            sub_p = f"/web{sub_p}"
        return await proxy_http_request(f"http://127.0.0.1:{JELLYFIN_PORT}{sub_p}", request, default_prefix="/jellyfin", extra_headers={"X-Forwarded-Prefix": "/jellyfin"})
    
    # Direct Telegram video streaming endpoints:
    if req_path.startswith("/stream/") or req_path.startswith("/stream_file"):
        logger.info(f"[ROUTER] {req_path} (Direct Stream) -> Telegram ({TG_PORT})")
        return await proxy_http_request(f"http://127.0.0.1:{TG_PORT}{raw_path}", request, default_prefix="")

    # Root Jellyfin media streaming endpoints:
    if req_path.startswith("/videos/") or req_path.startswith("/audio/"):
        logger.info(f"[ROUTER] {req_path} (Jellyfin Media Stream) -> Jellyfin ({JELLYFIN_PORT})")
        return await proxy_http_request(
            f"http://127.0.0.1:{JELLYFIN_PORT}{raw_path}",
            request,
            default_prefix="/jellyfin",
            extra_headers={"X-Forwarded-Prefix": "/jellyfin"},
        )

    if req_path in ("/session-login", "/session-login/"):
        return await proxy_http_request(f"http://127.0.0.1:{TG_PORT}/session-login", request, default_prefix="")

    if req_path in ("/tg-stream", "/tg_stream") or req_path.startswith("/tg-stream/") or req_path.startswith("/tg_stream/"):
        logger.info(f"[ROUTER] {req_path} -> Telegram ({TG_PORT})")
        if req_path in ("/tg-stream", "/tg_stream"):
            sub_p = "/"
        elif req_path.startswith("/tg-stream/"):
            sub_p = raw_path[len("/tg-stream"):]
        else:
            sub_p = raw_path[len("/tg_stream"):]
        return await proxy_http_request(f"http://127.0.0.1:{TG_PORT}{sub_p}", request, default_prefix="/tg-stream")

    if req_path == "/filetolink" or req_path.startswith("/filetolink/"):
        sub_p = "/" if req_path == "/filetolink" else raw_path[len("/filetolink"):]
        return await proxy_http_request(
            f"http://127.0.0.1:{FILETOLINK_PORT}{sub_p}",
            request,
            default_prefix="/filetolink",
        )
    
    if req_path == "/health/live":
        return JSONResponse({"status": "live"})
        
    if req_path.startswith("/ui/"):
        logger.info(f"[ROUTER] {req_path} (Jellyfin Web UI Asset) -> Jellyfin ({JELLYFIN_PORT})")
        return await proxy_http_request(
            f"http://127.0.0.1:{JELLYFIN_PORT}/web{raw_path}",
            request,
            default_prefix="/jellyfin",
            extra_headers={"X-Forwarded-Prefix": "/jellyfin"},
        )

    # Jellyfin Plugins and root-relative endpoints:
    # Plugins like SkinManager (/api/SkinManager/Resource) and InPlayerPreview (/InPlayerPreview/ClientScript)
    # emit root-relative fetch/script URLs without the /jellyfin prefix.
    JELLYFIN_PLUGIN_PREFIXES = (
        "/api/",
        "/inplayerpreview",
        "/skinmanager",
        "/introskipper",
        "/jellyscrub",
        "/mediabar",
        "/themesongs",
        "/playbackreporting",
        "/reports",
        "/ui/",
        "/videos/",
        "/audio/",
        "/sessions/",
    )
    referer = request.headers.get("referer", "").lower()
    is_jellyfin_call = any(req_path.startswith(p) for p in JELLYFIN_PLUGIN_PREFIXES) or (
        "/jellyfin" in referer
        and not any(req_path.startswith(p) for p in ("/watch/", "/f/", "/filetolink", "/tg-stream", "/tg_stream", "/status", "/health"))
    )

    if is_jellyfin_call:
        logger.info(f"[ROUTER] {req_path} (Jellyfin Plugin/Referer) -> Jellyfin ({JELLYFIN_PORT})")
        target_path = raw_path
        if req_path.startswith("/ui/"):
            target_path = f"/web{raw_path}"
        return await proxy_http_request(
            f"http://127.0.0.1:{JELLYFIN_PORT}{target_path}",
            request,
            default_prefix="/jellyfin",
            extra_headers={"X-Forwarded-Prefix": "/jellyfin"},
        )

    logger.info(f"[ROUTER] {req_path} -> FileToLink fallback ({FILETOLINK_PORT})")
    sub_p = request.url.path
    return await proxy_http_request(
        f"http://127.0.0.1:{FILETOLINK_PORT}{sub_p}",
        request,
        default_prefix="",
    )

@app.websocket("/socket")
@app.websocket("/jellyfin/socket")
async def jellyfin_socket(websocket: WebSocket):
    JELLYFIN_WS = f"ws://127.0.0.1:{JELLYFIN_PORT}/socket"
    logger.info(f"[ROUTER] WebSocket {websocket.url.path} -> Jellyfin ({JELLYFIN_PORT})")
    await proxy_websocket_stream(websocket, JELLYFIN_WS)
