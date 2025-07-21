"""
RadiAI.Care 會話狀態管理器
統一管理所有 Streamlit session state 變數
包含防止刷新濫用的機制
"""

import streamlit as st
import time
import uuid
import hashlib
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """會話狀態管理器"""
    
    # 預設值配置
    DEFAULT_VALUES = {
        'language': "简体中文",
        'translation_count': 0,
        'input_method': "text",
        'feedback_submitted_ids': set(),
        'last_translation_id': None,
        'user_session_id': lambda: str(uuid.uuid4())[:8],
        'app_start_time': lambda: time.time(),
        'translation_history': list,
        'last_activity': lambda: time.time(),
        'browser_fingerprint': None,
        'device_id': None,
        'used_translations': dict,  # 記錄已使用的翻譯
        'daily_usage': dict,  # 每日使用記錄
        'is_quota_locked': False,  # 是否鎖定配額
        'quota_lock_time': None  # 配額鎖定時間
    }
    
    def __init__(self):
        """初始化會話管理器"""
        self.storage_key = "radiai_usage_data"
    
    def init_session_state(self):
        """初始化所有會話狀態變數"""
        for key, default_value in self.DEFAULT_VALUES.items():
            if key not in st.session_state:
                if callable(default_value):
                    st.session_state[key] = default_value()
                else:
                    st.session_state[key] = default_value
        
        # 初始化持久化存儲
        self._init_persistent_storage()
        
        # 生成或獲取設備ID
        self._init_device_id()
        
        # 檢查配額狀態
        self._check_quota_status()
    
    def _init_persistent_storage(self):
        """初始化持久化存儲（使用瀏覽器特徵）"""
        try:
            # 嘗試從瀏覽器獲取存儲的數據
            if 'browser_storage' not in st.session_state:
                st.session_state.browser_storage = {}
            
            # 生成瀏覽器指紋
            self._generate_browser_fingerprint()
            
        except Exception as e:
            logger.error(f"初始化持久化存儲失敗: {e}")
    
    def _generate_browser_fingerprint(self):
        """生成瀏覽器指紋（基於多個因素）"""
        try:
            # 收集瀏覽器特徵
            components = []
            
            # 使用會話ID和時間戳
            components.append(st.session_state.user_session_id)
            
            # 添加用戶代理信息（如果可用）
            # 注意：Streamlit 不直接提供用戶代理，這裡使用替代方案
            components.append(str(time.time()))
            
            # 生成指紋
            fingerprint_str = "_".join(components)
            fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]
            
            st.session_state.browser_fingerprint = fingerprint
            
        except Exception as e:
            logger.error(f"生成瀏覽器指紋失敗: {e}")
            st.session_state.browser_fingerprint = str(uuid.uuid4())[:16]
    
    def _init_device_id(self):
        """初始化設備ID（持久化標識）"""
        if st.session_state.device_id is None:
            # 嘗試從本地存儲獲取
            stored_id = self._get_stored_device_id()
            
            if stored_id:
                st.session_state.device_id = stored_id
            else:
                # 生成新的設備ID
                new_id = self._generate_device_id()
                st.session_state.device_id = new_id
                self._store_device_id(new_id)
    
    def _generate_device_id(self) -> str:
        """生成唯一的設備ID"""
        components = [
            st.session_state.browser_fingerprint or "unknown",
            str(time.time()),
            str(uuid.uuid4())
        ]
        
        device_str = "_".join(components)
        return hashlib.sha256(device_str.encode()).hexdigest()[:32]
    
    def _get_stored_device_id(self) -> Optional[str]:
        """從存儲中獲取設備ID"""
        # 在實際部署中，這裡應該使用 cookies 或 localStorage
        # 由於 Streamlit 的限制，我們使用會話狀態模擬
        return st.session_state.get('stored_device_id')
    
    def _store_device_id(self, device_id: str):
        """存儲設備ID"""
        st.session_state.stored_device_id = device_id
    
    def _check_quota_status(self):
        """檢查配額狀態"""
        device_id = st.session_state.device_id
        
        # 獲取今天的日期
        today = time.strftime('%Y-%m-%d')
        
        # 檢查每日使用記錄
        if today not in st.session_state.daily_usage:
            st.session_state.daily_usage[today] = {}
        
        # 檢查設備使用記錄
        device_usage = st.session_state.daily_usage[today].get(device_id, {
            'count': 0,
            'translations': [],
            'first_use': None,
            'last_use': None
        })
        
        # 更新翻譯計數（防止刷新重置）
        if device_usage['count'] >= 3:
            st.session_state.translation_count = device_usage['count']
            st.session_state.is_quota_locked = True
            st.session_state.quota_lock_time = device_usage['last_use']
        else:
            # 如果設備有使用記錄，恢復計數
            if device_usage['count'] > 0:
                st.session_state.translation_count = device_usage['count']
    
    def can_use_translation(self) -> tuple[bool, str]:
        """
        檢查是否可以使用翻譯服務
        
        Returns:
            tuple[bool, str]: (是否可以使用, 原因消息)
        """
        device_id = st.session_state.device_id
        today = time.strftime('%Y-%m-%d')
        
        # 檢查是否被鎖定
        if st.session_state.is_quota_locked:
            return False, "您今日的免費額度已用完，請明天再來！"
        
        # 檢查設備每日使用量
        if today in st.session_state.daily_usage:
            device_usage = st.session_state.daily_usage[today].get(device_id, {})
            if device_usage.get('count', 0) >= 3:
                return False, "您今日的免費額度已用完（基於設備限制）"
        
        # 檢查會話使用量
        if st.session_state.translation_count >= 3:
            return False, "您的免費翻譯額度已用完"
        
        return True, "可以使用"
    
    def record_translation_usage(self, translation_id: str, text_hash: str):
        """
        記錄翻譯使用情況
        
        Args:
            translation_id: 翻譯ID
            text_hash: 文本哈希（用於防止重複翻譯相同內容）
        """
        device_id = st.session_state.device_id
        today = time.strftime('%Y-%m-%d')
        current_time = time.time()
        
        # 初始化今日記錄
        if today not in st.session_state.daily_usage:
            st.session_state.daily_usage[today] = {}
        
        # 初始化設備記錄
        if device_id not in st.session_state.daily_usage[today]:
            st.session_state.daily_usage[today][device_id] = {
                'count': 0,
                'translations': [],
                'first_use': current_time,
                'last_use': current_time,
                'text_hashes': set()
            }
        
        device_usage = st.session_state.daily_usage[today][device_id]
        
        # 檢查是否重複翻譯相同內容
        if text_hash in device_usage.get('text_hashes', set()):
            logger.warning(f"檢測到重複翻譯相同內容: {text_hash}")
            return
        
        # 記錄使用
        device_usage['count'] += 1
        device_usage['translations'].append({
            'id': translation_id,
            'time': current_time,
            'text_hash': text_hash
        })
        device_usage['last_use'] = current_time
        device_usage.setdefault('text_hashes', set()).add(text_hash)
        
        # 更新會話計數
        st.session_state.translation_count += 1
        
        # 檢查是否需要鎖定
        if device_usage['count'] >= 3:
            st.session_state.is_quota_locked = True
            st.session_state.quota_lock_time = current_time
            logger.info(f"設備 {device_id} 已達到每日限額")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        device_id = st.session_state.device_id
        today = time.strftime('%Y-%m-%d')
        
        stats = {
            'session_count': st.session_state.translation_count,
            'device_id': device_id[:8] + "****",  # 部分隱藏
            'is_locked': st.session_state.is_quota_locked,
            'today_usage': 0,
            'remaining': 3 - st.session_state.translation_count
        }
        
        if today in st.session_state.daily_usage:
            device_usage = st.session_state.daily_usage[today].get(device_id, {})
            stats['today_usage'] = device_usage.get('count', 0)
            stats['remaining'] = max(0, 3 - device_usage.get('count', 0))
        
        return stats
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值"""
        # 正規化文本（移除空白差異）
        normalized = " ".join(text.strip().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def clear_expired_data(self):
        """清理過期數據（保留7天）"""
        current_date = time.strftime('%Y-%m-%d')
