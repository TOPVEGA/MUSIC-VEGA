# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026


from pyrogram import filters, types
from pyrogram.enums import ChatType

from anony import app, db, lang
from anony.helpers import buttons, can_manage_vc


# ✅ معالج القنوات
@app.on_message(filters.command(["/loop","تكرار","كرر", "تكرر"], "") & filters.channel)
async def _loop_channel(_, m: types.Message):
    lang_code = await db.get_lang(m.chat.id) or "ar"
    lang_dict = lang.languages.get(lang_code, lang.languages.get("ar", {}))
    
    if not await db.get_call(m.chat.id):
        return await m.reply_text(lang_dict["not_playing"])

    chat_id = m.chat.id
    if len(m.command) < 2:
        if count := await db.get_loop(chat_id):
            return await m.reply_text(
                lang_dict["loop_count"].format(count),
                reply_markup=buttons.close_markup(lang_dict)
            )
        else:
            return await m.reply_text(
                lang_dict["loop_usage"],
                reply_markup=buttons.close_markup(lang_dict)
            )

    disable = m.command[1].lower() in ["off", "disable"]
    if not m.command[1].isdigit() and not disable:
        return await m.reply_text(
            lang_dict["loop_usage"],
            reply_markup=buttons.close_markup(lang_dict)
        )

    loop_num = int(m.command[1]) if not disable else 0
    if loop_num < 1: loop_num = 0
    elif loop_num > 10: loop_num = 10

    await db.set_loop(chat_id, loop_num)
    if loop_num == 0:
        return await m.reply_text(
            lang_dict["loop_off"],
            reply_markup=buttons.close_markup(lang_dict)
        )
    await m.reply_text(
        lang_dict["loop_set"].format(loop_num),
        reply_markup=buttons.close_markup(lang_dict)
    )


# ✅ معالج المجموعات
@app.on_message(filters.command(["/loop","تكرار","كرر", "تكرر"], "") & filters.group & ~app.bl_users, group=8080)
@lang.language()
@can_manage_vc
async def _loop(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    chat_id = m.chat.id
    if len(m.command) < 2:
        if count := await db.get_loop(chat_id):
            return await m.reply_text(
                m.lang["loop_count"].format(count),
                reply_markup=buttons.close_markup(m.lang)
            )
        else:
            return await m.reply_text(
                m.lang["loop_usage"],
                reply_markup=buttons.close_markup(m.lang)
            )

    disable = m.command[1].lower() in ["off", "disable"]
    if not m.command[1].isdigit() and not disable:
        return await m.reply_text(
            m.lang["loop_usage"],
            reply_markup=buttons.close_markup(m.lang)
        )

    loop_num = int(m.command[1]) if not disable else 0
    if loop_num < 1: loop_num = 0
    elif loop_num > 10: loop_num = 10

    await db.set_loop(m.chat.id, loop_num)
    if loop_num == 0:
        return await m.reply_text(
            m.lang["loop_off"],
            reply_markup=buttons.close_markup(m.lang)
        )
    await m.reply_text(
        m.lang["loop_set"].format(loop_num),
        reply_markup=buttons.close_markup(m.lang)
    )