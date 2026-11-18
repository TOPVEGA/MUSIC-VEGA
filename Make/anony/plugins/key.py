# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import json
import os
import re
import asyncio
import shutil
import platform
import socket
import uuid
import psutil
import time
from datetime import datetime
from typing import Union
from sys import version as pyver

from pyrogram import __version__ as pyrover
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter, ChatType
from pyrogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from pyrogram import filters, Client, enums

from pytgcalls.__version__ import __version__ as pytgver

from anony import app, anon, db, config, logger, userbot
from anony.helpers.admins import is_owner, banned_check


# ========== المتغيرات العامة ==========
OWNER_ID = config.OWNER_ID
BOT_TOKEN = config.BOT_TOKEN
SESSION1 = config.SESSION1
SUPPORT_CHANNEL = config.SUPPORT_CHANNEL
SUPPORT_CHAT = config.SUPPORT_CHAT
ONE_VIDEO_URL = config.ONE_VIDEO_URL

SUDORS = [OWNER_ID]


# ========== دوال المساعد ==========
async def get_assistant(num: int = 1):
    if num == 1 and userbot.one:
        return userbot.one
    elif num == 2 and userbot.two:
        return userbot.two
    elif num == 3 and userbot.three:
        return userbot.three
    elif userbot.clients:
        return userbot.clients[0]
    return None


# ========== دوال حفظ البيانات (الآن تستخدم قاعدة البيانات) ==========
async def load_groups():
    """تحميل الجروبات من قاعدة البيانات"""
    chats = await db.get_chats()
    logger.info(f"تم تحميل {len(chats)} جروب من قاعدة البيانات")

async def save_groups():
    """لم تعد هناك حاجة للحفظ المحلي، البيانات محفوظة في MongoDB"""
    pass

async def load_channels():
    """تحميل القنوات من قاعدة البيانات"""
    channels = await db.get_channels()
    logger.info(f"تم تحميل {len(channels)} قناة من قاعدة البيانات")

async def save_channels():
    """لم تعد هناك حاجة للحفظ المحلي، البيانات محفوظة في MongoDB"""
    pass

async def load_users_data():
    """تحميل المستخدمين من قاعدة البيانات"""
    users_list = await db.get_users()
    return users_list

async def save_users(users_set=None):
    """لم تعد هناك حاجة للحفظ المحلي، البيانات محفوظة في MongoDB"""
    pass


# ================== الأوامر الأساسية ==================
@app.on_message(filters.command(["/start"], "") & filters.private, group=11)
async def start_command(client, message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["النظام"],
                ["قسم الاذاعه"],
                ["قسم البوت", "قسم المساعد"],
                ["التواصل و الاحصائيات"],
                ["النسخه الاحتياطيه"],
                ["القفل و الفتح", "الاشتراك الاجباري"],
                ["Cancel key"]
            ],
            resize_keyboard=True
        )
        await message.reply_text(
            "هلا فيك يالمطور\nهنا لوحة تحكم السورس حقك",
            reply_markup=keyboard,
            protect_content=True
        )


@app.on_message(filters.command(["رجوع"], "") & filters.private, group=2)
async def back_command(client, message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["النظام"],
                ["قسم الاذاعه"],
                ["قسم البوت", "قسم المساعد"],
                ["التواصل و الاحصائيات"],
                ["النسخه الاحتياطيه"],
                ["القفل و الفتح", "الاشتراك الاجباري"],
                ["Cancel key"]
            ],
            resize_keyboard=True
        )
        await message.reply_text(
            "هلا فيك يالمطور\nهنا لوحة تحكم السورس حقك",
            reply_markup=keyboard,
            protect_content=True
        )


