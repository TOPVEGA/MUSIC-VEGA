# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import time
from datetime import datetime

import pytz
from pyrogram import Client, enums, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.types import (
    CallbackQuery,
    ChatPrivileges,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from anony import app, config, db, lang
from anony.helpers import admin_check, is_admin, utils
from anony.helpers.admins import banned_check, is_owner

# ========== المتغيرات العامة ==========
OWNER_ID = config.OWNER_ID
s_rank_cooldown = {}
rel_hist = {}


def _is_owner_id(user_id) -> bool:
    """مقارنة آمنة لمعرف المطور"""
    return str(user_id) == str(OWNER_ID)


# ========== أمر رتبتي ==========
@app.on_message(
    filters.command(["رتبتي", "/myrank", "رتبتِي"], "") & ~app.bl_users,
    group=799,
)
@lang.language()
@banned_check
async def my_rank(_, m: Message):
    user = m.from_user
    user_id = user.id
    rank = "👤 عضو عادي"
    rank_emoji = "👤"
    description = "ليس لديك أي صلاحيات خاصة في البوت"

    if _is_owner_id(user_id):
        rank = "👑 • المطور الأساسي (Owner)"
        rank_emoji = "👑"
        description = (
            "• لديك كامل الصلاحيات في البوت\n"
            "• يمكنك التحكم بجميع الإعدادات\n"
            "• يمكنك رفع وتنزيل المطورين\n"
            "• يمكنك التحكم برتبة 𝐒"
        )
    elif await db.is_s_rank(user_id):
        rank = "⭐ • رتبة 𝐒 (Super User)"
        rank_emoji = "⭐"
        description = (
            "<b>• لديك صلاحيات خاصة في كل المجموعات\n"
            "• يمكنك استخدام أوامر الحظر والطرد\n"
            "• ترحيب مميز عند الانضمام\n"
            "• صلاحياتك تتبعك في كل المجموعات</b>"
        )
    elif m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            member = await app.get_chat_member(m.chat.id, user_id)
            if member.status in [
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ]:
                rank = "🛡️ مشرف (Admin)"
                rank_emoji = "🛡️"
                description = (
                    "✅ لديك صلاحيات إدارة في هذه المجموعة\n"
                    "✅ يمكنك استخدام أوامر التحكم بالبوت هنا"
                )
        except Exception:
            pass

    rank_message = (
        f"<b>\n{rank_emoji} معلومات رتبتك {rank_emoji}\n\n"
        f"• الاسم: {user.mention}\n"
        f"• الايدي: <code>{user_id}</code>\n\n"
        f"{rank}\n\n"
        f"• الوصف:\n{description}\n"
        f"• ملاحظة: رتبة S تمنحك صلاحيات خاصة في كل المجموعات</b>\nㅤ"
    )

    keyboard = []
    if _is_owner_id(user_id):
        keyboard.append([InlineKeyboardButton("👑 قائمة رتب 𝐒", callback_data="show_s_list")])
        keyboard.append([InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")])
    elif await db.is_s_rank(user_id):
        keyboard.append([InlineKeyboardButton("⭐ صلاحيات رتبة 𝐒", callback_data="show_s_benefits")])

    if keyboard:
        await m.reply_text(
            rank_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
        )
    else:
        await m.reply_text(rank_message, disable_web_page_preview=True)


# ========== أمر صلاحياتي ==========
@app.on_message(
    filters.command(["صلاحياتي", "my_s", "/mys"], "") & ~app.bl_users,
    group=803,
)
@lang.language()
@banned_check
async def my_benefits(_, m: Message):
    user_id = m.from_user.id
    if _is_owner_id(user_id):
        return await m.reply_text(
            f"<b>صلاحيات المطور الأساسي 👑\n\n"
            f"• مرحباً {m.from_user.mention}\n\n"
            f"• الامتيازات الكاملة:\n"
            f"• التحكم الكامل بجميع إعدادات البوت\n"
            f"• إدارة المطورين (رفع تنزيل)\n"
            f"• إدارة رتبة 𝐒 (رفع تنزيل)\n"
            f"• الإذاعة لجميع المستخدمين والمجموعات\n"
            f"• تغيير إعدادات السورس\n"
            f"• الإحصائيات الكاملة للنظام\n"
            f"• حماية كاملة من الحظر\n"
            f"• جميع أوامر البوت متاحة لك</b>"
        )

    if not await db.is_s_rank(user_id):
        return await m.reply_text("هذا الأمر فقط لأعضاء رتبة S والمطور الأساسي!")

    await m.reply_text(
        f"<b>⭐ مزايا رتبة S ⭐\n\n"
        f"• مرحباً {m.from_user.mention}\n\n"
        f"• الامتيازات الحصرية:\n"
        f"• ترحيب مميز في كل المجموعات\n"
        f"• استخدام أوامر التحكم بالبوت بدون صلاحيات\n"
        f"• حماية من العقوبات (باند كتم طرد)\n"
        f"• أوامر خاصة متاحة لك فقط\n"
        f"• إمكانية طرد وحظر المخالفين\n"
        f"• تنظيف الرسائل بسرعة\n\n"
        f"• ملاحظة: صلاحياتك تتبعك في كل المجموعات</b>"
    )


# ========== أمر ترقية S ==========
@app.on_message(
    filters.command(["/ups", "ترقيه s"], "") & ~app.bl_users, group=800
)
@is_owner
async def give_s_rank(_, m: Message):
    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text("المستخدم غير موجود!")

    me = await app.get_me()
    if user.id == me.id:
        return await m.reply_text("لا يمكن منح رتبة S للبوت نفسه!")

    if await db.is_s_rank(user.id):
        return await m.reply_text(f"• المستخدم {user.mention} لديه بالفعل رتبة S!")

    await db.add_s_rank(user.id)
    await m.reply_text(
        f"<b>👑 تم منح رتبة 𝐒 👑\n\n"
        f"• المستخدم: {user.mention}\n"
        f"• الايدي: <code>{user.id}</code>\n\n"
        f"• يمكنه الآن استخدام صلاحيات البوت الخاصة في كل المجموعات</b>"
    )


# ========== أمر سحب رتبة S ==========
@app.on_message(
    filters.command(["/dels", "سحب اس"], "") & ~app.bl_users, group=801
)
@is_owner
async def take_s_rank(_, m: Message):
    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text("المستخدم غير موجود!")

    if not await db.is_s_rank(user.id):
        return await m.reply_text(f"• المستخدم {user.mention} ليس لديه رتبة S!")

    await db.rm_s_rank(user.id)
    await m.reply_text(
        f"<b>• تم سحب رتبة 𝐒\n\n"
        f"• المستخدم: {user.mention}\n"
        f"• الايدي: <code>{user.id}</code></b>"
    )


# ========== أمر عرض قائمة S ==========
@app.on_message(
    filters.command(["s_list", "قائمة اس"], "") & ~app.bl_users, group=802
)
async def s_rank_list(_, m: Message):
    if not _is_owner_id(m.from_user.id):
        if m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            if not await is_admin(m.chat.id, m.from_user.id):
                return await m.reply_text("❌ هذا الأمر للمشرفين ومالك البوت فقط!")
        else:
            return await m.reply_text("❌ هذا الأمر للمشرفين ومالك البوت فقط!")

    s_ranks = await db.get_all_s_ranks()
    if not s_ranks:
        return await m.reply_text("لا يوجد أعضاء برتبة S حالياً.")

    txt = f"👑 قائمة رتبة 𝐒 👑\n\n📊 العدد: {len(s_ranks)}\n"
    for i, user_id in enumerate(s_ranks, start=1):
        try:
            user = await app.get_users(user_id)
            mention = user.mention if user.mention else user.first_name
            username = f"@{user.username}" if user.username else "لا يوجد معرف"
            txt += f"{i}. {mention}\n   └ 🆔 <code>{user_id}</code> | {username}\n\n"
        except Exception:
            txt += (
                f"{i}. <a href='tg://user?id={user_id}'>المستخدم</a>\n"
                f"   └ 🆔 <code>{user_id}</code>\n\n"
            )

    if _is_owner_id(m.from_user.id):
        keyboard = [[InlineKeyboardButton("🔄 تحديث الكاش", callback_data="reload_s_ranks")]]
        await m.reply_text(
            txt, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await m.reply_text(txt, disable_web_page_preview=True)


# ========== أمر تحديث الكاش ==========
@app.on_message(
    filters.command(["reload_s", "تحديث s"], "") & ~app.bl_users, group=804
)
@is_owner
async def reload_s_rank_cache(_, m: Message):
    if m.from_user.id in s_rank_cooldown:
        if time.time() < s_rank_cooldown[m.from_user.id]:
            return await m.reply_text("⏳ يرجى الانتظار 5 دقائق قبل إعادة التحديث!")

    s_rank_cooldown[m.from_user.id] = time.time() + 300
    sent = await m.reply_text("🔄 جاري تحديث كاش رتبة S...")
    await db.load_s_ranks_cache()
    count = await db.get_s_ranks_count()
    await sent.edit_text(f"✅ تم التحديث!\n👑 عدد حاملي الرتبة: {count}")


# ========== معالجة الأزرار ==========
@app.on_callback_query(group=820)
async def s_rank_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data

    if data == "show_s_list":
        s_ranks = await db.get_all_s_ranks()
        if not s_ranks:
            return await callback_query.answer("📭 لا يوجد أعضاء برتبة S حالياً", show_alert=True)

        txt = f"👑 قائمة رتبة S 👑\n\n📊 العدد: {len(s_ranks)}\n"
        for i, user_id in enumerate(s_ranks, start=1):
            try:
                user = await app.get_users(user_id)
                mention = user.mention if user.mention else user.first_name
                txt += f"{i}. {mention}\n   └ 🆔 <code>{user_id}</code>\n\n"
            except Exception:
                txt += (
                    f"{i}. <a href='tg://user?id={user_id}'>المستخدم</a>\n"
                    f"   └ 🆔 <code>{user_id}</code>\n\n"
                )

        await callback_query.message.edit_text(txt, disable_web_page_preview=True)
        await callback_query.answer()

    elif data == "show_s_benefits":
        await callback_query.message.edit_text(
            f"<b>• مزايا رتبة S ⭐\n\n"
            f"• الامتيازات الحصرية:\n"
            f"• ترحيب مميز في كل المجموعات\n"
            f"• استخدام أوامر التحكم بالبوت بدون صلاحيات\n"
            f"• حماية من العقوبات (باند كتم طرد)\n"
            f"• أوامر خاصة متاحة لك فقط\n"
            f"• إمكانية طرد وحظر المخالفين\n"
            f"• تنظيف الرسائل بسرعة\n\n"
            f"• ملاحظة: صلاحياتك تتبعك في كل المجموعات</b>"
        )
        await callback_query.answer()

    elif data == "show_stats":
        users_count = len(await db.get_users())
        chats_count = len(await db.get_chats())
        s_ranks_count = await db.get_s_ranks_count()

        await callback_query.message.edit_text(
            f"• إحصائيات البوت 📊\n\n"
            f"• المستخدمين: {users_count}\n"
            f"• المجموعات: {chats_count}\n"
            f"• رتبة S: {s_ranks_count}\n"
            f"• المطور: {len(app.sudoers)}\n\n"
            f"• آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await callback_query.answer()

    elif data == "reload_s_ranks":
        await db.load_s_ranks_cache()
        count = await db.get_s_ranks_count()
        await callback_query.answer(
            f"✅ تم التحديث! عدد حاملي الرتبة: {count}", show_alert=True
        )
        try:
            await callback_query.message.delete()
        except Exception:
            pass


# ========== ترحيب مميز لرتبة S ==========
@app.on_chat_member_updated(group=805)
async def s_rank_welcome(client: Client, chat_member_updated):
    try:
        new_member = chat_member_updated.new_chat_member
        if not new_member or new_member.status != ChatMemberStatus.MEMBER:
            return

        user = new_member.user
        if not user or not await db.is_s_rank(user.id):
            return

        group_id = chat_member_updated.chat.id
        username = f"@{user.username}" if user.username else "لا يوجد معرف"
        cairo_tz = pytz.timezone("Africa/Cairo")
        cairo_time = datetime.now(cairo_tz).strftime("%Y-%m-%d %I:%M:%S %p")

        welcome_message = (
            f"⭐ ترحيب خاص برتبة S ⭐\n\n"
            f"☆ يتشرف المجموعة بانضمامك ☆\n"
            f"ɴᴧᴍᴇ ⌯ {user.mention}\n"
            f"ᴜѕᴇꝛɴᴧᴍᴇ ⌯ {username}\n"
            f"ᴅᴀᴛᴇ ⌯ {cairo_time}\n\n"
            f"• لديك صلاحيات خاصة في البوت ✨\n"
            f"• استخدم `صلاحياتي` لعرض صلاحياتك"
        )

        keyboard = None
        if user.username:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=user.first_name or "المستخدم", url=f"https://t.me/{user.username}")]]
            )

        await client.send_message(
            chat_id=group_id,
            text=welcome_message,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except FloodWait as e:
        import asyncio
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"[S_RANK] خطأ في الترحيب: {e}")


# ========== أوامر المصادقة ==========
@app.on_message(
    filters.command(["auth", "unauth"]) & filters.group & ~app.bl_users,
    group=809,
)
@lang.language()
@admin_check
async def _auth(_, m: Message):
    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if m.command[0] == "auth":
        if await is_admin(m.chat.id, user.id):
            return await m.reply_text(m.lang["auth_is_admin"])
        await db.add_auth(m.chat.id, user.id)
        await m.reply_text(m.lang["auth_added"].format(user.mention))
    else:
        await db.rm_auth(m.chat.id, user.id)
        await m.reply_text(m.lang["auth_removed"].format(user.mention))


# ========== قائمة المصادقة ==========
@app.on_message(
    filters.command(["authlist"]) & filters.group & ~app.bl_users, group=810
)
@lang.language()
@admin_check
async def _authlist(_, m: Message):
    auth = await db._get_auth(m.chat.id)
    if not auth:
        return await m.reply_text(m.lang["auth_empty"])

    auth_txt = m.lang["auth_list"].format(m.chat.title)
    for i, user in enumerate(auth, start=1):
        auth_txt += f"\n{i}. <a href=tg://user?id={user}>{user}</a>"
    await m.reply_text(auth_txt)


# ========== تحديث كاش الأدمن ==========
@app.on_message(
    filters.command(["تحديث الادمن", "/reload"], "") & filters.group & ~app.bl_users,
    group=811,
)
@lang.language()
async def _admincache(_, m: Message):
    if m.from_user.id in rel_hist:
        if time.time() < rel_hist[m.from_user.id]:
            return await m.reply_text(m.lang["admin_cache_wait"])

    rel_hist[m.from_user.id] = time.time() + 600
    sent = await m.reply_text(m.lang["admin_cache_reloading"])
    await db.get_admins(m.chat.id, reload=True)
    await sent.edit_text(m.lang["admin_cache_reloaded"])


# ========== ترحيب عند انضمام عضو جديد ==========
@app.on_chat_member_updated(group=815)
async def tr1hib(client: Client, chat_member_updated):
    try:
        new_member = chat_member_updated.new_chat_member
        old_member = chat_member_updated.old_chat_member

        if not new_member or new_member.status != ChatMemberStatus.MEMBER:
            return

        user = new_member.user
        if not user:
            return

        # تخطي رتبة S (لها ترحيب مخصص)
        if await db.is_s_rank(user.id):
            return

        if old_member and old_member.status == ChatMemberStatus.MEMBER:
            return

        group_id = chat_member_updated.chat.id
        user_mention = user.mention
        username = f"@{user.username}" if user.username else "لا يوجد معرف"
        cairo_tz = pytz.timezone("Africa/Cairo")
        cairo_time = datetime.now(cairo_tz).strftime("%I:%M %p")

        welcome_message = (
            f"• لا تُسِئ اللفظ وإن ضَاق عليك الرَّد\n"
            f"• ɴᴧᴍᴇ ⌯ {user_mention}\n"
            f"• ᴜѕᴇꝛɴᴧᴍᴇ ⌯ {username}\n"
            f"• ᴅᴀᴛᴇ ⌯ {cairo_time}"
        )

        keyboard = None
        if user.username:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=user.first_name, url=f"https://t.me/{user.username}")]]
            )

        await client.send_message(
            chat_id=group_id,
            text=welcome_message,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except FloodWait as e:
        import asyncio
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"حدث خطأ في إرسال الترحيب: {e}")


