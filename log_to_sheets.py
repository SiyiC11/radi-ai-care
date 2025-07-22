import base64
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class FeedbackLogger:
    WORKSHEET_TITLE = "Feedback"
    HEADER = [
        "Timestamp (UTC)",
        "Translation ID",
        "User ID",
        "Language",
        "File Type",
        "Feedback Text",
        "Device",
        "Extra",
    ]

    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self._client = None
        self._ws = None
        self._connect()

    def log_feedback(self, **kwargs: Any) -> bool:
        return self.append(kwargs)

    def append(self, row_data: Dict[str, Any]) -> bool:
        if not self._ws:
            logger.error("Worksheet not initialised")
            return False
        row = self._build_row(row_data)
        try:
            self._ws.append_row(row, value_input_option="RAW")
            return True
        except Exception as e:
            logger.exception("Failed to append row: %s", e)
            return False

    def _connect(self) -> None:
        secret_b64 = os.getenv("GOOGLE_SHEET_SECRET_B64")
        if not secret_b64:
            raise RuntimeError("Missing env var: GOOGLE_SHEET_SECRET_B64")

        creds_dict = json.loads(base64.b64decode(secret_b64))
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        self._client = gspread.authorize(creds)

        sheet = self._client.open_by_key(self.sheet_id)
        try:
            self._ws = sheet.worksheet(self.WORKSHEET_TITLE)
        except gspread.WorksheetNotFound:
            self._ws = sheet.add_worksheet(title=self.WORKSHEET_TITLE, rows="1000", cols="10")
        self._ensure_header()

    def _ensure_header(self):
        current = self._ws.row_values(1)
        if current != self.HEADER:
            self._ws.update("A1", [self.HEADER])

    def _build_row(self, data: Dict[str, Any]) -> List[Any]:
        row = []
        for col in self.HEADER:
            key = col.lower().replace(" ", "_")
            if col.lower().startswith("timestamp"):
                row.append(_now_iso())
            else:
                row.append(data.get(col, data.get(key, "")))
        return row
class UsageLogger(FeedbackLogger):
    WORKSHEET_TITLE = "UsageLog"
    HEADER = [
        "Timestamp (UTC)",
        "User ID",
        "Daily Count",
        "Session Count",
        "Translation ID",
        "Latency (ms)",
        "Device",
        "Extra",
    ]

    def log_usage(self, **kwargs: Any) -> bool:
        return self.append(kwargs)
