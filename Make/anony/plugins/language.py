# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import admin_check, buttons
from anony.helpers.admins import is_owner, banned_check

@app.on_message(filters.command(["/lang", "اللغه"], "") & ~app.bl_users, group=6060)
@lang.language()
@banned_check
async def _lang(_, m: types.Message):
    current = await db.get_lang(m.chat.id)
    keyboard = buttons.lang_markup(current)
    await m.reply_text(m.lang["lang_choose"], reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^lang(?:_change|uage)") & ~app.bl_users)
@lang.language()
@admin_check
async def _lang_cb(_, query: types.CallbackQuery):
    data = query.data.split()
    if data[0] == "language":
        current = await db.get_lang(query.message.chat.id)
        keyboard = buttons.lang_markup(current)
        return await query.edit_message_text(
            query.lang["lang_choose"], reply_markup=keyboard
        )

    _lang = data[1]
    current = await db.get_lang(query.message.chat.id)
    if current == _lang:
        return await query.answer(
            query.lang["lang_same"].format(current), show_alert=True
        )

    await query.answer(query.lang["lang_change"].format(_lang), show_alert=True)
    await db.set_lang(query.message.chat.id, _lang)
    await query.edit_message_text(query.lang["lang_changed"].format(_lang))
