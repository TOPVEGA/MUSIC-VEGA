# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026


import os
import asyncio

from pyrogram import errors, filters, types

from anony import app, db, lang, config
from anony.helpers.admins import is_owner, banned_check

broadcasting = False

@app.on_message(filters.command(["شير"], "") & app.sudoers)
@banned_check
@lang.language()
async def _broadcast(_, message: types.Message):
    global broadcasting    
    msg_to_send = None
    is_forward_mode = False
    
    if message.reply_to_message:
        msg_to_send = message.reply_to_message
        is_forward_mode = True
    elif len(message.command) > 1:
        args = message.text.split()
        text_parts = [arg for arg in args[1:] if not arg.startswith("-")]
        if text_parts:
            msg_to_send = " ".join(text_parts)
            is_forward_mode = False
        else:
            return await message.reply_text(message.lang["gcast_usage"])
    else:
        return await message.reply_text(message.lang["gcast_usage"])

    if broadcasting:
        return await message.reply_text(message.lang["gcast_active"])

    count, ucount = 0, 0
    chats, groups, users = [], [], []
    sent = await message.reply_text(message.lang["gcast_start"])
    send_to_users = "للمستخدمين" in message.command  
    
    if send_to_users:
        users.extend(await db.get_users())
    else:
        groups.extend(await db.get_chats())

    chats.extend(groups + users)
    broadcasting = True
    try:
        if is_forward_mode:
            await msg_to_send.forward(config.OWNER_ID)
        else:
            await app.send_message(config.OWNER_ID, msg_to_send)
    except Exception:
        pass
    
    await app.send_message(
        chat_id=config.OWNER_ID, 
        text=message.lang["gcast_log"].format(
            message.from_user.id,
            message.from_user.mention,
            message.text,
        )
    )
    await asyncio.sleep(5)

    failed = ""
    for chat in chats:
        if not broadcasting:
            await sent.edit_text(message.lang["gcast_stopped"].format(count, ucount))
            break

        try:
            if is_forward_mode:             
                if "-copy" in message.command:
                    await msg_to_send.copy(chat, reply_markup=msg_to_send.reply_markup)
                else:
                    await msg_to_send.forward(chat)
            else:           
                await app.send_message(chat, msg_to_send)
            
            if send_to_users:
                ucount += 1
            else:
                count += 1
            await asyncio.sleep(0.1)
        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 30)
        except Exception as ex:
            failed += f"{chat} - {ex}\n"
            continue

    text = message.lang["gcast_end"].format(count, ucount)
    if failed:
        with open("errors.txt", "w") as f:
            f.write(failed)
        await message.reply_document(
            document="errors.txt",
            caption=text,
        )
        os.remove("errors.txt")
    broadcasting = False
    await sent.edit_text(text)


@app.on_message(filters.command(["stop_gcast", "stop_broadcast"]) & app.sudoers)
@lang.language()
@banned_check
async def _stop_gcast(_, message: types.Message):
    global broadcasting
    if not broadcasting:
        return await message.reply_text(message.lang["gcast_inactive"])

    broadcasting = False
    await app.send_message(
        chat_id=config.OWNER_ID,
        text=message.lang["gcast_stop_log"].format(
            message.from_user.id,
            message.from_user.mention
        )
    )
    await message.reply_text(message.lang["gcast_stop"])