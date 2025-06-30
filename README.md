# 🧠 Agent Manager Bot

A modular, GPT-powered Telegram bot for managing scripts and Google Calendar with natural language.

---

## ✨ Features

**✅ Script Execution**
- List and describe available scripts
- Use natural prompts to run scripts with arguments
- Confirm before executing any command
- Logs every run and output

**✅ Google Calendar Integration**
- Create events just by describing them  
  Example: *Add lunch with Sarah tomorrow at noon for 90 minutes*
- Robust natural language deletion  
  Example: *Delete my 2pm meeting*  
  GPT suggests matches if ambiguous
- Timezone-aware scheduling

**✅ General Chat**
- Falls back to friendly GPT chat when the request isn’t a script or calendar action

**✅ Modular Codebase**
- Clean separation of concerns:
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
---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USER_ID=your_telegram_numeric_user_id
OPENAI_API_KEY=your_openai_key
TIMEZONE=America/Chicago

yaml
---

## 🏗️ Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
Authorize Google Calendar

Make sure you have a credentials.json file from Google Cloud.

Run your calendar_auth.py (or equivalent) to create token.pickle.

Prepare your scripts

Place your .sh and .py files in the scripts/ folder.

🚀 Running the Bot
```bash
python main.py
```
💬 Example Commands
Scripts

Run the backup script

Execute the test script with argument hello world

Calendar

Add a meeting with Bob tomorrow at 3pm for 45 minutes

Delete the dentist appointment

General Chat

What's the weather today?

Tell me a joke

🙌 Contributions
PRs welcome! This project is designed to be extended with new handlers and services.

yaml
---
