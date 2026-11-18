
import pyrogram
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from anony import config, logger


class Bot(pyrogram.Client):
    def __init__(self):
        super().__init__(
            name="Anony",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            parse_mode=pyrogram.enums.ParseMode.HTML,
            max_concurrent_transmissions=7,
        )
        self.owner = config.OWNER_ID
        self.bl_users = pyrogram.filters.user()
        self.sudoers = pyrogram.filters.user(self.owner)

    async def boot(self):
        await super().start()
        
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = self.me.mention
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        
        try:
            message_text = (
                f"<b>• تم تشغيل البوت بنجاح!</b>\n\n"
                f"<b>• النظام :</b> 3v\n"
                f"<b>• اسم البوت :</b> {self.mention}\n"
                f"<b>• معرف البوت :</b> @{self.username}\n"
                f"<b>• ايدي البوت :</b> <code>{self.id}</code>\n"
                f"<b>• وقت التشغيل :</b> {current_time}\n"
                f"<b>• حالة البوت :</b> يعمل بكفاءة\n\n"
                f"<b>• جاهز لتشغيل الموسيقى!</b>"
            )
            
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"{self.name}", url=f"https://t.me/{self.username}")
                    ]
                ]
            )            
            await self.send_video(
                chat_id=self.owner,
                video="https://files.catbox.moe/ctcu5l.mp4",
                caption=message_text,
                reply_markup=reply_markup,
                show_caption_above_media=True
            )            
            logger.info(f"Bot started as @{self.username}")            
        except Exception as ex:
            raise SystemExit(f"Bot has failed to send startup message to owner: {self.owner}\nReason: {ex}")
    async def stop(self):
        await super().stop()
        logger.info("Bot stopped.")