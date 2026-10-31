

import os
import re
import glob
import asyncio
import tempfile
import logging
from urllib.parse import urlparse

import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MAX_SIZE = 45 * 1024 * 1024

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("📥 دانلود از اینستاگرام", callback_data="download")],
    [InlineKeyboardButton("📖 راهنما", callback_data="help")],
    [InlineKeyboardButton("ℹ️ درباره ربات", callback_data="about")],
])

def valid_instagram_url(url):
    try:
        parsed = urlparse(url.strip())
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme in ("http", "https")
            and host in {
                "instagram.com",
                "www.instagram.com",
                "instagr.am",
                "www.instagr.am",
            }
        )
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 به MEHRSAM MUSIC AI خوش آمدی!\n\n"
        "لینک یک پست یا ریلز عمومی اینستاگرام را ارسال کن.\n"
        "محتوا باید بدون ورود به حساب یا دور زدن محدودیت‌ها "
        "قابل دریافت باشد و اجازه دانلود آن را داشته باشی.",
        reply_markup=MENU,
    )

async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "download":
        await query.message.reply_text(
            "🔗 لینک پست یا ریلز عمومی اینستاگرام را ارسال کن."
        )
    elif query.data == "help":
        await query.message.reply_text(
            "📖 راهنمای استفاده\n\n"
            "۱. لینک یک پست یا ریلز عمومی را کپی کن.\n"
            "۲. لینک را برای ربات بفرست.\n"
            "۳. منتظر بررسی و دریافت فایل بمان.\n\n"
            "محتوای خصوصی و محتوای نیازمند دور زدن محدودیت‌ها "
            "پشتیبانی نمی‌شود."
        )
    elif query.data == "about":
        await query.message.reply_text(
            "✨ MEHRSAM MUSIC AI\n"
            "ربات دریافت محتوای عمومی و مجاز اینستاگرام"
        )

def download_media(url, folder):
    options = {
        "outtmpl": os.path.join(folder, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "max_downloads": 5,
        "socket_timeout": 20,
        "retries": 1,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_SIZE,
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([url])

async def handle_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.message
    url = message.text.strip()

    if not valid_instagram_url(url):
        await message.reply_text(
            "⚠️ لطفاً یک لینک معتبر از اینستاگرام ارسال کن."
        )
        return

    status = await message.reply_text(
        "⏳ در حال بررسی لینک عمومی... لطفاً صبر کن."
    )

    try:
        with tempfile.TemporaryDirectory() as folder:
            await asyncio.to_thread(download_media, url, folder)

            files = [
                path for path in glob.glob(os.path.join(folder, "*"))
                if os.path.isfile(path)
            ]

            if not files:
                await status.edit_text(
                    "❌ فایلی دریافت نشد. ممکن است لینک در دسترس نباشد "
                    "یا اینستاگرام دریافت آن را محدود کرده باشد."
                )
                return

            sent = 0
            for path in files[:5]:
                if os.path.getsize(path) > MAX_SIZE:
                    continue

                with open(path, "rb") as media:
                    ext = os.path.splitext(path)[1].lower()
[31/10/2026 2:57 PM] Mehrdad Moghaddam: if ext in (".jpg", ".jpeg", ".png", ".webp"):
                        await message.reply_photo(photo=media)
                    elif ext in (".mp4", ".mov", ".m4v", ".webm"):
                        await message.reply_document(document=media)
                    else:
                        continue

                sent += 1

            if sent:
                await status.edit_text("✅ ارسال فایل‌ها انجام شد.")
            else:
                await status.edit_text(
                    "❌ فایل قابل ارسال پیدا نشد یا حجم آن بیش از حد مجاز بود."
                )

    except Exception:
        logging.exception("Instagram download failed")
        await status.edit_text(
            "❌ دریافت فایل موفق نبود. ممکن است لینک خصوصی، "
            "نامعتبر یا از طرف اینستاگرام محدود شده باشد."
        )

def main():
    if not TOKEN:
        raise RuntimeError(
            "متغیر TELEGRAM_BOT_TOKEN در تنظیمات محیطی تنظیم نشده است."
        )

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_click))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
    )

    print("MEHRSAM MUSIC AI is running...")
    app.run_polling()

if name == "main":
    main()
