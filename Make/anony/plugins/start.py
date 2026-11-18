# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import asyncio
import os

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from pyrogram import enums, filters, types

from anony import app, config, db, lang
from anony.helpers import buttons, utils
from anony.helpers.admins import banned_check, is_owner

# ========== المتغيرات العامة ==========
WAITING_FOR_CAPTION = {}
CUSTOM_START_PM = None
START_ENABLED = True


class BotThumbnail:
    def __init__(self):
        self.rect = (500, 500)
        self.size = (1280, 720)
        self.fill = (255, 255, 255)

        try:
            self.font1 = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 48)
            self.font2 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 36)
            self.font3 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 32)
            self.font_bot = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 48)
        except Exception:
            self.font1 = self.font2 = self.font3 = self.font_bot = ImageFont.load_default()
        self.session = None

    async def start(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def generate_bot_thumb(self, bot_name: str = None, bot_username: str = None, bot_id: int = None) -> str:
        try:
            output = "cache/bot_thumb.png"
            if not os.path.exists("cache"):
                os.makedirs("cache")

            if os.path.exists(output):
                return output

            me = await app.get_me()
            if bot_name is None or bot_username is None or bot_id is None:
                bot_name = me.first_name or "Bot"
                if me.last_name:
                    bot_name = f"{bot_name} {me.last_name}"
                bot_username = me.username or "NoUsername"
                bot_id = me.id

            temp = "cache/bot_temp.jpg"
            photos = []
            async for photo in app.get_chat_photos(me.id):
                photos.append(photo)
                break

            if not photos:
                return config.START_IMG

            try:
                photo = photos[0]
                file_id = getattr(photo, "big_file_id", None) or getattr(photo, "file_id", None)
                if not file_id:
                    return config.START_IMG

                file_path = await app.download_media(file_id, file_name=temp)
                if not (file_path and os.path.exists(temp)):
                    return config.START_IMG
            except Exception as e:
                print(f"Error downloading photo: {e}")
                return config.START_IMG

            thumb = Image.open(temp).convert("RGBA").resize(self.size, Image.Resampling.LANCZOS)

            blur = thumb.filter(ImageFilter.GaussianBlur(8))
            background = ImageEnhance.Brightness(blur).enhance(0.30)

            _rect = ImageOps.fit(thumb, self.rect, method=Image.LANCZOS, centering=(0.5, 0.5))
            mask = Image.new("L", self.rect, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, self.rect[0], self.rect[1]), radius=30, fill=255)
            _rect.putalpha(mask)
            background.paste(_rect, (40, 110), _rect)

            glass_size = (self.rect[0] + 40, self.rect[1] + 40)
            glass_overlay = Image.new("RGBA", glass_size, (255, 255, 255, 0))
            glass_draw = ImageDraw.Draw(glass_overlay)
            glass_draw.rounded_rectangle(
                (0, 0, glass_size[0], glass_size[1]),
                radius=45,
                fill=(255, 255, 255, 10),
                outline=(255, 255, 255, 25),
                width=1,
            )
            background.paste(glass_overlay, (20, 90), glass_overlay)

            draw = ImageDraw.Draw(background)

            text_start_x = 600
            text_start_y = 220
            bot_text = "فيجا | ساوند"
            bot_y = text_start_y - 55

            draw.text((text_start_x + 1, bot_y + 1), bot_text, font=self.font_bot, fill=(0, 0, 0, 40))
            draw.text((text_start_x, bot_y), bot_text, font=self.font_bot, fill=(255, 255, 255, 230))

            bot_name_text = "VEGA-MUSIC"
            draw.text((text_start_x + 2, text_start_y + 2), bot_name_text, font=self.font1, fill=(0, 0, 0, 50))
            draw.text((text_start_x, text_start_y), bot_name_text, font=self.font1, fill=(255, 255, 255))

            channel_y = text_start_y + 70
            username_text = f"USER: @{bot_username}"
            draw.text((text_start_x + 1, channel_y + 1), username_text, font=self.font2, fill=(0, 0, 0, 40))
            draw.text((text_start_x, channel_y), username_text, font=self.font2, fill=(255, 255, 255))

            views_y = channel_y + 55
            id_text = f"ID: {bot_id}"
            draw.text((text_start_x + 1, views_y + 1), id_text, font=self.font3, fill=(0, 0, 0, 40))
            draw.text((text_start_x, views_y), id_text, font=self.font3, fill=(255, 255, 255))

            duration_y = views_y + 45
            status_text = "Status: Online"
            draw.text((text_start_x + 1, duration_y + 1), status_text, font=self.font3, fill=(0, 0, 0, 40))
            draw.text((text_start_x, duration_y), status_text, font=self.font3, fill=(255, 255, 255))

            background.save(output)
            try:
                os.remove(temp)
            except Exception:
                pass
            return output
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.START_IMG


bot_thumb = BotThumbnail()


# ========== أمر الأوامر ==========
@app.on_message(filters.command(["/help", "الاوامر", "اوامر"], "") & ~app.bl_users, group=600)
@lang.language()
@banned_check
async def _help(_, m: types.Message):
    if bot_thumb.session is None:
        await bot_thumb.start()
    bot = await app.get_me()
    await app.send_photo(
        chat_id=m.chat.id,
        photo=await bot_thumb.generate_bot_thumb(bot.first_name, bot.username),
        caption=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
    )


