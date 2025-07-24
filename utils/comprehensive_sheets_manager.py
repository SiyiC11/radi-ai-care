"""
RadiAI.Care - 更新的 Google Sheets 數據管理系統（支持反饋功能）
在 UsageLog 表中添加用戶反饋功能
"""

import base64
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st
import pytz

try:
    import gspread
    from google.oauth2.service_account import Credentials
    SHEETS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Google Sheets dependencies not available: {e}")
    SHEETS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Google Sheets API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

def _get_sydney_time() -> datetime:
    """獲取悉尼時區的當前時間"""
    sydney_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(sydney_tz)

def _get_utc_time() -> datetime:
    """獲取UTC時間"""
    return datetime.now(timezone.utc)

class GoogleSheetsManager:
    """Google Sheets 統一管理器（支持反饋功能）"""
    
    # 更新的工作表定義 - 在 UsageLog 中添加反饋列
    WORKSHEETS_CONFIG = {
        'UsageLog': {
            'headers': [
                'Timestamp (Sydney)', 'Sydney Date', 'User ID', 'Session ID', 
                'Translation ID', 'Daily Count', 'Session Count', 
                'Processing Time (ms)', 'File Type', 'Content Length',
                'Status', 'Language', 'Device Info', 'IP Hash', 'User Agent',
                'Error Message', 'AI Model', 'API Cost', 'Extra Data',
                'User Name', 'User Feedback'  # 新增的反饋列
            ],
            'description': '用戶使用記錄、系統性能數據和用戶反饋（悉尼時間）'
        },
        'Feedback': {
            'headers': [
                'Timestamp (Sydney)', 'Sydney Date', 'Translation ID', 'User ID',
                'Overall Satisfaction', 'Translation Quality', 'Speed Rating',
                'Ease of Use', 'Feature Completeness', 'Likelihood to Recommend',
                'Primary Use Case', 'User Type', 'Improvement Areas',
                'Specific Issues', 'Feature Requests', 'Detailed Comments',
                'Contact Email', 'Follow-up Consent', 'Device Info', 'Language',
                'Usage Frequency', 'Comparison Rating', 'Extra Metadata'
            ],
            'description': '詳細用戶反饋和滿意度調查數據（悉尼時間）'
        },
        'Analytics': {
            'headers': [
                'Date', 'Total Users', 'Total Translations', 'Unique Users',
                'Avg Satisfaction', 'Avg Quality Rating', 'Avg Processing Time',
                'Most Common Issues', 'Feature Request Frequency',
                'User Retention Rate', 'Error Rate', 'Peak Usage Hours',
                'Device Distribution', 'Language Distribution', 'Conversion Rate'
            ],
            'description': '每日分析匯總數據'
        },
        'UserProfiles': {
            'headers': [
                'User ID', 'First Seen', 'Last Seen', 'Total Translations',
                'Avg Satisfaction', 'Preferred Language', 'Primary Device',
                'Usage Pattern', 'Feedback Count', 'Issues Reported',
                'Feature Requests', 'User Segment', 'Churn Risk',
                'Lifetime Value', 'Referral Source'
            ],
            'description': '用戶畫像和行為分析'
        }
    }
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.client = None
        self.spreadsheet = None
        self.worksheets = {}
        self.sydney_tz = pytz.timezone('Australia/Sydney')
        
        if SHEETS_AVAILABLE:
            self._initialize_connection()
        else:
            logger.error("Google Sheets dependencies not available")
            raise ImportError("Required packages: gspread, google-auth")
    
    def _initialize_connection(self):
        """初始化 Google Sheets 連接"""
        try:
            # 從 Streamlit secrets 獲取憑據
            secret_b64 = st.secrets.get("GOOGLE_SHEET_SECRET_B64", "")
            if not secret_b64:
                # 備用：從環境變數獲取
                secret_b64 = os.getenv("GOOGLE_SHEET_SECRET_B64", "")
            
            if not secret_b64:
                raise ValueError("Google Sheets credentials not found in secrets or environment")
            
            # 解碼憑據
            try:
                creds_json = base64.b64decode(secret_b64).decode('utf-8')
                creds_dict = json.loads(creds_json)
            except Exception as e:
                raise ValueError(f"Invalid Google Sheets credentials format: {e}")
            
            # 創建認證對象
            credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=SCOPES
            )
            
            # 初始化客戶端
            self.client = gspread.authorize(credentials)
            
            # 打開或創建工作簿
            try:
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                logger.info(f"Successfully opened existing spreadsheet: {self.sheet_id}")
            except gspread.SpreadsheetNotFound:
                logger.warning(f"Spreadsheet {self.sheet_id} not found or no access")
                raise
            
            # 初始化所有工作表
            self._setup_worksheets()
            
            logger.info("Google Sheets Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets connection: {e}")
            raise
    
    def _setup_worksheets(self):
        """設置所有必需的工作表"""
        for sheet_name, config in self.WORKSHEETS_CONFIG.items():
            try:
                # 嘗試獲取現有工作表
                worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"Found existing worksheet: {sheet_name}")
                
                # 檢查並更新表頭（如果需要）
                self._update_headers_if_needed(worksheet, config['headers'], sheet_name)
                
            except gspread.WorksheetNotFound:
                # 創建新工作表
                logger.info(f"Creating new worksheet: {sheet_name}")
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(config['headers'])
                )
                
                # 設置表頭
                worksheet.update('A1', [config['headers']])
                
                # 設置表頭格式（加粗）
                worksheet.format('A1:Z1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
                
                logger.info(f"Created worksheet {sheet_name} with {len(config['headers'])} columns")
            
            self.worksheets[sheet_name] = worksheet
    
    def _update_headers_if_needed(self, worksheet, expected_headers: List[str], sheet_name: str):
        """檢查並更新表頭（支持添加新的反饋列）"""
        try:
            existing_headers = worksheet.row_values(1)
            
            # 檢查是否需要更新
            needs_update = False
            updated_headers = existing_headers.copy()
            
            # 檢查長度是否匹配
            if len(existing_headers) != len(expected_headers):
                logger.info(f"Headers length mismatch in {sheet_name}: {len(existing_headers)} vs {len(expected_headers)}")
                
                # 如果是 UsageLog 表且缺少反饋列，則添加
                if sheet_name == 'UsageLog' and len(existing_headers) == 19 and len(expected_headers) == 21:
                    # 原來有19列，現在需要21列（添加 User Name 和 User Feedback）
                    updated_headers = expected_headers
                    needs_update = True
                    logger.info(f"Adding feedback columns to {sheet_name}")
                else:
                    # 其他情況直接使用期望的表頭
                    updated_headers = expected_headers
                    needs_update = True
            
            # 檢查時間戳列名是否需要更新
            if len(existing_headers) > 0 and existing_headers[0] == 'Timestamp (UTC)':
                updated_headers[0] = 'Timestamp (Sydney)'
                needs_update = True
                logger.info(f"Updating {sheet_name} timestamp header from UTC to Sydney")
            
            if needs_update:
                worksheet.update('A1', [updated_headers])
                logger.info(f"Updated headers for {sheet_name}")
                
        except Exception as e:
            logger.warning(f"Failed to update headers for {sheet_name}: {e}")
    
    def log_usage(self, usage_data: Dict[str, Any]) -> bool:
        """記錄使用數據（使用悉尼時間）"""
        try:
            worksheet = self.worksheets['UsageLog']
            
            # 獲取悉尼時間
            sydney_time = _get_sydney_time()
            
            # 構建數據行 - 現在包含反饋列
            row_data = [
                sydney_time.isoformat(),  # Timestamp (Sydney)
                sydney_time.strftime('%Y-%m-%d'),  # Sydney Date
                usage_data.get('user_id', ''),
                usage_data.get('session_id', ''),
                usage_data.get('translation_id', ''),
                usage_data.get('daily_count', 0),
                usage_data.get('session_count', 0),
                usage_data.get('processing_time_ms', 0),
                usage_data.get('file_type', 'text'),
                usage_data.get('content_length', 0),
                usage_data.get('status', 'success'),
                usage_data.get('language', 'zh_CN'),
                usage_data.get('device_info', ''),
                usage_data.get('ip_hash', ''),
                usage_data.get('user_agent', ''),
                usage_data.get('error_message', ''),
                usage_data.get('ai_model', 'gpt-4o-mini'),
                usage_data.get('api_cost', 0),
                json.dumps(usage_data.get('extra_data', {}), ensure_ascii=False),
                usage_data.get('user_name', ''),  # 新增：用戶姓名
                usage_data.get('user_feedback', '')  # 新增：用戶反饋
            ]
            
            # 插入數據
            worksheet.append_row(row_data, value_input_option='RAW')
            logger.debug(f"Logged usage data for translation: {usage_data.get('translation_id')} at Sydney time: {sydney_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log usage data: {e}")
            return False
    
    def log_feedback_to_usage(self, feedback_data: Dict[str, Any]) -> bool:
        """專門記錄反饋到 UsageLog 表的方法"""
        try:
            worksheet = self.worksheets['UsageLog']
            
            # 獲取悉尼時間
            sydney_time = _get_sydney_time()
            
            # 構建反饋記錄 - 這是一個特殊的使用記錄，主要用於記錄反饋
            row_data = [
                sydney_time.isoformat(),  # Timestamp (Sydney)
                sydney_time.strftime('%Y-%m-%d'),  # Sydney Date
                feedback_data.get('user_id', ''),
                feedback_data.get('session_id', ''),
                feedback_data.get('translation_id', ''),
                feedback_data.get('daily_count', 0),
                feedback_data.get('session_count', 0),
                0,  # Processing Time (ms) - 反饋不需要處理時間
                'feedback',  # File Type - 標記為反饋類型
                len(feedback_data.get('user_feedback', '')),  # Content Length - 反饋文字長度
                'feedback_submitted',  # Status - 標記為反饋提交
                feedback_data.get('language', 'zh_CN'),
                feedback_data.get('device_info', ''),
                feedback_data.get('ip_hash', ''),
                feedback_data.get('user_agent', ''),
                '',  # Error Message
                'feedback_system',  # AI Model - 標記為反饋系統
                0,  # API Cost
                json.dumps(feedback_data.get('extra_data', {}), ensure_ascii=False),
                feedback_data.get('user_name', ''),  # User Name
                feedback_data.get('user_feedback', '')  # User Feedback
            ]
            
            worksheet.append_row(row_data, value_input_option='RAW')
            logger.info(f"Logged feedback to UsageLog: {feedback_data.get('translation_id')} at Sydney time: {sydney_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log feedback to UsageLog: {e}")
            return False
    
    def log_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """記錄反饋數據（保留原有的詳細反饋功能）"""
        try:
            worksheet = self.worksheets['Feedback']
            
            # 獲取悉尼時間
            sydney_time = _get_sydney_time()
            
            # 構建反饋數據行
            row_data = [
                sydney_time.isoformat(),  # Timestamp (Sydney)
                sydney_time.strftime('%Y-%m-%d'),  # Sydney Date
                feedback_data.get('translation_id', ''),
                feedback_data.get('user_id', ''),
                feedback_data.get('overall_satisfaction', 0),
                feedback_data.get('translation_quality', 0),
                feedback_data.get('speed_rating', 0),
                feedback_data.get('ease_of_use', 0),
                feedback_data.get('feature_completeness', 0),
                feedback_data.get('likelihood_to_recommend', 0),
                feedback_data.get('primary_use_case', ''),
                feedback_data.get('user_type', ''),
                ','.join(feedback_data.get('improvement_areas', [])),
                ','.join(feedback_data.get('specific_issues', [])),
                ','.join(feedback_data.get('feature_requests', [])),
                feedback_data.get('detailed_comments', ''),
                feedback_data.get('contact_email', ''),
                feedback_data.get('follow_up_consent', False),
                feedback_data.get('device_info', ''),
                feedback_data.get('language', 'zh_CN'),
                feedback_data.get('usage_frequency', ''),
                feedback_data.get('comparison_rating', 0),
                json.dumps(feedback_data.get('extra_metadata', {}), ensure_ascii=False)
            ]
            
            worksheet.append_row(row_data, value_input_option='RAW')
            logger.info(f"Logged detailed feedback: {feedback_data.get('translation_id')} at Sydney time: {sydney_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log detailed feedback: {e}")
            return False
    
    def get_user_usage_count(self, user_id: str, date: str = None) -> int:
        """獲取用戶的使用次數（不包括反饋記錄）"""
        try:
            worksheet = self.worksheets['UsageLog']
            
            if date is None:
                date = _get_sydney_time().strftime('%Y-%m-%d')
            
            # 獲取所有記錄
            records = worksheet.get_all_records()
            
            # 過濾當日成功的翻譯記錄（排除反饋記錄）
            count = 0
            for record in records:
                if (record.get('User ID') == user_id and 
                    record.get('Sydney Date') == date and 
                    record.get('Status') == 'success' and 
                    record.get('File Type') != 'feedback'):  # 排除反饋記錄
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get user usage count: {e}")
            return 0
    
    def get_daily_analytics(self, date: str = None) -> Dict[str, Any]:
        """獲取每日分析數據"""
        try:
            if date is None:
                date = _get_sydney_time().strftime('%Y-%m-%d')
            
            usage_worksheet = self.worksheets['UsageLog']
            feedback_worksheet = self.worksheets['Feedback']
            
            # 獲取使用數據（排除反饋記錄）
            usage_records = usage_worksheet.get_all_records()
            daily_usage = [r for r in usage_records if (
                r.get('Sydney Date') == date and 
                r.get('File Type') != 'feedback'  # 排除反饋記錄
            )]
            
            # 獲取當日的反饋數據（從 UsageLog 中的反饋記錄）
            daily_feedback_from_usage = [r for r in usage_records if (
                r.get('Sydney Date') == date and 
                r.get('Status') == 'feedback_submitted'
            )]
            
            # 獲取詳細反饋數據
            feedback_records = feedback_worksheet.get_all_records()
            daily_detailed_feedback = [r for r in feedback_records if r.get('Sydney Date') == date]
            
            # 計算分析指標
            analytics = {
                'date': date,
                'total_translations': len([r for r in daily_usage if r.get('Status') == 'success']),
                'unique_users': len(set(r.get('User ID', '') for r in daily_usage)),
                'avg_processing_time': self._calculate_avg([r.get('Processing Time (ms)', 0) for r in daily_usage]),
                'error_rate': len([r for r in daily_usage if r.get('Status') != 'success']) / max(len(daily_usage), 1),
                'feedback_count': len(daily_feedback_from_usage) + len(daily_detailed_feedback),
                'simple_feedback_count': len(daily_feedback_from_usage),
                'detailed_feedback_count': len(daily_detailed_feedback),
                'avg_satisfaction': self._calculate_avg([r.get('Overall Satisfaction', 0) for r in daily_detailed_feedback]),
                'avg_quality_rating': self._calculate_avg([r.get('Translation Quality', 0) for r in daily_detailed_feedback]),
                'language_distribution': self._get_distribution(daily_usage, 'Language'),
                'device_distribution': self._get_distribution(daily_usage, 'Device Info'),
                'common_issues': self._get_common_issues(daily_detailed_feedback),
                'simple_feedback_samples': [r.get('User Feedback', '') for r in daily_feedback_from_usage if r.get('User Feedback', '')][:5]
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get daily analytics: {e}")
            return {}
    
    def _calculate_avg(self, values: List[float]) -> float:
        """計算平均值"""
        valid_values = [v for v in values if v and v > 0]
        return sum(valid_values) / len(valid_values) if valid_values else 0
    
    def _get_distribution(self, records: List[Dict], field: str) -> Dict[str, int]:
        """獲取字段值分布"""
        distribution = {}
        for record in records:
            value = record.get(field, 'unknown')
            distribution[value] = distribution.get(value, 0) + 1
        return distribution
    
    def _get_common_issues(self, feedback_records: List[Dict]) -> Dict[str, int]:
        """獲取常見問題統計"""
        issues = {}
        for record in feedback_records:
            specific_issues = record.get('Specific Issues', '')
            if specific_issues:
                for issue in specific_issues.split(','):
                    issue = issue.strip()
                    if issue:
                        issues[issue] = issues.get(issue, 0) + 1
        return dict(sorted(issues.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def test_connection(self) -> Dict[str, Any]:
        """測試連接狀態"""
        result = {
            'connected': False,
            'worksheets': {},
            'error': None,
            'timezone_info': {
                'sydney_time': _get_sydney_time().isoformat(),
                'utc_time': _get_utc_time().isoformat(),
                'timezone': 'Australia/Sydney'
            }
        }
        
        try:
            if not self.client or not self.spreadsheet:
                raise Exception("Client or spreadsheet not initialized")
            
            # 測試每個工作表
            for name, worksheet in self.worksheets.items():
                try:
                    # 嘗試讀取表頭
                    headers = worksheet.row_values(1)
                    result['worksheets'][name] = {
                        'accessible': True,
                        'header_count': len(headers),
                        'row_count': worksheet.row_count,
                        'first_header': headers[0] if headers else 'None',
                        'uses_sydney_time': headers[0] == 'Timestamp (Sydney)' if headers else False,
                        'has_feedback_columns': 'User Feedback' in headers if headers else False
                    }
                except Exception as e:
                    result['worksheets'][name] = {
                        'accessible': False,
                        'error': str(e)
                    }
            
            result['connected'] = True
            logger.info("Google Sheets connection test passed (Sydney timezone with feedback support)")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Google Sheets connection test failed: {e}")
        
        return result

# 測試函數
def test_feedback_functionality():
    """測試反饋功能"""
    print("=== 測試反饋功能 ===")
    
    # 測試數據結構
    usage_config = GoogleSheetsManager.WORKSHEETS_CONFIG['UsageLog']
    headers = usage_config['headers']
    
    print(f"UsageLog 表頭數量: {len(headers)}")
    print("最後兩列（反饋相關）:")
    print(f"  {len(headers)-1}. {headers[-2]}")
    print(f"  {len(headers)}. {headers[-1]}")
    
    # 測試反饋數據格式
    test_feedback_data = {
        'user_id': 'test_user_123',
        'session_id': 'session_456',
        'translation_id': 'trans_789',
        'user_name': '測試用戶',
        'user_feedback': '希望翻譯速度可以更快一些，整體體驗不錯！',
        'language': 'zh_CN',
        'device_info': 'web_browser'
    }
    
    print("\n測試反饋數據格式:")
    for key, value in test_feedback_data.items():
        print(f"  {key}: {value}")
    
    return True

if __name__ == "__main__":
    test_feedback_functionality()
