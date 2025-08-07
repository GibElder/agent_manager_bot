# Intelligent Server Interaction Agent

This project is a web-based AI assistant designed to interact with your Linux server through natural language commands. It supports executing shell commands, managing files and directories, editing scripts, reviewing system state, and more — all based on conversational inputs.

The assistant uses OpenAI models and a local vector database (Chroma) to reason over server context and decide what actions to take. Over time, it will support deeper context awareness, including chat history, installed tools, and multi-step task planning.

---

## Current Features

- Run shell commands from natural language
- Edit and execute server-side scripts
- Retrieve summaries of files and directories
- Use full chat history as context for reasoning
- Multi-intent classification: run commands, modify files, respond conversationally
- Custom handler architecture for more complex actions
- Safety checks and confirmation prompts before dangerous actions

---

## Roadmap

We are currently transitioning from a Telegram-based agent to a full web app interface and expanding the assistant’s capabilities with:

- A Chroma-based vector store for:
  - Script metadata and summaries
  - System information (tools, OS, services)
  - File and directory summaries
- A smart file/directory indexer that scans the system and updates the vector DB
- Prior chat history context injection for more conversational flow and follow-ups
- Long-term goal: replace rigid pipelines with intelligent reasoning that adapts to the task

Example use cases to support soon:

- “What scripts have backup in the name?”
- “Edit the python file in the directory with my flask app.”
- “Restart the thing I just ran.”
- “Fix the error I just got and try again.”
- “Push the latest code to GitHub.”

---

## Setup

### Requirements

- Python 3.11+
- A running Linux server or WSL instance
- OpenAI API key
- Chroma vector database (local mode)
- Pipenv or `venv` for Python environments

### Install

1. Clone the repo:

```bash
git clone https://github.com/yourusername/server-ai-agent.git
cd server-ai-agent
```

2. Set up environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Set environment variables (you can use a `.env` file):

```
OPENAI_API_KEY=your_key
TIMEZONE=America/Chicago
```

4. Run the indexer to build initial context:

```bash
python tools/index_files.py
```

5. Start the web app (coming soon)

---

## Structure

- `reasoning/` — prompt logic and planning functions
- `handlers/` — complex multi-step task handlers (file edit, git, etc.)
- `tools/` — scripts for indexing, summarizing, and vectorizing server content
- `data/` — vector database files, summaries, etc.
- `services/` — optional integrations (e.g., calendar, logging)
- `main.py` — orchestrates the flow for user interaction

---

## Status

This project is under active development and intended to evolve into a powerful personal assistant for server automation, observability, and development workflows.

Contributions welcome.
