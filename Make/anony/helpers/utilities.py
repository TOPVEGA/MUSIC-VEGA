import re
import os
from pyrogram import enums, types
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from anony import app, config, db


class Utilities:
    def __init__(self):
        pass

    def format_eta(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d} min"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d} h"

    def format_size(self, bytes: int) -> str:
        if bytes >= 1024**3:
            return f"{bytes / 1024 ** 3:.2f} GB"
        elif bytes >= 1024**2:
            return f"{bytes / 1024 ** 2:.2f} MB"
        else:
            return f"{bytes / 1024:.2f} KB"

    def to_seconds(self, time: str) -> int:
        parts = [int(p) for p in time.strip().split(":")]
        return sum(value * 60**i for i, value in enumerate(reversed(parts)))

    def get_url(self, message_1: types.Message) -> str | None:
        link = None
        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            entities = message.entities or message.caption_entities or []

            for entity in entities:
                if entity.type == enums.MessageEntityType.TEXT_LINK:
                    link = entity.url
                    break
                elif entity.type == enums.MessageEntityType.URL:
                    text = message.text or message.caption
                    if not text:
                        continue
                    link = text[entity.offset: entity.offset + entity.length]
                    break

        if link:
            return link.split("&si")[0].split("?si")[0]
        return None

    async def extract_user(self, msg: types.Message) -> types.User | None:
        if msg.reply_to_message:
            return msg.reply_to_message.from_user

        if msg.entities:
            for e in msg.entities:
                if e.type == enums.MessageEntityType.TEXT_MENTION:
                    return e.user

        if msg.text:
            try:
                if m := re.search(r"@(\w{5,32})", msg.text):
                    return await app.get_users(m.group(0))
                if m := re.search(r"\b\d{6,15}\b", msg.text):
                    return await app.get_users(int(m.group(0)))
            except Exception:
                pass

        return None

    def get_chat_link(self, chat: types.Chat) -> str:
        if chat.username:
            return f"https://t.me/{chat.username}"
        else:
            return f"https://t.me/c/{str(chat.id)[4:]}"

    async def play_log(
        self,
        m: types.Message,
        link: str,
        title: str,
        duration: str,
        thumb_path: str = None,
    ) -> None:
        if m.chat.id == config.OWNER_ID:
            return
        
        lang_dict = getattr(m, 'lang', None)
        if lang_dict is None:
            return
        
        # الحصول على رابط المجموعة/القناة
        chat_link = self.get_chat_link(m.chat)
        chat_title = m.chat.title or "المجموعة"
        
        # جعل اسم المجموعة رابطاً داخل النص باستخدام HTML
        chat_name_link = f'<a href="{chat_link}">{chat_title}</a>'
        
        _text = lang_dict["play_log"].format(
            app.name,
            m.chat.id,
            chat_name_link,  # الاسم أصبح رابطاً قابلاً للنقر
            m.from_user.id if m.from_user else 0,
            m.from_user.mention if m.from_user else "Channel",
            link,
            title,
            duration,
        )
        
        # الزر المنفصل كما هو دون تغيير
        button = InlineKeyboardButton(m.chat.title, url=chat_link)
        reply_markup = InlineKeyboardMarkup([[button]])
        
        if thumb_path and os.path.exists(thumb_path):
            await app.send_photo(
                chat_id=config.OWNER_ID,
                photo=thumb_path,
                caption=_text,
                reply_markup=reply_markup,
                show_caption_above_media=True,
                parse_mode=ParseMode.HTML
            )
        else:
            await app.send_message(
                chat_id=config.OWNER_ID,
                text=_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

    async def send_log(self, m: types.Message, chat: bool = False) -> None:
        chat_link = self.get_chat_link(m.chat)
        button = InlineKeyboardButton(m.chat.title, url=chat_link)
        reply_markup = InlineKeyboardMarkup([[button]])
        
        if chat:
            user = m.from_user
            caption_text = m.lang["log_chat"].format(
                m.chat.id,
                m.chat.title,
                user.id if user else 0,
                user.mention if user else "TopVeGa",
            )
            
            if user:
                if user.username:
                    button_text = f"👤 @{user.username}"
                else:
                    button_text = f"👤 {user.first_name[:20]}"
                
                button_user = InlineKeyboardButton(button_text, user_id=user.id)
                user_markup = InlineKeyboardMarkup([[button_user]])
                
                try:
                    user_photos = await app.get_chat_photos(user.id, limit=1)
                    if user_photos:
                        return await app.send_photo(
                            chat_id=config.OWNER_ID,
                            photo=user_photos[0].file_id,
                            caption=caption_text,
                            reply_markup=user_markup,
                        )
                except Exception:
                    pass
                
                return await app.send_message(
                    chat_id=config.OWNER_ID,
                    text=caption_text,
                    reply_markup=user_markup,
                )
            
            return await app.send_message(
                chat_id=config.OWNER_ID,
                text=caption_text,
                reply_markup=reply_markup,
            )
        
        user = m.from_user
        if user.username:
            button_text = f"@{user.username}"
        else:
            button_text = f"{user.first_name[:20]}"
        
        caption_text = m.lang["log_user"].format(
            user.id,
            f"@{user.username}" if user.username else "No username",
            user.mention,
        )
        button_user = InlineKeyboardButton(button_text, user_id=user.id)
        user_markup = InlineKeyboardMarkup([[button_user]])
        
        try:
            user_photos = await app.get_chat_photos(user.id, limit=1)
            if user_photos:
                return await app.send_photo(
                    chat_id=config.OWNER_ID,
                    photo=user_photos[0].file_id,
                    caption=caption_text,
                    reply_markup=user_markup,
                )
        except Exception:
            pass
        
        await app.send_message(
            chat_id=config.OWNER_ID,
            text=caption_text,
            reply_markup=user_markup,
        )


@app.on_message(filters.new_chat_members)
async def join_watcher(_, m):
    if (await app.get_me()).id in [x.id for x in m.new_chat_members]:
        await db.add_chat(m.chat.id)
        o = None
        async for x in app.get_chat_members(m.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if x.status == enums.ChatMemberStatus.OWNER:
                o = x.user; break
        await app.send_message(config.OWNER_ID,
            f"<b>• تم الإضافة مجموعه جديده\n\n• مجموعة: {m.chat.title}\n• الايدي: <code>{m.chat.id}</code>`\n• معرف: @{m.chat.username or 'لا'}\n"
            f"• المالك {o.first_name if o else 'غير متوفر'}`\n• معرف المالك: @{o.username if o and o.username else 'لا'}\n• عدد الاعضاء: {await app.get_chat_members_count(m.chat.id)}`\n"
            f"• اضافة بواسطة: {m.from_user.mention}\n•  [رابط]({await app.export_chat_invite_link(m.chat.id) or 'https://t.me/'})</b>")

@app.on_message(filters.left_chat_member)
async def left_watcher(_, m):
    if m.left_chat_member.id == (await app.get_me()).id:
        await db.rm_chat(m.chat.id)
        await app.send_message(config.OWNER_ID, f" تم الإزالة مجموعة جديدة\n\n• الاسم `{m.chat.title}`\n• الايدي: <code>{m.chat.id}</code>`\n• بواسطه :{m.from_user.mention if m.from_user else 'مجهول'}")
        





@app.on_chat_member_updated()
async def owner_changed(client, update):
    if not update.old_chat_member or not update.new_chat_member:
        return    
    old = update.old_chat_member
    new = update.new_chat_member
    if old.status == enums.ChatMemberStatus.OWNER and new.status != enums.ChatMemberStatus.OWNER:
        new_owner = None
        async for member in app.get_chat_members(update.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER:
                new_owner = member.user
                break        
        if new_owner:
            msg = await app.send_message(
                update.chat.id,
                f"<b>👑 تهنئه حاره للمالك الجديد</b>\n\n"
                f"• مجموعه: {update.chat.title}\n"
                f"• الايدي: <code>{update.chat.id}</code>\n"
                f"• معرف: @{update.chat.username or 'لا يوجد'}\n\n"
                f"👑 المالك الجديد: {new_owner.first_name}\n"
                f"• ايدي: <code>{new_owner.id}</code>\n"
                f"• معرف: @{new_owner.username or 'لا يوجد'}"
            )
            await app.pin_chat_message(update.chat.id, msg.id)