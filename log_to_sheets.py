import os
import base64
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import logging
from typing import Optional
import hashlib
import time
import uuid

logger = logging.getLogger(__name__)

class SimpleLogger:
    """Simple Google Sheets logger with improved session tracking"""
    
    def __init__(self):
        self.client = None
        self.worksheet = None
        self.initialized = False
        self.sheet_id = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"
        self._session_id = None  # Store session ID for reuse
        
    def _initialize_client(self) -> bool:
        """Initialize Google Sheets client"""
        try:
            # Get base64 encoded secret
            b64_secret = os.environ.get("GOOGLE_SHEET_SECRET_B64")
            if not b64_secret:
                logger.warning("GOOGLE_SHEET_SECRET_B64 environment variable not found")
                return False

            # Decode and parse service account info
            service_account_info = json.loads(base64.b64decode(b64_secret))
            
            # Define scopes and create credentials
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scopes)

            # Initialize client and get sheet
            self.client = gspread.authorize(creds)
            sheet = self.client.open_by_key(self.sheet_id)
            
            # Initialize worksheet
            try:
                self.worksheet = sheet.worksheet("UsageLog")
            except gspread.WorksheetNotFound:
                logger.info("UsageLog worksheet not found, creating new one")
                self.worksheet = sheet.add_worksheet(title="UsageLog", rows="1000", cols="7")
                self._initialize_headers()
            
            self.initialized = True
            logger.info("Google Sheets client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            return False
    
    def _initialize_headers(self):
        """Initialize worksheet headers with improved fields"""
        headers = [
            "Date & Time",
            "Language", 
            "Report Length",
            "File Type",
            "Session ID",
            "User ID",
            "Processing Status"
        ]
        try:
            self.worksheet.append_row(headers)
            # Format header row
            self.worksheet.format('A1:G1', {
                "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
            })
            logger.info("Initialized worksheet headers")
        except Exception as e:
            logger.error(f"Failed to initialize headers: {e}")
    
    def _get_sydney_datetime(self) -> str:
        """Get current date and time in Sydney timezone"""
        try:
            sydney_tz = pytz.timezone("Australia/Sydney")
            return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error getting Sydney time: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_session_id(self) -> str:
        """Get or create session ID that persists for the current app session"""
        if self._session_id is None:
            # Create a session ID that will be reused for this app instance
            self._session_id = str(uuid.uuid4())[:8]
            logger.info(f"Created new session ID: {self._session_id}")
        
        return self._session_id
    
    def _create_user_id(self) -> str:
        """Create a simple user identifier based on timestamp + random"""
        try:
            # Create a more unique user identifier
            timestamp = str(int(time.time()))
            random_part = str(uuid.uuid4())[:4]
            return f"user_{timestamp[-4:]}_{random_part}"
        except Exception:
            return "anonymous"
    
    def log_usage(self, 
                  language: str,
                  report_length: int,
                  file_type: str = "manual",
                  processing_status: str = "success") -> bool:
        """
        Log usage data to Google Sheets with improved session tracking
        
        Args:
            language: Language used for translation
            report_length: Length of the input report
            file_type: Type of file processed (txt, pdf, jpg, png, manual, unknown)
            processing_status: Status of processing (success, error, validation_failed)
            
        Returns:
            bool: True if logging successful, False otherwise
        """
        try:
            # Initialize client if needed
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            # Prepare row data with improved tracking
            current_datetime = self._get_sydney_datetime()
            session_id = self._get_session_id()  # Reuses same ID for this session
            user_id = self._create_user_id()     # Unique per interaction
            
            row_data = [
                current_datetime,    # Date & Time
                language,           # Language
                report_length,      # Report Length  
                file_type,          # File Type (pdf, jpg, txt, png, manual, unknown)
                session_id,         # Session ID (same for this app session)
                user_id,            # User ID (unique per interaction)
                processing_status   # Processing Status (success, error, etc.)
            ]
            
            # Log to worksheet
            self.worksheet.append_row(row_data)
            
            logger.info(f"Successfully logged usage: {language}, {report_length} chars, "
                       f"{file_type}, session: {session_id}, status: {processing_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
            return False

# Global instance
_simple_logger = SimpleLogger()

def log_to_google_sheets(language: str, 
                        report_length: int, 
                        file_type: str = "manual",
                        processing_status: str = "success",
                        **kwargs) -> bool:
    """
    Convenience function to log usage data to Google Sheets
    
    Args:
        language: Language used for translation
        report_length: Length of the input report
        file_type: Type of file processed (txt, pdf, jpg, png, manual, unknown)
        processing_status: Status of processing (success, error, validation_failed)
        **kwargs: Additional arguments (ignored for simplicity)
        
    Returns:
        bool: True if logging successful, False otherwise
    """
    return _simple_logger.log_usage(
        language=language,
        report_length=report_length,
        file_type=file_type,
        processing_status=processing_status
    )
