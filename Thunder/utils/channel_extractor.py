import asyncio
import os
import re
import datetime
from urllib.parse import unquote
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

    def register_live_user(self, user_id: int, name: str, username: str = "") -> None:
        """Immediately registers a user in memory when they start or interact with the bot."""
        clean_uname = username.lstrip("@").strip() if username else ""
        disp_name = f"@{clean_uname}" if clean_uname else (name.strip() if name and name.strip() else f"User {user_id}")
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = {
                "id": user_id,
                "name": disp_name,
                "username": clean_uname,
                "total_files": len(self._user_files.get(user_id, [])),
                "join_date": now_iso,
                "last_active": now_iso
            }
        else:
            if clean_uname:
                self._user_profiles[user_id]["username"] = clean_uname
            if disp_name and not disp_name.startswith("User "):
                self._user_profiles[user_id]["name"] = disp_name
            self._user_profiles[user_id]["last_active"] = now_iso

    def register_live_conversion(
        self,
        user_id: int,
        user_name: str,
        username: str,
        file_name: str,
        file_size: str,
        public_hash: str
    ) -> None:
        """Immediately registers a converted movie/series in memory as soon as the bot converts it."""
        self.register_live_user(user_id, user_name, username)
        if not file_name:
            return

        if user_id not in self._user_files:
            self._user_files[user_id] = []

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        m_type = "movie"
        upper = file_name.upper()
        if any(x in upper for x in ["S0", "E0", "EPISODE", "SEASON"]):
            m_type = "series"

        f_entry = {
            "file_name": file_name,
            "file_size": file_size or "Unknown Size",
            "media_type": m_type,
            "converted_at": now_iso,
            "public_hash": public_hash or ""
        }

        # Deduplicate
        existing_idx = next((i for i, x in enumerate(self._user_files[user_id]) if x["file_name"] == file_name), -1)
        if existing_idx >= 0:
            self._user_files[user_id][existing_idx] = f_entry
        else:
            self._user_files[user_id].insert(0, f_entry)

        if user_id in self._user_profiles:
            self._user_profiles[user_id]["total_files"] = len(self._user_files[user_id])

    async def scan_channel(self, client, limit: int = 2500) -> None:
        """Extracts all user requests, movies, series, and user profiles directly from BIN_CHANNEL using get_messages."""
        if not client or not getattr(client, "is_connected", False) or not Var.BIN_CHANNEL:
            return

        async with self._lock:
            if self._is_scanning:
                return
            self._is_scanning = True

        try:
            logger.info(f"[CHANNEL-EXTRACTOR] Starting chunked ID scan of BIN_CHANNEL ({Var.BIN_CHANNEL}) with limit {limit}...")
            media_messages: Dict[int, Dict[str, Any]] = {}
            raw_text_events: List[Dict[str, Any]] = []
            discovered_uids: Set[int] = set()

            # 1. Determine max_id in BIN_CHANNEL
            max_id = 0
            try:
                marker = await client.send_message(chat_id=int(Var.BIN_CHANNEL), text=".")
                max_id = marker.id
                try:
                    await marker.delete()
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"[CHANNEL-EXTRACTOR] Ping failed, checking DB canonical_message_id: {e}")
                try:
                    from Thunder.utils.database import db
                    doc = await db.files_col.find_one({}, sort=[("canonical_message_id", -1)])
                    if doc and doc.get("canonical_message_id"):
                        max_id = int(doc["canonical_message_id"]) + 50
                except Exception:
                    pass

            if max_id <= 0:
                max_id = 1500

            start_id = max(1, max_id - limit)
            chunk_size = 100
            current_id = max_id

            logger.info(f"[CHANNEL-EXTRACTOR] Scanning message range {start_id} to {max_id} in {Var.BIN_CHANNEL}...")

            # 2. Fetch messages in chunks of 100 via channels.GetMessages (compatible with bots)
            while current_id >= start_id:
                batch_start = max(start_id, current_id - chunk_size + 1)
                batch_ids = list(range(batch_start, current_id + 1))
                current_id = batch_start - 1

                try:
                    batch_msgs = await client.get_messages(chat_id=int(Var.BIN_CHANNEL), message_ids=batch_ids)
                    if not batch_msgs:
                        continue
                    if not isinstance(batch_msgs, list):
                        batch_msgs = [batch_msgs]

                    for msg in batch_msgs:
                        if not msg or getattr(msg, "empty", False):
                            continue

                        # Case A: Media message (movie, series, document, video, audio)
                        media = msg.document or msg.video or msg.audio
                        if media:
                            f_name = getattr(media, "file_name", None)
                            if not f_name:
                                from Thunder.utils.file_properties import get_name
                                f_name = get_name(msg) or "Unnamed Media"

                            f_size = getattr(media, "file_size", 0) or 0
                            m_type = "movie"
                            if msg.video:
                                m_type = "video"
                            elif msg.audio:
                                m_type = "audio"

                            f_entry = {
                                "message_id": msg.id,
                                "file_name": f_name,
                                "file_size": humanbytes(f_size) if f_size > 0 else "Unknown Size",
                                "media_type": m_type,
                                "date": msg.date.isoformat() if hasattr(msg, "date") and msg.date else "",
                                "raw_date": getattr(msg, "date", None),
                                "public_hash": ""
                            }
                            media_messages[msg.id] = f_entry

                        # Case B: Text message (user log / download link attribution)
                        text = msg.text or msg.caption or ""
                        if text:
                            m_id = re.search(r'(?:User\s*)?ID:\*?\*?\s*[`\[]?(\d+)', text, re.IGNORECASE)
                            m_src = re.search(r'(?:Source|Name):\*?\*?\s*\[(.*?)\]', text, re.IGNORECASE)
                            
                            # Extract public hash and explicit filename from link:
                            # Handles:
                            # /watch/f/<hash>/<filename>
                            # /f/<hash>/<filename>
                            # /watch/<hash>/<filename>
                            # /<hash>/<filename>
                            url_fname = ""
                            p_hash = ""

                            m_link = re.search(r'https?://[^\s`"\'<>]*/(?:watch/)?(?:f/)?([a-zA-Z0-9_-]{8,})/?([^\s\?`"\'<>]*)', text)
                            if m_link:
                                raw_h = m_link.group(1)
                                if raw_h.lower() not in ("watch", "download", "stream", "file"):
                                    p_hash = raw_h
                                if m_link.group(2):
                                    dec_name = unquote(m_link.group(2)).strip()
                                    if "." in dec_name:
                                        url_fname = dec_name

                            # Fallback: check for explicit File: or Name: in text
                            if not url_fname:
                                m_ftext = re.search(r'(?:File|Name):\*?\*?\s*[`]?([^`\n\r]+)[`]?', text, re.IGNORECASE)
                                if m_ftext:
                                    cand = m_ftext.group(1).strip()
                                    if "." in cand:
                                        url_fname = cand

                            reply_id = getattr(msg, "reply_to_message_id", None)

                            uid = int(m_id.group(1)) if m_id else None
                            src_name = m_src.group(1).strip() if m_src else ""

                            if uid and uid > 0:
                                discovered_uids.add(uid)
                                self.register_live_user(uid, src_name)

                                raw_text_events.append({
                                    "user_id": uid,
                                    "user_name": src_name,
                                    "file_name": url_fname,
                                    "public_hash": p_hash,
                                    "reply_to_message_id": reply_id,
                                    "message_id": msg.id,
                                    "date": getattr(msg, "date", None)
                                })
                except Exception as e:
                    logger.debug(f"[CHANNEL-EXTRACTOR] Error in message chunk: {e}")

            logger.info(f"[CHANNEL-EXTRACTOR] Read {len(media_messages)} media files, {len(raw_text_events)} user events. Found {len(discovered_uids)} users in BIN_CHANNEL.")

            # 3. Associate media files with requesting users
            for event in raw_text_events:
                uid = event["user_id"]
                rep_id = event["reply_to_message_id"]
                url_fname = event["file_name"]
                p_hash = event["public_hash"]
                msg_id = event["message_id"]

                # Find associated media
                target_media = None
                if rep_id and rep_id in media_messages:
                    target_media = media_messages[rep_id]
                else:
                    # Check adjacent messages (offsets: -1, -2, -3, -4, -5, +1, +2)
                    for offset in [-1, -2, -3, -4, -5, 1, 2]:
                        cand = media_messages.get(msg_id + offset)
                        if cand:
                            target_media = cand
                            break

                resolved_name = ""
                resolved_size = "Unknown Size"
                resolved_type = "movie"
                resolved_date = event["date"].isoformat() if event["date"] else datetime.datetime.now(datetime.timezone.utc).isoformat()

                if target_media:
                    t_name = target_media["file_name"]
                    if url_fname and (not t_name or t_name in ("Unnamed Media", "video", "document", "file")):
                        resolved_name = url_fname
                    else:
                        resolved_name = t_name or url_fname
                    resolved_size = target_media["file_size"]
                    resolved_type = target_media["media_type"]
                    resolved_date = target_media["date"] or resolved_date
                elif url_fname:
                    resolved_name = url_fname

                if resolved_name and resolved_name != "Unnamed Media":
                    if uid not in self._user_files:
                        self._user_files[uid] = []

                    f_entry = {
                        "file_name": resolved_name,
                        "file_size": resolved_size,
                        "media_type": resolved_type,
                        "converted_at": resolved_date,
                        "public_hash": p_hash
                    }

                    # Deduplicate by clean file name
                    clean_res = re.sub(r'[^a-zA-Z0-9]+', ' ', resolved_name).strip().lower()
                    if not any(re.sub(r'[^a-zA-Z0-9]+', ' ', x["file_name"]).strip().lower() == clean_res for x in self._user_files[uid]):
                        self._user_files[uid].append(f_entry)

            # 4. Resolve exact Telegram handles (@username and real name) for all users
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
                            disp = f"@{uname}" if uname else (full or prof["name"])

                            prof["name"] = disp
                            prof["username"] = uname
                            self._user_profiles[uid] = prof
                    except Exception as e:
                        logger.debug(f"[CHANNEL-EXTRACTOR] Telegram lookup for {uid}: {e}")

                prof["total_files"] = len(self._user_files.get(uid, []))
                self._user_profiles[uid] = prof

            self._last_scan_time = datetime.datetime.now(datetime.timezone.utc)
            logger.info(f"[CHANNEL-EXTRACTOR] Mapped {len(self._user_profiles)} users and {sum(len(v) for v in self._user_files.values())} files directly from BIN_CHANNEL.")

        except Exception as e:
            logger.error(f"[CHANNEL-EXTRACTOR] Scan error: {e}", exc_info=True)
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
        return diff.total_seconds() > 180

channel_extractor = TelegramChannelExtractor()
