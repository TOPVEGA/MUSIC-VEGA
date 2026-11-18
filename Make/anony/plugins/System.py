import json
import os
import kurimod
from typing import Union
from pyrogram import filters, Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from anony import app, anon, db, config
from anony.helpers.admins import is_owner, banned_check


# ========== المتغيرات العامة ==========
OWNER_ID = config.OWNER_ID
SUPPORT_CHANNEL = config.SUPPORT_CHANNEL
SUPPORT_CHAT = config.SUPPORT_CHAT
ONE_VIDEO_URL = config.ONE_VIDEO_URL


# ========== الإعدادات الافتراضية ==========
DEFAULT_MAIN_MENU = {
    "caption": """<b>
• بوت تشغيل أغاني - للمحادثات صوتيه 

• ترخيص بواسطة: @TopVeGa
• العلامة التجارية: VEGA & SOUND™
• حقوق الطبع والنشر: © 2015 - 2025</b>\nㅤ""",
    "buttons": [
        {"text": "ᴠᴇɢᴀ", "url": "{SUPPORT_CHANNEL}"}
    ],
    "media": ONE_VIDEO_URL,
}


# ========== دوال حفظ واسترجاع الإعدادات (مرتبطة بمعرّف البوت) ==========
async def save_source_caption(client, caption: str) -> None:
    await db.set_source_customization(client.me.id, "caption", caption)


async def get_source_caption(client) -> str:
    return await db.get_source_customization(client.me.id, "caption") or DEFAULT_MAIN_MENU["caption"]


async def save_source_buttons(client, buttons: list) -> None:
    await db.set_source_customization(client.me.id, "buttons", buttons)


async def get_source_buttons(client) -> list:
    buttons = await db.get_source_customization(client.me.id, "buttons")
    if not buttons:
        return DEFAULT_MAIN_MENU["buttons"].copy()
    return buttons


async def save_source_media(client, media_path: str) -> None:
    await db.set_source_customization(client.me.id, "media", media_path)


async def get_source_media(client) -> str:
    return await db.get_source_customization(client.me.id, "media") or DEFAULT_MAIN_MENU["media"]


async def reset_source_customization(client) -> None:
    await db.reset_source_customization(client.me.id)


async def get_source_customization(client):
    customization = DEFAULT_MAIN_MENU.copy()
    caption = await get_source_caption(client)
    buttons = await get_source_buttons(client)
    media = await get_source_media(client)
    
    customization["caption"] = caption
    customization["buttons"] = buttons
    customization["media"] = media
    
    # استبدال المتغيرات في النص
    customization["caption"] = customization["caption"].replace("{SUPPORT_CHANNEL}", SUPPORT_CHANNEL)
    customization["caption"] = customization["caption"].replace("{SUPPORT_CHAT}", SUPPORT_CHAT)
    
    # استبدال المتغيرات في الأزرار
    for button in customization["buttons"]:
        if "url" in button:
            button["url"] = button["url"].replace("{SUPPORT_CHANNEL}", SUPPORT_CHANNEL)
            button["url"] = button["url"].replace("{SUPPORT_CHAT}", SUPPORT_CHAT)
    
    return customization


# ========== دالة إرسال القائمة الرئيسية ==========
async def send_main_menu(target: Union[Message, CallbackQuery], client=None):
    if client is None:
        client = app
    
    customization = await get_source_customization(client)
    
    if isinstance(target, CallbackQuery):
        message = target.message
        edit = True
    else:
        message = target
        edit = False   
    
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(btn["text"], url=btn.get("url"), callback_data=btn.get("callback_data"))] 
         for btn in customization["buttons"]]
    )
    
    if edit:
        await message.edit_text(customization["caption"], reply_markup=markup)
    else:
        media = customization["media"]
        if media and media.endswith((".jpg", ".png", ".jpeg", ".gif")):
            await message.reply_photo(
                photo=media,
                caption=customization["caption"],
                reply_markup=markup,
                show_caption_above_media=True
            )
        elif media and media.endswith((".mp4", ".mov", ".avi")):
            await message.reply_video(
                video=media,
                caption=customization["caption"],
                reply_markup=markup,
                show_caption_above_media=True
            )
        else:
            await message.reply_text(
                customization["caption"],
                reply_markup=markup
            )


