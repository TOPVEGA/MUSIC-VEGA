import os
import platform
import sys
import asyncio

import psutil
from pyrogram import __version__, filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import __version__ as pytgver
from datetime import datetime
from anony import app, config, db, lang, userbot
from anony.plugins import all_modules
from anony.helpers.admins import is_owner, banned_check
from anony.plugins.start import bot_thumb


# ========== أمر عرض المجموعات ==========
@app.on_message(filters.command(["المجموعات","/groups"], ""), group=700)
@is_owner
async def groups_func(client, message):
    msg = await message.reply_text("⚡")
    await asyncio.sleep(2)
    await msg.delete()

    chats_ids = await db.get_chats()
    count = 0
    text = ""

    for chat_id in chats_ids:
        try:
            chat = await client.get_chat(chat_id)
            title = chat.title or "بدون عنوان"
            members = chat.members_count
            username = chat.username
            count += 1

            if username:
                txt = f"{count} • <b>{title}</b>\n👥 {members} عضو\n🔗 <a href='https://t.me/{username}'>رابط المجموعة</a>\nɪᴅ : <code>{chat_id}</code>\n\n"
            else:
                txt = f"{count} • <b>{title}</b>\n👥 {members} عضو\nɪᴅ : <code>{chat_id}</code>\n\n"

            text += txt
        except Exception as e:
            print(f"Error retrieving chat data for {chat_id}: {e}")
            count += 1
            txt = f"{count} • <b>غير متاح</b>\nɪᴅ : <code>{chat_id}</code>\n\n"
            text += txt

    if count == 0:
        text = "لايوجد معرفات للمجموعات لفحصها"

    MAX_MESSAGE_LENGTH = 4096
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.reply_text(text, disable_web_page_preview=True)
    else:
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            await message.reply_text(text[i:i + MAX_MESSAGE_LENGTH], disable_web_page_preview=True)


# ========== أمر عرض المستخدمين ==========
@app.on_message(filters.command(["المستخدمين","/users"], ""), group=701)
@is_owner
async def users_func(client, message):
    msg = await message.reply_text("⚡")
    await asyncio.sleep(2)
    await msg.delete()

    users_ids = await db.get_users()
    count = 0
    text = ""

    for user_id in users_ids:
        try:
            user = await client.get_users(user_id)
            first_name = user.first_name or "بدون اسم"
            last_name = user.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            username = user.username
            count += 1

            if username:
                txt = f"{count} • <b>{full_name}</b>\n👤 يوزر: <a href='https://t.me/{username}'>@{username}</a>\nɪᴅ : <code>{user_id}</code>\n\n"
            else:
                txt = f"{count} • <b>{full_name}</b>\n👤 يوزر: لا يوجد\nɪᴅ : <code>{user_id}</code>\n\n"

            text += txt
        except Exception as e:
            print(f"Error retrieving user data for {user_id}: {e}")
            count += 1
            txt = f"{count} • <b>غير متاح</b>\nɪᴅ : <code>{user_id}</code>\n\n"
            text += txt

    if count == 0:
        text = "لا يوجد مستخدمين في قاعدة البيانات"

    MAX_MESSAGE_LENGTH = 4096
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.reply_text(text, disable_web_page_preview=True)
    else:
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            await message.reply_text(text[i:i + MAX_MESSAGE_LENGTH], disable_web_page_preview=True)





        
        
