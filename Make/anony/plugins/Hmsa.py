# ============================================================
#  Hmsa.py — نظام الهمسات الكامل (محسّن + مجهول ذكي)
#  - همسه بالرد على شخص
#  - همسه بالمعرف @username
#  - همسه مجهولة (خاص البوت) مع ذكاء في التوصيل:
#       • إذا المستلم بدأ البوت -> همسة في الخاص (مجهولة تماماً)
#       • إذا المستلم في مجموعة مشتركة فقط -> منشن في المجموعة
#         بدون كشف اسم المرسل
#  - يدعم: نص / صوت / فيديو / صورة / ستيكر / مميز / متحرك /
#          فيديو نوت / ملف — مع أو بدون كابشن
#  - الأسماء قابلة للنقر (روابط مستخدم) كما هو مطلوب
#  - زر باسم المرسل أسفل رسالة الهمسة
# ============================================================

import re
import uuid
from datetime import datetime

from pyrogram import Client, filters, enums
from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from anony import app, db, lang, config

OWNER_ID = config.OWNER_ID
SUPPORT_CHANNEL = config.SUPPORT_CHANNEL
SUPPORT_CHAT = config.SUPPORT_CHAT
ONE_VIDEO_URL = config.ONE_VIDEO_URL


# ============================================================
#  التخزين
# ============================================================
waiting_users: dict[int, str] = {}
hmses: dict[str, dict] = {}
anonymous_pending: dict[int, dict] = {}


# ============================================================
#  أدوات مساعدة
# ============================================================
def user_link_html(user_id: int, name: str) -> str:
    """يبني رابط HTML لفتح محادثة المستخدم."""
    return f'<a href="tg://user?id={user_id}">{name}</a>'


def parse_payload(payload: str):
    """hms{from}to{to}in{chat} -> (from_id, to_id, in_id)"""
    try:
        to_id = int(payload.split("to")[-1].split("in")[0])
        from_id = int(payload.split("hms")[-1].split("to")[0])
        in_id = int(payload.split("in")[-1])
        return from_id, to_id, in_id
    except Exception:
        return None, None, None


def detect_media(message: Message):
    """يرجع (type, file_id, text)"""
    text = message.text or message.caption or ""

    if message.voice:
        return "voice", message.voice.file_id, text
    if message.audio:
        return "audio", message.audio.file_id, text
    if message.video:
        return "video", message.video.file_id, text
    if message.video_note:
        return "video_note", message.video_note.file_id, text
    if message.photo:
        return "photo", message.photo.file_id, text
    if message.sticker:
        if getattr(message.sticker, "is_premium", False) or getattr(
            message.sticker, "premium_animation", None
        ):
            return "premium_sticker", message.sticker.file_id, text
        return "sticker", message.sticker.file_id, text
    if message.animation:
        return "animation", message.animation.file_id, text
    if message.document:
        return "document", message.document.file_id, text
    if message.text:
        return "text", None, message.text
    return None, None, None


async def user_has_private_bot(user_id: int) -> bool:
    """هل المستخدم بدأ البوت (الخاص متاح)؟"""
    try:
        if await db.is_user(user_id):
            return True
    except Exception:
        pass

    try:
        test_msg = await app.send_message(user_id, "‏")
        await test_msg.delete()
        try:
            await db.add_user(user_id)
        except Exception:
            pass
        return True
    except Exception:
        return False


async def find_common_group(user_id: int):
    """يرجع أول مجموعة مشتركة مع البوت، أو None."""
    try:
        common = await app.get_common_chats(user_id)
        for chat in common:
            if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                return chat
    except Exception:
        pass

    try:
        all_chats = await db.get_chats()
    except Exception:
        all_chats = []

    for chat_id in all_chats:
        try:
            member = await app.get_chat_member(chat_id, user_id)
            if member.status not in (
                enums.ChatMemberStatus.LEFT,
                enums.ChatMemberStatus.BANNED,
            ):
                chat = await app.get_chat(chat_id)
                if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                    return chat
        except Exception:
            continue

    return None