# ========== أوامر تخصيص السورس ==========
@app.on_message(filters.command(["تغير كليشه السورس"], "") & filters.private, group=500)
@is_owner
@banned_check
async def change_source_text(client, message):
    try:
        ask = await client.ask(
            message.chat.id,
            "<b>أرسل الكليشة الجديدة للسورس</b>",
            timeout=300
        )
        
        if ask.text:
            await save_source_caption(client, ask.text)
            await message.reply("<b>• تم تغيير كليشة السورس بنجاح</b>")
    except Exception as e:
        await message.reply(f"• فشل في حفظ الكليشة: {str(e)}")


@app.on_message(filters.command(["تغير قناه السورس"], "") & filters.private, group=501)
@is_owner
@banned_check
async def change_vega_button(client: Client, message: Message):
    try:
        ask_text = await client.ask(
            chat_id=message.chat.id,
            text="• أرسل النص الجديد لزر ᴠᴇɢᴀ (مثال: قناة السورس)",
            timeout=300
        )
        
        ask_url = await client.ask(
            chat_id=message.chat.id,
            text="<b>أرسل الرابط الجديد للزر (يجب أن يبدأ بـ https://)</b>",
            timeout=300
        )
        
        if not ask_url.text.startswith(('http://', 'https://')):
            return await message.reply("• الرابط يجب أن يبدأ بـ http:// أو https://")
        
        buttons = await get_source_buttons(client)
        for btn in buttons:
            if btn.get("text", "").lower() == "ᴠᴇɢᴀ".lower():
                btn["text"] = ask_text.text
                btn["url"] = ask_url.text
                break
        else:
            # إذا لم يتم العثور على الزر، نضيفه
            buttons.append({"text": ask_text.text, "url": ask_url.text})
        
        await save_source_buttons(client, buttons)
        await message.reply("<b>• تم تحديث زر ᴠᴇɢᴀ بنجاح</b>")
    except Exception as e:
        await message.reply(f"• فشل في تحديث الزر: {str(e)}")


@app.on_message(filters.command(["اضف زر المطور"], "") & filters.private, group=502)
@is_owner
@banned_check
async def change_dev_button(client: Client, message: Message):
    try:
        ask_text = await client.ask(
            chat_id=message.chat.id,
            text="• أرسل النص الجديد لزر المطور (مثال: 𝙳𝙴𝚅𝙴𝙻𝙾𝙿𝙴𝚁)",
            timeout=300
        )
        
        ask_url = await client.ask(
            chat_id=message.chat.id,
            text="<b>أرسل معرف المطور الجديد (مثال: https://t.me/vegaone)</b>",
            timeout=300
        )
        
        if not ask_url.text.startswith(('http://', 'https://')):
            ask_url.text = f"https://t.me/{ask_url.text.replace('@', '')}"
        
        buttons = await get_source_buttons(client)
        found = False
        for btn in buttons:
            if btn.get("text", "").lower() in ["المطور", "developer"]:
                btn["text"] = ask_text.text
                btn["url"] = ask_url.text
                found = True
                break
        
        if not found:
            buttons.append({"text": ask_text.text, "url": ask_url.text})
        
        await save_source_buttons(client, buttons)
        await message.reply("<b>• تم اضافه زر المطور بنجاح\nتفقد الزر بي بكتابه سورس</b>")
    except Exception as e:
        await message.reply(f"• فشل في تحديث الزر: {str(e)}")