# ========== أمر الترويج ==========
@app.on_message(filters.command(["ترويج"], "") & filters.private, group=702)
@is_owner
@banned_check
async def promo_command(client, message):
    if bot_thumb.session is None:
        await bot_thumb.start()
    
    status = await message.reply_text("🚀")
    
    try:
        bot_user = await client.get_me()
        
        bot = await app.get_me()
        bot_thumbnail = await bot_thumb.generate_bot_thumb(bot.first_name, bot.username)
        
        caption = f"""
<b>• سرعة فائقة بدون تقطيع
• جودة صوت عالية Mp3
• ألعاب ترفيهية متنوعة
• تحميل مباشر من يوتيوب</b>\nㅤ
"""
        
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("• اضف البوت لمجموعتك •", url=f"https://t.me/{bot_user.username}?startgroup=new")
        ]])
        
        promo_img = bot_thumbnail
        
        chats = await db.get_chats()
        users = await db.get_users()
        
        sent = 0
        failed = 0
        for chat_id in chats[:50]:
            try:
                await client.send_photo(
                    chat_id, 
                    promo_img, 
                    caption=caption, 
                    reply_markup=reply_markup,
                    show_caption_above_media=True
                )
                sent += 1
                await asyncio.sleep(0.5)
            except:
                failed += 1
       
        # إرسال للمستخدمين
        for user_id in users[:100]:
            try:
                await client.send_photo(
                    user_id, 
                    promo_img, 
                    caption=caption, 
                    reply_markup=reply_markup,
                    show_caption_above_media=True
                )
                sent += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        
        await status.edit_text(f"✅ تم الترويج\n✓ تم الارسال: {sent}\n✗ فشل: {failed}")
    
    except Exception as e:
        await status.edit_text(f"❌ حدث خطأ: {e}")




@app.on_message(filters.command(["الاحصائيات", "stats"], "") & filters.private, group=50)
async def show_stats(client, message):
    try:
        msg = await message.reply_text("🔄 جاري تحميل الاحصائيات...")
        
        users_count = len(await db.get_users())
        chats_count = len(await db.get_chats())
        channels_count = 0
        try:
            channels_doc = await db.cache.find_one({"_id": "channels_count"})
            if channels_doc:
                channels_count = channels_doc.get("count", 0)
        except:
            channels_count = 0        
        banned_users_count = await db.get_banned_users_count()
        blacklisted_chats = await db.get_blacklisted(chat=True)
        blacklisted_chats_count = len(blacklisted_chats)
        s_ranks_count = await db.get_s_ranks_count()
        auth_users_count = 0
        try:
            async for chat in db.authdb.find({}):
                if "user_ids" in chat:
                    auth_users_count += len(chat["user_ids"])
        except:
            auth_users_count = 0
        admins_count = 0
        try:
            all_chats = await db.get_chats()
            for chat_id in all_chats[:20]:
                try:
                    admins = await db.get_admins(chat_id)
                    admins_count += len(admins)
                except:
                    continue
        except:
            admins_count = 0
        stats_text = f"""<b>إحصائيات البوت</b>

<b>
• عدد المستخدمين: `{users_count}`
• عدد المجموعات: `{chats_count}`
• عدد القنوات: `{channels_count}`
• المحظورين عام: `{banned_users_count}`
• الجروبات المحظورة: `{blacklisted_chats_count}`
• رتبة S: `{s_ranks_count}`
• المميزين (Auth): `{auth_users_count}`
• عدد الأدمن: `{admins_count}` (تقريبي)</b>\nㅤ
"""

        # ========== إرسال الاحصائيات ==========
        await msg.edit_text(stats_text)
        
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ: `{str(e)}`")
        
        
        
# ========== أمر الإحصائيات ==========
@app.on_message(filters.command(["/stats","احصائيات"], "") & filters.group & ~app.bl_users, group=703)
@lang.language()
@is_owner
@banned_check
async def _stats(_, m: types.Message):
    sent = await m.reply_photo(
        photo=config.PING_IMG,
        caption=m.lang["stats_fetching"],
    )

    pid = os.getpid()
    _utext = m.lang["stats_user"].format(
        app.name,
        len(userbot.clients),
        config.AUTO_LEAVE,
        len(db.blacklisted),
        len(app.bl_users),
        len(app.sudoers),
        len(await db.get_chats()),
        len(await db.get_users()),
    )
    if m.from_user.id in app.sudoers:
        process = psutil.Process(pid)
        storage = psutil.disk_usage("/")
        _utext += m.lang["stats_sudo"].format(
            len(all_modules),
            platform.system(),
            f"{process.memory_info().rss / 1024**2:.2f}",
            round(psutil.virtual_memory().total / (1024.0**3)),
            process.cpu_percent(interval=1.0),
            psutil.cpu_count(),
            f"{storage.used / (1024.0**3):.2f}",
            f"{storage.total / (1024.0**3):.2f}",
            sys.version.split()[0],
            __version__,
            pytgver,
        )
    await sent.edit_caption(_utext)