async def send_media_to_private(
    user_id: int, media_type: str, file_id, caption: str = None, reply_markup=None
):
    """إرسال ميديا في الخاص — مع كابشن HTML وزر إن وُجد."""
    kwargs = {}
    if caption:
        kwargs["caption"] = caption
        kwargs["parse_mode"] = ParseMode.HTML
    if reply_markup:
        kwargs["reply_markup"] = reply_markup

    if media_type == "voice":
        await app.send_voice(user_id, file_id, **kwargs)
    elif media_type == "audio":
        await app.send_audio(user_id, file_id, **kwargs)
    elif media_type == "video":
        await app.send_video(user_id, file_id, **kwargs)
    elif media_type == "video_note":
        await app.send_video_note(user_id, file_id)
        if caption or reply_markup:
            extra = {}
            if caption:
                extra["parse_mode"] = ParseMode.HTML
            if reply_markup:
                extra["reply_markup"] = reply_markup
            await app.send_message(user_id, caption or "‏", **extra)
    elif media_type == "photo":
        await app.send_photo(user_id, file_id, **kwargs)
    elif media_type in ("sticker", "premium_sticker"):
        await app.send_sticker(user_id, file_id)
        if caption or reply_markup:
            extra = {}
            if caption:
                extra["parse_mode"] = ParseMode.HTML
            if reply_markup:
                extra["reply_markup"] = reply_markup
            await app.send_message(user_id, caption or "‏", **extra)
    elif media_type == "animation":
        await app.send_animation(user_id, file_id, **kwargs)
    elif media_type == "document":
        await app.send_document(user_id, file_id, **kwargs)


# ============================================================
#  1) همسه بالرد  أو  همسه بالمعرف @username  (في المجموعة)
#     — الاسم قابل للنقر (يفتح محادثة المستخدم)
# ============================================================
@app.on_message(filters.group & filters.regex("^همسه"), group=579)
async def reply_with_link(client: Client, message: Message):
    # --- همسه بالرد ---
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user

        # منع الهمسة للبوتات
        if getattr(target, "is_bot", False):
            await message.reply_text("⚠️ لا يمكن إرسال همسة لبوت.")
            return

        # منع الهمسة للنفس
        if target.id == message.from_user.id:
            await message.reply_text("⚠️ لا يمكنك إرسال همسة لنفسك.")
            return

        start_link = (
            f"https://t.me/{app.username}"
            f"?start=hms{message.from_user.id}to{target.id}in{message.chat.id}"
        )
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "꙳. ارسل همستك .꙳",
                url=start_link,
                style=enums.ButtonStyle.PRIMARY,
            )]]
        )
        # الاسم كرابط مستخدم قابل للنقر
        target_link = user_link_html(target.id, target.first_name or "المستخدم")
        await message.reply_text(
            f"\n« ارسل الهمسه إلى {target_link} من هنا »\n",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        return

    # --- همسه بالمعرف @username ---
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        username = parts[1].strip().lstrip("@")
        try:
            target = await app.get_users(username)
        except Exception:
            await message.reply_text("⚠️ لم أجد هذا المستخدم، تأكد من المعرف.")
            return

        # منع الهمسة للبوتات
        if getattr(target, "is_bot", False):
            await message.reply_text("⚠️ لا يمكن إرسال همسة لبوت.")
            return

        # منع الهمسة للنفس
        if target.id == message.from_user.id:
            await message.reply_text("⚠️ لا يمكنك إرسال همسة لنفسك.")
            return

        start_link = (
            f"https://t.me/{app.username}"
            f"?start=hms{message.from_user.id}to{target.id}in{message.chat.id}"
        )
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "꙳. ارسل همستك .꙳",
                url=start_link,
                style=enums.ButtonStyle.PRIMARY,
            )]]
        )
        target_link = user_link_html(target.id, target.first_name or "المستخدم")
        await message.reply_text(
            f"\n« ارسل الهمسه إلى {target_link} من هنا »\n",
            reply_markup=markup,
            parse_mode=ParseMode.HTML,
        )
        return

    await message.reply_text(
        "» استخدم: همسه بالرد على شخص، أو همسه @username",
    )


