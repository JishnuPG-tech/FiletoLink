"""
Apex Ops Router
===============
Admin-gated endpoints to inspect and manage the persistent `/data` volume
(Jellyfin folder included) from outside the space container.

Authentication:
  All endpoints require `Authorization: Bearer <secret>` where <secret> matches
  the space's `APEX_OPS_KEY` (falling back to `APEX_SECRET_KEY` or `HF_TOKEN`).
  Without it every route returns 401.
"""

import os
import hmac
import json
import shutil
import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("ApexOps")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

router = APIRouter(tags=["Ops"])

JELLYFIN_ROOT = "/data/jellyfin"
APEX_ROOT = "/data/apex"

def _jellyfin_auth_header() -> dict:
    """Build a MediaBrowser Authorization header accepted by Jellyfin 12+.

    Uses the APEX_JELLYFIN_API_KEY secret first, then any active row from the
    server's api_keys table. Returns {} when no key is available.
    """
    key = os.environ.get("APEX_JELLYFIN_API_KEY", "").strip().strip('"')
    if not key:
        for db in ("/opt/jellyfin-local/data/data/jellyfin.db", os.path.join(JELLYFIN_ROOT, "data", "data", "jellyfin.db")):
            if os.path.exists(db):
                try:
                    import sqlite3
                    with sqlite3.connect(db, timeout=5) as conn:
                        cur = conn.cursor()
                        cur.execute("PRAGMA table_info('api_keys')")
                        columns = [r[1] for r in cur.fetchall()]
                        if "AccessToken" in columns:
                            if "IsActive" in columns:
                                cur.execute("SELECT AccessToken FROM api_keys WHERE IsActive IS NOT 0 ORDER BY DateCreated DESC LIMIT 1")
                            else:
                                cur.execute("SELECT AccessToken FROM api_keys ORDER BY DateCreated DESC LIMIT 1")
                            row = cur.fetchone()
                            if row and row[0]:
                                key = str(row[0]).strip()
                                break
                except Exception as e:
                    logger.warning(f"[JELLYFIN] Could not read api_keys table from {db}: {e}")
    if not key:
        logger.warning("[JELLYFIN] No API key available for library refresh.")
        return {}
    return {
        "Authorization": (
            'MediaBrowser Client="ApexOps", Device="Gateway", '
            'DeviceId="apex-ops", Version="12.1.0", '
            f'Token="{key}"'
        ),
        "Accept": "application/json",
    }

INITIAL_DIRS = [
    os.path.join(JELLYFIN_ROOT, "data"),
    os.path.join(JELLYFIN_ROOT, "config"),
    os.path.join(JELLYFIN_ROOT, "cache"),
    os.path.join(JELLYFIN_ROOT, "log"),
    os.path.join(JELLYFIN_ROOT, "media", "Movies"),
    os.path.join(JELLYFIN_ROOT, "media", "TV Shows"),
    os.path.join(APEX_ROOT, "session"),
    os.path.join(APEX_ROOT, "backups"),
]


def _is_admin(request: Request) -> bool:
    secret = (
        os.environ.get("APEX_OPS_KEY")
        or os.environ.get("APEX_SECRET_KEY")
        or os.environ.get("HF_TOKEN")
    )
    if not secret:
        return False
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return False
    provided = auth[len("Bearer "):].strip()
    return hmac.compare_digest(provided, secret)


def _denied():
    return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)


