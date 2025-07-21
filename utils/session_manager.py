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
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

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
        'quota_lock_time': None,  # 配額鎖定時間
        'persistent_device_id': None,  # 持久化設備ID
        'session_initialized': False  # 會話是否已初始化
    }
    
    def __init__(self):
        """初始化會話管理器"""
        self.storage_key = "radiai_usage_data"
        self._init_persistent_device_id()
    
    def _init_persistent_device_id(self):
        """初始化持久化設備ID（使用cookie模擬）"""
        # 注入JavaScript來處理localStorage
        if 'persistent_device_id' not in st.session_state or st.session_state.persistent_device_id is None:
            # 生成設備ID的JavaScript代碼
            device_id_script = """
            <script>
            (function() {
                // 檢查localStorage中是否有設備ID
                let deviceId = localStorage.getItem('radiai_device_id');
                
                if (!deviceId) {
                    // 生成新的設備ID
                    deviceId = 'dev_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9);
                    localStorage.setItem('radiai_device_id', deviceId);
                }
                
                // 將設備ID存儲到隱藏的div中供Python讀取
                const hiddenDiv = document.getElementById('device_id_storage');
                if (hiddenDiv) {
                    hiddenDiv.textContent = deviceId;
                }
                
                // 同時嘗試通過URL參數傳遞（備用方案）
                if (!window.location.search.includes('device_id=')) {
                    const newUrl = window.location.href + (window.location.search ? '&' : '?') + 'device_id=' + deviceId;
                    window.history.replaceState({}, '', newUrl);
                }
            })();
            </script>
            <div id="device_id_storage" style="display: none;"></div>
            """
            st.components.v1.html(device_id_script, height=0)
    
    def init_session_state(self):
        """初始化所有會話狀態變數"""
        # 標記會話初始化
        if not st.session_state.get('session_initialized', False):
            for key, default_value in self.DEFAULT_VALUES.items():
                if key not in st.session_state:
                    if callable(default_value):
                        st.session_state[key] = default_value()
                    else:
                        st.session_state[key] = default_value
            
            st.session_state.session_initialized = True
        
        # 初始化持久化存儲
        self._init_persistent_storage()
        
        # 生成或獲取設備ID
        self._init_device_id()
        
        # 載入持久化的使用記錄
        self._load_usage_data()
        
        # 檢查配額狀態
        self._check_quota_status()
    
    def _init_persistent_storage(self):
        """初始化持久化存儲"""
        try:
            # 嘗試從查詢參數獲取設備ID
            query_params = st.experimental_get_query_params()
            device_id_from_url = query_params.get('device_id', [None])[0]
            
            if device_id_from_url and device_id_from_url != st.session_state.get('persistent_device_id'):
                st.session_state.persistent_device_id = device_id_from_url
                logger.info(f"從URL獲取設備ID: {device_id_from_url[:8]}...")
            
            # 生成瀏覽器指紋
            self._generate_browser_fingerprint()
            
        except Exception as e:
            logger.error(f"初始化持久化存儲失敗: {e}")
    
    def _generate_browser_fingerprint(self):
        """生成瀏覽器指紋"""
        try:
            components = []
            
            # 使用會話ID和時間戳
            components.append(st.session_state.user_session_id)
            components.append(str(time.time()))
            
            # 如果有持久化設備ID，也加入
            if st.session_state.get('persistent_device_id'):
                components.append(st.session_state.persistent_device_id)
            
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
            # 優先使用持久化設備ID
            if st.session_state.get('persistent_device_id'):
                st.session_state.device_id = st.session_state.persistent_device_id
            else:
                # 嘗試從存儲獲取
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
        return st.session_state.get('stored_device_id') or st.session_state.get('persistent_device_id')
    
    def _store_device_id(self, device_id: str):
        """存儲設備ID"""
        st.session_state.stored_device_id = device_id
        # 同時更新持久化設備ID
        if not st.session_state.get('persistent_device_id'):
            st.session_state.persistent_device_id = device_id
    
    def _load_usage_data(self):
        """載入持久化的使用記錄"""
        try:
            # 嘗試從localStorage載入數據
            load_script = """
            <script>
            (function() {
                const usageData = localStorage.getItem('radiai_usage_data');
                if (usageData) {
                    const hiddenDiv = document.getElementById('usage_data_storage');
                    if (hiddenDiv) {
                        hiddenDiv.textContent = usageData;
                    }
                }
            })();
            </script>
            <div id="usage_data_storage" style="display: none;"></div>
            """
            # st.components.v1.html(load_script, height=0)
            
            # 如果有存儲的數據，載入到session state
            if hasattr(st.session_state, 'loaded_usage_data'):
                data = json.loads(st.session_state.loaded_usage_data)
                st.session_state.daily_usage = data.get('daily_usage', {})
                logger.info("成功載入持久化使用記錄")
        except Exception as e:
            logger.error(f"載入使用記錄失敗: {e}")
    
    def _save_usage_data(self):
        """保存使用記錄到持久化存儲"""
        try:
            # 準備要保存的數據
            data = {
                'daily_usage': st.session_state.daily_usage,
                'device_id': st.session_state.device_id,
                'last_update': time.time()
            }
            
            # 保存到localStorage的JavaScript代碼
            save_script = f"""
            <script>
            localStorage.setItem('radiai_usage_data', '{json.dumps(data)}');
            </script>
            """
            # st.components.v1.html(save_script, height=0)
            
        except Exception as e:
            logger.error(f"保存使用記錄失敗: {e}")
    
    def _check_quota_status(self):
        """檢查配額狀態"""
        device_id = st.session_state.device_id
        
        # 獲取今天的日期（澳洲時間）
        from datetime import datetime
        import pytz
        sydney_tz = pytz.timezone('Australia/Sydney')
        today = datetime.now(sydney_tz).strftime('%Y-%m-%d')
        
        # 清理過期數據（保留7天）
        self._clean_old_usage_data()
        
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
            # 恢復設備的使用計數
            if device_usage['count'] > 0:
                st.session_state.translation_count = device_usage['count']
    
    def _clean_old_usage_data(self):
        """清理過期的使用數據"""
        try:
            from datetime import datetime, timedelta
            import pytz
            
            sydney_tz = pytz.timezone('Australia/Sydney')
            today = datetime.now(sydney_tz)
            cutoff_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 刪除7天前的記錄
            dates_to_remove = []
            for date_str in st.session_state.daily_usage.keys():
                if date_str < cutoff_date:
                    dates_to_remove.append(date_str)
            
            for date_str in dates_to_remove:
                del st.session_state.daily_usage[date_str]
                logger.info(f"清理過期數據: {date_str}")
                
        except Exception as e:
            logger.error(f"清理過期數據失敗: {e}")
    
    def can_use_translation(self) -> Tuple[bool, str]:
        """
        檢查是否可以使用翻譯服務
        
        Returns:
            Tuple[bool, str]: (是否可以使用, 原因消息)
        """
        device_id = st.session_state.device_id
        
        # 獲取今天的日期（澳洲時間）
        from datetime import datetime
        import pytz
        sydney_tz = pytz.timezone('Australia/Sydney')
        today = datetime.now(sydney_tz).strftime('%Y-%m-%d')
        
        # 檢查是否被鎖定
        if st.session_state.is_quota_locked:
            # 檢查是否是新的一天
            if today in st.session_state.daily_usage:
                device_usage = st.session_state.daily_usage[today].get(device_id, {})
                if device_usage.get('count', 0) >= 3:
                    return False, "您今日的免費額度已用完，請明天再來！"
            else:
                # 新的一天，解鎖
                st.session_state.is_quota_locked = False
                st.session_state.translation_count = 0
        
        # 檢查設備每日使用量
        if today in st.session_state.daily_usage:
            device_usage = st.session_state.daily_usage[today].get(device_id, {})
            if device_usage.get('count', 0) >= 3:
                return False, "您今日的免費額度已用完（每個設備每天限3次）"
        
        # 檢查會話使用量
        if st.session_state.translation_count >= 3:
            return False, "您的免費翻譯額度已用完"
        
        return True, "可以使用"
    
    def record_translation_usage(self, translation_id: str, text_hash: str):
        """
        記錄翻譯使用情況
        
        Args:
            translation_id: 翻譯ID
            text_hash: 文本哈希
        """
        device_id = st.session_state.device_id
        
        # 獲取今天的日期（澳洲時間）
        from datetime import datetime
        import pytz
        sydney_tz = pytz.timezone('Australia/Sydney')
        today = datetime.now(sydney_tz).strftime('%Y-%m-%d')
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
            logger.warning(f"檢測到重複翻譯相同內容: {text_hash[:8]}...")
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
        st.session_state.translation_count = device_usage['count']
        
        # 檢查是否需要鎖定
        if device_usage['count'] >= 3:
            st.session_state.is_quota_locked = True
            st.session_state.quota_lock_time = current_time
            logger.info(f"設備 {device_id[:8]}... 已達到每日限額")
        
        # 保存數據到持久化存儲
        self._save_usage_data()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        device_id = st.session_state.device_id
        
        # 獲取今天的日期（澳洲時間）
        from datetime import datetime
        import pytz
        sydney_tz = pytz.timezone('Australia/Sydney')
        today = datetime.now(sydney_tz).strftime('%Y-%m-%d')
        
        stats = {
            'session_count': st.session_state.translation_count,
            'device_id': device_id[:8] + "****" if device_id else "unknown",
            'is_locked': st.session_state.is_quota_locked,
            'today_usage': 0,
            'remaining': 3
        }
        
        if today in st.session_state.daily_usage and device_id:
            device_usage = st.session_state.daily_usage[today].get(device_id, {})
            stats['today_usage'] = device_usage.get('count', 0)
            stats['remaining'] = max(0, 3 - device_usage.get('count', 0))
        else:
            stats['remaining'] = max(0, 3 - st.session_state.translation_count)
        
        return stats
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值"""
        # 正規化文本（移除空白差異）
        normalized = " ".join(text.strip().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def reset_daily_quota(self):
        """重置每日配額（用於測試）"""
        from datetime import datetime
        import pytz
        sydney_tz = pytz.timezone('Australia/Sydney')
        today = datetime.now(sydney_tz).strftime('%Y-%m-%d')
        
        if today in st.session_state.daily_usage:
            device_id = st.session_state.device_id
            if device_id and device_id in st.session_state.daily_usage[today]:
                del st.session_state.daily_usage[today][device_id]
        
        st.session_state.translation_count = 0
        st.session_state.is_quota_locked = False
        st.session_state.quota_lock_time = None
        logger.info("每日配額已重置")
