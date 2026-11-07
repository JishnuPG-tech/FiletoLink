# Thunder/utils/force_channel.py

import asyncio

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from Thunder.utils.logger import logger
from Thunder.utils.messages import MSG_COMMUNITY_CHANNEL
from Thunder.vars import Var

_force_link = None
_force_title = None

async def get_force_info(bot: Client):
    global _force_link, _force_title
    
    if not Var.FORCE_CHANNEL_ID:
        return None, None
    
    if _force_link is not None and _force_title is not None:
        return _force_link, _force_title
    
    try:
        try:
            chat = await bot.get_chat(Var.FORCE_CHANNEL_ID)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            chat = await bot.get_chat(Var.FORCE_CHANNEL_ID)
        if chat:
            _force_link = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else None)
            _force_title = chat.title or "Channel"
        return _force_link, _force_title
    except Exception as e:
        logger.error(f"Force channel error: {e}", exc_info=True)
        return None, None

async def force_channel_check(client: Client, message: Message):
    if not Var.FORCE_CHANNEL_ID:
        return True
    
    if message.from_user is None or message.from_user.id == Var.OWNER_ID:
        return True

    user_id = message.from_user.id

    try:
        while True:
            try:
                member = await client.get_chat_member(Var.FORCE_CHANNEL_ID, user_id)
                if member is None:
                    logger.error(f"Failed to get chat member for {user_id} in force channel {Var.FORCE_CHANNEL_ID}")
                    raise UserNotParticipant()
                
                # Strict check: If user left, was kicked, or is banned
                if getattr(member, "status", None) in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                    raise UserNotParticipant()
                    
                return True
            except FloodWait as e:
                logger.debug(f"FloodWait in force_channel_check, sleeping for {e.value}s")
                await asyncio.sleep(e.value)
    except UserNotParticipant:
        link, title = await get_force_info(client)
        channel_name = title or "our Updates Channel"
        
        buttons = []
        if link:
            buttons.append([InlineKeyboardButton(f"📢 Join {channel_name}", url=link)])
        buttons.append([InlineKeyboardButton("🔄 Joined! Check Again", callback_data=f"chk_fsub_{user_id}")])
        
        text = (
            f"⚠️ **Access Restricted!**\n\n"
            f"You must be an active subscriber of **{channel_name}** to use this bot.\n\n"
            f"👉 **Step 1:** Tap the button below to join our channel.\n"
            f"👉 **Step 2:** Tap **'Joined! Check Again'** to continue.\n\n"
            f"*(ℹ️ Note: If you leave the channel, your access is immediately revoked.)*"
        )
        
        try:
            await message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
        return False
    except Exception as e:
        logger.error(f"Error checking force channel: {e}", exc_info=True)
        try:
            await message.reply_text("An unexpected error occurred while checking channel membership. Please try again.")
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text("An unexpected error occurred while checking channel membership. Please try again.")
        return False
