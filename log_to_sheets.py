import os
import base64
import json
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import logging
from typing import Optional, Dict, Any, List
import hashlib
import time

logger = logging.getLogger(__name__)

class SheetsLogger:
    """Enhanced Google Sheets logging with comprehensive metrics tracking"""
    
    def __init__(self):
        self.client = None
        self.worksheet = None
        self.stats_worksheet = None
        self.initialized = False
        self.sheet_id = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"
        self.retry_attempts = 3
        self.retry_delay = 1  # seconds
        
    def _initialize_client(self) -> bool:
        """Initialize Google Sheets client with enhanced error handling"""
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
            
            # Initialize main usage log worksheet
            try:
                self.worksheet = sheet.worksheet("UsageLog")
            except gspread.WorksheetNotFound:
                logger.info("UsageLog worksheet not found, creating new one")
                self.worksheet = sheet.add_worksheet(title="UsageLog", rows="10000", cols="15")
                self._initialize_main_headers()
            
            # Initialize daily stats worksheet
            try:
                self.stats_worksheet = sheet.worksheet("DailyStats")
            except gspread.WorksheetNotFound:
                logger.info("DailyStats worksheet not found, creating new one")
                self.stats_worksheet = sheet.add_worksheet(title="DailyStats", rows="1000", cols="10")
                self._initialize_stats_headers()
            
            self.initialized = True
            logger.info("Google Sheets client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            return False
    
    def _initialize_main_headers(self):
        """Initialize main worksheet headers with comprehensive fields"""
        headers = [
            "Timestamp (Sydney)",
            "Date",
            "Language",
            "Report Length (chars)",
            "Processing Time (ms)",
            "AI Response Time (ms)",
            "Success",
            "Error Message",
            "User Hash",
            "File Type",
            "File Size (MB)",
            "OCR Used",
            "Characters Extracted",
            "Result Length (chars)",
            "Session ID"
        ]
        try:
            self.worksheet.append_row(headers)
            logger.info("Initialized main worksheet headers")
        except Exception as e:
            logger.error(f"Failed to initialize main headers: {e}")
    
    def _initialize_stats_headers(self):
        """Initialize stats worksheet headers"""
        headers = [
            "Date",
            "Total Requests",
            "Successful Requests",
            "Failed Requests",
            "Success Rate (%)",
            "Avg Processing Time (ms)",
            "Total Characters Processed",
            "Languages Used",
            "File Types Used",
            "OCR Usage Count"
        ]
        try:
            self.stats_worksheet.append_row(headers)
            logger.info("Initialized stats worksheet headers")
        except Exception as e:
            logger.error(f"Failed to initialize stats headers: {e}")
    
    def _get_sydney_time(self) -> str:
        """Get current time in Sydney timezone"""
        try:
            sydney_tz = pytz.timezone("Australia/Sydney")
            return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error getting Sydney time: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_sydney_date(self) -> str:
        """Get current date in Sydney timezone"""
        try:
            sydney_tz = pytz.timezone("Australia/Sydney")
            return datetime.now(sydney_tz).strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(f"Error getting Sydney date: {e}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def _create_user_hash(self, user_data: str) -> str:
        """Create anonymized user hash for privacy"""
        try:
            if not user_data:
                user_data = f"session_{int(time.time())}"
            return hashlib.sha256(user_data.encode()).hexdigest()[:12]
        except Exception:
            return "unknown"
    
    def _create_session_id(self) -> str:
        """Create unique session identifier"""
        try:
            timestamp = str(int(time.time()))
            return hashlib.md5(timestamp.encode()).hexdigest()[:8]
        except Exception:
            return "unknown"
    
    def _retry_operation(self, operation, *args, **kwargs):
        """Retry operation with exponential backoff"""
        for attempt in range(self.retry_attempts):
            try:
                return operation(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"API error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise
    
    def log_usage(self, 
                  language: str,
                  report_length: int,
                  processing_time_ms: Optional[int] = None,
                  ai_response_time_ms: Optional[int] = None,
                  success: bool = True,
                  error_message: Optional[str] = None,
                  user_data: str = "",
                  file_type: str = "manual",
                  file_size_mb: float = 0.0,
                  ocr_used: bool = False,
                  characters_extracted: int = 0,
                  result_length: int = 0) -> bool:
        """
        Log comprehensive usage data to Google Sheets
        
        Args:
            language: Language used for translation
            report_length: Length of the input report
            processing_time_ms: Total time taken to process
            ai_response_time_ms: Time taken for AI response specifically
            success: Whether processing was successful
            error_message: Error message if failed
            user_data: User identifier for hashing
            file_type: Type of file processed (text, image, pdf, manual)
            file_size_mb: Size of uploaded file in MB
            ocr_used: Whether OCR was used
            characters_extracted: Number of characters extracted from file
            result_length: Length of AI generated response
            
        Returns:
            bool: True if logging successful, False otherwise
        """
        try:
            # Initialize client if needed
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            # Prepare comprehensive row data
            current_time = self._get_sydney_time()
            current_date = self._get_sydney_date()
            
            row_data = [
                current_time,                                    # Timestamp (Sydney)
                current_date,                                    # Date
                language,                                        # Language
                str(report_length),                             # Report Length (chars)
                str(processing_time_ms) if processing_time_ms else "",  # Processing Time (ms)
                str(ai_response_time_ms) if ai_response_time_ms else "", # AI Response Time (ms)
                "Success" if success else "Failed",            # Success
                error_message or "",                            # Error Message
                self._create_user_hash(user_data),             # User Hash
                file_type,                                      # File Type
                f"{file_size_mb:.3f}" if file_size_mb > 0 else "", # File Size (MB)
                "Yes" if ocr_used else "No",                   # OCR Used
                str(characters_extracted) if characters_extracted > 0 else "", # Characters Extracted
                str(result_length) if result_length > 0 else "",    # Result Length (chars)
                self._create_session_id()                       # Session ID
            ]
            
            # Log to main worksheet with retry
            self._retry_operation(self.worksheet.append_row, row_data)
            
            # Update daily stats asynchronously (don't fail main logging if this fails)
            try:
                self._update_daily_stats(current_date, language, success, processing_time_ms, 
                                       report_length, file_type, ocr_used)
            except Exception as stats_error:
                logger.warning(f"Failed to update daily stats: {stats_error}")
            
            logger.info(f"Successfully logged usage: {language}, {report_length} chars, "
                       f"success: {success}, file_type: {file_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
            return False
    
    def _update_daily_stats(self, date: str, language: str, success: bool, 
                           processing_time_ms: Optional[int], report_length: int,
                           file_type: str, ocr_used: bool):
        """Update daily statistics worksheet"""
        try:
            # Get existing stats for today
            records = self.stats_worksheet.get_all_records()
            today_record = None
            row_index = None
            
            for i, record in enumerate(records):
                if record.get("Date") == date:
                    today_record = record
                    row_index = i + 2  # +2 because of header and 0-based indexing
                    break
            
            if today_record:
                # Update existing record
                total_requests = int(today_record.get("Total Requests", 0)) + 1
                successful_requests = int(today_record.get("Successful Requests", 0)) + (1 if success else 0)
                failed_requests = int(today_record.get("Failed Requests", 0)) + (0 if success else 1)
                success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
                
                # Calculate new average processing time
                old_avg = float(today_record.get("Avg Processing Time (ms)", 0))
                old_count = total_requests - 1
                if processing_time_ms and old_count > 0:
                    new_avg = ((old_avg * old_count) + processing_time_ms) / total_requests
                else:
                    new_avg = processing_time_ms or old_avg
                
                total_chars = int(today_record.get("Total Characters Processed", 0)) + report_length
                
                # Track languages and file types
                languages_used = today_record.get("Languages Used", "")
                if language not in languages_used:
                    languages_used = f"{languages_used},{language}" if languages_used else language
                
                file_types_used = today_record.get("File Types Used", "")
                if file_type not in file_types_used:
                    file_types_used = f"{file_types_used},{file_type}" if file_types_used else file_type
                
                ocr_count = int(today_record.get("OCR Usage Count", 0)) + (1 if ocr_used else 0)
                
                # Update the row
                updated_row = [
                    date,
                    total_requests,
                    successful_requests, 
                    failed_requests,
                    f"{success_rate:.1f}",
                    f"{new_avg:.0f}",
                    total_chars,
                    languages_used,
                    file_types_used,
                    ocr_count
                ]
                
                self._retry_operation(self.stats_worksheet.update, f"A{row_index}:J{row_index}", [updated_row])
                
            else:
                # Create new record
                new_row = [
                    date,
                    1,  # Total Requests
                    1 if success else 0,  # Successful Requests
                    0 if success else 1,  # Failed Requests
                    "100.0" if success else "0.0",  # Success Rate
                    str(processing_time_ms or 0),  # Avg Processing Time
                    report_length,  # Total Characters Processed
                    language,  # Languages Used
                    file_type,  # File Types Used
                    1 if ocr_used else 0  # OCR Usage Count
                ]
                
                self._retry_operation(self.stats_worksheet.append_row, new_row)
                
        except Exception as e:
            logger.error(f"Error updating daily stats: {e}")
            raise
    
    def get_usage_stats(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive usage statistics for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with detailed usage statistics or None if failed
        """
        try:
            if not self.initialized:
                if not self._initialize_client():
                    return None
            
            # Get records from main worksheet
            records = self._retry_operation(self.worksheet.get_all_records)
            if not records:
                return self._empty_stats_response(days)
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter recent records
            recent_records = []
            for record in records:
                try:
                    record_date = datetime.strptime(record.get("Timestamp (Sydney)", ""), "%Y-%m-%d %H:%M:%S")
                    if record_date >= cutoff_date:
                        recent_records.append(record)
                except (ValueError, TypeError):
                    continue
            
            if not recent_records:
                return self._empty_stats_response(days)
            
            # Calculate comprehensive statistics
            stats = self._calculate_detailed_stats(recent_records, days)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return None
    
    def _empty_stats_response(self, days: int) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            "period_days": days,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "success_rate": 0,
            "avg_processing_time_ms": 0,
            "total_characters_processed": 0,
            "by_language": {},
            "by_file_type": {},
            "ocr_usage": {"count": 0, "percentage": 0},
            "daily_breakdown": [],
            "peak_usage_day": None,
            "avg_report_length": 0
        }
    
    def _calculate_detailed_stats(self, records: List[Dict], days: int) -> Dict[str, Any]:
        """Calculate detailed statistics from records"""
        total_requests = len(records)
        successful_requests = sum(1 for r in records if r.get("Success") == "Success")
        failed_requests = total_requests - successful_requests
        
        # Processing times
        processing_times = [
            int(r.get("Processing Time (ms)", 0)) 
            for r in records 
            if r.get("Processing Time (ms)") and r.get("Processing Time (ms)").isdigit()
        ]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Character counts
        report_lengths = [
            int(r.get("Report Length (chars)", 0))
            for r in records
            if r.get("Report Length (chars)") and r.get("Report Length (chars)").isdigit()
        ]
        total_characters = sum(report_lengths)
        avg_report_length = total_characters / len(report_lengths) if report_lengths else 0
        
        # Language distribution
        language_counts = {}
        for record in records:
            lang = record.get("Language", "Unknown")
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # File type distribution
        file_type_counts = {}
        for record in records:
            file_type = record.get("File Type", "Unknown")
            file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1
        
        # OCR usage
        ocr_used_count = sum(1 for r in records if r.get("OCR Used") == "Yes")
        ocr_percentage = (ocr_used_count / total_requests) * 100 if total_requests > 0 else 0
        
        # Daily breakdown
        daily_counts = {}
        for record in records:
            date = record.get("Date", "Unknown")
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        daily_breakdown = [
            {"date": date, "requests": count}
            for date, count in sorted(daily_counts.items())
        ]
        
        # Peak usage day
        peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
            "avg_processing_time_ms": avg_processing_time,
            "total_characters_processed": total_characters,
            "avg_report_length": avg_report_length,
            "by_language": language_counts,
            "by_file_type": file_type_counts,
            "ocr_usage": {
                "count": ocr_used_count,
                "percentage": ocr_percentage
            },
            "daily_breakdown": daily_breakdown,
            "peak_usage_day": {
                "date": peak_day[0],
                "requests": peak_day[1]
            } if peak_day else None
        }
    
    def get_daily_stats(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific date from the daily stats worksheet"""
        try:
            if not self.initialized:
                if not self._initialize_client():
                    return None
            
            if not date:
                date = self._get_sydney_date()
            
            records = self._retry_operation(self.stats_worksheet.get_all_records)
            
            for record in records:
                if record.get("Date") == date:
                    return {
                        "date": date,
                        "total_requests": int(record.get("Total Requests", 0)),
                        "successful_requests": int(record.get("Successful Requests", 0)),
                        "failed_requests": int(record.get("Failed Requests", 0)),
                        "success_rate": float(record.get("Success Rate (%)", 0)),
                        "avg_processing_time_ms": float(record.get("Avg Processing Time (ms)", 0)),
                        "total_characters_processed": int(record.get("Total Characters Processed", 0)),
                        "languages_used": record.get("Languages Used", "").split(",") if record.get("Languages Used") else [],
                        "file_types_used": record.get("File Types Used", "").split(",") if record.get("File Types Used") else [],
                        "ocr_usage_count": int(record.get("OCR Usage Count", 0))
                    }
            
            return None  # No record found for this date
            
        except Exception as e:
            logger.error(f"Error getting daily stats for {date}: {e}")
            return None

# Global instance
_sheets_logger = SheetsLogger()

def log_to_google_sheets(language: str, 
                        report_length: int, 
                        processing_time_ms: Optional[int] = None,
                        ai_response_time_ms: Optional[int] = None,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        user_data: str = "",
                        file_type: str = "manual",
                        file_size_mb: float = 0.0,
                        ocr_used: bool = False,
                        characters_extracted: int = 0,
                        result_length: int = 0) -> bool:
    """
    Enhanced convenience function to log comprehensive usage data to Google Sheets
    
    Args:
        language: Language used for translation
        report_length: Length of the input report
        processing_time_ms: Total time taken to process
        ai_response_time_ms: Time taken for AI response specifically
        success: Whether processing was successful
        error_message: Error message if failed
        user_data: User identifier for hashing
        file_type: Type of file processed (text, image, pdf, manual)
        file_size_mb: Size of uploaded file in MB
        ocr_used: Whether OCR was used
        characters_extracted: Number of characters extracted from file
        result_length: Length of AI generated response
        
    Returns:
        bool: True if logging successful, False otherwise
    """
    return _sheets_logger.log_usage(
        language=language,
        report_length=report_length,
        processing_time_ms=processing_time_ms,
        ai_response_time_ms=ai_response_time_ms,
        success=success,
        error_message=error_message,
        user_data=user_data,
        file_type=file_type,
        file_size_mb=file_size_mb,
        ocr_used=ocr_used,
        characters_extracted=characters_extracted,
        result_length=result_length
    )

def get_usage_statistics(days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive usage statistics for the last N days
    
    Args:
        days: Number of days to look back
        
    Returns:
        Dictionary with detailed usage statistics or None if failed
    """
    return _sheets_logger.get_usage_stats(days)

def get_daily_statistics(date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get statistics for a specific date
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Dictionary with daily statistics or None if failed
    """
    return _sheets_logger.get_daily_stats(date)

# Backwards compatibility functions
def get_sydney_time() -> str:
    """Get current Sydney time (deprecated, use SheetsLogger._get_sydney_time)"""
    return _sheets_logger._get_sydney_time()

def get_sydney_date() -> str:
    """Get current Sydney date"""
    return _sheets_logger._get_sydney_date()
