import pytest
import io
import zipfile
from apex_stream.subtitles import (
    is_valid_srt,
    is_valid_subtitle_file,
    purge_corrupted_subtitles,
    clean_and_normalize_srt,
    extract_srt_from_payload,
    score_subtitle_candidate,
    fetch_stremio_subtitles,
    fetch_subdl_subtitles,
    fetch_opensubtitles_com,
    download_subtitle_file,
    inject_subtitles_for_entry,
    adjust_srt_timing,
    normalize_to_iso639_2,
)


def test_is_valid_srt():
    valid = "1\n00:01:20,000 --> 00:01:23,000\nHello World\n\n2\n00:01:24,000 --> 00:01:26,000\nGoodbye\n"
    assert is_valid_srt(valid) is True

    valid_vtt = "WEBVTT\n\n00:01:20.000 --> 00:01:23.000\nHello World\n"
    assert is_valid_srt(valid_vtt) is True

    invalid_html = "<html><body>404 Not Found</body></html>"
    assert is_valid_srt(invalid_html) is False

    empty = ""
    assert is_valid_srt(empty) is False


def test_clean_and_normalize_srt_cp1252():
    # CP1252 encoded curly quote (\x92) and windows CRLF
    raw = b"1\r\n00:00:01,000 --> 00:00:03,000\r\nIt\x92s working\r\n\r\n"
    cleaned = clean_and_normalize_srt(raw)
    assert "It’s working" in cleaned or "It's working" in cleaned
    assert "\r\n" not in cleaned
    assert is_valid_srt(cleaned) is True


def test_extract_srt_from_payload_plain():
    raw = b"1\n00:00:01,000 --> 00:00:03,000\nDirect subtitle text\n"
    srt_text = extract_srt_from_payload(raw)
    assert srt_text is not None
    assert "Direct subtitle text" in srt_text


def test_extract_srt_from_payload_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("readme.txt", "This is a readme file.")
        z.writestr("movie.srt", "1\n00:00:01,000 --> 00:00:03,000\nZip subtitle text\n")
    zip_bytes = buf.getvalue()

    srt_text = extract_srt_from_payload(zip_bytes)
    assert srt_text is not None
    assert "Zip subtitle text" in srt_text


def test_score_subtitle_candidate():
    video_name = "Interstellar.2014.1080p.BluRay.x264-SPARKS.mkv"

    # High match: 1080p, BluRay, SPARKS
    sub1 = {
        "subtitleFileName": "Interstellar.2014.1080p.BluRay.x264.srt",
        "movieReleaseName": "Interstellar.2014.1080p.BluRay.x264-SPARKS",
        "downloadCount": 10000,
    }
    # Low match: CAM quality (heavily penalized)
    sub2 = {
        "subtitleFileName": "Interstellar.2014.CAM.XviD.srt",
        "movieReleaseName": "Interstellar.2014.CAM",
        "downloadCount": 500,
    }
    # Medium match: WEB-DL, no CAM penalty
    sub3 = {
        "subtitleFileName": "Interstellar.2014.WEB-DL.srt",
        "movieReleaseName": "Interstellar.2014.WEB-DL",
        "downloadCount": 2000,
    }

    score1 = score_subtitle_candidate(sub1, video_name)
    score2 = score_subtitle_candidate(sub2, video_name)
    score3 = score_subtitle_candidate(sub3, video_name)

    assert score1 > score3 > score2


class MockResponse:
    def __init__(self, json_data=None, bytes_data=b"", status=200):
        self._json_data = json_data
        self._bytes_data = bytes_data
        self.status = status

    async def json(self):
        return self._json_data

    async def read(self):
        return self._bytes_data

    async def text(self):
        return self._bytes_data.decode("utf-8", errors="ignore")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockSession:
    def __init__(self, responses=None):
        self.responses = responses or {}

    def get(self, url, **kwargs):
        # Return matched response or default 200
        for pattern, resp in self.responses.items():
            if pattern in url:
                return resp
        return MockResponse(status=404)


@pytest.mark.asyncio
async def test_fetch_stremio_subtitles_mock():
    mock_payload = {
        "subtitles": [
            {
                "id": "123",
                "url": "https://subs.strem.io/sub1.srt",
                "lang": "eng",
                "subtitleFileName": "Movie.1080p.srt",
                "movieReleaseName": "Movie.1080p.BluRay",
                "downloadCount": 100,
            },
            {
                "id": "124",
                "url": "https://subs.strem.io/sub2.srt",
                "lang": "spa",
                "subtitleFileName": "Movie.spa.srt",
            }
        ]
    }
    session = MockSession({
        "opensubtitles-v3.strem.io": MockResponse(json_data=mock_payload)
    })

    results = await fetch_stremio_subtitles(session, "tt0111161", is_tv=False, target_langs=["eng"])
    assert len(results) == 1
    assert results[0]["lang"] == "eng"
    assert results[0]["url"] == "https://subs.strem.io/sub1.srt"


