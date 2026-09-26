"""TMDB-driven metadata & library organization.

Pure, Telegram-free helpers (unit-testable without a network):

- `parse_media_meta`  -> robust movie/TV filename & caption parsing (year, season,
                         episode, title/query cleaning across many release schemes)
- `best_tmdb_match`   -> pick the best TMDB search hit for a query + year + type
- NFO builders        -> Kodi/Jellyfin-compatible `movie.nfo`, `tvshow.nfo`,
                         `episodedetails.nfo` XML built from TMDB JSON

The async aiohttp calls live in tg_streamer.py; everything here is pure.
"""

import os
import re
from typing import Dict, List, Optional

from xml.sax.saxutils import escape as xml_escape

from .organize import (
    _ALL_LANG_TOKENS,
    _STOP_TOKENS,
    DEFAULT_LANGUAGE,
    detect_language,
    safe_folder,
)

TPL_BASE = "https://image.tmdb.org/t/p"

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

# TV patterns, in priority order. All return (show_name, season, episode) or None.
_SX_E = re.compile(r"(?i)\bS(\d{1,2})\s*(?:\.|\s|_|-)+\s*E(\d{1,3})\b")
_SX_EX = re.compile(r"(?i)\bS(\d{1,2})\s*E(\d{1,3})\b")
_SEASON_EP = re.compile(
    r"(?i)\bSeason\s*(\d{1,2})\s*(?:Episode\s*|Ep\s*)?(\d{1,3})\b"
)
_1X = re.compile(r"(?<!\d)(\d{1,2})x(\d{1,3})(?!\d)")
_EP_ONLY = re.compile(r"(?i)\b(?:E|Ep)\.?\s*(\d{1,3})\b")
_EPISODE_WORD = re.compile(r"(?i)\bEpisode\s*(\d{1,3})\b")

# Extra release/hardware tokens that pollute titles and queries.
_EXTRA_STOP = {
    "hdr", "dolby", "vision", "hd", "fhd", "uhd", "amzn", "nf", "netflix",
    "web-dl", "webdl", "webrip", "bdrip", "hdrip", "brrip", "hdtv", "remux",
    "10bit", "8bit", "50fps", "60fps", "multisub", "truehd", "ddplus", "ddp",
    "ddp5", "dtsx", "dtshd", "avc", "h264", "h265", "x264", "x265", "hevc",
    "itunes", "max", "disney", "disneyplus", "hulu", "paramount",
    "cmc", "hbo", "hbomax", "amazon", "googleplay", "sd", "hq",
    "ts", "cam", "hdcam", "blu-ray", "bluray", "hdrip", "dvdrip", "dvd",
    "webm", "mkv", "mp4",
    # OTT platform brandings that commonly prefix release audio/codec tags.
    "jiohotstar", "hotstar", "jiocinema", "sonyliv", "zee5", "mxplayer",
    "voot", "airtel", "sunnxt", "manoramamax", "primevideo", "nuefliks",
    "tvf",
}

_ALL_STOP = _STOP_TOKENS | _EXTRA_STOP | _ALL_LANG_TOKENS

# Dotted release/quality anchors: when a trailing dotted segment follows one of
# these, it is almost always an uploader group tag (".x264.Pah", ".WEB-DL.XYZ")
# and safe to drop — genuine dotted titles like "K.G.F.Chapter.2" contain none.
_QUALITY_ANCHORS = {
    "720p", "1080p", "2160p", "1440p", "480p", "360p",
    "x264", "x265", "h264", "h265", "hevc", "avc", "aac", "ac3",
    "web-dl", "webdl", "webrip", "hdrip", "bdrip", "brrip", "hdtv",
    "remux", "bluray", "blu-ray", "10bit", "8bit", "truehd", "dts",
    "ddp5", "tvrip", "dvdrip", "dvd", "web", "amzn", "nf", "netflix",
    "mkv", "mp4", "avi", "mov", "ts", "m2ts",
}


