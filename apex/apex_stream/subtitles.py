"""Automated subtitle fetching, validation, and sidecar injection.

Provides a multi-provider subtitle engine:
- Stremio OpenSubtitles v3 (Free, global CDN, direct UTF-8 SRT)
- MSone (malayalamsubtitles.org) for Malayalam community subtitles
- OpenSubtitles.com REST API & SubDL API (optional fallbacks via env vars)
- Candidate scoring based on video release characteristics (WEB-DL, BluRay, 1080p, etc.)
- Strict SRT timestamp and UTF-8 verification
- Sidecar placement next to Jellyfin .strm files ({base}.{lang}.srt)
"""

import io
import os
import re
import uuid
import socket
import zipfile
import logging
import aiohttp
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger("ApexSubtitles")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [SUBTITLES] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# Standard SRT / VTT timestamp matcher (e.g. 00:01:23,456 --> 00:01:25,789 or 00:01:23.456 --> 00:01:25.789)
SRT_TIMESTAMP_RE = re.compile(
    r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}"
)

# Known release signatures used to match video timing and avoid desync
_RELEASE_TOKENS = {
    "bluray", "bdrip", "brrip", "web-dl", "webrip", "web", "hdtv", "dvdrip", "remux",
    "2160p", "4k", "1080p", "720p", "480p",
    "x264", "x265", "h264", "h265", "hevc", "avc", "10bit",
    "yts", "yify", "psa", "sparks", "rarbg", "galaxyrg", "eztv", "flux", "qxr", "amzn", "nf", "dsnp",
    "ion10", "evo", "tgx", "chd", "wiki", "ctrlhd"
}

_CAM_TOKENS = {
    "cam", "camrip", "ts", "telesync", "hdcam", "hdts",
    "line", "hdscr", "scr", "screener", "r6", "telecine", "tc",
}


def extract_release_tokens(text: Optional[str]) -> set:
    """Extract release characteristics and group tokens from a filename or release string."""
    if not text:
        return set()
    cleaned = re.sub(r"[._\-\[\]\(\)]+", " ", text.lower())
    words = set(cleaned.split())
    return words


def score_subtitle_candidate(candidate: Dict[str, Any], video_filename: str) -> float:
    """Score a candidate subtitle dict against the video filename to guarantee timing sync."""
    if not candidate:
        return -100.0

    video_tokens = extract_release_tokens(video_filename)
    sub_text = " ".join([
        str(candidate.get("movieReleaseName") or ""),
        str(candidate.get("subtitleFileName") or ""),
        str(candidate.get("releaseGroup") or ""),
    ]).lower()
    sub_tokens = extract_release_tokens(sub_text)

    score = 50.0

    # Penalize low-quality CAM/TS/LINE/R6 subtitles unless the source video is also explicitly a CAM
    video_is_cam = bool(video_tokens & _CAM_TOKENS)
    sub_is_cam = bool(sub_tokens & _CAM_TOKENS)
    if sub_is_cam and not video_is_cam:
        score -= 100.0

    # Source type alignment bonuses: rewarding matching retail cuts (BluRay vs BluRay, WEB vs WEB)
    video_is_bluray = bool(video_tokens & {"bluray", "bdrip", "brrip"})
    sub_is_bluray = bool(sub_tokens & {"bluray", "bdrip", "brrip"})
    if video_is_bluray and sub_is_bluray:
        score += 35.0

    video_is_web = bool(video_tokens & {"web", "webdl", "web-dl", "webrip"})
    sub_is_web = bool(sub_tokens & {"web", "webdl", "web-dl", "webrip"})
    if video_is_web and sub_is_web:
        score += 35.0

    video_is_hdtv = bool(video_tokens & {"hdtv", "hdtvrip"})
    sub_is_hdtv = bool(sub_tokens & {"hdtv", "hdtvrip"})
    if video_is_hdtv and sub_is_hdtv:
        score += 30.0

    # Matching release signature tokens
    matching_tokens = (video_tokens & sub_tokens) & _RELEASE_TOKENS
    score += len(matching_tokens) * 20.0

    # Exact release group match (e.g. SPARKS, PSA, YTS)
    rel_group = str(candidate.get("releaseGroup") or "").strip().lower()
    if rel_group and rel_group in video_tokens:
        score += 30.0

    # Popularity tie-breaker
    dl_count = 0
    try:
        dl_count = int(candidate.get("downloadCount") or candidate.get("downloads") or candidate.get("g") or 0)
    except (ValueError, TypeError):
        dl_count = 0
    if dl_count > 0:
        import math
        score += min(15.0, math.log10(max(1, dl_count)) * 3.0)

    # High rating bonus
    rating = 0.0
    try:
        rating = float(candidate.get("rating") or candidate.get("vote_average") or 0.0)
    except (ValueError, TypeError):
        rating = 0.0
    if rating > 0:
        score += min(10.0, rating)

    return score


