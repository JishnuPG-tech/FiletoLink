"""Stage 4A Telegram Router for AI Administrator.

Registers isolated, private-admin Telegram handlers for /ai commands
and ai:* callback queries in Pyrogram group -1.
Ensures zero collisions with existing bot plugins (group 0 catch-all),
strict authorization, HTML escaping, and length capping <= 4000 chars.
"""

import html
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from pyrogram import Client, StopPropagation, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ai_admin.config import AIAdminConfig
from ai_admin.handler import AIAdminHandler
from ai_admin.permissions import PermissionChecker

logger = logging.getLogger("AIAdmin.TelegramRouter")

MAX_TELEGRAM_MESSAGE_LENGTH = 4000


def is_private_chat(chat_obj: Any) -> bool:
    """Verify whether a chat object represents a private 1-on-1 chat."""
    if not chat_obj:
        return False
    c_type = getattr(chat_obj, "type", None)
    if c_type is None:
        return False
    val = getattr(c_type, "value", c_type)
    return str(val).lower() == "private"


def is_forwarded(message: Any) -> bool:
    """Detect whether a message was forwarded."""
    if not message:
        return False
    return bool(
        getattr(message, "forward_date", None)
        or getattr(message, "forward_from", None)
        or getattr(message, "forward_from_chat", None)
        or getattr(message, "forward_sender_name", None)
    )


def safe_format_html(text: str, max_chars: int = MAX_TELEGRAM_MESSAGE_LENGTH) -> str:
    """Format text into safe Telegram HTML with dynamic escaping and length capping.
    
    Protects against tag injection from untrusted media titles or provider data.
    """
    if not text:
        return ""

    # Parse fenced code blocks first: ```json ... ```
    code_block_pattern = re.compile(r"```(?:[a-zA-Z0-9_\-]+)?\n?(.*?)```", re.DOTALL)
    parts = []
    last_idx = 0

    for m in code_block_pattern.finditer(text):
        # Text before code block
        pre_text = text[last_idx:m.start()]
        if pre_text:
            parts.append(_format_inline_markdown_to_html(pre_text))
        
        # Code block contents: strictly escape HTML
        code_content = html.escape(m.group(1), quote=True)
        parts.append(f"<pre><code>{code_content}</code></pre>")
        last_idx = m.end()

    # Trailing text after last code block
    if last_idx < len(text):
        parts.append(_format_inline_markdown_to_html(text[last_idx:]))

    rendered = "".join(parts)

    # Cap length strictly <= max_chars
    if len(rendered) > max_chars:
        suffix = "\n\n<i>... [Response truncated to stay within message limit]</i>"
        reserve = len(suffix) + 30
        allowed_len = max(20, max_chars - reserve)
        
        while allowed_len > 0:
            truncated = rendered[:allowed_len]
            balanced = _balance_html_tags(truncated)
            candidate = balanced + suffix
            if len(candidate) <= max_chars:
                rendered = candidate
                break
            allowed_len -= 5
        else:
            # Fallback if max_chars is extremely small
            rendered = suffix[:max_chars]

    return rendered


def _format_inline_markdown_to_html(raw: str) -> str:
    """Escape raw text and convert basic inline markdown (*bold*, `code`) safely."""
    # First, escape all HTML entities so raw untrusted input cannot inject tags
    escaped = html.escape(raw, quote=True)

    # Convert `inline code`
    escaped = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", escaped)

    # Convert *bold* (avoiding double asterisks or edge cases)
    escaped = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", escaped)

    return escaped


