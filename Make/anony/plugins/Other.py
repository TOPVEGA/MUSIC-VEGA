import os
import io
import time
import asyncio
import aiohttp
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    LinkPreviewOptions,
)
from PIL import Image, ImageDraw

import os
import random
import requests
import asyncio
import html
import io
import logging
import time
from datetime import datetime
from pytz import timezone

from PIL import Image, ImageDraw

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message,
    InputMediaPhoto
)
from pyrogram.enums import ParseMode, ChatType, ChatMembersFilter, ChatMemberStatus
from pyrogram.errors import FloodWait

from anony import app, db, lang, config
from anony.helpers.admins import is_owner, banned_check, admin_check, is_admin


# ========== المتغيرات العامة ==========
BOT_TOKEN = config.BOT_TOKEN
OWNER_ID = config.OWNER_ID
SUPPORT_CHANNEL = config.SUPPORT_CHANNEL
SUPPORT_CHAT = config.SUPPORT_CHAT


_USE_RICH_MESSAGE = True
_RICH_TIMEOUT = 60

user_photos_cache = {}
_PHOTOS_TTL = 300

# ✅ خيارات تعطيل معاينة الروابط (بديل disable_web_page_preview في Pyrogram الحديث)
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


def safe_mention(user) -> str:
    first_name = getattr(user, "first_name", None) or "مستخدم"
    return f'<a href="tg://user?id={user.id}">{first_name}</a>'


def extract_file_id(obj):
    if obj is None:
        return None
    for attr in ("file_id", "big_file_id", "small_file_id"):
        fid = getattr(obj, attr, None)
        if fid:
            return fid
    return None


async def _fetch_user_photos(client, user_id, limit=10):
    photos = []
    try:
        async for photo in client.get_chat_photos(user_id, limit=limit):
            fid = extract_file_id(photo)
            if fid and fid not in photos:
                photos.append(fid)
    except Exception as e:
        print(f"[_fetch_user_photos] {e}")
    return photos


def draw_dots_on_image(image_bytes: bytes, total: int, current: int) -> bytes:
    if total <= 1:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        width, height = img.size
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        base_size = width // 100
        dot_radius = max(5, min(base_size, 12))
        inactive_radius = max(4, dot_radius - 2)
        dot_spacing = dot_radius * 4

        active_color = (255, 255, 255, 255)
        inactive_color = (255, 255, 255, 110)
        shadow_color = (0, 0, 0, 100)

        total_width = (total - 1) * dot_spacing
        start_x = (width - total_width) // 2
        center_y = height - (dot_radius * 4)

        for i in range(total):
            cx = start_x + (i * dot_spacing)
            cy = center_y
            if i == current:
                draw.ellipse(
                    [cx - dot_radius - 2, cy - dot_radius - 2,
                     cx + dot_radius + 2, cy + dot_radius + 2],
                    fill=shadow_color,
                )
                draw.ellipse(
                    [cx - dot_radius, cy - dot_radius,
                     cx + dot_radius, cy + dot_radius],
                    fill=active_color,
                )
            else:
                draw.ellipse(
                    [cx - inactive_radius - 1, cy - inactive_radius - 1,
                     cx + inactive_radius + 1, cy + inactive_radius + 1],
                    fill=shadow_color,
                )
                draw.ellipse(
                    [cx - inactive_radius, cy - inactive_radius,
                     cx + inactive_radius, cy + inactive_radius],
                    fill=inactive_color,
                )

        combined = Image.alpha_composite(img, overlay)
        final = Image.new("RGB", combined.size, (255, 255, 255))
        final.paste(combined, mask=combined.split()[3])
        output = io.BytesIO()
        final.save(output, format="JPEG", quality=92, optimize=True)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        print(f"خطأ في رسم النقاط: {e}")
        return image_bytes