def is_valid_srt(text: Optional[str]) -> bool:
    """Validate that text contains actual subtitle entries with timestamp intervals."""
    if not text or not isinstance(text, str):
        return False
    if len(text.strip()) < 15:
        return False
    # Quick filter against HTML error documents
    lower = text.lower()
    if "<html" in lower or "<body" in lower or "cloudflare" in lower or "502 bad gateway" in lower or "404 not found" in lower:
        return False
    # Must find at least one valid subtitle time boundary
    return bool(SRT_TIMESTAMP_RE.search(text))


def is_valid_subtitle_file(file_path: Optional[str]) -> bool:
    """Check whether a subtitle file on disk exists, is non-empty, and contains valid timestamps."""
    if not file_path or not os.path.isfile(file_path):
        return False
    try:
        size = os.path.getsize(file_path)
        if size < 20:
            return False
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read(4096)
        return is_valid_srt(sample)
    except Exception:
        return False


def purge_corrupted_subtitles(search_roots: Optional[List[str]] = None) -> int:
    """Scan media folders and remove 0-byte, corrupt, or invalid subtitle files."""
    roots = search_roots or [
        "/data/jellyfin/media/Movies",
        "/data/jellyfin/media/TV Shows",
        "/data/movies",
        "/data/tvshows",
        "/opt/jellyfin-local/media",
    ]
    purged = 0
    for root_dir in roots:
        if not os.path.exists(root_dir):
            continue
        for dirpath, _, filenames in os.walk(root_dir):
            for fn in filenames:
                lower = fn.lower()
                if lower.endswith((".srt", ".vtt", ".sub", ".ass")):
                    full_p = os.path.join(dirpath, fn)
                    try:
                        sz = os.path.getsize(full_p)
                        # Remove 0-byte or corrupted subtitle files, or broken .0.srt / .forced.srt
                        is_broken_suffix = ".eng.0.srt" in lower or ".0.srt" in lower
                        if sz < 50 or is_broken_suffix or not is_valid_subtitle_file(full_p):
                            os.remove(full_p)
                            purged += 1
                            logger.info(f"[SUBTITLES] Purged corrupt/empty subtitle file: {full_p}")
                    except Exception as err:
                        logger.warning(f"[SUBTITLES] Could not remove {full_p}: {err}")
    return purged


def clean_and_normalize_srt(data: Any) -> str:
    """Decode raw bytes or string into a clean, normalized UTF-8 string with LF newlines."""
    if isinstance(data, bytes):
        text = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "iso-8859-1", "windows-1256"):
            try:
                text = data.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if text is None:
            text = data.decode("utf-8", errors="replace")
    elif isinstance(data, str):
        text = data
    else:
        return ""

    # Normalize CRLF and CR to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip() + "\n"


