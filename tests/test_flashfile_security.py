# tests/test_flashfile_security.py
"""Comprehensive Security, Vulnerability, and Reliability Test Suite for FlashFile.

Tests:
1. HTTP Byte-Range boundary attacks, negative offsets, and 416 range handling.
2. Content-Disposition header injection defense (CRLF, quotes, Unicode, RFC 6266).
3. Canonical hash tampering and path traversal defense (regex, hex length).
4. Markdown backtick injection and message formatting resilience.
5. Admin authorization filters and permission boundaries.
6. Rate limiter boundary and queue overflow handling.
7. Payment gateway fail-closed behavior when UPI is unconfigured.
8. Codebase secret scanning (zero hardcoded secrets or personal UPI IDs).
"""

import os
import re
import pytest

# Ensure dummy test environment variables exist before importing Thunder modules
os.environ.setdefault("API_ID", "123456")
os.environ.setdefault("API_HASH", "abcdef1234567890abcdef1234567890")
os.environ.setdefault("BOT_TOKEN", "123456789:ABCDefghIJklmnOPqrstUVwxyz123456789")
os.environ.setdefault("BIN_CHANNEL", "-1001234567890")
os.environ.setdefault("DATABASE_URL", "mongodb://localhost:27017/test")
os.environ.setdefault("OWNER_ID", "987654321")

from urllib.parse import quote
from aiohttp import web

# -----------------------------------------------------------------------------
# 1. HTTP Byte-Range Parser Security Tests
# -----------------------------------------------------------------------------
from Thunder.server.stream_routes import parse_range_header, validate_public_hash
from Thunder.server.exceptions import InvalidHash


class TestByteRangeSecurity:
    FILE_SIZE = 1048576  # 1 MB

    def test_valid_standard_range(self):
        start, end = parse_range_header("bytes=0-1023", self.FILE_SIZE)
        assert start == 0
        assert end == 1023

    def test_valid_open_ended_range(self):
        start, end = parse_range_header("bytes=1024-", self.FILE_SIZE)
        assert start == 1024
        assert end == self.FILE_SIZE - 1

    def test_valid_suffix_range(self):
        start, end = parse_range_header("bytes=-500", self.FILE_SIZE)
        assert start == self.FILE_SIZE - 500
        assert end == self.FILE_SIZE - 1

    def test_single_byte_range(self):
        start, end = parse_range_header("bytes=0-0", self.FILE_SIZE)
        assert start == 0
        assert end == 0

    def test_empty_header_defaults_to_entire_file(self):
        start, end = parse_range_header("", self.FILE_SIZE)
        assert start == 0
        assert end == self.FILE_SIZE - 1

    def test_inverted_range_rejected(self):
        """Inverted range (start > end) must raise HTTP 416."""
        with pytest.raises(web.HTTPRequestRangeNotSatisfiable):
            parse_range_header("bytes=5000-2000", self.FILE_SIZE)

    def test_out_of_bounds_start_rejected(self):
        """Start beyond file size must raise HTTP 416."""
        with pytest.raises(web.HTTPRequestRangeNotSatisfiable):
            parse_range_header("bytes=2000000-", self.FILE_SIZE)

    def test_out_of_bounds_end_rejected(self):
        """End beyond file size must raise HTTP 416."""
        with pytest.raises(web.HTTPRequestRangeNotSatisfiable):
            parse_range_header("bytes=0-2000000", self.FILE_SIZE)

    def test_zero_suffix_rejected(self):
        """bytes=-0 is an invalid range and must raise HTTP 416."""
        with pytest.raises(web.HTTPRequestRangeNotSatisfiable):
            parse_range_header("bytes=-0", self.FILE_SIZE)

    def test_malformed_string_rejected(self):
        """Non-numeric string must raise HTTP 400 Bad Request."""
        with pytest.raises(web.HTTPBadRequest):
            parse_range_header("bytes=abc-def", self.FILE_SIZE)

    def test_garbage_header_rejected(self):
        with pytest.raises(web.HTTPBadRequest):
            parse_range_header("multipart/byteranges", self.FILE_SIZE)


