"""Universal Media Extraction Engine.

Combines industry-standard GuessIt with structural anchor-based parsing
and AI LLM fallback to reliably extract (title, year, is_tv, season, episode)
from messy Telegram filenames and scene release conventions.
"""

import os
import re
from typing import Any, Dict, Optional

try:
    from guessit import guessit as _guessit_fn
    HAS_GUESSIT = True
except ImportError:
    _guessit_fn = None
    HAS_GUESSIT = False

# Boundary patterns for TV episodes
_TV_PATTERNS = [
    re.compile(r"(?i)(?:^|[\s_\.\-\[])[sS](\d{1,2})[.\-_ ]*[eE](\d{1,2})(?:[\s_\.\-\]]|$)"),
    re.compile(r"(?i)(?:^|[\s_\.\-\[])(\d{1,2})x(\d{1,2})(?:[\s_\.\-\]]|$)"),
    re.compile(r"(?i)(?:^|[\s_\.\-\[])season[.\-_ ]*(\d{1,2})[.\-_ ]*ep(?:isode)?[.\-_ ]*(\d{1,2})(?:[\s_\.\-\]]|$)"),
    re.compile(r"(?i)(?:^|[\s_\.\-\[])ep(?:isode)?[.\-_ ]*(\d{1,2})(?:[\s_\.\-\]]|$)"),
]

# Year anchor pattern (1900 - 2099)
_YEAR_RE = re.compile(r"(?:^|[\s_\.\-\[\(])(19\d{2}|20\d{2})(?:[\s_\.\-\]\)]|$)")

# Technical release and encoding boundaries
_QUALITY_BOUNDARY_RE = re.compile(
    r"(?i)[\s_\.\-\[](?:2160p|1080p|720p|480p|360p|4k|uhd|bluray|blu-ray|bdrip|brrip|"
    r"web-?dl|webrip|hdtv|dvdrip|x264|x265|hevc|av1|xvid|divx|ddp?5\.1|dts(?:-hd)?|aac|"
    r"mp3|flac|truehd|atmos|10bit|8bit|hindi|tamil|telugu|malayalam|kannada|english|"
    r"chinese|japanese|korean|dual[.\-_ ]?audio|multi|esub|sub)(?:[\s_\.\-\]]|$)"
)

# Outer envelope spam (channels, domains, watermarks)
_ENVELOPE_RE = re.compile(
    r"(?i)(?:^|[\s_\.\-\[])(?:@[a-z0-9_]+|www\.[a-z0-9\-]+(?:\.[a-z0-9\-]+)+|"
    r"[a-z0-9\-]+\.(?:com|org|net|vip|xyz|top|site|club|online|store|link))(?=[\]\s_\.\-]|$)"
)


def _anchor_parse(filename: str) -> Dict[str, Any]:
    """Deterministic structural anchor parsing for filenames."""
    if not filename:
        return {"title": "Unknown_Media", "is_tv": False, "year": None, "season": None, "episode": None}

    # 1. Clean outer extensions and channel handles
    clean = re.sub(r"(?i)\.(?:mkv|mp4|avi|mov|webm|strm|ts|m2ts)\s*$", "", filename.strip())
    clean = _ENVELOPE_RE.sub(" ", clean)
    clean = re.sub(r"^\[[^\]]+\]", "", clean).strip(" -._")

    # 2. Check for TV episode anchors
    is_tv = False
    season = None
    episode = None
    title_raw = clean

    for pat in _TV_PATTERNS:
        m = pat.search(clean)
        if m:
            is_tv = True
            groups = [g for g in m.groups() if g is not None]
            if len(groups) >= 2:
                season = int(groups[0])
                episode = int(groups[1])
            elif len(groups) == 1:
                season = 1
                episode = int(groups[0])
            # The show title is strictly BEFORE the episode anchor
            title_raw = clean[: m.start()]
            break

    # 3. Detect release year anchor
    year = None
    ym = _YEAR_RE.search(clean)
    if ym:
        year = int(ym.group(1))
        if not is_tv:
            title_cand = clean[: ym.start()].strip(" -._")
            if len(title_cand) >= 2:
                title_raw = title_cand
        else:
            # Strip year from show name if present (e.g. "Wednesday 2024" -> "Wednesday")
            title_raw = re.sub(rf"(?:^|[\s_\.\-\[\(]){year}(?:[\s_\.\-\]\)]|$)", " ", title_raw)

    # 4. Truncate at quality boundary
    qm = _QUALITY_BOUNDARY_RE.search(title_raw)
    if qm:
        title_raw = title_raw[: qm.start()]

    # 5. Clean punctuation to spaces
    title_clean = re.sub(r"[._\+]+", " ", title_raw)
    title_clean = re.sub(r"\s+", " ", title_clean).strip(" -._:,()[]{}")
    title_clean = re.sub(r"\s*\(\d{4}\)$", "", title_clean).strip()

    if not title_clean:
        title_clean = "Unknown_Media"

    return {
        "title": title_clean,
        "is_tv": is_tv,
        "season": season,
        "episode": episode,
        "year": year,
    }


def extract_media_info(filename: str) -> Dict[str, Any]:
    """Primary extraction entrypoint combining GuessIt and Anchor-based parsing."""
    if not filename:
        return {"title": "Unknown_Media", "is_tv": False, "year": None, "season": None, "episode": None}

    # Step 1: Attempt GuessIt if available
    if HAS_GUESSIT and _guessit_fn:
        try:
            g = _guessit_fn(filename)
            g_title = g.get("title")
            if g_title and len(str(g_title).strip()) >= 2:
                is_tv = g.get("type") == "episode" or "episode" in g or "season" in g
                season = int(g["season"]) if "season" in g else (1 if is_tv else None)
                episode = int(g["episode"]) if "episode" in g else (1 if is_tv else None)
                year = int(g["year"]) if "year" in g else None
                return {
                    "title": str(g_title).strip(),
                    "is_tv": is_tv,
                    "season": season,
                    "episode": episode,
                    "year": year,
                    "engine": "guessit",
                }
        except Exception:
            pass

    # Step 2: Fall back to deterministic anchor parser
    res = _anchor_parse(filename)
    res["engine"] = "anchor"
    return res