def _drop_dotted_group_tail(text: Optional[str]) -> str:
    """Drop a trailing dotted release-group (".x264.Pah" -> ".x264").

    Preserves genuine dotted title segments ("K.G.F.Chapter.2.2022") because
    those contain no release/quality anchor; only content AFTER the last
    recognized anchor segment is treated as group residue. Keeps tails that
    carry a year or a language/release token (real subtitle-less variants).
    """
    if not text:
        return text or ""
    stripped = text.strip()
    # Strip a real media extension so ".mkv" is never mistaken for a group,
    # but keep ".Pah"-style tails (not real extensions) so they can be detected.
    ext_re = re.split(r"(?i)\.(?:mkv|mp4|avi|mov|m4v|webm|ts|m2ts|mpg|mpeg|wmv|flv|iso)\s*$", stripped)
    base = ext_re[0]
    if "." not in base:
        return text
    parts = base.split(".")
    last_anchor = None
    for i, part in enumerate(parts):
        if part.strip().lower() in _QUALITY_ANCHORS:
            last_anchor = i
    if last_anchor is None:
        return text
    tail = parts[last_anchor + 1:]
    if not tail:
        return text
    tail_text = " ".join(p.strip() for p in tail)
    if re.search(r"\b(?:19|20)\d{2}\b", tail_text):
        return text
    # Keep a language token so detect_language still sees it after the drop
    # (e.g. ".1080p.Kannada"); pure codec/group residue is always dropped.
    if _ALL_LANG_TOKENS & set(re.findall(r"[a-z0-9]+", tail_text.lower())):
        return text
    return ".".join(parts[: last_anchor + 1])


def _sig_tokens(text: str) -> set:
    toks = {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _ALL_STOP}
    # A lone 4-digit token is a numeric title (e.g. the film "2018"), not a year.
    if len(toks) == 1 and next(iter(toks)).isdigit() and len(next(iter(toks))) == 4:
        return toks
    return {t for t in toks if not (t.isdigit() and len(t) == 4)}


def _clean_check(text: str) -> str:
    """Lowercased token check description used for year/tag stripping."""
    return text


_MEDIA_EXT_RE = re.compile(
    r"(?i)\.(?:mkv|mp4|avi|mov|m4v|webm|ts|m2ts|mpg|mpeg|wmv|flv|iso|rar|zip|7z)\s*$"
)


def _strip_noise(text: str) -> str:
    """Strip group tags ([...], @Handle), the real media extension and collapse
    whitespace.

    The media extension must be removed BEFORE dots are turned into spaces, or
    ".mkv" becomes a trailing "mkv" token that breaks the audio/language tail
    detection for every release that ends in one. Dots are release separators
    in filenames ("Movie.2021.720p.Pah") so they are turned into spaces here;
    keeping them produces dotted folder names and breaks both Jellyfin
    matching and TMDB search queries.
    """
    t = re.sub(r"\[[^\]]*\]", " ", text)
    t = re.sub(r"@[\w.\-]+", " ", t)
    t = _MEDIA_EXT_RE.sub(" ", t)
    # "+" and "&" are release/present separators too ("Dd+5.1 H" -> "Dd 5 1 H",
    # "Birds of Prey & Fantabulous" -> "Birds of Prey  Fantabulous"). A dash is a
    # word separator ("DTS-MA", "Dead-Reckoning") so it is left as-is; Dots are
    # release separators in filenames ("Movie.2021.720p.Pah") so they are also
    # turned into spaces here; keeping them produces dotted folder names and
    # breaks both Jellyfin matching and TMDB search queries.
    t = re.sub(r"[.+&_]", " ", t)
    t = re.sub(r"\.", " ", t)
    t = re.sub(r"[\s_]+", " ", t)
    return t.strip()


# Words that legitimately follow a dash in series titles ("Dead Reckoning",
# "Chapter 2") must never be dropped as if they were release groups.
_KEEP_DASH_PARTS = {"chapter", "part", "volume", "special", "collection"}


def _drop_group_tags(text: str) -> str:
    """Drop trailing uploader/release-group segments like ' -Pah' / ' -Tinymkv Xyz'.

    Only removes a whitespace-dash-whitespace run when the surviving title still
    has at least 3 significant tokens, so real hyphenated series parts like
    "Mission Impossible - Dead Reckoning" are preserved.
    """
    m = re.search(r"\s+-\s*([A-Za-z][A-Za-z0-9]*)(?:\s+\w+)*\s*$", text)
    if not m:
        return text
    if m.group(1).lower() in _KEEP_DASH_PARTS:
        return text
    head = text[: m.start()].strip(" -.,")
    if len(re.findall(r"[a-z0-9]+", head.lower())) < 3:
        return text
    return head


