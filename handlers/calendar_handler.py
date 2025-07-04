from datetime import datetime, timedelta
import json
from services.calendar import service
from reasoning import interpret_calendar_details
import os 
import pytz
import dateparser

LOCAL_TZ = pytz.timezone(os.getenv("TIMEZONE", "UTC"))

def fetch_and_save_events():
    now = datetime.utcnow().isoformat() + 'Z'
    one_year_later = (datetime.utcnow() + timedelta(days=365)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=one_year_later,
        maxResults=500,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    with open('data/current_calendar_cache.json', 'w') as f:
        json.dump(events, f, indent=2)

    return events

async def handle_calendar_action(update, context, user_message):
    events = fetch_and_save_events()
    details = interpret_calendar_details(user_message, events)
    action = details.get("action")

    if action == "create_event":
        # Save to pending and ask confirmation
        context.user_data["pending_calendar_action"] = {"type": "create", "details": details}
        await update.message.reply_text(
            f"📅 I am about to create event '{details.get('title')}' on {details.get('date')} at {details.get('time')} "
            f"for {details.get('duration_minutes') or 60} minutes.\n\nReply 'yes' to confirm or 'no' to cancel."
        )
    elif action == "delete_event":
        # Save to pending and ask confirmation
        context.user_data["pending_calendar_action"] = {"type": "delete", "details": details}
        if details.get("event_id"):
            desc = f"(ID {details.get('event_id')})"
        else:
            desc = f"with title '{details.get('title')}' on {details.get('date')}"
        await update.message.reply_text(
            f"🗑️ I am about to delete the event {desc}.\n\nReply 'yes' to confirm or 'no' to cancel."
        )
    elif action == "list_events":
        await list_events(update, events, details)
    else:
        await update.message.reply_text("Sorry, I couldn't figure out what you wanted to do.")

async def confirm_calendar_action(update, context, user_message):
    user_message = user_message.strip().lower()

    if user_message in ["no", "cancel", "never mind", "nevermind", "stop"]:
        context.user_data.pop("pending_calendar_action", None)
        await update.message.reply_text("❌ Okay, I’ve cancelled the calendar action.")
        return

    pending = context.user_data.pop("pending_calendar_action", None)
    if not pending:
        await update.message.reply_text("No calendar action pending confirmation.")
        return

    action_type = pending["type"]
    details = pending["details"]

    if action_type == "create":
        await create_event(update, details)
    elif action_type == "delete":
        # Fetch fresh events so deletes don't miss new entries
        events = fetch_and_save_events()
        await delete_event(update, details, events)
    else:
        await update.message.reply_text("❌ Unknown action type.")

async def delete_event(update, details, events):
    event_id = details.get("event_id")
    title = details.get("title", "").lower()
    target_date = details.get("date")

    if event_id:
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            await update.message.reply_text("🗑️ Event deleted successfully.")
        except Exception as e:
            await update.message.reply_text(f"Error deleting event: {e}")
        return

    # Fuzzy match
    matching = []
    for e in events:
        event_title = e["summary"].lower()
        start_dt = e["start"].get("dateTime", e["start"].get("date"))
        event_date = start_dt[:10]
        if title in event_title and event_date == target_date:
            matching.append(e)

    if len(matching) == 0:
        await update.message.reply_text("❌ Could not find any event matching that title and date.")
    elif len(matching) == 1:
        try:
            service.events().delete(
                calendarId='primary',
                eventId=matching[0]['id']
            ).execute()
            await update.message.reply_text(f"🗑️ Deleted event '{matching[0]['summary']}' on {target_date}.")
        except Exception as e:
            await update.message.reply_text(f"Error deleting event: {e}")
    else:
        message = "⚠️ Found multiple matching events:\n\n"
        for e in matching:
            message += f"- {e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}\n"
        message += "\nPlease be more specific."
        await update.message.reply_text(message)

async def create_event(update, details):
    title = details.get("title")
    date = details.get("date")
    time = details.get("time")
    duration = details.get("duration_minutes")

    if not (title and date and time):
        await update.message.reply_text("Missing details to create the event.")
        return

    if not duration:
        duration = 60
    else:
        duration = int(duration)

    datetime_str = f"{date} {time}"

    parsed = dateparser.parse(
        datetime_str,
        settings={
            "TIMEZONE": str(LOCAL_TZ),
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future"
        }
    )

    if not parsed:
        await update.message.reply_text(f"Could not parse date/time: {datetime_str}")
        return

    now = datetime.now(tz=parsed.tzinfo)
    if parsed < now:
        parsed = parsed.replace(year=parsed.year + 1)

    end_time = parsed + timedelta(minutes=duration)
    start_iso = parsed.astimezone(pytz.utc).isoformat()
    end_iso = end_time.astimezone(pytz.utc).isoformat()

    event = {
        'summary': title,
        'start': {'dateTime': start_iso, 'timeZone': 'UTC'},
        'end': {'dateTime': end_iso, 'timeZone': 'UTC'}
    }

    print("DEBUG Event payload:", json.dumps(event, indent=2))

    try:
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        await update.message.reply_text(
            f"✅ Event '{title}' created for {parsed.strftime('%Y-%m-%d %H:%M %Z')}."
        )
    except Exception as e:
        await update.message.reply_text(f"Error creating event: {e}")

async def list_events(update, events, details):
    filter_date = details.get("date")

    if filter_date:
        matching = []
        for e in events:
            start_dt = e["start"].get("dateTime", e["start"].get("date"))
            if start_dt.startswith(filter_date):
                matching.append(e)
        if not matching:
            await update.message.reply_text(f"✅ You have nothing scheduled on {filter_date}. Enjoy your free day!")
            return

        message = f"📅 Events on {filter_date}:\n\n"
        for e in matching:
            message += f"- {e['summary']} at {start_dt}\n"
        await update.message.reply_text(message)
    else:
        if not events:
            await update.message.reply_text("You have no upcoming events.")
            return

        message = "📅 Upcoming events:\n\n"
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            message += f"- {e['summary']} at {start}\n"
        await update.message.reply_text(message)
