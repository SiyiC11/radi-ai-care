"""
RadiAI.Care Google Sheets 數據記錄模塊
優化版本，支援使用記錄和回饋記錄
"""

import os
import base64
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import logging
from typing import Optional, Dict, Any
import uuid
import time

# 配置日誌
logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    """Google Sheets 數據記錄器（增強版）"""
    
    def __init__(self):
        self.client = None
        self.usage_worksheet = None
        self.feedback_worksheet = None
        self.initialized = False
        self.sheet_id = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"
        self._session_id = None
        
    def _initialize_client(self) -> bool:
        """初始化 Google Sheets 客戶端"""
        try:
            # 獲取 base64 編碼的服務帳戶密鑰
            b64_secret = os.environ.get("GOOGLE_SHEET_SECRET_B64")
            if not b64_secret:
                logger.warning("GOOGLE_SHEET_SECRET_B64 環境變量未找到")
                return False

            # 解碼並解析服務帳戶信息
            try:
                service_account_info = json.loads(base64.b64decode(b64_secret))
            except Exception as e:
                logger.error(f"解析服務帳戶信息失敗: {e}")
                return False
            
            # 定義權限範圍並創建憑證
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                service_account_info, scopes
            )

            # 初始化客戶端並獲取工作表
            self.client = gspread.authorize(creds)
            sheet = self.client.open_by_key(self.sheet_id)
            
            # 初始化使用記錄工作表
            try:
                self.usage_worksheet = sheet.worksheet("UsageLog")
            except gspread.WorksheetNotFound:
                logger.info("UsageLog 工作表未找到，正在創建新工作表")
                self.usage_worksheet = sheet.add_worksheet(
                    title="UsageLog", rows="1000", cols="12"
                )
                self._initialize_usage_headers()
            
            # 初始化回饋工作表
            try:
                self.feedback_worksheet = sheet.worksheet("Feedback")
            except gspread.WorksheetNotFound:
                logger.info("Feedback 工作表未找到，正在創建新工作表")
                self.feedback_worksheet = sheet.add_worksheet(
                    title="Feedback", rows="1000", cols="20"
                )
                self._initialize_feedback_headers()
            
            self.initialized = True
            logger.info("Google Sheets 客戶端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化 Google Sheets 客戶端失敗: {e}")
            return False
    
    def _initialize_usage_headers(self):
        """初始化使用記錄工作表標題行"""
        headers = [
            "Date & Time",
            "Language",
            "Report Length", 
            "File Type",
            "Session ID",
            "User ID",
            "Processing Status",
            "Processing Time (ms)",
            "Translation ID",
            "Medical Terms Count",
            "Confidence Score",
            "App Version"
        ]
        try:
            self.usage_worksheet.append_row(headers)
            self._format_header_row(self.usage_worksheet, len(headers))
            logger.info("使用記錄工作表標題行初始化完成")
        except Exception as e:
            logger.error(f"初始化使用記錄標題行失敗: {e}")
    
    def _initialize_feedback_headers(self):
        """初始化回饋工作表標題行"""
        headers = [
            "Date & Time",
            "Translation ID",
            "Language",
            "Feedback Type",
            "Sentiment",
            "Clarity Score",
            "Usefulness Score", 
            "Accuracy Score",
            "Recommendation Score",
            "Overall Satisfaction",
            "Issues",
            "Suggestion",
            "Email",
            "Report Length",
            "File Type",
            "Medical Terms Count",
            "Confidence Score",
            "Session ID",
            "User ID",
            "App Version"
        ]
        try:
            self.feedback_worksheet.append_row(headers)
            self._format_header_row(self.feedback_worksheet, len(headers))
            logger.info("回饋工作表標題行初始化完成")
        except Exception as e:
            logger.error(f"初始化回饋標題行失敗: {e}")
    
    def _format_header_row(self, worksheet, col_count: int):
        """格式化標題行"""
        try:
            # 設置標題行格式
            cell_range = f"A1:{chr(64 + col_count)}1"
            worksheet.format(cell_range, {
                "backgroundColor": {
                    "red": 0.2, "green": 0.6, "blue": 0.9
                },
                "textFormat": {
                    "bold": True, 
                    "foregroundColor": {
                        "red": 1, "green": 1, "blue": 1
                    }
                }
            })
        except Exception as e:
            logger.warning(f"格式化標題行失敗: {e}")
    
    def _get_sydney_datetime(self) -> str:
        """獲取悉尼時區的當前日期時間"""
        try:
            sydney_tz = pytz.timezone("Australia/Sydney")
            return datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"獲取悉尼時間錯誤: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_session_id(self) -> str:
        """獲取或創建會話ID"""
        if self._session_id is None:
            self._session_id = str(uuid.uuid4())[:8]
            logger.info(f"創建新會話ID: {self._session_id}")
        return self._session_id
    
    def _create_user_id(self) -> str:
        """創建用戶標識符"""
        try:
            timestamp = str(int(time.time()))
            random_part = str(uuid.uuid4())[:4]
            return f"user_{timestamp[-4:]}_{random_part}"
        except Exception:
            return "anonymous_user"
    
    def log_usage(self, **kwargs) -> bool:
        """
        記錄使用情況到 Google Sheets
        
        Args:
            **kwargs: 使用記錄數據
            
        Returns:
            bool: 記錄是否成功
        """
        try:
            # 如果需要，初始化客戶端
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            # 準備行數據
            current_datetime = self._get_sydney_datetime()
            session_id = self._get_session_id()
            user_id = self._create_user_id()
            
            row_data = [
                current_datetime,                                    # Date & Time
                kwargs.get('language', ''),                        # Language
                kwargs.get('report_length', 0),                    # Report Length
                kwargs.get('file_type', 'manual'),                 # File Type
                session_id,                                         # Session ID
                user_id,                                           # User ID
                kwargs.get('processing_status', 'unknown'),        # Processing Status
                kwargs.get('latency_ms', 0),                       # Processing Time (ms)
                kwargs.get('translation_id', ''),                  # Translation ID
                kwargs.get('medical_terms_count', 0),              # Medical Terms Count
                kwargs.get('confidence_score', 0),                 # Confidence Score
                kwargs.get('app_version', 'unknown')               # App Version
            ]
            
            # 記錄到工作表
            self.usage_worksheet.append_row(row_data)
            
            logger.info(f"成功記錄使用情況: {kwargs.get('language')}, {kwargs.get('processing_status')}")
            return True
            
        except Exception as e:
            logger.error(f"記錄使用情況失敗: {e}")
            return False
    
    def log_feedback(self, **kwargs) -> bool:
        """
        記錄回饋到 Google Sheets
        
        Args:
            **kwargs: 回饋數據
            
        Returns:
            bool: 記錄是否成功
        """
        try:
            # 如果需要，初始化客戶端
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            # 準備行數據
            current_datetime = self._get_sydney_datetime()
            session_id = self._get_session_id()
            user_id = self._create_user_id()
            
            row_data = [
                current_datetime,                                    # Date & Time
                kwargs.get('translation_id', ''),                  # Translation ID
                kwargs.get('language', ''),                        # Language
                kwargs.get('feedback_type', 'unknown'),            # Feedback Type
                kwargs.get('sentiment', ''),                       # Sentiment
                kwargs.get('clarity_score', 0),                    # Clarity Score
                kwargs.get('usefulness_score', 0),                 # Usefulness Score
                kwargs.get('accuracy_score', 0),                   # Accuracy Score
                kwargs.get('recommendation_score', 0),             # Recommendation Score
                kwargs.get('overall_satisfaction', 0),             # Overall Satisfaction
                kwargs.get('issues', ''),                          # Issues
                kwargs.get('suggestion', ''),                      # Suggestion
                kwargs.get('email', ''),                           # Email
                kwargs.get('report_length', 0),                    # Report Length
                kwargs.get('file_type', 'manual'),                 # File Type
                kwargs.get('medical_terms_detected', 0),           # Medical Terms Count
                kwargs.get('confidence_score', 0),                 # Confidence Score
                session_id,                                         # Session ID
                user_id,                                           # User ID
                kwargs.get('app_version', 'unknown')               # App Version
            ]
            
            # 記錄到回饋工作表
            self.feedback_worksheet.append_row(row_data)
            
            logger.info(f"成功記錄回饋: {kwargs.get('translation_id')}, {kwargs.get('feedback_type')}")
            return True
            
        except Exception as e:
            logger.error(f"記錄回饋失敗: {e}")
            return False

