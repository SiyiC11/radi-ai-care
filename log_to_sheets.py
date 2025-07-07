import os
import base64
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from pytz import timezone

def get_sydney_time():
    sydney_tz = pytz.timezone("Australia/Sydney")
    return datetime.now(sydney_tz).isoformat()

def log_to_google_sheets(language, report_length):
    # Step 1: decode base64 secret from GitHub Secret
    b64_secret = os.environ.get("GOOGLE_SHEET_SECRET_B64")
    if not b64_secret:
        raise ValueError("Missing GOOGLE_SHEET_SECRET_B64 environment variable")

    service_account_info = json.loads(base64.b64decode(b64_secret))
    
    # Step 2: define scopes and credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)

    # Step 3: connect to Google Sheet
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key("1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4")  # your Sheet ID
    worksheet = sheet.worksheet("UsageLog")

    # Step 4: write new row
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    syd_time = datetime.now(timezone("Australia/Sydney")).strftime("%Y-%m-%d %H:%M:%S")
    worksheet.append_row([syd_time, language, str(report_length)])
