import os
import logging
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from gateway.utils import get_http_client, proxy_http_request, proxy_websocket_stream
from gateway.ops import router as ops_router

logger = logging.getLogger("gateway.main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="OpenCode Space Gateway", docs_url=None, redoc_url=None)

app.include_router(ops_router)

JELLYFIN_PORT = int(os.environ.get("JELLYFIN_PORT", "8096"))
TG_PORT = int(os.environ.get("TG_LISTEN_PORT", "8082"))
FILETOLINK_PORT = int(os.environ.get("FILETOLINK_PORT", "8081"))

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
    
    if req_path in ("/", "/index.html"):
        return await root_portal(request)
    
    if req_path == "/jellyfin" or req_path.startswith("/jellyfin/"):
        logger.info(f"[ROUTER] {req_path} -> Jellyfin ({JELLYFIN_PORT})")
        sub_p = "/" if req_path == "/jellyfin" else raw_path[len("/jellyfin"):]
        return await proxy_http_request(f"http://127.0.0.1:{JELLYFIN_PORT}{sub_p}", request, default_prefix="/jellyfin", extra_headers={"X-Forwarded-Prefix": "/jellyfin"})
    
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