def _build_tree(path: str, max_depth: int = 3, max_entries: int = 600):
    """Return a bounded, serializable directory tree below `path`."""
    result = {"path": path, "exists": os.path.exists(path)}

    def walk(current: str, depth: int, budget: list):
        node = {"path": current, "type": "dir"}
        try:
            names = sorted(os.listdir(current))
        except OSError as exc:
            node["error"] = str(exc)
            return node
        children = []
        for name in names:
            if budget[0] <= 0:
                children.append({"path": os.path.join(current, name), "type": "dir", "truncated": True})
                break
            budget[0] -= 1
            entry = os.path.join(current, name)
            try:
                if os.path.isdir(entry) and not os.path.islink(entry):
                    if depth < max_depth:
                        children.append(walk(entry, depth + 1, budget))
                    else:
                        children.append({"path": entry, "type": "dir"})
                else:
                    children.append({"path": entry, "type": "file", "size": os.path.getsize(entry)})
            except OSError as exc:
                children.append({"path": entry, "type": "error", "message": str(exc)})
        node["children"] = children
        return node

    if os.path.isdir(path):
        result["tree"] = walk(path, 0, [max_entries])
    else:
        result["tree"] = None
    return result


@router.get("/apex/ops/tree")
async def ops_tree(path: str = "/data", request: Request = None):
    if not _is_admin(request):
        return _denied()
    return JSONResponse(_build_tree(path))


READ_ROOTS = ("/data", "/opt/jellyfin-local")

@router.get("/apex/ops/read")
async def ops_read(path: str, tail: int = 0, lines: int = 200, request: Request = None):
    if not _is_admin(request):
        return _denied()

    normalized = os.path.abspath(path)
    if not any(normalized == root or normalized.startswith(root + os.sep) for root in READ_ROOTS):
        return JSONResponse({"ok": False, "error": f"path not allow-listed ({READ_ROOTS})"}, status_code=403)
    if not os.path.isfile(normalized):
        return JSONResponse({"ok": False, "error": "not a file or missing"}, status_code=404)

    try:
        size = os.path.getsize(normalized)
        if tail > 0:
            with open(normalized, "rb") as f:
                f.seek(max(0, size - tail))
                content = f.read()
        else:
            with open(normalized, "rb") as f:
                content = f.read()
    except OSError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    text = content.decode("utf-8", errors="replace")
    if tail <= 0 and lines > 0:
        part = text.splitlines()
        text = "\n".join(part[-lines:])
    return JSONResponse({"ok": True, "path": normalized, "size": size, "content": text})


@router.post("/apex/ops/jellyfin/reset")
async def ops_jellyfin_reset(request: Request):
    """Remove everything under /data/jellyfin and lay down a clean directory skeleton."""
    if not _is_admin(request):
        return _denied()

    removed = {"dirs": [], "files": [], "bytes": 0}
    if os.path.exists(JELLYFIN_ROOT):
        ordered = sorted(
            os.listdir(JELLYFIN_ROOT),
            key=lambda n: os.path.join(JELLYFIN_ROOT, n).count(os.sep),
            reverse=True,
        )
        for name in ordered:
            entry = os.path.join(JELLYFIN_ROOT, name)
            try:
                if os.path.isdir(entry) and not os.path.islink(entry):
                    size = 0
                    for root, _, files in os.walk(entry):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                size += os.path.getsize(fp)
                            except OSError:
                                pass
                    shutil.rmtree(entry)
                    removed["dirs"].append(name)
                    removed["bytes"] += size
                else:
                    try:
                        removed["bytes"] += os.path.getsize(entry)
                    except OSError:
                        pass
                    os.remove(entry)
                    removed["files"].append(name)
            except OSError as exc:
                return JSONResponse(
                    {"ok": False, "error": f"Failed to remove {entry}: {exc}", "removed": removed},
                    status_code=500,
                )

    os.makedirs("/data", exist_ok=True)
    for d in INITIAL_DIRS:
        os.makedirs(d, exist_ok=True)

    return JSONResponse({
        "ok": True,
        "jellyfin_root": JELLYFIN_ROOT,
        "removed": removed,
        "initialized": INITIAL_DIRS,
    })


@router.post("/apex/ops/jellyfin/init")
async def ops_jellyfin_init(request: Request):
    """Idempotently create the standard Jellyfin + Apex data directory skeleton."""
    if not _is_admin(request):
        return _denied()
    os.makedirs("/data", exist_ok=True)
    created = []
    for d in INITIAL_DIRS:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            created.append(d)
    return JSONResponse({"ok": True, "created": created, "base": INITIAL_DIRS})