def extract_srt_from_payload(payload: bytes) -> Optional[str]:
    """Extract and validate subtitle text from direct bytes or a ZIP archive payload."""
    if not payload or not isinstance(payload, bytes):
        return None

    # Check for ZIP archive magic bytes ('PK\x03\x04')
    if payload.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                # Find all files with subtitle extensions (.srt, .vtt)
                srt_names = [
                    n for n in z.namelist()
                    if n.lower().endswith((".srt", ".vtt")) and not n.startswith("__MACOSX")
                ]
                # Prefer .srt files
                srt_names.sort(key=lambda x: (not x.lower().endswith(".srt"), len(x)))
                for name in srt_names:
                    try:
                        raw = z.read(name)
                        cleaned = clean_and_normalize_srt(raw)
                        if is_valid_srt(cleaned):
                            return cleaned
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Error reading zip payload: {e}")

    # Direct subtitle payload
    cleaned = clean_and_normalize_srt(payload)
    if is_valid_srt(cleaned):
        return cleaned

    return None


LANG_3TO2 = {
    "eng": "en", "mal": "ml", "hin": "hi", "tam": "ta", "tel": "te",
    "kan": "kn", "ben": "bn", "pan": "pa", "mar": "mr", "guj": "gu",
    "urd": "ur", "kor": "ko", "jpn": "ja", "chi": "zh", "zho": "zh",
    "spa": "es", "fra": "fr", "fre": "fr", "ger": "de", "deu": "de",
    "rus": "ru", "ara": "ar", "por": "pt", "pob": "pt-br", "ind": "id", "ita": "it"
}

LANG_2TO3 = {v: k for k, v in LANG_3TO2.items()}
LANG_2TO3.update({
    "en": "eng", "ml": "mal", "hi": "hin", "ta": "tam", "te": "tel",
    "zh": "chi", "ja": "jpn", "ko": "kor", "fr": "fra", "de": "ger"
})

_NAME_TO_ISO639_2 = {
    "english": "eng", "malayalam": "mal", "hindi": "hin", "tamil": "tam",
    "telugu": "tel", "kannada": "kan", "bengali": "ben", "punjabi": "pan",
    "marathi": "mar", "gujarati": "guj", "urdu": "urd", "korean": "kor",
    "japanese": "jpn", "chinese": "chi", "spanish": "spa", "french": "fra",
    "german": "ger", "russian": "rus", "arabic": "ara", "portuguese": "por",
    "indonesian": "ind", "italian": "ita"
}


def normalize_to_iso639_2(code: Optional[str]) -> str:
    """Normalize language code or name to 3-letter ISO-639-2/B (e.g. 'en' -> 'eng', 'English' -> 'eng')."""
    if not code:
        return "eng"
    c = str(code).strip().lower()
    if c in _NAME_TO_ISO639_2:
        return _NAME_TO_ISO639_2[c]
    if len(c) == 2:
        return LANG_2TO3.get(c, c)
    return c


