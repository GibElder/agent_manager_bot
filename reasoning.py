# reasoning.py
from openai import OpenAI
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import pytz
LOCAL_TZ = pytz.timezone(os.getenv("TIMEZONE", "UTC"))

load_dotenv()
client = OpenAI()


def interpret_high_level_intent(message: str) -> dict:
    prompt = f"""
You are an AI assistant that classifies user messages into high-level intents.

Possible intents:
- script: The user wants to run, list, or manage scripts on their server.
- calendar: The user wants to create, delete, or manage calendar events.
- server_command: The user wants to execute a Linux shell command and get the results.
- general_chat: General questions, conversation, or anything else.

Also, suggest any context you think will be needed.

Respond ONLY in this JSON format:

{{
  "intent": "<one of: script, calendar, server_command, general_chat>",
  "context_needed": [<list of context items, e.g., script_summaries, calendar_events>],
  "notes": "<short explanation>"
}}

User message:
\"\"\"
{message}
\"\"\"
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output structured JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())

def interpret_calendar_details(message: str, calendar_events: list) -> dict:
    now_local = datetime.now(LOCAL_TZ)
    today_str = now_local.strftime("%Y-%m-%d")
    prompt = f"""
You are an AI assistant that determines the exact calendar action the user wants to perform.

Here is the user's message:
\"\"\"
{message}
\"\"\"

Here are all upcoming calendar events in JSON:
{json.dumps(calendar_events, indent=2)}

Determine the action:

- If the user wants to know what events they have on a specific date (e.g., "today," "tomorrow," "July 5th"), set "action" to "list_events" and ALWAYS include "date" in YYYY-MM-DD format. However, it the date is ambiguous (e.g., "next Friday"), always use the next occurrence of that day in the future. Keep in mind todays date time is TODAY'S DATE (local timezone): {today_str}, use only this as a reference to calculate dates.
- If they want to create an event, set "action" to "create_event" and fill in as many details as possible.
- If they want to delete an event, set "action" to "delete_event" and include "event_id" if you can identify it by title or date. If you cannot confidently determine the event_id, leave it blank and instead fill out the "title" and "date" fields exactly matching the event to delete.
- If you're not sure, pick the closest action and include notes explaining any uncertainty.

Respond ONLY in this exact JSON format:

{{
  "action": "<create_event | delete_event | list_events>",
  "title": "<event title if applicable>",
  "date": "<YYYY-MM-DD if applicable>",
  "time": "<HH:MM if applicable>",
  "duration_minutes": "<integer if applicable>",
  "event_id": "<Google Calendar event ID if applicable>",
  "notes": "<explanation or clarification if needed>"
}}

Examples:

If the user says "What do I have tomorrow?", you might respond:
{{
  "action": "list_events",
  "title": "",
  "date": "2024-07-04",
  "time": "",
  "duration_minutes": "",
  "event_id": "",
  "notes": "User asked for tomorrow's events."
}}

If the user says "Create a meeting called Project Kickoff tomorrow at 10 AM for 60 minutes", you might respond:
{{
  "action": "create_event",
  "title": "Project Kickoff",
  "date": "2024-07-04",
  "time": "10:00",
  "duration_minutes": "60",
  "event_id": "",
  "notes": ""
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output structured JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())

def interpret_script_details(message: str, script_summaries: list) -> dict:
    import json
    prompt = f"""
You are an AI assistant that determines which script to run based on the user's message.

Here are available scripts:
{json.dumps(script_summaries, indent=2)}

User message:
\"\"\"
{message}
\"\"\"

Determine the best matching script, how it should be executed (python or bash), and any arguments to pass.

Respond ONLY in this JSON format:

{{
  "script_name": "<script filename>",
  "execution_method": "<python | bash>",
  "arguments": ["arg1", "arg2"],
  "notes": "<short explanation>"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output structured JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())
