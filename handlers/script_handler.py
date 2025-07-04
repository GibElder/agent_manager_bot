
# script_handler.py
import subprocess
import json
from reasoning import interpret_script_details

async def handle_script_action(update, context, user_message):
    # Load script summaries
    with open('data/script_summaries.json') as f:
        script_summaries = json.load(f)

    # Get detailed script action
    details = interpret_script_details(user_message, script_summaries)

    script_name = details.get("script_name")
    execution_method = details.get("execution_method")
    arguments = details.get("arguments", [])

    # Save to context so we can confirm before executing
    context.user_data["pending_script"] = details

    arg_str = " ".join(arguments) if arguments else "(no arguments)"

    # Ask for confirmation
    await update.message.reply_text(
        f"Run script '{script_name}' with method '{execution_method}' and arguments {arg_str}? Reply 'yes' to confirm or 'no' to cancel."
    )

async def confirm_script_execution(update, context, user_message):
    user_message = user_message.strip().lower()
    print(user_message)
    # Handle "no" or cancellation
    if user_message in ["no", "cancel", "never mind", "nevermind", "stop"]:
        context.user_data.pop("pending_script", None)
        await update.message.reply_text("❌ Okay, I’ve cancelled the script.")
        return

    details = context.user_data.get("pending_script")
    if not details:
        await update.message.reply_text("No script pending execution.")
        return

    script_name = details["script_name"]
    execution_method = details["execution_method"]
    arguments = details["arguments"]

    script_path = f"scripts/{script_name}"

    try:
        if execution_method == "bash":
            result = subprocess.run(
                ["bash", script_path] + arguments,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
        elif execution_method == "python":
            result = subprocess.run(
                ["python", script_path] + arguments,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
        else:
            await update.message.reply_text(f"Unknown execution method: {execution_method}")
            return

        output = result.stdout or "(No output)"
        error = result.stderr

        if result.returncode == 0:
            await update.message.reply_text(f"✅ Script completed successfully:\n\n{output[:4000]}")
        else:
            await update.message.reply_text(f"⚠️ Script returned errors:\n\n{error}")

    except Exception as e:
        await update.message.reply_text(f"Error running script: {e}")

    # Clear the pending script
    context.user_data["pending_script"] = None


