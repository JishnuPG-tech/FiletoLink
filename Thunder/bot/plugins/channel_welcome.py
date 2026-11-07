# Thunder/bot/plugins/channel_welcome.py
"""Channel Welcome Plugin: Automatically greets new users in the channel with id/username."""

import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated

from Thunder.bot import StreamBot
from Thunder.utils.logger import logger
from Thunder.vars import Var


@StreamBot.on_chat_member_updated()
async def on_channel_member_updated(client: Client, update: ChatMemberUpdated):
    if not Var.WELCOME_CHANNEL_ENABLED:
        return

    target_channel = Var.FORCE_CHANNEL_ID or Var.BIN_CHANNEL
    if not target_channel or update.chat.id != target_channel:
        return

    # Check if a new member joined
    old_status = getattr(update.old_chat_member, "status", None) if update.old_chat_member else None
    new_status = getattr(update.new_chat_member, "status", None) if update.new_chat_member else None

    is_new_join = (
        (old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, None) or old_status is None)
        and new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED)
    )

    if not is_new_join:
        return

    user = update.new_chat_member.user
    if not user or user.is_bot:
        return

    try:
        user_name = user.first_name or "User"
        user_mention = f"[{user_name}](tg://user?id={user.id})"
        username_str = f" (@{user.username})" if user.username else ""
        
        me = await client.get_me()
        bot_username = me.username or Var.NAME

        welcome_text = (
            f"👋 Welcome {user_mention}{username_str} (`{user.id}`) to the channel! ⚡\n"
            f"Access fast streaming & direct links on @{bot_username}"
        )

        sent_msg = await client.send_message(
            chat_id=target_channel,
            text=welcome_text,
            disable_web_page_preview=True
        )

        if Var.WELCOME_AUTO_DELETE_SECONDS > 0:
            await asyncio.sleep(Var.WELCOME_AUTO_DELETE_SECONDS)
            try:
                await sent_msg.delete()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error in on_channel_member_updated welcome: {e}", exc_info=True)
