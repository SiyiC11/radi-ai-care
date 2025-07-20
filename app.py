import streamlit as st
import time
import logging
import uuid
from typing import Optional, Tuple

# 導入自定義模組
from config.settings import AppConfig, UIText, CSS_STYLES
from utils.session_manager import SessionManager
from utils.file_handler import FileHandler
from utils.translator import Translator
from utils.feedback_manager import FeedbackManager
from components.ui_components import UIComponents
from log_to_sheets import log_to_google_sheets

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RadiAIApp:
    """RadiAI.Care 主應用類"""
    
    def __init__(self):
        self.config = AppConfig()
        self.session_manager = SessionManager()
        self.file_handler = FileHandler()
        self.translator = Translator()
        self.feedback_manager = FeedbackManager()
        self.ui = UIComponents()
        
    def initialize(self):
        """初始化應用"""
        # 頁面配置
        st.set_page_config(
            page_title=self.config.APP_TITLE,
            page_icon=self.config.APP_ICON,
            layout="centered",
            initial_sidebar_state="collapsed"
        )
        
        # 初始化會話狀態
        self.session_manager.init_session_state()
        
        # 載入 CSS
        st.markdown(CSS_STYLES, unsafe_allow_html=True)
    
    def run(self):
        """運行主應用"""
        try:
            self.initialize()
            
            # 獲取當前語言配置
            lang = UIText.get_language_config(st.session_state.language)
            
            # 主容器
            with st.container():
                st.markdown('<div class="main-container">', unsafe_allow_html=True)
                
                # 渲染標題和 Logo
                self.ui.render_header(lang)
                
                # 語言選擇
                self.ui.render_language_selection(lang)
                
                # 更新語言配置
                lang = UIText.get_language_config(st.session_state.language)
                
                # 法律聲明
                self.ui.render_disclaimer(lang)
                
                # 使用次數追蹤
                remaining = self.ui.render_usage_tracker(lang)
                
                # 檢查額度
                if remaining <= 0:
                    self.ui.render_quota_exceeded(lang)
                    return
                
                # 輸入區塊
                report_text, file_type = self.ui.render_input_section(lang)
                
                # 翻譯按鈕和處理
                if self.ui.render_translate_button(lang, report_text):
                    self._handle_translation(report_text, file_type, lang)
                
                # 底部資訊
                self.ui.render_footer(lang)
                
                # 版本資訊
                self.ui.render_version_info()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            self._handle_error(e)
    
    def _handle_translation(self, report_text: str, file_type: str, lang: dict):
        """處理翻譯請求"""
        # 內容驗證
        validation_result = self.translator.validate_content(report_text)
        
        if not validation_result["is_valid"]:
            st.warning(f"⚠️ {lang['warning_no_medical']}")
        
        # 生成翻譯 ID
        translation_id = str(uuid.uuid4())
        
        # 處理進度顯示
        with st.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 執行翻譯
                result = self.translator.translate_with_progress(
                    report_text, lang["code"], progress_bar, status_text
                )
                
                if result["success"]:
                    # 顯示結果
                    self.ui.render_translation_result(result["content"], lang)
                    
                    # 更新計數器
                    st.session_state.translation_count += 1
                    st.session_state.last_translation_id = translation_id
                    
                    # 記錄使用情況
                    self._log_usage(report_text, file_type, "success", translation_id, validation_result)
                    
                    # 顯示完成狀態
                    remaining = self.config.MAX_FREE_TRANSLATIONS - st.session_state.translation_count
                    self.ui.render_completion_status(lang, remaining)
                    
                    # 渲染回饋區塊
                    self.feedback_manager.render_feedback_section(
                        lang, translation_id, report_text, file_type, validation_result
                    )
                    
                else:
                    st.error(f"❌ {result['error']}")
                    self._log_usage(report_text, file_type, "error", translation_id, validation_result, result['error'])
                    
            except Exception as e:
                st.error(f"❌ 翻譯過程中發生錯誤：{str(e)}")
                self._log_usage(report_text, file_type, "error", translation_id, validation_result, str(e))
            
            finally:
                progress_bar.empty()
                status_text.empty()
    
    def _log_usage(self, report_text: str, file_type: str, status: str, 
                   translation_id: str, validation_result: dict, error: str = None):
        """記錄使用情況"""
        try:
            log_data = {
                'language': st.session_state.language,
                'report_length': len(report_text),
                'file_type': file_type,
                'processing_status': status,
                'translation_id': translation_id,
                'medical_terms_count': len(validation_result.get('found_terms', [])),
                'confidence_score': validation_result.get('confidence', 0),
                'app_version': self.config.APP_VERSION
            }
            
            if error:
                log_data['error'] = error
                
            log_to_google_sheets(**log_data)
            
        except Exception as log_error:
            logger.warning(f"記錄使用情況失敗: {log_error}")
    
    def _handle_error(self, error: Exception):
        """處理應用錯誤"""
        logger.error(f"應用錯誤: {error}")
        st.error("❌ 應用程式發生錯誤")
        
        with st.expander("🔧 故障排除", expanded=False):
            st.markdown(f"""
            ### 🔄 錯誤資訊：
            ```
            錯誤類型: {type(error).__name__}
            錯誤描述: {str(error)}
            時間戳記: {time.strftime('%Y-%m-%d %H:%M:%S')}
            應用版本: {self.config.APP_VERSION}
            ```
            
            ### 🛠 解決方案：
            1. **重新整理頁面**：按 F5 或點擊瀏覽器重新整理按鈕
            2. **清除瀏覽器快取**：Ctrl+Shift+Delete 清除快取
            3. **稍後重試**：等待 1-2 分鐘後重新嘗試
            4. **檢查網路連線**：確保網路連線穩定
            5. **聯繫技術支援**：發送錯誤資訊至 support@radiai.care
            """)

def main():
    """主函數"""
    app = RadiAIApp()
    app.run()

if __name__ == "__main__":
    main()