# ========== أوامر تخصيص رسالة الاستارت ==========
@app.on_message(filters.command(["تغير رسالة استارت"], "") & filters.private, group=601)
@is_owner
async def set_start_caption(client, message):
    global WAITING_FOR_CAPTION, CUSTOM_START_PM
    WAITING_FOR_CAPTION[message.from_user.id] = True
    request_msg = await message.reply_text(
        "• أرسل رسالة الاستارت الجديدة\n"
        "• الوسوم: `{user_name}` `{app_name}`\n"
        "• /cancel للإلغاء"
    )
    try:
        caption_msg = await client.listen(message.from_user.id, filters.text, timeout=120)
        if caption_msg.text.lower() == "/cancel":
            WAITING_FOR_CAPTION.pop(message.from_user.id, None)
            await request_msg.delete()
            return await message.reply_text("تم الإلغاء.")
        CUSTOM_START_PM = caption_msg.text
        WAITING_FOR_CAPTION.pop(message.from_user.id, None)
        await request_msg.delete()
        await message.reply_text("تم تغيير رسالة الاستارت!")
    except asyncio.TimeoutError:
        WAITING_FOR_CAPTION.pop(message.from_user.id, None)
        await request_msg.delete()
        await message.reply_text("انتهى الوقت.")


@app.on_message(filters.command(["حذف رساله استارت"], "") & filters.private, group=602)
@is_owner
async def delete_start_caption(client, message):
    global CUSTOM_START_PM
    CUSTOM_START_PM = None
    await message.reply_text("تم حذف الرسالة المخصصة.")


@app.on_message(filters.command(["تفعيل استارت"], "") & filters.private, group=603)
@is_owner
async def enable_start(client, message):
    global START_ENABLED
    START_ENABLED = True
    await message.reply_text("تم تفعيل الاستارت.")


@app.on_message(filters.command(["تعطيل استارت"], "") & filters.private, group=604)
@is_owner
async def disable_start(client, message):
    global START_ENABLED
    START_ENABLED = False
    await message.reply_text("تم تعطيل الاستارت.")


# ========== أمر الاستارت الرئيسي ==========
@app.on_message(filters.command(["start"]), group=605)
@lang.language()
@banned_check
async def start(_, message: types.Message):
    if bot_thumb.session is None:
        await bot_thumb.start()

    if not START_ENABLED:
        return await message.reply_text("• البوت في الصيانة")

    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE
    if CUSTOM_START_PM and private:
        _text = CUSTOM_START_PM.format(
            user_name=message.from_user.first_name, app_name=app.name
        )
    else:
        _text = (
            message.lang["start_pm"].format(message.from_user.first_name, app.name)
            if private
            else message.lang["start_gp"].format(app.name)
        )

    bot = await app.get_me()
    await app.send_photo(
        chat_id=message.chat.id,
        photo=await bot_thumb.generate_bot_thumb(bot.first_name, bot.username),
        caption=_text,
        reply_markup=await buttons.start_key(message.lang, private),
    )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        await db.add_user(message.from_user.id)
    else:
        if await db.is_chat(message.chat.id):
            return
        await utils.send_log(message, True)
        await db.add_chat(message.chat.id)


# ========== معالجة الرسائل النصية ==========
@app.on_message(filters.text & filters.private, group=606)
async def handle_caption_message(client, message):
    if WAITING_FOR_CAPTION.get(message.from_user.id, False):
        global CUSTOM_START_PM
        CUSTOM_START_PM = message.text
        WAITING_FOR_CAPTION[message.from_user.id] = False
        await message.reply_text("تم تغيير الرسالة!")


# ========== أمر الاعدادات ==========
@app.on_message(filters.command(["/set"]) & filters.group & ~app.bl_users, group=607)
@lang.language()
@banned_check
async def settings(_, message: types.Message):
    await app.send_photo(
        chat_id=message.chat.id,
        photo="https://qu.ax/34EaA.jpg",
        caption=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang,
            await db.get_play_mode(message.chat.id),
            await db.get_cmd_delete(message.chat.id),
            await db.get_lang(message.chat.id),
            message.chat.id,
        ),
    )


# ========== ترحيب بالأعضاء الجدد ==========
@app.on_message(filters.new_chat_members, group=10)
@lang.language()
async def welcome_new_members(_, message: types.Message):
    try:
        bot = await app.get_me()
        bot_added = any(m.id == bot.id for m in message.new_chat_members)
        if not bot_added or message.chat.type == enums.ChatType.PRIVATE:
            return

        if bot_thumb.session is None:
            await bot_thumb.start()

        welcome_text = message.lang["start_gp"].format(app.name)
        owner_id = int(config.OWNER_ID)
        owner = await app.get_users(owner_id)

        await app.send_photo(
            chat_id=message.chat.id,
            photo=await bot_thumb.generate_bot_thumb(bot.first_name, bot.username),
            caption=welcome_text,
            reply_markup=types.InlineKeyboardMarkup(
                [[types.InlineKeyboardButton(owner.first_name, user_id=owner_id)]]
            ),
        )
    except Exception as e:
        print(f"Error: {e}")