def _balance_html_tags(text: str) -> str:
    """Close any unclosed standard tags (<pre>, <code>, <b>, <i>) and strip partial tags."""
    if not text:
        return ""

    # Strip any trailing incomplete tag (e.g. "something <pr" or "something </")
    last_lt = text.rfind("<")
    last_gt = text.rfind(">")
    if last_lt > last_gt:
        text = text[:last_lt]

    # Strip any trailing incomplete HTML entity (e.g. "something &qu")
    last_amp = text.rfind("&")
    last_semi = text.rfind(";")
    if last_amp > last_semi and last_amp >= len(text) - 10:
        text = text[:last_amp]

    open_tags = []
    tag_regex = re.compile(r"<\s*(/)?\s*(b|i|code|pre)\s*>", re.IGNORECASE)
    
    for match in tag_regex.finditer(text):
        is_closing = bool(match.group(1))
        tag_name = match.group(2).lower()
        if is_closing:
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
        else:
            open_tags.append(tag_name)

    # Append closing tags in reverse order
    closers = "".join(f"</{t}>" for t in reversed(open_tags))
    return text + closers


class TelegramAIAdminRouter:
    """Pyrogram handler router for AI Admin operations."""

    def __init__(
        self,
        config: AIAdminConfig,
        permissions: PermissionChecker,
        handler: AIAdminHandler,
    ):
        self.config = config
        self.permissions = permissions
        self.handler = handler
        self._registered_handlers: List[Tuple[Any, int]] = []

    def register_handlers(self, client: Client, group: int = -1) -> None:
        """Register /ai command and ai:* callback query handlers in group -1."""
        cmd_h = MessageHandler(self.handle_ai_command, filters=filters.command(["ai"]))
        cb_h = CallbackQueryHandler(self.handle_callback_query, filters=filters.regex(r"^ai:"))

        client.add_handler(cmd_h, group=group)
        client.add_handler(cb_h, group=group)

        self._registered_handlers.append((cmd_h, group))
        self._registered_handlers.append((cb_h, group))
        logger.info(f"Registered AI Admin handlers in Pyrogram group={group}")

    def unregister_handlers(self, client: Client) -> None:
        """Remove previously registered handlers from client."""
        for h, grp in self._registered_handlers:
            try:
                client.remove_handler(h, group=grp)
            except Exception as e:
                logger.debug(f"Error removing handler {h} from group {grp}: {e}")
        self._registered_handlers.clear()

    async def handle_ai_command(self, client: Client, message: Message) -> None:
        """Handle incoming /ai commands in group -1."""
        try:
            # 1. Config enabled check
            if not self.config.enabled:
                if is_private_chat(getattr(message, "chat", None)):
                    await message.reply_text(
                        "⚠️ <b>AI Administrator is currently disabled.</b>",
                        parse_mode=ParseMode.HTML,
                    )
                raise StopPropagation

            # 2. Config validity check
            if not self.config.is_valid or not self.config.admin_telegram_ids:
                if is_private_chat(getattr(message, "chat", None)):
                    await message.reply_text(
                        "⚠️ <b>AI Administrator configuration is invalid or missing admin IDs.</b>",
                        parse_mode=ParseMode.HTML,
                    )
                raise StopPropagation

            # 3. Private chat constraint: reject group, channel, supergroup
            if not is_private_chat(getattr(message, "chat", None)):
                logger.warning(
                    f"Rejected /ai command from non-private chat id={getattr(message.chat, 'id', None)} "
                    f"type={getattr(message.chat, 'type', None)}"
                )
                raise StopPropagation

            # 4. Reject forwarded commands
            if is_forwarded(message):
                logger.warning(
                    f"Rejected forwarded /ai command from user={getattr(message.from_user, 'id', None)}"
                )
                await message.reply_text(
                    "⚠️ <b>Forwarded commands are rejected for security.</b>",
                    parse_mode=ParseMode.HTML,
                )
                raise StopPropagation

            # 5. Authorization check
            user_id = message.from_user.id if message.from_user else None
            chat_id = message.chat.id if message.chat else None
            auth_ok, reason = self.permissions.check_authorization(
                user_id=user_id,
                chat_id=chat_id,
                is_channel=False,
                is_anonymous_admin=False,
            )
            if not auth_ok:
                logger.warning(f"Unauthorized /ai attempt by user={user_id} in chat={chat_id}: {reason}")
                await message.reply_text(
                    "⛔ <b>Access Denied:</b> You are not authorized to use the AI Administrator.",
                    parse_mode=ParseMode.HTML,
                )
                raise StopPropagation

            # 6. Parse command instruction
            raw_text = getattr(message, "text", "") or ""
            # Strip '/ai' or '/ai@BotUsername'
            parts = raw_text.split(maxsplit=1)
            instruction = parts[1].strip() if len(parts) > 1 else ""

            # 7. Execute via isolated AIAdminHandler
            handled, response = await self.handler.handle_message(
                user_id=user_id,
                chat_id=chat_id,
                text=instruction,
                is_channel=False,
                is_anonymous_admin=False,
            )

            # 8. Format safely and send
            formatted_html = safe_format_html(response)
            
            # Optional quick action buttons for status / help
            reply_markup = None
            if not instruction or instruction.lower() in ("help", "status"):
                reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⚙️ Status", callback_data="ai:status"),
                        InlineKeyboardButton("❓ Help", callback_data="ai:help"),
                    ]
                ])

            # 8. Format safely and send with fallback
            await self._send_safe_reply(message, response, reply_markup=reply_markup)
            raise StopPropagation

        except StopPropagation:
            raise
        except Exception as e:
            logger.error(f"Error handling /ai command: {e}", exc_info=True)
            raise StopPropagation

    async def _send_safe_reply(self, target_msg: Message, text: str, reply_markup: Optional[Any] = None) -> None:
        """Send message in HTML mode, falling back safely to plain text if parsing fails."""
        formatted_html = safe_format_html(text)
        try:
            await target_msg.reply_text(
                formatted_html,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.warning(f"HTML reply failed ({e}), falling back to plain text")
            clean_plain = (text or "")[:MAX_TELEGRAM_MESSAGE_LENGTH]
            await target_msg.reply_text(
                clean_plain,
                parse_mode=None,
                reply_markup=reply_markup,
            )

    async def handle_callback_query(self, client: Client, callback_query: CallbackQuery) -> None:
        """Handle incoming ai:* callback queries in group -1."""
        try:
            # 1. Config checks
            if not self.config.enabled or not self.config.is_valid:
                await callback_query.answer("AI Administrator is disabled or unconfigured.", show_alert=True)
                raise StopPropagation

            # 2. Private chat check
            msg = getattr(callback_query, "message", None)
            if msg and not is_private_chat(getattr(msg, "chat", None)):
                await callback_query.answer("AI Admin actions are restricted to private chats.", show_alert=True)
                raise StopPropagation

            # 3. Authorization check
            user_id = callback_query.from_user.id if callback_query.from_user else None
            chat_id = msg.chat.id if msg and msg.chat else user_id
            auth_ok, reason = self.permissions.check_authorization(
                user_id=user_id,
                chat_id=chat_id,
                is_channel=False,
                is_anonymous_admin=False,
            )
            if not auth_ok:
                await callback_query.answer("⛔ Access denied: unauthorized administrator.", show_alert=True)
                raise StopPropagation

            # 4. Dispatch callback action
            data = getattr(callback_query, "data", "") or ""
            action = data[3:] if data.startswith("ai:") else data

            if action == "status":
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text="status",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action == "help":
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text="",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action.startswith("item:"):
                item_id = action.split(":", 1)[1]
                handled, response = await self.handler.handle_message(
                    user_id=user_id,
                    chat_id=chat_id,
                    text=f"details {item_id}",
                )
                await callback_query.answer()
                if msg:
                    await self._send_safe_reply(msg, response)

            elif action == "cancel":
                await callback_query.answer("Operation cancelled.")
                if msg:
                    try:
                        await msg.delete()
                    except Exception:
                        pass
            else:
                await callback_query.answer(f"Unknown action: {action[:20]}", show_alert=True)

            raise StopPropagation

        except StopPropagation:
            raise
        except Exception as e:
            logger.error(f"Error handling callback query: {e}", exc_info=True)
            raise StopPropagation