# ============================================================
#  2) همسه مجهولة — بدء من الخاص
# ============================================================
@app.on_message(filters.private & filters.regex("^همسه"), group=578)
async def anonymous_start(client: Client, message: Message):
    if message.text.startswith("/"):
        return

    match = re.search(r"@([A-Za-z0-9_]{5,32})", message.text)
    if not match:
        await message.reply_text(
            "» استخدم: همسه @username أو همسه مجهوله @username\n"
            "أو همسه بالرد على شخص في مجموعة.",
        )
        return

    username = match.group(1)

    try:
        target = await app.get_users(username)
    except Exception:
        await message.reply_text(
            f"⚠️ لم أجد المستخدم @{username}. تأكد من المعرف.",
        )
        return

    if target.id == message.from_user.id:
        await message.reply_text("⚠️ لا يمكنك إرسال همسة لنفسك.")
        return
    if getattr(target, "is_bot", False):
        await message.reply_text("⚠️ لا يمكن إرسال همسة لبوت.")
        return

    anonymous_pending[message.from_user.id] = {
        "target_id": target.id,
        "target_name": target.first_name or "مجهول",
        "target_username": target.username,
        "common_group_id": None,
        "common_group_title": None,
    }

    target_link = user_link_html(target.id, target.first_name or "المستخدم")
    await message.reply_text(
        f"« أرسل الهمسه الآن إلى {target_link} »\n"
        "سيتم توصيلها في الخاص إن أمكن، وإلا سيتم منشنه في مجموعة مشتركة.\n"
        "يمكنك إرسال: نص / صوت / فيديو / صورة / ستيكر / متحرك / ملف",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "˹✘˼ إلغاء",
                callback_data="anon_cancel",
                style=enums.ButtonStyle.DANGER,
            )]]
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
#  3) /start مع hms -> فتح جلسة انتظار (همسة عادية)
# ============================================================
@app.on_message(filters.command("start") & filters.private, group=5790)
async def hms_start(client: Client, message: Message):
    payload = message.text.split(" ", 1)[-1] if " " in message.text else ""

    if payload.startswith("hms"):
        # التحقق من صحة البيانات: منع الهمسة للنفس أو للبوت
        from_id, to_id, in_id = parse_payload(payload)

        if from_id is None or to_id is None or in_id is None:
            await message.reply_text("⚠️ رابط الهمسة غير صالح.")
            return

        # منع غير صاحب الأمر من ضغط الزر
        if message.from_user.id != from_id:
            await message.reply_text(
                "⚠️ هذا الرابط ليس لك. اطلب همستك بنفسك من المجموعة."
            )
            return

        # منع الهمسة للنفس
        if to_id == message.from_user.id:
            await message.reply_text("⚠️ لا يمكنك إرسال همسة لنفسك.")
            return

        # منع الهمسة للبوت
        try:
            target = await app.get_users(to_id)
            if getattr(target, "is_bot", False):
                await message.reply_text("⚠️ لا يمكن إرسال همسة لبوت.")
                return
        except Exception:
            pass

        waiting_users[message.from_user.id] = payload
        await message.reply_text(
            "« أرسل الهمسه الآن »\n"
            "يمكنك إرسال: نص / صوت / فيديو / صورة / ستيكر / مميز / متحرك / ملف",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    "˹✘˼ إلغاء",
                    callback_data="hms_cancel",
                    style=enums.ButtonStyle.DANGER,
                )]]
            ),
        )

