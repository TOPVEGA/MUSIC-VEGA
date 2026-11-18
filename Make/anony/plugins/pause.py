# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

from pyrogram import filters, types
from pyrogram.enums import ChatType

from anony import anon, app, db, lang
from anony.helpers import buttons, can_manage_vc
from anony.helpers.admins import banned_check


# ✅ معالج القنوات (بدون decorators معقدة)
@app.on_message(filters.command(["/pause","وقف"], "") & filters.channel)
async def _pause_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if not await db.get_call(m.chat.id):
        return await m.reply_text(lang_dict["not_playing"])

    if not await db.playing(m.chat.id):
        return await m.reply_text(lang_dict["play_already_paused"])

    await anon.pause(m.chat.id)
    await m.reply_text(
        text=lang_dict["play_paused"].format(m.chat.title),
        reply_markup=buttons.close_markup(lang_dict),
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/pause","وقف"], "") & filters.group & ~app.bl_users, group=6)
@lang.language()
@banned_check
@can_manage_vc
async def _pause(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    if not await db.playing(m.chat.id):
        return await m.reply_text(m.lang["play_already_paused"])

    await anon.pause(m.chat.id)
    await m.reply_text(
        text=m.lang["play_paused"].format(m.from_user.mention),
        reply_markup=buttons.close_markup(m.lang),
    )