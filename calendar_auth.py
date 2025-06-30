# agent_manager_bot/main.py

import os
import subprocess
import logging
import json
import datetime
import pickle
from collections import defaultdict, deque
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import dateparser
import asyncio

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCRIPTS_DIR = "./scripts"
SUMMARY_CACHE_FILE = "script_summaries.json"
LOG_FILE = "action_log.json"
TASK_HISTORY_FILE = "task_history.json"

client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(level=logging.INFO)

# Short-term memory and chat history
last_gpt_response = {}
chat_memory = defaultdict(lambda: deque(maxlen=10))
calendar_confirmation = {}

# Load or generate script summaries
def get_script_summaries():
    if os.path.exists(SUMMARY_CACHE_FILE):
        with open(SUMMARY_CACHE_FILE, 'r') as f:
            return json.load(f)

    summaries = {}
    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith(('.sh', '.py')):
            path = os.path.join(SCRIPTS_DIR, filename)
            try:
                with open(path, 'r') as f:
                    code = f.read(1500)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a code analyst. Summarize what this script does in 1-2 sentences."},
                        {"role": "user", "content": code}
                    ],
                    temperature=0.3
                )
                summary = response.choices[0].message.content.strip()
                summaries[filename] = summary
            except Exception as e:
                summaries[filename] = f"(Error reading or summarizing: {e})"

    with open(SUMMARY_CACHE_FILE, 'w') as f:
        json.dump(summaries, f, indent=2)

    return summaries

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    return build('calendar', 'v3', credentials=creds)

async def handle_calendar_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global calendar_confirmation
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    message = update.message.text.strip().lower()

    # Check for confirmation follow-up
    if user_id in calendar_confirmation:
        if message in ["yes", "y"]:
            data = calendar_confirmation[user_id]
            service = get_calendar_service()
            try:
                event = {
                    'summary': data['title'],
                    'start': {'dateTime': data['datetime'], 'timeZone': 'UTC'},
                    'end': {'dateTime': data['datetime'], 'timeZone': 'UTC'},
                }
                created_event = service.events().insert(calendarId='primary', body=event).execute()
                await update.message.reply_text(f"✅ Event '{data['title']}' added to calendar at {data['datetime']}")
            except Exception as e:
                await update.message.reply_text(f"❌ Failed to add event: {e}")
            del calendar_confirmation[user_id]
            return
        elif message in ["no", "n"]:
            await update.message.reply_text("❌ Event creation cancelled.")
            del calendar_confirmation[user_id]
            return

    system_prompt = (
        "You are a smart assistant that controls the user's Google Calendar.\n"
        "Interpret user requests and decide on a single calendar action.\n"
        "Respond using this format only when an action is needed:\n"
        "calendar: list [number] events\n"
        "calendar: add event [title] at [natural time expression]\n"
        "If no action is needed, reply normally."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.4
        )
        parsed = response.choices[0].message.content.strip()

        if parsed.startswith("calendar:"):
            command = parsed[len("calendar:"):].strip()
            service = get_calendar_service()

            if command.startswith("list"):
                try:
                    n = int(command.split()[1])
                except:
                    n = 5

                events_result = service.events().list(
                    calendarId='primary', maxResults=n, singleEvents=True,
                    orderBy='startTime').execute()

                events = events_result.get('items', [])
                if not events:
                    await update.message.reply_text("📅 No upcoming events found.")
                    return

                reply = "📅 Upcoming events:\n\n"
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    reply += f"- {start} — {event.get('summary')}\n"
                await update.message.reply_text(reply)

            elif command.startswith("add event"):
                try:
                    parts = command[len("add event"):].strip().split(" at ")
                    title = parts[0].strip()
                    time_expr = parts[1].strip()
                    parsed_dt = dateparser.parse(time_expr)
                    if not parsed_dt:
                        await update.message.reply_text(f"❌ Couldn't understand time expression: {time_expr}")
                        return

                    iso_time = parsed_dt.isoformat()
                    calendar_confirmation[user_id] = {
                        "title": title,
                        "datetime": iso_time
                    }
                    await update.message.reply_text(
                        f"📅 Add '{title}' to your calendar at {parsed_dt.strftime('%Y-%m-%d %H:%M')} UTC? (yes/no)"
                    )
                except Exception as e:
                    await update.message.reply_text(f"❌ Failed to parse event: {e}")
            else:
                await update.message.reply_text(f"🤖 GPT replied:\n{parsed}")
        else:
            await update.message.reply_text(parsed)

    except Exception as e:
        await update.message.reply_text(f"❌ Calendar GPT Error:\n{e}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_general_chat))
    app.add_handler(CommandHandler("calendar", handle_calendar_chat))

    asyncio.run(app.run_polling())
