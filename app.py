# 完整的 app.py 修復代碼
# ===========================

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
        try:
            # 使用快取的 logo
            try:
                logo_data, mime_type = self.config.get_logo_base64()
                page_icon = self.config.APP_ICON
            except Exception as e:
                logger.warning(f"Logo 加載警告: {e}")
                page_icon = self.config.APP_ICON
            
            st.set_page_config(
                page_title=self.config.APP_TITLE,
                page_icon=page_icon,
                layout="centered",
                initial_sidebar_state="collapsed"
            )
            
            # 初始化會話狀態
            self.session_manager.init_session_state()
            
            # 載入 CSS
            st.markdown(CSS_STYLES, unsafe_allow_html=True)
            
            logger.info("應用初始化成功")
            
        except Exception as e:
            logger.error(f"應用初始化失敗: {e}")
            st.set_page_config(
                page_title="RadiAI.Care",
                page_icon="🏥",
                layout="centered"
            )
    
    def run(self):
        """運行主應用"""
        try:
            self.initialize()
            
            # 檢查配額狀態
            can_use, reason = self.session_manager.can_use_translation()
            
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
                usage_stats = self.session_manager.get_usage_stats()
                remaining = self.ui.render_usage_tracker_enhanced(lang, usage_stats)
                
                # 檢查是否可以使用服務
                if not can_use:
                    self.ui.render_quota_exceeded_enhanced(lang, reason)
                    # 仍然顯示底部資訊
                    self.ui.render_footer(lang)
                    self.ui.render_version_info()
                    st.markdown('</div>', unsafe_allow_html=True)
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
        try:
            # 1. 內容驗證
            validation_result = self.translator.validate_content(report_text)
            
            if not validation_result["is_valid"]:
                if len(report_text) < self.config.MIN_TEXT_LENGTH:
                    st.error("❌ 內容過短，請確保包含完整的醫學報告內容")
                    return
                elif len(validation_result["found_terms"]) < 2:
                    st.warning("⚠️ 內容中未發現明顯的醫學術語，請確認這是一份放射科報告")
                else:
                    st.warning(f"⚠️ {lang['warning_no_medical']}")
            
            # 2. 檢查配額
            can_use, reason = self.session_manager.can_use_translation()
            if not can_use:
                st.error(f"❌ {reason}")
                return
            
            # 3. 生成翻譯 ID
            translation_id = str(uuid.uuid4())
            text_hash = self.session_manager.generate_text_hash(report_text)
            
            # 4. 處理進度顯示
            with st.container():
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 記錄開始時間
                    start_time = time.time()
                    
                    # 執行翻譯
                    result = self.translator.translate_with_progress(
                        report_text, lang["code"], progress_bar, status_text
                    )
                    
                    if result["success"]:
                        # 顯示結果
                        self.ui.render_translation_result(result["content"], lang)
                        
                        # 記錄使用
                        self.session_manager.record_translation_usage(translation_id, text_hash)
                        
                        # 記錄到 Google Sheets
                        processing_time = int((time.time() - start_time) * 1000)
                        self._log_usage(
                            report_text, file_type, "success", translation_id, 
                            validation_result, processing_time=processing_time
                        )
                        
                        # 顯示完成狀態
                        updated_stats = self.session_manager.get_usage_stats()
                        self.ui.render_completion_status_enhanced(lang, updated_stats)
                        
                        # 渲染回饋區塊
                        self.feedback_manager.render_feedback_section(
                            lang, translation_id, report_text, file_type, validation_result
                        )
                        
                    else:
                        st.error(f"❌ {result.get('error', '翻譯過程中發生錯誤')}")
                        
                except Exception as e:
                    st.error(f"❌ 翻譯過程中發生錯誤: {str(e)}")
                    
                    self._log_usage(
                        report_text, file_type, "error", translation_id, 
                        validation_result, error=str(e)
                    )
                
                finally:
                    progress_bar.empty()
                    status_text.empty()
                    
        except Exception as e:
            st.error(f"❌ 處理翻譯請求時發生錯誤: {str(e)}")
            logger.exception("Translation handling error")
    
    def _log_usage(self, report_text: str, file_type: str, status: str, 
                   translation_id: str, validation_result: dict, 
                   error: str = None, processing_time: int = 0):
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
                'app_version': self.config.APP_VERSION,
                'latency_ms': processing_time,
                'session_id': st.session_state.get('user_session_id', 'unknown'),
                'device_id': st.session_state.get('device_id', 'unknown')
            }
            
            if error:
                log_data['error'] = error[:200]
                
            log_to_google_sheets(**log_data)
            
        except Exception as log_error:
            logger.warning(f"記錄使用情況失敗: {log_error}")
    
    def _handle_error(self, error: Exception):
        """處理應用錯誤"""
        logger.error(f"應用錯誤: {error}")
        
        st.error(f"❌ 應用運行時發生錯誤")
        
        with st.expander("🔧 故障排除", expanded=False):
            st.markdown(f"""
            ### 🔄 錯誤資訊：
            ```
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

def debug_feedback_in_app():
    """在應用中添加調試工具"""
    if st.sidebar.checkbox("🔧 顯示調試工具"):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 回饋調試")
        
        if st.sidebar.button("🔍 診斷回饋功能"):
            try:
                from log_to_sheets import GoogleSheetsLogger
                
                logger = GoogleSheetsLogger()
                if logger._initialize_client():
                    if logger.feedback_worksheet:
                        headers = logger.feedback_worksheet.row_values(1)
                        st.sidebar.success(f"✅ Feedback工作表連接正常")
                        st.sidebar.write(f"標題行: {len(headers)} 個欄位")
                        st.sidebar.write(f"前5個標題: {headers[:5]}")
                        
                        # 檢查現有數據
                        all_values = logger.feedback_worksheet.get_all_values()
                        st.sidebar.info(f"📊 總行數: {len(all_values)}")
                    else:
                        st.sidebar.error("❌ Feedback工作表不存在")
                else:
                    st.sidebar.error("❌ 無法連接Google Sheets")
            except Exception as e:
                st.sidebar.error(f"❌ 錯誤: {e}")
                st.sidebar.write(f"詳細錯誤: {str(e)}")
        
        if st.sidebar.button("🧪 測試回饋提交"):
            try:
                from log_to_sheets import log_feedback_to_sheets
                import time
                
                test_data = {
                    'translation_id': f'debug_test_{int(time.time())}',
                    'language': '简体中文',
                    'feedback_type': 'debug_test',
                    'sentiment': 'positive',
                    'clarity_score': 5,
                    'usefulness_score': 5,
                    'accuracy_score': 5,
                    'recommendation_score': 10,
                    'overall_satisfaction': 5.0,
                    'issues': '調試測試',
                    'suggestion': '調試建議',
                    'email': 'debug@test.com',
                    'report_length': 1000,
                    'file_type': 'manual',
                    'medical_terms_detected': 5,
                    'confidence_score': 0.85,
                    'app_version': 'v4.2-debug'
                }
                
                # 顯示要提交的數據
                st.sidebar.write("📤 提交數據:")
                st.sidebar.json(test_data)
                
                # 嘗試提交
                success = log_feedback_to_sheets(**test_data)
                
                if success:
                    st.sidebar.success("✅ 測試提交成功！")
                    st.sidebar.info(f"測試ID: {test_data['translation_id']}")
                else:
                    st.sidebar.error("❌ 測試提交失敗")
                    
            except Exception as e:
                st.sidebar.error(f"❌ 測試失敗: {e}")

def main():
    """主函數"""
    try:
        app = RadiAIApp()
        app.run()
        
        # 添加調試工具
        debug_feedback_in_app()
        
    except Exception as e:
        # 最後的錯誤處理
        st.error("🚨 應用啟動失敗")
        st.exception(e)
        
        st.markdown("""
        ### 🆘 緊急恢復步驟：
        
        1. **檢查文件結構**：確保所有必要文件都存在
        2. **檢查環境變量**：確保 OPENAI_API_KEY 和 GOOGLE_SHEET_SECRET_B64 已設置
        3. **檢查依賴包**：運行 `pip install -r requirements.txt`
        4. **聯繫支援**：發送錯誤信息至 support@radiai.care
        """)

if __name__ == "__main__":
    main()
