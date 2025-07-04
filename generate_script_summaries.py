# generate_script_summaries.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

SCRIPTS_DIR = "scripts"
OUTPUT_FILE = "data/script_summaries.json"

def summarize_script(script_name, script_content):
    prompt = f"""
You are an AI assistant that summarizes scripts for documentation.

Script filename: {script_name}

Script contents:
\"\"\"
{script_content}
\"\"\"

Generate a JSON object describing this script.

Respond ONLY with JSON in this format:

{{
  "description": "<short summary of what the script does>",
  "requires_arguments": <true or false>,
  "example_usage": "<example command line usage>"
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

def generate_summaries():
    summaries = []

    for filename in os.listdir(SCRIPTS_DIR):
        if filename.endswith(".py") or filename.endswith(".sh"):
            path = os.path.join(SCRIPTS_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Call GPT to summarize
            summary = summarize_script(filename, content)
            summary["name"] = filename
            summaries.append(summary)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    print(f"✅ Generated {len(summaries)} script summaries in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_summaries()
