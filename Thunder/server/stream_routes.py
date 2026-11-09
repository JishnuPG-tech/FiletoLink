import os
import mimetypes
# Thunder/server/stream_routes.py

import re
import secrets
import time
from urllib.parse import quote, unquote

from aiohttp import web

from Thunder import __version__, StartTime
from Thunder.bot import StreamBot, multi_clients, work_loads
from Thunder.server.exceptions import FileNotFound, InvalidHash
from Thunder.utils.bot_utils import quote_media_name
from Thunder.utils.canonical_files import (
    PUBLIC_HASH_LENGTH,
    get_file_by_hash,
    update_cached_file_id,
)
from Thunder.utils.custom_dl import ByteStreamer
from Thunder.utils.file_properties import get_media
from Thunder.utils.logger import logger
from Thunder.utils.render_template import render_media_page, render_page
from Thunder.utils.time_format import get_readable_time
from Thunder.vars import Var

routes = web.RouteTableDef()

# FlashFile Production Webapp path
WEBAPP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "webapp", "dist"))
WEBAPP_INDEX = os.path.join(WEBAPP_DIR, "index.html")
WEBAPP_ASSETS = os.path.join(WEBAPP_DIR, "assets")
WEBAPP_JS = os.path.join(WEBAPP_DIR, "js")
WEBAPP_IMAGES = os.path.join(WEBAPP_DIR, "images")

if os.path.exists(WEBAPP_ASSETS):
    routes.static("/assets", WEBAPP_ASSETS)
if os.path.exists(WEBAPP_JS):
    routes.static("/js", WEBAPP_JS)
if os.path.exists(WEBAPP_IMAGES):
    routes.static("/images", WEBAPP_IMAGES)

@routes.get("/motion_blur.png", allow_head=True)
async def serve_motion_blur(request):
    mb_path = os.path.join(WEBAPP_DIR, "motion_blur.png")
    if os.path.exists(mb_path):
        return web.FileResponse(mb_path)
    raise web.HTTPNotFound()

@routes.get("/dispatches", allow_head=True)
@routes.get("/api/live-dispatches", allow_head=True)
async def api_live_dispatches(request):
    try:
        from Thunder.utils.dispatches import get_live_dispatches_from_sources
        dispatches = await get_live_dispatches_from_sources(limit=30)
    except Exception as e:
        dispatches = []
    return web.json_response(
        {"ok": True, "count": len(dispatches), "dispatches": dispatches},
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"}
    )

SECURE_HASH_LENGTH = 6
CHUNK_SIZE = 1024 * 1024
MAX_CONCURRENT_PER_CLIENT = 8
RANGE_REGEX = re.compile(r"^bytes=(?P<start>\d*)-(?P<end>\d*)$")
PATTERN_HASH_FIRST = re.compile(
    rf"^([a-zA-Z0-9_-]{{{SECURE_HASH_LENGTH}}})(\d+)(?:/.*)?$")
PATTERN_ID_FIRST = re.compile(r"^(\d+)(?:/.*)?$")
VALID_HASH_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')
VALID_PUBLIC_HASH_REGEX = re.compile(rf'^[0-9a-f]{{{PUBLIC_HASH_LENGTH}}}$')
VALID_DISPOSITIONS = {"inline", "attachment"}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Range, Content-Type, *",
    "Access-Control-Expose-Headers": "Content-Length, Content-Range, Content-Disposition",
}

streamers = {}


def get_streamer(client_id: int) -> ByteStreamer:
    if client_id not in streamers:
        streamers[client_id] = ByteStreamer(multi_clients[client_id])
    return streamers[client_id]


def parse_media_request(path: str, query: dict) -> tuple[int, str]:
    clean_path = unquote(path).strip('/')

    match = PATTERN_HASH_FIRST.match(clean_path)
    if match:
        try:
            message_id = int(match.group(2))
            secure_hash = match.group(1)
            if (len(secure_hash) == SECURE_HASH_LENGTH and
                    VALID_HASH_REGEX.match(secure_hash)):
                return message_id, secure_hash
        except ValueError as e:
            raise InvalidHash(f"Invalid message ID format in path: {e}") from e

    match = PATTERN_ID_FIRST.match(clean_path)
    if match:
        try:
            message_id = int(match.group(1))
            secure_hash = query.get("hash", "").strip()
            if (len(secure_hash) == SECURE_HASH_LENGTH and
                    VALID_HASH_REGEX.match(secure_hash)):
                return message_id, secure_hash
            else:
                raise InvalidHash("Invalid or missing hash in query parameter")
        except ValueError as e:
            raise InvalidHash(f"Invalid message ID format in path: {e}") from e

    raise InvalidHash("Invalid URL structure or missing hash")