# ============================================================
#  4) استقبال الهمسة (كل الوسائط + النص)
# ============================================================
@app.on_message(
    filters.private
    & ~filters.command("start")
    & (
        filters.text
        | filters.audio
        | filters.voice
        | filters.video
        | filters.video_note
        | filters.photo
        | filters.sticker
        | filters.animation
        | filters.document
    ),
    group=576,
)
async def send_hms(client: Client, message: Message):
    uid = message.from_user.id

    # ============ همسة مجهولة ============
    if uid in anonymous_pending:
        info = anonymous_pending[uid]
        target_id = info["target_id"]
        target_name = info["target_name"]
        target_username = info.get("target_username")

        media_type, file_id, text = detect_media(message)
        if media_type is None:
            await message.reply_text("⚠️ نوع الوسيط غير مدعوم.")
            return

        # ==== جرّب الخاص أولاً ====
        sent_private = False
        try:
            if media_type == "text":
                await app.send_message(
                    target_id,
                    f"💌 همسة مجهولة:\n\n{text}\n\n🕵️ المرسل غير معروف.",
                )
            else:
                await send_media_to_private(target_id, media_type, file_id, text)
                await app.send_message(
                    target_id,
                    "🕵️ هذه همسة مجهولة، المرسل غير معروف.",
                )
            sent_private = True
        except Exception:
            sent_private = False

        if sent_private:
            try:
                await db.add_user(target_id)
            except Exception:
                pass
            await message.reply_text("✅ تم إرسال همستك المجهولة بنجاح (في الخاص).")
            anonymous_pending.pop(uid, None)
            return

        # ==== فشل الخاص -> ابحث عن مجموعة مشتركة ====
        group_id = info.get("common_group_id")
        if not group_id:
            group_chat = await find_common_group(target_id)
            if group_chat:
                group_id = group_chat.id
                info["common_group_id"] = group_id
                info["common_group_title"] = group_chat.title

        if not group_id:
            await message.reply_text(
                "⚠️ تعذر توصيل الهمسة: المستخدم لم يبدأ البوت، "
                "ولم أجد مجموعة مشتركة بينكما."
            )
            anonymous_pending.pop(uid, None)
            return

        # ==== إرسال في المجموعة مع منشن ====
        if target_username:
            mention = f"@{target_username}"
        else:
            mention = user_link_html(target_id, target_name)

        try:
            if media_type == "text":
                await app.send_message(
                    group_id,
                    f"💌 همسة مجهولة لـ {mention}:\n\n{text}\n\n🕵️ المرسل غير معروف.",
                    parse_mode=ParseMode.HTML,
                )
            else:
                caption_base = text or ""
                caption = (
                    f"💌 همسة مجهولة لـ {mention}"
                    + (f"\n\n{caption_base}" if caption_base else "")
                )

                if media_type == "voice":
                    await app.send_voice(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type == "audio":
                    await app.send_audio(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type == "video":
                    await app.send_video(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type == "video_note":
                    await app.send_video_note(group_id, file_id)
                    await app.send_message(
                        group_id,
                        f"💌 همسة مجهولة لـ {mention}\n🕵️ المرسل غير معروف.",
                        parse_mode=ParseMode.HTML,
                    )
                elif media_type == "photo":
                    await app.send_photo(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type in ("sticker", "premium_sticker"):
                    await app.send_sticker(group_id, file_id)
                    await app.send_message(
                        group_id,
                        f"💌 همسة مجهولة لـ {mention}"
                        + (f"\n\n{caption_base}" if caption_base else "")
                        + "\n🕵️ المرسل غير معروف.",
                        parse_mode=ParseMode.HTML,
                    )
                elif media_type == "animation":
                    await app.send_animation(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
                elif media_type == "document":
                    await app.send_document(group_id, file_id, caption=caption, parse_mode=ParseMode.HTML)

                if media_type not in ("video_note", "sticker", "premium_sticker"):
                    await app.send_message(
                        group_id,
                        "🕵️ هذه همسة مجهولة، المرسل غير معروف.",
                    )

            await message.reply_text("✅ تم إرسال همستك المجهولة بنجاح (في المجموعة).")
        except Exception as e:
            await message.reply_text(f"⚠️ تعذر إرسال الهمسة في المجموعة: {e}")

        anonymous_pending.pop(uid, None)
        return

    # ============ همسة عادية ============
    if uid not in waiting_users:
        return

    payload = waiting_users[uid]
    from_id, to_id, in_id = parse_payload(payload)

    if not to_id or not in_id:
        await message.reply_text("⚠️ حدث خطأ في بيانات الهمسة، أعد المحاولة.")
        waiting_users.pop(uid, None)
        return

    # التحقق: المرسل نفسه، وليس نفس المستلم، وليس بوت
    if from_id != uid:
        await message.reply_text("⚠️ هذه الهمسة ليست لك.")
        waiting_users.pop(uid, None)
        return

    if to_id == from_id:
        await message.reply_text("⚠️ لا يمكنك إرسال همسة لنفسك.")
        waiting_users.pop(uid, None)
        return

    try:
        target_user = await app.get_users(to_id)
        if getattr(target_user, "is_bot", False):
            await message.reply_text("⚠️ لا يمكن إرسال همسة لبوت.")
            waiting_users.pop(uid, None)
            return
    except Exception:
        pass

    media_type, file_id, text = detect_media(message)
    if media_type is None:
        await message.reply_text("⚠️ نوع الوسيط غير مدعوم.")
        return

    hms_id = uuid.uuid4().hex[:16]
    hmses[hms_id] = {
        "from_id": from_id,
        "from_name": message.from_user.first_name or "مجهول",
        "to_id": to_id,
        "in_id": in_id,
        "type": media_type,
        "file_id": file_id,
        "text": text,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "anonymous": False,
    }

    await message.reply_text("✅ تم إرسال الهمسة بنجاح")

    # أسماء قابلة للنقر
    try:
        target = await app.get_users(to_id)
        target_name = target.first_name or "المستلم"
    except Exception:
        target_name = "المستلم"

    to_link = user_link_html(to_id, target_name)
    from_link = user_link_html(from_id, message.from_user.first_name or "مجهول")

    header = (
        f"<b>⭓ ᴍᴜꜱɪᴄ ✘ ᴠᴇɢᴧ ♪\n"
        f"╮⦿ هذه الهمسه لك: {to_link}\n"
        f"╯⦿ من هذا الشخص: {from_link}</b>"
    )

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "꙳. افتح الهمسة .꙳",
                callback_data=f"hms_answer:{hms_id}",
                style=enums.ButtonStyle.PRIMARY,
            )],
            [InlineKeyboardButton(
                "꙳. ᴠᴇɢᴧ .꙳",
                url=SUPPORT_CHANNEL,
                style=enums.ButtonStyle.DANGER,
            )],
        ]
    )

    try:
        await app.send_message(in_id, header, reply_markup=markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"[HMS NOTIFY ERROR] {e}")

    waiting_users.pop(uid, None)


# ============================================================
#  5) زر "افتح"
#     - الميديا تُرسل مع كابشن يحتوي اسم المرسل كرابط قابل للنقر
#     - وزر باسم المرسل أسفل الرسالة
# ============================================================
@app.on_callback_query(filters.regex(r"^hms_answer:"), group=5766565)
async def display_hms(client: Client, callback: CallbackQuery):
    hms_id = callback.data.split(":", 1)[1]
    who_id = callback.from_user.id

    data = hmses.get(hms_id)
    if not data:
        await callback.answer("» هذه الهمسة لم تعد متاحة أو تم حذفها «", show_alert=True)
        return

    if str(data["to_id"]) != str(who_id):
        await callback.answer("» حجي هذه لا تخصك انلقع «", show_alert=True)
        return

    # ==== همسة نصية فقط -> alert ====
    if data["type"] == "text":
        text = data.get("text") or "—"
        if len(text) > 200:
            text = text[:197] + "..."
        await callback.answer(text, show_alert=True)
        hmses.pop(hms_id, None)
        return

    # ==== ميديا -> إرسال في الخاص ====
    try:
        await app.get_users(who_id)
    except Exception:
        await callback.answer(
            "⚠️ ابدأ البوت في الخاص أولاً ثم اضغط فتح", show_alert=True
        )
        return

    await callback.answer("📩 جاري إرسال الهمسة في الخاص...")

    from_id = data.get("from_id")
    from_name = data.get("from_name") or "مجهول"
    date_str = data.get("date", "")
    caption_text = (data.get("text") or "").strip()

    # بناء اسم المرسل كرابط قابل للنقر (يفتح محادثته)
    from_link = user_link_html(from_id, from_name) if from_id else from_name

    # بناء الكابشن: النص (إن وُجد) + اسم المرسل (قابل للنقر) + التاريخ
    parts = []
    if caption_text:
        parts.append(caption_text)
    parts.append(f"👤 من: {from_link}")
    if date_str:
        parts.append(f"🕐 {date_str}")
    full_caption = "\n\n".join(parts)

    # زر باسم المرسل أسفل الرسالة
    reply_markup = None
    if from_id:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                f"👤 {from_name}",
                url=f"tg://user?id={from_id}",
                style=enums.ButtonStyle.PRIMARY,
            )]]
        )

    try:
        await send_media_to_private(
            who_id, data["type"], data["file_id"], full_caption, reply_markup
        )
    except Exception as e:
        try:
            await app.send_message(who_id, f"⚠️ تعذر إرسال الهمسة: {e}")
        except Exception:
            pass

    hmses.pop(hms_id, None)


# ============================================================
#  6) زر الإلغاء
# ============================================================
@app.on_callback_query(filters.regex("^hms_cancel$"), group=57967)
async def cancel_hms(client: Client, callback: CallbackQuery):
    waiting_users.pop(callback.from_user.id, None)
    try:
        await callback.message.edit_text("🗑 تم إلغاء الهمسه بنجاح")
    except Exception:
        await callback.answer("تم الإلغاء")


@app.on_callback_query(filters.regex("^anon_cancel$"), group=57968)
async def cancel_anon(client: Client, callback: CallbackQuery):
    anonymous_pending.pop(callback.from_user.id, None)
    try:
        await callback.message.edit_text("🗑 تم إلغاء الهمسه المجهولة")
    except Exception:
        await callback.answer("تم الإلغاء")