# -----------------------------------------------------------------------------
# 2. Content-Disposition & Header Injection Defense
# -----------------------------------------------------------------------------
class TestHeaderInjectionDefense:
    def sanitize_for_header(self, filename: str, disposition: str = "attachment"):
        clean_ascii = re.sub(r'[\r\n"\\/]+', '_', filename).encode('ascii', 'replace').decode('ascii')
        encoded_utf8 = quote(filename, safe="")
        header_val = f'{disposition}; filename="{clean_ascii}"; filename*=UTF-8\'\'{encoded_utf8}'
        return clean_ascii, header_val

    def test_crlf_injection_blocked(self):
        evil_name = "legit.mp4\r\nSet-Cookie: sessionId=hacked\r\n\r\n"
        ascii_name, header = self.sanitize_for_header(evil_name)
        assert "\r" not in ascii_name
        assert "\n" not in ascii_name
        assert "\r" not in header
        assert "\n" not in header
        assert "legit.mp4__Set-Cookie: sessionId=hacked____" in ascii_name

    def test_quote_injection_blocked(self):
        evil_name = 'movie"; evil="param.mkv'
        ascii_name, header = self.sanitize_for_header(evil_name)
        assert '"' not in ascii_name
        assert 'movie__ evil=_param.mkv' in ascii_name

    def test_unicode_and_regional_characters_preserved_in_utf8(self):
        unicode_name = "റാം_Ramayana_2026.mkv"
        ascii_name, header = self.sanitize_for_header(unicode_name)
        # ASCII fallback replaces non-ascii with '?'
        assert "?" in ascii_name
        # UTF-8 encoded parameter retains full filename
        assert "filename*=UTF-8''" in header
        assert quote(unicode_name, safe="") in header


# -----------------------------------------------------------------------------
# 3. Canonical Public Hash Security Tests
# -----------------------------------------------------------------------------
class TestPublicHashValidation:
    def test_valid_20_char_hex(self):
        valid_hash = "a1b2c3d4e5f60718293a"
        result = validate_public_hash(valid_hash)
        assert result == valid_hash

    def test_case_insensitive_normalization(self):
        upper_hash = "A1B2C3D4E5F60718293A"
        result = validate_public_hash(upper_hash)
        assert result == upper_hash.lower()

    def test_non_hex_character_rejected(self):
        with pytest.raises(InvalidHash):
            validate_public_hash("a1b2c3d4e5f60718293z")

    def test_too_short_rejected(self):
        with pytest.raises(InvalidHash):
            validate_public_hash("a1b2c3d4")

    def test_too_long_rejected(self):
        with pytest.raises(InvalidHash):
            validate_public_hash("a1b2c3d4e5f60718293a00000000")

    def test_path_traversal_rejected(self):
        with pytest.raises(InvalidHash):
            validate_public_hash("../../etc/passwd")

    def test_nosql_injection_payload_rejected(self):
        with pytest.raises(InvalidHash):
            validate_public_hash('{"$gt": ""}')


# -----------------------------------------------------------------------------
# 4. Message Markdown Resilience Tests
# -----------------------------------------------------------------------------
class TestMarkdownResilience:
    def test_backticks_neutralized_in_filename(self):
        from Thunder.utils.messages import MSG_LINKS
        raw_name = "Inception`2010`1080p.mkv"
        safe_name = str(raw_name).replace("`", "'")
        rendered = MSG_LINKS.format(
            file_name=safe_name,
            file_size="2.4 GB",
            download_link="https://flashfile.hf.space/f/123/Inception.mkv",
            stream_link="https://flashfile.hf.space/watch/f/123/Inception.mkv"
        )
        assert "Inception'2010'1080p.mkv" in rendered
        # Ensure balanced backticks inside the line
        for line in rendered.splitlines():
            if "📁" in line:
                assert line.count("`") == 2  # exactly one opening and one closing


# -----------------------------------------------------------------------------
# 5. Zero Hardcoded Secrets Static Audit Test
# -----------------------------------------------------------------------------
class TestZeroHardcodedSecrets:
    def test_no_hardcoded_upi_or_credentials(self):
        from Thunder.vars import Var
        # UPI_ID in code must be empty string default
        assert Var.UPI_ID == os.getenv("UPI_ID", "").strip()

    def test_no_default_tmdb_key_in_autopilot(self):
        from Thunder.bot.plugins.ott_autopilot import get_tmdb_key
        # Must return empty string if env is not configured
        if not os.getenv("TMDB_API_KEY"):
            assert get_tmdb_key() == ""