def validate_public_hash(public_hash: str) -> str:
    secure_hash = public_hash.strip().lower()
    if len(secure_hash) != PUBLIC_HASH_LENGTH or not VALID_PUBLIC_HASH_REGEX.match(secure_hash):
        raise InvalidHash("Invalid canonical file hash")
    return secure_hash


def select_optimal_client() -> tuple[int, ByteStreamer]:
    if not work_loads:
        raise web.HTTPInternalServerError(
            text=("No available clients to handle the request. "
                  "Please try again later."))

    available_clients = [
        (cid, load) for cid, load in work_loads.items()
        if load < MAX_CONCURRENT_PER_CLIENT]

    if available_clients:
        client_id = min(available_clients, key=lambda x: x[1])[0]
    else:
        client_id = min(work_loads, key=work_loads.get)

    return client_id, get_streamer(client_id)


def get_content_disposition(request: web.Request) -> str:
    disposition = request.query.get("disposition", "attachment").strip().lower()
    return disposition if disposition in VALID_DISPOSITIONS else "attachment"


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    if not range_header:
        return 0, file_size - 1

    match = RANGE_REGEX.fullmatch(range_header)
    if not match:
        raise web.HTTPBadRequest(text=f"Invalid range header: {range_header}")

    start_str = match.group("start")
    end_str = match.group("end")
    if start_str:
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
    else:
        if not end_str:
            raise web.HTTPBadRequest(text=f"Invalid range header: {range_header}")
        suffix_len = int(end_str)
        if suffix_len <= 0:
            raise web.HTTPRequestRangeNotSatisfiable(
                headers={"Content-Range": f"bytes */{file_size}"})
        start = max(file_size - suffix_len, 0)
        end = file_size - 1

    if start < 0 or end >= file_size or start > end:
        raise web.HTTPRequestRangeNotSatisfiable(
            headers={"Content-Range": f"bytes */{file_size}"}
        )

    return start, end


def _resolve_unique_id(file_info: dict) -> str:
    unique_id = file_info.get("unique_id") or file_info.get("file_unique_id")
    if not unique_id:
        raise FileNotFound("File unique ID not found in info.")
    return unique_id


def _resolve_filename(file_info: dict, mime_type: str) -> str:
    filename = file_info.get("file_name")
    if filename:
        return filename

    ext = mime_type.split('/')[-1] if '/' in mime_type else 'bin'
    ext_map = {'jpeg': 'jpg', 'mpeg': 'mp3', 'octet-stream': 'bin'}
    ext = ext_map.get(ext, ext)
    return f"file_{secrets.token_hex(4)}.{ext}"


async def _serve_media_response(
    request: web.Request,
    *,
    file_info: dict,
    streamer: ByteStreamer,
    client_id: int,
    media_ref: int | str,
    fallback_message_id: int | None = None,
    on_fallback_message=None
):
    file_size = int(file_info.get('file_size', 0) or 0)
    if file_size == 0:
        raise FileNotFound("File size is reported as zero or unavailable.")

    range_header = request.headers.get("Range", "")
    start, end = parse_range_header(range_header, file_size)
    content_length = end - start + 1

    if start == 0 and end == file_size - 1:
        range_header = ""

    raw_mime = file_info.get('mime_type')
    filename = _resolve_filename(file_info, raw_mime or "")
    mime_type = raw_mime
    if not mime_type or mime_type in ('application/octet-stream', 'application/x-tgm'):
        guessed, _ = mimetypes.guess_type(filename)
        if guessed:
            mime_type = guessed
        elif filename.lower().endswith('.mkv'):
            mime_type = 'video/x-matroska'
    if not mime_type:
        mime_type = 'application/octet-stream'
    disposition = get_content_disposition(request)

    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(content_length),
        "Content-Disposition": (
            f"{disposition}; filename*=UTF-8''{quote(filename, safe='')}"),
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=31536000",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Range, Content-Type, *",
        "Access-Control-Expose-Headers": (
            "Content-Length, Content-Range, Content-Disposition"),
        "X-Content-Type-Options": "nosniff"
    }

    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    if request.method == 'HEAD':
        work_loads[client_id] -= 1
        return web.Response(
            status=206 if range_header else 200,
            headers=headers
        )

    async def stream_generator():
        try:
            bytes_sent = 0
            bytes_to_skip = start % CHUNK_SIZE

            async for chunk in streamer.stream_file(
                media_ref,
                offset=start,
                limit=content_length,
                fallback_message_id=fallback_message_id,
                on_fallback_message=on_fallback_message
            ):
                if bytes_to_skip > 0:
                    if len(chunk) <= bytes_to_skip:
                        bytes_to_skip -= len(chunk)
                        continue
                    chunk = chunk[bytes_to_skip:]
                    bytes_to_skip = 0

                remaining = content_length - bytes_sent
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]

                if chunk:
                    yield chunk
                    bytes_sent += len(chunk)

                if bytes_sent >= content_length:
                    break
        finally:
            work_loads[client_id] -= 1

    return web.Response(
        status=206 if range_header else 200,
        body=stream_generator(),
        headers=headers
    )


