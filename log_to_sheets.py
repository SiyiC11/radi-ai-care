import os
import json
import base64
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 取得 Google Sheets 憑證
encoded = os.getenv("GCP_SERVICE_ACCOUNT_ENCODED")
if not encoded:
    raise Exception("Missing GCP_SERVICE_ACCOUNT_ENCODED environment variable")

credentials_info = json.loads(base64.b64decode(encoded))
creds = Credentials.from_service_account_info(credentials_info)
gc = gspread.authorize(creds)

# 開啟 Google Sheets（用你的 Sheet 名稱）
SPREADSHEET_NAME = "RadiAI_Usage_Log"
try:
    sh = gc.open(SPREADSHEET_NAME)
except gspread.exceptions.SpreadsheetNotFound:
    sh = gc.create(SPREADSHEET_NAME)
    sh.share('', perm_type='anyone', role='writer')  # 可視情況改為特定 email

worksheet = sh.sheet1

# 讀取本地 log.csv 並寫入 Sheets
if not os.path.exists("log.csv"):
    raise FileNotFoundError("log.csv not found")

df = pd.read_csv("log.csv", header=None, names=["timestamp"])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date
df["time"] = df["timestamp"].dt.time

# 清空再寫入（簡單方式）
worksheet.clear()
worksheet.append_row(["timestamp", "date", "time"])

for index, row in df.iterrows():
    worksheet.append_row([str(row["timestamp"]), str(row["date"]), str(row["time"])])

print("✅ Log uploaded to Google Sheets.")