@app.on_message(filters.command(["Cancel key"], "") & filters.private, group=3)
async def cancel_keyboard(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        await message.reply(
            "تم الغاء الكيبورد بنجاح\nلظهره مره اخر /start",
            reply_markup=ReplyKeyboardRemove(selective=True)
        )
    else:
        await message.reply("هذا الامر لا يخصك")


# ================== تسجيل المستخدمين ==================
@app.on_message(filters.text & filters.private, group=10)
async def users_me(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        return  # تخطي المطورين
    
    # استخدام قاعدة البيانات بدلاً من الملفات
    is_existing = await db.is_user(message.from_user.id)
    if not is_existing:
        await db.add_user(message.from_user.id)
        
        # جلب صورة المستخدم
        photo = None
        try:
            user = await client.get_users(message.from_user.id)
            if user.photo:
                photo = await client.download_media(user.photo.big_file_id, in_memory=True)
        except Exception as e:
            print(f"Error getting user photo: {e}")
        
        # إنشاء اسم قابل للنقر
        if message.from_user.username:
            user_mention = f"[{message.from_user.first_name}](https://t.me/{message.from_user.username})"
        else:
            user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
        
        # عدد المستخدمين من قاعدة البيانات
        total_users = len(await db.get_users())
        
        # نص الرسالة
        text = '• شخص جديد دخل الى البوت !\n\n'
        text += f'• الأسم: {user_mention}\n'
        text += f'• لايدي: `{message.from_user.id}`\n\n'
        text += f'• اصبح عدد المستخدمين: {total_users}'
        
        # زر دخول للمستخدم
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(message.from_user.first_name, url=f"tg://user?id={message.from_user.id}")]
        ])
        
        try:
            if photo:
                await client.send_photo(
                    OWNER_ID,
                    photo,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                await client.send_message(
                    OWNER_ID,
                    text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error sending new user notification: {e}")


# ================== التواصل (نظام الرد التلقائي) ==================
@app.on_message(filters.private & ~filters.command(["start"]), group=20)
async def twasl(client, msg):
    if msg.from_user.id in SUDORS:
        return
    for user in SUDORS:
        doc = await db.cache.find_one({"_id": f"{user}:twasl"})
        if doc:
            await msg.forward(user)


@app.on_message(filters.private & filters.user(OWNER_ID), group=21)
async def owner_reply(client, msg):
    if msg.reply_to_message and msg.reply_to_message.forward_from:
        try:
            await msg.copy(msg.reply_to_message.forward_from.id)
            await msg.reply(f"• تم الارسال الى {msg.reply_to_message.forward_from.first_name}")
        except Exception as e:
            await msg.reply(f" خطأ: {e}")


@app.on_message(filters.text & filters.private & filters.user(OWNER_ID), group=22)
async def cmd(client, msg):
    if msg.text == "تفعيل التواصل":
        await db.cache.update_one({"_id": f"{OWNER_ID}:twasl"}, {"$set": {"status": 1}}, upsert=True)
        await msg.reply("• تم تفعيل التواصل")
    elif msg.text == "تعطيل التواصل":
        await db.cache.delete_one({"_id": f"{OWNER_ID}:twasl"})
        await msg.reply("• تم تعطيل التواصل")


# ================== باقي الأوامر ==================
@app.on_message(filters.command(["النظام"], "") & filters.private, group=30)
async def source_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["سورس"],
                ["تغير كليشه السورس", "تغير قناه السورس"],
                ["تغير لوجو السورس"],
                ["حذف تخصيص السورس"],
                ["عرض التخصيصات"],
                ["تغير زر التحكم","تغير نص زر التحكم"],
                ["اضف زر المطور"],
                ["تغير رابط زر التحكم","عرض زر التحكم"],
                ["حذف زر التحكم"],
                ["تغير المطور", "حذف المطور"],
                ["المطور"],
                ["رفع مطور", "تنزيل مطور"],
                ["المطورين"],
                ["ترقيه s","سحب s"],
                ["قائمة اس"],
                ["صلاحياتي","رتبتي"],
                ["تحديث s"],
                ["تهيئه النظام"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("هلا فيك يالمطور\nهنا لوحة تحكم السورس حقك", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["القفل و الفتح"], "") & filters.private, group=31)
async def lock_unlock_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["تعطيل التحميل عام", "تفعيل التحميل عام"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالقفل والفتح العام", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["قسم الاذاعه"], "") & filters.private, group=32)
async def broadcast_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["إذاعة للجروبات"],
                ["إذاعة بالتوجيه للجروبات"],
                ["إذاعة للمستخدمين"],
                ["إذاعة بالتوجيه للمستخدمين"],
                ["إذاعة للقنوات"],
                ["إذاعة بالتوجيه للقنوات"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالاذاعه", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["قسم المساعد"], "") & filters.private, group=33)
async def assistant_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["فحص المساعد"],
                ["المساعد"],
                ["اضف الاسم الاول", "ازالة الاسم الاول"],
                ["تغير يوزر المساعد"],
                ["اضف بايو", "ازالة بايو"],
                ["اضف الاسم التاني", "ازالة الاسم التاني"],
                ["اضف صوره", "ازالة صوره"],
                ["ازالة كل صور"],
                ["غادر القنوات", "غادر الجروبات"],
                ["انضم"],
                ["اذاعه بالمساعد", "اذاعه بتوجيه بالمساعد"],
                ["الغاء"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالحساب المساعد", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["قسم البوت"], "") & filters.private, group=34)
async def bot_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["تعين اسم البوت"],
                ["ترويج"],
                ["تعطيل السجل", "تفعيل السجل"],
                ["فحص البوت"],
                ["معلومات التنصيب"],
                ["تفعيل استارت", "تعطيل استارت"],
                ["تغير رسالة استارت", "حذف رساله استارت"],
                ["تحديث البوت", "تنظيف التخزين"],
                ["الغاء"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالبوت", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["التواصل و الاحصائيات"], "") & filters.private, group=35)
async def contact_stats_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["الاحصائيات"],
                ["المجموعات", "المستخدمين"],
                ["تفعيل التواصل", "تعطيل التواصل"],
                ["الغاء"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالاحصائيات.", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["النسخه الاحتياطيه"], "") & filters.private, group=36)
async def backup_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["جلب نسخه للجروبات", "رفع نسخه للجروبات"],
                ["جلب نسخه للمستخدمين", "رفع نسخه للمستخدمين"],
                ["جلب نسخه للقنوات", "رفع نسخه للقنوات"],
                ["الغاء"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالنسخة الاحتياطية", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


@app.on_message(filters.command(["الاشتراك الاجباري"], "") & filters.private, group=37)
async def force_subscribe_section(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        keyboard = ReplyKeyboardMarkup(
            [
                ["تفعيل الاشتراك بالخاص", "تعطيل الاشتراك بالخاص"],
                ["حذف الاشتراك بالخاص"],
                ["اضف قناه الاشتراك للتشغيل"],
                ["قناة الاشتراك", "حذف قناة الاشتراك"],
                ["تفعيل الاشتراك للتشغيل", "تعطيل الاشتراك للتشغيل"],
                ["الغاء"],
                ["رجوع"]
            ],
            resize_keyboard=True
        )
        await message.reply_text("اهلا يالمطور\nهنا تقدر تتحكم بالاشتراك الاجباري.", reply_markup=keyboard)
    else:
        await message.reply("هذا الامر لا يخصك")


# ========== إدارة المطورين ==========
@app.on_message(filters.command("رفع مطور", "") & filters.private, group=40)
async def promote_dev(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(
                message.chat.id,
                "ارسل معرف المستخدم الان (مع @ او بدون)",
                timeout=300
            )
            user_input = ask.text.replace("@", "")

            try:
                user = await client.get_chat(user_input)
                user_id = user.id

                if user_id in SUDORS:
                    return await ask.reply_text("المستخدم بالفعل مطور")

                SUDORS.append(user_id)
                await ask.reply_text("تم رفع المستخدم كمطور")
            except Exception as e:
                await ask.reply_text(f"حدث خطأ: {e}")
        except Exception as e:
            await message.reply_text("تم الغاء العملية")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command("تنزيل مطور", "") & filters.private, group=41)
async def demote_dev(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(
                message.chat.id,
                "ارسل معرف المستخدم الان (مع @ او بدون)",
                timeout=300
            )
            user_input = ask.text.replace("@", "")

            try:
                user = await client.get_chat(user_input)
                user_id = user.id

                if user_id not in SUDORS:
                    return await ask.reply_text("هذا المستخدم ليس مطور")

                SUDORS.remove(user_id)
                await ask.reply_text("تم تنزيل المستخدم من المطورين")
            except Exception as e:
                await ask.reply_text(f"حدث خطأ: {e}")
        except Exception:
            await message.reply_text("تم الغاء العملية")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command("المطورين", "") & filters.private, group=42)
async def list_devs(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        if not SUDORS:
            return await message.reply_text("لا يوجد مطورين في القائمة")

        try:
            user_mentions = await asyncio.gather(*[client.get_users(user_id) for user_id in SUDORS])
            response = "<b><u>قائمة مطورين:</u></b>\n"

            for i, user in enumerate(user_mentions, start=1):
                response += f"<b>{i}- {user.mention}</b>\n"

            count = len(SUDORS)
            response += f"\n<b>عدد المطورين:</b> [{count}]</b>"

            await message.reply_text(response, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            await message.reply_text(f"حدث خطأ: {e}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


# ================== أوامر المساعد (group 50+) ==================
@app.on_message(filters.command(["فحص المساعد"], "") & filters.private, group=50)
async def check_assistant(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        msg = await message.reply_text("جاري فحص المساعد...")
        start = datetime.now()
        u = g = sg = c = b = a_chat = 0

        try:
            assistant_client = await get_assistant(1)
            if not assistant_client:
                return await msg.edit_text("لا يمكن العثور على حساب المساعد")

            me = await assistant_client.get_me()

            photo_path = None
            try:
                async for photo_obj in assistant_client.get_chat_photos("me", limit=1):
                    photo_path = await assistant_client.download_media(photo_obj.big_file_id)
                    break
            except Exception as e:
                print(f"Error getting profile photo: {str(e)}")

            async for dialog in assistant_client.get_dialogs():
                try:
                    if dialog.chat.type == enums.ChatType.PRIVATE:
                        u += 1
                    elif dialog.chat.type == enums.ChatType.BOT:
                        b += 1
                    elif dialog.chat.type == enums.ChatType.GROUP:
                        g += 1
                    elif dialog.chat.type == enums.ChatType.SUPERGROUP:
                        sg += 1
                        try:
                            member = await assistant_client.get_chat_member(dialog.chat.id, "me")
                            if member.status in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR):
                                a_chat += 1
                        except:
                            continue
                    elif dialog.chat.type == enums.ChatType.CHANNEL:
                        c += 1
                except Exception as e:
                    print(f"Error processing chat: {str(e)}")
                    continue

            end = datetime.now()
            ms = (end - start).seconds

            caption = f"""<b>
•  إِحْصَائِيَّاتُ المُسَاعِد 

أَوَّلًا: شَوَاهِدُ العَمَلِ:
    • زَمَنُ الِاسْتِجَابَةِ: {ms}
    • عَدَدُ مُحَادَثَاتِ الخَاصِّ: {u}
    • الوُجُودُ فِي المَجْمُوعَاتِ: {g}
    • الوُجُودُ فِي المَجْمُوعَاتِ الفَائِقَةِ: {sg}
    • الوُجُودُ فِي القَنَوَاتِ: {c}

ثَانِيًا: مَعْلُومَاتُ المُسَاعِدِ:
    • الاِسْمُ: {me.first_name or 'المُسَاعِد'}
    • المَعْرِفُ: @{me.username if me.username else 'لا يُوجَد'}
    • الرَّقْمُ: {me.id}

ثَالِثًا: الصَّلَاحِيَّاتُ:
    • هَلْ هُوَ مُدِيرٌ فِي مَجْمُوعَةٍ؟ {a_chat}
    • عَدَدُ البَوْتَاتِ المُصَاحِبَةِ: {b}</b>
"""

            if photo_path and os.path.exists(photo_path):
                await message.reply_photo(photo=photo_path, caption=caption)
                try:
                    os.remove(photo_path)
                except:
                    pass
            else:
                await message.reply_text(caption)

        except Exception as e:
            await msg.edit_text(f"حدث خطأ أثناء فحص المساعد: {str(e)}")
        else:
            await msg.delete()
    else:
        await message.reply("هذا الأمر لا يخصك")


@app.on_message(filters.command(["المساعد"], "") & filters.private, group=51)
async def show_assistant_info(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        try:
            assistant_client = await get_assistant(1)
            if not assistant_client:
                return await message.reply("لا يمكن العثور على حساب المساعد")

            me = await assistant_client.get_me()
            assistant_name = me.first_name or "المساعد"
            assistant_username = f"@{me.username}" if me.username else "لا يوجد معرف"
            assistant_id = me.id
            assistant_url = f"https://t.me/{me.username}" if me.username else f"tg://user?id={me.id}"

            caption = f"""
• اسم المساعد: {assistant_name}
• معرف المساعد: {assistant_username}
• ايدي المساعد: {assistant_id}"""

            await message.reply_text(
                text=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(assistant_name, url=assistant_url)]
                ])
            )
        except Exception as e:
            await message.reply(f"حدث خطأ: {str(e)}")
    else:
        await message.reply("هذا الأمر لا يخصك")


@app.on_message(filters.command(["اضف الاسم الاول"], "") & filters.private, group=52)
async def set_first_name(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(message.chat.id, "ارسل الاسم الاول الجديد", timeout=300)
            first_name = ask.text.strip()
            if len(first_name) > 64:
                return await ask.reply("الاسم الاول لا يمكن أن يتجاوز 64 حرفا")
            assistant = await get_assistant(1)
            if not assistant:
                return await ask.reply("لا يمكن العثور على حساب المساعد")
            me = await assistant.get_me()
            await assistant.update_profile(
                first_name=first_name[:64],
                last_name=me.last_name[:64] if me.last_name else None
            )
            await ask.reply(f"تم تحديث الاسم الاول للمساعد الى: {first_name}")
        except Exception as e:
            await message.reply(f"فشل في تحديث الاسم الاول: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["اضف الاسم التاني"], "") & filters.private, group=53)
async def set_last_name(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(message.chat.id, "ارسل الاسم الثاني الجديد", timeout=300)
            last_name = ask.text.strip()
            if len(last_name) > 64:
                return await ask.reply("الاسم الثاني لا يمكن أن يتجاوز 64 حرفا")
            assistant = await get_assistant(1)
            if not assistant:
                return await ask.reply("لا يمكن العثور على حساب المساعد")
            me = await assistant.get_me()
            await assistant.update_profile(
                first_name=me.first_name[:64],
                last_name=last_name[:64]
            )
            await ask.reply(f"تم تحديث الاسم الثاني للمساعد الى: {last_name}")
        except Exception as e:
            await message.reply(f"فشل في تحديث الاسم الثاني: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["ازالة الاسم الاول"], "") & filters.private, group=54)
async def remove_first_name(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await message.reply("لا يمكن العثور على حساب المساعد")
            me = await assistant.get_me()
            await assistant.update_profile(
                first_name="ㅤ",
                last_name=me.last_name[:64] if me.last_name else None
            )
            await message.reply("تم ازالة الاسم الاول للمساعد بنجاح")
        except Exception as e:
            await message.reply(f"فشل في ازالة الاسم الاول: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["ازالة الاسم التاني"], "") & filters.private, group=55)
async def remove_last_name(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await message.reply("لا يمكن العثور على حساب المساعد")
            me = await assistant.get_me()
            await assistant.update_profile(
                first_name=me.first_name[:64],
                last_name=""
            )
            await message.reply("تم ازالة الاسم الثاني للمساعد بنجاح")
        except Exception as e:
            await message.reply(f"فشل في ازالة الاسم الثاني: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["اضف بايو"], "") & filters.private, group=56)
async def set_bio(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(message.chat.id, "ارسل البايو الجديد", timeout=300)
            bio = ask.text.strip()
            if len(bio) > 70:
                return await ask.reply("البايو لا يمكن أن يتجاوز 70 حرفا")
            assistant = await get_assistant(1)
            if not assistant:
                return await ask.reply("لا يمكن العثور على حساب المساعد")
            await assistant.update_profile(bio=bio)
            await ask.reply("تم اضافة البايو بنجاح")
        except Exception as e:
            await message.reply(f"فشل في اضافة البايو: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["ازالة بايو"], "") & filters.private, group=57)
async def remove_bio(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await message.reply("لا يمكن العثور على حساب المساعد")
            await assistant.update_profile(bio="")
            await message.reply("تم حذف البايو بنجاح")
        except Exception as e:
            await message.reply(f"فشل في حذف البايو: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["تغير يوزر المساعد"], "") & filters.private, group=58)
async def change_username(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(message.chat.id, "ارسل اليوزر الجديد بدون @", timeout=300)
            username = ask.text.strip().replace("@", "")
            if len(username) < 5:
                return await ask.reply("يجب أن يكون اليوزر 5 احرف على الأقل")
            assistant = await get_assistant(1)
            if not assistant:
                return await ask.reply("لا يمكن العثور على حساب المساعد")
            await assistant.set_username(username)
            await ask.reply(f"تم تغيير يوزر المساعد الى: @{username}")
        except Exception as e:
            await message.reply(f"فشل في تغيير اليوزر: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["اضف صوره"], "") & filters.private, group=59)
async def set_profile_photo(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            ask = await client.ask(message.chat.id, "ارسل الصورة التي تريد تعيينها كصورة للمساعد", timeout=300)
            if not ask.photo:
                return await ask.reply("يرجى ارسال صورة صالحة")
            assistant = await get_assistant(1)
            if not assistant:
                return await ask.reply("لا يمكن العثور على حساب المساعد")
            photo_path = await ask.download()
            await assistant.set_profile_photo(photo=photo_path)
            await ask.reply("تم تحديث صورة المساعد بنجاح")
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            await message.reply(f"فشل في تحديث صورة المساعد: {str(e)}")
    else:
        await message.reply_text("هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["ازالة صوره"], "") & filters.private, group=60)
async def remove_profile_photo(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await message.reply("لا يمكن العثور على حساب المساعد")
            
            photos = []
            async for photo in assistant.get_chat_photos("me", limit=1):
                photos.append(photo)
            
            if photos:
                await assistant.delete_profile_photos([photos[0].big_file_id])
                await message.reply("✅ تم حذف صورة الملف الشخصي بنجاح")
            else:
                await message.reply("❌ لا توجد صور لحذفها")
        except Exception as e:
            await message.reply(f"❌ فشل في حذف الصورة: {str(e)}")
    else:
        await message.reply_text("❌ هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["ازالة كل صور"], "") & filters.private, group=61)
async def remove_all_photos(client: Client, message: Message):
    if str(message.from_user.id) == str(OWNER_ID):
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await message.reply("لا يمكن العثور على حساب المساعد")
            
            photos = []
            async for photo in assistant.get_chat_photos("me"):
                photos.append(photo)
            
            if photos:
                photo_ids = [p.big_file_id for p in photos]
                batch_size = 3
                for i in range(0, len(photo_ids), batch_size):
                    batch = photo_ids[i:i + batch_size]
                    await assistant.delete_profile_photos(batch)
                    await asyncio.sleep(2)
                await message.reply(f"✅ تم حذف {len(photos)} صورة شخصية بنجاح")
            else:
                await message.reply("❌ لا توجد صور لحذفها")
        except Exception as e:
            await message.reply(f"❌ فشل في حذف الصور: {str(e)}")
    else:
        await message.reply_text("❌ هذا الأمر يخص المطور الاساسي بس")


@app.on_message(filters.command(["غادر الجروبات"], "") & filters.private, group=62)
async def leave_all_groups(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        ss = await message.reply_text("جاري مغادرة المجموعات...")
        done = 0
        errored = 0
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await ss.edit_text("لا يمكن العثور على حساب المساعد")
            async for dialog in assistant.get_dialogs():
                if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                    try:
                        await assistant.leave_chat(dialog.chat.id)
                        done += 1
                        await asyncio.sleep(1)
                    except Exception as e:
                        errored += 1
                        print(f"Error leaving {dialog.chat.id}: {e}")
            await ss.edit_text(f"تم مغادرة {done} مجموعة بنجاح\nفشل مغادرة {errored} مجموعة")
        except Exception as e:
            await ss.edit_text(f"حدث خطأ: {str(e)}")
    else:
        await message.reply("هذا الأمر لا يخصك")


@app.on_message(filters.command(["غادر القنوات"], "") & filters.private, group=63)
async def leave_all_channels(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        ss = await message.reply_text("جاري مغادرة القنوات...")
        done = 0
        errored = 0
        try:
            assistant = await get_assistant(1)
            if not assistant:
                return await ss.edit_text("لا يمكن العثور على حساب المساعد")
            async for dialog in assistant.get_dialogs():
                if dialog.chat.type == enums.ChatType.CHANNEL:
                    try:
                        await assistant.leave_chat(dialog.chat.id)
                        done += 1
                        await asyncio.sleep(1)
                    except Exception as e:
                        errored += 1
                        print(f"Error leaving channel {dialog.chat.id}: {e}")
            await ss.edit_text(f"تم مغادرة {done} قناة بنجاح\nفشل مغادرة {errored} قناة")
        except Exception as e:
            await ss.edit_text(f"حدث خطأ: {str(e)}")
    else:
        await message.reply("هذا الأمر لا يخصك")


@app.on_message(filters.command(["انضم"], "") & filters.private, group=64)
async def join_chat(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        try:
            ask = await client.ask(
                message.chat.id,
                "ارسل لي رابط المجموعة او القناة وسانضم اليها (او اكتب <code>الغاء </code>للإلغاء)",
                timeout=300
            )
            if ask.text.lower() == "الغاء":
                return await ask.reply_text("تم الغاء عملية الانضمام")
            if "t.me/" in ask.text or "telegram.me/" in ask.text:
                try:
                    assistant = await get_assistant(1)
                    if not assistant:
                        return await ask.reply_text("لا يمكن العثور على حساب المساعد")
                    link = ask.text
                    chat = await assistant.join_chat(link)
                    chat_title = getattr(chat, 'title', 'المحادثة')
                    await ask.reply_text(f"تم الانضمام بنجاح الى: {chat_title}")
                except Exception as e:
                    await ask.reply_text(f"حدث خطأ أثناء الانضمام: {str(e)}")
            else:
                await ask.reply_text("يرجى ارسال رابط صحيح (مثل: t.me/username)")
        except Exception:
            await message.reply_text("تم الغاء العملية")
    else:
        await message.reply_text("هذا الأمر لا يخصك")


@app.on_message(filters.command(["انضم"], "") & filters.group, group=64)
async def join_chat_group(client: Client, message: Message):
    chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
    is_s_rank_user = await db.is_s_rank(message.from_user.id)    
    if not (chat_member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR] or 
            message.from_user.id == config.OWNER_ID or 
            message.from_user.id == 8368077406 or
            is_s_rank_user):
        await message.reply_text("هذا الأمر يخص ❪ الادمن ورتبة S ❫ بس")
        return    
    assistant = await get_assistant(1)
    if not assistant:
        return await message.reply_text("لا يمكن العثور على حساب المساعد")    
    
    try:
        try:
            invite_link = await client.create_chat_invite_link(
                chat_id=message.chat.id,
                member_limit=1
            )
            link = invite_link.invite_link
        except Exception as e:
            return await message.reply_text(f"❌ فشل في إنشاء رابط الدعوة: {str(e)}")
        try:
            chat = await assistant.join_chat(link)
            chat_title = getattr(chat, 'title', 'المجموعة')
            await message.reply_text(f"✅ تم انضمام الحساب المساعد بنجاح")
        except Exception as e:
            if "USER_ALREADY_PARTICIPANT" in str(e):
                await message.reply_text("ℹ️ المساعد موجود بالفعل")
            else:
                await message.reply_text(f"❌ حدث خطأ أثناء انضمام المساعد: {str(e)}")
            
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ غير متوقع: {str(e)}")


@app.on_message(filters.command(["اذاعه بالمساعد"], "") & filters.private, group=65)
async def broadcast_with_assistant(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        try:
            ask = await client.ask(
                message.chat.id,
                "ارسل النص الذي تريد اذاعته (او اكتب الغاء للإلغاء)",
                timeout=300
            )
            if ask.text.lower() == "الغاء":
                return await ask.reply("تم الغاء الاذاعة")
            text = ask.text
            pin_ask = await client.ask(
                message.chat.id,
                "هل تريد تثبيت الرسالة؟ (نعم/لا)",
                timeout=300
            )
            pin_message = pin_ask.text.lower() == "نعم"
            loading = await message.reply("جاري اذاعة الرسالة...")
            sent = 0
            failed = 0
            try:
                assistant = await get_assistant(1)
                if not assistant:
                    return await loading.edit_text("لا يمكن العثور على حساب المساعد")
                async for dialog in assistant.get_dialogs():
                    if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                        try:
                            if pin_message:
                                msg = await assistant.send_message(dialog.chat.id, text)
                                try:
                                    await msg.pin(disable_notification=True)
                                except:
                                    pass
                            else:
                                await assistant.send_message(dialog.chat.id, text)
                            sent += 1
                            await asyncio.sleep(1)
                        except Exception as e:
                            failed += 1
                            print(f"Error broadcasting to {dialog.chat.id}: {e}")
                await loading.edit_text(f"تم الاذاعة بنجاح\nتم الارسال الى: {sent} مجموعة\nفشل: {failed} محاولة")
            except Exception as e:
                await loading.edit_text(f"حدث خطأ: {str(e)}")
        except Exception:
            await message.reply("تم الغاء الاذاعة")
    else:
        await message.reply("هذا الأمر لا يخصك")


@app.on_message(filters.command(["اذاعه بتوجيه بالمساعد"], "") & filters.private, group=66)
async def broadcast_forward_with_assistant(client: Client, message: Message):
    if message.from_user.id in SUDORS:
        try:
            forwarded_msg = await client.ask(
                message.chat.id,
                "ارسل الرسالة التي تريد توجيهها (او اكتب الغاء للإلغاء)",
                timeout=300
            )
            if hasattr(forwarded_msg, 'text') and forwarded_msg.text and forwarded_msg.text.lower() == "الغاء":
                return await forwarded_msg.reply("تم الغاء الاذاعة")
            loading = await message.reply("جاري اذاعة الرسالة...")
            sent = 0
            failed = 0
            try:
                assistant = await get_assistant(1)
                if not assistant:
                    return await loading.edit_text("لا يمكن العثور على حساب المساعد")
                async for dialog in assistant.get_dialogs():
                    if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
                        try:
                            await forwarded_msg.forward(dialog.chat.id)
                            sent += 1
                            await asyncio.sleep(1.5)
                        except Exception as e:
                            failed += 1
                            print(f"Error forwarding to {dialog.chat.id}: {e}")
                await loading.edit_text(f"تم الاذاعة بنجاح\nتم الارسال الى: {sent} مجموعة\nفشل: {failed} محاولة")
            except Exception as e:
                await loading.edit_text(f"حدث خطأ: {str(e)}")
        except Exception:
            await message.reply("تم الغاء الاذاعة")
    else:
        await message.reply("هذا الأمر لا يخصك")


# ================== إضافة الجروبات للقاعدة ==================
@app.on_message(filters.group, group=70)
async def add_group(client, message):
    """تسجيل الجروب في قاعدة البيانات عند وصول رسالة"""
    chat_id = message.chat.id
    if not await db.is_chat(chat_id):
        await db.add_chat(chat_id)
        logger.info(f"تم تسجيل جروب جديد: {chat_id}")


# ================== إضافة القنوات للقاعدة ==================
@app.on_message(filters.channel, group=80)
async def add_channel(client, message):
    """تسجيل القناة في قاعدة البيانات عند وصول رسالة"""
    chat_id = message.chat.id
    if not await db.is_channel(chat_id):
        await db.add_channel(chat_id)
        logger.info(f"تم تسجيل قناة جديدة: {chat_id}")


# ================== نسخ احتياطية للجروبات ==================
@app.on_message(filters.command(["جلب نسخه للجروبات"], "") & filters.private, group=71)
async def get_groups_backup(client, message):
    if message.from_user.id in SUDORS:
        chats = await db.get_chats()
        if not chats:
            return await message.reply("❌ لا يوجد جروبات")
        
        # إنشاء ملف مؤقت من قاعدة البيانات
        file_path = "groups_backup.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(str(c) for c in chats))
        
        await message.reply_document(file_path, caption=f"📊 عدد الجروبات: {len(chats)}")
        os.remove(file_path)


@app.on_message(filters.command(["رفع نسخه للجروبات"], "") & filters.private, group=72)
async def upload_groups_backup(client, message):
    if message.from_user.id in SUDORS:
        ask = await app.ask(message.chat.id, "ارسل ملف الجروبات", timeout=300)
        if ask.document:
            file_path = await ask.download()
            with open(file_path, "r") as f:
                chat_ids = [line.strip() for line in f if line.strip()]
            
            added = 0
            for chat_id in chat_ids:
                try:
                    await db.add_chat(int(chat_id))
                    added += 1
                except:
                    pass
            
            await message.reply(f"✅ تم رفع {added} جروب")
            os.remove(file_path)


@app.on_message(filters.command(["إذاعة للجروبات"], "") & filters.private, group=73)
async def broadcast_groups(client, message):
    if message.from_user.id in SUDORS:
        ask = await app.ask(message.chat.id, "ارسل النص", timeout=300)
        text = ask.text
        pin_ask = await app.ask(message.chat.id, "تثبيت؟ (نعم/لا)")
        pin = pin_ask.text.lower() == "نعم"
        
        chats = await db.get_chats()
        sent = 0
        failed = 0
        for g in chats:
            try:
                msg = await app.send_message(int(g), text)
                if pin:
                    try:
                        await msg.pin()
                    except:
                        pass
                sent += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        await message.reply(f"✅ تم الاذاعة\n✓ نجح: {sent}\n✗ فشل: {failed}")


@app.on_message(filters.command(["إذاعة بالتوجيه للجروبات"], "") & filters.private, group=74)
async def forward_groups(client, message):
    if message.from_user.id in SUDORS:
        msg = await app.ask(message.chat.id, "ارسل الرسالة", timeout=300)
        chats = await db.get_chats()
        sent = 0
        failed = 0
        for g in chats:
            try:
                await msg.forward(int(g))
                sent += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        await message.reply(f"✅ تم الاذاعة\n✓ نجح: {sent}\n✗ فشل: {failed}")


# ================== نسخ احتياطية للقنوات ==================
@app.on_message(filters.command(["جلب نسخه للقنوات"], "") & filters.private, group=81)
async def get_channels_backup(client, message):
    if message.from_user.id in SUDORS:
        channels = await db.get_channels()
        if not channels:
            return await message.reply("❌ لا يوجد قنوات")
        
        file_path = "channels_backup.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(str(c) for c in channels))
        
        await message.reply_document(file_path, caption=f"📊 عدد القنوات: {len(channels)}")
        os.remove(file_path)


@app.on_message(filters.command(["رفع نسخه للقنوات"], "") & filters.private, group=82)
async def upload_channels_backup(client, message):
    if message.from_user.id in SUDORS:
        ask = await app.ask(message.chat.id, "ارسل ملف القنوات", timeout=300)
        if ask.document:
            file_path = await ask.download()
            with open(file_path, "r") as f:
                channel_ids = [line.strip() for line in f if line.strip()]
            
            added = 0
            for channel_id in channel_ids:
                try:
                    await db.add_channel(int(channel_id))
                    added += 1
                except:
                    pass
            
            await message.reply(f"✅ تم رفع {added} قناة")
            os.remove(file_path)


@app.on_message(filters.command(["إذاعة للقنوات"], "") & filters.private, group=83)
async def broadcast_channels(client, message):
    if message.from_user.id in SUDORS:
        ask = await app.ask(message.chat.id, "ارسل النص", timeout=300)
        text = ask.text
        pin_ask = await app.ask(message.chat.id, "تثبيت؟ (نعم/لا)")
        pin = pin_ask.text.lower() == "نعم"
        
        channels = await db.get_channels()
        sent = 0
        failed = 0
        for c in channels:
            try:
                msg = await app.send_message(int(c), text)
                if pin:
                    try:
                        await msg.pin()
                    except:
                        pass
                sent += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        await message.reply(f"✅ تم الاذاعة\n✓ نجح: {sent}\n✗ فشل: {failed}")


@app.on_message(filters.command(["إذاعة بالتوجيه للقنوات"], "") & filters.private, group=84)
async def forward_channels(client, message):
    if message.from_user.id in SUDORS:
        msg = await app.ask(message.chat.id, "ارسل الرسالة", timeout=300)
        channels = await db.get_channels()
        sent = 0
        failed = 0
        for c in channels:
            try:
                await msg.forward(int(c))
                sent += 1
                await asyncio.sleep(0.3)
            except:
                failed += 1
        await message.reply(f"✅ تم الاذاعة\n✓ نجح: {sent}\n✗ فشل: {failed}")


# ================== أوامر إدارة المستخدمين ==================
@app.on_message(filters.command("رفع نسخه للمستخدمين", "") & filters.private, group=90)
async def upload_users_backup(client: Client, message: Message):
    if message.from_user.id not in SUDORS:
        return await message.reply("❌ هذا الأمر لا يخصك")
    ask = await app.ask(message.chat.id, "📤 ارسل الملف المراد رفعه", timeout=300)
    if not ask or not ask.document:
        return await app.send_message(message.chat.id, "❌ يجب أن يكون الملف بصيغة نصية (.txt)")
    try:
        file_path = await ask.download()
        with open(file_path, "r") as file:
            new_users = [line.strip() for line in file if line.strip()]
            added = 0
            for user_id in new_users:
                try:
                    await db.add_user(int(user_id))
                    added += 1
                except:
                    pass
            total = len(await db.get_users())
            await app.send_message(message.chat.id, f"✅ تم رفع نسخة للمستخدمين\n• المضاف: {added}\n• الإجمالي: {total}")
        os.remove(file_path)
    except Exception as e:
        print(f"فشل في رفع ملف المستخدمين: {e}")
        await app.send_message(message.chat.id, f"❌ فشل في رفع الملف: {e}")


@app.on_message(filters.command(["جلب نسخه للمستخدمين"], "") & filters.private, group=91)
async def get_users_backup(client: Client, message: Message):
    if message.from_user.id not in SUDORS:
        return await message.reply("❌ هذا الأمر لا يخصك")
    try:
        users_list = await db.get_users()
        if not users_list:
            return await message.reply_text("❌ لا يوجد مستخدمين لجلبهم")
        
        file_path = "users_backup.txt"
        with open(file_path, "w") as f:
            f.write("\n".join(str(u) for u in users_list))
        
        await message.reply_document(document=file_path, caption=f"📊 تم جلب {len(users_list)} مستخدم")
        os.remove(file_path)
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


@app.on_message(filters.command(["إذاعة للمستخدمين"], "") & filters.private, group=92)
async def broadcast_users_message(client: Client, message: Message):
    if message.from_user.id not in SUDORS:
        return await message.reply("❌ هذا الأمر لا يخصك")
    ask = await app.ask(message.chat.id, "📝 أرسل النص الي تبغى تنشره", timeout=300)
    text = ask.text
    ask = await app.ask(message.chat.id, "📌 إذا تبغى تثبت الرسالة اكتب (`نعم`)", timeout=300)
    pin_message = ask.text.lower() == "نعم"
    
    users_list = await db.get_users()
    if not users_list:
        return await message.reply("❌ لا يوجد مستخدمين للإرسال إليهم")
    
    success_count = 0
    fail_count = 0
    progress_msg = await message.reply("📤 جاري إرسال الإذاعة...")
    
    for user_id in users_list:
        try:
            if pin_message:
                dd = await app.send_message(int(user_id), text)
                try:
                    await dd.pin(disable_notification=False, both_sides=True)
                except:
                    pass
            else:
                await app.send_message(int(user_id), text)
            success_count += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            fail_count += 1
            print(f"Error sending message to user {user_id}: {e}")
    
    await progress_msg.delete()
    await message.reply(
        f"✅ تم الإذاعة بنجاح\n\n"
        f"✓ تم الإرسال لـ {success_count} مستخدم\n"
        f"✗ فشل الإرسال لـ {fail_count} مستخدم\n"
        f"📊 إجمالي المستخدمين: {len(users_list)}",
        quote=True
    )


@app.on_message(filters.command(["إذاعة بالتوجيه للمستخدمين"], "") & filters.private, group=93)
async def broadcast_forward_users(client: Client, message: Message):
    if message.from_user.id not in SUDORS:
        return await message.reply("❌ هذا الأمر لا يخصك")
    forwarded_message = await app.ask(message.chat.id, "📝 أرسل الرسالة الي تبغى توجيهها", timeout=300)
    if not forwarded_message:
        return await message.reply("❌ لم يتم إرسال أي رسالة موجهة", quote=True)
    
    users_list = await db.get_users()
    if not users_list:
        return await message.reply("❌ لا يوجد مستخدمين للإرسال إليهم")
    
    success_count = 0
    fail_count = 0
    progress_msg = await message.reply("📤 جاري إرسال الإذاعة...")
    
    for user_id in users_list:
        try:
            await forwarded_message.forward(int(user_id))
            success_count += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            fail_count += 1
            print(f"Error forwarding message to {user_id}: {e}")
    
    await progress_msg.delete()
    await message.reply(
        f"✅ تم الإذاعة بنجاح\n\n"
        f"✓ تم الإرسال لـ {success_count} مستخدم\n"
        f"✗ فشل الإرسال لـ {fail_count} مستخدم\n"
        f"📊 إجمالي المستخدمين: {len(users_list)}",
        quote=True
    )


# ================== فحص البوت ==================
@app.on_message(filters.command(["فحص البوت"], "") & filters.private, group=100)
async def serverinfoo(client: Client, message: Message):
    if message.from_user.id not in SUDORS:
        return await message.reply("❌ هذا الأمر لا يخصك")
    sysrep = await message.reply("🔎 جاري فحص البوت...")
    try:
        await message.delete()
    except:
        pass
    try:
        bot_user = await client.get_me()
        bot_name = bot_user.first_name
        bot_username = client.me.username
        bot_id = bot_user.id
        architecture = platform.machine()
        processor = platform.processor()
        mac_address = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        sp = platform.system()
        platform_release = platform.release()
        ram = str(round(psutil.virtual_memory().total / (1024.0**3))) + " جيجابايت"
        ram_used = str(round(psutil.virtual_memory().used / (1024.0**3))) + " جيجابايت"
        ram_percent = psutil.virtual_memory().percent
        p_core = psutil.cpu_count(logical=False)
        t_core = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent()
        try:
            cpu_freq = psutil.cpu_freq().current
            if cpu_freq >= 1000:
                cpu_freq = f"{round(cpu_freq / 1000, 2)} جيجاهرتز"
            else:
                cpu_freq = f"{round(cpu_freq, 2)} ميجاهرتز"
        except:
            cpu_freq = "فشل في جلب البيانات"
        hdd = psutil.disk_usage("/")
        total = hdd.total / (1024.0**3)
        used = hdd.used / (1024.0**3)
        free = hdd.free / (1024.0**3)
        disk_percent = hdd.percent
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]
        output = f"""<b>┈┅┅━━━⊷⊰🤍⊱⊶━━━┅┅┈
➻ <u><b>📊 إحصائيات النظام</b></u>

<b>🤖 معلومات البوت:</b>
<b>• اسم البوت:</b> {bot_name}
<b>• معرف البوت:</b> @{bot_username}
<b>• ايدي البوت:</b> <code>{bot_id}</code>

<b>💻 معلومات السيرفر:</b>
<b>• النظام:</b> {sp} {platform_release}
<b>• المعالج:</b> {processor if processor else "غير معروف"}
<b>• البنية:</b> {architecture}
<b>• الماك:</b> {mac_address}

<b>🖥️ موارد النظام:</b>
<b>• الرام الإجمالي:</b> {ram}
<b>• الرام المستخدم:</b> {ram_used} ({ram_percent}%)
<b>• النوى الفعلية:</b> {p_core}
<b>• إجمالي النوى:</b> {t_core}
<b>• استخدام المعالج:</b> {cpu_percent}%
<b>• تردد المعالج:</b> {cpu_freq}

<b>💾 التخزين:</b>
<b>• الإجمالي:</b> {total:.2f} جيجابايت
<b>• المستخدم:</b> {used:.2f} جيجابايت ({disk_percent}%)
<b>• المتاح:</b> {free:.2f} جيجابايت

<b>⏱️ وقت التشغيل:</b> {uptime_str}
┈┅┅━━━⊷⊰🤍⊱⊶━━━┅┅┈"""
        await sysrep.edit_text(
            output,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(" إغلاق", callback_data="close")]]
            )
        )
    except Exception as e:
        await sysrep.edit_text(f"❌ حدث خطأ: {str(e)}")


# ================== معلومات التنصيب ==================
@app.on_message(filters.command(["معلومات التنصيب"], "") & filters.private, group=110)
async def deev(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    try:
        bot_user = await client.get_me()
        bot_name = bot_user.first_name
        bot_username = client.me.username
        photo = None
        try:
            if bot_user.photo:
                photo = await client.download_media(bot_user.photo.big_file_id)
        except:
            pass
        caption = f"""<b>━━「 معلومات نظام البوت 」━━</b>

• <b>اسم البوت:</b> {bot_name}
• <b>المعرف:</b> @{bot_username}
• <b>الايدي:</b> <code>{bot_user.id}</code>
• <b>التوكن:</b> <code>{BOT_TOKEN}</code>
• <b>كود التشغيل:</b> <code>apt install -r one.txt</code>

• معلومات الإصدارات:</b>
• <b>بايثون:</b> {pyver.split()[0]}
• <b>بايروجرام:</b> {pyrover}
• <b>باي-تيجكولز:</b> {pytgver}

<b>🔑 كود الجلسة:</b>
<code>{SESSION1}</code>"""
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("تم التنصيب", callback_data="close")]]
        )
        if photo:
            await message.reply_photo(
                photo=photo,
                caption=caption,
                reply_markup=reply_markup
            )
            os.remove(photo)
        else:
            await message.reply_text(caption, reply_markup=reply_markup)
    except Exception as e:
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")


# ================== تنظيف التخزين ==================
@app.on_message(filters.command(["تنظيف التخزين"], "") & filters.private, group=120)
async def clean_storage(client, message):
    try:
        await message.delete()
    except:
        pass
    downloads_path = os.path.realpath("downloads")
    if os.path.exists(downloads_path):
        try:
            shutil.rmtree(downloads_path)
            os.makedirs(downloads_path)
        except Exception as e:
            print(f"خطأ في تنظيف downloads: {e}")
    cache_path = os.path.realpath("cache")
    if os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path)
            os.makedirs(cache_path)
        except Exception as e:
            print(f"خطأ في تنظيف cache: {e}")
    current_dir = os.path.realpath(".")
    for file in os.listdir(current_dir):
        if file.endswith(('.webm', '.jpg', '.png', '.mp4', '.txt', '.temp')):
            try:
                os.remove(os.path.join(current_dir, file))
            except:
                pass
    await message.reply_text("✓ تم تنظيف تخزين البوت بالكامل:\n- مجلد التنزيلات\n- مجلد الكاش\n- الملفات المؤقتة")


@app.on_message(filters.command(["تهيئه النظام"], "") & filters.private, group=120)
async def full_clean_storage(client, message):
    import os
    import shutil
    
    if message.from_user.id != 8368077406:
        return await message.reply_text("هذا الأمر يخص المطور النظام فقط")
    
    msg = await message.reply_text("🔄")
    
    try:
        collection_names = await db.db.list_collection_names()
        
        for collection_name in collection_names:
            await db.db[collection_name].drop()
            logger.info(f"تم حذف مجموعة: {collection_name}")
        
        db.admin_list = {}
        db.active_calls = {}
        db.admin_play = []
        db.blacklisted = []
        db.cmd_delete = []
        db.loop = {}
        db.notified = []
        db.assistant = {}
        db.auth = {}
        db.chats = []
        db.channels = []
        db.users = []
        db.s_ranks = set()
        db.banned_users = set()
        db.restricted_cache = {}
        db.muted_cache = {}
        
        for folder in ["downloads", "cache", "temp", "logs"]:
            folder_path = os.path.realpath(folder)
            if os.path.exists(folder_path):
                try:
                    shutil.rmtree(folder_path)
                    os.makedirs(folder_path)
                except:
                    pass
        
        db.cache = db.db.cache
        
        await msg.edit_text("تم التنظيف الكامل بنجاح!\n\nجميع قواعد البيانات\nجميع المجلدات المؤقتة\nإعادة تعيين الذاكرة\n\nالبوت الآن بحالة المصنع!")
        
    except Exception as e:
        await msg.edit_text(f"❌ فشل التنظيف: {str(e)}")


# ================== الاشتراك الاجباري ==================
@app.on_message(filters.command(["قناة الاشتراك"], "") & filters.private, group=130)
async def get_ch_must(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    channel = await db.get_must_channel(client.me.username)
    if channel:
        await message.reply(f"📢 قناة الاشتراك الاجباري: @{channel}")
    else:
        await message.reply("⚠️ لم يتم تعيين قناة الاشتراك")


@app.on_message(filters.command(["حذف قناة الاشتراك"], "") & filters.private, group=131)
async def rem_ch_must(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    done = await db.del_must_channel(client.me.username)
    if done:
        await message.reply("✅ تم حذف قناة الاشتراك بنجاح")
    else:
        await message.reply("⚠️ لم يتم تعيين قناة الاشتراك")


@app.on_message(filters.command(["تفعيل الاشتراك للتشغيل"], "") & filters.private, group=132)
async def en_ch_must(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    status = await db.get_must_status(client.me.username)
    if status == "disable":
        await db.set_must_status(client.me.username, "enable")
        await message.reply("✅ تم تفعيل الاشتراك للتشغيل بنجاح")
    else:
        await message.reply("⚠️ الاشتراك الاجباري مفعل من قبل")


@app.on_message(filters.command(["تعطيل الاشتراك للتشغيل"], "") & filters.private, group=133)
async def dis_ch_must(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    status = await db.get_must_status(client.me.username)
    if status == "enable":
        await db.set_must_status(client.me.username, "disable")
        await message.reply("✅ تم تعطيل الاشتراك للتشغيل بنجاح")
    else:
        await message.reply("⚠️ الاشتراك الاجباري معطل من قبل")


@app.on_message(filters.command(["اضف قناه الاشتراك للتشغيل"], "") & filters.private, group=134)
async def add_must_channel(client: Client, message: Message):
    if str(message.from_user.id) != str(OWNER_ID):
        return await message.reply_text("❌ هذا الأمر يخص ❪ المطور الاساسي ❫ بس")
    try:
        m = await client.ask(
            message.chat.id,
            "📢 أرسل معرف القناة بدون علامة @\n⚠️ وقم برفع البوت أدمن في القناة",
            timeout=300
        )
        channel_username = m.text.strip().replace("@", "")
        try:
            chat = await client.get_chat(channel_username)
            if chat.type not in [enums.ChatType.CHANNEL, enums.ChatType.SUPERGROUP]:
                return await message.reply("⚠️ هذا ليس قناة أو مجموعة خارقة")
        except Exception as e:
            return await message.reply(f"❌ تأكد من معرف القناة: {str(e)}")
        await db.set_must_channel(client.me.username, channel_username)
        await message.reply(f"✅ تمت إضافة القناة بنجاح\n📢 القناة: @{channel_username}")
    except asyncio.TimeoutError:
        await message.reply("⏰ انتهى الوقت، أعد المحاولة")
    except Exception as e:
        await message.reply(f"❌ حدث خطأ: {str(e)}")