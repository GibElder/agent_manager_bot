# 🧠 Agent Manager Bot

A modular, GPT-powered Telegram bot for managing scripts and Google Calendar via natural language.

---

## ✨ Features

✅ **Script Execution**
- List and describe available scripts
- Use natural prompts to run scripts with arguments
- Confirm before executing any command
- Logs every run and output

✅ **Google Calendar Integration**
- Create events by simply describing them
  - Example: *"Add lunch with Sarah tomorrow at noon for 90 minutes"*
- Robust natural language deletion
  - Example: *"Delete my 2pm meeting"*
  - GPT suggests matches if ambiguous
- Timezone-aware scheduling

✅ **General Chat**
- Falls back to friendly GPT chat when the request isn’t a script or calendar action

✅ **Modular Codebase**
- Clean separation:
  - `handlers/` for scripts & calendar logic
  - `services/` for Google API integration
  - `main.py` for setup and routing

---

## 📁 Project Structure

.
├── main.py
├── handlers/
│ ├── general.py
│ ├── script_handler.py
│ └── calendar_handler.py
├── services/
│ └── calendar.py
├── scripts/ # Your custom .py and .sh scripts
├── .env # Environment configuration
└── requirements.txt

yaml
Copy
Edit

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_numeric_user_id
OPENAI_API_KEY=your_openai_key
TIMEZONE=America/Chicago

yaml
Copy
Edit

---

## 🏗️ Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
Authorize Google Calendar

Make sure you have a credentials.json file from Google Cloud.

Run your calendar_auth.py (or similar) script to generate token.pickle.

Prepare your scripts

Place your .sh and .py files into scripts/.

🚀 Running the Bot
bash
Copy
Edit
python main.py
💬 Example Commands
Scripts

"Run the backup script"

"Execute the test script with argument hello world"

Calendar

"Add a meeting with Bob tomorrow at 3pm for 45 minutes"

"Delete the dentist appointment"

General Chat

"What's the weather today?"

"Tell me a joke"

🛡️ Safety
All commands require confirmation before execution.

Only the specified TELEGRAM_USER_ID can control the bot.

📝 License
MIT License

🙌 Contributions
PRs welcome! This project is designed to be extended with new handlers and services.

yaml
Copy
Edit

---