@app.on_message(filters.command(["تغير لوجو السورس"], "") & filters.private, group=503)
@is_owner
@banned_check
async def change_source_media(client, message):
    try:
        ask = await client.ask(
            message.chat.id,
            "<b>أرسل الصورة او الفيديو الجديد (للسورس)</b>",
            timeout=300
        )
        
        if ask.photo or ask.video:
            media_path = await ask.download()
            await save_source_media(client, media_path)
            await message.reply("<b>• تم تغيير لوجو السورس بنجاح</b>")
        else:
            await message.reply("• يجب أن تكون الوسائط صورة أو فيديو")
    except Exception as e:
        await message.reply(f"• فشل في حفظ الوسائط: {str(e)}")


@app.on_message(filters.command(["حذف تخصيص السورس"], "") & filters.private, group=504)
@is_owner
@banned_check
async def reset_source_customization_command(client, message):
    try:
        await reset_source_customization(client)
        await message.reply("• تم حذف التخصيصات بنجاح وإعادة السورس إلى الإعدادات الافتراضية")
    except Exception as e:
        await message.reply(f"• فشل في حذف التخصيصات: {str(e)}")


@app.on_message(filters.command(["سورس", "فيجا", "السورس", "/vega", "/System"], ""), group=505)
@banned_check
async def source_handler(client: Client, message: Message):
    await send_main_menu(message, client)
    




# ========== أوامر تخصيص زر التحكم ==========
@app.on_message(filters.command(["تغير زر التحكم"], "") & filters.private, group=600)
@is_owner
@banned_check
async def change_control_button(client: Client, message: Message):
    try:
        # طلب النص الجديد
        ask_text = await client.ask(
            chat_id=message.chat.id,
            text="<b>• أرسل النص الجديد لزر التحكم</b>\n\n"
                 "<i>• مثال: قناة السورس | 𝙳𝙴𝚅 | 𝚂𝙾𝚄𝚁𝙲𝙴 | فيجا</i>\n"
                 "<b>• يمكنك استخدام إيموجي أو نص عادي</b>",
            timeout=300
        )
        
        if not ask_text.text:
            return await message.reply("<b>❌ لا يمكن ترك النص فارغاً!</b>")
        
        # طلب الرابط الجديد
        ask_url = await client.ask(
            chat_id=message.chat.id,
            text="<b>• أرسل الرابط الجديد للزر</b>\n\n"
                 "<i>• مثال: https://t.me/vegaone</i>\n"
                 "<b>• يمكنك إرسال معرف القناة فقط مثل: @username</b>",
            timeout=300
        )
        
        if not ask_url.text:
            return await message.reply("<b> لا يمكن ترك الرابط فارغاً!</b>")
        
        # معالجة الرابط
        url_text = ask_url.text.strip()
        if not url_text.startswith(('http://', 'https://')):
            # إزالة @ إذا وجدت
            if url_text.startswith('@'):
                url_text = url_text[1:]
            url_text = f"https://t.me/{url_text}"
        
        # حفظ الإعدادات في قاعدة البيانات (مرتبطة بمعرّف البوت)
        await db.set_control_button_text(client.me.id, ask_text.text)
        await db.set_control_button_url(client.me.id, url_text)
        
        # تحديث الكاش
        from anony.helpers.inline import update_control_button_cache
        await update_control_button_cache(client.me.id)
        
        # عرض معاينة للزر الجديد
        preview_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=ask_text.text, url=url_text)]
        ])
        
        await message.reply(
            f"<b>•  تم تحديث زر التحكم بنجاح</b>\n\n"
            f"<u>•  النص الجديد:</u> <code>{ask_text.text}</code>\n"
            f"<u>• الرابط الجديد:</u> <code>{url_text}</code>\n\n"
            f"<i>• معاينة الزر:</i>",
            reply_markup=preview_markup
        )
        
    except TimeoutError:
        await message.reply("<b>تم إلغاء العملية لعدم الاستجابة</b>")
    except Exception as e:
        await message.reply(f"<b> فشل في تحديث زر التحكم:</b>\n<code>{str(e)}</code>")


