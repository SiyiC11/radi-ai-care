import os
import json
import base64
import uuid
import datetime as dt
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


@dataclass
class GoogleSheetsLogger:
    sheet_id: str
    worksheet_title: str = "Feedback"
    verify_write: bool = False
    creds_b64_env: str = "GOOGLE_SHEET_SECRET_B64"

    client: Optional[gspread.Client] = field(default=None, init=False)
    worksheet: Optional[gspread.Worksheet] = field(default=None, init=False)
    initialized: bool = field(default=False, init=False)
    last_error: Optional[str] = field(default=None, init=False)

    # ------------------------- Public API ------------------------- #
    def init(self) -> bool:
        """Initialize connection and worksheet (idempotent)."""
        if self.initialized:
            return True
        try:
            creds_json = self._load_service_account()
            creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            sheet = self.client.open_by_key(self.sheet_id)
            try:
                self.worksheet = sheet.worksheet(self.worksheet_title)
            except gspread.WorksheetNotFound:
                self.worksheet = sheet.add_worksheet(title=self.worksheet_title, rows="2000", cols="30")
                self._write_headers()
            self.initialized = True
            return True
        except Exception as e:
            self.last_error = traceback.format_exc()
            return False

    def append_feedback(self, row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Append one feedback row. Returns (ok, error_msg)."""
        if not self.initialized and not self.init():
            return False, self.last_error or "Failed to initialize GoogleSheetsLogger"

        try:
            values = self._row_to_list(row)
            self.worksheet.append_row(values, value_input_option="RAW")

            if self.verify_write and row.get("translation_id"):
                ok = self._verify_translation_id(row["translation_id"])
                if not ok:
                    return False, "Verification failed: translation_id not found after append"
            return True, None
        except Exception:
            err = traceback.format_exc()
            self.last_error = err
            return False, err

    def diagnose(self) -> Dict[str, Any]:
        """Return diagnostics for UI display."""
        info = {
            "initialized": self.initialized,
            "worksheet_title": self.worksheet_title,
            "sheet_id_present": bool(self.sheet_id),
            "last_error": self.last_error,
        }
        if not self.initialized:
            # Try init silently
            _ = self.init()
        if self.initialized:
            try:
                info.update({
                    "spreadsheet_title": self.worksheet.spreadsheet.title,
                    "worksheets": [ws.title for ws in self.worksheet.spreadsheet.worksheets()],
                    "headers": self.worksheet.row_values(1)
                })
            except Exception:
                info["ws_error"] = traceback.format_exc()
        return info

    # ------------------------- Internal Helpers ------------------------- #
    def _load_service_account(self) -> Dict[str, Any]:
        b64 = os.environ.get(self.creds_b64_env)
        if not b64:
            raise RuntimeError(f"Missing env var {self.creds_b64_env}")
        return json.loads(base64.b64decode(b64))

    def _write_headers(self):
        headers = [
            "timestamp_utc",
            "uuid",
            "translation_id",
            "feedback_text",
            "language",
            "file_type",
            "device_type",
            "user_agent",
            "extra",
        ]
        self.worksheet.update("A1", [headers])

    def _row_to_list(self, row: Dict[str, Any]) -> List[Any]:
        # Ensure fixed order as headers above
        now = dt.datetime.utcnow().isoformat()
        return [
            row.get("timestamp_utc", now),
            row.get("uuid", str(uuid.uuid4())),
            row.get("translation_id", ""),
            row.get("feedback_text", ""),
            row.get("language", ""),
            row.get("file_type", ""),
            row.get("device_type", ""),
            row.get("user_agent", ""),
            json.dumps(row.get("extra", {}), ensure_ascii=False),
        ]

    def _verify_translation_id(self, tid: str) -> bool:
        try:
            cell = self.worksheet.find(tid)
            return cell is not None
        except Exception:
            return False