def _remove_tokens(text: str, tokens: set) -> str:
    for tok in sorted(tokens, key=len, reverse=True):
        if len(tok) < 2:
            continue
        text = re.sub(
            r"(?<![a-z0-9])" + re.escape(tok) + r"(?![a-z0-9])", " ", text,
            flags=re.IGNORECASE,
        )
    return re.sub(r"\s+", " ", text).strip(" -.,")


# Junk words that are safe to consume in a trailing release run: OTT brands,
# language tokens, quality/codec/res tokens and generic "release word"
# suffixes. These are all also in `_ALL_STOP`, so `_remove_tokens` clears any
# that survive; the tail-stripper only exists to carry the adjacent channel
# DIGITS whose stop-words were already resolved.
_TAIL_RUN_WORDS = _ALL_LANG_TOKENS | _EXTRA_STOP | _STOP_TOKENS | {
    "blu", "ray", "dvdr", "web", "hdtv", "hdtvrip", "xvid", "divx", "wmv",
    "flac", "mp3", "dual", "subs", "proper", "repack", "extended", "uncut",
    "unrated",
}

# Short ISO 639-1 dub/language codes that appear as release tail tokens.
_ISO_LANG_CODES = {
    "en", "hi", "ml", "ta", "te", "kn", "bn", "pa", "mr", "gu", "ur", "ko",
    "ja", "zh", "es", "fr", "de", "ru", "ar", "pt", "id", "it",
}

# Audio channel markers ("6CH", "5.1", "2Ch", "DD5.1CH" -> "5 1 ch"). After
# `_strip_noise` these become "6ch", "5 1 ch"; a bare "NCH" token is never part
# of a real film title and must be removed from search queries ("Obsession
# 2025 1080p 6CH x265" -> "Obsession").
_CHANNEL_TOKEN_RE = re.compile(r"(?i)^\d{1,2}(?:\.\d)?ch$")

# TRUE audio/codec channel anchors. A trailing run is only dropped when it
# contains one of these, so quality tokens ("1080p", "x264") or a lone digit
# never eat a real number in a title ("K.G.F. Chapter 2", "Room 237").
_AUDIO_WORDS = {
    "dd", "dd5", "ddp", "ddp5", "ddplus", "dolby", "dts", "dtsx", "dtshd",
    "dtse", "dtsecore", "atmos", "truehd", "aac", "ac3", "ehq", "eac3",
}


def _strip_audio_lang_tail(text: str) -> str:
    """Drop a trailing audio/codec/language/platform run from a search query.

    Release names in any Telegram format carry release junk after the real
    title: "I Nobody Jiohotstar Dd+5.1 H (2026)", "Premam Dd5.1 1080p
    Malayalam", "Vikram.2022.1080p.DDP5.1.Tamil", "Interstellar (2014) 1080p
    DTS-MA Hindi". After `_strip_noise` those become space-separated tokens
    ("dd 5 1 h", "ddp5 1 tamil", "dts ma hin"). A trailing run of junk tokens
    (codec/dub digits included) is dropped only when it CONTAINS a true audio
    anchor word ("dd", "ddp5", "dts", "dts-ma", "atmos", ...), so real numbers
    in titles end up preserved:
      - "K.G.F.Chapter.2.1080p"      -> run "2 1080p", no audio anchor -> keep
      - "Manjummel.Boys.DDP5.1.Hindi" -> run "ddp5 1 hindi", anchor present -> drop
      - "I Nobody Jiohotstar Dd 5 1 H"-> run "dd 5 1 h", anchor present   -> drop
    """
    if not text:
        return text
    parts = text.split()
    i = len(parts) - 1
    run = []  # (token, is_audio_anchor)
    while i >= 0:
        tok = parts[i].lower().lstrip("-_.")
        npfx, dash, mark = tok.partition("-ma")
        is_channel = bool(_CHANNEL_TOKEN_RE.match(tok))
        is_anchor = (
            tok in _AUDIO_WORDS
            or (dash and npfx in _AUDIO_WORDS)
            or is_channel
        )
        is_ma = tok == "ma"
        is_digit = bool(re.fullmatch(r"\d[\d.]*", tok.strip(".-_")))
        is_short = (len(tok) == 1 and tok.isalpha()) or tok in _ISO_LANG_CODES
        is_word_junk = tok in _TAIL_RUN_WORDS or is_ma or is_short or is_channel
        if not (is_anchor or is_digit or is_word_junk):
            break
        run.append((tok, is_anchor))
        i -= 1

    if not run:
        return text
    # A trailing run is only dropped when it contains a true audio anchor.
    has_anchor = any(is_anchor for _, is_anchor in run)
    if not has_anchor:
        return text
    # Bare "ma" with an audio anchor on its left ("dts ma") counts into the run.
    head = parts[: i + 1]
    if len(re.findall(r"[a-z0-9]+", " ".join(head).lower())) < 1:
        return text
    return " ".join(head).strip()


