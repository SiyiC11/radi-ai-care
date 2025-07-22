"""
RadiAI.Care Google Sheets 數據記錄模塊 - 終極修復版
===============================================
解決 Feedback Sheet 寫入問題的終極方案
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

logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    """Google Sheets 數據記錄器（終極修復版）"""
    
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
            b64_secret = os.environ.get("GOOGLE_SHEET_SECRET_B64")
            if not b64_secret:
                logger.warning("GOOGLE_SHEET_SECRET_B64 環境變量未找到")
                return False

            try:
                service_account_info = json.loads(base64.b64decode(b64_secret))
            except Exception as e:
                logger.error(f"解析服務帳戶信息失敗: {e}")
                return False
            
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                service_account_info, scopes
            )

            self.client = gspread.authorize(creds)
            sheet = self.client.open_by_key(self.sheet_id)
            
            # 初始化 UsageLog 工作表
            try:
                self.usage_worksheet = sheet.worksheet("UsageLog")
                logger.info("UsageLog 工作表連接成功")
            except gspread.WorksheetNotFound:
                logger.info("創建新的 UsageLog 工作表")
                self.usage_worksheet = sheet.add_worksheet(
                    title="UsageLog", rows="1000", cols="12"
                )
                self._initialize_usage_headers()
            
            # ============ 終極修復 Feedback 工作表 ============
            self._initialize_feedback_worksheet_ultimate_fix(sheet)
            
            self.initialized = True
            logger.info("Google Sheets 客戶端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化 Google Sheets 客戶端失敗: {e}")
            return False
    
    def _initialize_feedback_worksheet_ultimate_fix(self, sheet):
        """終極修復 Feedback 工作表初始化"""
        try:
            # 嘗試獲取現有的 Feedback 工作表
            try:
                self.feedback_worksheet = sheet.worksheet("Feedback")
                logger.info("找到現有的 Feedback 工作表")
                
                # 檢查工作表是否有標題行
                try:
                    headers = self.feedback_worksheet.row_values(1)
                    if not headers or len(headers) < 10:
                        logger.info("Feedback 工作表缺少標題行，重新初始化")
                        self._setup_feedback_headers()
                    else:
                        logger.info(f"Feedback 工作表標題行正常，共 {len(headers)} 列")
                except Exception as e:
                    logger.warning(f"檢查 Feedback 標題行失敗: {e}")
                    self._setup_feedback_headers()
                    
            except gspread.WorksheetNotFound:
                logger.info("Feedback 工作表不存在，創建新工作表")
                
                # ============ 修復方案 1: 使用安全的工作表名稱 ============
                # 根據搜索結果，某些名稱可能導致問題，我們使用絕對安全的名稱
                safe_title = "FeedbackData"
                
                # 刪除可能存在的同名工作表
                try:
                    existing = sheet.worksheet(safe_title)
                    sheet.del_worksheet(existing)
                    logger.info(f"刪除現有的 {safe_title} 工作表")
                    time.sleep(2)  # 等待刪除完成
                except gspread.WorksheetNotFound:
                    pass
                
                # 創建新工作表，使用較小的初始大小避免問題
                self.feedback_worksheet = sheet.add_worksheet(
                    title=safe_title, 
                    rows=100,  # 使用較小的行數避免 1000 行問題
                    cols=25    # 足夠的列數
                )
                
                # 等待工作表創建完成
                time.sleep(3)
                logger.info(f"成功創建 {safe_title} 工作表")
                
                # 設置標題行
                self._setup_feedback_headers()
                
                # 嘗試重新獲取以確保連接正常
                try:
                    self.feedback_worksheet = sheet.worksheet(safe_title)
                    logger.info("重新連接 Feedback 工作表成功")
                except Exception as e:
                    logger.error(f"重新連接失敗: {e}")
                    # 備用方案：使用數字索引獲取最後一個工作表
                    worksheets = sheet.worksheets()
                    self.feedback_worksheet = worksheets[-1]
                    logger.info("使用備用方案連接到最後一個工作表")
                    
        except Exception as e:
            logger.error(f"初始化 Feedback 工作表失敗: {e}")
            self.feedback_worksheet = None
    
    def _setup_feedback_headers(self):
        """設置 Feedback 工作表標題行"""
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
            "App Version",
            "Timestamp",  # 額外的時間戳
            "Status"      # 記錄狀態
        ]
        
        try:
            # ============ 修復方案 2: 使用批量更新替代 append_row ============
            # 根據搜索結果，使用 update 方法更可靠
            self.feedback_worksheet.update('A1', [headers])
            
            # 格式化標題行
            self._format_header_row(self.feedback_worksheet, len(headers))
            
            logger.info(f"Feedback 工作表標題行設置完成，共 {len(headers)} 列")
            
        except Exception as e:
            logger.error(f"設置 Feedback 標題行失敗: {e}")
    
    def _initialize_usage_headers(self):
        """初始化 UsageLog 工作表標題行"""
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
            self.usage_worksheet.update('A1', [headers])
            self._format_header_row(self.usage_worksheet, len(headers))
            logger.info("UsageLog 工作表標題行初始化完成")
        except Exception as e:
            logger.error(f"初始化 UsageLog 標題行失敗: {e}")
    
    def _format_header_row(self, worksheet, col_count: int):
        """格式化標題行"""
        try:
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
        """記錄使用情況到 UsageLog"""
        try:
            if not self.initialized:
                if not self._initialize_client():
                    return False
            
            if not self.usage_worksheet:
                logger.error("UsageLog 工作表不可用")
                return False
            
            current_datetime = self._get_sydney_datetime()
            session_id = self._get_session_id()
            user_id = kwargs.get('session_id', self._create_user_id())
            
            row_data = [
                current_datetime,
                kwargs.get('language', ''),
                kwargs.get('report_length', 0),
                kwargs.get('file_type', 'manual'),
                session_id,
                user_id,
                kwargs.get('processing_status', 'unknown'),
                kwargs.get('latency_ms', 0),
                kwargs.get('translation_id', ''),
                kwargs.get('medical_terms_count', 0),
                kwargs.get('confidence_score', 0),
                kwargs.get('app_version', 'unknown')
            ]
            
            # 使用 append_row 記錄到 UsageLog（這個一直工作正常）
            self.usage_worksheet.append_row(row_data)
            
            logger.info(f"UsageLog 記錄成功: {kwargs.get('language')}, {kwargs.get('processing_status')}")
            return True
            
        except Exception as e:
            logger.error(f"記錄到 UsageLog 失敗: {e}")
            return False
    
    def log_feedback(self, **kwargs) -> bool:
        """記錄回饋到 Feedback 工作表（終極修復版）"""
        try:
            if not self.initialized:
                if not self._initialize_client():
                    logger.error("無法初始化 Google Sheets 客戶端")
                    return False
            
            if not self.feedback_worksheet:
                logger.error("Feedback 工作表不可用")
                return False
            
            # ============ 數據準備和驗證 ============
            current_datetime = self._get_sydney_datetime()
            session_id = self._get_session_id()
            user_id = kwargs.get('session_id', self._create_user_id())
            
            # 確保所有數據都是有效的類型
            def safe_convert(value, default_value=""):
                """安全轉換數據類型"""
                if value is None:
                    return default_value
                if isinstance(value, (int, float)):
                    return value
                if isinstance(value, str):
                    # 清理字符串，移除可能導致問題的字符
                    cleaned = value.replace('\n', ' ').replace('\r', ' ').strip()
                    return cleaned[:500]  # 限制長度
                return str(value)[:500]
            
            row_data = [
                current_datetime,                                           # Date & Time
                safe_convert(kwargs.get('translation_id', '')),           # Translation ID
                safe_convert(kwargs.get('language', '')),                 # Language
                safe_convert(kwargs.get('feedback_type', 'unknown')),     # Feedback Type
                safe_convert(kwargs.get('sentiment', '')),                # Sentiment
                safe_convert(kwargs.get('clarity_score', 0), 0),         # Clarity Score
                safe_convert(kwargs.get('usefulness_score', 0), 0),      # Usefulness Score
                safe_convert(kwargs.get('accuracy_score', 0), 0),        # Accuracy Score
                safe_convert(kwargs.get('recommendation_score', 0), 0),   # Recommendation Score
                safe_convert(kwargs.get('overall_satisfaction', 0), 0.0), # Overall Satisfaction
                safe_convert(kwargs.get('issues', '')),                   # Issues
                safe_convert(kwargs.get('suggestion', '')),               # Suggestion
                safe_convert(kwargs.get('email', '')),                    # Email
                safe_convert(kwargs.get('report_length', 0), 0),         # Report Length
                safe_convert(kwargs.get('file_type', 'manual')),         # File Type
                safe_convert(kwargs.get('medical_terms_detected', 0), 0), # Medical Terms Count
                safe_convert(kwargs.get('confidence_score', 0), 0.0),    # Confidence Score
                session_id,                                               # Session ID
                user_id,                                                  # User ID
                safe_convert(kwargs.get('app_version', 'unknown')),      # App Version
                int(time.time()),                                        # Timestamp
                "submitted"                                               # Status
            ]
            
            # ============ 修復方案 3: 多種寫入方法嘗試 ============
            
            # 方法 1: 使用 append_row
            try:
                logger.info("嘗試使用 append_row 寫入 Feedback...")
                self.feedback_worksheet.append_row(row_data)
                logger.info("✅ append_row 寫入成功")
                
                # 驗證寫入是否成功
                time.sleep(2)  # 等待寫入完成
                if self._verify_feedback_written(kwargs.get('translation_id', '')):
                    logger.info("✅ Feedback 寫入驗證成功")
                    return True
                else:
                    logger.warning("⚠️ append_row 寫入後驗證失敗，嘗試其他方法")
                    
            except Exception as e:
                logger.warning(f"append_row 方法失敗: {e}")
            
            # 方法 2: 使用 values_append (更可靠的 API)
            try:
                logger.info("嘗試使用 values_append 寫入 Feedback...")
                
                # 獲取工作表名稱
                worksheet_title = self.feedback_worksheet.title
                
                # 使用 values_append API
                body = {
                    'values': [row_data],
                    'majorDimension': 'ROWS'
                }
                
                result = self.client.open_by_key(self.sheet_id).values_append(
                    worksheet_title, 
                    {'valueInputOption': 'RAW'}, 
                    body
                )
                
                logger.info("✅ values_append 寫入成功")
                
                # 驗證寫入
                time.sleep(2)
                if self._verify_feedback_written(kwargs.get('translation_id', '')):
                    logger.info("✅ values_append 寫入驗證成功")
                    return True
                else:
                    logger.warning("⚠️ values_append 寫入後驗證失敗")
                    
            except Exception as e:
                logger.warning(f"values_append 方法失敗: {e}")
            
            # 方法 3: 使用 update 到指定行
            try:
                logger.info("嘗試使用 update 方法寫入 Feedback...")
                
                # 找到下一個空行
                all_values = self.feedback_worksheet.get_all_values()
                next_row = len(all_values) + 1
                
                # 使用 update 方法
                range_name = f"A{next_row}"
                self.feedback_worksheet.update(range_name, [row_data])
                
                logger.info(f"✅ update 方法寫入成功到行 {next_row}")
                
                # 驗證寫入
                time.sleep(2)
                if self._verify_feedback_written(kwargs.get('translation_id', '')):
                    logger.info("✅ update 方法寫入驗證成功")
                    return True
                else:
                    logger.warning("⚠️ update 方法寫入後驗證失敗")
                    
            except Exception as e:
                logger.warning(f"update 方法失敗: {e}")
            
            # 方法 4: 批量更新方法
            try:
                logger.info("嘗試使用批量更新寫入 Feedback...")
                
                # 獲取當前所有數據
                existing_data = self.feedback_worksheet.get_all_values()
                
                # 添加新行
                updated_data = existing_data + [row_data]
                
                # 清空工作表並重新寫入
                self.feedback_worksheet.clear()
                time.sleep(1)
                
                # 批量更新
                self.feedback_worksheet.update('A1', updated_data)
                
                logger.info("✅ 批量更新方法寫入成功")
                
                # 驗證寫入
                time.sleep(3)
                if self._verify_feedback_written(kwargs.get('translation_id', '')):
                    logger.info("✅ 批量更新寫入驗證成功")
                    return True
                else:
                    logger.warning("⚠️ 批量更新寫入後驗證失敗")
                    
            except Exception as e:
                logger.warning(f"批量更新方法失敗: {e}")
            
            # 所有方法都失敗
            logger.error("❌ 所有寫入方法都失敗了")
            return False
            
        except Exception as e:
            logger.error(f"記錄 Feedback 時發生嚴重錯誤: {e}")
            return False
    
    def _verify_feedback_written(self, translation_id: str) -> bool:
        """驗證 Feedback 是否成功寫入"""
        try:
            if not translation_id:
                return False
            
            # 獲取最近的記錄檢查
            all_records = self.feedback_worksheet.get_all_records()
            
            # 檢查最後幾行是否包含我們的 translation_id
            for record in reversed(all_records[-5:]):  # 檢查最後5行
                if record.get('Translation ID') == translation_id:
                    logger.info(f"找到 translation_id {translation_id} 的記錄")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"驗證 Feedback 寫入失敗: {e}")
            return False
    
    def get_feedback_worksheet_info(self) -> Dict[str, Any]:
        """獲取 Feedback 工作表信息（用於診斷）"""
        try:
            if not self.feedback_worksheet:
                return {"error": "Feedback 工作表不可用"}
            
            info = {
                "title": self.feedback_worksheet.title,
                "id": self.feedback_worksheet.id,
                "row_count": self.feedback_worksheet.row_count,
                "col_count": self.feedback_worksheet.col_count,
                "url": self.feedback_worksheet.url
            }
            
            # 獲取標題行
            try:
                headers = self.feedback_worksheet.row_values(1)
                info["headers"] = headers
                info["header_count"] = len(headers)
            except Exception as e:
                info["headers_error"] = str(e)
            
            # 獲取數據行數
            try:
                all_values = self.feedback_worksheet.get_all_values()
                info["actual_rows"] = len(all_values)
                info["data_rows"] = len(all_values) - 1 if all_values else 0
            except Exception as e:
                info["data_error"] = str(e)
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def diagnose_feedback_sheet(self) -> Dict[str, Any]:
        """診斷 Feedback 工作表問題"""
        diagnosis = {
            "timestamp": self._get_sydney_datetime(),
            "client_initialized": bool(self.client),
            "worksheet_available": bool(self.feedback_worksheet),
        }
        
        if self.feedback_worksheet:
            diagnosis.update(self.get_feedback_worksheet_info())
            
            # 測試寫入權限
            try:
                test_range = "Z1000"  # 使用遠離數據的位置
                self.feedback_worksheet.update(test_range, [["test"]])
                self.feedback_worksheet.update(test_range, [[""]])  # 清除測試數據
                diagnosis["write_permission"] = True
            except Exception as e:
                diagnosis["write_permission"] = False
                diagnosis["write_error"] = str(e)
        
        return diagnosis

# 全局實例
_sheets_logger = GoogleSheetsLogger()

def log_to_google_sheets(**kwargs) -> bool:
    """統一的記錄函數"""
    processing_status = kwargs.get('processing_status', '')
    
    if processing_status == 'feedback':
        return log_feedback_to_sheets(**kwargs)
    else:
        return log_usage_to_sheets(**kwargs)

def log_usage_to_sheets(**kwargs) -> bool:
    """記錄使用情況到 UsageLog"""
    return _sheets_logger.log_usage(**kwargs)

def log_feedback_to_sheets(**kwargs) -> bool:
    """記錄回饋到 Feedback 工作表（終極修復版）"""
    success = _sheets_logger.log_feedback(**kwargs)
    
    # 如果失敗，記錄診斷信息
    if not success:
        diagnosis = _sheets_logger.diagnose_feedback_sheet()
        logger.error(f"Feedback 寫入失敗，診斷信息: {diagnosis}")
    
    return success

def get_session_id() -> str:
    """獲取當前會話ID"""
    return _sheets_logger._get_session_id()

def reset_session() -> None:
    """重置會話ID"""
    _sheets_logger._session_id = None
    logger.info("會話ID已重置")

def diagnose_feedback_system() -> Dict[str, Any]:
    """診斷整個 Feedback 系統"""
    return _sheets_logger.diagnose_feedback_sheet()

def get_feedback_worksheet_info() -> Dict[str, Any]:
    """獲取 Feedback 工作表詳細信息"""
    return _sheets_logger.get_feedback_worksheet_info()

# 測試函數
def test_feedback_logging_ultimate() -> Dict[str, Any]:
    """終極 Feedback 記錄測試"""
    test_results = {
        "test_time": datetime.now().isoformat(),
        "results": []
    }
    
    # 測試數據
    test_cases = [
        {
            "name": "基本測試",
            "data": {
                'translation_id': f'ultimate_test_{int(time.time())}',
                'language': '简体中文',
                'feedback_type': 'test',
                'sentiment': 'positive',
                'clarity_score': 5,
                'usefulness_score': 5,
                'accuracy_score': 5,
                'recommendation_score': 10,
                'overall_satisfaction': 5.0,
                'issues': '測試問題',
                'suggestion': '測試建議',
                'email': 'test@ultimate.com',
                'report_length': 1000,
                'file_type': 'test',
                'medical_terms_detected': 5,
                'confidence_score': 0.85,
                'app_version': 'v4.2-ultimate-test'
            }
        },
        {
            "name": "空值測試",
            "data": {
                'translation_id': f'null_test_{int(time.time())}',
                'language': '',
                'feedback_type': None,
                'sentiment': '',
                'clarity_score': None,
                'issues': None,
                'suggestion': '',
                'email': None,
                'app_version': 'v4.2-null-test'
            }
        },
        {
            "name": "特殊字符測試",
            "data": {
                'translation_id': f'special_test_{int(time.time())}',
                'language': '繁體中文',
                'feedback_type': 'special_chars',
                'issues': '測試\n換行\r回車\t製表符',
                'suggestion': '特殊字符：@#$%^&*()',
                'email': 'test+special@email.com',
                'app_version': 'v4.2-special-test'
            }
        }
    ]
    
    for test_case in test_cases:
        try:
            logger.info(f"執行測試: {test_case['name']}")
            success = log_feedback_to_sheets(**test_case['data'])
            
            result = {
                "test_name": test_case['name'],
                "success": success,
                "translation_id": test_case['data']['translation_id']
            }
            
            if success:
                logger.info(f"✅ {test_case['name']} 成功")
            else:
                logger.error(f"❌ {test_case['name']} 失敗")
                
            test_results["results"].append(result)
            
        except Exception as e:
            logger.error(f"測試 {test_case['name']} 時發生異常: {e}")
            test_results["results"].append({
                "test_name": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    return test_results

if __name__ == "__main__":
    # 運行終極測試
    print("🚀 開始終極 Feedback 測試...")
    results = test_feedback_logging_ultimate()
    
    print("\n📊 測試結果:")
    for result in results["results"]:
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {result['test_name']}: {result.get('translation_id', 'N/A')}")
        if not result.get("success") and "error" in result:
            print(f"   錯誤: {result['error']}")
    
    print("\n🔍 診斷信息:")
    diagnosis = diagnose_feedback_system()
    for key, value in diagnosis.items():
        print(f"{key}: {value}")