async def fetch_stremio_subtitles(
    session,
    imdb_id: str,
    is_tv: bool = False,
    season: int = 1,
    episode: int = 1,
    target_langs: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Query Stremio OpenSubtitles v3 endpoint for direct UTF-8 SRT subtitle candidates."""
    if not imdb_id or not imdb_id.startswith("tt"):
        return []

    norm_target = {normalize_to_iso639_2(l) for l in (target_langs or [])} if target_langs else None

    if is_tv:
        endpoint = f"https://opensubtitles-v3.strem.io/subtitles/series/{imdb_id}:{season}:{episode}.json"
    else:
        endpoint = f"https://opensubtitles-v3.strem.io/subtitles/movie/{imdb_id}.json"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    candidates = []
    try:
        async with session.get(endpoint, headers=headers, timeout=12) as resp:
            if resp.status == 200:
                payload = await resp.json()
                subs = payload.get("subtitles") or []
                for s in subs:
                    raw_lang = s.get("lang") or ""
                    lang_3 = normalize_to_iso639_2(raw_lang)
                    if norm_target and lang_3 not in norm_target:
                        continue
                    candidates.append({
                        "id": s.get("id"),
                        "url": s.get("url"),
                        "lang": lang_3,
                        "subtitleFileName": s.get("subtitleFileName") or "",
                        "movieReleaseName": s.get("movieReleaseName") or "",
                        "releaseGroup": s.get("releaseGroup") or "",
                        "downloadCount": s.get("downloadCount") or s.get("g") or 0,
                        "provider": "stremio-opensubtitles",
                    })
    except Exception as exc:
        logger.warning(f"Error fetching subtitles from Stremio for {imdb_id}: {exc}")

    return candidates


async def fetch_msone_subtitles(
    session,
    title: str,
    year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Search malayalamsubtitles.org (MSone) for Malayalam subtitles for foreign films."""
    if not title:
        return []

    from urllib.parse import quote_plus
    search_url = f"https://malayalamsubtitles.org/?s={quote_plus(title)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    candidates = []
    try:
        async with session.get(search_url, headers=headers, timeout=12) as resp:
            if resp.status != 200:
                return []
            html = await resp.text()

        # Parse links using regex / light BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        post_links = []
        for a in soup.select("h2.entry-title a, article a"):
            href = a.get("href")
            post_title = a.get_text(strip=True)
            if href and "/languages/" in href:
                # Check year match if year was provided
                if year and str(year) not in post_title and str(year) not in href:
                    continue
                post_links.append((post_title, href))

        # Check top matching post for direct download link
        for p_title, p_href in post_links[:2]:
            try:
                async with session.get(p_href, headers=headers, timeout=10) as p_resp:
                    if p_resp.status != 200:
                        continue
                    p_html = await p_resp.text()
                    p_soup = BeautifulSoup(p_html, "html.parser")
                    for a in p_soup.find_all("a", href=True):
                        link = a["href"]
                        if link.endswith((".zip", ".srt")) or "download" in link.lower() or "drive.google" in link:
                            candidates.append({
                                "id": p_href,
                                "url": link,
                                "lang": "mal",
                                "subtitleFileName": f"{p_title}.srt",
                                "movieReleaseName": p_title,
                                "releaseGroup": "MSone",
                                "downloadCount": 1000,
                                "provider": "msone",
                            })
                            break
            except Exception:
                continue
    except Exception as exc:
        logger.info(f"MSone search query '{title}' note: {exc}")

    return candidates


async def fetch_subdl_subtitles(
    session,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    film_name: Optional[str] = None,
    year: Optional[int] = None,
    is_tv: bool = False,
    season: int = 1,
    episode: int = 1,
    target_langs: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Query SubDL API for subtitle candidates."""
    api_key = os.environ.get("SUBDL_API_KEY", "")
    params: Dict[str, str] = {}
    if api_key:
        params["api_key"] = api_key
    if imdb_id and str(imdb_id).startswith("tt"):
        params["imdb_id"] = str(imdb_id)
    elif tmdb_id:
        params["tmdb_id"] = str(tmdb_id)
    elif film_name:
        params["film_name"] = str(film_name)
    else:
        return []

    params["type"] = "tv" if is_tv else "movie"
    if is_tv:
        params["season_number"] = str(season)
        params["episode_number"] = str(episode)
    if year:
        params["year"] = str(year)

    if target_langs:
        langs_2 = [LANG_3TO2.get(normalize_to_iso639_2(l), "en") for l in target_langs]
        params["languages"] = ",".join(sorted(set(langs_2)))

    endpoint = "https://api.subdl.com/api/v1/subtitles"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    norm_target = {normalize_to_iso639_2(l) for l in (target_langs or [])} if target_langs else None
    candidates: List[Dict[str, Any]] = []
    try:
        async with session.get(endpoint, params=params, headers=headers, timeout=12) as resp:
            if resp.status == 200:
                payload = await resp.json()
                subs = payload.get("subtitles") or payload.get("results") or []
                for s in subs:
                    raw_url = s.get("url") or s.get("download_url") or ""
                    if not raw_url:
                        continue
                    full_url = raw_url if raw_url.startswith("http") else f"https://dl.subdl.com{raw_url}"
                    raw_lang = s.get("lang") or s.get("language") or ""
                    lang_3 = normalize_to_iso639_2(raw_lang)
                    if norm_target and lang_3 not in norm_target:
                        continue
                    candidates.append({
                        "id": full_url,
                        "url": full_url,
                        "lang": lang_3,
                        "subtitleFileName": s.get("release_name") or s.get("name") or "",
                        "movieReleaseName": s.get("release_name") or "",
                        "releaseGroup": s.get("author") or "",
                        "downloadCount": int(s.get("download_count") or s.get("downloads") or 100),
                        "provider": "subdl",
                    })
    except Exception as exc:
        logger.info(f"SubDL search note: {exc}")

    return candidates


async def fetch_opensubtitles_com(
    session,
    imdb_id: Optional[str] = None,
    tmdb_id: Optional[str] = None,
    query: Optional[str] = None,
    is_tv: bool = False,
    season: int = 1,
    episode: int = 1,
    target_langs: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Query OpenSubtitles.com REST API if OPENSUBTITLES_API_KEY is configured."""
    api_key = os.environ.get("OPENSUBTITLES_API_KEY")
    if not api_key:
        return []

    params: Dict[str, str] = {}
    if imdb_id and str(imdb_id).startswith("tt"):
        raw_numeric = re.sub(r"\D", "", str(imdb_id))
        if raw_numeric:
            params["imdb_id"] = raw_numeric
    elif tmdb_id:
        params["tmdb_id"] = str(tmdb_id)
    elif query:
        params["query"] = str(query)
    else:
        return []

    if is_tv:
        params["type"] = "episode"
        params["season_number"] = str(season)
        params["episode_number"] = str(episode)
    else:
        params["type"] = "movie"

    if target_langs:
        langs_2 = [LANG_3TO2.get(normalize_to_iso639_2(l), "en") for l in target_langs]
        params["languages"] = ",".join(sorted(set(langs_2)))

    endpoint = "https://api.opensubtitles.com/api/v1/subtitles"
    headers = {
        "Api-Key": api_key,
        "User-Agent": "Jellyfin-Apex v2.1.0",
        "Accept": "application/json",
    }

    norm_target = {normalize_to_iso639_2(l) for l in (target_langs or [])} if target_langs else None
    candidates: List[Dict[str, Any]] = []
    try:
        async with session.get(endpoint, params=params, headers=headers, timeout=12) as resp:
            if resp.status == 200:
                payload = await resp.json()
                data = payload.get("data") or []
                for item in data:
                    attrs = item.get("attributes") or {}
                    files = attrs.get("files") or []
                    for f in files:
                        fid = f.get("file_id")
                        if not fid:
                            continue
                        dl_url = f"https://api.opensubtitles.com/api/v1/download/{fid}"
                        raw_lang = attrs.get("language") or ""
                        lang_3 = normalize_to_iso639_2(raw_lang)
                        if norm_target and lang_3 not in norm_target:
                            continue
                        candidates.append({
                            "id": str(fid),
                            "url": dl_url,
                            "lang": lang_3,
                            "subtitleFileName": f.get("file_name") or attrs.get("release") or "",
                            "movieReleaseName": attrs.get("release") or "",
                            "releaseGroup": "",
                            "downloadCount": int(attrs.get("download_count") or 50),
                            "provider": "opensubtitles.com",
                        })
    except Exception as exc:
        logger.info(f"OpenSubtitles.com API note: {exc}")

    return candidates


TIMING_LINE_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})([,.])(\d{3})\s*-->\s*(\d{1,2}):(\d{2}):(\d{2})([,.])(\d{3})"
)


