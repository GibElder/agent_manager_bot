import subprocess
from openai import OpenAI
import json

client = OpenAI()

# List of dangerous commands
BLACKLIST = [
    "rm ",
    "shutdown",
    "reboot",
    "mkfs",
    ":(){",  # fork bomb
]

def interpret_server_command(message: str) -> dict:
    """
    Asks GPT to generate the command and a short explanation.
    """
    prompt = f"""
You are an assistant that converts user requests into safe shell commands.

Respond ONLY in this JSON format:

{{
  "command": "<the shell command>",
  "notes": "<short explanation of what this does>"
}}

Examples:

User: Show disk usage
Output:
{{
  "command": "df -h",
  "notes": "Shows disk usage in human-readable format."
}}

User: Show my IP
Output:
{{
  "command": "ip addr",
  "notes": "Shows network interfaces."
}}

If you are unsure, leave the command blank.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output structured JSON only."},
            {"role": "user", "content": f"{prompt}\n\nUser: {message}"}
        ],
        temperature=0
    )
    return json.loads(response.choices[0].message.content.strip())

def analyze_command_error(command: str, stderr: str) -> str:
    """
    Asks GPT to explain the error output in plain language.
    """
    prompt = f"""
You are a Linux troubleshooting assistant.

Here is the command:
{command}

Here is the error output:
{stderr}

Explain clearly what the error means and suggest how to fix it.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You provide plain text explanations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

async def handle_server_command(update, context, user_message):
    """
    Handles new commands (not confirmations).
    """
    interpretation = interpret_server_command(user_message)
    command = interpretation.get("command")
    notes = interpretation.get("notes")

    if not command:
        await update.message.reply_text("Sorry, I couldn't figure out what command to run.")
        return

    for forbidden in BLACKLIST:
        if forbidden in command:
            await update.message.reply_text(
                f"❌ The command was blocked because it contains a forbidden pattern: {forbidden}"
            )
            return

    # Save to context for confirmation
    context.user_data["pending_server_command"] = {"command": command}
    await update.message.reply_text(
        f"🛠️ I will run this command:\n\n`{command}`\n\nNotes: {notes}\n\nReply 'yes' to confirm or 'no' to cancel."
    )

async def confirm_server_command(update, context, user_message):
    """
    Handles confirmations (yes/no) for pending commands.
    """
    user_message = user_message.strip().lower()

    if user_message in ["no", "cancel", "never mind", "nevermind", "stop"]:
        context.user_data.pop("pending_server_command", None)
        await update.message.reply_text("❌ Okay, I’ve cancelled the command.")
        return

    pending = context.user_data.pop("pending_server_command", None)
    if not pending:
        await update.message.reply_text("No command is pending confirmation.")
        return

    command = pending["command"]

    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20
        )

        if result.returncode == 0:
            output = result.stdout or "(No output)"
            await update.message.reply_text(f"✅ Command output:\n\n{output[:4000]}")
        else:
            error_summary = analyze_command_error(command, result.stderr)
            await update.message.reply_text(
                f"⚠️ The command returned an error:\n\n{result.stderr}\n\n🔍 {error_summary}"
            )

    except Exception as e:
        await update.message.reply_text(f"Error running command: {e}")
