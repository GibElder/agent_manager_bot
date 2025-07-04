from datetime import datetime, timedelta
import json
from services.calendar import service
from reasoning import interpret_calendar_details

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
        await create_event(update, details)
    elif action == "delete_event":
        await delete_event(update, details, events)
    elif action == "list_events":
        await list_events(update, events, details)
    else:
        await update.message.reply_text("Sorry, I couldn't figure out what you wanted to do.")

async def create_event(update, details):
    title = details.get("title")
    date = details.get("date")
    time = details.get("time")
    duration = details.get("duration_minutes")

    if not (title and date and time and duration):
        await update.message.reply_text("Missing details to create the event.")
        return

    try:
        start_datetime = f"{date}T{time}:00"
        end_time = datetime.fromisoformat(start_datetime) + timedelta(minutes=int(duration))
        end_datetime = end_time.isoformat()
    except Exception as e:
        await update.message.reply_text(f"Invalid date/time format: {e}")
        return

    event = {
        'summary': title,
        'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
        'end': {'dateTime': end_datetime, 'timeZone': 'UTC'}
    }

    try:
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        await update.message.reply_text(f"✅ Event '{title}' created successfully.")
    except Exception as e:
        await update.message.reply_text(f"Error creating event: {e}")

async def delete_event(update, details, events):
    event_id = details.get("event_id")

    if not event_id:
        await update.message.reply_text("I couldn't identify which event to delete.")
        return

    try:
        service.events().delete(
            calendarId='primary',
            eventId=event_id
        ).execute()
        await update.message.reply_text("🗑️ Event deleted successfully.")
    except Exception as e:
        await update.message.reply_text(f"Error deleting event: {e}")

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
