"""
RadiAI.Care Session Manager - 修復版
=====================================
基於 UsageLog Sheet 的計數系統，完全移除對 Feedback 的依賴
"""

import streamlit as st
import hashlib
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """修復版會話管理器 - 基於 UsageLog Sheet"""
    
    def __init__(self):
        self.sheets_logger = None
        self.daily_limit = 3
        self._usage_cache = {}  # 緩存查詢結果
        self._last_query_time = 0
        self._cache_duration = 30  # 緩存30秒
        
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
            "usage_last_sync": 0,
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
        
        # 從 UsageLog Sheet 載入今日實際使用次數
        self._sync_usage_from_usagelog_sheet()
        
        st.session_state.session_initialized = True
    
    def _generate_device_id(self) -> str:
        """生成設備ID"""
        raw_data = f"{st.session_state.user_session_id}_{int(time.time() / 3600)}"
        device_hash = hashlib.md5(raw_data.encode()).hexdigest()[:12]
        return f"dev_{device_hash}"
    
    def _generate_user_id(self) -> str:
        """生成用戶ID"""
        today = datetime.now().strftime("%Y-%m-%d")
        raw_data = f"{st.session_state.device_id}_{today}"
        user_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
        return f"user_{user_hash}"
    
    def _get_sheets_logger(self):
        """獲取 Google Sheets Logger"""
        if not self.sheets_logger:
            try:
                from log_to_sheets import GoogleSheetsLogger
                self.sheets_logger = GoogleSheetsLogger()
                if not self.sheets_logger.initialized:
                    self.sheets_logger._initialize_client()
            except ImportError:
                logger.error("無法導入 GoogleSheetsLogger")
                return None
        return self.sheets_logger
    
    def _sync_usage_from_usagelog_sheet(self):
        """從 UsageLog Sheet 同步今日使用次數"""
        try:
            # 檢查緩存
            current_time = time.time()
            if (current_time - self._last_query_time < self._cache_duration and 
                self._usage_cache):
                logger.debug("使用緩存的使用次數數據")
                st.session_state.translation_count = self._usage_cache.get('count', 0)
                st.session_state.is_quota_locked = self._usage_cache.get('is_locked', False)
                return
            
            sheets_logger = self._get_sheets_logger()
            if not sheets_logger or not sheets_logger.usage_worksheet:
                logger.warning("無法獲取 UsageLog 工作表，使用本地計數")
                return
            
            # 查詢今日該用戶在 UsageLog 中的成功記錄
            today = datetime.now().strftime("%Y-%m-%d")
            user_id = st.session_state.permanent_user_id
            
            actual_count = self._count_successful_translations(sheets_logger, today, user_id)
            
            if actual_count is not None:
                # 更新本地狀態
                st.session_state.translation_count = actual_count
                st.session_state.is_quota_locked = actual_count >= self.daily_limit
                
                # 更新緩存
                self._usage_cache = {
                    'count': actual_count,
                    'is_locked': actual_count >= self.daily_limit,
                    'query_time': current_time
                }
                self._last_query_time = current_time
                
                logger.info(f"從 UsageLog 同步使用次數成功: {actual_count}/{self.daily_limit}")
            else:
                logger.warning("無法從 UsageLog 獲取使用次數，使用本地計數")
                
        except Exception as e:
            logger.error(f"從 UsageLog 同步使用次數失敗: {e}")
    
    def _count_successful_translations(self, sheets_logger, date: str, user_id: str) -> Optional[int]:
        """計算指定日期和用戶的成功翻譯次數"""
        try:
            # 獲取所有記錄
            all_records = sheets_logger.usage_worksheet.get_all_records()
            
            # 計算今日該用戶的成功翻譯次數
            success_count = 0
            for record in all_records:
                try:
                    # 提取記錄信息
                    record_date = record.get('Date & Time', '')[:10]  # 取日期部分
                    record_user = record.get('User ID', '')
                    record_status = record.get('Processing Status', '')
                    
                    # 匹配條件：日期、用戶ID、狀態為 success
                    if (record_date == date and 
                        record_user == user_id and 
                        record_status == 'success'):
                        success_count += 1
                        
                except (KeyError, ValueError, IndexError):
                    # 跳過格式不正確的記錄
                    continue
            
            logger.debug(f"UsageLog 中找到 {success_count} 次成功翻譯記錄")
            return success_count
            
        except Exception as e:
            logger.error(f"計算成功翻譯次數失敗: {e}")
            return None
    
    def can_use_translation(self) -> Tuple[bool, str]:
        """檢查是否可以使用翻譯服務"""
        # 先同步最新數據
        self._sync_usage_from_usagelog_sheet()
        
        if st.session_state.is_quota_locked:
            return False, "今日免費額度已用完，請明日再來"
        
        if st.session_state.translation_count >= self.daily_limit:
            st.session_state.is_quota_locked = True
            return False, "今日免費額度已用完，請明日再來"
        
        return True, "可以使用"
    
    def record_translation_usage(self, translation_id: str, text_hash: str):
        """記錄翻譯使用 - 僅更新本地狀態，實際記錄由 app.py 處理"""
        try:
            # 預先更新本地計數（樂觀更新）
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
            
            # 清除緩存，強制下次重新查詢
            self._usage_cache = {}
            self._last_query_time = 0
            
            logger.info(f"本地記錄翻譯使用: {translation_id}, 預期總計: {st.session_state.translation_count}")
            
        except Exception as e:
            logger.error(f"記錄翻譯使用失敗: {e}")
    
    def restore_usage_on_failure(self, translation_id: str):
        """翻譯失敗時恢復使用次數"""
        try:
            # 減少計數器
            if st.session_state.translation_count > 0:
                st.session_state.translation_count -= 1
            
            # 解除鎖定狀態
            if st.session_state.translation_count < self.daily_limit:
                st.session_state.is_quota_locked = False
            
            # 從翻譯歷史中移除失敗的記錄
            if 'translation_history' in st.session_state:
                st.session_state.translation_history = [
                    record for record in st.session_state.translation_history 
                    if record.get('id') != translation_id
                ]
            
            # 清除緩存
            self._usage_cache = {}
            self._last_query_time = 0
            
            logger.info(f"已恢復使用次數，當前計數: {st.session_state.translation_count}")
            
        except Exception as e:
            logger.error(f"恢復使用次數失敗: {e}")
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值（防重複翻譯）"""
        normalized = ' '.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        # 確保數據是最新的（但使用緩存避免頻繁查詢）
        current_time = time.time()
        if current_time - st.session_state.get('usage_last_sync', 0) > 30:  # 30秒同步一次
            self._sync_usage_from_usagelog_sheet()
            st.session_state.usage_last_sync = current_time
        
        today_usage = st.session_state.translation_count
        remaining = max(0, self.daily_limit - today_usage)
        is_locked = st.session_state.is_quota_locked or today_usage >= self.daily_limit
        
        return {
            'today_usage': today_usage,
            'remaining': remaining,
            'daily_limit': self.daily_limit,
            'is_locked': is_locked,
            'user_id': st.session_state.permanent_user_id[:8] + "****",
            'device_id': st.session_state.device_id,
            'session_id': st.session_state.user_session_id,
            'is_incognito': False,
            'security_issues': [],
            'data_source': 'UsageLog Sheet',  # 標識數據來源
        }
    
    def force_sync_usage(self):
        """強制同步使用次數（用於調試）"""
        self._usage_cache = {}
        self._last_query_time = 0
        self._sync_usage_from_usagelog_sheet()
        logger.info("已強制同步使用次數")
    
    def reset_daily_usage(self):
        """重置每日使用量（僅用於測試）"""
        st.session_state.translation_count = 0
        st.session_state.is_quota_locked = False
        st.session_state.translation_history = []
        self._usage_cache = {}
        self._last_query_time = 0
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
            'language': st.session_state.language,
            'cache_info': {
                'cached_count': self._usage_cache.get('count'),
                'cache_age': time.time() - self._last_query_time if self._last_query_time else 0,
                'cache_valid': time.time() - self._last_query_time < self._cache_duration
            }
        }
