# import os
# import pickle
# from google.auth.transport.requests import Request
# from googleapiclient.discovery import build
# from dotenv import load_dotenv
# from pathlib import Path

# env_path = Path(__file__).resolve().parent.parent / '.env'
# load_dotenv(dotenv_path=env_path)

# def get_calendar_service():
#     creds = None
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#     return build('calendar', 'v3', credentials=creds)

# services/calendar.py
import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SCOPES = ['https://www.googleapis.com/auth/calendar']

TOKEN_PATH = Path(__file__).resolve().parent.parent / 'token.pickle'

print("✅ Calendar service will look for token here:", TOKEN_PATH)

def get_calendar_service():
    creds = None
    if TOKEN_PATH.exists():
        print("✅ Found token.pickle at", TOKEN_PATH)
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    else:
        print("❌ token.pickle not found at", TOKEN_PATH)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("No valid credentials. You must authenticate and generate token.pickle.")
    return build('calendar', 'v3', credentials=creds)

service = get_calendar_service()

