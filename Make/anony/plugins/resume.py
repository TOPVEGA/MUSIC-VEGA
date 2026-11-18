# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026


from pyrogram import filters, types
from pyrogram.enums import ChatType
from anony import anon, app, db, lang
from anony.helpers import buttons, can_manage_vc
from anony.helpers.admins import banned_check


# ✅ معالج القنوات
@app.on_message(filters.command(["/resume", "كمل"], "") & filters.channel)
async def _resume_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if not await db.get_call(m.chat.id):
        return await m.reply_text(
            lang_dict["not_playing"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    if await db.playing(m.chat.id):
        return await m.reply_text(
            lang_dict["play_not_paused"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    await anon.resume(m.chat.id)
    await m.reply_text(
        text=lang_dict["play_resumed"].format(m.chat.title),
        reply_markup=buttons.close_markup(lang_dict),
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/resume", "كمل"], "") & filters.group & ~app.bl_users, group=4)
@lang.language()
@can_manage_vc
@banned_check
async def _resume(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(
            m.lang["not_playing"],
            reply_markup=buttons.close_markup(m.lang)
        )

    if await db.playing(m.chat.id):
        return await m.reply_text(
            m.lang["play_not_paused"],
            reply_markup=buttons.close_markup(m.lang)
        )

    await anon.resume(m.chat.id)
    await m.reply_text(
        text=m.lang["play_resumed"].format(m.from_user.mention),
        reply_markup=buttons.close_markup(m.lang),
    )