import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
# from handlers.general import handle_general_chat
from dotenv import load_dotenv
from pathlib import Path
# from telegram.ext import Updater, MessageHandler, Filters


# env_path = Path(__file__).resolve().parent.parent / '.env'
# load_dotenv(dotenv_path=env_path)

# load_dotenv()
# BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# if __name__ == "__main__":
#     if not BOT_TOKEN:
#         raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

#     app = ApplicationBuilder().token(BOT_TOKEN).build()
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_general_chat))
#     app.run_polling()
#     print("Bot started. Listening for messages...")
    
    
    
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

from generate_script_summaries import generate_summaries
from general import handle_message

def main():
    # Create application (new v20 API)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    print("✅ Bot started. Listening for messages...")
    app.run_polling()

if __name__ == "__main__":
    generate_summaries()
    main()
