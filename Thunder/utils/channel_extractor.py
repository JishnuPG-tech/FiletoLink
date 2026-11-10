import asyncio
import os
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
        self._all_library_files: List[Dict[str, Any]] = []
        self._last_scan_time: Optional[datetime.datetime] = None
        self._is_scanning: bool = False
        self._lock = asyncio.Lock()

    async def scan_channel(self, client, limit: int = 1500) -> None:
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
            user_links: List[Dict[str, Any]] = []
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
                logger.debug(f"[CHANNEL-EXTRACTOR] Ping failed, determining max_id from database: {e}")
                try:
                    from Thunder.utils.database import db
                    doc = await db.files_col.find_one({}, sort=[("canonical_message_id", -1)])
                    if doc and doc.get("canonical_message_id"):
                        max_id = int(doc["canonical_message_id"]) + 50
                except Exception:
                    pass

            if max_id <= 0:
                max_id = 500  # Fallback starting probe

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
                except Exception as e:
                    logger.debug(f"[CHANNEL-EXTRACTOR] Error in message chunk: {e}")

            logger.info(f"[CHANNEL-EXTRACTOR] Read {len(media_messages)} media files, {len(user_links)} user events, discovered {len(discovered_uids)} users in BIN_CHANNEL.")

            # 3. Associate media messages with users
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

            # 4. Resolve live Telegram profiles for all discovered users
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

            # 5. Scan local disk for Jellyfin / Media STRM library if present
            self._scan_disk_library()

            self._last_scan_time = datetime.datetime.now(datetime.timezone.utc)
            logger.info(f"[CHANNEL-EXTRACTOR] Extraction complete. Mapped {len(self._user_profiles)} users and {sum(len(v) for v in self._user_files.values())} files.")

        except Exception as e:
            logger.error(f"[CHANNEL-EXTRACTOR] Scan error: {e}", exc_info=True)
        finally:
            self._is_scanning = False

    def _scan_disk_library(self) -> None:
        """Discovers all movies, series, and STRM files in persistent storage."""
        lib_dirs = ["/data/jellyfin/media", "/opt/jellyfin-local/media"]
        all_files = []
        for base in lib_dirs:
            if not os.path.exists(base):
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    if f.endswith((".strm", ".mkv", ".mp4", ".avi")):
                        f_name = os.path.splitext(f)[0] if f.endswith(".strm") else f
                        p_hash = ""
                        # If it's a strm file, read the public_hash from the URL
                        if f.endswith(".strm"):
                            try:
                                with open(os.path.join(root, f), "r", encoding="utf-8") as s_file:
                                    s_content = s_file.read().strip()
                                    m_hash = re.search(r'/(?:download|stream|watch)/([a-zA-Z0-9_-]+)', s_content)
                                    if m_hash:
                                        p_hash = m_hash.group(1)
                            except Exception:
                                pass

                        m_type = "tv" if "TV Shows" in root or "Season" in root else "movie"
                        all_files.append({
                            "file_name": f_name,
                            "file_size": "Direct Stream",
                            "media_type": m_type,
                            "converted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "public_hash": p_hash
                        })
        if all_files:
            self._all_library_files = all_files
            logger.info(f"[CHANNEL-EXTRACTOR] Discovered {len(all_files)} library media items on disk.")

    def get_extracted_users(self) -> List[Dict[str, Any]]:
        return list(self._user_profiles.values())

    def get_extracted_user_files(self, user_id: int) -> List[Dict[str, Any]]:
        return self._user_files.get(user_id, [])

    def get_all_library_files(self) -> List[Dict[str, Any]]:
        return self._all_library_files

    def should_rescan(self) -> bool:
        if self._last_scan_time is None:
            return True
        diff = datetime.datetime.now(datetime.timezone.utc) - self._last_scan_time
        return diff.total_seconds() > 180  # Rescan every 3 minutes

channel_extractor = TelegramChannelExtractor()
