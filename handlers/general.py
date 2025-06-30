# handlers/general.py

from handlers.calendar_handler import handle_calendar_task, calendar_confirmation
from handlers.script_handler import handle_script_task, script_confirmation
from openai import OpenAI
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))


def is_calendar_related(text):
    return "calendar" in text or "meeting" in text or "schedule" in text or text.lower().startswith("add")

def is_script_related(text):
    return "run" in text or "script" in text or "backup" in text

async def handle_general_chat(update, context):
    message = update.message.text.strip()
    user_id = update.effective_user.id

    if user_id in script_confirmation:
        await handle_script_task(update, context)
        return

    if user_id in calendar_confirmation:
        await handle_calendar_task(update, context)
        return

    if is_calendar_related(message):
        await handle_calendar_task(update, context)
    elif is_script_related(message):
        await handle_script_task(update, context)
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful and friendly assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            await update.message.reply_text(reply[:4000])
        except Exception as e:
            await update.message.reply_text(f"❌ GPT error: {e}")