@app.on_message(filters.command(["حذف زر التحكم", "مسح زر التحكم"], "") & filters.private, group=601)
@is_owner
@banned_check
async def reset_control_button_command(client: Client, message: Message):
    """
    حذف تخصيص زر التحكم والعودة للإعدادات الافتراضية
    """
    try:
        # تأكيد الحذف
        confirm = await client.ask(
            chat_id=message.chat.id,
            text="<b>• هل أنت متأكد من حذف تخصيص زر التحكم؟</b>\n"
                 "<i>• سيتم إعادة الزر إلى الإعدادات الافتراضية: 𝔬𝔫𝔢</i>\n\n"
                 "<b>• أرسل <code>نعم</code> للتأكيد أو أي شيء للإلغاء</b>",
            timeout=60
        )
        
        if confirm.text.lower() not in ['نعم', 'yes', 'y', 'تأكيد']:
            return await message.reply("<b>❌ تم إلغاء العملية</b>")
        
        # حذف التخصيصات
        await db.reset_control_button(client.me.id)
        
        # تحديث الكاش
        from anony.helpers.inline import update_control_button_cache
        await update_control_button_cache(client.me.id)
        
        await message.reply(
            "<b>• تم حذف تخصيص زر التحكم بنجاح</b>\n\n"
            f"<i>• تم إعادة الزر إلى الإعدادات الافتراضية: 𝔬𝔫𝔢</i>\n"
            f"<i>•  الرابط الافتراضي: {config.SUPPORT_CHANNEL}</i>"
        )
        
    except TimeoutError:
        await message.reply("<b>⏰ تم إلغاء العملية لعدم الاستجابة</b>")
    except Exception as e:
        await message.reply(f"<b>❌ فشل في حذف تخصيص الزر:</b>\n<code>{str(e)}</code>")


@app.on_message(filters.command(["عرض زر التحكم", "حالة زر التحكم"], "") & filters.private, group=602)
@is_owner
@banned_check
async def show_control_button(client: Client, message: Message):
    """
    عرض الإعدادات الحالية لزر التحكم
    """
    try:
        # جلب الإعدادات من قاعدة البيانات
        text = await db.get_control_button_text(client.me.id)
        url = await db.get_control_button_url(client.me.id)
        
        # التحقق إذا كانت الإعدادات افتراضية أم مخصصة
        is_default = (text == "𝔬𝔫𝔢" and url == config.SUPPORT_CHANNEL)
        
        # إنشاء معاينة للزر
        preview_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=text, url=url)]
        ])
        
        status_text = "🔵 الإعدادات الافتراضية" if is_default else "🟢 إعدادات مخصصة"
        
        await message.reply(
            f"<b>•  {status_text}</b>\n\n"
            f"<u>• النص الحالي:</u>\n<code>{text}</code>\n\n"
            f"<u>• الرابط الحالي:</u>\n<code>{url}</code>\n\n"
            f"<i>• معاينة الزر:</i>",
            reply_markup=preview_markup
        )
        
    except Exception as e:
        await message.reply(f"<b>❌ فشل في عرض إعدادات الزر:</b>\n<code>{str(e)}</code>")


@app.on_message(filters.command(["تغير نص زر التحكم"], "") & filters.private, group=603)
@is_owner
@banned_check
async def change_control_button_text_only(client: Client, message: Message):
    """
    تغيير نص زر التحكم فقط دون تغيير الرابط
    """
    try:
        # جلب الرابط الحالي
        current_url = await db.get_control_button_url(client.me.id)
        
        # طلب النص الجديد
        ask_text = await client.ask(
            chat_id=message.chat.id,
            text="<b>✨ أرسل النص الجديد لزر التحكم</b>\n"
                 "<b>سيتم تغيير النص فقط</b>",
            timeout=300
        )
        
        if not ask_text.text:
            return await message.reply("<b> لا يمكن ترك النص فارغاً!</b>")
        
        # حفظ النص الجديد فقط
        await db.set_control_button_text(client.me.id, ask_text.text)
        
        # تحديث الكاش
        from anony.helpers.inline import update_control_button_cache
        await update_control_button_cache(client.me.id)
        
        # عرض معاينة
        preview_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=ask_text.text, url=current_url)]
        ])
        
        await message.reply(
            f"<b>•  تم تحديث نص زر التحكم بنجاح</b>\n\n"
            f"<u>•  النص الجديد:</u> <code>{ask_text.text}</code>\n"
            f"<u>•  الرابط (لم يتغير):</u> <code>{current_url}</code>\n\n"
            f"<i>•  معاينة الزر:</i>",
            reply_markup=preview_markup
        )
        
    except TimeoutError:
        await message.reply("<b>⏰ تم إلغاء العملية لعدم الاستجابة</b>")
    except Exception as e:
        await message.reply(f"<b>❌ فشل في تحديث النص:</b>\n<code>{str(e)}</code>")


