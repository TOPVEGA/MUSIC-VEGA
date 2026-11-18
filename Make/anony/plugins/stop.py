from pyrogram import filters, types
from pyrogram.enums import ChatType

from anony import anon, app, db, lang
from anony.helpers import buttons, can_manage_vc
from anony.helpers.admins import banned_check


# ✅ معالج القنوات
@app.on_message(filters.command(["/end", "/stop", "ايقاف"], "") & filters.channel)
async def stop_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if len(m.command) > 1:
        return
    
    chat_id = m.chat.id
    call = await db.get_call(chat_id)    
    if not call:
        return await m.reply_text(
            lang_dict["not_playing"],
            reply_markup=buttons.close_markup(lang_dict)
        )
    
    await anon.stop(chat_id)
    await m.reply_text(
        lang_dict["play_stopped"].format(m.chat.title),
        reply_markup=buttons.close_markup(lang_dict)
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/end", "/stop", "ايقاف"], "") & filters.group & ~app.bl_users, group=5)
@lang.language()
@can_manage_vc
@banned_check
async def _stop(_, m: types.Message):
    if len(m.command) > 1:
        return

    call = await db.get_call(m.chat.id)
    await anon.stop(m.chat.id)
    if not call:
        return await m.reply_text(
            m.lang["not_playing"],
            reply_markup=buttons.close_markup(m.lang)
        )

    await m.reply_text(
        m.lang["play_stopped"].format(m.from_user.mention),
        reply_markup=buttons.close_markup(m.lang)
    )