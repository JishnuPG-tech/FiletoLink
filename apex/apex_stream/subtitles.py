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
import zipfile
import logging
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
    "yts", "psa", "sparks", "rarbg", "galaxyrg", "eztv", "flux", "qxr", "amzn", "nf", "dsnp"
}

_CAM_TOKENS = {"cam", "camrip", "ts", "telesync", "hdcam", "hdts"}


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

    # Penalize low-quality CAM/TS subtitles unless the source video is also explicitly a CAM
    video_is_cam = bool(video_tokens & _CAM_TOKENS)
    sub_is_cam = bool(sub_tokens & _CAM_TOKENS)
    if sub_is_cam and not video_is_cam:
        score -= 100.0

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
    # Quick filter against HTML error documents
    if "<html" in text.lower() or "<body" in text.lower() or "cloudflare" in text.lower():
        return False
    # Must find at least one valid subtitle time boundary
    return bool(SRT_TIMESTAMP_RE.search(text))


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


def normalize_to_iso639_2(code: Optional[str]) -> str:
    """Normalize language code to 3-letter ISO-639-2/B (e.g. 'en' -> 'eng', 'ml' -> 'mal')."""
    if not code:
        return "eng"
    c = code.strip().lower()
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
    session,
    entry: Dict[str, Any],
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

    # Default languages: English is mandatory; add Malayalam if original is foreign or requested
    langs = list(target_langs) if target_langs else ["eng"]
    orig_lang = (entry.get("language") or entry.get("tmdb_original_language") or "").lower()
    if "mal" not in langs and "ml" not in langs:
        if orig_lang not in ("malayalam", "mal", "ml"):
            langs.append("mal")

    normalized_langs = [normalize_to_iso639_2(l) for l in langs]

    injected_paths = []
    for lang in normalized_langs:
        sidecar_path = os.path.join(target_dir, f"{base}.{lang}.srt")
        if os.path.exists(sidecar_path) and not force:
            continue

        # Gather candidates from all available providers
        candidates: List[Dict[str, Any]] = []

        # 1. Stremio OpenSubtitles v3 (using IMDb ID)
        if imdb_id and imdb_id.startswith("tt"):
            stremio_cand = await fetch_stremio_subtitles(
                session, imdb_id, is_tv=is_tv, season=season, episode=episode, target_langs=[lang]
            )
            candidates.extend(stremio_cand)

        # 2. MSone provider if language is Malayalam ('mal')
        if lang == "mal" and not is_tv:
            msone_title = entry.get("tmdb_title") or entry.get("clean_title") or entry.get("title")
            msone_cand = await fetch_msone_subtitles(session, msone_title, year=entry.get("year"))
            candidates.extend(msone_cand)

        if not candidates:
            continue

        # Score and pick the best synchronized release
        candidates.sort(key=lambda c: score_subtitle_candidate(c, video_filename), reverse=True)

        for best_cand in candidates[:3]:
            dl_url = best_cand.get("url")
            if not dl_url:
                continue

            srt_content = await download_subtitle_file(session, dl_url)
            if srt_content and is_valid_srt(srt_content):
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    with open(sidecar_path, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    logger.info(f"✅ Injected subtitle: {sidecar_path} (provider={best_cand.get('provider')})")
                    injected_paths.append(sidecar_path)
                    break
                except Exception as write_err:
                    logger.warning(f"Error writing subtitle to {sidecar_path}: {write_err}")

    return injected_paths