@app.on_message(filters.command(["تغير رابط زر التحكم"], "") & filters.private, group=604)
@is_owner
@banned_check
async def change_control_button_url_only(client: Client, message: Message):
    try:
        # جلب النص الحالي
        current_text = await db.get_control_button_text(client.me.id)
        
        # طلب الرابط الجديد
        ask_url = await client.ask(
            chat_id=message.chat.id,
            text="<b>• أرسل الرابط الجديد للزر</b>\n\n"
                 f"<i>• النص الحالي: {current_text}</i>\n"
                 "<b>• سيتم تغيير الرابط فقط</b>\n\n"
                 "<i>• مثال: https://t.me/vegaone أو @vegaone</i>",
            timeout=300
        )
        
        if not ask_url.text:
            return await message.reply("<b>❌ لا يمكن ترك الرابط فارغاً!</b>")
        
        url_text = ask_url.text.strip()
        if not url_text.startswith(('http://', 'https://')):
            if url_text.startswith('@'):
                url_text = url_text[1:]
            url_text = f"https://t.me/{url_text}"
        
        await db.set_control_button_url(client.me.id, url_text)
        from anony.helpers.inline import update_control_button_cache
        await update_control_button_cache(client.me.id)
        
        # عرض معاينة
        preview_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=current_text, url=url_text)]
        ])
        
        await message.reply(
            f"<b>• تم تحديث رابط زر التحكم بنجاح</b>\n\n"
            f"<u>• النص (لم يتغير):</u> <code>{current_text}</code>\n"
            f"<u>• الرابط الجديد:</u> <code>{url_text}</code>\n\n"
            f"<i>•  معاينة الزر:</i>",
            reply_markup=preview_markup
        )
        
    except TimeoutError:
        await message.reply("<b>تم إلغاء العملية لعدم الاستجابة</b>")
    except Exception as e:
        await message.reply(f"<b>فشل في تحديث الرابط:</b>\n<code>{str(e)}</code>")
        

@app.on_message(filters.command(["عرض التخصيصات"], "") & filters.private, group=98009)
@is_owner
async def show_all_customizations(client, message):
    source_custom = await db.get_source_customization(client.me.id, "caption")
    source_buttons = await db.get_source_customization(client.me.id, "buttons")
    source_media = await db.get_source_customization(client.me.id, "media")
    control_text = await db.get_control_button_text(client.me.id)
    control_url = await db.get_control_button_url(client.me.id)
    caption = f"""
<b>• محتويات قاعدة البيانات (بوت: {client.me.id}):</b>

<b>• تخصيصات السورس:</b>
├ caption: {source_custom[:50] if source_custom else 'افتراضي'}...
├ buttons: {source_buttons if source_buttons else 'افتراضي'}
└ media: {source_media if source_media else 'افتراضي'}

<b>• تخصيصات زر التحكم:</b>
├ text: {control_text}
└ url: {control_url}

<b>📁 التخزين في:</b>
└ Collection: cache
"""
    await message.reply_video(
        video=config.ONE_VIDEO_URL,
        caption=caption,
        show_caption_above_media=True
    )