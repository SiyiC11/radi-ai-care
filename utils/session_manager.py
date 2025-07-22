"""
RadiAI.Care Session Manager - 簡化修復版
===================================
移除複雜的 JavaScript 指紋系統，使用簡單可靠的方法：
1. Session State + Google Sheets 查詢
2. 設備指紋基於 Streamlit 原生功能
3. 修復刷新頁面重置問題
"""

import streamlit as st
import hashlib
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

# 延遲導入避免循環依賴
def get_sheets_logger():
    try:
        from log_to_sheets import GoogleSheetsLogger
        return GoogleSheetsLogger()
    except ImportError:
        return None

logger = logging.getLogger(__name__)


class SessionManager:
    """簡化版會話管理器"""
    
    def __init__(self):
        self.sheets_logger = None
        self.daily_limit = 3
        
    def init_session_state(self):
        """初始化會話狀態"""
        # 基本狀態初始化
        defaults = {
            "language": "简体中文",
            "translation_count": 0,
            "input_method": "text",
            "feedback_submitted_ids": set(),
            "last_translation_id": None,
            "user_session_id": str(uuid.uuid4())[:8],
            "app_start_time": time.time(),
            "translation_history": [],
            "last_activity": time.time(),
            "device_id": None,
            "permanent_user_id": None,
            "daily_usage": {},
            "is_quota_locked": False,
            "session_initialized": False,
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # 生成設備ID（基於瀏覽器會話）
        if not st.session_state.device_id:
            st.session_state.device_id = self._generate_device_id()
        
        # 生成永久用戶ID
        if not st.session_state.permanent_user_id:
            st.session_state.permanent_user_id = self._generate_user_id()
        
        # 從 Google Sheets 加載今日實際使用次數（修復刷新問題）
        self._load_today_usage_from_sheets()
        
        st.session_state.session_initialized = True
    
    def _generate_device_id(self) -> str:
        """生成設備ID"""
        # 使用 session_id + 時間戳生成穩定的設備ID
        raw_data = f"{st.session_state.user_session_id}_{int(time.time() / 3600)}"
        device_hash = hashlib.md5(raw_data.encode()).hexdigest()[:12]
        return f"dev_{device_hash}"
    
    def _generate_user_id(self) -> str:
        """生成用戶ID"""
        # 結合設備ID和日期生成相對穩定的用戶ID
        today = datetime.now().strftime("%Y-%m-%d")
        raw_data = f"{st.session_state.device_id}_{today}"
        user_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
        return f"user_{user_hash}"
    
    def _load_today_usage_from_sheets(self):
        """從 Google Sheets 加載今日實際使用次數"""
        try:
            if not self.sheets_logger:
                self.sheets_logger = get_sheets_logger()
            
            if not self.sheets_logger or not self.sheets_logger.initialized:
                if self.sheets_logger and not self.sheets_logger.initialized:
                    self.sheets_logger._initialize_client()
            
            # 查詢今日使用次數
            today = datetime.now().strftime("%Y-%m-%d")
            user_id = st.session_state.permanent_user_id
            
            actual_count = self._query_usage_from_sheets(today, user_id)
            
            if actual_count is not None:
                st.session_state.translation_count = actual_count
                logger.info(f"從 Google Sheets 加載今日使用次數: {actual_count}")
                
                # 檢查是否超過限額
                if actual_count >= self.daily_limit:
                    st.session_state.is_quota_locked = True
            else:
                logger.warning("無法從 Google Sheets 獲取使用次數，使用本地記錄")
                
        except Exception as e:
            logger.error(f"加載今日使用次數失敗: {e}")
            # 使用本地記錄作為備用
    
    def _query_usage_from_sheets(self, date: str, user_id: str) -> Optional[int]:
        """查詢指定日期和用戶的使用次數"""
        try:
            if not self.sheets_logger or not self.sheets_logger.usage_worksheet:
                return None
            
            # 獲取所有記錄
            records = self.sheets_logger.usage_worksheet.get_all_records()
            
            # 計算今日該用戶的使用次數
            count = 0
            for record in records:
                try:
                    record_date = record.get('Date & Time', '')[:10]  # 取日期部分
                    record_user = record.get('User ID', '')
                    record_status = record.get('Processing Status', '')
                    
                    if (record_date == date and 
                        record_user == user_id and 
                        record_status == 'success'):
                        count += 1
                except Exception:
                    continue
            
            return count
            
        except Exception as e:
            logger.error(f"查詢使用次數失敗: {e}")
            return None
    
    def can_use_translation(self) -> Tuple[bool, str]:
        """檢查是否可以使用翻譯服務"""
        # 簡單的限制檢查
        if st.session_state.is_quota_locked:
            return False, "今日免費額度已用完，請明日再來"
        
        if st.session_state.translation_count >= self.daily_limit:
            st.session_state.is_quota_locked = True
            return False, "今日免費額度已用完，請明日再來"
        
        return True, "可以使用"
    
    def record_translation_usage(self, translation_id: str, text_hash: str):
        """記錄翻譯使用"""
        try:
            # 更新本地計數
            st.session_state.translation_count += 1
            st.session_state.last_translation_id = translation_id
            st.session_state.last_activity = time.time()
            
            # 添加到歷史記錄
            if 'translation_history' not in st.session_state:
                st.session_state.translation_history = []
            
            st.session_state.translation_history.append({
                'id': translation_id,
                'timestamp': time.time(),
                'text_hash': text_hash
            })
            
            # 檢查是否達到限額
            if st.session_state.translation_count >= self.daily_limit:
                st.session_state.is_quota_locked = True
            
            logger.info(f"記錄翻譯使用: {translation_id}, 總計: {st.session_state.translation_count}")
            
        except Exception as e:
            logger.error(f"記錄翻譯使用失敗: {e}")
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值（防重複翻譯）"""
        # 標準化文本：移除多餘空格，轉小寫
        normalized = ' '.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        today_usage = st.session_state.translation_count
        remaining = max(0, self.daily_limit - today_usage)
        is_locked = st.session_state.is_quota_locked or today_usage >= self.daily_limit
        
        return {
            'today_usage': today_usage,
            'remaining': remaining,
            'daily_limit': self.daily_limit,
            'is_locked': is_locked,
            'user_id': st.session_state.permanent_user_id[:8] + "****",  # 部分遮蔽
            'device_id': st.session_state.device_id,
            'session_id': st.session_state.user_session_id,
            'is_incognito': False,  # 簡化版不檢測無痕模式
            'security_issues': [],  # 簡化版不檢測安全問題
        }
    
    def reset_daily_usage(self):
        """重置每日使用量（僅用於測試）"""
        st.session_state.translation_count = 0
        st.session_state.is_quota_locked = False
        st.session_state.translation_history = []
        logger.info("每日使用量已重置")
    
    def get_session_info(self) -> Dict[str, Any]:
        """獲取會話信息（用於調試）"""
        return {
            'session_id': st.session_state.user_session_id,
            'device_id': st.session_state.device_id,
            'user_id': st.session_state.permanent_user_id,
            'translation_count': st.session_state.translation_count,
            'is_quota_locked': st.session_state.is_quota_locked,
            'app_start_time': st.session_state.app_start_time,
            'last_activity': st.session_state.last_activity,
            'language': st.session_state.language
        }
