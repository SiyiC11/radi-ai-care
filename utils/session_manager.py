"""
RadiAI.Care 會話狀態管理器
統一管理所有 Streamlit session state 變數
"""

import streamlit as st
import time
import uuid
from typing import Dict, Any, Optional

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
        'last_activity': lambda: time.time()
    }
    
    def __init__(self):
        """初始化會話管理器"""
        pass
    
    def init_session_state(self):
        """初始化所有會話狀態變數"""
        for key, default_value in self.DEFAULT_VALUES.items():
            if key not in st.session_state:
                if callable(default_value):
                    st.session_state[key] = default_value()
                else:
                    st.session_state[key] = default_value
    
    def get_session_value(self, key: str, default: Any = None) -> Any:
        """獲取會話狀態值"""
        return st.session_state.get(key, default)
    
    def set_session_value(self, key: str, value: Any):
        """設置會話狀態值"""
        st.session_state[key] = value
    
    def update_activity(self):
        """更新最後活動時間"""
        st.session_state.last_activity = time.time()
    
    def add_translation_record(self, translation_id: str, text_length: int, language: str):
        """添加翻譯記錄到歷史"""
        if 'translation_history' not in st.session_state:
            st.session_state.translation_history = []
        
        record = {
            'id': translation_id,
            'timestamp': time.time(),
            'text_length': text_length,
            'language': language
        }
        
        st.session_state.translation_history.append(record)
        
        # 限制歷史記錄數量
        if len(st.session_state.translation_history) > 50:
            st.session_state.translation_history = st.session_state.translation_history[-50:]
    
    def get_session_duration(self) -> int:
        """獲取會話持續時間（分鐘）"""
        if 'app_start_time' in st.session_state:
            return int((time.time() - st.session_state.app_start_time) / 60)
        return 0
    
    def get_translation_stats(self) -> Dict[str, Any]:
        """獲取翻譯統計信息"""
        history = st.session_state.get('translation_history', [])
        
        if not history:
            return {
                'total_translations': 0,
                'total_characters': 0,
                'session_duration': self.get_session_duration()
            }
        
        total_translations = len(history)
        total_characters = sum(record['text_length'] for record in history)
        
        return {
            'total_translations': total_translations,
            'total_characters': total_characters,
            'session_duration': self.get_session_duration(),
            'average_length': total_characters // total_translations if total_translations > 0 else 0
        }
    
    def clear_session(self):
        """清除所有會話狀態"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        self.init_session_state()
    
    def is_feedback_submitted(self, translation_id: str) -> bool:
        """檢查是否已提交回饋"""
        submitted_ids = st.session_state.get('feedback_submitted_ids', set())
        return translation_id in submitted_ids
    
    def mark_feedback_submitted(self, translation_id: str):
        """標記回饋已提交"""
        if 'feedback_submitted_ids' not in st.session_state:
            st.session_state.feedback_submitted_ids = set()
        st.session_state.feedback_submitted_ids.add(translation_id)
    
    def get_remaining_translations(self, max_translations: int = 3) -> int:
        """獲取剩餘翻譯次數"""
        used = st.session_state.get('translation_count', 0)
        return max(0, max_translations - used)
    
    def increment_translation_count(self):
        """增加翻譯計數"""
        if 'translation_count' not in st.session_state:
            st.session_state.translation_count = 0
        st.session_state.translation_count += 1
    
    def get_user_session_id(self) -> str:
        """獲取用戶會話ID"""
        return st.session_state.get('user_session_id', 'unknown')
    
    def set_language(self, language: str):
        """設置語言並重新運行"""
        st.session_state.language = language
        self.update_activity()
        st.rerun()
    
    def export_session_data(self) -> Dict[str, Any]:
        """導出會話數據（用於調試或分析）"""
        return {
            'user_session_id': self.get_user_session_id(),
            'language': st.session_state.get('language'),
            'translation_count': st.session_state.get('translation_count', 0),
            'session_duration': self.get_session_duration(),
            'translation_stats': self.get_translation_stats(),
            'last_activity': st.session_state.get('last_activity'),
            'app_start_time': st.session_state.get('app_start_time')
        }