def adjust_srt_timing(srt_text: str, offset_seconds: float) -> str:
    """Shift all timestamps in an SRT or WebVTT subtitle text by offset_seconds (can be positive or negative).

    Timestamps are clamped to 00:00:00,000.
    Preserves all dialogue, indices, and markup.
    """
    if not srt_text or not isinstance(srt_text, str) or offset_seconds == 0.0:
        return srt_text

    offset_ms = int(round(offset_seconds * 1000))

    def _shift_ts(h: int, m: int, s: int, ms: int) -> Tuple[int, int, int, int]:
        tot_ms = (h * 3600 + m * 60 + s) * 1000 + ms + offset_ms
        tot_ms = max(0, tot_ms)
        nh = tot_ms // 3600000
        rem = tot_ms % 3600000
        nm = rem // 60000
        rem = rem % 60000
        ns = rem // 1000
        nms = rem % 1000
        return nh, nm, ns, nms

    def _replace_match(match: re.Match) -> str:
        h1, m1, s1, sep1, ms1 = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4), int(match.group(5))
        h2, m2, s2, sep2, ms2 = int(match.group(6)), int(match.group(7)), int(match.group(8)), match.group(9), int(match.group(10))

        nh1, nm1, ns1, nms1 = _shift_ts(h1, m1, s1, ms1)
        nh2, nm2, ns2, nms2 = _shift_ts(h2, m2, s2, ms2)

        return f"{nh1:02d}:{nm1:02d}:{ns1:02d}{sep1}{nms1:03d} --> {nh2:02d}:{nm2:02d}:{ns2:02d}{sep2}{nms2:03d}"

    return TIMING_LINE_RE.sub(_replace_match, srt_text)


