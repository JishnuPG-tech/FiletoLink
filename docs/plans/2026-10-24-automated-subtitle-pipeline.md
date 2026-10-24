# Automated Subtitle Injection Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Provide an automated, accurate subtitle downloading and injection pipeline for all existing and future movies and TV series in Jellyfin, fetching matching subtitles (English, Malayalam, and user-specified languages) and placing verified `.srt` files alongside media.

**Architecture:** A modular subtitle service (`apex/apex_stream/subtitles.py`) querying high-availability providers (Stremio OpenSubtitles v3, MSone, optional OpenSubtitles.com / SubDL APIs), scoring candidates against media release signatures to prevent desync, validating SRT timestamps and UTF-8 encoding, writing sidecars (`<base>.<lang>.srt`), and updating Jellyfin via item refresh.

**Tech Stack:** Python 3, aiohttp, zipfile, BeautifulSoup4, Jellyfin REST API.

---

### Task 1: Subtitle Validator and File Normalizer

**Files:**
- Create: `apex/apex_stream/subtitles.py`
- Create: `apex/tests/test_subtitles.py`

**Step 1: Write the failing test**

```python
# apex/tests/test_subtitles.py
import pytest
from apex_stream.subtitles import is_valid_srt, clean_and_normalize_srt, extract_srt_from_payload

def test_is_valid_srt():
    valid = "1\n00:01:20,000 --> 00:01:23,000\nHello World\n\n2\n00:01:24,000 --> 00:01:26,000\nGoodbye\n"
    assert is_valid_srt(valid) is True

    invalid_html = "<html><body>404 Not Found</body></html>"
    assert is_valid_srt(invalid_html) is False

    empty = ""
    assert is_valid_srt(empty) is False

def test_clean_and_normalize_srt_cp1252():
    # CP1252 encoded curly quote
    raw = b"1\r\n00:00:01,000 --> 00:00:03,000\r\nIt\x92s working\r\n\r\n"
    cleaned = clean_and_normalize_srt(raw)
    assert "It’s working" in cleaned or "It's working" in cleaned
    assert "\r\n" not in cleaned
```

**Step 2: Run test to verify it fails**

Run: `pytest apex/tests/test_subtitles.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError

**Step 3: Write minimal implementation**

Implement `is_valid_srt`, `clean_and_normalize_srt`, and `extract_srt_from_payload` in `apex/apex_stream/subtitles.py`:
- Checks for standard timestamp regex: `\d{2}:\d{2}:\d{2}[,. ]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,. ]\d{3}`.
- Detects ZIP headers (`PK\x03\x04`) and extracts the first valid `.srt` from the archive.
- Detects encoding (utf-8, utf-8-sig, cp1252, iso-8859-1) and converts to clean LF UTF-8.

**Step 4: Run test to verify it passes**

Run: `pytest apex/tests/test_subtitles.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apex/apex_stream/subtitles.py apex/tests/test_subtitles.py
git commit -m "feat(subtitles): add srt validator and file normalizer"
```

---

### Task 2: Release Matching and Candidate Scoring

**Files:**
- Modify: `apex/apex_stream/subtitles.py`
- Modify: `apex/tests/test_subtitles.py`

**Step 1: Write the failing test**

```python
def test_score_subtitle_candidate():
    from apex_stream.subtitles import score_subtitle_candidate

    video_name = "Interstellar.2014.1080p.BluRay.x264-SPARKS.mkv"
    
    sub1 = {
        "subtitleFileName": "Interstellar.2014.1080p.BluRay.x264.srt",
        "movieReleaseName": "Interstellar.2014.1080p.BluRay.x264-SPARKS",
        "downloadCount": 10000,
    }
    sub2 = {
        "subtitleFileName": "Interstellar.2014.CAM.XviD.srt",
        "movieReleaseName": "Interstellar.2014.CAM",
        "downloadCount": 500,
    }

    score1 = score_subtitle_candidate(sub1, video_name)
    score2 = score_subtitle_candidate(sub2, video_name)
    assert score1 > score2
```

**Step 2: Run test to verify it fails**

Run: `pytest apex/tests/test_subtitles.py -k test_score_subtitle_candidate -v`
Expected: FAIL with "score_subtitle_candidate not found"

**Step 3: Write minimal implementation**

Implement `score_subtitle_candidate(candidate: dict, video_filename: str) -> float`:
- Extracts release tokens from video filename: `bluray`, `web-dl`, `webrip`, `hdtv`, `dvdrip`, `1080p`, `720p`, `2160p`, `4k`, `x264`, `x265`, `hevc`, `yts`, `psa`, `rarbg`, `galaxyrg`.
- Awards positive weight for token matches in `movieReleaseName`, `releaseGroup`, and `subtitleFileName`.
- Heavily penalizes mismatched quality categories (e.g. `cam` / `telesync` when video is `1080p` or `web-dl`).
- Includes download count / rating as tie-breaker.

**Step 4: Run test to verify it passes**

Run: `pytest apex/tests/test_subtitles.py -k test_score_subtitle_candidate -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apex/apex_stream/subtitles.py apex/tests/test_subtitles.py
git commit -m "feat(subtitles): add candidate scoring and release tag matching"
```

---

### Task 3: Multi-Provider Subtitle Engine (Stremio, MSone, OpenSubtitles)

**Files:**
- Modify: `apex/apex_stream/subtitles.py`
- Modify: `apex/tests/test_subtitles.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_fetch_stremio_subtitles(monkeypatch):
    from apex_stream.subtitles import fetch_stremio_subtitles
    # Mock network call to return sample Stremio JSON
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest apex/tests/test_subtitles.py -k test_fetch_stremio_subtitles -v`
Expected: FAIL with function missing

**Step 3: Write minimal implementation**

Implement provider fetchers in `apex/apex_stream/subtitles.py`:
1. `fetch_stremio_subtitles(imdb_id: str, is_tv: bool = False, season: int = 1, episode: int = 1, target_langs: list = None)`
   - Queries `https://opensubtitles-v3.strem.io/subtitles/movie/{imdb_id}.json` or `/series/{imdb_id}:{s}:{e}.json`.
   - Filters by target languages (`eng`, `mal`, etc.).
