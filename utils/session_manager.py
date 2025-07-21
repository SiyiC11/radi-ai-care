"""
RadiAI.Care ‒ SessionManager (強化版)
===================================
‧ 追蹤每日免費額度，防連刷
‧ 端到端 JS ⇄ Python 溝通（LocalStorage 與 Browser Fingerprint）
‧ 基本安全檢查：無痕模式、指紋缺失、多重異常即降額
"""
from pathlib import Path        # ← 新增

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)


class SessionManager:
    """增強版會話狀態管理器"""

    # ──────────────────────────
    # 預設 Session State 欄位
    # ──────────────────────────
    DEFAULT_VALUES: Dict[str, Any] = {
        "language": "简体中文",
        "translation_count": 0,
        "input_method": "text",
        "feedback_submitted_ids": set(),
        "last_translation_id": None,
        "user_session_id": lambda: str(uuid.uuid4())[:8],
        "app_start_time": lambda: time.time(),
        "translation_history": list,
        "last_activity": lambda: time.time(),
        "browser_fingerprint": None,
        "device_id": None,
        "permanent_user_id": None,
        "used_translations": dict,
        "daily_usage": dict,
        "is_quota_locked": False,
        "quota_lock_time": None,
        "session_initialized": False,
        "fingerprint_data": dict,
        "security_checks": dict,
        "js_initialized": False,
    }

    # 伺服器端 HMAC 密鑰（正式環境請改用環境變數）
    SECURITY_KEY = "radiai_2024_security_key"

    # --------------------------------------------------------------------- #
    # 初始化                                                                 #
    # --------------------------------------------------------------------- #
    def __init__(self) -> None:
        self.storage_key = "radiai_usage_data"
        self.user_id_key = "radiai_permanent_user_id"
        self.daily_usage_key = "radiai_daily_usage"

    def init_session_state(self) -> None:
        """一步到位：初始化所有 Session 欄位 + JS 橋接 + 安全檢查"""

        if not st.session_state.get("session_initialized", False):
            for k, default in self.DEFAULT_VALUES.items():
                st.session_state[k] = default() if callable(default) else default
            st.session_state.session_initialized = True

        # 注入 JS（一次即可）
        if not st.session_state.get("js_initialized", False):
            self._inject_javascript_bridge()
            st.session_state.js_initialized = True

        # 後續流程
        self._collect_device_fingerprint()
        self._init_permanent_user_id()
        self._load_usage_data()
        self._perform_security_checks()
        self._check_quota_status()

    # --------------------------------------------------------------------- #
    # JavaScript 通信橋接                                                    #
    # --------------------------------------------------------------------- #
    def _inject_javascript_bridge(self) -> None:
        """將防濫用 JS 代碼注入到目前頁面（高度 0，不佔版面）"""
        js_code = Path(__file__).with_name("usage_bridge.js").read_text(encoding="utf-8")
        components.html(js_code, height=0)  # type: ignore

    # --------------------------------------------------------------------- #
    # 收集與同步瀏覽器端資料                                                 #
    # --------------------------------------------------------------------- #
    def _collect_device_fingerprint(self) -> None:
        """透過隱藏 input 值取得 JS 傳回的 Base64 資料並同步到 session"""
        data_b64: str = st.session_state.get("radiai_data_bridge_value", "")
        if not data_b64:
            return

        try:
            decoded = base64.b64decode(data_b64).decode("utf-8")
            payload = json.loads(decoded)

            st.session_state.permanent_user_id = payload["permanentUserId"]
            st.session_state.fingerprint_data = payload["browserFingerprint"]
            st.session_state.is_incognito = payload.get("isIncognito", False)

            self._sync_usage_data(payload["dailyUsage"])
            logger.info(f"已同步設備指紋與日用量，UID={payload['permanentUserId'][:16]}…")
        except Exception as e:
            logger.error(f"解析 JS 指紋資料失敗: {e}")

    def _sync_usage_data(self, js_daily_usage: Dict[str, Any]) -> None:
        """把 LocalStorage 的同日使用量同步到 Server 端"""
        today = datetime.now().strftime("%Y-%m-%d")
        st.session_state.daily_usage.setdefault(today, {})
        st.session_state.daily_usage[today][
            st.session_state.permanent_user_id
        ] = js_daily_usage

        st.session_state.translation_count = js_daily_usage.get("count", 0)
        daily_limit = st.session_state.get("daily_limit", 3)
        if js_daily_usage.get("count", 0) >= daily_limit:
            st.session_state.is_quota_locked = True

    # --------------------------------------------------------------------- #
    # 永久 UID 產生／回收                                                    #
    # --------------------------------------------------------------------- #
    def _init_permanent_user_id(self) -> None:
        """優先從 URL 參數拿 UID，否則候補 JS 回傳；都沒有就自生一個"""
        if st.session_state.permanent_user_id:
            return

        uid_from_url = st.experimental_get_query_params().get("uid", [None])[0]
        if uid_from_url:
            st.session_state.permanent_user_id = uid_from_url
            logger.info(f"UID 來源：URL 參數 {uid_from_url}")
            return

        # 先給一個暫時 ID，待 JS 覆寫
        st.session_state.permanent_user_id = self._generate_secure_user_id()
        logger.info("已產生暫時 UID（等待 JS 覆寫）")

    def _generate_secure_user_id(self) -> str:
        """用 SHA‑256 雜湊組合時間戳 + UUID + Secret 產生 16 碼 UID"""
        raw = f"{time.time()}_{uuid.uuid4()}_{self.SECURITY_KEY}"
        return f"uid_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    # --------------------------------------------------------------------- #
    # 使用量與安全檢查                                                      #
    # --------------------------------------------------------------------- #
    def _load_usage_data(self) -> None:
        """清理七日前的舊紀錄，確保 daily_usage 結構存在"""
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        st.session_state.daily_usage = {
            d: v
            for d, v in st.session_state.daily_usage.items()
            if d >= cutoff
        }

    def _perform_security_checks(self) -> None:
        """無痕模式 / 指紋缺失 皆算可疑；多重異常者降日額"""
        issues = []

        if st.session_state.get("is_incognito"):
            issues.append("incognito_mode")
        if not st.session_state.get("fingerprint_data"):
            issues.append("no_fingerprint")
        if (
            not st.session_state.get("permanent_user_id")
            or len(st.session_state.permanent_user_id) < 20
        ):
            issues.append("invalid_uid")

        st.session_state.security_checks = {
            "timestamp": time.time(),
            "issues": issues,
            "is_suspicious": bool(issues),
        }

        st.session_state.daily_limit = 1 if len(issues) > 1 else 3

    def _check_quota_status(self) -> None:
        """根據已使用量與每日限額，判定是否鎖定"""
        today = datetime.now().strftime("%Y-%m-%d")
        uid = st.session_state.permanent_user_id
        usage = st.session_state.daily_usage.get(today, {}).get(uid, {})
        used = usage.get("count", 0)
        limit = st.session_state.get("daily_limit", 3)

        if used >= limit:
            st.session_state.is_quota_locked = True
            st.session_state.translation_count = used

    # --------------------------------------------------------------------- #
    # Public API                                                            #
    # --------------------------------------------------------------------- #
    def can_use_translation(self) -> Tuple[bool, str]:
        """回傳 (可否使用, 訊息)"""
        if st.session_state.security_checks.get("is_suspicious"):
            return False, "偵測到瀏覽器異常，請使用正常模式或聯絡客服。"

        if st.session_state.is_quota_locked:
            return False, "今日免費額度已用完，請明日再來或升級付費方案。"

        return True, "OK"

    def record_translation_usage(self, translation_id: str, text_hash: str) -> None:
        """完成一次翻譯後記錄並同步 JS"""
        today = datetime.now().strftime("%Y-%m-%d")
        uid = st.session_state.permanent_user_id
        limit = st.session_state.get("daily_limit", 3)

        st.session_state.daily_usage.setdefault(today, {}).setdefault(
            uid,
            {
                "count": 0,
                "translations": [],
                "first_use": time.time(),
                "last_use": time.time(),
                "text_hashes": set(),
            },
        )

        usage = st.session_state.daily_usage[today][uid]

        if text_hash in usage["text_hashes"]:
            logger.warning("重複翻譯相同內容，忽略計數")
            return

        usage["count"] += 1
        usage["translations"].append({"id": translation_id, "time": time.time()})
        usage["last_use"] = time.time()
        usage["text_hashes"].add(text_hash)
        st.session_state.translation_count = usage["count"]

        if usage["count"] >= limit:
            st.session_state.is_quota_locked = True

        # 呼叫 JS 更新 localStorage
        self._update_js_usage(translation_id)

    def generate_text_hash(self, text: str) -> str:
        """產生內容雜湊值（去符號、壓小寫、壓空白）"""
        normalized = re.sub(r"[^\w\s]", "", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return hmac.new(
            self.SECURITY_KEY.encode(), normalized.encode(), hashlib.sha256
        ).hexdigest()

    def get_usage_stats(self) -> Dict[str, Any]:
        """回傳前端可顯示的基本統計"""
        today = datetime.now().strftime("%Y-%m-%d")
        uid = st.session_state.permanent_user_id
        usage = st.session_state.daily_usage.get(today, {}).get(uid, {})

        limit = st.session_state.get("daily_limit", 3)
        used = usage.get("count", 0)

        return {
            "today_used": used,
            "remaining": max(0, limit - used),
            "limit": limit,
            "session_used": st.session_state.translation_count,
            "is_locked": st.session_state.is_quota_locked,
        }

    # --------------------------------------------------------------------- #
    # Internal helpers                                                      #
    # --------------------------------------------------------------------- #
    def _update_js_usage(self, translation_id: str) -> None:
        """呼叫前端函式 `updateUsage`"""
        components.html(
            f"""
            <script>
            window.RadiAIUsageManager && window.RadiAIUsageManager.updateUsage('{translation_id}');
            </script>
            """,
            height=0,
        )