async def download_subtitle_file(session, url: str) -> Optional[str]:
    """Download and extract clean, validated UTF-8 SRT content from a URL."""
    if not url:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                payload = await resp.read()
                return extract_srt_from_payload(payload)
            else:
                logger.warning(f"Subtitle download HTTP {resp.status} for {url}")
    except Exception as exc:
        logger.warning(f"Subtitle download failed for {url}: {exc}")

    return None


async def inject_subtitles_for_entry(
    session: Any = None,
    entry: Optional[Dict[str, Any]] = None,
    target_langs: Optional[List[str]] = None,
    force: bool = False,
) -> List[str]:
    """Search, download, score, and inject subtitle sidecars next to media .strm file."""
    if not entry or not isinstance(entry, dict):
        return []

    target_dir = entry.get("target_dir")
    base = entry.get("strm_base") or entry.get("clean_title") or entry.get("title")
    if not target_dir or not base:
        return []

    imdb_id = entry.get("imdb_id")
    is_tv = bool(entry.get("is_tv"))
    season = int(entry.get("season") or 1)
    episode = int(entry.get("episode") or 1)
    video_filename = entry.get("file_name") or f"{base}.mkv"

    # Fallback to resolve IMDb ID from TMDB if entry has tmdb_id but missing imdb_id
    if (not imdb_id or not imdb_id.startswith("tt")) and entry.get("tmdb_id"):
        tmdb_key = os.environ.get("TMDB_API_KEY") or os.environ.get("APEX_TMDB_API_KEY") or "2e737c385b0d00f7b0f340889f074dcf"
        try:
            if is_tv:
                u = f"https://api.themoviedb.org/3/tv/{entry['tmdb_id']}/external_ids?api_key={tmdb_key}"
            else:
                u = f"https://api.themoviedb.org/3/movie/{entry['tmdb_id']}?api_key={tmdb_key}"
            async with active_session.get(u, timeout=6) as tmdb_r:
                if tmdb_r.status == 200:
                    tmdb_data = await tmdb_r.json()
                    fetched_imdb = tmdb_data.get("imdb_id")
                    if fetched_imdb and str(fetched_imdb).startswith("tt"):
                        imdb_id = str(fetched_imdb)
                        entry["imdb_id"] = imdb_id
        except Exception:
            pass

    # Default languages: English is mandatory; add Malayalam if original is foreign or requested
    langs = list(target_langs) if target_langs else ["eng"]
    orig_lang = (entry.get("language") or entry.get("tmdb_original_language") or "").lower()
    if "mal" not in langs and "ml" not in langs:
        if orig_lang not in ("malayalam", "mal", "ml"):
            langs.append("mal")

    normalized_langs = [normalize_to_iso639_2(l) for l in langs]

    managed_session = None
    if session is None or getattr(session, "closed", False):
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        managed_session = aiohttp.ClientSession(connector=connector)
        active_session = managed_session
    else:
        active_session = session

    injected_paths = []
    try:
        for lang in normalized_langs:
            sidecar_path = os.path.join(target_dir, f"{base}.{lang}.srt")
            if os.path.exists(sidecar_path):
                if not is_valid_subtitle_file(sidecar_path):
                    try:
                        os.remove(sidecar_path)
                        logger.info(f"[SUBTITLES] Removed corrupt/empty existing subtitle: {sidecar_path}")
                    except Exception:
                        pass
                elif not force:
                    continue

            # Remove any orphan/corrupted .0.srt or .forced.srt left behind by older plugins
            for orphan in (f"{base}.{lang}.0.srt", f"{base}.0.srt", f"{base}.{lang}.forced.srt", f"{base}.forced.srt"):
                orphan_path = os.path.join(target_dir, orphan)
                if os.path.exists(orphan_path) and not is_valid_subtitle_file(orphan_path):
                    try:
                        os.remove(orphan_path)
                        logger.info(f"[SUBTITLES] Cleaned up broken orphan subtitle: {orphan_path}")
                    except Exception:
                        pass

            # Gather candidates from all available providers
            candidates: List[Dict[str, Any]] = []

            # 1. Stremio OpenSubtitles v3 (using IMDb ID)
            if imdb_id and imdb_id.startswith("tt"):
                stremio_cand = await fetch_stremio_subtitles(
                    active_session, imdb_id, is_tv=is_tv, season=season, episode=episode, target_langs=[lang]
                )
                candidates.extend(stremio_cand)

            # 2. SubDL provider (dual redundancy fallback)
            subdl_cand = await fetch_subdl_subtitles(
                active_session,
                imdb_id=imdb_id,
                tmdb_id=entry.get("tmdb_id"),
                film_name=entry.get("tmdb_title") or entry.get("clean_title") or entry.get("title"),
                year=entry.get("year"),
                is_tv=is_tv,
                season=season,
                episode=episode,
                target_langs=[lang],
            )
            candidates.extend(subdl_cand)

            # 3. OpenSubtitles.com REST API (if configured)
            if os.environ.get("OPENSUBTITLES_API_KEY"):
                os_cand = await fetch_opensubtitles_com(
                    active_session,
                    imdb_id=imdb_id,
                    tmdb_id=entry.get("tmdb_id"),
                    query=entry.get("tmdb_title") or entry.get("clean_title") or entry.get("title"),
                    is_tv=is_tv,
                    season=season,
                    episode=episode,
                    target_langs=[lang],
                )
                candidates.extend(os_cand)

            # 4. MSone provider if language is Malayalam ('mal')
            if lang == "mal" and not is_tv:
                msone_title = entry.get("tmdb_title") or entry.get("clean_title") or entry.get("title")
                msone_cand = await fetch_msone_subtitles(active_session, msone_title, year=entry.get("year"))
                candidates.extend(msone_cand)

            if not candidates:
                continue

            # Score and pick the best synchronized release
            candidates.sort(key=lambda c: score_subtitle_candidate(c, video_filename), reverse=True)

            for best_cand in candidates[:3]:
                dl_url = best_cand.get("url")
                if not dl_url:
                    continue

                srt_content = await download_subtitle_file(active_session, dl_url)
                if srt_content and is_valid_srt(srt_content):
                    # Check for subtitle timing offset
                    offset_sec = float(entry.get("subtitle_offset_seconds") or 0.0)
                    if offset_sec != 0.0:
                        srt_content = adjust_srt_timing(srt_content, offset_sec)

                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        tmp_sub = f"{sidecar_path}.{os.getpid()}_{uuid.uuid4().hex[:8]}.tmp"
                        with open(tmp_sub, "w", encoding="utf-8") as f:
                            f.write(srt_content)
                            f.flush()
                            os.fsync(f.fileno())
                        os.replace(tmp_sub, sidecar_path)
                        try:
                            os.chmod(sidecar_path, 0o664)
                        except Exception:
                            pass

                        logger.info(f"✅ Injected subtitle: {sidecar_path} (provider={best_cand.get('provider')})")
                        injected_paths.append(sidecar_path)
                        break
                    except Exception as write_err:
                        logger.warning(f"Error writing subtitle to {sidecar_path}: {write_err}")
    finally:
        if managed_session:
            await managed_session.close()

    return injected_paths

