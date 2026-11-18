# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import asyncio
import random
import time
from collections import defaultdict

from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaPhoto, InputMediaVideo, Message

from anony import app, config, db

# ✅ set بدل list (أسرع + يمنع التكرار)
active_chats: set = set()

MIN_MENTIONS = 15
MAX_MENTIONS = 35
MIN_DELAY = 2.0
MAX_DELAY = 5.0
album_buffer = defaultdict(list)
album_lock = asyncio.Lock()


def extract_media(message: Message):
    if message.photo:
        return "photo", message.photo.file_id
    if message.video:
        return "video", message.video.file_id
    if message.animation:
        return "animation", message.animation.file_id
    if message.audio:
        return "audio", message.audio.file_id
    if message.voice:
        return "voice", message.voice.file_id
    if message.document:
        return "document", message.document.file_id
    if message.video_note:
        return "video_note", message.video_note.file_id
    if message.sticker:
        return "sticker", message.sticker.file_id
    return None, None


async def send_tag_message(
    client, chat_id, media_data, counter, body, mentions, reply_to=None
):
    text = f"{counter} - {body}\n{mentions}" if body else f"{counter}\n{mentions}"

    try:
        if media_data is None:
            await client.send_message(chat_id, text, reply_to_message_id=reply_to)
            return True

        media_type = media_data[0]
        file_id = media_data[1]

        if media_type == "album":
            media_list = []
            for i, (mtype, fid) in enumerate(file_id):
                caption = text if i == 0 else ""
                if mtype == "photo":
                    media_list.append(InputMediaPhoto(media=fid, caption=caption))
                elif mtype == "video":
                    media_list.append(InputMediaVideo(media=fid, caption=caption))

            if media_list:
                await client.send_media_group(
                    chat_id, media=media_list, reply_to_message_id=reply_to
                )
                if not media_list[0].caption:
                    await client.send_message(chat_id, text)
            return True

        caption_supported = {"photo", "video", "animation", "audio", "document"}
        if media_type in caption_supported:
            if media_type == "photo":
                await client.send_photo(
                    chat_id, photo=file_id, caption=text, reply_to_message_id=reply_to
                )
            elif media_type == "video":
                await client.send_video(
                    chat_id, video=file_id, caption=text, reply_to_message_id=reply_to
                )
            elif media_type == "animation":
                await client.send_animation(
                    chat_id, animation=file_id, caption=text, reply_to_message_id=reply_to
                )
            elif media_type == "audio":
                await client.send_audio(
                    chat_id, audio=file_id, caption=text, reply_to_message_id=reply_to
                )
            elif media_type == "document":
                await client.send_document(
                    chat_id, document=file_id, caption=text, reply_to_message_id=reply_to
                )
        else:
            if media_type == "voice":
                await client.send_voice(chat_id, voice=file_id, reply_to_message_id=reply_to)
            elif media_type == "video_note":
                await client.send_video_note(
                    chat_id, video_note=file_id, reply_to_message_id=reply_to
                )
            elif media_type == "sticker":
                await client.send_sticker(
                    chat_id, sticker=file_id, reply_to_message_id=reply_to
                )
            await client.send_message(chat_id, text)

        return True
    except FloodWait as e:
        wait_time = e.value
        print(f"[FloodWait] {wait_time}s")
        if wait_time < 300:
            await asyncio.sleep(wait_time)
            return await send_tag_message(
                client, chat_id, media_data, counter, body, mentions, reply_to
            )
        return False
    except Exception as e:
        print(f"[Send Error] {e}")
        return False


async def run_tag(client, chat_id, media_data, txt_body, reply_to):
    active_chats.add(chat_id)
    counter = 0
    mention_buffer = ""
    current_batch_target = random.randint(MIN_MENTIONS, MAX_MENTIONS)
    start_time = time.time()
    tagged_users = set()

    try:
        async for member in client.get_chat_members(chat_id):
            if chat_id not in active_chats:
                break
            if member.user.is_deleted or member.user.is_bot:
                continue
            if member.user.id in tagged_users:
                continue

            tagged_users.add(member.user.id)
            counter += 1
            mention_buffer += f" {member.user.mention} ›"

            if counter % current_batch_target == 0:
                await send_tag_message(
                    client, chat_id, media_data, counter, txt_body, mention_buffer, reply_to
                )
                mention_buffer = ""
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                current_batch_target = random.randint(MIN_MENTIONS, MAX_MENTIONS)

        if mention_buffer and chat_id in active_chats:
            await send_tag_message(
                client, chat_id, media_data, counter, txt_body, mention_buffer, reply_to
            )

        if chat_id in active_chats:
            await client.send_message(
                chat_id, "<b>• انتهى التاك بنجاح</b>"
            )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if chat_id in active_chats:
            active_chats.discard(chat_id)


@app.on_message(filters.command(["@all", "تاك", "all"], ""), group=9089)
async def tag_all(client: Client, message: Message):
    chat_id = message.chat.id

    if chat_id in active_chats:
        return await message.reply_text("<b>تـاك قـيد تشـغيل\n༄</b>")

    try:
        check = await client.get_chat_member(chat_id, message.from_user.id)
    except Exception:
        return

    if check.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply("<b>هذا الامر يخص ❪ الادمن وفوق ❫ بس\n༄</b>")

    if message.media_group_id:
        async with album_lock:
            album_buffer[message.media_group_id].append(message)
        await asyncio.sleep(1.5)

        async with album_lock:
            messages = album_buffer.pop(message.media_group_id, [])

        if not messages:
            return

        messages.sort(key=lambda m: m.id)
        album_media = []
        for msg in messages:
            mtype, fid = extract_media(msg)
            if mtype in ("photo", "video"):
                album_media.append((mtype, fid))

        txt_body = messages[0].caption or ""
        for keyword in ("@all", "تاك", "all"):
            txt_body = txt_body.replace(keyword, "")
        txt_body = " ".join(w for w in txt_body.split() if not w.isdigit()).strip()

        reply_to = (
            messages[0].reply_to_message.id if messages[0].reply_to_message else None
        )

        if len(album_media) > 1:
            media_data = ("album", album_media)
        elif len(album_media) == 1:
            media_data = album_media[0]
        else:
            media_data = None
    else:
        media_type, file_id = extract_media(message)

        txt_body = message.text or message.caption or ""
        for keyword in ("@all", "تاك", "all"):
            txt_body = txt_body.replace(keyword, "")
        txt_body = " ".join(w for w in txt_body.split() if not w.isdigit()).strip()

        reply_to = message.reply_to_message.id if message.reply_to_message else None

        if media_type:
            media_data = (media_type, file_id)
        else:
            media_data = None

    await message.reply_text("<b>جـاري بـدء تـاك\nاضغط /cancel لايقـافه</b>")
    await run_tag(client, chat_id, media_data, txt_body, reply_to)


@app.on_message(filters.command("/cancel", "بس منشن"), group=7666)
async def cancel_tag(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        check = await client.get_chat_member(chat_id, message.from_user.id)
    except Exception:
        return
    if check.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await message.reply("<b>هذا الامر يخص ❪ الادمن وفوق ❫ بس\n༄</b>")

    if chat_id in active_chats:
        active_chats.discard(chat_id)
        await message.reply_text("<b>✅ تـم ايـقاف التـاك</b>")
    else:
        await message.reply_text("<b>❌ لا يوجد تاك قيد التشغيل</b>")