2. `fetch_msone_subtitles(movie_title: str, year: int = None)`
   - Queries `https://malayalamsubtitles.org/?s={title}`.
   - Finds matching post, extracts direct `.zip` or `.srt` download link for Malayalam subtitles.
3. Fallback `fetch_opensubtitles_com` and `fetch_subdl` if API keys are configured via environment variables.

**Step 4: Run test to verify it passes**

Run: `pytest apex/tests/test_subtitles.py -k test_fetch_stremio_subtitles -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apex/apex_stream/subtitles.py apex/tests/test_subtitles.py
git commit -m "feat(subtitles): add stremio and msone subtitle providers"
```

---

### Task 4: Subtitle Downloader & Sidecar Injector

**Files:**
- Modify: `apex/apex_stream/subtitles.py`
- Modify: `apex/tests/test_subtitles.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_download_and_inject_subtitles(tmp_path):
    from apex_stream.subtitles import inject_subtitles_for_entry
    # Mock video entry pointing to tmp_path / "Movies" / "Ne Zha 2 (2025)" / "Ne Zha 2 (2025).strm"
    # Ensure subtitle file is written with valid name "{base}.{lang}.srt"
```

**Step 2: Run test to verify it fails**

Run: `pytest apex/tests/test_subtitles.py -k test_download_and_inject_subtitles -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement `inject_subtitles_for_entry(entry: dict, target_langs=("eng", "mal"), force: bool = False)`:
- Identifies target directory from `entry["target_dir"]` or `strm_dir(...)`.
- For each target language:
  - Checks if subtitle file `{base}.{lang}.srt` already exists (skips if exists unless `force=True`).
  - Fetches candidates from providers using `entry.get("imdb_id")` or TMDB details.
  - Scores candidates and downloads the top match.
  - Validates and normalizes content with `clean_and_normalize_srt`.
  - Atomically writes `{base}.{lang}.srt` to the media directory.
  - Returns count and paths of injected subtitles.

**Step 4: Run test to verify it passes**

Run: `pytest apex/tests/test_subtitles.py -k test_download_and_inject_subtitles -v`
Expected: PASS

**Step 5: Commit**

```bash
git add apex/apex_stream/subtitles.py apex/tests/test_subtitles.py
git commit -m "feat(subtitles): implement inject_subtitles_for_entry"
```

---

### Task 5: Pipeline Integration & Full Jellyfin Backfill

**Files:**
- Modify: `apex/tg_streamer.py`
- Modify: `apex/proxy.py`
- Modify: `apex/tests/test_tg_streamer_routes.py`

**Step 1: Write the failing test**

```python
def test_subtitles_status_endpoint():
    # Test GET /api/subtitles/status returns subtitle metrics
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest apex/tests/test_tg_streamer_routes.py -k test_subtitles_status -v`
Expected: FAIL (endpoint not found)

**Step 3: Write minimal implementation**

1. In `apex/tg_streamer.py`:
   - In `_tmdb_fetch_meta(...)`: after TMDB metadata and posters/NFO are saved, trigger `asyncio.create_task(inject_subtitles_for_entry(entry))` so every future ingested movie/series gets subtitles automatically.
   - Add `async def backfill_all_subtitles()`:
     - Iterates through `FILE_ID_CACHE`.
     - Identifies movies and TV episodes missing subtitles.
     - Automatically searches, downloads, and places subtitles.
     - Calls `refresh_jellyfin_item_by_path(...)` to immediately register the new subtitle tracks in Jellyfin.
   - Launch `backfill_all_subtitles()` in the background on startup (after cache restore).
2. In `apex/proxy.py`:
   - Expose `GET /api/subtitles/status` and `POST /api/subtitles/sync` so users can check subtitle coverage or trigger manual synchronization.

**Step 4: Run test to verify it passes**

Run: `pytest apex/tests/ -v`
Expected: All 220+ tests PASS

**Step 5: Commit**

```bash
git add apex/tg_streamer.py apex/proxy.py apex/tests/
git commit -m "feat(subtitles): integrate automated subtitle injection into media ingest and backfill"
```

---

### Verification and Sanity Testing

1. Run full test suite: `$env:PYTHONPATH="apex;apex/apex_stream"; pytest apex/tests`
2. Test live query on sample movie IDs (e.g. Ne Zha 2, Interstellar, Breaking Bad).
3. Confirm sidecar file placement and Jellyfin API item refresh behavior.
