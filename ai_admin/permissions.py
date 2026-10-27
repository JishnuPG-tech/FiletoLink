"""Authorization and permission enforcement for AI Admin."""

import logging
from typing import Optional, Tuple
from ai_admin.config import AIAdminConfig

logger = logging.getLogger("AIAdmin.Permissions")


class PermissionChecker:
    def __init__(self, config: AIAdminConfig):
        self.config = config

    def check_authorization(
        self,
        user_id: Optional[int],
        chat_id: Optional[int],
        is_channel: bool = False,
        is_anonymous_admin: bool = False,
    ) -> Tuple[bool, str]:
        """Authorize a request. Fails closed on any unexpected state or error.

        Returns (is_authorized, refusal_reason).
        """
        try:
            # 1. Master Kill Switch
            if not self.config.enabled:
                return False, "AI administration is currently disabled."

            # 2. Reject Channels and Anonymous Admins immediately
            if is_channel or is_anonymous_admin:
                logger.info(f"[AUTH] Rejected non-user update (channel={is_channel}, anon={is_anonymous_admin})")
                return False, "Access denied: channel posts and anonymous admins are not supported."

            if user_id is None or user_id <= 0:
                logger.info("[AUTH] Rejected update without verifiable user ID.")
                return False, "Access denied: invalid sender identity."

            if chat_id is None:
                return False, "Access denied: invalid chat identity."

            # 3. User Admin Verification (Fail closed if empty admin list)
            if not self.config.admin_telegram_ids:
                logger.warning("[AUTH] Deny-all: No admin IDs configured in AI_ADMIN_TELEGRAM_IDS.")
                return False, "Access denied: no administrators configured."

            if user_id not in self.config.admin_telegram_ids:
                logger.info(f"[AUTH] User {user_id} is not in admin allowlist.")
                return False, "Access denied: unauthorized user."

            # 4. Chat Allowlist Verification
            is_private_chat = (user_id == chat_id)
            if self.config.allowed_chat_ids:
                # If explicit chat allowlist is defined, chat_id must be in it
                if chat_id not in self.config.allowed_chat_ids:
                    logger.info(f"[AUTH] Chat {chat_id} is not in AI_ALLOWED_CHAT_IDS.")
                    return False, "Access denied: commands not permitted in this chat."
            else:
                # Default policy: private chats of admins only
                if not is_private_chat:
                    logger.info(f"[AUTH] Non-private chat {chat_id} rejected under default private-only policy.")
                    return False, "Access denied: /ai is restricted to private admin chats."

            return True, "authorized"

        except Exception as e:
            logger.error(f"[AUTH] Exception in authorization check: {e}", exc_info=True)
            # Fail closed on any exception
            return False, "Access denied due to an internal security verification error."

    def check_mutation_allowed(self) -> Tuple[bool, str]:
        """Verify whether write/mutation operations are currently allowed."""
        if not self.config.enabled:
            return False, "AI administration is disabled."
        if not self.config.mutations_enabled:
            return False, "Mutations are disabled (read-only mode active)."
        return True, "mutations_allowed"
