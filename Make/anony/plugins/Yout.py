# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import asyncio
import hashlib
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from pyrogram import filters
from pyrogram.types import Message

from anony import app, config, logger

# ============================================
# إعدادات
# ============================================
CACHE_DIR = "/tmp/audio_cache"
COOKIE_DIR = "anony/cookies"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(COOKIE_DIR, exist_ok=True)
executor = ThreadPoolExecutor(max_workers=8)

# ✅ ربط المدة بحد التشغيل الأساسي (لا تتجاوزه)
MAX_DURATION_SECONDS = min(getattr(config, "DURATION_LIMIT", 3600), 3600)
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ============================================
# مدير الكوكيز
# ============================================
class CookieManager:
    def __init__(self):
        self.cookie_files = []
        self.last_load = 0

    def get_cookie_file(self):
        if time.time() - self.last_load > 300:
            self._load_cookies()
        return random.choice(self.cookie_files) if self.cookie_files else None

    def _load_cookies(self):
        try:
            self.cookie_files = []
            if os.path.exists(COOKIE_DIR):
                for f in os.listdir(COOKIE_DIR):
                    if f.endswith(".txt"):
                        full_path = os.path.join(COOKIE_DIR, f)
                        if os.path.isfile(full_path):
                            self.cookie_files.append(full_path)
            self.last_load = time.time()
        except Exception:
            pass


cookie_manager = CookieManager()


def check_duration_before_download(query: str):
    cookie_file = cookie_manager.get_cookie_file()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "socket_timeout": 15,
        "default_search": "ytsearch1",
    }
    if cookie_file:
        opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if not info:
                return None, None
            if "entries" in info:
                entries = [e for e in info["entries"] if e]
                if not entries:
                    return None, None
                info = entries[0]

            duration = info.get("duration", 0)
            if duration > MAX_DURATION_SECONDS:
                logger.warning(f"المدة {duration} ثانية تتجاوز الحد المسموح")
                return None, None
            return info, duration
    except Exception as e:
        logger.error(f"خطأ في التحقق من المدة: {e}")
        return None, None


def download_audio(info, cache_key: str):
    cookie_file = cookie_manager.get_cookie_file()
    outtmpl = os.path.join(CACHE_DIR, f"{cache_key}.%(ext)s")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "socket_timeout": 15,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
        "http_chunk_size": 10485760,
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "outtmpl": outtmpl,
        "restrictfilenames": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "opus",
            "preferredquality": "32",
        }],
        "keepvideo": False,
    }
    if cookie_file:
        opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            file_path = ydl.prepare_filename(info)
            ydl.download([info.get("webpage_url", info.get("url"))])
            base_name = os.path.splitext(file_path)[0]
            opus_file = f"{base_name}.opus"
            if os.path.exists(opus_file):
                file_path = opus_file
            else:
                if not os.path.exists(file_path):
                    base = os.path.splitext(file_path)[0]
                    for f in os.listdir(CACHE_DIR):
                        if f.startswith(os.path.basename(base)):
                            file_path = os.path.join(CACHE_DIR, f)
                            break

            if not os.path.exists(file_path):
                return None

            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.warning(f"حجم الملف كبير جداً: {file_size / (1024 * 1024):.1f}MB")
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return None

            channel = info.get("uploader", info.get("channel", "غير معروف"))
            return {
                "file_path": file_path,
                "title": info.get("title", "أغنية"),
                "duration": info.get("duration", 0),
                "views": info.get("view_count", 0),
                "channel": channel,
                "file_size": file_size,
            }
    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        return None


async def search_and_download_async(query: str):
    cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

    for f in os.listdir(CACHE_DIR):
        if f.startswith(cache_key):
            path = os.path.join(CACHE_DIR, f)
            try:
                if 0 < os.path.getsize(path) <= MAX_FILE_SIZE_BYTES:
                    return {
                        "file_path": path,
                        "title": query,
                        "duration": 0,
                        "views": 0,
                        "channel": "من تخزين",
                        "file_size": os.path.getsize(path),
                    }
            except Exception:
                continue

    loop = asyncio.get_event_loop()
    info, duration = await loop.run_in_executor(executor, check_duration_before_download, query)
    if not info:
        return None

    result = await loop.run_in_executor(executor, download_audio, info, cache_key)
    return result


@app.on_message(filters.command(["نزل", "يوت", "تحميل", "س"], ""), group=908)
async def download_song(client, msg: Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return await msg.reply("كتب اسم الأغنية")

    query = parts[1].strip()
    if not query:
        return await msg.reply("اكتب اسم الأغنية مع الامر")

    loading = await msg.reply("⏳")

    data = await search_and_download_async(query)
    if not data:
        return await loading.edit("<b>• عذراً المدة تتجاوز الحد المسموح به</b>")

    title = data["title"]
    duration = data["duration"]
    file_path = data["file_path"]
    channel = data.get("channel", "غير معروف")
    file_size = data.get("file_size", 0)

    mins, secs = divmod(int(duration), 60)
    duration_str = f"{mins}:{secs:02d}"
    size_mb = file_size / (1024 * 1024)

    try:
        await client.send_audio(
            chat_id=msg.chat.id,
            audio=file_path,
            caption=(
                f"<b>• العنوان: {title[:50]}\n"
                f"• القناة: {channel[:30]}\n"
                f"• المدة: {duration_str}\n"
                f"• الحجم: {size_mb:.1f}MB\nㅤ"
            ),
            title=title[:50],
            performer=channel[:30],
            duration=int(duration) if duration else 0,
            disable_notification=True,
        )
        try:
            await loading.delete()
        except Exception:
            pass
        try:
            os.remove(file_path)
        except Exception:
            pass
    except Exception as e:
        await loading.edit(f"❌ خطأ: {str(e)[:50]}")


async def clean_cache():
    while True:
        await asyncio.sleep(3600)
        now = time.time()
        try:
            for f in os.listdir(CACHE_DIR):
                path = os.path.join(CACHE_DIR, f)
                if os.path.isfile(path) and (now - os.path.getmtime(path)) > 7200:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        except Exception:
            pass