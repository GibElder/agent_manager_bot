# handlers/script_handler.py

import os
import subprocess
import json
import datetime
from telegram import Update
from openai import OpenAI

SCRIPTS_DIR = "./scripts"
SUMMARY_CACHE_FILE = "script_summaries.json"
LOG_FILE = "action_log.json"
TASK_HISTORY_FILE = "task_history.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))

client = OpenAI(api_key=OPENAI_API_KEY)
script_confirmation = {}

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
                        {"role": "system", "content": "Summarize what this script does."},
                        {"role": "user", "content": code}
                    ],
                    temperature=0.3
                )
                summaries[filename] = response.choices[0].message.content.strip()
            except Exception as e:
                summaries[filename] = f"(Error: {e})"

    with open(SUMMARY_CACHE_FILE, 'w') as f:
        json.dump(summaries, f, indent=2)

    return summaries

def log_action(user_id, message, script, args):
    entry = {
        "user_id": user_id,
        "message": message,
        "script": script,
        "args": args
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + "\n")

def log_task_history(user_id, original_message, task_list):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "original_message": original_message,
        "scripts": task_list
    }
    with open(TASK_HISTORY_FILE, 'a') as f:
        f.write(json.dumps(entry) + "\n")

async def handle_script_task(update: Update, context):
    global script_confirmation

    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        return

    message = update.message.text.strip()
    message_lower = message.lower()

    # Handle confirmation
    if user_id in script_confirmation:
        if message_lower in ["yes", "y"]:
            data = script_confirmation[user_id]
            results = []
            tasks = []

            for cmd in data["commands"]:
                script = cmd["script"]
                args = cmd.get("args", [])
                path = os.path.join(SCRIPTS_DIR, script)
                summary = {"script": script, "args": args}

                if not os.path.exists(path):
                    results.append(f"⚠️ Script '{script}' not found.")
                    summary["result"] = "not found"
                    tasks.append(summary)
                    continue

                run_cmd = ["python3", path] + args if script.endswith(".py") else ["bash", path] + args
                try:
                    output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=30).decode()[:1000]
                    results.append(f"✅ `{script}` ran successfully:\n{output}")
                    summary["result"] = "success"
                    log_action(user_id, data["original_msg"], script, args)
                except Exception as e:
                    results.append(f"❌ Error running `{script}`: {e}")
                    summary["result"] = f"error: {e}"
                tasks.append(summary)

            log_task_history(user_id, data["original_msg"], tasks)
            del script_confirmation[user_id]
            await update.message.reply_text("\n\n".join(results)[:4000])
            return

        elif message_lower in ["no", "n"]:
            await update.message.reply_text("❌ Script execution cancelled.")
            del script_confirmation[user_id]
            return

    # Ask GPT to map message to script command
    summaries = get_script_summaries()
    script_list = "\n".join([f"- {name}: {desc}" for name, desc in summaries.items()])
    system_prompt = (
        "You are a script assistant. Based on the user's message, respond ONLY in this format:\n"
        "run: script_name [arg1 arg2 ...]\n"
        "Available scripts:\n" + script_list
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

        reply = response.choices[0].message.content.strip()
        run_blocks = [line for line in reply.splitlines() if line.startswith("run:")]
        commands = []
        for line in run_blocks:
            parts = line[len("run:"):].strip().split()
            if parts:
                commands.append({"script": parts[0], "args": parts[1:]})

        if commands:
            script_confirmation[user_id] = {
                "commands": commands,
                "original_msg": message
            }
            summary = "\n".join([f"- {cmd['script']} {' '.join(cmd['args'])}" for cmd in commands])
            await update.message.reply_text(f"🛠️ Do you want to run this script?\n{summary}\n\nProceed? (yes/no)")
        else:
            await update.message.reply_text("🤖 Sorry, I couldn't match that to any script.")

    except Exception as e:
        await update.message.reply_text(f"❌ GPT error: {e}")
