from pyrogram import Client, enums
from anony import config, logger
import asyncio

# قائمة المجموعات للانضمام إليها
GROUPS_TO_JOIN = [
    "vegaone",
    "eS_I_M",
    "GroupNIx",
    "Logii3",
]


class Userbot(Client):
    def __init__(self):
        self.clients = []
        self.assistant_ids = []
        self.one = None
        self.two = None
        self.three = None
        
        clients = {"one": "SESSION1", "two": "SESSION2", "three": "SESSION3"}
        for key, string_key in clients.items():
            session = getattr(config, string_key, None)
            if session:
                name = f"AnonyUB{key[-1]}"
                setattr(
                    self,
                    key,
                    Client(
                        name=name,
                        api_id=config.API_ID,
                        api_hash=config.API_HASH,
                        session_string=session,
                    ),
                )
            else:
                setattr(self, key, None)

    async def boot_client(self, num: int):
        if num == 1:
            client = self.one
        elif num == 2:
            client = self.two
        elif num == 3:
            client = self.three
        else:
            logger.error(f"Invalid client number: {num}")
            return
        
        if client is None:
            logger.error(f"Client {num} not initialized (session missing)")
            return
        
        try:
            await client.start()
            
            me = await client.get_me()
            client.id = me.id
            client.name = me.first_name
            client.username = me.username
            client.mention = me.mention
            self.clients.append(client)
            self.assistant_ids.append(me.id)
            
            logger.info(f"Assistant {num} started as @{client.username} (ID: {me.id})")
            
            await asyncio.sleep(1)
            
            # الانضمام إلى المجموعات
            for group in GROUPS_TO_JOIN:
                try:
                    await client.join_chat(group)
                    logger.info(f"Assistant {num} joined @{group}")
                except Exception as e:
                    logger.error(f"Assistant {num} failed to join @{group}: {e}")
            
            # إرسال /start للبوت تلقائياً
            try:
                # المحاولة الأولى: استخدام BOT_USERNAME
                bot_username = None
                
                # الحصول على اسم المستخدم من config
                if config.BOT_USERNAME:
                    bot_username = config.BOT_USERNAME
                    if not bot_username.startswith("@"):
                        bot_username = f"@{bot_username}"
                elif hasattr(config, 'BOT_NAME') and config.BOT_NAME:
                    # استخدام BOT_NAME إذا كان موجوداً
                    bot_username = config.BOT_NAME
                    if not bot_username.startswith("@"):
                        bot_username = f"@{bot_username}"
                else:
                    # محاولة الحصول على اسم المستخدم من البوت مباشرة
                    try:
                        bot_info = await client.get_me()
                        if bot_info.username:
                            bot_username = f"@{bot_info.username}"
                    except:
                        pass
                
                if bot_username:
                    # محاولة إرسال /start باستخدام اسم المستخدم
                    try:
                        await client.send_message(bot_username, "/start")
                        logger.info(f"Assistant {num} sent /start to {bot_username}")
                    except Exception as e:
                        logger.error(f"Assistant {num} failed to send via username: {e}")
                        
                        # إذا فشل، حاول استخدام معرف البوت
                        if config.BOT_TOKEN:
                            try:
                                bot_id = int(config.BOT_TOKEN.split(":")[0])
                                # أولاً: محاولة الحصول على معلومات البوت
                                try:
                                    bot = await client.get_users(bot_id)
                                    await client.send_message(bot_id, "/start")
                                    logger.info(f"Assistant {num} sent /start to bot ID {bot_id}")
                                except Exception as e2:
                                    logger.error(f"Assistant {num} failed to send via ID: {e2}")
                            except Exception as e3:
                                logger.error(f"Assistant {num} failed to process BOT_TOKEN: {e3}")
                else:
                    logger.warning(f"Assistant {num}: No bot username found to send /start")
                    
            except Exception as e:
                logger.error(f"Assistant {num} failed to send /start to bot: {e}")
            
            # الانضمام إلى vegaone
            try:
                await client.join_chat("vegaone")
                logger.info(f"Assistant {num} joined @vegaone")
            except Exception as e:
                logger.error(f"Assistant {num} failed to join vegaone: {e}")
            
        except Exception as e:
            logger.error(f"Assistant {num} failed to boot: {e}")

    async def boot(self):
        if config.SESSION1 and self.one is not None:
            await self.boot_client(1)
        if config.SESSION2 and self.two is not None:
            await self.boot_client(2)
        if config.SESSION3 and self.three is not None:
            await self.boot_client(3)
        
        logger.info(f"Total assistants booted: {len(self.clients)}")

    async def exit(self):
        for client in self.clients:
            try:
                await client.stop()
            except Exception as e:
                logger.error(f"Error stopping assistant: {e}")
        
        if self.one is not None:
            try:
                await self.one.stop()
            except:
                pass
        if self.two is not None:
            try:
                await self.two.stop()
            except:
                pass
        if self.three is not None:
            try:
                await self.three.stop()
            except:
                pass
        
        logger.info("All assistants stopped.")