@router.post("/apex/ops/jellyfin/scan")
async def ops_jellyfin_scan(request: Request):
    """Trigger a Jellyfin library refresh once the media server is up."""
    if not _is_admin(request):
        return _denied()
    import aiohttp

    headers = _jellyfin_auth_header()
    if not headers:
        return JSONResponse({"ok": False, "error": "No Jellyfin API key available"}, status_code=503)

    async with aiohttp.ClientSession(headers=headers) as session:
        for attempt in range(6):
            if attempt:
                logger.info(f"Retrying Jellyfin scan (attempt {attempt + 1})...")
            try:
                async with session.post("http://127.0.0.1:8096/Library/Refresh", timeout=10) as resp:
                    return JSONResponse({"ok": True, "status": resp.status})
            except Exception:
                await asyncio.sleep(5)
    return JSONResponse({"ok": False, "error": "Jellyfin not reachable after retries"}, status_code=502)


# Netflix-style community skin for the Jellyfin web UI. Injected through the
# server's branding configuration (BrandingOptions -> branding.xml, which lives
# on the /data/jellyfin/config volume) so it applies server-wide and survives
# restarts. Jellyfin 10.11+ no longer supports the legacy SystemConfiguration
# CustomCss field; the api is POST /System/Configuration/Branding.
JELLYFIN_THEME_CSS = (
    '@import url("https://raw.githubusercontent.com/Automationxperts/jellyflix/main/default.css");\n'
    '@import url("https://raw.githubusercontent.com/Automationxperts/jellyflix/main/Logo.css");\n'
    "/* App bar / sidebar logo */\n"
    ".imgLogoIcon {\n"
    "content: url('https://raw.githubusercontent.com/Automationxperts/jellyflix/main/img/logo.png') !important; }\n"
    "/* Main Drawer Mobile Logo */\n"
    ".adminDrawerLogo img {\n"
    "content: url('https://raw.githubusercontent.com/Automationxperts/jellyflix/main/img/logo.png') !important; }\n"
    "/* Home Page Logo */\n"
    ".pageTitleWithLogo {\n"
    "background-image: url('https://raw.githubusercontent.com/Automationxperts/jellyflix/main/img/logo.png') !important; }\n"
)

_JELLYFIN_BASE = "http://127.0.0.1:8096"


@router.post("/apex/ops/jellyfin/theme")
async def ops_jellyfin_theme(request: Request):
    """Apply (or clear) the server-wide custom-CSS skin on the Jellyfin web UI.

    Body: {"css": "<custom css>"}          -> replace; omit/empty to clear
          {"action": "status"}              -> report current value only
    The CSS is written through Jellyfin's branding endpoint
    (POST /System/Configuration/Branding, persisted to branding.xml on the
    /data/jellyfin/config volume) so it survives every container restart.
    """
    if not _is_admin(request):
        return _denied()
    import aiohttp

    headers = _jellyfin_auth_header()
    if not headers:
        return JSONResponse({"ok": False, "error": "No Jellyfin API key available"}, status_code=503)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(f"{_JELLYFIN_BASE}/Branding/Configuration", timeout=10) as resp:
                if resp.status != 200:
                    return JSONResponse({"ok": False, "error": f"GET Branding/Configuration -> {resp.status}"}, status_code=502)
                branding = await resp.json()
        except Exception as exc:
            return JSONResponse({"ok": False, "error": f"GET Branding/Configuration failed: {exc}"}, status_code=502)

        current = str(branding.get("CustomCss") or "")

        if str(payload.get("action") or "").lower() == "status":
            return JSONResponse({
                "ok": True,
                "applied": bool(current.strip()),
                "css_len": len(current),
                "css": current,
            })

        css = str(payload.get("css") or "").strip()
        if not css:
            css = JELLYFIN_THEME_CSS

        changed = current != css
        branding["CustomCss"] = css
        try:
            async with session.post(
                f"{_JELLYFIN_BASE}/System/Configuration/Branding",
                json=branding,
                timeout=10,
            ) as resp:
                if resp.status not in (200, 204):
                    return JSONResponse({"ok": False, "error": f"POST System/Configuration/Branding -> {resp.status}"}, status_code=502)
        except Exception as exc:
            return JSONResponse({"ok": False, "error": f"POST System/Configuration/Branding failed: {exc}"}, status_code=502)

        # Confirm the server actually persisted it in branding.xml.
        confirmed = False
        try:
            async with session.get(f"{_JELLYFIN_BASE}/Branding/Configuration", timeout=10) as resp:
                if resp.status == 200:
                    confirmed = str((await resp.json()).get("CustomCss") or "").strip() == css
        except Exception:
            pass

        return JSONResponse({
            "ok": True,
            "changed": changed,
            "confirmed": confirmed,
            "theme": "JellyFlix",
            "prev_css_len": len(current),
            "new_css_len": len(css),
        })