@pytest.mark.asyncio
async def test_download_subtitle_file_mock():
    raw_srt = b"1\n00:00:01,000 --> 00:00:03,000\nHello from downloaded sub\n"
    session = MockSession({
        "https://subs.strem.io/sub1.srt": MockResponse(bytes_data=raw_srt)
    })

    content = await download_subtitle_file(session, "https://subs.strem.io/sub1.srt")
    assert content is not None
    assert "Hello from downloaded sub" in content


@pytest.mark.asyncio
async def test_inject_subtitles_for_entry_mock(tmp_path):
    media_dir = tmp_path / "Movies" / "Inception (2010)"
    media_dir.mkdir(parents=True)
    strm_file = media_dir / "Inception (2010).strm"
    strm_file.write_text("http://stream/123")

    raw_srt = b"1\n00:00:01,000 --> 00:00:03,000\nDream inside a dream\n"
    mock_stremio_json = {
        "subtitles": [
            {
                "id": "999",
                "url": "https://subs.strem.io/inception.srt",
                "lang": "eng",
                "subtitleFileName": "Inception.1080p.BluRay.srt",
                "movieReleaseName": "Inception.1080p.BluRay",
                "downloadCount": 5000,
            }
        ]
    }

    session = MockSession({
        "opensubtitles-v3.strem.io": MockResponse(json_data=mock_stremio_json),
        "https://subs.strem.io/inception.srt": MockResponse(bytes_data=raw_srt),
    })

    entry = {
        "title": "Inception",
        "year": 2010,
        "is_tv": False,
        "imdb_id": "tt1375666",
        "strm_base": "Inception (2010)",
        "target_dir": str(media_dir),
        "file_name": "Inception.2010.1080p.BluRay.x264.mkv",
    }

    injected = await inject_subtitles_for_entry(session, entry, target_langs=["eng"])
    assert len(injected) == 1
    expected_srt = media_dir / "Inception (2010).eng.srt"
    assert expected_srt.exists()
    assert "Dream inside a dream" in expected_srt.read_text(encoding="utf-8")

    # Second run without force should skip because subtitle already exists
    injected2 = await inject_subtitles_for_entry(session, entry, target_langs=["eng"])
    assert len(injected2) == 0


def test_normalize_to_iso639_2():
    from apex_stream.subtitles import normalize_to_iso639_2
    assert normalize_to_iso639_2("en") == "eng"
    assert normalize_to_iso639_2("eng") == "eng"
    assert normalize_to_iso639_2("ml") == "mal"
    assert normalize_to_iso639_2("mal") == "mal"
    assert normalize_to_iso639_2("hi") == "hin"
    assert normalize_to_iso639_2("") == "eng"
    assert normalize_to_iso639_2(None) == "eng"


def test_is_valid_subtitle_file(tmp_path):
    empty_file = tmp_path / "empty.srt"
    empty_file.write_text("")
    assert is_valid_subtitle_file(str(empty_file)) is False

    corrupt_file = tmp_path / "corrupt.srt"
    corrupt_file.write_text("<html><body>Error 502 Bad Gateway</body></html>")
    assert is_valid_subtitle_file(str(corrupt_file)) is False

    valid_file = tmp_path / "valid.srt"
    valid_file.write_text("1\n00:00:01,000 --> 00:00:03,000\nThis is valid\n")
    assert is_valid_subtitle_file(str(valid_file)) is True


def test_purge_corrupted_subtitles(tmp_path):
    movie_dir = tmp_path / "Movies" / "Iron Man (2008)"
    movie_dir.mkdir(parents=True)

    # Corrupt 0-byte files and broken suffix
    zero_sub = movie_dir / "Iron Man (2008).eng.0.srt"
    zero_sub.write_text("")
    forced_sub = movie_dir / "Iron Man (2008).eng.forced.srt"
    forced_sub.write_text("Not valid subtitle content")
    broken_sub = movie_dir / "Iron Man (2008).eng.srt"
    broken_sub.write_text("")

    # Legitimate subtitle file
    good_sub = movie_dir / "Iron Man (2008).mal.srt"
    good_sub.write_text("1\n00:00:05,000 --> 00:00:08,000\nValid malayalam line\n")

    purged = purge_corrupted_subtitles([str(tmp_path)])
    assert purged == 3
    assert not zero_sub.exists()
    assert not forced_sub.exists()
    assert not broken_sub.exists()
    assert good_sub.exists()


