"""
FlashFile Sleep Notification Dispatcher
=======================================
Sends an instant, high-priority alert to the bot owner's Telegram chat
when the Hugging Face Space is shutting down / going to sleep.

Includes an inline '⚡ Wake Up Space' button linking to the /keepalive
endpoint to allow instant 1-tap reawakening.
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("notify_sleep")


def build_sleep_payload(bot_token: str, owner_id: int, public_url: str) -> dict:
    """Constructs the Telegram sendMessage payload with inline wakeup button."""
    base_url = public_url.rstrip("/") + "/"
    wake_url = f"{base_url}keepalive"
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    text = (
        "⚡ <b>FlashFile Alert: Space Going to Sleep</b> 💤\n\n"
        "Your Hugging Face Space container has been idle and is now entering <b>sleep mode</b>.\n\n"
        f"⏱ <b>Timestamp:</b> <code>{now_utc}</code>\n"
        f"🌐 <b>Space:</b> <code>{base_url}</code>\n\n"
        "<i>Tap the button below to re-ping the server and wake it up instantly!</i>"
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚡ Wake Up Space", "url": wake_url}
            ]
        ]
    }

    return {
        "chat_id": owner_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": keyboard,
    }


def send_sleep_alert() -> bool:
    """Dispatches a Telegram message to OWNER_ID notifying that Space is entering sleep."""
    bot_token = os.environ.get("BOT_TOKEN", "").strip(" '\"")
    raw_owner_id = os.environ.get("OWNER_ID", "").strip(" '\"")
    raw_url = os.environ.get("URL", "https://jishnupg-filetolink.hf.space/").strip(" '\"")

    if not bot_token or not raw_owner_id or raw_owner_id == "0":
        try:
            from Thunder.vars import Var
            bot_token = bot_token or getattr(Var, "BOT_TOKEN", "")
            raw_owner_id = raw_owner_id or str(getattr(Var, "OWNER_ID", 0))
            raw_url = raw_url or getattr(Var, "URL", "https://jishnupg-filetolink.hf.space/")
        except Exception as e:
            logger.debug("Could not read from Thunder.vars: %s", e)

    if not bot_token:
        logger.warning("[SLEEP_ALERT] BOT_TOKEN is missing. Cannot send alert.")
        return False

    if not raw_owner_id or raw_owner_id == "0":
        logger.warning("[SLEEP_ALERT] OWNER_ID is missing or 0. Cannot send alert.")
        return False

    try:
        owner_id = int(raw_owner_id)
    except ValueError:
        logger.warning("[SLEEP_ALERT] Invalid numeric OWNER_ID: %s", raw_owner_id)
        return False

    payload = build_sleep_payload(bot_token, owner_id, raw_url)
    endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "FlashFile-SleepNotifier/1.0"},
    )

    try:
        logger.info("[SLEEP_ALERT] Sending sleep alert to chat_id=%s via Telegram API...", owner_id)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                logger.info("[SLEEP_ALERT] Successfully delivered sleep alert to Telegram.")
                return True
            logger.warning("[SLEEP_ALERT] Telegram API responded with HTTP %s", resp.status)
            return False
    except urllib.error.HTTPError as he:
        try:
            err_body = he.read().decode("utf-8")
        except Exception:
            err_body = str(he)
        logger.error("[SLEEP_ALERT] Telegram HTTP error: %s - %s", he.code, err_body)
        return False
    except Exception as exc:
        logger.error("[SLEEP_ALERT] Failed to deliver sleep alert: %s", exc)
        return False


if __name__ == "__main__":
    success = send_sleep_alert()
    sys.exit(0 if success else 1)
