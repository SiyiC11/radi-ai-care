import os
import time
import uuid
import streamlit as st

from config.settings import AppConfig, UIText, CSS_STYLES
from utils.session_manager import SessionManager
from utils.file_handler import FileHandler
from utils.translator import Translator
from components.ui_components import UIComponents
from feedback_manager import FeedbackManager  # ✅ 改為新版
from log_to_sheets import UsageLogger         # ✅ 使用新版 Usage 記錄器（可選）

# 初始化應用配置與元件
config = AppConfig()
session_manager = SessionManager()
file_handler = FileHandler()
translator = Translator()
ui = UIComponents()

# 取得 Feedback Sheet ID
sheet_id = st.secrets.get("feedback_sheet_id", os.getenv("FEEDBACK_SHEET_ID", ""))
feedback_manager = FeedbackManager(sheet_id)
usage_logger = UsageLogger(sheet_id)  # ✅ 可選，未整合 logUsage 可先不用

# Streamlit 頁面配置
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# 初始化 Session State
session_manager.init_session_state()

# 語言設定
lang_cfg = UIText.get_language_config(st.session_state.language)

# 標題與語言選擇
ui.render_header(lang_cfg)
ui.render_language_selection(lang_cfg)
lang_cfg = UIText.get_language_config(st.session_state.language)
ui.render_disclaimer(lang_cfg)

# 顯示配額狀態
usage_stats = session_manager.get_usage_stats()
can_use, reason = session_manager.can_use_translation()
remaining = ui.render_usage_tracker_enhanced(lang_cfg, usage_stats)

if not can_use:
    ui.render_quota_exceeded_enhanced(lang_cfg, reason)
    ui.render_footer(lang_cfg)
    ui.render_version_info()
    st.stop()

# 輸入報告
report_text, file_type = ui.render_input_section(lang_cfg)

# 按鈕觸發翻譯
if ui.render_translate_button(lang_cfg, report_text):
    translation_id = str(uuid.uuid4())
    text_hash = session_manager.generate_text_hash(report_text)
    session_manager.record_translation_usage(translation_id, text_hash)

    # 驗證內容
    validation = translator.validate_content(report_text)
    if not validation["is_valid"]:
        st.warning("⚠️ 無法確認內容為有效放射科報告，請再確認")

    # 翻譯進度條
    with st.container():
        bar = st.progress(0)
        status = st.empty()
        try:
            start = time.time()
            result = translator.translate_with_progress(report_text, lang_cfg["code"], bar, status)
            latency_ms = int((time.time() - start) * 1000)

            if result["success"]:
                st.success("✅ 翻譯完成")
                ui.render_translation_result(result["content"], lang_cfg)
                ui.render_completion_status_enhanced(lang_cfg, session_manager.get_usage_stats())

                # 顯示 Feedback 表單
                feedback_manager.render(
                    translation_id=translation_id,
                    language=lang_cfg["code"],
                    file_type=file_type,
                    device=st.session_state.get("device_type", "unknown"),
                    extra={
                        "confidence": validation.get("confidence"),
                        "terms": validation.get("found_terms", []),
                        "version": config.APP_VERSION,
                    },
                )

            else:
                session_manager.restore_usage_on_failure(translation_id)
                st.error("❌ 翻譯失敗，請稍後重試")
        except Exception as e:
            session_manager.restore_usage_on_failure(translation_id)
            st.error(f"❌ 發生錯誤: {e}")
        finally:
            bar.empty()
            status.empty()

# 底部資訊
ui.render_footer(lang_cfg)
ui.render_version_info()
