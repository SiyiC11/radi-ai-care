"""
RadiAI.Care 會話狀態管理器 - 增強版
包含多層防護機制，防止各種繞過限制的嘗試
"""

import streamlit as st
import streamlit.components.v1 as components
import time
import uuid
import hashlib
import json
import base64
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import hmac
import re

logger = logging.getLogger(__name__)

class SessionManager:
    """增強版會話狀態管理器"""
    
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
        'permanent_user_id': None,  # 永久用戶ID
        'used_translations': dict,
        'daily_usage': dict,
        'is_quota_locked': False,
        'quota_lock_time': None,
        'session_initialized': False,
        'fingerprint_data': dict,  # 儲存指紋數據
        'security_checks': dict,   # 安全檢查記錄
        'js_initialized': False    # JavaScript是否已初始化
    }
    
    # 安全密鑰（應該從環境變量讀取）
    SECURITY_KEY = "radiai_2024_security_key"
    
    def __init__(self):
        """初始化會話管理器"""
        self.storage_key = "radiai_usage_data"
        self.user_id_key = "radiai_permanent_user_id"
        self.daily_usage_key = "radiai_daily_usage"
    
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
        
        # 初始化JavaScript通信
        if not st.session_state.get('js_initialized', False):
            self._init_javascript_bridge()
            st.session_state.js_initialized = True
        
        # 收集設備指紋
        self._collect_device_fingerprint()
        
        # 初始化永久用戶ID
        self._init_permanent_user_id()
        
        # 載入使用記錄
        self._load_usage_data()
        
        # 執行安全檢查
        self._perform_security_checks()
        
        # 檢查配額狀態
        self._check_quota_status()
    
    def _init_javascript_bridge(self):
        """初始化JavaScript通信橋接"""
        js_code = """
        <script>
        // RadiAI.Care 防濫用系統
        (function() {
            // 生成或獲取永久用戶ID
            function getPermanentUserId() {
                let userId = localStorage.getItem('radiai_permanent_user_id');
                
                if (!userId) {
                    // 生成新的用戶ID - 包含時間戳、隨機數和瀏覽器特徵
                    const timestamp = Date.now().toString(36);
                    const random = Math.random().toString(36).substr(2, 9);
                    const browserData = collectBrowserData();
                    const browserHash = hashCode(JSON.stringify(browserData)).toString(36);
                    
                    userId = `uid_${timestamp}_${random}_${browserHash}`;
                    localStorage.setItem('radiai_permanent_user_id', userId);
                    localStorage.setItem('radiai_user_created', new Date().toISOString());
                }
                
                return userId;
            }
            
            // 收集瀏覽器指紋數據
            function collectBrowserData() {
                const data = {
                    userAgent: navigator.userAgent,
                    language: navigator.language,
                    languages: navigator.languages ? navigator.languages.join(',') : '',
                    platform: navigator.platform,
                    cookieEnabled: navigator.cookieEnabled,
                    doNotTrack: navigator.doNotTrack,
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    screenResolution: `${screen.width}x${screen.height}`,
                    screenColorDepth: screen.colorDepth,
                    timezoneOffset: new Date().getTimezoneOffset(),
                    sessionStorage: typeof(sessionStorage) !== 'undefined',
                    localStorage: typeof(localStorage) !== 'undefined',
                    indexedDB: !!window.indexedDB,
                    webGL: getWebGLFingerprint(),
                    canvas: getCanvasFingerprint(),
                    fonts: getInstalledFonts(),
                    plugins: getPlugins(),
                    touchSupport: getTouchSupport(),
                    connectionType: getConnectionType()
                };
                
                return data;
            }
            
            // WebGL指紋
            function getWebGLFingerprint() {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return null;
                    
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return debugInfo ? {
                        vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                        renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
                    } : null;
                } catch (e) {
                    return null;
                }
            }
            
            // Canvas指紋
            function getCanvasFingerprint() {
                try {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const text = 'RadiAI.Care 2024';
                    ctx.textBaseline = 'top';
                    ctx.font = '14px Arial';
                    ctx.fillText(text, 2, 2);
                    return canvas.toDataURL().substring(0, 100);
                } catch (e) {
                    return null;
                }
            }
            
            // 檢測已安裝字體
            function getInstalledFonts() {
                const testFonts = ['Arial', 'Verdana', 'Times New Roman', 'Courier', 'Georgia'];
                const baseFonts = ['monospace', 'sans-serif', 'serif'];
                const testString = "mmmmmmmmmmlli";
                const testSize = '72px';
                
                const h = document.getElementsByTagName("body")[0];
                const s = document.createElement("span");
                s.style.fontSize = testSize;
                s.innerHTML = testString;
                const defaultWidth = {};
                const defaultHeight = {};
                
                for (const baseFont of baseFonts) {
                    s.style.fontFamily = baseFont;
                    h.appendChild(s);
                    defaultWidth[baseFont] = s.offsetWidth;
                    defaultHeight[baseFont] = s.offsetHeight;
                    h.removeChild(s);
                }
                
                const detected = [];
                for (const font of testFonts) {
                    let detected_font = false;
                    for (const baseFont of baseFonts) {
                        s.style.fontFamily = font + ',' + baseFont;
                        h.appendChild(s);
                        const matched = (s.offsetWidth !== defaultWidth[baseFont] || s.offsetHeight !== defaultHeight[baseFont]);
                        h.removeChild(s);
                        detected_font = detected_font || matched;
                    }
                    if (detected_font) {
                        detected.push(font);
                    }
                }
                
                return detected.join(',');
            }
            
            // 獲取插件列表
            function getPlugins() {
                try {
                    return Array.from(navigator.plugins || [])
                        .map(p => p.name)
                        .join(',');
                } catch (e) {
                    return '';
                }
            }
            
            // 觸摸支援檢測
            function getTouchSupport() {
                return {
                    maxTouchPoints: navigator.maxTouchPoints || 0,
                    touchEvent: 'ontouchstart' in window,
                    touchPoints: navigator.msMaxTouchPoints || 0
                };
            }
            
            // 網絡連接類型
            function getConnectionType() {
                return navigator.connection ? {
                    effectiveType: navigator.connection.effectiveType,
                    type: navigator.connection.type,
                    downlink: navigator.connection.downlink
                } : null;
            }
            
            // 簡單的哈希函數
            function hashCode(str) {
                let hash = 0;
                for (let i = 0; i < str.length; i++) {
                    const char = str.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash;
                }
                return Math.abs(hash);
            }
            
            // 獲取或創建每日使用記錄
            function getDailyUsage() {
                const today = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD格式
                const storageKey = `radiai_usage_${today}`;
                
                let usage = localStorage.getItem(storageKey);
                if (!usage) {
                    usage = {
                        date: today,
                        count: 0,
                        translations: [],
                        userId: getPermanentUserId(),
                        firstUse: null,
                        lastUse: null
                    };
                    localStorage.setItem(storageKey, JSON.stringify(usage));
                } else {
                    usage = JSON.parse(usage);
                }
                
                return usage;
            }
            
            // 更新使用記錄
            function updateUsage(translationId) {
                const today = new Date().toLocaleDateString('en-CA');
                const storageKey = `radiai_usage_${today}`;
                const usage = getDailyUsage();
                
                usage.count += 1;
                usage.translations.push({
                    id: translationId,
                    timestamp: new Date().toISOString()
                });
                usage.lastUse = new Date().toISOString();
                if (!usage.firstUse) {
                    usage.firstUse = new Date().toISOString();
                }
                
                localStorage.setItem(storageKey, JSON.stringify(usage));
                
                // 清理舊記錄（保留7天）
                cleanOldUsageData();
                
                return usage;
            }
            
            // 清理過期記錄
            function cleanOldUsageData() {
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - 7);
                
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('radiai_usage_')) {
                        const dateStr = key.replace('radiai_usage_', '');
                        const keyDate = new Date(dateStr);
                        if (keyDate < cutoffDate) {
                            localStorage.removeItem(key);
                        }
                    }
                }
            }
            
            // 檢測無痕模式
            function detectIncognito() {
                return new Promise((resolve) => {
                    // 檢測 Chrome 無痕模式
                    if ('storage' in navigator && 'estimate' in navigator.storage) {
                        navigator.storage.estimate().then(({usage, quota}) => {
                            if (quota < 120000000) {
                                resolve(true);
                            } else {
                                resolve(false);
                            }
                        });
                    } else {
                        // Firefox 檢測
                        let db;
                        const test = () => {
                            try {
                                db = indexedDB.open('test');
                                db.onsuccess = () => resolve(false);
                                db.onerror = () => resolve(true);
                            } catch (e) {
                                resolve(true);
                            }
                        };
                        test();
                    }
                });
            }
            
            // 將數據發送到 Streamlit
            function sendDataToStreamlit() {
                const userId = getPermanentUserId();
                const browserData = collectBrowserData();
                const dailyUsage = getDailyUsage();
                
                detectIncognito().then(isIncognito => {
                    const data = {
                        permanentUserId: userId,
                        browserFingerprint: browserData,
                        dailyUsage: dailyUsage,
                        isIncognito: isIncognito,
                        timestamp: new Date().toISOString()
                    };
                    
                    // 將數據編碼並存儲到隱藏元素
                    const encodedData = btoa(JSON.stringify(data));
                    const dataElement = document.getElementById('radiai_data_bridge');
                    if (dataElement) {
                        dataElement.value = encodedData;
                        dataElement.dispatchEvent(new Event('change'));
                    }
                    
                    // 同時更新 URL 參數（備用方案）
                    const url = new URL(window.location);
                    url.searchParams.set('uid', userId.substring(0, 16));
                    window.history.replaceState({}, '', url);
                });
            }
            
            // 初始化
            sendDataToStreamlit();
            
            // 定期更新（每5秒）
            setInterval(sendDataToStreamlit, 5000);
            
            // 暴露API給Streamlit
            window.RadiAIUsageManager = {
                getUserId: getPermanentUserId,
                getDailyUsage: getDailyUsage,
                updateUsage: updateUsage,
                getBrowserData: collectBrowserData,
                detectIncognito: detectIncognito
            };
        })();
        </script>
        
        <!-- 數據橋接元素 -->
        <input type="hidden" id="radiai_data_bridge" value="" />
        
        <script>
        // 監聽Streamlit命令
        document.addEventListener('streamlit:update_usage', (event) => {
            if (window.RadiAIUsageManager && event.detail) {
                window.RadiAIUsageManager.updateUsage(event.detail.translationId);
            }
        });
        </script>
        """
        
        # 注入JavaScript代碼
        components.html(js_code, height=0)
    
    def _collect_device_fingerprint(self):
        """收集設備指紋數據"""
        try:
            # 從JavaScript橋接獲取數據
            data_element_value = st.session_state.get('radiai_data_bridge_value', '')
            
            if data_element_value:
                # 解碼數據
                decoded_data = base64.b64decode(data_element_value).decode('utf-8')
                data = json.loads(decoded_data)
                
                # 更新session state
                st.session_state.permanent_user_id = data['permanentUserId']
                st.session_state.fingerprint_data = data['browserFingerprint']
                st.session_state.is_incognito = data.get('isIncognito', False)
                
                # 更新每日使用記錄
                self._sync_usage_data(data['dailyUsage'])
                
                logger.info(f"收集到設備指紋，用戶ID: {data['permanentUserId'][:16]}...")
                
        except Exception as e:
            logger.error(f"收集設備指紋失敗: {e}")
    
    def _init_permanent_user_id(self):
        """初始化永久用戶ID"""
        if not st.session_state.permanent_user_id:
            # 嘗試從URL參數獲取
            try:
                query_params = st.experimental_get_query_params()
                uid_from_url = query_params.get('uid', [None])[0]
                
                if uid_from_url:
                    st.session_state.permanent_user_id = uid_from_url
                    logger.info(f"從URL獲取用戶ID: {uid_from_url}")
                else:
                    # 生成臨時ID（等待JavaScript返回真實ID）
                    temp_id = self._generate_secure_user_id()
                    st.session_state.permanent_user_id = temp_id
                    logger.info(f"生成臨時用戶ID: {temp_id[:16]}...")
                    
            except Exception as e:
                logger.error(f"初始化用戶ID失敗: {e}")
                st.session_state.permanent_user_id = self._generate_secure_user_id()
    
    def _generate_secure_user_id(self) -> str:
        """生成安全的用戶ID"""
        components = [
            str(time.time()),
            str(uuid.uuid4()),
            st.session_state.get('browser_fingerprint', 'unknown'),
            self.SECURITY_KEY
        ]
        
        combined = "_".join(components)
        user_id_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return f"uid_{int(time.time())}_{user_id_hash[:16]}"
    
    def _sync_usage_data(self, js_usage_data: Dict):
        """同步JavaScript的使用數據"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if today not in st.session_state.daily_usage:
                st.session_state.daily_usage[today] = {}
            
            user_id = st.session_state.permanent_user_id
            
            # 更新使用記錄
            st.session_state.daily_usage[today][user_id] = {
                'count': js_usage_data.get('count', 0),
                'translations': js_usage_data.get('translations', []),
                'first_use': js_usage_data.get('firstUse'),
                'last_use': js_usage_data.get('lastUse')
            }
            
            # 更新當前會話的計數
            st.session_state.translation_count = js_usage_data.get('count', 0)
            
            # 檢查是否需要鎖定
            if js_usage_data.get('count', 0) >= 3:
                st.session_state.is_quota_locked = True
                st.session_state.quota_lock_time = js_usage_data.get('lastUse')
                
        except Exception as e:
            logger.error(f"同步使用數據失敗: {e}")
    
    def _perform_security_checks(self):
        """執行安全檢查"""
        security_issues = []
        
        # 檢查無痕模式
        if st.session_state.get('is_incognito', False):
            security_issues.append("incognito_mode")
            logger.warning("檢測到無痕/隱私模式")
        
        # 檢查指紋異常
        if not st.session_state.get('fingerprint_data'):
            security_issues.append("no_fingerprint")
        
        # 檢查用戶ID合法性
        user_id = st.session_state.get('permanent_user_id', '')
        if not user_id or len(user_id) < 20:
            security_issues.append("invalid_user_id")
        
        # 記錄安全檢查結果
        st.session_state.security_checks = {
            'timestamp': time.time(),
            'issues': security_issues,
            'is_suspicious': len(security_issues) > 0
        }
        
        # 如果檢測到可疑行為，增加額外限制
        if len(security_issues) > 1:
            st.session_state.daily_limit = 1  # 降低每日限制
            logger.warning(f"檢測到多個安全問題: {security_issues}")
        else:
            st.session_state.daily_limit = 3  # 正常限制
    
    def _load_usage_data(self):
        """載入使用記錄"""
        try:
            # 清理過期數據
            self._clean_old_usage_data()
            
            # 確保daily_usage存在
            if 'daily_usage' not in st.session_state:
                st.session_state.daily_usage = {}
                
        except Exception as e:
            logger.error(f"載入使用記錄失敗: {e}")
    
    def _clean_old_usage_data(self):
        """清理過期的使用數據"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            dates_to_remove = []
            for date_str in st.session_state.daily_usage.keys():
                if date_str < cutoff_date:
                    dates_to_remove.append(date_str)
            
            for date_str in dates_to_remove:
                del st.session_state.daily_usage[date_str]
                logger.info(f"清理過期數據: {date_str}")
                
        except Exception as e:
            logger.error(f"清理過期數據失敗: {e}")
    
    def _check_quota_status(self):
        """檢查配額狀態"""
        user_id = st.session_state.permanent_user_id
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 檢查每日使用記錄
        if today not in st.session_state.daily_usage:
            st.session_state.daily_usage[today] = {}
        
        # 檢查用戶使用記錄
        user_usage = st.session_state.daily_usage[today].get(user_id, {
            'count': 0,
            'translations': [],
            'first_use': None,
            'last_use': None
        })
        
        # 獲取每日限制（可能因安全檢查而降低）
        daily_limit = st.session_state.get('daily_limit', 3)
        
        # 更新翻譯計數
        if user_usage['count'] >= daily_limit:
            st.session_state.translation_count = user_usage['count']
            st.session_state.is_quota_locked = True
            st.session_state.quota_lock_time = user_usage['last_use']
        else:
            if user_usage['count'] > 0:
                st.session_state.translation_count = user_usage['count']
    
    def can_use_translation(self) -> Tuple[bool, str]:
        """檢查是否可以使用翻譯服務"""
        user_id = st.session_state.permanent_user_id
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 檢查安全問題
        security_checks = st.session_state.get('security_checks', {})
        if security_checks.get('is_suspicious', False):
            issues = security_checks.get('issues', [])
            if 'incognito_mode' in issues:
                return False, "檢測到無痕/隱私模式。請使用正常瀏覽模式以使用免費服務。"
            elif len(issues) > 1:
                return False, "檢測到異常使用行為。請聯繫客服或升級付費版本。"
        
        # 獲取每日限制
        daily_limit = st.session_state.get('daily_limit', 3)
        
        # 檢查是否被鎖定
        if st.session_state.is_quota_locked:
            if today in st.session_state.daily_usage:
                user_usage = st.session_state.daily_usage[today].get(user_id, {})
                if user_usage.get('count', 0) >= daily_limit:
                    return False, f"您今日的免費額度已用完（{user_usage['count']}/{daily_limit}次）。明天再來或升級付費版本！"
            else:
                # 新的一天，解鎖
                st.session_state.is_quota_locked = False
                st.session_state.translation_count = 0
        
        # 檢查用戶每日使用量
        if today in st.session_state.daily_usage:
            user_usage = st.session_state.daily_usage[today].get(user_id, {})
            if user_usage.get('count', 0) >= daily_limit:
                return False, f"您今日的免費額度已用完（每個設備每天限{daily_limit}次）"
        
        # 檢查會話使用量
        if st.session_state.translation_count >= daily_limit:
            return False, "您的免費翻譯額度已用完"
        
        return True, "可以使用"
    
    def record_translation_usage(self, translation_id: str, text_hash: str):
        """記錄翻譯使用情況"""
        user_id = st.session_state.permanent_user_id
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = time.time()
        
        # 初始化今日記錄
        if today not in st.session_state.daily_usage:
            st.session_state.daily_usage[today] = {}
        
        # 初始化用戶記錄
        if user_id not in st.session_state.daily_usage[today]:
            st.session_state.daily_usage[today][user_id] = {
                'count': 0,
                'translations': [],
                'first_use': current_time,
                'last_use': current_time,
                'text_hashes': set()
            }
        
        user_usage = st.session_state.daily_usage[today][user_id]
        
        # 檢查是否重複翻譯相同內容
        if text_hash in user_usage.get('text_hashes', set()):
            logger.warning(f"檢測到重複翻譯相同內容: {text_hash[:8]}...")
            return
        
        # 記錄使用
        user_usage['count'] += 1
        user_usage['translations'].append({
            'id': translation_id,
            'time': current_time,
            'text_hash': text_hash
        })
        user_usage['last_use'] = current_time
        user_usage.setdefault('text_hashes', set()).add(text_hash)
        
        # 更新會話計數
        st.session_state.translation_count = user_usage['count']
        
        # 獲取每日限制
        daily_limit = st.session_state.get('daily_limit', 3)
        
        # 檢查是否需要鎖定
        if user_usage['count'] >= daily_limit:
            st.session_state.is_quota_locked = True
            st.session_state.quota_lock_time = current_time
            logger.info(f"用戶 {user_id[:16]}... 已達到每日限額")
        
        # 通知JavaScript更新localStorage
        self._update_javascript_usage(translation_id)
    
    def _update_javascript_usage(self, translation_id: str):
        """通知JavaScript更新使用記錄"""
        js_code = f"""
        <script>
        if (window.RadiAIUsageManager) {{
            window.RadiAIUsageManager.updateUsage('{translation_id}');
        }}
        </script>
        """
        components.html(js_code, height=0)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """獲取使用統計"""
        user_id = st.session_state.permanent_user_id
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 獲取每日限制
        daily_limit = st.session_state.get('daily_limit', 3)
        
        stats = {
            'session_count': st.session_state.translation_count,
            'user_id': user_id[:16] + "****" if user_id else "unknown",
            'is_locked': st.session_state.is_quota_locked,
            'today_usage': 0,
            'remaining': daily_limit,
            'daily_limit': daily_limit,
            'is_incognito': st.session_state.get('is_incognito', False),
            'security_issues': st.session_state.get('security_checks', {}).get('issues', [])
        }
        
        if today in st.session_state.daily_usage and user_id:
            user_usage = st.session_state.daily_usage[today].get(user_id, {})
            stats['today_usage'] = user_usage.get('count', 0)
            stats['remaining'] = max(0, daily_limit - user_usage.get('count', 0))
        else:
            stats['remaining'] = max(0, daily_limit - st.session_state.translation_count)
        
        return stats
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值"""
        # 正規化文本
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # 使用HMAC生成安全哈希
        return hmac.new(
            self.SECURITY_KEY.encode(),
            normalized.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_user_authenticity(self) -> bool:
        """驗證用戶真實性"""
        # 檢查多個因素
        checks = {
            'has_user_id': bool(st.session_state.get('permanent_user_id')),
            'has_fingerprint': bool(st.session_state.get('fingerprint_data')),
            'not_incognito': not st.session_state.get('is_incognito', False),
            'has_valid_session': st.session_state.get('session_initialized', False)
        }
        
        # 計算真實性分數
        authenticity_score = sum(1 for check in checks.values() if check)
        
        # 至少需要3個檢查通過
        return authenticity_score >= 3
    
    def get_user_profile(self) -> Dict[str, Any]:
        """獲取用戶檔案"""
        return {
            'user_id': st.session_state.get('permanent_user_id', 'unknown'),
            'device_fingerprint': st.session_state.get('fingerprint_data', {}),
            'usage_history': self._get_usage_history(),
            'security_status': st.session_state.get('security_checks', {}),
            'daily_limit': st.session_state.get('daily_limit', 3),
            'is_authenticated': self.verify_user_authenticity()
        }
    
    def _get_usage_history(self) -> Dict[str, Any]:
        """獲取使用歷史"""
        user_id = st.session_state.get('permanent_user_id')
        if not user_id:
            return {}
        
        history = {}
        for date, daily_data in st.session_state.daily_usage.items():
            if user_id in daily_data:
                history[date] = daily_data[user_id]
        
        return history
    
    def reset_daily_quota(self):
        """重置每日配額（僅用於測試）"""
        if st.session_state.get('dev_mode', False):
            today = datetime.now().strftime('%Y-%m-%d')
            user_id = st.session_state.permanent_user_id
            
            if today in st.session_state.daily_usage:
                if user_id and user_id in st.session_state.daily_usage[today]:
                    del st.session_state.daily_usage[today][user_id]
            
            st.session_state.translation_count = 0
            st.session_state.is_quota_locked = False
            st.session_state.quota_lock_time = None
            
            # 清除JavaScript端的記錄
            js_code = """
            <script>
            if (window.localStorage) {
                const today = new Date().toLocaleDateString('en-CA');
                const storageKey = `radiai_usage_${today}`;
                localStorage.removeItem(storageKey);
            }
            </script>
            """
            components.html(js_code, height=0)
            
            logger.info("每日配額已重置（測試模式）")r'\s+', ' ', text.strip().lower())
        # 移除標點符號
        normalized = re.sub(
