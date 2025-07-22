print("✅ FeedbackManager loaded")
from __future__ import annotations
from typing import Optional

import streamlit as st
from log_to_sheets import FeedbackLogger


class FeedbackManager:
    """
    Streamlit wrapper for rendering a feedback form and saving it via Google Sheets.
    """

    def __init__(self, sheet_id: str):
        self._logger = FeedbackLogger(sheet_id)

    def render(
        self,
        translation_id: str,
        *,
        user_id: str | None = None,
        language: str = "zh_TW",
        file_type: str = "text",
        device: str = "",
        extra: str | dict = "",
    ) -> None:
        """
        Renders a feedback form and persists the result to Google Sheets.

        After a successful submission, the form is disabled for that session.
        """
        key_prefix = f"fb_{translation_id}"
        if st.session_state.get(f"{key_prefix}_done"):
            st.success("🙏 感謝您的回饋！")
            return

        with st.form(key=f"{key_prefix}_form"):
            st.write("### 回饋意見 (Feedback)")
            feedback_text = st.text_area("請留下任何建議或錯誤回報…", height=160)
            submitted = st.form_submit_button("送出回饋")

        if not submitted:
            return

        # 確保 extra 是 string
        if isinstance(extra, dict):
            import json
            extra = json.dumps(extra, ensure_ascii=False)

        payload = {
            "translation_id": translation_id,
            "user_id": user_id or "",
            "language": language,
            "file_type": file_type,
            "device": device,
            "feedback_text": feedback_text.strip(),
            "extra": extra,
        }

        ok = self._logger.log_feedback(**payload)
        if ok:
            st.success("✅ 已成功記錄至 Google Sheet")
            st.session_state[f"{key_prefix}_done"] = True
        else:
            st.error("❌ 寫入失敗，請稍後再試或聯絡開發者。")
