import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from handlers.general import handle_general_chat
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_general_chat))
    app.run_polling()
    print("Bot started. Listening for messages...")