async def send_rich_slideshow(
    chat_id: int,
    photo_file_ids: list[str],
    caption: str = "",
    buttons: list[dict] | None = None,
    reply_to_message_id: int | None = None,
) -> dict | None:
    global _USE_RICH_MESSAGE

    if not _USE_RICH_MESSAGE:
        return None
    if not photo_file_ids or len(photo_file_ids) < 2:
        return None

    photos = photo_file_ids[:10]

    media_payload = []
    slideshow_tags = ""
    for i, fid in enumerate(photos):
        mid = f"p{i}"
        media_payload.append({
            "id": mid,
            "media": {"type": "photo", "media": fid},
        })
        slideshow_tags += f'<img src="tg://photo?id={mid}"/>'

    rich_html = f"<tg-slideshow>{slideshow_tags}</tg-slideshow>"

    if caption:
        caption_html = caption.replace("\n", "<br/>")
        rich_html += f"<br/>{caption_html}"

    if buttons:
        btn_tags = ""
        for b in buttons:
            emoji_attr = (
                f' icon_custom_emoji_id="{b["emoji_id"]}"'
                if b.get("emoji_id") else ""
            )
            style = b.get("style", "primary")
            if b.get("url"):
                btn_tags += (
                    f'<tg-button url="{b["url"]}" style="{style}"{emoji_attr}>'
                    f'{b["text"]}'
                    f'</tg-button>'
                )
        if btn_tags:
            rich_html += f'<tg-button-row align="center">{btn_tags}</tg-button-row>'

    payload = {
        "chat_id": chat_id,
        "rich_message": {
            "html": rich_html,
            "media": media_payload,
        },
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
        payload["allow_sending_without_reply"] = True

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"

    try:
        timeout = aiohttp.ClientTimeout(
            total=_RICH_TIMEOUT, connect=15, sock_read=_RICH_TIMEOUT
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                text = await resp.text()
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    print(f"[rich] response not JSON: {text[:200]}")
                    return None

                if data.get("ok"):
                    print(f"[rich]  Sent to {chat_id}")
                    return data["result"]

                err_code = data.get("error_code")
                err_desc = data.get("description", "")
                print(f"[rich]  API {err_code}: {err_desc}")

                if err_code in (400, 404, 405):
                    _USE_RICH_MESSAGE = False
                    print("[rich]  sendRichMessage not supported → album mode")
                    return None

                return None
    except asyncio.TimeoutError:
        print(f"[rich] ⏱️ Timeout for {chat_id}")
        _USE_RICH_MESSAGE = False
        return None
    except Exception as e:
        print(f"[rich]  {e}")
        return None


async def send_rich_bot_message(
    chat_id: int,
    bar: str,
    bot_username: str,
    reply_to_message_id: int | None = None,
) -> dict | None:
    """
    إرسال رسالة غنية (Rich Message) مع زر RichMessageButton لفتح رابط إضافة البوت للمجموعة.
    """
    button_text = "أضفني"

    rich_html = (
        f"<p>{bar}</p>"
        f'<tg-button-row align="center">'
        f'<tg-button type="url" style="primary" '
        f'url="https://t.me/{bot_username}?startgroup=true">'
        f'{button_text}'
        f'</tg-button>'
        f'</tg-button-row>'
    )

    payload = {
        "chat_id": chat_id,
        "rich_message": {
            "html": rich_html,
        },
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
        payload["allow_sending_without_reply"] = True

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"

    try:
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json(content_type=None)
                if data.get("ok"):
                    print(f"[rich-bot] ✅ Sent to {chat_id}")
                    return data["result"]
                else:
                    print(
                        f"[rich-bot] ❌ API {data.get('error_code')}: "
                        f"{data.get('description')}"
                    )
                    return None
    except Exception as e:
        print(f"[rich-bot] ❌ Exception: {e}")
        return None


def build_id_keyboard(user_id: int, user_name: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(user_name, url=f"tg://user?id={user_id}")]
    ])


async def send_id_card(client, message, user_id, base_text, user_name):
    now = time.time()
    cached = user_photos_cache.get(user_id)
    if cached and (now - cached[0]) < _PHOTOS_TTL:
        photos = cached[1]
    else:
        photos = await _fetch_user_photos(client, user_id, limit=10)
        user_photos_cache[user_id] = (now, photos)

    kb = build_id_keyboard(user_id, user_name)

    # 1) محاولة السلايدر الغني (Rich Message) مع reply
    if len(photos) >= 2 and _USE_RICH_MESSAGE:
        try:
            res = await send_rich_slideshow(
                chat_id=message.chat.id,
                photo_file_ids=photos,
                caption=base_text,
                buttons=[{
                    "text": user_name,
                    "url": f"tg://user?id={user_id}",
                    "style": "primary",
                }],
                reply_to_message_id=message.id,
            )
            if res:
                return res
            print(f"[rich]  فشل السلايدر — تحويل للألبوم")
        except Exception as e:
            print(f"[rich]  {e}")

    # 2) ألبوم عادي مع quote=True (الرد على رسالة المستخدم)
    if len(photos) >= 2:
        try:
            media_list = []
            for i, fid in enumerate(photos[:10]):
                media_list.append(
                    InputMediaPhoto(
                        fid,
                        caption=base_text if i == 0 else None,
                        parse_mode=ParseMode.HTML,
                    )
                )
            msgs = await message.reply_media_group(
                media=media_list,
                quote=True,
            )
            await message.reply_text(
                "•",
                reply_markup=kb,
                quote=True,
            )
            return {"message_id": msgs[0].id}
        except Exception as e:
            print(f"[album]  {e}")

    # 3) صورة واحدة مع quote=True
    if len(photos) == 1:
        try:
            return await message.reply_photo(
                photo=photos[0],
                caption=base_text,
                reply_markup=kb,
                parse_mode=ParseMode.HTML,
                quote=True,
            )
        except Exception as e:
            print(f"[photo]  {e}")

    # 4) نص فقط مع quote=True
    return await message.reply_text(
        base_text,
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
        link_preview_options=NO_PREVIEW,
        quote=True,
    )


@app.on_message(
    filters.command(["ايدي", "الايدي", "ا", "id", "/id", "/ID"], ""),
    group=12,
)
async def user_id(client, message):
    user = message.from_user
    chat = message.chat

    base_text = f"""<b>• الاسم: <a href="tg://user?id={user.id}">{user.first_name}</a>
• المعرف: @{user.username or 'لا يوجد'}
• الايدي: <code>{user.id}</code>
• الدردشه: {chat.title or 'خاص'}
• ايدي الدردشه: <code>{chat.id}</code></b>
ㅤ"""

    return await send_id_card(
        client, message, user.id, base_text, user.first_name
    )


OWNER_ID = config.OWNER_ID
SUPPORT_CHANNEL = config.SUPPORT_CHANNEL
SUPPORT_CHAT = config.SUPPORT_CHAT

CURRENT_OWNER_ID = OWNER_ID
group_locks = {}
bot_name_cache = {}


# ========== دوال مساعدة ==========
def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "sticker",
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj


# ========== قائمة الردود التلقائية للبوت ==========
KEEMO_RESPONSES = [
    "هاها {name} أنت مين 😂",
    "شخبارك {name} يالغبي 🐸",
    "أهلاً وسهلاً بك {name} 🤍",
    "تشرفنا {name} نورت 🫡",
    "شو بدك {name} بدي أعملك بلوك 😤",
    "خر {name} تعبت من نداءك 💢",
    "{name} طلعت حمار 😂🐴",
    "هاي {name} أنت بتعرف تحكي أصلن 🤪",
    "أمرني {name} أنا معاك 🤍",
    "{name} معاك لحد الآخر 🔥"
]


# ========== أوامر المطور ==========
@app.on_message(filters.command(["المطور", "مطور", "مطور البوت", "/dev"], ""), group=1)
@banned_check
async def devbots(client: Client, message: Message):
    global CURRENT_OWNER_ID
    dev_id = CURRENT_OWNER_ID if CURRENT_OWNER_ID else OWNER_ID
    user = await client.get_chat(dev_id)
    name = user.first_name
    username = user.username
    bio = user.bio
    user_id_val = user.id

    try:
        chat_title = f"• اسم: {message.from_user.mention}\n• اسم الدردشة: {message.chat.title}" if message.from_user else f"• اسم الدردشة: {message.chat.title}\nㅤ"
        link = f"https://t.me/{message.chat.username}" if message.chat.username else f"https://t.me/{message.chat.id}"
        await client.send_message(
            dev_id,
            f"• عزيزي المطور هناك شخص يريدك\n{chat_title}\n• معرف الدردشة: {message.chat.id}\nㅤ",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{message.chat.title if message.chat.title else 'الدردشة'}", url=f"{link}")]])
        )
    except:
        pass

    base_text = f"""<b>• الاسم: {name}
• المعرف: @{username if username else 'لا يوجد'}
• الايدي: <code>{user_id_val}</code>
• البايو: {bio if bio else 'لا يوجد'}</b>
ㅤ"""

    return await send_id_card(client, message, user_id_val, base_text, name)


@app.on_message(filters.command("تغير المطور", "") & filters.private, group=2)
@banned_check
@is_owner
async def change_dev(client: Client, message: Message):
    global CURRENT_OWNER_ID
    try:
        msg = await client.ask(
            chat_id=message.chat.id,
            text="•  أرسل المعرف أو الأيدي الخاص بالمطور الجديد:",
            timeout=60,
            filters=filters.user(message.from_user.id)
        )

        if not msg.text:
            return await message.reply_text("• يجب إرسال معرف أو أيدي صالح", quote=True)
        new_dev = msg.text.strip()
        if new_dev.startswith("@"):
            user = await client.get_users(new_dev)
        else:
            user = await client.get_users(int(new_dev))

        CURRENT_OWNER_ID = user.id

        await message.reply_text(
            f"• تم تغيير المطور بنجاح\n"
            f"• المطور الجديد: {user.mention}\n"
            f"• الأيدي:<code> {user.id}</code>\n"
            f"• المعرف: @{user.username if user.username else 'لا يوجد'}",
            quote=True,
        )
    except ValueError:
        await message.reply_text("• يجب أن يكون الأيدي أرقام فقط", quote=True)
    except Exception as e:
        await message.reply_text(f"• لم أتمكن من تغيير المطور: {str(e)}", quote=True)


@app.on_message(filters.command(["حذف المطور"], "") & filters.private, group=3)
@banned_check
@is_owner
async def delete_dev(client: Client, message: Message):
    global CURRENT_OWNER_ID

    if CURRENT_OWNER_ID is None or str(CURRENT_OWNER_ID) == str(OWNER_ID):
        return await message.reply_text(
            "• لا يوجد مطور إضافي ليتم حذفه\n• المطور الحالي هو المطور الأساسي الافتراضي",
            quote=True,
        )

    try:
        current_dev = await client.get_chat(CURRENT_OWNER_ID)
        default_dev = await client.get_chat(OWNER_ID)
        dev_name = current_dev.first_name
        dev_id = current_dev.id
        CURRENT_OWNER_ID = None
        await message.reply_text(
            f"• تم حذف المطور الإضافي بنجاح\n"
            f"• الاسم: {dev_name}\n"
            f"• الأيدي: <code>{dev_id}</code>\n\n"
            f"• تم الرجوع إلى المطور الأساسي:\n"
            f"• الاسم: {default_dev.first_name}\n"
            f"• الأيدي: {default_dev.id}",
            quote=True,
        )
    except Exception as e:
        await message.reply_text(f"• لم أتمكن من حذف المطور: {str(e)}", quote=True)


# ========== أمر المالك ==========
@app.on_message(filters.command(["المالك", "صاحب الخرابه", "المنشي"], "") & filters.group, group=13)
@banned_check
async def ownner(client: Client, message: Message):
    owner = None
    async for m in client.get_chat_members(message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if m.status == enums.ChatMemberStatus.OWNER:
            owner = m.user
            break
    if not owner:
        await message.reply_text("الحساب الخاص بالدردشة محذوف", quote=True)
        return

    base_text = f"""<b>• المالك: {owner.first_name}
• المعرف: @{owner.username or 'لا يوجد'}
• الايدي: <code>{owner.id}</code>
• الدردشه: {message.chat.title}
• ايدي الدردشه: <code>{message.chat.id}</code></b>
ㅤ"""

    return await send_id_card(client, message, owner.id, base_text, owner.first_name)


# ========== أمر الكشف ==========
@app.on_message(filters.command(["كشف", "مين دا", "الكشف"], "") & filters.group, group=14)
@banned_check
async def kassfggg(client, message):
    chat_id = message.chat.id
    if group_locks.get(chat_id, False):
        return await message.reply_text("الامر معطل من قبل الادمن", quote=True)

    if not message.reply_to_message:
        return

    target = message.reply_to_message.from_user

    base_text = f"""<b>• المستخدم: {target.mention}
• المعرف: @{target.username or 'لا يوجد'}
• الايدي: <code>{target.id}</code>
• الدردشه: {message.chat.title or 'خاص'}
• معرف الدردشه: @{message.chat.username or 'لا يوجد'}
• ايدي الدردشه: <code>{message.chat.id}</code></b>
ㅤ"""

    return await send_id_card(client, message, target.id, base_text, target.first_name)


# ========== أمر فوكس ==========
@app.on_message(filters.command(["/fox", "ꜰᴏx", "فوكس"], ""), group=15)
@banned_check
async def handle_uer_fox(client, message):
    try:
        user = await client.get_chat("devVega")
        name = user.first_name
        username = user.username if user.username else "لا يوجد"
        bio = user.bio if user.bio else "لا يوجد"

        base_text = (
            f"<b>ㅤ\n• الاسم : {name}\n"
            f"• المعرف : @{username}\n"
            f"• الايدي : <code>{user.id}</code>\n"
            f"• البايو : {bio}</b>\nㅤ"
        )

        return await send_id_card(client, message, user.id, base_text, name)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("حدث خطأ في جلب المعلومات", quote=True)


# ========== أمر كيمي (مبرمج السورس) ==========
@app.on_message(filters.command(["كيمي", "مطور فيجا", "صاحب سورس فيجا", "مبرمج السورس", "مطور السورس", "/kim", "KIM", "كيم", "مبرمج", "المبرمج"], ""), group=16)
@banned_check
async def handle_user_kim(client, message):
    command = message.text.split()[0].lower()
    if command in ["مطور", "مطور البوت", "المطور"]:
        return
    try:
        user = await client.get_chat("TopVeGa")
        name = user.first_name
        username = user.username if user.username else "لا يوجد"
        bio = user.bio if user.bio else "لا يوجد"

        base_text = (
            f"<b>ㅤ\n"
            f"• الاسم : {name}\n"
            f"• المعرف : @{username}\n"
            f"• الايدي : <code>{user.id}</code>\n"
            f"• البايو : {bio}</b>\n"
            f"• الرتبه : مؤسس النظام</b>\nㅤ"
        )

        return await send_id_card(client, message, user.id, base_text, name)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("حدث خطأ في جلب المعلومات", quote=True)


@app.on_message(filters.regex(r"تعين اسم البوت|set bot name") & filters.private, group=30)
async def set_bot_name(client, message):
    try:
        ask = await app.ask(message.chat.id, "ارسل الاسم الجديد للبوت", timeout=300)
        bot_name_cache['name'] = ask.text
        await message.reply_text(f"✅ تم تعيين الاسم {bot_name_cache['name']}", quote=True)
    except Exception as e:
        await message.reply_text(f"حدث خطأ: {e}", quote=True)


# ========== أوامر البوت التلقائية ==========
@app.on_message(filters.command(["بوت", "البوت", "بوتي", "بوتك", "/bot"], "") & filters.group, group=31)
@banned_check
async def bot_name_command(client, message):
    if 'name' not in bot_name_cache:
        me = await app.get_me()
        bot_name_cache['name'] = me.first_name
        bot_name_cache['username'] = me.username

    name = bot_name_cache['name']
    bot_username = bot_name_cache['username']

    bar = random.choice(KEEMO_RESPONSES).format(name=name)

    # ✅ محاولة إرسال Rich Message مع RichMessageButton
    rich_result = await send_rich_bot_message(
        chat_id=message.chat.id,
        bar=bar,
        bot_username=bot_username,
        reply_to_message_id=message.id,
    )
    if rich_result:
        return

    # 🔄 fallback: رسالة عادية مع InlineKeyboardMarkup
    print("[bot] RichMessage غير مدعوم → استخدام inline keyboard عادي")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "أضفني",
            url=f"https://t.me/{bot_username}?startgroup=true",
        )
    ]])

    await message.reply_text(
        bar,
        link_preview_options=NO_PREVIEW,
        reply_markup=keyboard,
        quote=True,
    )


