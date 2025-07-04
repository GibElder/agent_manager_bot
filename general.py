from email.mime import message
from reasoning import interpret_high_level_intent
from handlers import calendar_handler, script_handler, server_handler
from openai import OpenAI

client = OpenAI()

async def handle_message(update, context):
    user_text = update.message.text

    # Check if user is confirming a pending script
    if context.user_data.get("pending_script"):
        await script_handler.confirm_script_execution(update, context, user_text)
        return

    if context.user_data.get("pending_server_command"):
        await server_handler.confirm_server_command(update, context, user_text)
        return

    if context.user_data.get("pending_calendar_action"):
        await calendar_handler.confirm_calendar_action(update, context, user_text)
        return
        
    interpretation = interpret_high_level_intent(user_text)
    intent = interpretation.get("intent")

    if intent == "calendar":
        await calendar_handler.handle_calendar_action(update, context, user_text)
    elif intent == "script":
        await script_handler.handle_script_action(update, context, user_text)
    elif intent == "server_command":
        await server_handler.handle_server_command(update, context, user_text)
    else:
        # Fallback to general GPT conversation
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        await update.message.reply_text(reply)
