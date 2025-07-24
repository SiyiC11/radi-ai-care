"""
RadiAI.Care - 完整的 Google Sheets 数据管理系统（悉尼时间版）
整合使用量追踪、反馈收集、数据分析的统一管理平台
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
    """获取悉尼时区的当前时间"""
    sydney_tz = pytz.timezone('Australia/Sydney')
    return datetime.now(sydney_tz)

def _get_utc_time() -> datetime:
    """获取UTC时间"""
    return datetime.now(timezone.utc)

class GoogleSheetsManager:
    """Google Sheets 统一管理器（悉尼时间版）"""
    
    # 工作表定义 - 更新时间戳列名
    WORKSHEETS_CONFIG = {
        'UsageLog': {
            'headers': [
                'Timestamp (Sydney)', 'Sydney Date', 'User ID', 'Session ID', 
                'Translation ID', 'Daily Count', 'Session Count', 
                'Processing Time (ms)', 'File Type', 'Content Length',
                'Status', 'Language', 'Device Info', 'IP Hash', 'User Agent',
                'Error Message', 'AI Model', 'API Cost', 'Extra Data'
            ],
            'description': '用户使用记录和系统性能数据（悉尼时间）'
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
            'description': '用户反馈和满意度调查数据（悉尼时间）'
        },
        'Analytics': {
            'headers': [
                'Date', 'Total Users', 'Total Translations', 'Unique Users',
                'Avg Satisfaction', 'Avg Quality Rating', 'Avg Processing Time',
                'Most Common Issues', 'Feature Request Frequency',
                'User Retention Rate', 'Error Rate', 'Peak Usage Hours',
                'Device Distribution', 'Language Distribution', 'Conversion Rate'
            ],
            'description': '每日分析汇总数据'
        },
        'UserProfiles': {
            'headers': [
                'User ID', 'First Seen', 'Last Seen', 'Total Translations',
                'Avg Satisfaction', 'Preferred Language', 'Primary Device',
                'Usage Pattern', 'Feedback Count', 'Issues Reported',
                'Feature Requests', 'User Segment', 'Churn Risk',
                'Lifetime Value', 'Referral Source'
            ],
            'description': '用户画像和行为分析'
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
        """初始化 Google Sheets 连接"""
        try:
            # 从 Streamlit secrets 获取凭据
            secret_b64 = st.secrets.get("GOOGLE_SHEET_SECRET_B64", "")
            if not secret_b64:
                # 备用：从环境变量获取
                secret_b64 = os.getenv("GOOGLE_SHEET_SECRET_B64", "")
            
            if not secret_b64:
                raise ValueError("Google Sheets credentials not found in secrets or environment")
            
            # 解码凭据
            try:
                creds_json = base64.b64decode(secret_b64).decode('utf-8')
                creds_dict = json.loads(creds_json)
            except Exception as e:
                raise ValueError(f"Invalid Google Sheets credentials format: {e}")
            
            # 创建认证对象
            credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=SCOPES
            )
            
            # 初始化客户端
            self.client = gspread.authorize(credentials)
            
            # 打开或创建工作簿
            try:
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                logger.info(f"Successfully opened existing spreadsheet: {self.sheet_id}")
            except gspread.SpreadsheetNotFound:
                # 如果工作簿不存在，尝试创建（需要Drive权限）
                logger.warning(f"Spreadsheet {self.sheet_id} not found or no access")
                raise
            
            # 初始化所有工作表
            self._setup_worksheets()
            
            logger.info("Google Sheets Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets connection: {e}")
            raise
    
    def _setup_worksheets(self):
        """设置所有必需的工作表"""
        for sheet_name, config in self.WORKSHEETS_CONFIG.items():
            try:
                # 尝试获取现有工作表
                worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"Found existing worksheet: {sheet_name}")
                
                # 检查并更新表头（如果需要）
                self._update_headers_if_needed(worksheet, config['headers'], sheet_name)
                
            except gspread.WorksheetNotFound:
                # 创建新工作表
                logger.info(f"Creating new worksheet: {sheet_name}")
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(config['headers'])
                )
                
                # 设置表头
                worksheet.update('A1', [config['headers']])
                
                # 设置表头格式（加粗）
                worksheet.format('A1:Z1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
                
                logger.info(f"Created worksheet {sheet_name} with {len(config['headers'])} columns")
            
            self.worksheets[sheet_name] = worksheet
    
    def _update_headers_if_needed(self, worksheet, expected_headers: List[str], sheet_name: str):
        """检查并更新表头（如果需要从UTC改为Sydney时间）"""
        try:
            existing_headers = worksheet.row_values(1)
            
            # 检查是否需要更新时间戳列
            needs_update = False
            updated_headers = existing_headers.copy()
            
            if len(existing_headers) > 0:
                # 检查第一列是否是UTC时间戳
                if existing_headers[0] == 'Timestamp (UTC)':
                    updated_headers[0] = 'Timestamp (Sydney)'
                    needs_update = True
                    logger.info(f"Updating {sheet_name} timestamp header from UTC to Sydney")
            
            # 如果表头不完整或不匹配，使用期望的表头
            if len(existing_headers) != len(expected_headers):
                updated_headers = expected_headers
                needs_update = True
                logger.info(f"Updating {sheet_name} headers to match expected format")
            
            if needs_update:
                worksheet.update('A1', [updated_headers])
                logger.info(f"Updated headers for {sheet_name}")
                
        except Exception as e:
            logger.warning(f"Failed to update headers for {sheet_name}: {e}")
    
    def log_usage(self, usage_data: Dict[str, Any]) -> bool:
        """记录使用数据（使用悉尼时间）"""
        try:
            worksheet = self.worksheets['UsageLog']
            
            # 获取悉尼时间
            sydney_time = _get_sydney_time()
            
            # 构建数据行 - 使用悉尼时间作为主时间戳
            row_data = [
                sydney_time.isoformat(),  # Timestamp (Sydney) - 修改点1
                sydney_time.strftime('%Y-%m-%d'),  # Sydney Date
                usage_data.get('user_id', ''),
                usage_data.get('session_id', ''),
                usage_data.get('translation_id', ''),
                usage_data.get('daily_count', 0),
                usage_data.get('session_count', 0),
                usage_data.get('processing_time_ms', 0),
                usage_data.get('file_type', 'text'),
                usage_data.get('content_length', 0),
                usage_data.get('status', 'success'),  # success/failed/timeout
                usage_data.get('language', 'zh_CN'),
                usage_data.get('device_info', ''),
                usage_data.get('ip_hash', ''),
                usage_data.get('user_agent', ''),
                usage_data.get('error_message', ''),
                usage_data.get('ai_model', 'gpt-4o-mini'),
                usage_data.get('api_cost', 0),
                json.dumps(usage_data.get('extra_data', {}), ensure_ascii=False)
            ]
            
            # 插入数据
            worksheet.append_row(row_data, value_input_option='RAW')
            logger.debug(f"Logged usage data for translation: {usage_data.get('translation_id')} at Sydney time: {sydney_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log usage data: {e}")
            return False
    
    def log_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """记录反馈数据（使用悉尼时间）"""
        try:
            worksheet = self.worksheets['Feedback']
            
            # 获取悉尼时间
            sydney_time = _get_sydney_time()
            
            # 构建反馈数据行 - 使用悉尼时间作为主时间戳
            row_data = [
                sydney_time.isoformat(),  # Timestamp (Sydney) - 修改点2
                sydney_time.strftime('%Y-%m-%d'),  # Sydney Date
                feedback_data.get('translation_id', ''),
                feedback_data.get('user_id', ''),
                feedback_data.get('overall_satisfaction', 0),  # 1-5
                feedback_data.get('translation_quality', 0),   # 1-5
                feedback_data.get('speed_rating', 0),          # 1-5
                feedback_data.get('ease_of_use', 0),           # 1-5
                feedback_data.get('feature_completeness', 0),  # 1-5
                feedback_data.get('likelihood_to_recommend', 0), # 1-5
                feedback_data.get('primary_use_case', ''),
                feedback_data.get('user_type', ''),  # patient/family/professional/student
                ','.join(feedback_data.get('improvement_areas', [])),
                ','.join(feedback_data.get('specific_issues', [])),
                ','.join(feedback_data.get('feature_requests', [])),
                feedback_data.get('detailed_comments', ''),
                feedback_data.get('contact_email', ''),
                feedback_data.get('follow_up_consent', False),
                feedback_data.get('device_info', ''),
                feedback_data.get('language', 'zh_CN'),
                feedback_data.get('usage_frequency', ''),  # first-time/occasional/regular
                feedback_data.get('comparison_rating', 0),  # vs other tools
                json.dumps(feedback_data.get('extra_metadata', {}), ensure_ascii=False)
            ]
            
            worksheet.append_row(row_data, value_input_option='RAW')
            logger.info(f"Logged feedback for translation: {feedback_data.get('translation_id')} at Sydney time: {sydney_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log feedback: {e}")
            return False
    
    def get_user_usage_count(self, user_id: str, date: str = None) -> int:
        """获取用户的使用次数"""
        try:
            worksheet = self.worksheets['UsageLog']
            
            if date is None:
                date = _get_sydney_time().strftime('%Y-%m-%d')
            
            # 获取所有记录
            records = worksheet.get_all_records()
            
            # 过滤当日成功的翻译记录
            count = 0
            for record in records:
                if (record.get('User ID') == user_id and 
                    record.get('Sydney Date') == date and 
                    record.get('Status') == 'success'):
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get user usage count: {e}")
            return 0
    
    def get_daily_analytics(self, date: str = None) -> Dict[str, Any]:
        """获取每日分析数据"""
        try:
            if date is None:
                date = _get_sydney_time().strftime('%Y-%m-%d')
            
            usage_worksheet = self.worksheets['UsageLog']
            feedback_worksheet = self.worksheets['Feedback']
            
            # 获取使用数据
            usage_records = usage_worksheet.get_all_records()
            daily_usage = [r for r in usage_records if r.get('Sydney Date') == date]
            
            # 获取反馈数据
            feedback_records = feedback_worksheet.get_all_records()
            daily_feedback = [r for r in feedback_records if r.get('Sydney Date') == date]
            
            # 计算分析指标
            analytics = {
                'date': date,
                'total_translations': len([r for r in daily_usage if r.get('Status') == 'success']),
                'unique_users': len(set(r.get('User ID', '') for r in daily_usage)),
                'avg_processing_time': self._calculate_avg([r.get('Processing Time (ms)', 0) for r in daily_usage]),
                'error_rate': len([r for r in daily_usage if r.get('Status') != 'success']) / max(len(daily_usage), 1),
                'feedback_count': len(daily_feedback),
                'avg_satisfaction': self._calculate_avg([r.get('Overall Satisfaction', 0) for r in daily_feedback]),
                'avg_quality_rating': self._calculate_avg([r.get('Translation Quality', 0) for r in daily_feedback]),
                'language_distribution': self._get_distribution(daily_usage, 'Language'),
                'device_distribution': self._get_distribution(daily_usage, 'Device Info'),
                'common_issues': self._get_common_issues(daily_feedback)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get daily analytics: {e}")
            return {}
    
    def _calculate_avg(self, values: List[float]) -> float:
        """计算平均值"""
        valid_values = [v for v in values if v and v > 0]
        return sum(valid_values) / len(valid_values) if valid_values else 0
    
    def _get_distribution(self, records: List[Dict], field: str) -> Dict[str, int]:
        """获取字段值分布"""
        distribution = {}
        for record in records:
            value = record.get(field, 'unknown')
            distribution[value] = distribution.get(value, 0) + 1
        return distribution
    
    def _get_common_issues(self, feedback_records: List[Dict]) -> Dict[str, int]:
        """获取常见问题统计"""
        issues = {}
        for record in feedback_records:
            specific_issues = record.get('Specific Issues', '')
            if specific_issues:
                for issue in specific_issues.split(','):
                    issue = issue.strip()
                    if issue:
                        issues[issue] = issues.get(issue, 0) + 1
        return dict(sorted(issues.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def update_user_profile(self, user_id: str) -> bool:
        """更新用户画像"""
        try:
            # 这里实现用户画像更新逻辑
            # 基于用户的使用和反馈历史计算用户特征
            pass
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接状态"""
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
            
            # 测试每个工作表
            for name, worksheet in self.worksheets.items():
                try:
                    # 尝试读取表头
                    headers = worksheet.row_values(1)
                    result['worksheets'][name] = {
                        'accessible': True,
                        'header_count': len(headers),
                        'row_count': worksheet.row_count,
                        'first_header': headers[0] if headers else 'None',
                        'uses_sydney_time': headers[0] == 'Timestamp (Sydney)' if headers else False
                    }
                except Exception as e:
                    result['worksheets'][name] = {
                        'accessible': False,
                        'error': str(e)
                    }
            
            result['connected'] = True
            logger.info("Google Sheets connection test passed (Sydney timezone)")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Google Sheets connection test failed: {e}")
        
        return result

# 测试函数
def test_sydney_time_functionality():
    """测试悉尼时间功能"""
    print("=== 测试悉尼时间功能 ===")
    
    # 测试时间获取函数
    sydney_time = _get_sydney_time()
    utc_time = _get_utc_time()
    
    print(f"悉尼时间: {sydney_time.isoformat()}")
    print(f"UTC时间: {utc_time.isoformat()}")
    print(f"时区信息: {sydney_time.tzinfo}")
    
    # 测试时间格式
    print(f"悉尼日期: {sydney_time.strftime('%Y-%m-%d')}")
    print(f"悉尼时间戳: {sydney_time.isoformat()}")
    
    # 测试工作表配置
    config = GoogleSheetsManager.WORKSHEETS_CONFIG
    for sheet_name, sheet_config in config.items():
        headers = sheet_config['headers']
        print(f"\n{sheet_name} 表头:")
        print(f"  第一列: {headers[0]}")
        print(f"  第二列: {headers[1]}")
        print(f"  是否使用悉尼时间: {'是' if 'Sydney' in headers[0] else '否'}")
    
    return True

if __name__ == "__main__":
    # 运行测试
    test_sydney_time_functionality()
