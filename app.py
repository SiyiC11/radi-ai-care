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
        try:
            # 嘗試獲取 logo 用於頁面圖標
            try:
                logo_data, mime_type = self.config.get_logo_base64()
                # 如果是圖片格式，不能直接用作頁面圖標，使用默認
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
            # 提供最小初始化
            st.set_page_config(
                page_title="RadiAI.Care",
                page_icon="🏥",
                layout="centered"
            )
    
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
                
                # 開發模式：顯示 Logo 調試信息
                if st.secrets.get("DEBUG_MODE", False):
                    self.ui.render_logo_debug_info()
                
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
            
            ### 🔍 系統檢查：
            """)
            
            # 系統狀態檢查
            self._render_system_status()
    
    def _render_system_status(self):
        """渲染系統狀態檢查"""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔧 組件狀態：**")
                
                # 檢查各個組件
                components_status = {
                    "配置模塊": self._check_config(),
                    "翻譯引擎": self._check_translator(),
                    "文件處理": self._check_file_handler(),
                    "UI 組件": self._check_ui_components(),
                    "Logo 文件": self._check_logo()
                }
                
                for component, status in components_status.items():
                    status_icon = "✅" if status else "❌"
                    st.text(f"{status_icon} {component}")
            
            with col2:
                st.markdown("**🌐 網路狀態：**")
                
                # 檢查網路相關
                network_status = {
                    "OpenAI 連接": self._check_openai_connection(),
                    "Google Sheets": self._check_google_sheets(),
                    "環境變量": self._check_environment()
                }
                
                for service, status in network_status.items():
                    status_icon = "✅" if status else "❌"
                    st.text(f"{status_icon} {service}")
                    
        except Exception as e:
            st.error(f"系統檢查失敗: {e}")
    
    def _check_config(self) -> bool:
        """檢查配置模塊"""
        try:
            return hasattr(self.config, 'APP_TITLE') and hasattr(self.config, 'MEDICAL_KEYWORDS')
        except:
            return False
    
    def _check_translator(self) -> bool:
        """檢查翻譯引擎"""
        try:
            return hasattr(self.translator, 'client') and self.translator.client is not None
        except:
            return False
    
    def _check_file_handler(self) -> bool:
        """檢查文件處理器"""
        try:
            return hasattr(self.file_handler, 'supported_types')
        except:
            return False
    
    def _check_ui_components(self) -> bool:
        """檢查 UI 組件"""
        try:
            return hasattr(self.ui, 'render_header')
        except:
            return False
    
    def _check_logo(self) -> bool:
        """檢查 Logo 文件"""
        try:
            logo_data, mime_type = self.config.get_logo_base64()
            return len(logo_data) > 0
        except:
            return False
    
    def _check_openai_connection(self) -> bool:
        """檢查 OpenAI 連接"""
        try:
            import os
            return bool(os.getenv("OPENAI_API_KEY"))
        except:
            return False
    
    def _check_google_sheets(self) -> bool:
        """檢查 Google Sheets 連接"""
        try:
            import os
            return bool(os.getenv("GOOGLE_SHEET_SECRET_B64"))
        except:
            return False
    
    def _check_environment(self) -> bool:
        """檢查環境變量"""
        try:
            import os
            required_vars = ["OPENAI_API_KEY", "GOOGLE_SHEET_SECRET_B64"]
            return all(os.getenv(var) for var in required_vars)
        except:
            return False

def main():
    """主函數"""
    try:
        app = RadiAIApp()
        app.run()
    except Exception as e:
        # 最後的錯誤處理
        st.error("🚨 應用啟動失敗")
        st.exception(e)
        
        st.markdown("""
        ### 🆘 緊急恢復步驟：
        
        1. **檢查文件結構**：確保所有必要文件都存在
        2. **檢查環境變量**：確保 OPENAI_API_KEY 和 GOOGLE_SHEET_SECRET_B64 已設置
        3. **檢查依賴包**：運行 `pip install -r requirements.txt`
        4. **檢查 Logo 文件**：確保 assets/llogo 文件存在且可讀
        5. **聯繫支援**：發送錯誤信息至 support@radiai.care
        
        ### 🔍 快速診斷：
        """)
        
        # 簡單的文件結構檢查
        import os
        from pathlib import Path
        
        required_files = [
            "config/settings.py",
            "utils/translator.py", 
            "utils/file_handler.py",
            "components/ui_components.py",
            "log_to_sheets.py"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                st.success(f"✅ {file_path}")
            else:
                st.error(f"❌ {file_path} - 文件缺失")
        
        # Logo 文件檢查
        logo_paths = ["assets/llogo", "assets/llogo.png", "llogo", "llogo.png"]
        logo_found = False
        for logo_path in logo_paths:
            if Path(logo_path).exists():
                st.success(f"✅ Logo: {logo_path}")
                logo_found = True
                break
        
        if not logo_found:
            st.warning("⚠️ Logo 文件未找到，將使用默認圖標")

if __name__ == "__main__":
    main()
