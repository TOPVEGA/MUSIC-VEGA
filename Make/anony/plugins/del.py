# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026



from pyrogram import Client, filters, enums
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, ChatAdminRequired, UserNotMutualContact
from anony import app, db, config
import asyncio


async def check_user_permission(client, message):
    try:
        if message.from_user.id == config.OWNER_ID:
            return True
        is_s_rank = await db.is_s_rank(message.from_user.id)
        if is_s_rank:
            return True
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return True
        
        return False
    except:
        return False

async def promote_assistant(client, chat_id):
    try:
        assistant_client = await db.get_assistant_userbot(chat_id)
        if not assistant_client:
            return None, "لا يوجد حساب مساعد لهذه المجموعة"
        assistant_info = await assistant_client.get_me()
        try:
            await db.join_assistant_to_channel(chat_id)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"خطأ في انضمام المساعد: {e}")
        try:
            chat_member = await client.get_chat_member(chat_id, assistant_info.id)
            if chat_member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return None, " لم يتمكن المساعد من الانضمام للمجموعة"
        except:
            return None, "لم يتمكن المساعد من الانضمام للمجموعة"

        await client.promote_chat_member(
            chat_id,
            assistant_info.id,
            privileges=ChatPrivileges(
                can_delete_messages=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_video_chats=True
            )
        )
        
        return assistant_client, "✅ تم ترقية المساعد بنجاح"
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await promote_assistant(client, chat_id)
    except ChatAdminRequired:
        return None, "البوت ليس أدمن أو لا يملك صلاحية الترقية"
    except Exception as e:
        return None, f"فشل الترقية: {str(e)}"

async def demote_assistant(client, chat_id):
    try:
        assistant_client = await db.get_assistant_userbot(chat_id)
        if not assistant_client:
            return True
        
        assistant_info = await assistant_client.get_me()        
        await client.promote_chat_member(
            chat_id,
            assistant_info.id,
            privileges=ChatPrivileges(
                can_delete_messages=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_video_chats=False
            )
        )
        return True
    except:
        return True

@app.on_message(filters.command(["حذف"], prefixes=[""]) & filters.group & ~filters.command(["حذف الكل"], prefixes=[""]), group=65)
async def delete_messages(client: Client, message: Message):
    try:
        if not await check_user_permission(client, message):
            return await message.reply_text("هذا الأمر يخص الادمن ورتبة S فقط")
        
        chat_id = message.chat.id
        is_reply = message.reply_to_message
        command_parts = message.text.split()
        delete_count = 1
        
        if len(command_parts) > 1:
            try:
                delete_count = int(command_parts[1])
                if delete_count < 1:
                    delete_count = 1
                elif delete_count > 50:
                    delete_count = 50
            except ValueError:
                return await message.reply_text(" الرجاء إدخال عدد صحيح")        
        try:
            await message.delete()
        except:
            pass
        
        progress_msg = await client.send_message(chat_id, "🔄 جاري حذف الرسائل...")
        assistant_client, result = await promote_assistant(client, chat_id)
        if not assistant_client:
            return await progress_msg.edit_text(f"{result}")
        
        try:
            deleted_count = 0
            
            if is_reply and delete_count == 1:
                try:
                    await assistant_client.delete_messages(chat_id, message.reply_to_message.id)
                    await progress_msg.edit_text("تم حذف الرسالة بنجاح")
                except Exception as e:
                    await progress_msg.edit_text(f" خطأ: {str(e)}")
                    
            elif is_reply and delete_count > 1:
                target_user_id = message.reply_to_message.from_user.id
                target_user = message.reply_to_message.from_user.mention
                
                async for msg in assistant_client.get_chat_history(chat_id):
                    if deleted_count >= delete_count:
                        break                    
                    if msg.from_user and msg.from_user.id == target_user_id:
                        try:
                            await assistant_client.delete_messages(chat_id, msg.id)
                            deleted_count += 1
                            await asyncio.sleep(0.3)
                        except:
                            continue
                
                await progress_msg.edit_text(f"• تم حذف {deleted_count} رسالة من {target_user}")
            
            else:
                async for msg in assistant_client.get_chat_history(chat_id, limit=delete_count + 5):
                    if deleted_count >= delete_count:
                        break
                    
                    if msg.id == message.id:
                        continue
                    
                    try:
                        await assistant_client.delete_messages(chat_id, msg.id)
                        deleted_count += 1
                        await asyncio.sleep(0.3)
                    except:
                        continue
                
                await progress_msg.edit_text(f"✅ تم حذف {deleted_count} رسالة")
        
        except Exception as e:
            await progress_msg.edit_text(f"❌ خطأ أثناء الحذف: {str(e)}")
        
        finally:
            await demote_assistant(client, chat_id)            
            await asyncio.sleep(5)
            try:
                await progress_msg.delete()
            except:
                pass    
    except Exception as e:
        await client.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")


@app.on_message(filters.command(["حذف الكل"], prefixes=[""]) & filters.group, group=66)
async def delete_all_user_messages(client: Client, message: Message):
    try:
        if not await check_user_permission(client, message):
            return await message.reply_text("هذا الأمر يخص الادمن ورتبة S فقط")
        
        if not message.reply_to_message:
            return await message.reply_text("قم بالرد على رسالة المستخدم")
        
        chat_id = message.chat.id
        target_user_id = message.reply_to_message.from_user.id
        target_user = message.reply_to_message.from_user.mention
        
        try:
            await message.delete()
        except:
            pass
        
        progress_msg = await client.send_message(chat_id, f"🔄 جاري حذف جميع رسائل {target_user}...")
        
        # ترقية المساعد
        assistant_client, result = await promote_assistant(client, chat_id)
        if not assistant_client:
            return await progress_msg.edit_text(f"{result}")
        
        try:
            deleted_count = 0
            max_delete = 200
            
            async for msg in assistant_client.get_chat_history(chat_id, limit=500):
                if deleted_count >= max_delete:
                    break
                
                if msg.from_user and msg.from_user.id == target_user_id:
                    try:
                        await assistant_client.delete_messages(chat_id, msg.id)
                        deleted_count += 1
                        await asyncio.sleep(0.5)
                    except:
                        continue
            
            await progress_msg.edit_text(f"✅ تم حذف {deleted_count} رسالة من {target_user}")
        
        except Exception as e:
            await progress_msg.edit_text(f"❌ خطأ أثناء الحذف: {str(e)}")
        
        finally:
            await demote_assistant(client, chat_id)           
            await asyncio.sleep(5)
            try:
                await progress_msg.delete()
            except:
                pass    
    except Exception as e:
        await client.send_message(message.chat.id, f" حدث خطأ: {str(e)}")