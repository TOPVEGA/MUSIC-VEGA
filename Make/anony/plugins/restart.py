
# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import os
import sys
import shutil
import asyncio
from pyrogram import filters, types
from anony import app, db, lang, stop
from anony.helpers.admins import is_owner, banned_check

@app.on_message(filters.command(["log"]) & app.sudoers, group=77)
@lang.language()
@is_owner
async def _logs(_, m: types.Message):
    sent = await m.reply_text(m.lang["log_fetch"])
    if not os.path.exists("log.txt"):
        return await sent.edit_text(m.lang["log_not_found"])
    await sent.edit_media(
        media=types.InputMediaDocument(
            media="log.txt",
            caption=m.lang["log_sent"].format(app.name),
        )
    )


@app.on_message(filters.command(["تفعيل السجل", "تعطيل السجل"], ""), group=124)
@lang.language()
@is_owner
@banned_check
async def _logger(_, m: types.Message):
    if len(m.command) < 1:
        return await m.reply_text(m.lang["logger_usage"].format(m.command[0]))
    if m.command[0] == "تفعيل السجل":
        await db.set_logger(True)
        await m.reply_text(m.lang["logger_on"])
    elif m.command[0] == "تعطيل السجل":
        await db.set_logger(False)
        await m.reply_text(m.lang["logger_off"])
    else:
        await m.reply_text(m.lang["logger_usage"].format(m.command[0]))


@app.on_message(filters.command(["تحديث البوت","/restart"], "") & app.sudoers, group=780)
@lang.language()
@is_owner
async def _restart(_, m: types.Message):
    sent = await m.reply_text(m.lang["restarting"])
    for directory in ["cache", "downloads"]:
        shutil.rmtree(directory, ignore_errors=True)
    await sent.edit_text(m.lang["restarted"])
    asyncio.create_task(stop())
    await asyncio.sleep(2)
    try: os.remove("log.txt")
    except Exception: pass
    os.execl(sys.executable, sys.executable, "-m", "anony")