@router.api_route("/apex/ops/jellyfin/api", methods=["GET", "POST", "PUT", "DELETE"])
async def ops_jellyfin_api(request: Request):
    """Admin-gated passthrough to the internal Jellyfin API.

    Query: ?path=<api path incl. query string> e.g.
      /Items?Recursive=true&IncludeItemTypes=Movie&searchTerm=Mollywood
    Optional: &method=GET|POST|DELETE (default GET) — upstream verb to use.
              &body=<json>  (raw JSON body for POST; else the request body is used)
    The route itself accepts GET, POST and DELETE verbs, so a normal
    `POST /apex/ops/jellyfin/api?path=Repositories` (with a JSON request body)
    works as well as the GET-with-query-params form.
    Uses the server-side API key, so it survives behind the public proxy.
    """
    if not _is_admin(request):
        return _denied()
    import aiohttp

    headers = _jellyfin_auth_header()
    if not headers:
        return JSONResponse({"ok": False, "error": "No Jellyfin API key available"}, status_code=503)

    method = str(request.query_params.get("method") or request.method or "GET").upper()
    if method not in ("GET", "POST", "PUT", "DELETE"):
        return JSONResponse({"ok": False, "error": "method must be GET, POST, PUT or DELETE"}, status_code=400)

    api_path = str(request.query_params.get("path") or "").lstrip("/")
    if not api_path:
        return JSONResponse({"ok": False, "error": "Missing 'path' query param"}, status_code=400)
    if "\n" in api_path or "\r" in api_path:
        return JSONResponse({"ok": False, "error": "Invalid path"}, status_code=400)

    json_body = None
    if method in ("POST", "PUT"):
        raw_body = request.query_params.get("body")
        if raw_body is None:
            try:
                raw_body = (await request.body()).decode("utf-8") or None
            except Exception:
                raw_body = None
        if raw_body:
            try:
                json_body = json.loads(raw_body)
            except Exception:
                return JSONResponse({"ok": False, "error": "body must be valid JSON"}, status_code=400)

    url = f"{_JELLYFIN_BASE}/{api_path}"
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.request(method, url, json=json_body, timeout=60) as resp:
                body = await resp.text()
                ctype = resp.headers.get("content-type", "")
                if "application/json" in ctype:
                    try:
                        return JSONResponse({"ok": True, "status": resp.status, "data": json.loads(body)})
                    except Exception:
                        pass
                return JSONResponse({"ok": True, "status": resp.status, "text": body[:40000]})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": f"Jellyfin API call failed: {exc}"}, status_code=502)


