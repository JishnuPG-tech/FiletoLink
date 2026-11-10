import asyncio
import re
import datetime
from typing import Dict, Any, List, Optional, Set
from Thunder.vars import Var
from Thunder.utils.logger import logger
from Thunder.utils.human_readable import humanbytes

class TelegramChannelExtractor:
    def __init__(self):
        self._user_files: Dict[int, List[Dict[str, Any]]] = {}
        self._user_profiles: Dict[int, Dict[str, Any]] = {}
        self._last_scan_time: Optional[datetime.datetime] = None
        self._is_scanning: bool = False
        self._lock = asyncio.Lock()

    async def scan_channel(self, client, limit: int = 2500) -> None:
        """Extracts all user requests, movies, series, and user profiles directly from BIN_CHANNEL."""
        if not client or not getattr(client, "is_connected", False) or not Var.BIN_CHANNEL:
            return

        async with self._lock:
            if self._is_scanning:
                return
            self._is_scanning = True

        try:
            logger.info(f"[CHANNEL-EXTRACTOR] Starting scan of BIN_CHANNEL ({Var.BIN_CHANNEL}) with limit {limit}...")
            media_messages: Dict[int, Dict[str, Any]] = {}
            user_links: List[Dict[str, Any]] = []
            discovered_uids: Set[int] = set()

            async for msg in client.get_chat_history(chat_id=int(Var.BIN_CHANNEL), limit=limit):
                if not msg:
                    continue

                # 1. Capture media message (movie, series, document, video, audio)
                media = msg.document or msg.video or msg.audio
                if media:
                    f_name = getattr(media, "file_name", None) or "Unnamed Media"
                    f_size = getattr(media, "file_size", 0) or 0
                    m_type = "movie"
                    if msg.video:
                        m_type = "video"
                    elif msg.audio:
                        m_type = "audio"

                    media_messages[msg.id] = {
                        "message_id": msg.id,
                        "file_name": f_name,
                        "file_size": humanbytes(f_size) if f_size > 0 else "Unknown Size",
                        "media_type": m_type,
                        "date": msg.date.isoformat() if hasattr(msg, "date") and msg.date else "",
                        "raw_date": msg.date if hasattr(msg, "date") else None,
                        "public_hash": ""
                    }

                # 2. Capture attribution message (MSG_NEW_FILE_REQUEST or MSG_NEW_USER)
                text = msg.text or msg.caption or ""
                if text:
                    m_id = re.search(r'(?:User\s*)?ID:\*?\*?\s*[`\[]?(\d+)', text, re.IGNORECASE)
                    m_src = re.search(r'(?:Source|Name):\*?\*?\s*\[(.*?)\]', text, re.IGNORECASE)
                    m_hash = re.search(r'/(?:download|stream|watch)/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)

                    uid = int(m_id.group(1)) if m_id else None
                    src_name = m_src.group(1).strip() if m_src else ""
                    p_hash = m_hash.group(1) if m_hash else ""
                    reply_id = getattr(msg, "reply_to_message_id", None)

                    if uid and uid > 0:
                        discovered_uids.add(uid)
                        if uid not in self._user_profiles:
                            self._user_profiles[uid] = {
                                "id": uid,
                                "name": src_name or f"User {uid}",
                                "username": "",
                                "total_files": 0,
                                "join_date": msg.date.isoformat() if hasattr(msg, "date") and msg.date else "",
                                "last_active": msg.date.isoformat() if hasattr(msg, "date") and msg.date else ""
                            }
                        elif src_name and (self._user_profiles[uid]["name"].startswith("User ") or not self._user_profiles[uid]["name"]):
                            self._user_profiles[uid]["name"] = src_name

                        user_links.append({
                            "user_id": uid,
                            "user_name": src_name,
                            "public_hash": p_hash,
                            "reply_to_message_id": reply_id,
                            "message_id": msg.id,
                            "date": getattr(msg, "date", None)
                        })

            logger.info(f"[CHANNEL-EXTRACTOR] Scanned {len(media_messages)} media files and {len(user_links)} user events. Found {len(discovered_uids)} users in BIN_CHANNEL.")

            # 3. Associate media messages with requesting user
            paired_media_ids: Set[int] = set()
            for link in user_links:
                uid = link["user_id"]
                rep_id = link["reply_to_message_id"]
                p_hash = link["public_hash"]

                target_media = None
                if rep_id and rep_id in media_messages:
                    target_media = media_messages[rep_id]
                    paired_media_ids.add(rep_id)
                elif (link["message_id"] - 1) in media_messages and (link["message_id"] - 1) not in paired_media_ids:
                    target_media = media_messages[link["message_id"] - 1]
                    paired_media_ids.add(link["message_id"] - 1)

                if target_media:
                    f_entry = {
                        "file_name": target_media["file_name"],
                        "file_size": target_media["file_size"],
                        "media_type": target_media["media_type"],
                        "converted_at": target_media["date"] or (link["date"].isoformat() if link["date"] else ""),
                        "public_hash": p_hash or target_media.get("public_hash", "")
                    }
                    if uid not in self._user_files:
                        self._user_files[uid] = []
                    if not any(x["file_name"] == f_entry["file_name"] for x in self._user_files[uid]):
                        self._user_files[uid].append(f_entry)

            # 4. Resolve exact Telegram profiles for all discovered users
            for uid in discovered_uids:
                prof = self._user_profiles.get(uid, {"id": uid, "name": f"User {uid}", "username": ""})
                if not prof.get("username") or prof.get("name", "").startswith("User "):
                    try:
                        tg_user = await client.get_users(uid)
                        if tg_user:
                            first = getattr(tg_user, "first_name", "") or ""
                            last = getattr(tg_user, "last_name", "") or ""
                            uname = getattr(tg_user, "username", "") or ""
                            full = f"{first} {last}".strip()
                            if not full and uname:
                                full = f"@{uname}"
                            elif not full:
                                full = prof["name"]

                            prof["name"] = full
                            prof["username"] = uname
                            self._user_profiles[uid] = prof
                    except Exception as e:
                        logger.debug(f"[CHANNEL-EXTRACTOR] Telegram lookup for {uid}: {e}")

                prof["total_files"] = len(self._user_files.get(uid, []))
                self._user_profiles[uid] = prof

            self._last_scan_time = datetime.datetime.now(datetime.timezone.utc)
            logger.info(f"[CHANNEL-EXTRACTOR] Successfully mapped {len(self._user_profiles)} users from BIN_CHANNEL.")

        except Exception as e:
            logger.error(f"[CHANNEL-EXTRACTOR] Error scanning BIN_CHANNEL: {e}", exc_info=True)
        finally:
            self._is_scanning = False

    def get_extracted_users(self) -> List[Dict[str, Any]]:
        return list(self._user_profiles.values())

    def get_extracted_user_files(self, user_id: int) -> List[Dict[str, Any]]:
        return self._user_files.get(user_id, [])

    def should_rescan(self) -> bool:
        if self._last_scan_time is None:
            return True
        diff = datetime.datetime.now(datetime.timezone.utc) - self._last_scan_time
        return diff.total_seconds() > 120  # Rescan every 2 minutes

channel_extractor = TelegramChannelExtractor()