@routes.get("/pay", allow_head=True)
async def upi_redirect_handler(request: web.Request):
    upi_uri = f"upi://pay?pa={Var.UPI_ID}&pn=DJ&am={Var.SUB_PRICE}&cu=INR"
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Pay ₹{Var.SUB_PRICE} - Flash File</title>
    <meta http-equiv="refresh" content="0; url={upi_uri}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1115; color: #fff; text-align: center; padding: 40px 20px; }}
        .card {{ max-width: 400px; margin: 0 auto; background: #181a20; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        h2 {{ margin-top: 0; color: #4ade80; }}
        .btn {{ display: block; background: #2563eb; color: #fff; text-decoration: none; padding: 14px 20px; border-radius: 12px; font-weight: bold; margin: 16px 0; }}
        .upi-box {{ background: #232730; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 16px; margin: 15px 0; user-select: all; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>⚡ Flash File Premium</h2>
        <p>Redirecting to your UPI app (Google Pay, PhonePe, Paytm)...</p>
        <a class="btn" href="{upi_uri}">Launch UPI App (₹{Var.SUB_PRICE})</a>
        <p style="color: #94a3b8; font-size: 14px;">Or copy UPI ID manually:</p>
        <div class="upi-box">{Var.UPI_ID}</div>
    </div>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

@routes.get("/", allow_head=True)
async def root_redirect(request):
    accept = request.headers.get("Accept", "")
    # If a browser requests HTML and the built webapp exists, serve FlashFile Showcase Webapp
    if ("text/html" in accept or "*/*" in accept) and os.path.exists(WEBAPP_INDEX):
        try:
            with open(WEBAPP_INDEX, "r", encoding="utf-8") as f:
                html = f.read()
            bot_username = getattr(StreamBot, "username", "") or "flashfilezbot"
            config_script = f'<script>window.__FLASHFILE_CONFIG__ = {{"bot_username": "{bot_username}", "server_name": "FlashFile", "channel_url": "https://t.me/flashfilez"}};</script>'
            html = html.replace("<head>", f"<head>{config_script}")
            return web.Response(
                text=html,
                content_type="text/html",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to serve FlashFile webapp HTML: {e}")

    # Fallback or API check response (curl, health probes, uptime monitors)
    return web.json_response({
        "server": {
            "status": "operational",
            "name": "FlashFile",
            "version": __version__,
        }
    })


@routes.get("/status", allow_head=True)
async def status_endpoint(request):
    uptime = time.time() - StartTime
    total_load = sum(work_loads.values())

    workload_distribution = {str(k): v for k, v in sorted(work_loads.items())}

    return web.json_response(
        {
            "server": {
                "status": "operational",
                "version": __version__,
                "uptime": get_readable_time(uptime)
            },
            "telegram_bot": {
                "username": f"@{StreamBot.username}",
                "active_clients": len(multi_clients)
            },
            "resources": {
                "total_workload": total_load,
                "workload_distribution": workload_distribution
            }
        },
        headers={"Access-Control-Allow-Origin": "*"}
    )


@routes.options("/status")
async def status_options(request: web.Request):
    return web.Response(headers={
        **CORS_HEADERS,
        "Access-Control-Max-Age": "86400"
    })


@routes.options(r"/{path:.+}")
async def media_options(request: web.Request):
    return web.Response(headers={
        **CORS_HEADERS,
        "Access-Control-Max-Age": "86400"
    })


@routes.get(r"/watch/f/{secure_hash}/{name:.+}", allow_head=True)
async def canonical_media_preview(request: web.Request):
    try:
        secure_hash = validate_public_hash(request.match_info["secure_hash"])
        file_record = await get_file_by_hash(secure_hash, raise_on_error=False)
        if not file_record:
            raise FileNotFound("Canonical file not found")

        file_name = file_record.get("file_name") or f"file_{secure_hash}"
        src = f"{Var.URL.rstrip('/')}/f/{secure_hash}/{quote_media_name(file_name)}"
        rendered_page = await render_media_page(file_name, src, requested_action='stream')

        response = web.Response(
            text=rendered_page,
            content_type='text/html',
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Range, Content-Type, *",
                "X-Content-Type-Options": "nosniff",
            }
        )
        response.enable_compression()
        return response
    except (InvalidHash, FileNotFound) as e:
        logger.debug(f"Canonical preview error: {type(e).__name__} - {e}", exc_info=True)
        raise web.HTTPNotFound(text="Resource not found") from e
    except Exception as e:
        error_id = secrets.token_hex(6)
        logger.error(f"Canonical preview error {error_id}: {e}", exc_info=True)
        raise web.HTTPInternalServerError(
            text=f"Server error occurred: {error_id}") from e


@routes.get(r"/watch/{path:.+}", allow_head=True)
async def media_preview(request: web.Request):
    try:
        path = request.match_info["path"]
        message_id, secure_hash = parse_media_request(path, request.query)

        rendered_page = await render_page(
            message_id, secure_hash, requested_action='stream')

        response = web.Response(
            text=rendered_page,
            content_type='text/html',
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Range, Content-Type, *",
                "X-Content-Type-Options": "nosniff",
            }
        )
        response.enable_compression()
        return response

    except (InvalidHash, FileNotFound) as e:
        logger.debug(
            f"Client error in preview: {type(e).__name__} - {e}",
            exc_info=True)
        raise web.HTTPNotFound(text="Resource not found") from e
    except Exception as e:
        error_id = secrets.token_hex(6)
        logger.error(f"Preview error {error_id}: {e}", exc_info=True)
        raise web.HTTPInternalServerError(
            text=f"Server error occurred: {error_id}") from e


@routes.get(r"/f/{secure_hash}/{name:.+}", allow_head=True)
async def canonical_media_delivery(request: web.Request):
    try:
        secure_hash = validate_public_hash(request.match_info["secure_hash"])
        file_record = await get_file_by_hash(secure_hash, raise_on_error=False)
        if not file_record:
            raise FileNotFound("Canonical file not found")

        client_id, streamer = select_optimal_client()
        work_loads[client_id] += 1

        try:
            _resolve_unique_id(file_record)
            media_ref = int(file_record["canonical_message_id"])
            fallback_message_id = int(file_record["canonical_message_id"])

            async def persist_refreshed_file_id(message):
                if client_id != 0:
                    return
                media = get_media(message)
                new_file_id = getattr(media, "file_id", None) if media else None
                if new_file_id and new_file_id != file_record.get("file_id"):
                    try:
                        await update_cached_file_id(file_record, new_file_id)
                    except Exception as e:
                        logger.warning(
                            f"Failed to refresh cached file_id for canonical file {secure_hash}: {e}",
                            exc_info=True
                        )

            return await _serve_media_response(
                request,
                file_info=file_record,
                streamer=streamer,
                client_id=client_id,
                media_ref=media_ref,
                fallback_message_id=fallback_message_id,
                on_fallback_message=persist_refreshed_file_id
            )
        except (FileNotFound, InvalidHash):
            work_loads[client_id] -= 1
            raise
        except Exception as e:
            work_loads[client_id] -= 1
            error_id = secrets.token_hex(6)
            logger.error(f"Canonical stream error {error_id}: {e}", exc_info=True)
            raise web.HTTPInternalServerError(
                text=f"Server error during streaming: {error_id}") from e
    except (InvalidHash, FileNotFound) as e:
        logger.debug(f"Canonical client error: {type(e).__name__} - {e}", exc_info=True)
        raise web.HTTPNotFound(text="Resource not found") from e
    except Exception as e:
        error_id = secrets.token_hex(6)
        logger.error(f"Canonical server error {error_id}: {e}", exc_info=True)
        raise web.HTTPInternalServerError(
            text=f"An unexpected server error occurred: {error_id}") from e


@routes.get(r"/{path:.+}", allow_head=True)
async def media_delivery(request: web.Request):
    try:
        path = request.match_info["path"]
        message_id, secure_hash = parse_media_request(path, request.query)

        client_id, streamer = select_optimal_client()

        work_loads[client_id] += 1

        try:
            file_info = await streamer.get_file_info(message_id)
            unique_id = _resolve_unique_id(file_info)

            if unique_id[:SECURE_HASH_LENGTH] != secure_hash:
                raise InvalidHash(
                    "Provided hash does not match file's unique ID.")
            return await _serve_media_response(
                request,
                file_info=file_info,
                streamer=streamer,
                client_id=client_id,
                media_ref=message_id
            )

        except (FileNotFound, InvalidHash):
            work_loads[client_id] -= 1
            raise
        except Exception as e:
            work_loads[client_id] -= 1
            error_id = secrets.token_hex(6)
            logger.error(
                f"Stream error {error_id}: {e}",
                exc_info=True)
            raise web.HTTPInternalServerError(
                text=f"Server error during streaming: {error_id}") from e

    except (InvalidHash, FileNotFound) as e:
        logger.debug(f"Client error: {type(e).__name__} - {e}", exc_info=True)
        raise web.HTTPNotFound(text="Resource not found") from e
    except Exception as e:
        error_id = secrets.token_hex(6)
        logger.error(f"Server error {error_id}: {e}", exc_info=True)
        raise web.HTTPInternalServerError(
            text=f"An unexpected server error occurred: {error_id}") from e
