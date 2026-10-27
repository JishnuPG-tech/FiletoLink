"""Unit tests for ai_admin/validators.py and ai_admin/net_guard.py."""

import pytest
from ai_admin.net_guard import is_ip_private_or_restricted, validate_outbound_url
from ai_admin.validators import (
    safe_join_path,
    validate_candidate_id,
    validate_image_bytes,
    validate_image_type,
    validate_item_id,
    validate_language_code,
    validate_subtitle_bytes,
)


def test_item_and_candidate_id_validation():
    assert validate_item_id("767BFFE4-F11C-93EF-34B8-05451A696A4E") is True
    assert validate_item_id("abc12345") is True
    assert validate_item_id("../evil") is False
    assert validate_item_id("") is False

    assert validate_candidate_id("cand_0123456789abcdef0123456789abcdef") is True
    assert validate_candidate_id("cand_short") is False
    assert validate_candidate_id("https://evil.com") is False


def test_image_type_and_bytes_validation():
    assert validate_image_type("primary") is True
    assert validate_image_type("Backdrop") is True
    assert validate_image_type("malicious_type") is False

    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 30
    ok, ctype = validate_image_bytes(jpeg_bytes)
    assert ok is True
    assert ctype == "image/jpeg"

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
    ok, ctype = validate_image_bytes(png_bytes)
    assert ok is True
    assert ctype == "image/png"

    html_bytes = b"<html><body>Not an image</body></html>"
    ok, reason = validate_image_bytes(html_bytes)
    assert ok is False


def test_subtitle_bytes_validation():
    valid_srt = (
        b"1\n00:01:20,000 --> 00:01:23,000\nHello World\n\n"
        b"2\n00:01:24,000 --> 00:01:26,000\nGoodbye\n"
    )
    ok, msg = validate_subtitle_bytes(valid_srt)
    assert ok is True

    html_srt = b"<html><body>404 Not Found</body></html>"
    ok, msg = validate_subtitle_bytes(html_srt)
    assert ok is False
    assert "HTML error page" in msg

    binary_data = b"PK\x03\x04\x00\x00somebinarydata"
    ok, msg = validate_subtitle_bytes(binary_data)
    assert ok is False


def test_safe_join_path_traversal_prevention(tmp_path):
    root = str(tmp_path / "media")
    ok, path = safe_join_path(root, "Movies", "Inception (2010)", "poster.jpg")
    assert ok is True
    assert path.startswith(str(tmp_path))

    # Traversal attempts
    ok_bad, msg = safe_join_path(root, "..", "..", "etc", "passwd")
    assert ok_bad is False
    assert "Path traversal" in msg


def test_net_guard_ssrf_and_ip_restrictions():
    # Restricted IPs
    assert is_ip_private_or_restricted("127.0.0.1") is True
    assert is_ip_private_or_restricted("10.0.0.5") is True
    assert is_ip_private_or_restricted("192.168.1.1") is True
    assert is_ip_private_or_restricted("169.254.169.254") is True
    assert is_ip_private_or_restricted("::1") is True
    assert is_ip_private_or_restricted("8.8.8.8") is False

    # Protocol checks
    ok, msg = validate_outbound_url("http://image.tmdb.org/t/p/original/test.jpg")
    assert ok is False
    assert "Insecure protocol" in msg

    # Disallowed host check
    ok, msg = validate_outbound_url("https://malicious-external-site.com/bad.jpg")
    assert ok is False
    assert "not in approved provider allowlist" in msg
