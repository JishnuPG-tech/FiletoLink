# Thunder/vars.py

import os

from dotenv import load_dotenv
from typing import Set, Optional, Union
from Thunder.utils.logger import logger

load_dotenv("config.env")

def str_to_bool(val: str) -> bool:
    return val.lower() in ("true", "1", "t", "y", "yes")

def str_to_int_set(val: str) -> Set[int]:
    if not val:
        return set()
    result: Set[int] = set()
    for x in val.split():
        try:
            result.add(int(x))
        except (TypeError, ValueError):
            continue
    return result

def parse_channel_target(val: Optional[str], default: Optional[str] = None) -> Optional[Union[int, str]]:
    raw = (val or default or "").strip(" '\"")
    if not raw:
        return None
    if "t.me/" in raw:
        raw = raw.split("t.me/")[-1].strip("/")
    try:
        num = int(raw)
        if num > 0 and len(str(num)) >= 9:
            num = int(f"-100{num}")
        return num
    except ValueError:
        if not raw.startswith("@") and not raw.startswith("-"):
            raw = f"@{raw}"
        return raw




class Var:
    raw_api_id = os.getenv("API_ID", "0").strip(" '\"")
    API_ID: int = int(raw_api_id) if raw_api_id.isdigit() else 0
    API_HASH: str = os.getenv("API_HASH", "").strip(" '\"")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip(" '\"")

    logger.info(
        "FlashFile Telegram configuration loaded "
        "(api_id=%s, api_hash=%s, bot_token=%s)",
        "set" if API_ID else "missing",
        "set" if API_HASH else "missing",
        "set" if BOT_TOKEN else "missing",
    )

    if not all([API_ID, API_HASH, BOT_TOKEN]):
        logger.critical("Missing required Telegram API configuration")
        raise ValueError("Missing required Telegram API configuration")

    NAME: str = os.getenv("NAME", "FlashFile")
    SLEEP_THRESHOLD: int = int(os.getenv("SLEEP_THRESHOLD", "600"))
    WORKERS: int = int(os.getenv("WORKERS", "8"))

    BIN_CHANNEL: int = int(os.getenv("BIN_CHANNEL", "0"))

    if not BIN_CHANNEL:
        logger.critical("BIN_CHANNEL is required")
        raise ValueError("BIN_CHANNEL is required")

    PORT: int = int(os.getenv("FILETOLINK_PORT", os.getenv("PORT", "8080")))
    BIND_ADDRESS: str = os.getenv("BIND_ADDRESS", "0.0.0.0")
    PING_INTERVAL: int = int(os.getenv("PING_INTERVAL", "840"))
    NO_PORT: bool = str_to_bool(os.getenv("NO_PORT", "True"))


    raw_owner_id = os.getenv("OWNER_ID", "0").strip(" '\"")
    OWNER_ID: int = int(raw_owner_id) if (raw_owner_id.isdigit() or (raw_owner_id.startswith("-") and raw_owner_id[1:].isdigit())) else 0
    if not OWNER_ID:
        logger.warning("WARNING: OWNER_ID is not set. No user will be granted owner access.")

    FQDN: str = os.getenv("FQDN", "") or BIND_ADDRESS
    HAS_SSL: bool = str_to_bool(os.getenv("HAS_SSL", "True"))
    PROTOCOL: str = "https" if HAS_SSL else "http"
    PORT_SEGMENT: str = "" if NO_PORT else f":{PORT}"
    URL: str = f"{PROTOCOL}://{FQDN}{PORT_SEGMENT}/"

    SET_COMMANDS: bool = str_to_bool(os.getenv("SET_COMMANDS", "True"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    if not DATABASE_URL:
        logger.critical("DATABASE_URL is required")
        raise ValueError("DATABASE_URL is required")

    MAX_BATCH_FILES: int = int(os.getenv("MAX_BATCH_FILES", "50"))

    CHANNEL: bool = str_to_bool(os.getenv("CHANNEL", "False"))

    BANNED_CHANNELS: Set[int] = str_to_int_set(os.getenv("BANNED_CHANNELS", ""))

    MULTI_CLIENT: bool = False

    FORCE_CHANNEL_ID: Optional[Union[int, str]] = parse_channel_target(os.getenv("FORCE_CHANNEL_ID"), default="@flashfilez")

    TOKEN_ENABLED: bool = str_to_bool(os.getenv("TOKEN_ENABLED", "False"))
    TOKEN_TTL_HOURS: int = int(os.getenv("TOKEN_TTL_HOURS", "24"))

    SHORTEN_ENABLED: bool = str_to_bool(os.getenv("SHORTEN_ENABLED", "False"))
    SHORTEN_MEDIA_LINKS: bool = str_to_bool(os.getenv("SHORTEN_MEDIA_LINKS", "False"))
    URL_SHORTENER_API_KEY: str = os.getenv("URL_SHORTENER_API_KEY", "")
    URL_SHORTENER_SITE: str = os.getenv("URL_SHORTENER_SITE", "")

    GLOBAL_RATE_LIMIT: bool = str_to_bool(os.getenv("GLOBAL_RATE_LIMIT", "False"))
    MAX_GLOBAL_REQUESTS_PER_MINUTE: int = int(os.getenv("MAX_GLOBAL_REQUESTS_PER_MINUTE", "4"))

    RATE_LIMIT_ENABLED: bool = str_to_bool(os.getenv("RATE_LIMIT_ENABLED", "False"))
    MAX_FILES_PER_PERIOD: int = int(os.getenv("MAX_FILES_PER_PERIOD", "2"))
    RATE_LIMIT_PERIOD_MINUTES: int = int(os.getenv("RATE_LIMIT_PERIOD_MINUTES", "1"))
    MAX_QUEUE_SIZE: int = int(os.getenv("MAX_QUEUE_SIZE", "100"))

    # Subscription & Payment Gateway (Dormant by default)
    PAYMENT_ENABLED: bool = str_to_bool(os.getenv("PAYMENT_ENABLED", os.getenv("PAYMENT", os.getenv("Payment", os.getenv("payment", "False")))))
    SUB_PRICE: int = int(os.getenv("SUB_PRICE", "10"))
    SUB_DURATION_DAYS: int = int(os.getenv("SUB_DURATION_DAYS", "30"))
    UPI_ID: str = os.getenv("UPI_ID", "").strip()
    ADMIN_CHANNEL: int = int(os.getenv("ADMIN_CHANNEL", "0"))

    # TMDB & OTT Channel Autopilot
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "").strip()
    OTT_AUTOPILOT: bool = str_to_bool(os.getenv("OTT_AUTOPILOT", "True"))
    OTT_CHANNEL_ID: Optional[Union[int, str]] = parse_channel_target(
        os.getenv("OTT_CHANNEL_ID"),
        default=os.getenv("FORCE_CHANNEL_ID", "@flashfilez"),
    )

    OTT_REGION: str = os.getenv("OTT_REGION", "IN").strip().upper()
    OTT_SCHEDULE_HOUR: int = int(os.getenv("OTT_SCHEDULE_HOUR", "9"))
    OTT_SCHEDULE_MINUTE: int = int(os.getenv("OTT_SCHEDULE_MINUTE", "0"))
    OTT_TIMEZONE_OFFSET: float = float(os.getenv("OTT_TIMEZONE_OFFSET", "5.5"))

    # Channel Welcome System
    WELCOME_CHANNEL_ENABLED: bool = str_to_bool(os.getenv("WELCOME_CHANNEL_ENABLED", "True"))
    WELCOME_AUTO_DELETE_SECONDS: int = int(os.getenv("WELCOME_AUTO_DELETE_SECONDS", "60"))

    # Weekly Server Milestone Card
    MILESTONE_ENABLED: bool = str_to_bool(os.getenv("MILESTONE_ENABLED", "True"))
    MILESTONE_CHANNEL_ID: Optional[Union[int, str]] = parse_channel_target(
        os.getenv("MILESTONE_CHANNEL_ID"),
        default=os.getenv("FORCE_CHANNEL_ID", "@flashfilez"),
    )

    MILESTONE_DAY: int = int(os.getenv("MILESTONE_DAY", "6"))  # 6 = Sunday
    MILESTONE_HOUR: int = int(os.getenv("MILESTONE_HOUR", "20"))  # 20:00 = 8:00 PM
    MILESTONE_MINUTE: int = int(os.getenv("MILESTONE_MINUTE", "0"))