def _detect_year(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = YEAR_RE.search(text)
    return int(m.group(0)) if m else None


def _clean_search_title(text: str) -> str:
    """A title ready to send to the TMDB search API (no year/release tags)."""
    text = _strip_noise(_drop_dotted_group_tail(text))
    text = YEAR_RE.sub(" ", text)
    text = re.sub(r"\(\s*\)", " ", text)
    # Remove audio/dub tails BEFORE generic token removal so codec words are
    # still present to anchor the trailing pattern.
    text = _strip_audio_lang_tail(text)
    text = _remove_tokens(text, _ALL_STOP)
    text = " ".join(t for t in text.split() if not _CHANNEL_TOKEN_RE.match(t))
    text = _drop_group_tags(text)
    return " ".join(text.lower().split())


def _significant_token_stream(text: str):
    """Yield non-stop, non-digit words that are likely part of the real title."""
    seen = set()
    stop_tokens = _ALL_STOP
    for tok in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if tok in stop_tokens or (tok.isdigit() and len(tok) != 4):
            continue
        if _CHANNEL_TOKEN_RE.match(tok):
            continue
        # Drop ambiguous fragments ripped off a release token ("1080p"->"p",
        # "DTS-MA"->"ma", "WEB-DL"->"dl") that add no matching value and only
        # widen the wrong-hit window on the TMDB search.
        if any(
            w != tok and (w.startswith(tok) or w.endswith(tok))
            for w in stop_tokens
        ):
            continue
        if tok not in seen:
            seen.add(tok)
            yield tok


def _search_candidates(raw: Optional[str]) -> List[str]:
    """Ordered candidate search queries for a raw Telegram file name.

    The fully-cleaned title is the most precise, but unforeseen release
    formats can leave OTT/codec junk in the middle of the string that a
    prefix-cleaning pass cannot see. We therefore also emit progressively
    simpler token queries that TMDB handles gracefully:
      - full significant-token stream (drops every stop/quality/dub token),
      - then leading-prefix sub-queries of that stream.
    Every candidate is still filtered through `best_tmdb_match`, so an
    over-broad query can never return a wrong hit.
    """
    if not raw:
        return []
    cands: List[str] = []
    cleaned = _clean_search_title(raw)
    if cleaned:
        cands.append(cleaned)
    toks = list(_significant_token_stream(raw))
    full_toks = " ".join(toks[:12])
    if full_toks and full_toks != cleaned:
        cands.append(full_toks)
    for n in (1, 2, 3, 4):
        prefix = " ".join(toks[:n])
        if prefix and prefix not in cands:
            cands.append(prefix)
    return cands


def _numeric_title_fallback(raw: str) -> str:
    """Recover a numeric-only title eaten by the year remover.

    MYSTERY_2018.2018.Malayalam.1080p -> "2018" (the film "2018"), while a real
    year ("2008", "2015") in the tag tail still reads as `year`. Rebuilds the
    first dotted numeric run when the stop-token pipeline emptied the title.
    """
    if not raw:
        return ""
    for token in re.split(r"[._\-\s]+", raw.strip()):
        if re.fullmatch(r"(?:19|20)\d{2}", token):
            return token
    return ""


def _extract_tv(filename: str):
    """Return (show_name, season, episode) if the name looks like a TV episode."""
    text = filename or ""
    for pattern in (_SEASON_EP, _SX_EX, _SX_E, _1X):
        m = pattern.search(text)
        if m:
            season = int(m.group(1))
            try:
                episode = int(m.group(2))
            except (IndexError, ValueError):
                episode = season  # Season-only pattern leaves episode unset
            before = text[: m.start()]
            return before, season, episode
    # Word/episode-only fallbacks require a show name prefix.
    for pattern in (_EPISODE_WORD, _EP_ONLY):
        m = pattern.search(text)
        if m:
            before = text[: m.start()].strip(" -.,_")
            if before and len(before.split()) >= 1:
                season = 1
                episode = int(m.group(1))
                return before, season, episode
    return None


def parse_media_meta(filename_or_caption: Optional[str]) -> Dict:
    """Robustly parse a Telegram file name / caption into media metadata.

    Returns a dict with:
      is_tv, title, show_name, season, episode, year,
      clean_title (folder-safe movie/show title w/ year removed),
      search_title (TMDB query), language
    """
    raw = _strip_noise(_drop_dotted_group_tail(filename_or_caption or ""))
    if not raw:
        return {
            "is_tv": False, "title": "Unknown_Media", "show_name": None,
            "season": None, "episode": None, "year": None,
            "clean_title": "Unknown_Media", "search_title": "", "language": DEFAULT_LANGUAGE,
        }

    year = _detect_year(raw)
    language = detect_language(raw)

    tv = _extract_tv(raw)
    if tv:
        show_raw, season, episode = tv
        clean_show = _clean_search_title(show_raw)
        if not clean_show:
            clean_show = "Unknown_Show"
        show_title = safe_folder(_clean_search_title(show_raw).title() or clean_show)
        title = f"{show_title} - S{int(season):02d}E{int(episode):02d}"
        return {
            "is_tv": True,
            "title": title,
            "show_name": show_title,
            "season": int(season),
            "episode": int(episode),
            "year": year,
            "clean_title": show_title,
            "search_title": clean_show,
            "search_candidates": _search_candidates(show_raw),
            "language": language,
        }

    movie_title = _clean_search_title(raw)
    if not movie_title:
        # Numeric-only/recovered titles: "2018.2018.Malayalam.1080p" is the
        # Malayalam film "2018", not a bare year; TMDB knows it by that name.
        movie_title = _numeric_title_fallback(filename_or_caption or raw)
    if not movie_title:
        movie_title = "Unknown_Media"
    display = safe_folder(movie_title.title() or movie_title)
    return {
        "is_tv": False,
        "title": display,
        "show_name": None,
        "season": None,
        "episode": None,
        "year": year,
        "clean_title": display,
        "search_title": movie_title,
        "search_candidates": _search_candidates(raw),
        "language": language,
    }


def best_tmdb_match(results: List[Dict], query: str, media_type: str,
                    year: Optional[int] = None, threshold: float = 0.5):
    """Return the best TMDB search result for (query, year, type), or None.

    Scoring: token containment of the query against the hit title, with a boost
    when the hit's release/first-air year equals the parsed file year. Results
    of the wrong media_type are excluded so movies never steal a series match.
    """
    q_toks = _sig_tokens(query)
    if not q_toks:
        return None
    best, best_score = None, -1.0
    for r in results or []:
        mt = r.get("media_type")
        if mt and mt != media_type:
            continue
        name = r.get("title") or r.get("name") or ""
        r_toks = _sig_tokens(name)
        if not r_toks:
            continue
        overlap = len(q_toks & r_toks)
        if not overlap:
            continue
        score = overlap / max(1, min(len(q_toks), len(r_toks)))
        date = (r.get("release_date") or r.get("first_air_date") or "")[:4]
        if year and date and int(date) == year:
            score += 0.3
        if q_toks <= r_toks:
            score += 0.3
        if score > best_score:
            best, best_score = r, score
    return best if best_score >= threshold else None


def tmdb_image_url(path: Optional[str], size: str = "w500") -> Optional[str]:
    if not path:
        return None
    return f"{TPL_BASE}/{size}{path}"


def build_movie_nfo(data: Dict) -> str:
    g = lambda k: str(data.get(k) or "")
    genres = [_gen(x) for x in (data.get("genres") or []) if _gen(x)]
    country = ""
    for c in data.get("production_countries") or []:
        if c.get("iso_3166_1"):
            country = c["iso_3166_1"]
            break
    genre_lines = "".join("  <genre>%s</genre>\n" % xml_escape(x) for x in genres)
    country_line = "  <country>%s</country>\n" % xml_escape(country) if country else ""
    return """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <title>%(title)s</title>
  <originaltitle>%(original_title)s</originaltitle>
  <year>%(year)s</year>
  <premiered>%(premiered)s</premiered>
  <releasedate>%(releasedate)s</releasedate>
  <rating>%(rating)s</rating>
  <votes>%(votes)s</votes>
  <runtime>%(runtime)s</runtime>
  <plot>%(plot)s</plot>
  <tagline>%(tagline)s</tagline>
  <imdbid>%(imdbid)s</imdbid>
  <tmdbid>%(tmdbid)s</tmdbid>
  <uniqueid type="tmdb">%(tmdbid)s</uniqueid>
  %(genres)s%(country)s  <art>
    <poster>poster.jpg</poster>
    <backdrop>backdrop.jpg</backdrop>
  </art>
</movie>
""" % {
        "title": xml_escape(g("title")),
        "original_title": xml_escape(g("original_title")),
        "year": xml_escape(g("release_date"))[:4],
        "premiered": xml_escape(g("release_date")),
        "releasedate": xml_escape(g("release_date")),
        "rating": xml_escape(g("vote_average")),
        "votes": xml_escape(g("vote_count")),
        "runtime": xml_escape(g("runtime")),
        "plot": xml_escape(g("overview")),
        "tagline": xml_escape(g("tagline")),
        "imdbid": xml_escape(str(data.get("imdb_id") or "")),
        "tmdbid": xml_escape(str(data.get("id") or "")),
        "genres": genre_lines,
        "country": country_line,
    }


def build_tvshow_nfo(data: Dict) -> str:
    g = lambda k: str(data.get(k) or "")
    genres = [_gen(x) for x in (data.get("genres") or []) if _gen(x)]
    genre_lines = "".join("  <genre>%s</genre>\n" % xml_escape(x) for x in genres)
    return """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<tvshow>
  <title>%(title)s</title>
  <originaltitle>%(original_title)s</originaltitle>
  <year>%(year)s</year>
  <premiered>%(premiered)s</premiered>
  <rating>%(rating)s</rating>
  <votes>%(votes)s</votes>
  <runtime>%(runtime)s</runtime>
  <plot>%(plot)s</plot>
  <tmdbid>%(tmdbid)s</tmdbid>
  <uniqueid type="tmdb">%(tmdbid)s</uniqueid>
  %(genres)s  <art>
    <poster>poster.jpg</poster>
    <backdrop>backdrop.jpg</backdrop>
  </art>
</tvshow>
""" % {
        "title": xml_escape(g("name")),
        "original_title": xml_escape(g("original_name")),
        "year": xml_escape(g("first_air_date"))[:4],
        "premiered": xml_escape(g("first_air_date")),
        "rating": xml_escape(g("vote_average")),
        "votes": xml_escape(g("vote_count")),
        "runtime": xml_escape(_tv_runtime(data)),
        "plot": xml_escape(g("overview")),
        "tmdbid": xml_escape(str(data.get("id") or "")),
        "genres": genre_lines,
    }


def build_episode_nfo(data: Dict) -> str:
    g = lambda k: str(data.get(k) or "")
    return """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<episodedetails>
  <season>%(season)s</season>
  <episode>%(episode)s</episode>
  <title>%(title)s</title>
  <plot>%(plot)s</plot>
  <aired>%(aired)s</aired>
  <rating>%(rating)s</rating>
  <runtime>%(runtime)s</runtime>
  <uniqueid type="tmdb">%(tmdbid)s</uniqueid>
</episodedetails>
""" % {
        "season": xml_escape(g("season_number")),
        "episode": xml_escape(g("episode_number")),
        "title": xml_escape(g("name")),
        "plot": xml_escape(g("overview")),
        "aired": xml_escape(g("air_date")),
        "rating": xml_escape(g("vote_average")),
        "runtime": xml_escape(g("runtime")),
        "tmdbid": xml_escape(str(data.get("id") or "")),
    }


def _gen(obj) -> str:
    return str(obj.get("name") or "") if isinstance(obj, dict) else ""


def _tv_runtime(data: Dict) -> str:
    rt = data.get("episode_run_time") or []
    return str(rt[0]) if rt else ""