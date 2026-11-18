# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import os
from pathlib import Path
import asyncio
from pyrogram import filters, types
from pyrogram.enums import MessageMediaType

from anony import anon, app, config, db, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers.play import checkUB
from anony.helpers.joins import must_join_ch
from anony.helpers.thumbnails import Thumbnail
from anony.helpers import Track
from anony.helpers.admins import is_owner, banned_check


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


# ==================== أوامر التشغيل الرئيسية ================
@app.on_message(
    filters.command(["/play", "شغل", "/vplay", "تشغيل", "فيديو"], "")
    & filters.group
    & ~app.bl_users, group=1
)
@lang.language()
@must_join_ch
@checkUB
@banned_check
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:

    if not await db.is_chat(m.chat.id):
        await db.add_chat(m.chat.id)
        
    await m.delete()
    sent = await m.reply_text("⚡")
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    try:
        thumb = Thumbnail()
        await thumb.start()
        thumb_path = await thumb.generate(file)
        await thumb.close()
    except Exception as e:
        print(f"خطأ في إنشاء صورة التشغيل: {e}")
        thumb_path = None

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration, thumb_path)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            if thumb_path and os.path.exists(thumb_path):
                try:
                    await sent.delete() 
                    sent = await app.send_photo(
                        chat_id=m.chat.id,
                        photo=thumb_path,
                        caption=m.lang["play_queued"].format(
                            position,
                            file.url,
                            file.title,
                            file.duration,
                            m.from_user.mention,
                        ),
                        reply_markup=buttons.play_queued(
                            m.chat.id, file.id, m.lang["play_now"]
                        ),
                        show_caption_above_media=True
                    )
                except Exception as e:
                    print(f"خطأ في إرسال الصورة: {e}")
                    await sent.edit_text(
                        m.lang["play_queued"].format(
                            position,
                            file.url,
                            file.title,
                            file.duration,
                            m.from_user.mention,
                        ),
                        reply_markup=buttons.play_queued(
                            m.chat.id, file.id, m.lang["play_now"]
                        ),
                        show_caption_above_media=True
                    )
            else:
                await sent.edit_text(
                    m.lang["play_queued"].format(
                        position,
                        file.url,
                        file.title,
                        file.duration,
                        m.from_user.mention,
                    ),
                    reply_markup=buttons.play_queued(
                        m.chat.id, file.id, m.lang["play_now"]
                    ),
                )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(file.id, video=video)

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )


# ==================== أوامر القنوات ====================

@app.on_message(
    filters.command(["/play", "شغل", "تشغيل", "/vplay", "فيديو", "ف"], "")
    & filters.channel
)
async def play_channel_handler(_, m: types.Message):
    from anony import lang
    try:
        lang_code = await db.get_lang(m.chat.id)
        lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    except:
        lang_dict = lang.languages.get("ar", {})
    
    chat_id = m.chat.id
    sent = await m.reply_text("⚡")

    if not await db.is_chat(m.chat.id):
        await db.add_chat(m.chat.id)
    
    if not await db.join_assistant_to_channel(chat_id, sent):
        return
    
    if not m.reply_to_message and (len(m.command) < 2):
        return await sent.edit_text(lang_dict["play_usage"])
    
    video = m.command[0][0] == "ف" and config.VIDEO_PLAY
    url = utils.get_url(m)
    mention = m.chat.title or "القناة"
    file = None
    tracks = []
    
    if url:
        if "playlist" in url:
            await sent.edit_text(lang_dict["playlist_fetch"])
            tracks = await yt.playlist(config.PLAYLIST_LIMIT, mention, url, video)
            if not tracks:
                return await sent.edit_text(lang_dict["playlist_error"])
            file = tracks[0]
            tracks.remove(file) if tracks else None
        else:
            file = await yt.search(url, sent.id, video=video)
    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
    
    if not file:
        return await sent.edit_text(lang_dict["play_not_found"].format(config.SUPPORT_CHAT))
    
    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(lang_dict["play_duration_limit"].format(config.DURATION_LIMIT // 60))
    
    thumb_path = None
    try:
        thumb = Thumbnail()
        await thumb.start()
        thumb_path = await thumb.generate(file)
        await thumb.close()
    except Exception as e:
        print(f"خطأ في إنشاء صورة التشغيل للقناة: {e}")
        thumb_path = None
    
    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration, thumb_path)
    
    file.user = mention
    position = queue.add(chat_id, file)
    
    if position != 0 or await db.get_call(chat_id):
        if thumb_path and os.path.exists(thumb_path):
            try:
                await sent.delete()
                sent = await app.send_photo(
                    chat_id=chat_id,
                    photo=thumb_path,
                    caption=lang_dict["play_queued"].format(
                        position, file.url, file.title, file.duration, mention
                    ),
                    reply_markup=buttons.play_queued(
                        m.chat.id, file.id, lang_dict["play_now"]
                    ),
                    show_caption_above_media=True
                )
            except Exception as e:
                print(f"خطأ في إرسال الصورة للقناة: {e}")
                await sent.edit_text(
                    lang_dict["play_queued"].format(
                        position, file.url, file.title, file.duration, mention
                    ),
                    reply_markup=buttons.play_queued(
                        m.chat.id, file.id, lang_dict["play_now"]
                    )
                )
        else:
            await sent.edit_text(
                lang_dict["play_queued"].format(
                    position, file.url, file.title, file.duration, mention
                )
            )
        
        if tracks:
            added = playlist_to_queue(chat_id, tracks)
            await app.send_message(
                chat_id=chat_id,
                text=lang_dict["playlist_queued"].format(len(tracks)) + added,
            )
        return
    
    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await sent.edit_text(lang_dict["play_downloading"])
            file.file_path = await yt.download(file.id, video=video)    
    await anon.play_media(chat_id=chat_id, message=sent, media=file)   
    if tracks:
        added = playlist_to_queue(chat_id, tracks)
        await app.send_message(
            chat_id=chat_id,
            text=lang_dict["playlist_queued"].format(len(tracks)) + added,
        )