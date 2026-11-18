# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026


from pyrogram import filters, types
from pyrogram.enums import ChatType

from anony import anon, app, db, lang, queue
from anony.helpers import buttons, can_manage_vc
from anony.helpers.admins import banned_check


# ✅ معالج القنوات
@app.on_message(filters.command(["/seek", "رجع","رجوع", "قدم", "تقديم"], "") & filters.channel)
async def _seek_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if len(m.command) < 2:
        return await m.reply_text(
            lang_dict["play_seek_usage"].format(m.command[0]),
            reply_markup=buttons.close_markup(lang_dict)
        )

    try:
        to_seek = int(m.command[1])
    except ValueError:
        return await m.reply_text(
            lang_dict["play_seek_usage"].format(m.command[0]),
            reply_markup=buttons.close_markup(lang_dict)
        )
    
    if to_seek < 10:
        return await m.reply_text(
            lang_dict["play_seek_min"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    chat_id = m.chat.id
    
    if not await db.get_call(chat_id):
        return await m.reply_text(
            lang_dict["not_playing"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    if not await db.playing(chat_id):
        return await m.reply_text(
            lang_dict["play_already_paused"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    media = queue.get_current(chat_id)
    if not media or not media.duration_sec:
        return await m.reply_text(
            lang_dict["play_seek_no_dur"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    sent = await m.reply_text(lang_dict["play_seeking"])
    
    if m.command[0] in ["seekback", "رجوع"]:
        stype = lang_dict["backward"]
        start_from = media.time - to_seek
        if start_from < 1:
            start_from = 1
    else:
        stype = lang_dict["forward"]
        start_from = media.time + to_seek
        if start_from + 10 > media.duration_sec:
            start_from = media.duration_sec - 5

    await anon.play_media(chat_id, sent, media, start_from)
    media.time = start_from
    await sent.edit_text(
        lang_dict["play_seeked"].format(stype, start_from, m.chat.title),
        reply_markup=buttons.close_markup(lang_dict)
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/seek", "رجع","رجوع", "قدم", "تقديم"], "") & filters.group & ~app.bl_users)
@lang.language()
@banned_check
@can_manage_vc
async def _seek(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(
            m.lang["play_seek_usage"].format(m.command[0]),
            reply_markup=buttons.close_markup(m.lang)
        )

    try:
        to_seek = int(m.command[1])
    except ValueError:
        return await m.reply_text(
            m.lang["play_seek_usage"].format(m.command[0]),
            reply_markup=buttons.close_markup(m.lang)
        )
    if to_seek < 10:
        return await m.reply_text(
            m.lang["play_seek_min"],
            reply_markup=buttons.close_markup(m.lang)
        )

    if not await db.get_call(m.chat.id):
        return await m.reply_text(
            m.lang["not_playing"],
            reply_markup=buttons.close_markup(m.lang)
        )

    if not await db.playing(m.chat.id):
        return await m.reply_text(
            m.lang["play_already_paused"],
            reply_markup=buttons.close_markup(m.lang)
        )

    media = queue.get_current(m.chat.id)
    if not media or not media.duration_sec:
        return await m.reply_text(
            m.lang["play_seek_no_dur"],
            reply_markup=buttons.close_markup(m.lang)
        )

    sent = await m.reply_text(m.lang["play_seeking"])
    if m.command[0] == "seekback":
        stype = m.lang["backward"]
        start_from = media.time - to_seek
        if start_from < 1:
            start_from = 1
    else:
        stype = m.lang["forward"]
        start_from = media.time + to_seek
        if start_from + 10 > media.duration_sec:
            start_from = media.duration_sec - 5

    await anon.play_media(m.chat.id, sent, media, start_from)
    media.time = start_from
    await sent.edit_text(
        m.lang["play_seeked"].format(stype, start_from, m.from_user.mention),
        reply_markup=buttons.close_markup(m.lang)
    )