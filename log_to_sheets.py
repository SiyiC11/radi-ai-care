# log_to_sheets.py
"""
Google Sheets 數據記錄模塊
用於記錄 RadiAI.Care 的使用統計數據
"""

import os
import base64
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
import logging
from typing import Optional
import uuid
import time

# 配置日誌
logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    """Google Sheets 數據記錄器"""
    
    def __init__(self):
        self.client = None
        self.worksheet = None
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
            
            # 初始化工作表
            try:
                self.worksheet = sheet.worksheet("UsageLog")
            except gspread.WorksheetNotFound:
                logger.info("UsageLog 工作表未找到，正在創建新工作表")
                self.worksheet = sheet.add_worksheet(
                    title="UsageLog", rows="1000", cols="8"
                )
                self._initialize_headers()
            
            self.initialized = True
            logger.info("Google Sheets 客戶端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化 Google Sheets 客戶端失敗: {e}")
            return False
    
    def _initialize_headers(self):
        """初始化工作表標題行"""
        headers = [
            "Date & Time",
            "Language", 
            "Report Length",
            "File Type",
            "Session ID",
            "User ID",
            "Processing Status",
            "Processing Time (ms)"
        ]
        try:
            self.worksheet.append_row(headers)
            # 格式化標題行
            self.worksheet.format('A1:H1', {
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
            logger.info("工作表標題行初始化完成")
        except Exception as e:
            logger.error(f"初始化標題行失敗: {e}")
    
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
    
    def log_usage(self, 
                  language: str,
                  report_length: int,
                  file_type: str = "manual",
                  processing_status: str = "success",
                  processing_time_ms: int = 0) -> bool:
        """
        記錄使用情況到 Google Sheets
        
        Args:
            language: 使用的語言
            report_length: 報告長度
            file_type: 文件類型 (txt, pdf, docx, manual, unknown)
            processing_status: 處理狀態 (success, error, validation_failed)
            processing_time_ms: 處理時間（毫秒）
            
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
                current_datetime,        # Date & Time
                language,               # Language
                report_length,          # Report Length  
                file_type,              # File Type
                session_id,             # Session ID
                user_id,                # User ID
                processing_status,      # Processing Status
                processing_time_ms      # Processing Time (ms)
            ]
            
            # 記錄到工作表
            self.worksheet.append_row(row_data)
            
            logger.info(
                f"成功記錄使用情況: {language}, "
                f"{report_length} chars, {file_type}, "
                f"session: {session_id}, status: {processing_status}"
            )
            return True
            
        except Exception as e:
            logger.error(f"記錄使用情況失敗: {e}")
            return False

# 全局實例
_sheets_logger = GoogleSheetsLogger()

def log_to_google_sheets(language: str, 
                        report_length: int, 
                        file_type: str = "manual",
                        processing_status: str = "success",
                        processing_time_ms: int = 0,
                        **kwargs) -> bool:
    """
    便捷函數：記錄使用數據到 Google Sheets
    
    Args:
        language: 使用的語言
        report_length: 報告長度
        file_type: 文件類型 (txt, pdf, docx, manual, unknown)
        processing_status: 處理狀態 (success, error, validation_failed)
        processing_time_ms: 處理時間（毫秒）
        **kwargs: 其他參數（為了兼容性，被忽略）
        
    Returns:
        bool: 記錄是否成功
    """
    return _sheets_logger.log_usage(
        language=language,
        report_length=report_length,
        file_type=file_type,
        processing_status=processing_status,
        processing_time_ms=processing_time_ms
    )

def get_session_id() -> str:
    """獲取當前會話ID"""
    return _sheets_logger._get_session_id()

def reset_session() -> None:
    """重置會話ID（用於測試或特殊情況）"""
    _sheets_logger._session_id = None
    logger.info("會話ID已重置")

class UsageMetrics:
    """使用統計指標類"""
    
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

# 使用示例和測試函數
def test_logging():
    """測試日誌記錄功能"""
    try:
        # 測試記錄
        success = log_to_google_sheets(
            language="简体中文",
            report_length=1500,
            file_type="pdf",
            processing_status="success",
            processing_time_ms=2500
        )
        
        if success:
            print("✅ 測試記錄成功")
        else:
            print("❌ 測試記錄失敗")
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    # 運行測試
    test_logging()
