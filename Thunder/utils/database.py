import secrets
# Thunder/utils/database.py

import datetime
from typing import Any, Dict, Optional
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError
from Thunder.vars import Var
from Thunder.utils.logger import logger

class Database:
    def __init__(self, uri: str, database_name: str, *args, **kwargs):
        self._client = AsyncMongoClient(uri, *args, **kwargs)
        self.db = self._client[database_name]
        self.col: AsyncCollection = self.db.users
        self.banned_users_col: AsyncCollection = self.db.banned_users
        self.banned_channels_col: AsyncCollection = self.db.banned_channels
        self.token_col: AsyncCollection = self.db.tokens
        self.authorized_users_col: AsyncCollection = self.db.authorized_users
        self.restart_message_col: AsyncCollection = self.db.restart_message
        self.files_col: AsyncCollection = self.db.files
        self.file_ingest_locks_col: AsyncCollection = self.db.file_ingest_locks
        self.subscriptions_col: AsyncCollection = self.db.subscriptions
        self.temp_passes_col: AsyncCollection = self.db.temp_passes
        self.sub_requests_col: AsyncCollection = self.db.subscription_requests

    async def _deduplicate_users(self) -> None:
        pipeline = [
            {"$sort": {"join_date": 1}},
            {"$group": {"_id": "$id", "doc_id": {"$first": "$_id"}}},
            {"$project": {"_id": "$doc_id"}}
        ]
        keep_ids = []
        async for doc in self.col.aggregate(pipeline):
            keep_ids.append(doc["_id"])
        if keep_ids:
            result = await self.col.delete_many({"_id": {"$nin": keep_ids}})
            if result.deleted_count > 0:
                logger.warning(f"Deduplicated {result.deleted_count} duplicate user documents.")

    async def ensure_indexes(self, *, raise_on_error: bool = True) -> bool:
        try:
            await self.banned_users_col.create_index("user_id", unique=True)
            await self.banned_channels_col.create_index("channel_id", unique=True)
            await self.token_col.create_index("token", unique=True)
            await self.authorized_users_col.create_index("user_id", unique=True)
            try:
                await self.col.create_index("id", unique=True)
            except DuplicateKeyError:
                logger.warning("Duplicate users found, deduplicating...")
                await self._deduplicate_users()
                await self.col.create_index("id", unique=True)
            await self.token_col.create_index("expires_at", expireAfterSeconds=0)
            await self.token_col.create_index("activated")
            await self.restart_message_col.create_index("message_id", unique=True)
            await self.restart_message_col.create_index("timestamp", expireAfterSeconds=3600)
            await self.files_col.create_index("file_unique_id", unique=True)
            await self.files_col.create_index("public_hash", unique=True)
            await self.files_col.create_index("canonical_message_id", unique=True)
            await self.files_col.create_index("created_at")
            await self.files_col.create_index("last_seen_at")
            await self.file_ingest_locks_col.create_index("expires_at", expireAfterSeconds=0)
            await self.subscriptions_col.create_index("user_id", unique=True)
            await self.subscriptions_col.create_index("expires_at")
            await self.subscriptions_col.create_index("status")
            await self.temp_passes_col.create_index([("user_id", 1), ("file_id", 1)], unique=True)
            await self.temp_passes_col.create_index("expires_at", expireAfterSeconds=0)
            await self.sub_requests_col.create_index("request_id", unique=True)
            await self.sub_requests_col.create_index("user_id")

            logger.debug("Database indexes ensured.")
            return True
        except Exception as e:
            logger.error(f"Error in ensure_indexes: {e}", exc_info=True)
            if raise_on_error:
                raise
            return False

    def new_user(self, user_id: int) -> dict:
        try:
            return {
                'id': user_id,
                'join_date': datetime.datetime.now(datetime.timezone.utc)
            }
        except Exception as e:
            logger.error(f"Error in new_user for user {user_id}: {e}", exc_info=True)
            raise

    async def add_user(self, user_id: int) -> bool:
        try:
            result = await self.col.update_one(
                {'id': user_id},
                {'$setOnInsert': self.new_user(user_id)},
                upsert=True
            )
            if result.upserted_id:
                logger.debug(f"Added new user {user_id} to database.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error in add_user for user {user_id}: {e}", exc_info=True)
            raise


    async def is_user_exist(self, user_id: int) -> bool:
        """Read-only existence check. For user registration, use add_user() instead."""
        try:
            user = await self.col.find_one({'id': user_id}, {'_id': 1})
            return bool(user)
        except Exception as e:
            logger.error(f"Error in is_user_exist for user {user_id}: {e}", exc_info=True)
            raise

    async def total_users_count(self) -> int:
        try:
            return await self.col.count_documents({})
        except Exception as e:
            logger.error(f"Error in total_users_count: {e}", exc_info=True)
            return 0

    async def get_authorized_users_count(self) -> int:
        try:
            return await self.authorized_users_col.count_documents({})
        except Exception as e:
            logger.error(f"Error in get_authorized_users_count: {e}", exc_info=True)
            return 0

    async def get_regular_users_count(self) -> int:
        try:
            auth_ids = await self.authorized_users_col.distinct("user_id")
            return await self.col.count_documents({"id": {"$nin": auth_ids}})
        except Exception as e:
            logger.error(f"Error in get_regular_users_count: {e}", exc_info=True)
            return 0

    async def get_all_users(self):
        try:
            return self.col.find({})
        except Exception as e:
            logger.error(f"Error in get_all_users: {e}", exc_info=True)
            return self.col.find({"_id": {"$exists": False}})

    async def get_authorized_users_cursor(self):
        try:
            return self.authorized_users_col.find({})
        except Exception as e:
            logger.error(f"Error in get_authorized_users_cursor: {e}", exc_info=True)
            return self.authorized_users_col.find({"_id": {"$exists": False}})

    async def get_regular_users_cursor(self):
        try:
            auth_ids = await self.authorized_users_col.distinct("user_id")
            return self.col.find({"id": {"$nin": auth_ids}})
        except Exception as e:
            logger.error(f"Error in get_regular_users_cursor: {e}", exc_info=True)
            return self.col.find({"_id": {"$exists": False}})

    async def delete_user(self, user_id: int):
        try:
            await self.col.delete_one({'id': user_id})
            logger.debug(f"Deleted user {user_id}.")
        except Exception as e:
            logger.error(f"Error in delete_user for user {user_id}: {e}", exc_info=True)
            raise


    async def add_banned_user(
        self, user_id: int, banned_by: Optional[int] = None,
        reason: Optional[str] = None
    ):
        try:
            ban_data = {
                "user_id": user_id,
                "banned_at": datetime.datetime.now(datetime.timezone.utc),
                "banned_by": banned_by,
                "reason": reason
            }
            await self.banned_users_col.update_one(
                {"user_id": user_id},
                {"$set": ban_data},
                upsert=True
            )
            logger.debug(f"Added/Updated banned user {user_id}. Reason: {reason}")
        except Exception as e:
            logger.error(f"Error in add_banned_user for user {user_id}: {e}", exc_info=True)
            raise

    async def remove_banned_user(self, user_id: int) -> bool:
        try:
            result = await self.banned_users_col.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logger.debug(f"Removed banned user {user_id}.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error in remove_banned_user for user {user_id}: {e}", exc_info=True)
            return False

    async def is_user_banned(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.banned_users_col.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error in is_user_banned for user {user_id}: {e}", exc_info=True)
            return None

    async def add_banned_channel(
        self, channel_id: int, banned_by: Optional[int] = None,
        reason: Optional[str] = None
    ):
        try:
            ban_data = {
                "channel_id": channel_id,
                "banned_at": datetime.datetime.now(datetime.timezone.utc),
                "banned_by": banned_by,
                "reason": reason
            }
            await self.banned_channels_col.update_one(
                {"channel_id": channel_id},
                {"$set": ban_data},
                upsert=True
            )
            logger.debug(f"Added/Updated banned channel {channel_id}. Reason: {reason}")
        except Exception as e:
            logger.error(f"Error in add_banned_channel for channel {channel_id}: {e}", exc_info=True)
            raise

    async def remove_banned_channel(self, channel_id: int) -> bool:
        try:
            result = await self.banned_channels_col.delete_one({"channel_id": channel_id})
            if result.deleted_count > 0:
                logger.debug(f"Removed banned channel {channel_id}.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error in remove_banned_channel for channel {channel_id}: {e}", exc_info=True)
            return False

    async def is_channel_banned(self, channel_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.banned_channels_col.find_one({"channel_id": channel_id})
        except Exception as e:
            logger.error(f"Error in is_channel_banned for channel {channel_id}: {e}", exc_info=True)
            return None

    async def save_main_token(self, user_id: int, token_value: str, expires_at: datetime.datetime, created_at: datetime.datetime, activated: bool) -> None:
        try:
            await self.token_col.update_one(
                {"user_id": user_id, "token": token_value},
                {"$set": {
                    "expires_at": expires_at,
                    "created_at": created_at,
                    "activated": activated
                    }
                },
                upsert=True
            )
            logger.debug(f"Saved main token {token_value} for user {user_id} with activated status {activated}.")
        except Exception as e:
            logger.error(f"Error saving main token for user {user_id}: {e}", exc_info=True)
            raise


    async def add_restart_message(self, message_id: int, chat_id: int) -> None:
        try:
            await self.restart_message_col.insert_one({
                "message_id": message_id,
                "chat_id": chat_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
            logger.debug(f"Added restart message {message_id} for chat {chat_id}.")
        except Exception as e:
            logger.error(f"Error adding restart message {message_id}: {e}", exc_info=True)

    async def get_restart_message(self) -> Optional[Dict[str, Any]]:
        try:
            return await self.restart_message_col.find_one(sort=[("timestamp", -1)])
        except Exception as e:
            logger.error(f"Error getting restart message: {e}", exc_info=True)
            return None

    async def delete_restart_message(self, message_id: int) -> None:
        try:
            await self.restart_message_col.delete_one({"message_id": message_id})
            logger.debug(f"Deleted restart message {message_id}.")
        except Exception as e:
            logger.error(f"Error deleting restart message {message_id}: {e}", exc_info=True)

    async def is_user_authorized(self, user_id: int) -> bool:
        try:
            user = await self.authorized_users_col.find_one({'user_id': user_id}, {'_id': 1})
            return bool(user)
        except Exception as e:
            logger.error(f"Error in is_user_authorized for user {user_id}: {e}", exc_info=True)
            return False

    async def get_file_by_unique_id(self, file_unique_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.files_col.find_one({"file_unique_id": file_unique_id})
        except Exception as e:
            logger.error(f"Error getting file by unique_id {file_unique_id}: {e}", exc_info=True)
            return None

    async def get_file_by_hash(
        self,
        public_hash: str,
        *,
        raise_on_error: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self.files_col.find_one({"public_hash": public_hash})
        except Exception as e:
            logger.error(f"Error getting file by hash {public_hash}: {e}", exc_info=True)
            if raise_on_error:
                raise
            return None

    async def get_file_by_message_id(self, canonical_message_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.files_col.find_one({"canonical_message_id": canonical_message_id})
        except Exception as e:
            logger.error(
                f"Error getting file by message_id {canonical_message_id}: {e}",
                exc_info=True
            )
            return None

    async def create_file_record(self, file_record: Dict[str, Any]) -> None:
        try:
            await self.files_col.insert_one(file_record)
        except Exception as e:
            logger.error(
                f"Error creating canonical file record for {file_record.get('file_unique_id')}: {e}",
                exc_info=True
            )
            raise

    async def replace_file_record(self, file_record: Dict[str, Any]) -> None:
        try:
            await self.files_col.replace_one(
                {"file_unique_id": file_record["file_unique_id"]},
                file_record,
                upsert=True
            )
        except Exception as e:
            logger.error(
                f"Error replacing canonical file record for {file_record.get('file_unique_id')}: {e}",
                exc_info=True
            )
            raise

    async def touch_file_record(
        self,
        public_hash: str,
        *,
        reused: bool = False,
        raise_on_error: bool = False
    ) -> bool:
        try:
            update_doc: Dict[str, Any] = {
                "$set": {"last_seen_at": datetime.datetime.now(datetime.timezone.utc)},
                "$inc": {"seen_count": 1}
            }
            if reused:
                update_doc["$inc"]["reuse_count"] = 1
            await self.files_col.update_one({"public_hash": public_hash}, update_doc)
            return True
        except Exception as e:
            logger.error(f"Error touching canonical file {public_hash}: {e}", exc_info=True)
            if raise_on_error:
                raise
            return False

    async def update_file_id(
        self,
        public_hash: str,
        file_id: str,
        *,
        raise_on_error: bool = False
    ) -> bool:
        try:
            await self.files_col.update_one(
                {"public_hash": public_hash},
                {
                    "$set": {
                        "file_id": file_id,
                        "last_seen_at": datetime.datetime.now(datetime.timezone.utc)
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error updating file_id for {public_hash}: {e}", exc_info=True)
            if raise_on_error:
                raise
            return False

    async def acquire_file_ingest_claim(
        self,
        file_unique_id: str,
        *,
        ttl_seconds: int = 60
    ) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc)
        claim_fields = {
            "created_at": now,
            "expires_at": now + datetime.timedelta(seconds=ttl_seconds)
        }
        try:
            await self.file_ingest_locks_col.insert_one({
                "_id": file_unique_id,
                **claim_fields
            })
            return True
        except DuplicateKeyError:
            try:
                result = await self.file_ingest_locks_col.find_one_and_update(
                    {
                        "_id": file_unique_id,
                        "$or": [
                            {"expires_at": {"$lte": now}},
                            {"expires_at": {"$exists": False}}
                        ]
                    },
                    {
                        "$set": claim_fields
                    },
                    return_document=False
                )
                return bool(result)
            except Exception as e:
                logger.error(f"Error updating ingest claim for {file_unique_id}: {e}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Error acquiring ingest claim for {file_unique_id}: {e}", exc_info=True)
            raise

    async def release_file_ingest_claim(self, file_unique_id: str) -> bool:
        try:
            await self.file_ingest_locks_col.delete_one({"_id": file_unique_id})
            return True
        except Exception as e:
            logger.error(f"Error releasing ingest claim for {file_unique_id}: {e}", exc_info=True)
            return False

    async def is_file_ingest_claim_active(self, file_unique_id: str) -> bool:
        try:
            claim = await self.file_ingest_locks_col.find_one(
                {
                    "_id": file_unique_id,
                    "expires_at": {"$gt": datetime.datetime.now(datetime.timezone.utc)}
                },
                {"_id": 1}
            )
            return bool(claim)
        except Exception as e:
            logger.error(f"Error checking ingest claim for {file_unique_id}: {e}", exc_info=True)
            raise


    async def is_subscribed(self, user_id: int) -> bool:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            doc = await self.subscriptions_col.find_one({
                "user_id": user_id,
                "status": "active",
                "expires_at": {"$gt": now}
            })
            return bool(doc)
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id}: {e}", exc_info=True)
            return False

    async def get_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            return await self.subscriptions_col.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {e}", exc_info=True)
            return None

    async def add_subscription(self, user_id: int, days: int = 30, tx_ref: str = "", plan: str = "monthly") -> Dict[str, Any]:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            existing = await self.get_subscription(user_id)
            if existing and existing.get("status") == "active" and existing.get("expires_at") and existing["expires_at"] > now:
                new_expiry = existing["expires_at"] + datetime.timedelta(days=days)
            else:
                new_expiry = now + datetime.timedelta(days=days)

            doc = {
                "user_id": user_id,
                "plan": plan,
                "status": "active",
                "activated_at": now,
                "expires_at": new_expiry,
                "tx_ref": tx_ref or (existing.get("tx_ref", "") if existing else "")
            }
            await self.subscriptions_col.update_one(
                {"user_id": user_id},
                {"$set": doc},
                upsert=True
            )
            logger.info(f"Subscription added for user {user_id}: valid until {new_expiry.isoformat()}")
            return doc
        except Exception as e:
            logger.error(f"Error adding subscription for user {user_id}: {e}", exc_info=True)
            raise

    async def remove_subscription(self, user_id: int) -> bool:
        try:
            res = await self.subscriptions_col.update_one(
                {"user_id": user_id},
                {"$set": {"status": "revoked", "revoked_at": datetime.datetime.now(datetime.timezone.utc)}}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"Error removing subscription for user {user_id}: {e}", exc_info=True)
            return False

    async def get_active_subscribers_count(self) -> int:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            return await self.subscriptions_col.count_documents({
                "status": "active",
                "expires_at": {"$gt": now}
            })
        except Exception as e:
            logger.error(f"Error counting subscribers: {e}", exc_info=True)
            return 0

    async def get_all_subscribers(self, limit: int = 50) -> list:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            cursor = self.subscriptions_col.find({
                "status": "active",
                "expires_at": {"$gt": now}
            }).sort("expires_at", -1).limit(limit)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error(f"Error listing subscribers: {e}", exc_info=True)
            return []

    async def add_temp_pass(self, user_id: int, file_id: str, hours: int = 24) -> bool:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            expiry = now + datetime.timedelta(hours=hours)
            await self.temp_passes_col.update_one(
                {"user_id": user_id, "file_id": str(file_id)},
                {"$set": {"created_at": now, "expires_at": expiry, "used": False}},
                upsert=True
            )
            logger.info(f"Temporary pass added for user {user_id}, file {file_id} (valid {hours}h)")
            return True
        except Exception as e:
            logger.error(f"Error adding temp pass for {user_id}: {e}", exc_info=True)
            return False

    async def has_temp_pass(self, user_id: int, file_id: str) -> bool:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            doc = await self.temp_passes_col.find_one({
                "user_id": user_id,
                "file_id": str(file_id),
                "expires_at": {"$gt": now}
            })
            return bool(doc)
        except Exception as e:
            logger.error(f"Error checking temp pass for {user_id}: {e}", exc_info=True)
            return False

    async def create_sub_request(
        self,
        user_id: int,
        user_name: str,
        req_type: str,
        file_id: Optional[str] = None,
        tx_ref: Optional[str] = None,
        proof_file_id: Optional[str] = None
    ) -> str:
        try:
            req_id = secrets.token_hex(6)
            doc = {
                "request_id": req_id,
                "user_id": user_id,
                "user_name": user_name,
                "req_type": req_type,
                "file_id": str(file_id) if file_id else None,
                "tx_ref": tx_ref,
                "proof_file_id": proof_file_id,
                "status": "pending",
                "created_at": datetime.datetime.now(datetime.timezone.utc)
            }
            await self.sub_requests_col.insert_one(doc)
            return req_id
        except Exception as e:
            logger.error(f"Error creating subscription request: {e}", exc_info=True)
            raise

    async def get_sub_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.sub_requests_col.find_one({"request_id": request_id})
        except Exception as e:
            logger.error(f"Error fetching subscription request {request_id}: {e}", exc_info=True)
            return None

    async def update_sub_request_status(self, request_id: str, status: str, admin_id: int) -> bool:
        try:
            res = await self.sub_requests_col.update_one(
                {"request_id": request_id},
                {"$set": {
                    "status": status,
                    "decided_by": admin_id,
                    "decided_at": datetime.datetime.now(datetime.timezone.utc)
                }}
            )
            return res.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating request {request_id}: {e}", exc_info=True)
            return False

    async def close(self):
        if self._client:
            await self._client.close()

db = Database(Var.DATABASE_URL, Var.NAME)
