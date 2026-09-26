"""Tests for tg_streamer route parsing, cache lookup, and defensive ID handling."""

import hashlib
import hmac
import types
from unittest.mock import MagicMock

import pytest

from apex_stream.tmdb_meta import parse_media_meta


def _cache_key(chat_id, message_id):
    try:
        chat = int(chat_id or 0)
    except (TypeError, ValueError):
        chat = 0
    return f"{chat}:{int(message_id)}"


def _meta_to_entry(msg_id, chat_id, file_id, file_size, file_name):
    try:
        m_int = int(msg_id)
        c_int = int(chat_id)
        if m_int < 0 and c_int > 0:
            msg_id, chat_id = c_int, m_int
    except (TypeError, ValueError):
        pass
    meta = parse_media_meta(file_name)
    return {
        "file_id": file_id,
        "chat_id": chat_id,
        "msg_id": msg_id,
        "file_size": file_size,
        "file_name": file_name,
        "title": meta["title"],
        "clean_title": meta["clean_title"],
        "search_title": meta["search_title"],
        "is_tv": meta["is_tv"],
        "show_name": meta["show_name"],
        "season": meta["season"],
        "episode": meta["episode"],
        "year": meta["year"],
        "language": meta["language"],
        "_cache_key": _cache_key(chat_id, msg_id),
    }


def _split_cache_key(key):
    if isinstance(key, str) and ":" in key:
        try:
            chat_part, msg_part = key.rsplit(":", 1)
            c = int(chat_part)
            m = int(msg_part)
            if c > 0 and m < 0:
                c, m = m, c
            return c, m
        except (TypeError, ValueError):
            return None, key
    return None, key


def _cache_lookup(cache, message_id, chat_id=None):
    try:
        m_int = int(message_id)
        if m_int < 0 and chat_id is not None and int(chat_id) > 0:
            message_id, chat_id = int(chat_id), m_int
    except (TypeError, ValueError):
        pass
    if chat_id:
        entry = cache.get(_cache_key(chat_id, message_id))
        if isinstance(entry, dict):
            return entry
        alt_entry = cache.get(_cache_key(message_id, chat_id))
        if isinstance(alt_entry, dict):
            return alt_entry
    legacy = cache.get(str(message_id))
    if isinstance(legacy, dict):
        if chat_id and legacy.get("chat_id") and str(legacy.get("chat_id")) != str(chat_id):
            return None
        return legacy
    if not chat_id:
        for key, entry in cache.items():
            if not isinstance(entry, dict) or not isinstance(key, str) or ":" not in key:
                continue
            try:
                _chat_part, _msg_part = key.rsplit(":", 1)
                if int(_msg_part) == int(message_id):
                    return entry
            except (TypeError, ValueError):
                continue
    return None


def _source_path_from_request(match_info, query=None, cache=None):
    query = query or {}
    cache = cache or {}
    chat_id = match_info.get("chat_id")
    msg_id = match_info.get("message_id") or query.get("message_id")
    if msg_id is None:
        return None
    try:
        message_id = int(msg_id)
    except (TypeError, ValueError):
        return None
    if chat_id is None:
        entry = _cache_lookup(cache, message_id)
        if isinstance(entry, dict) and entry.get("chat_id"):
            chat_id = entry["chat_id"]
        else:
            chat_id = 0
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        chat_id = 0
    if chat_id > 0 and message_id < 0:
        chat_id, message_id = message_id, chat_id
    return chat_id, message_id


def _stream_signature(key, chat_id, message_id, expires):
    if not key:
        return ""
    value = f"{int(chat_id)}:{int(message_id)}:{int(expires)}".encode()
    return hmac.new(key.encode(), value, hashlib.sha256).hexdigest()


class TestDefensiveIds:
    def test_meta_to_entry_normal_order(self):
        entry = _meta_to_entry(22, -1003907801136, "fid123", 1000, "Movie (2022).mp4")
        assert entry["msg_id"] == 22
        assert entry["chat_id"] == -1003907801136
        assert entry["_cache_key"] == "-1003907801136:22"

    def test_meta_to_entry_swapped_order_auto_corrected(self):
        # When passed (-1003907801136, 22), it should detect and un-swap them
        entry = _meta_to_entry(-1003907801136, 22, "fid123", 1000, "Movie (2022).mp4")
        assert entry["msg_id"] == 22
        assert entry["chat_id"] == -1003907801136
        assert entry["_cache_key"] == "-1003907801136:22"

    def test_split_cache_key(self):
        assert _split_cache_key("-1003907801136:22") == (-1003907801136, 22)
        assert _split_cache_key("22:-1003907801136") == (-1003907801136, 22)

    def test_cache_lookup_with_normal_and_swapped_keys(self):
        cache = {
            "-1003907801136:22": {"msg_id": 22, "chat_id": -1003907801136, "title": "Spider-Man"},
        }
        # Normal lookup
        res = _cache_lookup(cache, 22, -1003907801136)
        assert res is not None
        assert res["title"] == "Spider-Man"

        # Lookup when caller passes inverted args: _cache_lookup(-1003907801136, 22)
        res_inv = _cache_lookup(cache, -1003907801136, 22)
        assert res_inv is not None
        assert res_inv["title"] == "Spider-Man"

    def test_source_path_inverted_url_correction(self):
        # URL had /stream/22/-1003907801136/video.mp4
        match_info = {"chat_id": "22", "message_id": "-1003907801136"}
        chat_id, message_id = _source_path_from_request(match_info)
        assert chat_id == -1003907801136
        assert message_id == 22

    def test_dual_signature_matches(self):
        signing_key = "secret_key"
        expires = 1790507041
        # Signature created with swapped (22, -1003907801136)
        sig_old = _stream_signature(signing_key, 22, -1003907801136, expires)

        # Corrected source
        chat_id = -1003907801136
        message_id = 22

        expected = _stream_signature(signing_key, chat_id, message_id, expires)
        alt_expected = _stream_signature(signing_key, message_id, chat_id, expires)

        sig_matches = hmac.compare_digest(sig_old, expected) or hmac.compare_digest(sig_old, alt_expected)
        assert sig_matches is True