# ========== رسالة مغادرة ==========
@app.on_chat_member_updated(group=816)
async def tr1hibi(client: Client, chat_member_updated):
    try:
        old_member = chat_member_updated.old_chat_member
        new_member = chat_member_updated.new_chat_member

        if not old_member or old_member.status != ChatMemberStatus.MEMBER:
            return
        if not new_member or new_member.status != ChatMemberStatus.LEFT:
            return

        user = old_member.user
        if not user:
            return

        group_id = chat_member_updated.chat.id
        user_mention = user.mention
        username = f"@{user.username}" if user.username else "لا يوجد معرف"
        cairo_tz = pytz.timezone("Africa/Cairo")
        cairo_time = datetime.now(cairo_tz).strftime("%I:%M %p")

        goodbye_message = (
            f"غادر المجموعة\n"
            f"ɴᴧᴍᴇ ⌯ {user_mention}\n"
            f"ᴜѕᴇꝛɴᴧᴍᴇ ⌯ {username}\n"
            f"ᴅᴀᴛᴇ ⌯ {cairo_time}"
        )

        keyboard = None
        if user.username:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=user.first_name, url=f"https://t.me/{user.username}")]]
            )

        await client.send_message(
            chat_id=group_id,
            text=goodbye_message,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except FloodWait as e:
        import asyncio
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"حدث خطأ في إرسال رسالة المغادرة: {e}")


# ========== أحداث المكالمة الصوتية ==========
@app.on_message(filters.video_chat_started, group=812)
async def call_started(client: Client, message: Message):
    await message.reply_text("<b>↵ تم بدء المكالمة الصوتية</b>")


@app.on_message(filters.video_chat_ended, group=813)
async def call_ended(client: Client, message: Message):
    await message.reply_text("<b>↵ تم إنهاء المكالمة الصوتية</b>")


@app.on_message(filters.video_chat_members_invited, group=814)
async def members_invited(client: Client, message: Message):
    text = f"<b>• قـام: {message.from_user.mention}\n• بـدعـوه : </b>"
    for user in message.video_chat_members_invited.users:
        try:
            text += f"<a href=\"tg://user?id={user.id}\">{user.first_name}</a> "
        except Exception:
            pass
    try:
        await message.reply_text(text)
    except Exception:
        pass