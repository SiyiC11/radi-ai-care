import streamlit as st
from typing import Callable

# 你可以把 GoogleSheetsLogger 放在另一個檔案，這裡示範直接 import
# from log_to_sheets import GoogleSheetsLogger


class FeedbackManager:
    """封裝 Streamlit UI 與 GoogleSheet 寫入流程。"""

    def __init__(self, logger: GoogleSheetsLogger):
        self.logger = logger

    def render_feedback_section(
        self,
        translation_id: str,
        file_type: str,
        device_type: str,
        user_agent: str,
        extra_builder: Optional[Callable[[], dict]] = None,
        key_suffix: str = "",
    ):
        """在頁面上渲染回饋表單。"""
        form_key = f"feedback_form_{translation_id}_{key_suffix}"
        sent_key = f"feedback_sent_{translation_id}_{key_suffix}"

        if st.session_state.get(sent_key):
            st.info("你已提交過此筆回饋，感謝！")
            return

        with st.form(key=form_key):
            feedback_text = st.text_area("留下你的意見或建議", key=f"feedback_text_{translation_id}_{key_suffix}")
            lang = st.selectbox("語言", ["繁體中文", "简体中文"], index=0, key=f"feedback_lang_{translation_id}_{key_suffix}")
            submitted = st.form_submit_button("送出回饋")

        if submitted:
            payload = {
                "translation_id": translation_id,
                "feedback_text": feedback_text,
                "language": lang,
                "file_type": file_type,
                "device_type": device_type,
                "user_agent": user_agent,
            }
            if extra_builder:
                try:
                    payload["extra"] = extra_builder() or {}
                except Exception:
                    payload["extra"] = {"extra_error": "extra_builder failed"}

            ok, err = self.logger.append_feedback(payload)
            if ok:
                st.success("✅ 已成功寫入 Google Sheet")
                st.session_state[sent_key] = True
            else:
                st.error("❌ 寫入失敗，請稍後再試")
                with st.expander("錯誤細節 (debug)"):
                    st.code(err or self.logger.last_error)

    def render_diagnose_block(self):
        """顯示診斷資訊，方便 debug。"""
        st.subheader("🩺 Google Sheet 診斷")
        info = self.logger.diagnose()
        st.json(info)
