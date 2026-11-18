from pyrogram import filters, types
from pyrogram.enums import ChatType

from anony import anon, app, db, lang
from anony.helpers import buttons, can_manage_vc
from anony.helpers.admins import banned_check


# ✅ معالج القنوات
@app.on_message(filters.command(["/skip", "تخطي"], "") & filters.channel)
async def _skip_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if not await db.get_call(m.chat.id):
        return await m.reply_text(
            lang_dict["not_playing"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    await anon.play_next(m.chat.id)
    await m.reply_text(
        lang_dict["play_skipped"].format(m.chat.title),
        reply_markup=buttons.close_markup(lang_dict)
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/skip", "تخطي"], "") & filters.group & ~app.bl_users, group=23276)
@lang.language()
@banned_check
@can_manage_vc
async def _skip(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(
            m.lang["not_playing"],
            reply_markup=buttons.close_markup(m.lang)
        )

    await anon.play_next(m.chat.id)
    await m.reply_text(
        m.lang["play_skipped"].format(m.from_user.mention),
        reply_markup=buttons.close_markup(m.lang)
    )