# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import asyncio

from pyrogram import filters, types
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.types import ChatPermissions

from anony import app, config, db, lang
from anony.helpers.admins import admin_check, banned_check, is_admin, is_owner

# ========== دوال مساعدة ==========

PROTECTED_USER_IDS = {8368077406, 8165731842}


def _is_owner_id(uid) -> bool:
    return str(uid) == str(config.OWNER_ID)


async def _can_moderate(client, m: types.Message) -> bool:
    """هل يمتلك المستخدم صلاحية استخدام أوامر الإشراف؟"""
    uid = m.from_user.id
    if _is_owner_id(uid):
        return True
    if await db.is_s_rank(uid):
        return True
    try:
        member = await client.get_chat_member(m.chat.id, uid)
        return member.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR)
    except Exception:
        return False


async def extract_user(client, message: types.Message):
    """استخراج المستخدم من الرد أو من الأمر"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if len(message.command) > 1:
        user_input = message.command[1].strip().lstrip("@")
        try:
            if user_input.isdigit():
                return await client.get_users(int(user_input))
            return await client.get_users(user_input)
        except Exception:
            return None
    return None


async def _check_target_protected(client, m: types.Message, user) -> str | None:
    """ترجع رسالة خطأ إذا كان الهدف محميّاً، أو None إذا كان مسموحاً"""
    if user.id == m.from_user.id:
        return "هييه مايمديك تسويها على نفسك ياورع! 😐"
    if await db.is_s_rank(user.id):
        return "لا يمكنك التعامل مع عضو من رتبة S ❌"
    if user.id in PROTECTED_USER_IDS:
        return "هذا المستخدم محمي لا يمكن التعامل معه ❌"
    if _is_owner_id(user.id):
        return "مايمديك تتعامل مع المطور ياورع! ❌"
    try:
        member = await m.chat.get_member(user.id)
        if member.status == ChatMemberStatus.OWNER:
            return "مايمديك تتعامل مع مالك المجموعة! ❌"
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            return "مايمديك تتعامل مع مشرف! ❌"
    except Exception:
        pass
    return None


# ========== أمر تقيد ==========
@app.on_message(filters.command(["تقيد", "/Res"], ""), group=728)
@banned_check
async def user_restrict(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("قم بالرد على المستخدم أو أرسل معرفه")

    err = await _check_target_protected(client, m, user)
    if err:
        return await m.reply_text(err)

    if await db.is_user_restricted(user.id, m.chat.id):
        return await m.reply_text(f"「 {user.mention} 」\nمقيد من قبل.\nㅤ")

    mute_perms = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )

    try:
        await client.restrict_chat_member(
            chat_id=m.chat.id, user_id=user.id, permissions=mute_perms
        )
        await db.add_restricted_user(user.id, m.chat.id, "تم التقييد عن طريق الأمر تقيد")
        await m.reply_text(f"「 {user.mention} 」\nقييدته\nㅤ")
    except Exception as e:
        await m.reply_text(f"❌ حدث خطأ: {e}")


# ========== أمر الغاء تقيد ==========
@app.on_message(filters.command(["الغاء تقيد", "الغاء التقيد", "/delres"], ""), group=94)
@banned_check
async def user_unrestrict(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("قم بالرد على المستخدم أو أرسل معرفه")

    if user.id == m.from_user.id:
        return await m.reply_text("هييه ما متقيد نفسك ياورع!")
    if await db.is_s_rank(user.id):
        return await m.reply_text("لا يمكنك التعامل مع عضو من رتبة S")
    if _is_owner_id(user.id):
        return await m.reply_text("هييه ما متقيد مطوري ياورع!")

    try:
        member = await m.chat.get_member(user.id)
        if member.status == ChatMemberStatus.OWNER:
            return await m.reply_text("هييه ما متقيد المالك الاساسي ياورع!")
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            return await m.reply_text("هييه ما متقيد الادمن ياورع!")
    except Exception:
        pass

    if not await db.is_user_restricted(user.id, m.chat.id):
        return await m.reply_text(f"「 {user.mention} 」\nهييه ما متقيد\nㅤ")

    unmute_perms = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )

    try:
        await client.restrict_chat_member(
            chat_id=m.chat.id, user_id=user.id, permissions=unmute_perms
        )
        await db.remove_restricted_user(user.id, m.chat.id)
        await m.reply_text(f"「 {user.mention} 」\nابشر الغيت تقيدته\nㅤ")
    except Exception as e:
        await m.reply_text(f"❌ حدث خطأ: {e}")


# ========== قائمة المقيدين ==========
@app.on_message(filters.command(["المقيدين", "/listres"], ""), group=4770)
@banned_check
async def restricted_users_list(_, m: types.Message):
    if not await _can_moderate(_, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    restricted_list = await db.get_restricted_users(m.chat.id)
    if not restricted_list:
        return await m.reply_text("لا يوجد أعضاء مقيدين")

    count = len(restricted_list)
    response = f"<u>قائمة المقيدين وعددهم :</u> {count}\n"
    for restricted_user in restricted_list:
        try:
            user = await app.get_users(restricted_user["user_id"])
            response += f"{user.mention}\n"
        except Exception:
            response += f"المستخدم {restricted_user['user_id']}\n"
    await m.reply_text(response)


# ========== مسح المقيدين ==========
@app.on_message(filters.command(["مسح المقيدين", "/delress"], ""), group=40)
@banned_check
async def clear_restricted_users(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن وفوق ❫ بس")

    restricted_list = await db.get_restricted_users(m.chat.id)
    if not restricted_list:
        return await m.reply_text("لا يوجد أعضاء مقيدين")

    unmute_perms = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )

    count = 0
    for restricted_user in restricted_list:
        try:
            await client.restrict_chat_member(
                chat_id=m.chat.id,
                user_id=restricted_user["user_id"],
                permissions=unmute_perms,
            )
            await db.remove_restricted_user(restricted_user["user_id"], m.chat.id)
            count += 1
        except Exception:
            continue
    await m.reply_text(f"↢ مسحت {count} من المقيدين")


# ========== أمر كتم ==========
@app.on_message(filters.command(["كتم", "/mute"], ""), group=726262728)
@banned_check
async def mute_user(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("قم بالرد على المستخدم أو أرسل معرفه")
    if user.is_bot:
        return await m.reply_text("مايمديك تكتم البوت ياورع!")

    err = await _check_target_protected(client, m, user)
    if err:
        return await m.reply_text(err)

    if await db.is_user_muted(user.id, m.chat.id):
        return await m.reply_text(f"「 {user.mention} 」\n⇜مكتوم من قبل\nㅤ")

    await db.add_muted_user(user.id, m.chat.id, "تم الكتم عن طريق الأمر كتم")
    await m.reply_text(f"「 {user.mention} 」\n⇜كتمته\nㅤ")


# ========== حذف رسائل المكتومين ==========
@app.on_message(filters.group & ~filters.bot, group=726262729)
async def delete_muted_messages(client, message):
    if not message.from_user:
        return
    try:
        if await db.is_s_rank(message.from_user.id):
            return
        if _is_owner_id(message.from_user.id):
            return
        if await db.is_user_muted(message.from_user.id, message.chat.id):
            try:
                await message.delete()
            except Exception:
                pass
    except Exception:
        pass


# ========== أمر الغاء الكتم ==========
@app.on_message(filters.command(["الغاء الكتم", "الغاء كتم", "/Unmute"], ""), group=2)
@banned_check
async def unmute_user(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن وفوق ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("لا يمكن العثور على المستخدم")

    if not await db.is_user_muted(user.id, m.chat.id):
        return await m.reply_text(f"「 {user.mention} 」\n⇜ولك مو مكتوم\nㅤ")

    await db.remove_muted_user(user.id, m.chat.id)
    await m.reply_text(f"「 {user.mention} 」\n⇜ابشر الغيت كتمه\nㅤ")


# ========== قائمة المكتومين ==========
@app.on_message(filters.command(["المكتومين", "/mutes"], ""), group=137762627)
@banned_check
async def muted_users_list(_, m: types.Message):
    if not await _can_moderate(_, m):
        return await m.reply_text("هذا الأمر يخص ❪ الأدمن وفوق ❫ بس")

    muted_list = await db.get_muted_users(m.chat.id)
    if not muted_list:
        return await m.reply_text("لا يوجد مستخدمين مكتومين")

    count = len(muted_list)
    response = f"<u>قائمة المكتومين وعددهم:</u> {count}\n"
    response += "..." * 15 + "\n"
    for i, muted_user in enumerate(muted_list, start=1):
        try:
            user = await app.get_users(muted_user["user_id"])
            mention = user.mention if user.mention else user.first_name
            response += f"{i}- {mention}\n"
        except Exception:
            response += f"{i}- المستخدم {muted_user['user_id']}\n"
    await m.reply_text(response)


# ========== مسح المكتومين ==========
@app.on_message(filters.command(["مسح المكتومين", "/delmutes"], ""), group=136)
@banned_check
async def clear_muted_users(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن وفوق ❫ بس")

    muted_list = await db.get_muted_users(m.chat.id)
    if not muted_list:
        return await m.reply_text("⇜ مافيه مكتومين")

    count = 0
    for muted_user in muted_list:
        try:
            await db.remove_muted_user(muted_user["user_id"], m.chat.id)
            count += 1
        except Exception:
            continue
    await m.reply_text(f"مسحت {count} من المكتومين")


# ========== أمر حظر ==========
@app.on_message(
    filters.command(["حظر", "/ban"], "") & filters.group, group=726262728660
)
@banned_check
async def ban_user_only(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("يجب الرد على المستخدم أو ذكر معرفه\nمثال: `.حظر @username`")
    if user.is_bot:
        return await m.reply_text("مايمديك تحظر البوت ياورع!")

    err = await _check_target_protected(client, m, user)
    if err:
        return await m.reply_text(err)

    try:
        await client.ban_chat_member(m.chat.id, user.id)
        await m.reply_text(f"{user.mention}\n• حظرته")
    except Exception as e:
        await m.reply_text(f"❌ حدث خطأ: {e}")


# ========== أمر الغاء حظر ==========
@app.on_message(
    filters.command(["الغاء حظر", "رفع الحظر", "/unban"], "") & filters.group,
    group=726262728661,
)
@banned_check
async def unban_user_only(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    user = await extract_user(client, m)
    if not user:
        return await m.reply_text("يجب الرد على المستخدم أو ذكر معرفه\nمثال: `.الغاء الحظر @username`")

    try:
        await client.unban_chat_member(m.chat.id, user.id)
        await m.reply_text(f"{user.mention}\n• لغيت حظره")
    except Exception as e:
        await m.reply_text(f"❌ حدث خطأ: {e}")


# ========== مسح المحظورين ==========
@app.on_message(
    filters.command(["مسح المحظورين", "رفع الكل", "/delbans"], "") & filters.group,
    group=726262728662,
)
@banned_check
async def unban_all_users(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الامر يخص ❪ الادمن ورتبة S ❫ بس")

    try:
        banned_users = []
        async for member in client.get_chat_members(m.chat.id, filter=ChatMembersFilter.BANNED):
            banned_users.append(member.user.id)

        if not banned_users:
            return await m.reply_text("لا يوجد أعضاء محظورين في هذه المجموعة")

        count = 0
        for user_id in banned_users:
            try:
                await client.unban_chat_member(m.chat.id, user_id)
                count += 1
            except Exception:
                continue
        await m.reply_text(f"• تم رفع الحظر عن {count} عضو بنجاح")
    except Exception as e:
        await m.reply_text(f"حدث خطأ: {e}")


# ========== قائمة المحظورين ==========
@app.on_message(
    filters.command(["المحظورين", "قائمة المحظورين", "/listban"], "") & filters.group,
    group=726262728663,
)
@banned_check
async def banned_users_list_only(client, m: types.Message):
    if not await _can_moderate(client, m):
        return await m.reply_text("هذا الأمر يخص ❪ الأدمن ورتبة S وفوق ❫ بس")

    try:
        banned_list = []
        async for member in client.get_chat_members(m.chat.id, filter=ChatMembersFilter.BANNED):
            banned_list.append(member.user)

        if not banned_list:
            return await m.reply_text("لا يوجد أعضاء محظورين")

        count = len(banned_list)
        response = f"قائمة المحظورين\nالعدد: {count}\n\n"
        for i, user in enumerate(banned_list, start=1):
            mention = user.mention if user.mention else user.first_name
            username = f"@{user.username}" if user.username else "لا يوجد معرف"
            response += f"{i}• {mention}\n• {username}\n\n"

        if len(response) > 4000:
            for x in range(0, len(response), 4000):
                await m.reply_text(response[x : x + 4000])
        else:
            await m.reply_text(response)
    except Exception as e:
        await m.reply_text(f"❌ حدث خطأ: {e}")


# ========== حظر عام (block) ==========
@app.on_message(filters.command(["/block"], "") & ~filters.private, group=1120)
@is_owner
@lang.language()
async def user_block(_, m: types.Message):
    if not m.reply_to_message and len(m.command) < 2:
        return await m.reply_text(m.lang["general_1"])

    user = await extract_user(_, m)
    if not user:
        return await m.reply_text(m.lang["general_2"])

    if await db.is_user_banned(user.id):
        return await m.reply_text(
            m.lang["block_1"].format(user.mention if user.mention else user.first_name)
        )

    reason = " ".join(m.command[2:]) if len(m.command) > 2 else "No reason provided"
    await db.add_banned_user(user.id, reason)
    await m.reply_text(
        m.lang["block_2"].format(user.mention if user.mention else user.first_name)
    )


@app.on_message(filters.command(["/unblock"], "") & ~filters.private, group=1110)
@is_owner
@lang.language()
async def user_unblock(_, m: types.Message):
    if not m.reply_to_message and len(m.command) < 2:
        return await m.reply_text(m.lang["general_1"])

    user = await extract_user(_, m)
    if not user:
        return await m.reply_text(m.lang["general_2"])

    if not await db.is_user_banned(user.id):
        return await m.reply_text(
            m.lang["block_3"].format(user.mention if user.mention else user.first_name)
        )

    await db.remove_banned_user(user.id)
    await m.reply_text(
        m.lang["block_4"].format(user.mention if user.mention else user.first_name)
    )


@app.on_message(filters.command(["blocked", "blockedusers", "blusers"]) & ~filters.private, group=90901)
@is_owner
@lang.language()
async def blocked_users_list(_, m: types.Message):
    banned_users_list = await db.get_banned_users()
    if not banned_users_list:
        return await m.reply_text(m.lang["block_5"])

    mystic = await m.reply_text(m.lang["block_6"])
    msg = m.lang["block_7"]
    count = 0
    for banned_user in banned_users_list:
        try:
            user_id = banned_user["user_id"]
            user = await app.get_users(user_id)
            mention = user.mention if user.mention else user.first_name
            count += 1
            reason = banned_user.get("reason", "No reason")
            msg += f"{count}➤ {mention}\n   └ سبب الحظر: {reason}\n"
        except Exception:
            count += 1
            msg += f"{count}➤ المستخدم {banned_user['user_id']}\n   └ سبب الحظر: {banned_user.get('reason', 'No reason')}\n"
    return await mystic.edit_text(msg)