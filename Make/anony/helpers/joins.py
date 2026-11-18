# anony/helpers/must_join.py
from functools import wraps
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import requests

from anony import config, app, anon, db

OWNER_ID = config.OWNER_ID
BOT_TOKEN = config.BOT_TOKEN


def must_join_ch(func):
    @wraps(func)
    async def wrapper(c, m):
        if m.chat.type != ChatType.CHANNEL:
            bot_username = (await c.get_me()).username
            channel = await db.get_must_channel(bot_username)
            status = await db.get_must_status(bot_username)
            
            if channel and status == "enable":
                try:
                    import requests
                    s = requests.get(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
                        params={"chat_id": f"@{channel}", "user_id": m.from_user.id}
                    )
                    data = s.json()
                    
                    if data["ok"] and data["result"]["status"] in ["member", "creator", "administrator"]:
                        return await func(c, m)
                    else:
                        return await m.reply(
                            f"<b>• عـزيزي : {m.from_user.mention}\n"
                            f"• اشترك فالقناه اولا لتشغيل الاغاني</b>",
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("• للاشتراك بالقناه •", url=f"https://t.me/{channel}")
                            ]])
                        )
                except Exception as e:
                    print(f"Error checking subscription: {e}")
                    return await func(c, m)                    
        return await func(c, m)
    return wrapper