# 全局實例
_sheets_logger = GoogleSheetsLogger()

def log_to_google_sheets(**kwargs) -> bool:
    """
    統一的記錄函數，根據 processing_status 決定記錄類型
    
    Args:
        **kwargs: 記錄數據
        
    Returns:
        bool: 記錄是否成功
    """
    processing_status = kwargs.get('processing_status', '')
    
    if processing_status == 'feedback':
        # 記錄回饋數據
        return _sheets_logger.log_feedback(**kwargs)
    else:
        # 記錄使用數據
        return _sheets_logger.log_usage(**kwargs)

def log_usage_to_sheets(**kwargs) -> bool:
    """
    專門記錄使用情況的函數
    
    Args:
        **kwargs: 使用記錄數據
        
    Returns:
        bool: 記錄是否成功
    """
    return _sheets_logger.log_usage(**kwargs)

def log_feedback_to_sheets(**kwargs) -> bool:
    """
    專門記錄回饋的函數
    
    Args:
        **kwargs: 回饋數據
        
    Returns:
        bool: 記錄是否成功
    """
    return _sheets_logger.log_feedback(**kwargs)

def get_session_id() -> str:
    """獲取當前會話ID"""
    return _sheets_logger._get_session_id()

def reset_session() -> None:
    """重置會話ID（用於測試或特殊情況）"""
    _sheets_logger._session_id = None
    logger.info("會話ID已重置")