@app.on_message(filters.text & filters.group, group=33)
async def bot_name_in_text(client, message):
    """
    يعمل عندما يكون اسم البوت داخل نص (مثل: 'يا بوت شخبارك')
    أو عندما يكون النص مطابقاً لاسم البوت (مع/بدون @).
    """
    if not message.text:
        return

    if 'name' not in bot_name_cache:
        me = await app.get_me()
        bot_name_cache['name'] = me.first_name
        bot_name_cache['username'] = me.username

    name = bot_name_cache['name']
    username = bot_name_cache['username']
    text = message.text.strip()

    # تجاهل الأوامر (/) حتى لا يتعارض مع الأوامر الأخرى
    if text.startswith("/"):
        return

    text_lower = text.lower()
    name_lower = name.lower()
    mentioned = False

    if text_lower == name_lower:
        mentioned = True
    elif username and f"@{username.lower()}" in text_lower:
        mentioned = True
    elif name_lower and name_lower in text_lower:
        mentioned = True

    if not mentioned:
        return

    bar = random.choice(KEEMO_RESPONSES).format(name=name)

    # ✅ محاولة إرسال Rich Message مع RichMessageButton
    rich_result = await send_rich_bot_message(
        chat_id=message.chat.id,
        bar=bar,
        bot_username=username,
        reply_to_message_id=message.id,
    )
    if rich_result:
        return

    # 🔄 fallback: رسالة عادية
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "أضفني",
            url=f"https://t.me/{username}?startgroup=true",
        )
    ]])

    await message.reply_text(
        bar,
        link_preview_options=NO_PREVIEW,
        reply_markup=keyboard,
        quote=True,
    )