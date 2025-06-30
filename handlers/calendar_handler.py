# handlers/calendar_handler.py

import os
import pytz
from dateparser import parse as dateparse
from services.calendar import get_calendar_service
from openai import OpenAI
from datetime import timedelta
import datetime
import re

TIMEZONE = os.getenv("TIMEZONE", "UTC")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))

client = OpenAI(api_key=OPENAI_API_KEY)
calendar_confirmation = {}

async def handle_calendar_task(update, context):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    message_lower = message.lower()

    if user_id != ALLOWED_USER_ID:
        return

    # Handle confirmation
    if user_id in calendar_confirmation:
        if message_lower in ["yes", "y"]:
            data = calendar_confirmation[user_id]
            try:
                duration = data.get("duration", 60)  # in minutes
                end_dt = dateparse(data["datetime"]) + timedelta(minutes=duration)
                event = {
                    "summary": data["title"],
                    "start": {"dateTime": data["datetime"], "timeZone": TIMEZONE},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
                }
                get_calendar_service().events().insert(calendarId="primary", body=event).execute()
                await update.message.reply_text(f"✅ Event '{data['title']}' added at {data['datetime']} for {duration} minutes")
            except Exception as e:
                await update.message.reply_text(f"❌ Failed to add event: {e}")
            del calendar_confirmation[user_id]
            return
        elif message_lower in ["no", "n"]:
            await update.message.reply_text("❌ Event creation cancelled.")
            del calendar_confirmation[user_id]
            return

    # Use GPT to extract event title, time, and duration
    try:
        if "delete" in message_lower or "remove" in message_lower:
            await attempt_event_deletion(update, message)
            return

        system_prompt = (
            "You are a calendar assistant. Extract the event title, time, and optional duration.\n"
            "Respond ONLY in the format: calendar: add \"title\" at \"natural time\" for \"duration in minutes\"\n"
            "If duration is unknown, use 60. If time is unclear, reply: calendar: error missing time."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.3
        )

        reply = response.choices[0].message.content.strip()

        if "calendar: error" in reply:
            await update.message.reply_text("❌ I couldn't figure out the time. Can you rephrase?")
            return

        if reply.startswith("calendar: add"):
            pattern = r'calendar: add "(.+?)" at "(.+?)" for "(\d+)"'
            match = re.search(pattern, reply)
            if not match:
                raise ValueError("Pattern mismatch")

            title, time_expr, duration_str = match.groups()
            duration = int(duration_str)

            tz = pytz.timezone(TIMEZONE)
            parsed_dt = dateparse(time_expr, settings={"TIMEZONE": TIMEZONE, "RETURN_AS_TIMEZONE_AWARE": True})
            parsed_dt = parsed_dt.astimezone(tz) if parsed_dt else None

            if not parsed_dt:
                await update.message.reply_text(f"❌ Couldn't parse time: {time_expr}")
                return

            calendar_confirmation[user_id] = {
                "title": title,
                "datetime": parsed_dt.isoformat(),
                "duration": duration
            }
            await update.message.reply_text(
                f"📅 Add '{title}' at {parsed_dt.strftime('%Y-%m-%d %H:%M')} for {duration} minutes? (yes/no)"
            )
            return

        await update.message.reply_text("❌ Sorry, I couldn’t understand your calendar request.")

    except Exception as e:
        await update.message.reply_text(f"❌ Calendar parsing error: {e}")


async def attempt_event_deletion(update, message):
    try:
        service = get_calendar_service()
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            await update.message.reply_text("No upcoming events found.")
            return

        # Build event list
        event_list = "\n".join([f"{i+1}. {e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}" for i, e in enumerate(events)])

        system_prompt = (
            "You are a smart calendar assistant that helps users delete upcoming events.\n"
            "Use the user's natural language and match it to one or more of the events listed below.\n"
            "Be flexible: match by time, keywords, or partial titles.\n"
            "If you are unsure, list 1-3 close matches and ask the user to confirm which number to delete.\n"
            "If it's clear, respond ONLY in the format: delete: 2 or delete: 1,3\n"
            f"User message: {message}\nEvents:\n{event_list}"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            temperature=0.2
        )

        reply = response.choices[0].message.content.strip()

        if reply.startswith("delete:"):
            indexes = [int(x.strip())-1 for x in reply[len("delete:"):].split(",") if x.strip().isdigit()]
            deleted = []
            for idx in indexes:
                if 0 <= idx < len(events):
                    service.events().delete(calendarId='primary', eventId=events[idx]['id']).execute()
                    deleted.append(events[idx]['summary'])
            if deleted:
                await update.message.reply_text(f"🗑️ Deleted events: {', '.join(deleted)}")
            else:
                await update.message.reply_text("❌ Nothing deleted.")
        else:
            await update.message.reply_text("❌ Couldn't determine what to delete. Please clarify.")

    except Exception as e:
        await update.message.reply_text(f"❌ Deletion error: {e}")