class AnalyticsHelper:
    """分析輔助工具"""
    
    @staticmethod
    def calculate_processing_time(start_time: float) -> int:
        """
        計算處理時間
        
        Args:
            start_time: 開始時間（time.time()）
            
        Returns:
            int: 處理時間（毫秒）
        """
        try:
            return int((time.time() - start_time) * 1000)
        except Exception:
            return 0
    
    @staticmethod
    def get_file_type_from_filename(filename: str) -> str:
        """
        從文件名獲取文件類型
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件類型
        """
        try:
            if not filename:
                return "unknown"
            extension = filename.lower().split('.')[-1]
            return extension if extension in ['pdf', 'txt', 'docx', 'doc'] else "unknown"
        except Exception:
            return "unknown"
    
    @staticmethod
    def validate_report_length(report_text: str) -> int:
        """
        驗證並返回報告長度
        
        Args:
            report_text: 報告文本
            
        Returns:
            int: 報告長度
        """
        try:
            return len(report_text) if report_text else 0
        except Exception:
            return 0
    
    @staticmethod
    def create_analytics_summary(**kwargs) -> Dict[str, Any]:
        """
        創建分析摘要
        
        Args:
            **kwargs: 分析數據
            
        Returns:
            Dict: 分析摘要
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'session_id': get_session_id(),
            'metrics': kwargs
        }

# 測試函數
def test_logging():
    """測試日誌記錄功能"""
    try:
        # 測試使用記錄
        usage_success = log_usage_to_sheets(
            language="简体中文",
            report_length=1500,
            file_type="pdf",
            processing_status="success",
            latency_ms=2500,
            translation_id=str(uuid.uuid4()),
            medical_terms_count=5,
            confidence_score=0.85,
            app_version="v4.2-test"
        )
        
        # 測試回饋記錄
        feedback_success = log_feedback_to_sheets(
            translation_id=str(uuid.uuid4()),
            language="简体中文",
            feedback_type="detailed",
            clarity_score=4,
            usefulness_score=5,
            accuracy_score=4,
            recommendation_score=8,
            overall_satisfaction=4.3,
            issues="無問題",
            suggestion="很好用",
            app_version="v4.2-test"
        )
        
        if usage_success and feedback_success:
            print("✅ 所有測試記錄成功")
        else:
            print(f"❌ 測試記錄部分失敗 - 使用記錄: {usage_success}, 回饋記錄: {feedback_success}")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    # 運行測試
    test_logging()
