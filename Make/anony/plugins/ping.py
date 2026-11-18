# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import time
import psutil
from pyrogram import filters, types, errors
from anony import app, anon, boot, config, lang
from anony.plugins.start import bot_thumb
from anony.helpers import buttons
from anony.helpers.admins import is_owner, banned_check


@app.on_message(filters.command(["بنج", "/ping","بينج"], "") & ~app.bl_users, group=6770)
@lang.language()
@banned_check
async def _ping(_, m: types.Message):
    if bot_thumb.session is None:
        await bot_thumb.start()
    
    start = time.time()
    sent = await m.reply_text(m.lang["pinging"])
    
    get_time = lambda s: (lambda r: (f"{r[-1]}, " if r[-1][:-4] != "0" else "") + ":".join(reversed(r[:-1])))([f"{v}{u}" for v, u in zip([s%60, (s//60)%60, (s//3600)%24, s//86400], ["s", "m", "h", "days"])])
    uptime = get_time(int(time.time() - boot))
    latency = round((time.time() - start) * 1000, 2)
    bot = await app.get_me()
    bot_thumbnail = await bot_thumb.generate_bot_thumb(bot.first_name, bot.username)    
    try:
        await sent.delete()
        await m.reply_photo(
            photo=bot_thumbnail,
            caption=m.lang["ping_pong"].format(
                latency,
                uptime,
                psutil.cpu_percent(interval=0),
                psutil.virtual_memory().percent,
                psutil.disk_usage("/").percent,
                await anon.ping(),
            ),
            reply_markup=buttons.ping_markup(m.lang["support"]),
            quote=True
        )
    except errors.ChatAdminRequired:
        await sent.edit_text(
            m.lang["ping_pong"].format(
                latency,
                uptime,
                psutil.cpu_percent(interval=0),
                psutil.virtual_memory().percent,
                psutil.disk_usage("/").percent,
                await anon.ping(),
            ),
            reply_markup=buttons.ping_markup(m.lang["support"]),
        )
    except Exception as e:
        await sent.edit_text(f"حدث خطأ:`{str(e)}`")