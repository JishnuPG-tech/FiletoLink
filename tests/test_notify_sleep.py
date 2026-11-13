"""Unit tests for Thunder/utils/notify_sleep.py."""

import json
import os
from unittest.mock import MagicMock, patch
import pytest

from Thunder.utils.notify_sleep import build_sleep_payload, send_sleep_alert


def test_build_sleep_payload():
    payload = build_sleep_payload(
        bot_token="123456:ABC-DEF",
        owner_id=987654321,
        public_url="https://jishnupg-filetolink.hf.space/"
    )
    assert payload["chat_id"] == 987654321
    assert payload["parse_mode"] == "HTML"
    assert "sleep mode" in payload["text"]
    assert "inline_keyboard" in payload["reply_markup"]

    buttons = payload["reply_markup"]["inline_keyboard"][0]
    assert len(buttons) == 1
    assert buttons[0]["text"] == "⚡ Wake Up Space"
    assert buttons[0]["url"] == "https://jishnupg-filetolink.hf.space/keepalive"


def test_send_sleep_alert_missing_credentials(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("OWNER_ID", raising=False)
    assert send_sleep_alert() is False


def test_send_sleep_alert_invalid_owner_id(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OWNER_ID", "not_a_number")
    assert send_sleep_alert() is False


def test_send_sleep_alert_success(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OWNER_ID", "987654321")
    monkeypatch.setenv("URL", "https://test.hf.space")

    mock_resp = MagicMock()
    mock_resp.status = 200

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        result = send_sleep_alert()
        assert result is True
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert "123456:ABC-DEF/sendMessage" in req.full_url
        data = json.loads(req.data.decode("utf-8"))
        assert data["chat_id"] == 987654321
        assert "https://test.hf.space/keepalive" in data["reply_markup"]["inline_keyboard"][0][0]["url"]


def test_send_sleep_alert_network_failure(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OWNER_ID", "987654321")

    with patch("urllib.request.urlopen", side_effect=Exception("Connection timed out")):
        assert send_sleep_alert() is False