@router.post("/apex/ops/jellyfin/cleanup")
async def ops_jellyfin_cleanup(request: Request):
    """Remove ghost library entries left behind by file relocations.

    Body: {"folders": ["/abs/path/to/dir", ...],
           "item_ids": ["<jellyfin item id>", ...]}
    A folder is only removed when it lives under /data/jellyfin. Our-streamer
    .strm files inside the folder are deleted first (content must reference
    the local streamer), then the directory is removed if it becomes empty.
    Each item_id is then deleted through the Jellyfin API (DELETE /Items/{id},
    best effort, tolerant of 404 when Jellyfin already dropped it).
    """
    if not _is_admin(request):
        return _denied()
    import aiohttp

    headers = _jellyfin_auth_header()
    if not headers:
        return JSONResponse({"ok": False, "error": "No Jellyfin API key available"}, status_code=503)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    folders = payload.get("folders") or []
    item_ids = payload.get("item_ids") or []
    results = {"folders": [], "items": []}

    stream_port = os.environ.get("TG_LISTEN_PORT", os.environ.get("PORT", "8080"))

    for folder in folders:
        folder = str(folder)
        if not folder.startswith("/data/jellyfin/"):
            results["folders"].append({"path": folder, "status": "skipped_not_under_data"})
            continue
        try:
            if not os.path.isdir(folder):
                results["folders"].append({"path": folder, "status": "not_found"})
                continue
            removed_strms = 0
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if not os.path.isfile(path) or not name.lower().endswith(".strm"):
                    continue
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read(256)
                except OSError:
                    continue
                if (
                    f"127.0.0.1:{stream_port}" not in content
                    and f"{stream_port}/stream" not in content
                ):
                    continue
                os.remove(path)
                removed_strms += 1
            remaining = os.listdir(folder)
            if remaining:
                results["folders"].append({
                    "path": folder,
                    "status": "not_empty",
                    "removed_streamer_strms": removed_strms,
                    "entries": remaining[:20],
                })
            else:
                shutil.rmtree(folder)
                results["folders"].append({"path": folder, "status": "removed", "removed_streamer_strms": removed_strms})
        except Exception as exc:
            results["folders"].append({"path": folder, "status": "error", "detail": str(exc)})

    async with aiohttp.ClientSession(headers=headers) as session:
        for item_id in item_ids:
            item_id = str(item_id).strip()
            if not item_id:
                continue
            try:
                async with session.delete(f"{_JELLYFIN_BASE}/Items/{item_id}", timeout=15) as resp:
                    results["items"].append({"id": item_id, "status": resp.status})
            except Exception as exc:
                results["items"].append({"id": item_id, "status": "error", "detail": str(exc)})

    return JSONResponse({"ok": True, "results": results})


@router.post("/apex/ops/jellyfin/cache/patch")
async def ops_jellyfin_cache_patch(request: Request):
    """Patch a single entry of the streamer's file_ids.json cache.

    Body: {"key": "<chat_id>:<msg_id>", "fields": {...}}

    Only safe path fields are honored (must stay under /data/jellyfin):
    target_dir, strm_path, _prev_strm_path, show_root. Other scalar fields
    (language, canonical_key, strm_base, year, ...) are applied verbatim.
    The cache file is written atomically (tmp + replace) so an interrupted
    save can never corrupt it.
    """
    if not _is_admin(request):
        return _denied()

    cache_path = os.path.join(JELLYFIN_ROOT, "file_ids.json")
    if not os.path.isfile(cache_path):
        return JSONResponse({"ok": False, "error": "cache file not found"}, status_code=404)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "body must be JSON"}, status_code=400)

    key = str(payload.get("key") or "").strip()
    fields = payload.get("fields")
    if not key or not isinstance(fields, dict) or not fields:
        return JSONResponse({"ok": False, "error": "key and non-empty fields required"}, status_code=400)

    try:
        with open(cache_path, "r", encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"cache unreadable: {exc}"}, status_code=500)

    if not isinstance(cache, dict) or not isinstance(cache.get(key), dict):
        return JSONResponse({"ok": False, "error": f"no cache entry for key '{key}'"}, status_code=404)

    path_fields = ("target_dir", "strm_path", "_prev_strm_path", "show_root")
    entry = cache[key]
    old = dict(entry)
    for name, value in fields.items():
        if name in path_fields:
            if value is None or value == "":
                entry.pop(name, None)
                continue
            text = str(value)
            if not text.startswith("/data/jellyfin/"):
                return JSONResponse(
                    {"ok": False, "error": f"field '{name}' must stay under /data/jellyfin"},
                    status_code=400,
                )
            entry[name] = text
        else:
            entry[name] = value

    cache[key] = entry
    tmp_path = cache_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, cache_path)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"cache write failed: {exc}"}, status_code=500)

    return JSONResponse({"ok": True, "old": old, "new": entry})