@pytest.mark.asyncio
async def test_inject_subtitles_replaces_corrupt_existing_file(tmp_path):
    media_dir = tmp_path / "Movies" / "Iron Man (2008)"
    media_dir.mkdir(parents=True)
    strm_file = media_dir / "Iron Man (2008).strm"
    strm_file.write_text("http://stream/120")

    # Existing corrupt 0-byte file (reproducing the user's issue)
    corrupt_existing = media_dir / "Iron Man (2008).eng.srt"
    corrupt_existing.write_text("")

    raw_srt = b"1\n00:01:19,240 --> 00:01:21,760\nI feel like you\n"
    mock_json = {
        "subtitles": [
            {
                "id": "111",
                "url": "https://subs.strem.io/ironman.srt",
                "lang": "eng",
                "subtitleFileName": "Iron.Man.1080p.srt",
                "downloadCount": 1000,
            }
        ]
    }
    session = MockSession({
        "opensubtitles-v3.strem.io": MockResponse(json_data=mock_json),
        "https://subs.strem.io/ironman.srt": MockResponse(bytes_data=raw_srt),
    })

    entry = {
        "title": "Iron Man",
        "year": 2008,
        "is_tv": False,
        "imdb_id": "tt0371746",
        "strm_base": "Iron Man (2008)",
        "target_dir": str(media_dir),
        "file_name": "Iron.Man.2008.1080p.mkv",
    }

    # Should detect corrupt existing file, delete it, and download healthy replacement
    injected = await inject_subtitles_for_entry(session, entry, target_langs=["eng"])
    assert len(injected) == 1
    assert corrupt_existing.exists()
    assert is_valid_subtitle_file(str(corrupt_existing)) is True
    assert "I feel like you" in corrupt_existing.read_text(encoding="utf-8")


def test_adjust_srt_timing():
    srt = (
        "1\n"
        "00:01:20,000 --> 00:01:23,500\n"
        "Hello World\n\n"
        "2\n"
        "00:02:10.200 --> 00:02:15.800\n"
        "Second Line\n"
    )

    # Shift +2.5 seconds
    shifted_pos = adjust_srt_timing(srt, 2.5)
    assert "00:01:22,500 --> 00:01:26,000" in shifted_pos
    assert "00:02:12.700 --> 00:02:18.300" in shifted_pos
    assert "Hello World" in shifted_pos

    # Shift -100.0 seconds (clamped to 0)
    shifted_neg = adjust_srt_timing(srt, -100.0)
    assert "00:00:00,000 --> 00:00:00,000" in shifted_neg

    # Shift 0 seconds
    assert adjust_srt_timing(srt, 0.0) == srt


def test_normalize_to_iso639_2():
    assert normalize_to_iso639_2("en") == "eng"
    assert normalize_to_iso639_2("English") == "eng"
    assert normalize_to_iso639_2("Malayalam") == "mal"
    assert normalize_to_iso639_2("ml") == "mal"
    assert normalize_to_iso639_2("mal") == "mal"
    assert normalize_to_iso639_2("es") == "spa"


@pytest.mark.asyncio
async def test_fetch_subdl_subtitles_mock():
    mock_payload = {
        "status": True,
        "subtitles": [
            {
                "release_name": "Iron.Man.3.2013.1080p.BluRay.x264-SPARKS",
                "name": "Iron Man 3",
                "lang": "English",
                "author": "SPARKS",
                "url": "/subtitle/iron-man-3-1080p.zip",
                "download_count": 12000,
            }
        ]
    }
    session = MockSession({
        "api.subdl.com": MockResponse(json_data=mock_payload)
    })

    cands = await fetch_subdl_subtitles(session, imdb_id="tt1300854", target_langs=["eng"])
    assert len(cands) == 1
    assert cands[0]["url"] == "https://dl.subdl.com/subtitle/iron-man-3-1080p.zip"
    assert cands[0]["lang"] == "eng"
    assert cands[0]["provider"] == "subdl"
    assert cands[0]["movieReleaseName"] == "Iron.Man.3.2013.1080p.BluRay.x264-SPARKS"


@pytest.mark.asyncio
async def test_fetch_opensubtitles_com_mock(monkeypatch):
    monkeypatch.setenv("OPENSUBTITLES_API_KEY", "test-api-key")
    mock_payload = {
        "data": [
            {
                "attributes": {
                    "language": "en",
                    "release": "Iron.Man.3.2013.1080p.BluRay",
                    "download_count": 450,
                    "files": [
                        {"file_id": 98765, "file_name": "IronMan3.srt"}
                    ]
                }
            }
        ]
    }
    session = MockSession({
        "api.opensubtitles.com": MockResponse(json_data=mock_payload)
    })

    cands = await fetch_opensubtitles_com(session, imdb_id="tt1300854", target_langs=["eng"])
    assert len(cands) == 1
    assert cands[0]["id"] == "98765"
    assert cands[0]["url"] == "https://api.opensubtitles.com/api/v1/download/98765"
    assert cands[0]["lang"] == "eng"
    assert cands[0]["provider"] == "opensubtitles.com"





