# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import re
from random import randint
from time import time

from pymongo import AsyncMongoClient

from anony import config, logger, userbot


class MongoDB:
    def __init__(self):
        self.mongo = AsyncMongoClient(config.MONGO_URL, serverSelectionTimeoutMS=12500)
        self.db = self.mongo.Anon

        self.admin_list = {}
        self.active_calls = {}
        self.admin_play = []
        self.blacklisted = []
        self.cmd_delete = []
        self.loop = {}
        self.notified = []
        self.cache = self.db.cache
        self.logger = False

        self.assistant = {}
        self.assistantdb = self.db.assistant

        self.auth = {}
        self.authdb = self.db.auth

        self.chats = []
        self.chatsdb = self.db.chats

        self.channels = []
        self.channelsdb = self.db.channels

        self.lang = {}
        self.langdb = self.db.lang

        self.users = []
        self.usersdb = self.db.users

        self.s_ranks = set()
        self.banned_users = set()
        self.restricted_cache = {}
        self.muted_cache = {}
        self.hms_cache = {}  # كاش الهمسات في الذاكرة

    # ============================================
    #  الاتصال والإغلاق
    # ============================================
    async def connect(self) -> None:
        try:
            start = time()
            await self.mongo.admin.command("ping")
            logger.info(f"Database connection successful. ({time() - start:.2f}s)")
            await self._create_indexes()
            await self.load_cache()
        except Exception as e:
            raise SystemExit(f"Database connection failed: {type(e).__name__}") from e

    async def close(self) -> None:
        await self.mongo.close()
        logger.info("Database connection closed.")

    async def _create_indexes(self) -> None:
        """إنشاء indexes لتحسين الأداء"""
        try:
            await self.usersdb.create_index("_id")
            await self.chatsdb.create_index("_id")
            await self.channelsdb.create_index("_id")
            await self.cache.create_index("_id")
            logger.info("✅ تم إنشاء indexes")
        except Exception as e:
            logger.warning(f"فشل إنشاء indexes: {e}")

    # ============================================
    #  دوال رتبة S
    # ============================================
    async def add_s_rank(self, user_id: int) -> None:
        self.s_ranks.add(user_id)
        await self.cache.update_one(
            {"_id": "s_ranks"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True,
        )
        logger.info(f"تمت إضافة المستخدم {user_id} إلى رتبة S")

    async def rm_s_rank(self, user_id: int) -> None:
        self.s_ranks.discard(user_id)
        await self.cache.update_one(
            {"_id": "s_ranks"},
            {"$pull": {"user_ids": user_id}},
        )
        logger.info(f"تمت إزالة المستخدم {user_id} من رتبة S")

    async def is_s_rank(self, user_id: int) -> bool:
        # ✅ fast path: set المحلي أولاً (بدون DB query)
        if user_id in self.s_ranks:
            return True

        # fallback للـ DB فقط لو مش موجود
        doc = await self.cache.find_one({"_id": "s_ranks"})
        if doc and user_id in doc.get("user_ids", []):
            self.s_ranks.add(user_id)
            return True

        return False

    async def get_all_s_ranks(self) -> list[int]:
        doc = await self.cache.find_one({"_id": "s_ranks"})
        return doc.get("user_ids", []) if doc else []

    async def get_s_ranks_count(self) -> int:
        doc = await self.cache.find_one({"_id": "s_ranks"})
        return len(doc.get("user_ids", [])) if doc else 0

    async def load_s_ranks_cache(self) -> None:
        doc = await self.cache.find_one({"_id": "s_ranks"})
        s_rank_ids = doc.get("user_ids", []) if doc else []
        self.s_ranks = set(s_rank_ids)
        logger.info(f"تم تحميل {len(self.s_ranks)} عضو من رتبة S إلى الذاكرة المؤقتة")

    # ============================================
    #  دوال حظر المستخدمين (Banned)
    # ============================================
    async def add_banned_user(self, user_id: int, reason: str = "بدون سبب") -> None:
        self.banned_users.add(user_id)
        await self.cache.update_one(
            {"_id": "banned_users"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True,
        )
        await self.cache.update_one(
            {"_id": f"ban_reason_{user_id}"},
            {"$set": {"reason": reason, "banned_at": time()}},
            upsert=True,
        )
        logger.info(f"تم حظر المستخدم {user_id} بسبب: {reason}")

    async def remove_banned_user(self, user_id: int) -> None:
        self.banned_users.discard(user_id)
        await self.cache.update_one(
            {"_id": "banned_users"},
            {"$pull": {"user_ids": user_id}},
        )
        await self.cache.delete_one({"_id": f"ban_reason_{user_id}"})
        logger.info(f"تم إلغاء حظر المستخدم {user_id}")

    async def is_user_banned(self, user_id: int) -> bool:
        if await self.is_s_rank(user_id):
            return False

        if user_id in self.banned_users:
            return True

        doc = await self.cache.find_one({"_id": "banned_users"})
        if doc and user_id in doc.get("user_ids", []):
            self.banned_users.add(user_id)
            return True

        return False

    async def get_banned_users(self) -> list[dict]:
        """✅ محسّنة: query واحد بدل N+1"""
        doc = await self.cache.find_one({"_id": "banned_users"})
        banned_ids = doc.get("user_ids", []) if doc else []
        if not banned_ids:
            return []

        # جلب كل الأسباب في query واحد
        reasons_map = {}
        ids_to_fetch = [f"ban_reason_{uid}" for uid in banned_ids]
        async for r in self.cache.find({"_id": {"$in": ids_to_fetch}}):
            try:
                uid = int(r["_id"].replace("ban_reason_", ""))
                reasons_map[uid] = r
            except (ValueError, KeyError):
                continue

        result = []
        for user_id in banned_ids:
            r = reasons_map.get(user_id)
            result.append({
                "user_id": user_id,
                "reason": r.get("reason", "بدون سبب") if r else "بدون سبب",
                "banned_at": r.get("banned_at", 0) if r else 0,
            })
        return result

    async def get_ban_reason(self, user_id: int) -> str:
        doc = await self.cache.find_one({"_id": f"ban_reason_{user_id}"})
        return doc.get("reason", "لا يوجد سبب") if doc else "غير محظور"

    async def get_banned_users_count(self) -> int:
        doc = await self.cache.find_one({"_id": "banned_users"})
        return len(doc.get("user_ids", [])) if doc else 0

    async def load_banned_users_cache(self) -> None:
        doc = await self.cache.find_one({"_id": "banned_users"})
        banned_ids = doc.get("user_ids", []) if doc else []
        self.banned_users = set(banned_ids)
        logger.info(f"تم تحميل {len(self.banned_users)} مستخدم محظور إلى الذاكرة المؤقتة")

    # ============================================
    #  دوال الكتم (Mute)
    # ============================================
    async def add_muted_user(self, user_id: int, chat_id: int, reason: str = "بدون سبب") -> None:
        await self.cache.update_one(
            {"_id": f"muted_user_{chat_id}_{user_id}"},
            {"$set": {
                "user_id": user_id,
                "chat_id": chat_id,
                "reason": reason,
                "muted_at": time(),
            }},
            upsert=True,
        )
        if chat_id not in self.muted_cache:
            self.muted_cache[chat_id] = set()
        self.muted_cache[chat_id].add(user_id)
        logger.info(f"تم كتم المستخدم {user_id} في المجموعة {chat_id} بسبب: {reason}")

    async def remove_muted_user(self, user_id: int, chat_id: int) -> None:
        await self.cache.delete_one({"_id": f"muted_user_{chat_id}_{user_id}"})
        if chat_id in self.muted_cache:
            self.muted_cache[chat_id].discard(user_id)
        logger.info(f"تم إلغاء كتم المستخدم {user_id} في المجموعة {chat_id}")

    async def is_user_muted(self, user_id: int, chat_id: int) -> bool:
        if await self.is_s_rank(user_id):
            return False

        if chat_id in self.muted_cache and user_id in self.muted_cache[chat_id]:
            return True

        doc = await self.cache.find_one({"_id": f"muted_user_{chat_id}_{user_id}"})
        if doc:
            if chat_id not in self.muted_cache:
                self.muted_cache[chat_id] = set()
            self.muted_cache[chat_id].add(user_id)
            return True

        return False

    async def get_muted_users(self, chat_id: int) -> list[dict]:
        """✅ escape للـ regex"""
        escaped = re.escape(str(chat_id))
        muted_users_list = []
        async for doc in self.cache.find({"_id": {"$regex": f"^muted_user_{escaped}_"}}):
            muted_users_list.append({
                "user_id": doc.get("user_id"),
                "reason": doc.get("reason", "بدون سبب"),
                "muted_at": doc.get("muted_at", 0),
            })
        return muted_users_list

    async def get_muted_users_count(self, chat_id: int) -> int:
        if chat_id in self.muted_cache:
            return len(self.muted_cache[chat_id])

        escaped = re.escape(str(chat_id))
        count = 0
        async for _ in self.cache.find({"_id": {"$regex": f"^muted_user_{escaped}_"}}):
            count += 1
        return count

    async def load_muted_cache(self) -> None:
        self.muted_cache = {}
        async for doc in self.cache.find({"_id": {"$regex": "^muted_user_"}}):
            chat_id = doc.get("chat_id")
            user_id = doc.get("user_id")
            if chat_id and user_id:
                if chat_id not in self.muted_cache:
                    self.muted_cache[chat_id] = set()
                self.muted_cache[chat_id].add(user_id)
        logger.info("تم تحميل كاش المكتمين بنجاح")

    # ============================================
    #  دوال المقيدين (Restricted)
    # ============================================
    async def add_restricted_user(
        self, user_id: int, chat_id: int, reason: str = "بدون سبب", duration: int = 86400
    ) -> None:
        until_time = time() + duration
        await self.cache.update_one(
            {"_id": f"restricted_user_{chat_id}_{user_id}"},
            {"$set": {
                "user_id": user_id,
                "chat_id": chat_id,
                "reason": reason,
                "restricted_at": time(),
                "until_date": until_time,
            }},
            upsert=True,
        )
        if chat_id not in self.restricted_cache:
            self.restricted_cache[chat_id] = {}
        self.restricted_cache[chat_id][user_id] = {
            "reason": reason,
            "until_date": until_time,
        }
        logger.info(f"تم تقييد المستخدم {user_id} في المجموعة {chat_id} لمدة {duration} ثانية")

    async def remove_restricted_user(self, user_id: int, chat_id: int) -> None:
        await self.cache.delete_one({"_id": f"restricted_user_{chat_id}_{user_id}"})
        if chat_id in self.restricted_cache:
            self.restricted_cache[chat_id].pop(user_id, None)
        logger.info(f"تم رفع التقييد عن المستخدم {user_id} في المجموعة {chat_id}")

    async def is_user_restricted(self, user_id: int, chat_id: int) -> bool:
        if await self.is_s_rank(user_id):
            return False

        if chat_id in self.restricted_cache and user_id in self.restricted_cache[chat_id]:
            restricted_data = self.restricted_cache[chat_id][user_id]
            if restricted_data.get("until_date", 0) > time():
                return True
            await self.remove_restricted_user(user_id, chat_id)
            return False

        doc = await self.cache.find_one({"_id": f"restricted_user_{chat_id}_{user_id}"})
        if doc:
            until_date = doc.get("until_date", 0)
            if until_date > time():
                if chat_id not in self.restricted_cache:
                    self.restricted_cache[chat_id] = {}
                self.restricted_cache[chat_id][user_id] = {
                    "reason": doc.get("reason", "بدون سبب"),
                    "until_date": until_date,
                }
                return True
            await self.remove_restricted_user(user_id, chat_id)
            return False
        return False

    async def get_restricted_users(self, chat_id: int) -> list[dict]:
        escaped = re.escape(str(chat_id))
        restricted_users_list = []
        current_time = time()

        async for doc in self.cache.find(
            {"_id": {"$regex": f"^restricted_user_{escaped}_"}}
        ):
            until_date = doc.get("until_date", 0)
            if until_date > current_time:
                restricted_users_list.append({
                    "user_id": doc.get("user_id"),
                    "reason": doc.get("reason", "بدون سبب"),
                    "restricted_at": doc.get("restricted_at", 0),
                    "until_date": until_date,
                })
            else:
                await self.remove_restricted_user(doc.get("user_id"), chat_id)

        return restricted_users_list

    async def get_restricted_users_count(self, chat_id: int) -> int:
        escaped = re.escape(str(chat_id))
        count = 0
        current_time = time()
        async for doc in self.cache.find(
            {"_id": {"$regex": f"^restricted_user_{escaped}_"}}
        ):
            if doc.get("until_date", 0) > current_time:
                count += 1
        return count

    # ============================================
    #  دوال الهمسات (HMS)
    # ============================================
    async def set_hms(self, user_id: int, data: dict) -> None:
        """حفظ همسة لمستخدم"""
        payload = {
            "hms": data.get("hms"),
            "type": data.get("type", "text"),
            "bar": data.get("bar"),
            "from_id": data.get("from_id"),
            "anonymous": data.get("anonymous", False),
            "voice_msg_id": data.get("voice_msg_id"),
            "created_at": time(),
        }
        self.hms_cache[str(user_id)] = payload
        await self.cache.update_one(
            {"_id": f"hms_{user_id}"},
            {"$set": payload},
            upsert=True,
        )

    async def get_hms(self, user_id: int) -> dict | None:
        """جلب همسة مستخدم"""
        # fast path: من الكاش
        cached = self.hms_cache.get(str(user_id))
        if cached:
            return cached

        doc = await self.cache.find_one({"_id": f"hms_{user_id}"})
        if not doc:
            return None

        result = {
            "hms": doc.get("hms"),
            "type": doc.get("type", "text"),
            "bar": doc.get("bar"),
            "from_id": doc.get("from_id"),
            "anonymous": doc.get("anonymous", False),
            "voice_msg_id": doc.get("voice_msg_id"),
        }
        self.hms_cache[str(user_id)] = result
        return result

    async def del_hms(self, user_id: int) -> bool:
        """حذف همسة مستخدم"""
        self.hms_cache.pop(str(user_id), None)
        result = await self.cache.delete_one({"_id": f"hms_{user_id}"})
        return result.deleted_count > 0

    async def load_hms_cache(self) -> None:
        """تحميل الهمسات الموجودة في DB إلى الكاش"""
        self.hms_cache = {}
        count = 0
        async for doc in self.cache.find({"_id": {"$regex": "^hms_"}}):
            try:
                uid = str(doc["_id"]).replace("hms_", "")
                self.hms_cache[uid] = {
                    "hms": doc.get("hms"),
                    "type": doc.get("type", "text"),
                    "bar": doc.get("bar"),
                    "from_id": doc.get("from_id"),
                    "anonymous": doc.get("anonymous", False),
                    "voice_msg_id": doc.get("voice_msg_id"),
                }
                count += 1
            except Exception:
                continue
        logger.info(f"تم تحميل {count} همسة إلى الذاكرة المؤقتة")

    # ============================================
    #  دوال قفل وفتح الميوزك
    # ============================================
    async def set_chat_lock(self, chat_id: int, locked: bool) -> bool:
        try:
            await self.chatsdb.update_one(
                {"_id": chat_id},
                {"$set": {"music_locked": locked}},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"خطأ في تعيين قفل الجروب {chat_id}: {e}")
            return False

    async def is_chat_locked(self, chat_id: int) -> bool:
        try:
            chat = await self.chatsdb.find_one({"_id": chat_id})
            if chat:
                return chat.get("music_locked", False)
            return False
        except Exception as e:
            logger.error(f"خطأ في التحقق من قفل الجروب {chat_id}: {e}")
            return False

    async def set_all_chats_lock(self, locked: bool) -> bool:
        try:
            async for chat in self.chatsdb.find({}):
                chat_id = chat["_id"]
                await self.chatsdb.update_one(
                    {"_id": chat_id},
                    {"$set": {"music_locked": locked}},
                    upsert=True,
                )
            logger.info(f"تم {'قفل' if locked else 'فتح'} الميوزك في جميع الجروبات")
            return True
        except Exception as e:
            logger.error(f"خطأ في تعيين قفل جميع الجروبات: {e}")
            return False

    async def get_all_chats(self) -> list[int]:
        try:
            chats = []
            async for chat in self.chatsdb.find({}):
                chats.append(chat["_id"])
            return chats
        except Exception as e:
            logger.error(f"خطأ في جلب الجروبات: {e}")
            return []

    # ============================================
    #  دوال الكاش العامة (Calls)
    # ============================================
    async def get_call(self, chat_id: int) -> bool:
        return chat_id in self.active_calls

    async def add_call(self, chat_id: int) -> None:
        self.active_calls[chat_id] = 1

    async def remove_call(self, chat_id: int) -> None:
        self.active_calls.pop(chat_id, None)

    async def playing(self, chat_id: int, paused: bool = None) -> bool | None:
        if paused is not None:
            self.active_calls[chat_id] = int(not paused)
        return bool(self.active_calls.get(chat_id, 0))

    async def get_admins(self, chat_id: int, reload: bool = False) -> list[int]:
        from anony.helpers.admins import reload_admins

        if chat_id not in self.admin_list or reload:
            self.admin_list[chat_id] = await reload_admins(chat_id)
        return self.admin_list[chat_id]

    # ✅ loop محفوظ في DB
    async def get_loop(self, chat_id: int) -> int:
        if chat_id not in self.loop:
            doc = await self.chatsdb.find_one({"_id": chat_id})
            self.loop[chat_id] = doc.get("loop", 0) if doc else 0
        return self.loop[chat_id]

    async def set_loop(self, chat_id: int, count: int) -> None:
        self.loop[chat_id] = count
        await self.chatsdb.update_one(
            {"_id": chat_id}, {"$set": {"loop": count}}, upsert=True
        )

    # ============================================
    #  دوال المصادقة (AUTH)
    # ============================================
    async def _get_auth(self, chat_id: int) -> set[int]:
        if chat_id not in self.auth:
            doc = await self.authdb.find_one({"_id": chat_id}) or {}
            self.auth[chat_id] = set(doc.get("user_ids", []))
        return self.auth[chat_id]

    async def is_auth(self, chat_id: int, user_id: int) -> bool:
        return user_id in await self._get_auth(chat_id)

    async def add_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id not in users:
            users.add(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$addToSet": {"user_ids": user_id}}, upsert=True
            )

    async def rm_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id in users:
            users.discard(user_id)
            await self.authdb.update_one(
                {"_id": chat_id}, {"$pull": {"user_ids": user_id}}
            )

    # ============================================
    #  دوال المساعد (ASSISTANT)
    # ============================================
    async def set_assistant(self, chat_id: int) -> int:
        n = len(userbot.clients)
        if n == 0:
            raise RuntimeError("لا يوجد حساب مساعد متاح")
        num = randint(1, n)
        await self.assistantdb.update_one(
            {"_id": chat_id},
            {"$set": {"num": num}},
            upsert=True,
        )
        self.assistant[chat_id] = num
        return num

    async def get_assistant(self, chat_id: int):
        from anony import anon

        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})
            num = doc["num"] if doc else None

            if not num or num > len(anon.clients):
                num = await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        return anon.clients[self.assistant[chat_id] - 1]

    async def get_client(self, chat_id: int):
        if chat_id not in self.assistant:
            await self.get_assistant(chat_id)

        num = self.assistant[chat_id]
        if num > len(userbot.clients):
            num = await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        return {1: userbot.one, 2: userbot.two, 3: userbot.three}.get(num)

    async def get_assistant_userbot(self, chat_id: int):
        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})
            num = doc["num"] if doc else None

            if not num or num > len(userbot.clients):
                num = await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        num = self.assistant[chat_id]
        if num == 1:
            return userbot.one
        elif num == 2:
            return userbot.two
        elif num == 3:
            return userbot.three
        return userbot.one

    async def join_assistant_to_channel(self, chat_id: int, message=None):
        from anony import app
        from pyrogram import errors
        import asyncio

        client = await self.get_assistant_userbot(chat_id)

        try:
            member = await app.get_chat_member(chat_id, client.id)
            if member.status in [
                errors.enums.ChatMemberStatus.BANNED,
                errors.enums.ChatMemberStatus.RESTRICTED,
            ]:
                try:
                    await app.unban_chat_member(chat_id=chat_id, user_id=client.id)
                except Exception:
                    pass
            return True

        except errors.UserNotParticipant:
            if message:
                await message.reply_text("⚡ جاري إضافة الحساب المساعد إلى القناة...")

            try:
                chat = await app.get_chat(chat_id)
                if chat.username:
                    invite_link = chat.username
                    await client.resolve_peer(invite_link)
                else:
                    invite_link = await app.export_chat_invite_link(chat_id)
                try:
                    await client.join_chat(invite_link)
                except errors.InviteRequestSent:
                    await asyncio.sleep(2)
                    try:
                        await app.approve_chat_join_request(chat_id, client.id)
                    except errors.HideRequesterMissing:
                        pass
                    except Exception:
                        pass

                if message:
                    await message.reply_text("✅ تم إضافة الحساب المساعد بنجاح")
                return True

            except Exception as ex:
                if message:
                    await message.reply_text(f"❌ فشل إضافة المساعد: {type(ex).__name__}")
                return False

        except Exception:
            return True

    # ============================================
    #  دوال القائمة السوداء (Blacklist)
    # ============================================
    async def add_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            if chat_id not in self.blacklisted:
                self.blacklisted.append(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"}, {"$addToSet": {"chat_ids": chat_id}}, upsert=True
            )
        await self.cache.update_one(
            {"_id": "bl_users"}, {"$addToSet": {"user_ids": chat_id}}, upsert=True
        )

    async def del_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            if chat_id in self.blacklisted:
                self.blacklisted.remove(chat_id)
            return await self.cache.update_one(
                {"_id": "bl_chats"}, {"$pull": {"chat_ids": chat_id}}
            )
        await self.cache.update_one(
            {"_id": "bl_users"}, {"$pull": {"user_ids": chat_id}}
        )

    async def get_blacklisted(self, chat: bool = False) -> list[int]:
        if chat:
            if not self.blacklisted:
                doc = await self.cache.find_one({"_id": "bl_chats"})
                self.blacklisted.extend(doc.get("chat_ids", []) if doc else [])
            return self.blacklisted
        doc = await self.cache.find_one({"_id": "bl_users"})
        return doc.get("user_ids", []) if doc else []

    # ============================================
    #  دوال الدردشات (Chats)
    # ============================================
    async def is_chat(self, chat_id: int) -> bool:
        return chat_id in self.chats

    async def add_chat(self, chat_id: int) -> None:
        if not await self.is_chat(chat_id):
            self.chats.append(chat_id)
            # ✅ upsert بدل insert_one (يمنع DuplicateKeyError)
            await self.chatsdb.update_one(
                {"_id": chat_id}, {"$setOnInsert": {"_id": chat_id}}, upsert=True
            )

    async def rm_chat(self, chat_id: int) -> None:
        if await self.is_chat(chat_id):
            self.chats.remove(chat_id)
            await self.chatsdb.delete_one({"_id": chat_id})

    async def get_chats(self) -> list:
        if not self.chats:
            self.chats.extend([chat["_id"] async for chat in self.chatsdb.find()])
        return self.chats

    # ============================================
    #  دوال القنوات (Channels)
    # ============================================
    async def is_channel(self, channel_id: int) -> bool:
        return channel_id in self.channels

    async def add_channel(self, channel_id: int) -> None:
        if not await self.is_channel(channel_id):
            self.channels.append(channel_id)
            await self.channelsdb.update_one(
                {"_id": channel_id}, {"$setOnInsert": {"_id": channel_id}}, upsert=True
            )
            await self.cache.update_one(
                {"_id": "channels_count"}, {"$inc": {"count": 1}}, upsert=True
            )

    async def rm_channel(self, channel_id: int) -> None:
        if await self.is_channel(channel_id):
            self.channels.remove(channel_id)
            await self.channelsdb.delete_one({"_id": channel_id})
            await self.cache.update_one(
                {"_id": "channels_count"}, {"$inc": {"count": -1}}, upsert=True
            )

    async def get_channels(self) -> list:
        if not self.channels:
            self.channels.extend([ch["_id"] async for ch in self.channelsdb.find()])
        return self.channels

    async def get_channels_count(self) -> int:
        doc = await self.cache.find_one({"_id": "channels_count"})
        if doc:
            return doc.get("count", 0)
        count = await self.channelsdb.count_documents({})
        await self.cache.update_one(
            {"_id": "channels_count"}, {"$set": {"count": count}}, upsert=True
        )
        return count

    # ============================================
    #  دوال حذف الأوامر (cmd_delete)
    # ============================================
    async def get_cmd_delete(self, chat_id: int) -> bool:
        if chat_id not in self.cmd_delete:
            doc = await self.chatsdb.find_one({"_id": chat_id})
            if doc and doc.get("cmd_delete"):
                self.cmd_delete.append(chat_id)
        return chat_id in self.cmd_delete

    async def set_cmd_delete(self, chat_id: int, delete: bool = False) -> None:
        if delete:
            if chat_id not in self.cmd_delete:
                self.cmd_delete.append(chat_id)
        else:
            if chat_id in self.cmd_delete:
                self.cmd_delete.remove(chat_id)
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"cmd_delete": delete}},
            upsert=True,
        )

    # ============================================
    #  دوال اللغة (Language)
    # ============================================
    async def set_lang(self, chat_id: int, lang_code: str):
        await self.langdb.update_one(
            {"_id": chat_id},
            {"$set": {"lang": lang_code}},
            upsert=True,
        )
        self.lang[chat_id] = lang_code

    async def get_lang(self, chat_id: int) -> str:
        if chat_id not in self.lang:
            doc = await self.langdb.find_one({"_id": chat_id})
            self.lang[chat_id] = doc["lang"] if doc else config.LANG_CODE
        return self.lang[chat_id]

    # ============================================
    #  دوال التسجيل (Logger)
    # ============================================
    async def is_logger(self) -> bool:
        return self.logger

    async def get_logger(self) -> bool:
        doc = await self.cache.find_one({"_id": "logger"})
        if doc:
            self.logger = doc["status"]
        return self.logger

    async def set_logger(self, status: bool) -> None:
        self.logger = status
        await self.cache.update_one(
            {"_id": "logger"},
            {"$set": {"status": status}},
            upsert=True,
        )

    # ============================================
    #  دوال وضع التشغيل (Play Mode)
    # ============================================
    async def get_play_mode(self, chat_id: int) -> bool:
        if chat_id not in self.admin_play:
            doc = await self.chatsdb.find_one({"_id": chat_id})
            if doc and doc.get("admin_play"):
                self.admin_play.append(chat_id)
        return chat_id in self.admin_play

    async def set_play_mode(self, chat_id: int, remove: bool = False) -> None:
        if remove:
            if chat_id in self.admin_play:
                self.admin_play.remove(chat_id)
        else:
            if chat_id not in self.admin_play:
                self.admin_play.append(chat_id)
        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"admin_play": not remove}},
            upsert=True,
        )

    # ============================================
    #  دوال المطورين الإضافيين (Sudoers)
    # ============================================
    async def add_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"}, {"$addToSet": {"user_ids": user_id}}, upsert=True
        )

    async def del_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"}, {"$pull": {"user_ids": user_id}}
        )

    async def get_sudoers(self) -> list[int]:
        doc = await self.cache.find_one({"_id": "sudoers"})
        return doc.get("user_ids", []) if doc else []

    # ============================================
    #  دوال المستخدمين (Users)
    # ============================================
    async def is_user(self, user_id: int) -> bool:
        return user_id in self.users

    async def add_user(self, user_id: int) -> None:
        if not await self.is_user(user_id):
            self.users.append(user_id)
            await self.usersdb.update_one(
                {"_id": user_id}, {"$setOnInsert": {"_id": user_id}}, upsert=True
            )

    async def rm_user(self, user_id: int) -> None:
        if await self.is_user(user_id):
            self.users.remove(user_id)
            await self.usersdb.delete_one({"_id": user_id})

    async def get_users(self) -> list:
        if not self.users:
            self.users.extend([user["_id"] async for user in self.usersdb.find()])
        return self.users

    # ============================================
    #  دوال الترحيل (Migration)
    # ============================================
    async def migrate_coll(self) -> None:
        existing = await self.cache.find_one({"_id": "migrated"})
        if existing:
            logger.info("تم الترحيل مسبقاً، جاري التخطي...")
            return

        # ✅ backup قبل الحذف
        backup_users = [u async for u in self.usersdb.find()]
        backup_chats = [c async for c in self.chatsdb.find()]
        backup_tg = [u async for u in self.db.tgusersdb.find()]

        try:
            users, musers, mchats = [], [], []
            seen_chats, seen_users = set(), set()
            users.extend(backup_users)
            users.extend(backup_tg)

            for user in users:
                _id = user.get("_id")
                if isinstance(_id, int):
                    user_id = _id
                else:
                    user_id = int(user.get("user_id"))

                if user_id in seen_users:
                    continue
                seen_users.add(user_id)
                musers.append({"_id": user_id})

            await self.usersdb.drop()
            await self.db.tgusersdb.drop()
            if musers:
                await self.usersdb.insert_many(musers)

            async for chat in backup_chats:
                _id = chat.get("_id")
                if isinstance(_id, int):
                    chat_id = _id
                else:
                    chat_id = int(chat.get("chat_id"))
                if chat_id in seen_chats:
                    continue
                seen_chats.add(chat_id)
                mchats.append({"_id": chat_id})

            await self.chatsdb.drop()
            if mchats:
                await self.chatsdb.insert_many(mchats)

            await self.cache.update_one(
                {"_id": "migrated"},
                {"$set": {"migrated_at": time()}},
                upsert=True,
            )
            logger.info("تم إكمال الترحيل بنجاح.")

        except Exception as e:
            logger.error(f"فشل الترحيل: {e} — استرجاع البيانات...")
            try:
                if backup_users:
                    await self.usersdb.drop()
                    await self.usersdb.insert_many(backup_users)
                if backup_tg:
                    await self.db.tgusersdb.drop()
                    await self.db.tgusersdb.insert_many(backup_tg)
                if backup_chats:
                    await self.chatsdb.drop()
                    await self.chatsdb.insert_many(backup_chats)
                logger.info("تم استرجاع البيانات بنجاح")
            except Exception as e2:
                logger.error(f"فشل استرجاع البيانات: {e2}")
            raise

    # ============================================
    #  دوال تخصيص السورس
    # ============================================
    async def set_source_customization(self, bot_id: int, key: str, value: any) -> None:
        await self.cache.update_one(
            {"_id": f"source_customization_{bot_id}"},
            {"$set": {key: value}},
            upsert=True,
        )

    async def get_source_customization(self, bot_id: int, key: str) -> any:
        doc = await self.cache.find_one({"_id": f"source_customization_{bot_id}"})
        return doc.get(key) if doc else None

    async def reset_source_customization(self, bot_id: int) -> None:
        try:
            await self.cache.delete_one({"_id": f"source_customization_{bot_id}"})
            logger.info(f"تم حذف تخصيصات السورس للبوت {bot_id} بنجاح")
        except Exception as e:
            logger.warning(f"خطأ أثناء حذف تخصيصات السورس للبوت {bot_id}: {e}")
            try:
                await self.cache.update_one(
                    {"_id": f"source_customization_{bot_id}"},
                    {"$set": {"caption": None, "buttons": None, "media": None}},
                    upsert=True,
                )
                logger.info(
                    f"تم إعادة تعيين تخصيصات السورس للبوت {bot_id} باستخدام طريقة بديلة"
                )
            except Exception as e2:
                logger.error(f"فشل إعادة تعيين تخصيصات السورس للبوت {bot_id}: {e2}")

    # ============================================
    #  دوال الاشتراك الإجباري
    # ============================================
    async def set_must_channel(self, bot_username: str, channel_username: str) -> None:
        await self.cache.update_one(
            {"_id": f"must_join_{bot_username}"},
            {"$set": {"channel": channel_username}},
            upsert=True,
        )

    async def get_must_channel(self, bot_username: str) -> str | None:
        doc = await self.cache.find_one({"_id": f"must_join_{bot_username}"})
        return doc.get("channel") if doc else None

    async def del_must_channel(self, bot_username: str) -> bool:
        result = await self.cache.delete_one({"_id": f"must_join_{bot_username}"})
        return result.deleted_count > 0

    async def set_must_status(self, bot_username: str, status: str) -> None:
        await self.cache.update_one(
            {"_id": f"must_status_{bot_username}"},
            {"$set": {"status": status}},
            upsert=True,
        )

    async def get_must_status(self, bot_username: str) -> str:
        doc = await self.cache.find_one({"_id": f"must_status_{bot_username}"})
        return doc.get("status", "disable") if doc else "disable"

    async def get_must(self, bot_username: str) -> str | None:
        return await self.get_must_channel(bot_username)

    async def get_must_ch(self, bot_username: str) -> str:
        status = await self.get_must_status(bot_username)
        return "مفعل" if status == "enable" else "معطل"

    # ============================================
    #  دوال تخصيص زر التحكم
    # ============================================
    async def set_control_button_text(self, bot_id: int, text: str) -> None:
        await self.cache.update_one(
            {"_id": f"control_button_{bot_id}"},
            {"$set": {"text": text}},
            upsert=True,
        )

    async def get_control_button_text(self, bot_id: int) -> str:
        doc = await self.cache.find_one({"_id": f"control_button_{bot_id}"})
        return doc.get("text") if doc else "𝔬𝔫𝔢"

    async def set_control_button_url(self, bot_id: int, url: str) -> None:
        await self.cache.update_one(
            {"_id": f"control_button_{bot_id}"},
            {"$set": {"url": url}},
            upsert=True,
        )

    async def get_control_button_url(self, bot_id: int) -> str:
        doc = await self.cache.find_one({"_id": f"control_button_{bot_id}"})
        return doc.get("url") if doc else config.SUPPORT_CHANNEL

    async def reset_control_button(self, bot_id: int) -> None:
        await self.cache.delete_one({"_id": f"control_button_{bot_id}"})

    # ============================================
    #  تحميل الكاش
    # ============================================
    async def load_cache(self) -> None:
        doc = await self.cache.find_one({"_id": "migrated"})
        if not doc:
            await self.migrate_coll()

        await self.get_chats()
        await self.get_users()
        await self.get_channels()
        await self.get_blacklisted(True)
        await self.get_logger()
        await self.load_banned_users_cache()
        await self.load_s_ranks_cache()
        await self.load_muted_cache()
        await self.load_hms_cache()  # ✅ جديد
        logger.info("تم تحميل ذاكرة التخزين بنجاح")