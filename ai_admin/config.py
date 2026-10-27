"""Configuration, environment validation, and feature flags for AI Admin."""

import os
import logging
from dataclasses import dataclass, field
from typing import Set, Optional, List
from ai_admin.redaction import register_secret_string

logger = logging.getLogger("AIAdmin.Config")

DEFAULT_WORKING_MODELS: List[str] = [
    "oc/gemini-3.5-flash-lite",
    "oc/gemini-3.5-flash",
    "oc/gemini-3.6-flash",
    "oc/claude-sonnet-4-6",
    "oc/grok-4.5",
    "oc/glm-5.3-flash",
    "oc/kimi-k3",
]


def _str_to_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on", "t")


def _parse_id_set(val: Optional[str]) -> Set[int]:
    if not val:
        return set()
    result = set()
    for token in re_split(r"[,\s;]+", val.strip()):
        if not token:
            continue
        try:
            result.add(int(token))
        except ValueError:
            logger.warning(f"Invalid integer ID in configuration: '{token}'")
    return result


import re


def re_split(pattern: str, text: str):
    return re.split(pattern, text)


@dataclass
class AIAdminConfig:
    # Feature flags (fail-closed defaults)
    enabled: bool = False
    mutations_enabled: bool = False

    # Authorization
    admin_telegram_ids: Set[int] = field(default_factory=set)
    allowed_chat_ids: Set[int] = field(default_factory=set)

    # OmniRoute LLM settings
    omniroute_api_url: str = ""
    omniroute_api_key: str = ""
    ai_model: str = "oc/gemini-3.5-flash-lite"
    ai_models: List[str] = field(default_factory=list)
    ai_max_tokens: int = 1024

    # Storage and Lifetimes
    data_dir: str = "/data/ai_admin"
    confirm_ttl_seconds: int = 120
    context_ttl_seconds: int = 900
    max_bulk_items: int = 50
    test_item_id: Optional[str] = None

    # Jellyfin settings
    jellyfin_base_url: str = "http://127.0.0.1:8096"
    jellyfin_api_key: str = ""

    # Status diagnostic
    is_valid: bool = False
    validation_error: str = ""

    def __post_init__(self):
        if not self.ai_models:
            if self.ai_model and self.ai_model != "auto/best-fast":
                self.ai_models = [self.ai_model] + [m for m in DEFAULT_WORKING_MODELS if m != self.ai_model]
            else:
                self.ai_models = list(DEFAULT_WORKING_MODELS)
                if self.ai_models:
                    self.ai_model = self.ai_models[0]

    @classmethod
    def from_env(cls) -> "AIAdminConfig":
        """Load configuration from environment with fail-closed validation."""
        enabled = _str_to_bool(os.environ.get("AI_ENABLED", "false"), default=False)
        mutations_enabled = _str_to_bool(os.environ.get("AI_MUTATIONS_ENABLED", "false"), default=False)

        admin_ids = _parse_id_set(os.environ.get("AI_ADMIN_TELEGRAM_IDS", ""))
        # Also incorporate OWNER_ID if present in environment
        owner_id_env = os.environ.get("OWNER_ID", "").strip()
        if owner_id_env and owner_id_env.isdigit() and int(owner_id_env) != 0:
            admin_ids.add(int(owner_id_env))

        allowed_chats = _parse_id_set(os.environ.get("AI_ALLOWED_CHAT_IDS", ""))

        omniroute_url = (os.environ.get("OMNIROUTE_API_URL") or "").rstrip("/")
        omniroute_key = (os.environ.get("OMNIROUTE_API_KEY") or "").strip()

        model_env = os.environ.get("AI_MODELS") or os.environ.get("AI_MODEL") or os.environ.get("AI_TITLE_MODEL") or ""
        configured_models: List[str] = []
        if model_env:
            for m in re_split(r"[,\s;]+", model_env.strip()):
                if m and m != "auto/best-fast":
                    configured_models.append(m)

        ai_models: List[str] = []
        for m in configured_models:
            if m not in ai_models:
                ai_models.append(m)
        for m in DEFAULT_WORKING_MODELS:
            if m not in ai_models:
                ai_models.append(m)

        primary_model = ai_models[0] if ai_models else DEFAULT_WORKING_MODELS[0]

        try:
            max_tokens = int(os.environ.get("AI_TITLE_MAX_TOKENS", "1024"))
        except ValueError:
            max_tokens = 1024

        data_dir = os.environ.get("AI_DATA_DIR") or "/data/ai_admin"

        try:
            confirm_ttl = int(os.environ.get("AI_CONFIRM_TTL_SECONDS", "120"))
        except ValueError:
            confirm_ttl = 120

        try:
            context_ttl = int(os.environ.get("AI_CONTEXT_TTL_SECONDS", "900"))
        except ValueError:
            context_ttl = 900

        try:
            max_bulk = int(os.environ.get("AI_MAX_BULK_ITEMS", "50"))
        except ValueError:
            max_bulk = 50

        test_item = os.environ.get("AI_TEST_ITEM_ID", "").strip() or None

        jf_url = (os.environ.get("JELLYFIN_BASE_URL") or "http://127.0.0.1:8096").rstrip("/")
        jf_key = (os.environ.get("APEX_JELLYFIN_API_KEY") or os.environ.get("JELLYFIN_API_KEY") or "").strip()

        # Register secrets for scrubbing
        if omniroute_key:
            register_secret_string(omniroute_key)
        if jf_key:
            register_secret_string(jf_key)

        config = cls(
            enabled=enabled,
            mutations_enabled=mutations_enabled,
            admin_telegram_ids=admin_ids,
            allowed_chat_ids=allowed_chats,
            omniroute_api_url=omniroute_url,
            omniroute_api_key=omniroute_key,
            ai_model=primary_model,
            ai_models=ai_models,
            ai_max_tokens=max_tokens,
            data_dir=data_dir,
            confirm_ttl_seconds=confirm_ttl,
            context_ttl_seconds=context_ttl,
            max_bulk_items=max_bulk,
            test_item_id=test_item,
            jellyfin_base_url=jf_url,
            jellyfin_api_key=jf_key,
        )

        # Validate configuration
        validation_error = config._validate()
        if validation_error:
            config.is_valid = False
            config.validation_error = validation_error
            if config.enabled:
                logger.warning(f"[AI-CONFIG] Invalid configuration ({validation_error}). Disabling AI admin fail-closed.")
                config.enabled = False
        else:
            config.is_valid = True

        return config

    def _validate(self) -> str:
        """Returns error description if configuration is invalid; empty string if valid."""
        if self.enabled:
            if not self.admin_telegram_ids:
                return "AI_ADMIN_TELEGRAM_IDS is empty; deny-all active"
            if not self.omniroute_api_url and not self.omniroute_api_key:
                # LLM proxy is unconfigured
                pass
        return ""