@router.post("/apex/ops/jellyfin/repositories")
async def ops_jellyfin_repositories(request: Request):
    """Write the plugin repository list straight into the on-disk system.xml.

    Body: {"repositories": [{"Name": "...", "Url": "...", "Enabled": true}]}

    Fallback helper that edits the live <PluginRepositories> element so the
    server reads it at the next start-up. Preferred path is the API
    passthrough (POST /Repositories via /apex/ops/jellyfin/api), which Jellyfin
    applies immediately and which its write-back loop also mirrors to /data.
    """
    if not _is_admin(request):
        return _denied()

    cfg_path = os.path.join(JELLYFIN_ROOT, "config", "system.xml")
    if not os.path.isfile(cfg_path):
        return JSONResponse({"ok": False, "error": "system.xml not found"}, status_code=404)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "body must be JSON"}, status_code=400)

    repositories = payload.get("repositories")
    if not isinstance(repositories, list):
        return JSONResponse({"ok": False, "error": "'repositories' must be a list"}, status_code=400)

    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(cfg_path)
        root = tree.getroot()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"system.xml unreadable: {exc}"}, status_code=500)

    repos_el = root.find(".//PluginRepositories")
    if repos_el is None:
        repos_el = ET.SubElement(root, "PluginRepositories")
    for child in list(repos_el):
        repos_el.remove(child)

    for repo in repositories:
        name = str(repo.get("Name") or repo.get("name") or "").strip()
        url = str(repo.get("Url") or repo.get("url") or "").strip()
        if not name or not url:
            return JSONResponse({"ok": False, "error": "each repository needs Name and Url"}, status_code=400)
        item = ET.SubElement(repos_el, "RepositoryInfo")
        ET.SubElement(item, "Name").text = name
        ET.SubElement(item, "Url").text = url
        ET.SubElement(item, "Enabled").text = "true" if repo.get("Enabled", True) else "false"

    tmp_path = cfg_path + ".tmp"
    try:
        tree.write(tmp_path, encoding="utf-8", xml_declaration=True)
        with open(tmp_path, "rb+") as fh:
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, cfg_path)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"system.xml write failed: {exc}"}, status_code=500)

    return JSONResponse({
        "ok": True,
        "wrote": len(repositories),
        "note": "Jellyfin reads this at start-up; restart the app (Space Restart) to apply.",
    })


@router.post("/apex/ops/space/restart")
async def ops_space_restart(request: Request):
    """Restart the HF Space runtime (no rebuild) so the Jellyfin process
    re-reads system.xml / config from the /data volume.
    """
    if not _is_admin(request):
        return _denied()

    token = os.environ.get("HF_TOKEN", "").strip()
    space_id = (os.environ.get("SPACE_ID") or os.environ.get("SPACE_REPO_NAME") or "").strip()
    if not space_id or "/" not in space_id:
        return JSONResponse({"ok": False, "error": "SPACE_ID env not set"}, status_code=500)
    if not token:
        return JSONResponse({"ok": False, "error": "HF_TOKEN not available"}, status_code=500)

    import aiohttp

    owner, name = space_id.split("/", 1)
    url = f"https://huggingface.co/api/spaces/{owner}/{name}/restart"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers={"Authorization": f"Bearer {token}"}, timeout=20) as resp:
                body = await resp.text()
                return JSONResponse({"ok": resp.status < 300, "status": resp.status, "detail": body[:400]})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"restart call failed: {exc}"}, status_code=502)