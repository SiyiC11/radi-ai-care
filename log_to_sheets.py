import os
import base64
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pytz
import logging
from typing import Optional, Dict, Any
import hashlib

logger = logging.getLogger(__name__)

class SheetsLogger:
    """Enhanced Google Sheets logging with better error handling and retry logic"""
    
    def __init__(self):
        self.client = None
        self.worksheet = None
        self.initialized = False
        self.sheet_id = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"
        
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
            creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)

            # Initialize client and get worksheet
            self.client = gspread.authorize(creds)
            sheet = self.client.open_by_key(self.sheet_id)
            
            # Try to get existing worksheet or create new one
            try:
                self.worksheet = sheet.worksheet("UsageLog")
            except gspread.WorksheetNotFound:
                logger.info("UsageLog worksheet not found, creating new one")
                self.worksheet = sheet.add_worksheet(title="UsageLog", rows="1000", cols="10")
                self._initialize_headers()
            
            self.initialized = True
            logger.info("Google Sheets client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            return False
    
    def _initialize_headers(self):
        """Initialize worksheet headers"""
        headers = [
            "Timestamp (Sydney)",
            "Language",
            "Report Length",
            "Processing Time (ms)",
            "Success",
            "Error Message",
            "User Hash",
            "File Type",
            "OCR Used"
        ]
        try:
            self.worksheet.append_row(headers)
            logger.info("Initialized worksheet headers")
        except Exception as e:
            logger.error(f"Failed to initialize headers: {e}")
    
    def _get_sydney_time(self) -> str:
        """Get current time in Sydney timezone"""
        try:
            sydney_tz = pytz.timezone("Australia/Sydney")
            return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error getting Sydney time: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _create_user_hash(self, user_data: str) -> str:
        """Create anonymized user hash for privacy"""
        try:
            # Create hash from user data (could be IP, session ID, etc.)
            return hashlib.sha256(user_data.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"
    
    def log_usage(self, 
                  language: str,
                  report_length: int,
                  processing_time_ms: Optional[int] = None,
                  success: bool = True,
                  error_message: Optional[str] = None,
                  user_data: str = "",
                  file_type: str = "text",
                  ocr_used: bool = False) -> bool:
        """
        Log usage to Google Sheets
        
        Args:
            language: Language used for translation
            report_length: Length of the input report
            processing_time_ms: Time taken to process (optional)
            success: Whether processing was successful
            error_message: Error message if failed (optional)
            user_data: User identifier for hashing (optional)
            file_type: Type of file processed (text, image, pdf)
            ocr_used: Whether OCR was used
            
        Returns:
            bool: True if logging successful, False otherwise
        """
        try:
            # Initialize client if needed
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            # Prepare row data
            row_data = [
                self._get_sydney_time(),
                language,
                str(report_length),
                str(processing_time_ms) if processing_time_ms else "",
                "Success" if success else "Failed",
                error_message or "",
                self._create_user_hash(user_data),
                file_type,
                "Yes" if ocr_used else "No"
            ]
            
            # Append to worksheet
            self.worksheet.append_row(row_data)
            logger.info(f"Successfully logged usage: {language}, {report_length} chars")
            return True
            
        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error logging to sheets: {e}")
            return False
    
    def get_usage_stats(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get usage statistics for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with usage statistics or None if failed
        """
        try:
            if not self.initialized:
                if not self._initialize_client():
                    return None
            
            # Get all records
            records = self.worksheet.get_all_records()
            if not records:
                return {"total": 0, "by_language": {}, "success_rate": 0}
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter and analyze records
            recent_records = []
            for record in records:
                try:
                    record_date = datetime.strptime(record.get("Timestamp (Sydney)", ""), "%Y-%m-%d %H:%M:%S")
                    if record_date >= cutoff_date:
                        recent_records.append(record)
                except (ValueError, TypeError):
                    continue
            
            # Calculate statistics
            total_requests = len(recent_records)
            successful_requests = sum(1 for r in recent_records if r.get("Success") == "Success")
            
            language_counts = {}
            for record in recent_records:
                lang = record.get("Language", "Unknown")
                language_counts[lang] = language_counts.get(lang, 0) + 1
            
            return {
                "total": total_requests,
                "successful": successful_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
                "by_language": language_counts,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return None

# Global instance
_sheets_logger = SheetsLogger()

def log_to_google_sheets(language: str, 
                        report_length: int, 
                        processing_time_ms: Optional[int] = None,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        user_data: str = "",
                        file_type: str = "text",
                        ocr_used: bool = False) -> bool:
    """
    Convenience function to log usage to Google Sheets
    
    Args:
        language: Language used for translation
        report_length: Length of the input report
        processing_time_ms: Time taken to process (optional)
        success: Whether processing was successful
        error_message: Error message if failed (optional)
        user_data: User identifier for hashing (optional)
        file_type: Type of file processed (text, image, pdf)
        ocr_used: Whether OCR was used
        
    Returns:
        bool: True if logging successful, False otherwise
    """
    return _sheets_logger.log_usage(
        language=language,
        report_length=report_length,
        processing_time_ms=processing_time_ms,
        success=success,
        error_message=error_message,
        user_data=user_data,
        file_type=file_type,
        ocr_used=ocr_used
    )

def get_usage_statistics(days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Get usage statistics for the last N days
    
    Args:
        days: Number of days to look back
        
    Returns:
        Dictionary with usage statistics or None if failed
    """
    return _sheets_logger.get_usage_stats(days)

# For backwards compatibility
def get_sydney_time() -> str:
    """Get current Sydney time (deprecated, use SheetsLogger._get_sydney_time)"""
    return _sheets_logger._get_sydney_time()
