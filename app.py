# 完整的 app.py 修復代碼 - 包含延遲測試
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
        """處理翻譯請求 - 修復版含延遲測試"""
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
            
            # 2. 檢查配額（基於 UsageLog Sheet）
            can_use, reason = self.session_manager.can_use_translation()
            if not can_use:
                st.error(f"❌ {reason}")
                return
            
            # 3. 生成翻譯 ID
            translation_id = str(uuid.uuid4())
            text_hash = self.session_manager.generate_text_hash(report_text)
            
            # 4. 樂觀更新本地狀態（實際記錄在翻譯成功後）
            self.session_manager.record_translation_usage(translation_id, text_hash)
            
            # 5. 顯示更新後的使用次數
            updated_stats = self.session_manager.get_usage_stats()
            remaining_after_deduction = updated_stats['remaining']
            
            if lang["code"] == "traditional_chinese":
                deduction_msg = f"✅ 已開始翻譯！剩餘使用次數：{remaining_after_deduction}"
            else:
                deduction_msg = f"✅ 已开始翻译！剩余使用次数：{remaining_after_deduction}"
            
            st.success(deduction_msg)
            
            # 6. 重新渲染更新後的使用量追蹤器
            st.markdown("### 📊 更新後使用狀況")
            self.ui.render_usage_tracker_enhanced(lang, updated_stats)
            
            # 7. 處理進度顯示和翻譯
            with st.container():
                progress_bar = st.progress(0)
                status_text = st.empty()
                translation_success = False
                
                try:
                    # 記錄開始時間
                    start_time = time.time()
                    
                    # 執行翻譯
                    result = self.translator.translate_with_progress(
                        report_text, lang["code"], progress_bar, status_text
                    )
                    
                    if result["success"]:
                        # 翻譯成功 - 記錄到 UsageLog
                        processing_time = int((time.time() - start_time) * 1000)
                        usage_logged = self._log_usage_to_sheets(
                            report_text, file_type, "success", translation_id, 
                            validation_result, processing_time=processing_time
                        )
                        
                        if not usage_logged:
                            logger.warning("使用記錄到 UsageLog 失敗，但翻譯繼續")
                        
                        # ===== 🧪 延遲測試 =====
                        st.info("⏳ 延遲測試：等待 5 秒後再渲染回饋區塊...")
                        time.sleep(5)  # 等待 5 秒
                        logger.info("延遲測試：UsageLog 寫入後等待 5 秒完成")
                        st.success("✅ 延遲完成，現在可以提交回饋")
                        # ===== 延遲測試結束 =====
                        
                        # 顯示翻譯結果
                        self.ui.render_translation_result(result["content"], lang)
                        
                        # 顯示完成狀態
                        final_stats = self.session_manager.get_usage_stats()
                        self.ui.render_completion_status_enhanced(lang, final_stats)
                        
                        # 渲染回饋區塊
                        self.feedback_manager.render_feedback_section(
                            lang, translation_id, report_text, file_type, validation_result
                        )
                        
                        translation_success = True
                        
                    else:
                        # 翻譯失敗 - 恢復使用次數並記錄錯誤
                        self._restore_usage_on_failure(translation_id)
                        st.error(f"❌ {result.get('error', '翻譯過程中發生錯誤')}")
                        
                        # 記錄失敗到 UsageLog
                        self._log_usage_to_sheets(
                            report_text, file_type, "error", translation_id, 
                            validation_result, error=result.get('error', '未知錯誤')
                        )
                        
                except Exception as e:
                    # 翻譯異常 - 恢復使用次數並記錄錯誤
                    self._restore_usage_on_failure(translation_id)
                    st.error(f"❌ 翻譯過程中發生錯誤: {str(e)}")
                    
                    # 記錄異常到 UsageLog
                    self._log_usage_to_sheets(
                        report_text, file_type, "error", translation_id, 
                        validation_result, error=str(e)
                    )
                
                finally:
                    progress_bar.empty()
                    status_text.empty()
                    
                    # 如果翻譯失敗，強制同步使用次數
                    if not translation_success:
                        self.session_manager.force_sync_usage()
                    
        except Exception as e:
            st.error(f"❌ 處理翻譯請求時發生錯誤: {str(e)}")
            logger.exception("Translation handling error")
    
    def _restore_usage_on_failure(self, translation_id: str):
        """翻譯失敗時恢復使用次數 - 修復版"""
        try:
            # 調用 session manager 的恢復方法
            self.session_manager.restore_usage_on_failure(translation_id)
            
            # 顯示恢復訊息
            st.info("✅ 翻譯失敗，使用次數已恢復")
            
            logger.info(f"已恢復使用次數: {translation_id}")
            
        except Exception as e:
            logger.error(f"恢復使用次數失敗: {e}")
    
    def _log_usage_to_sheets(self, report_text: str, file_type: str, status: str, 
                           translation_id: str, validation_result: dict, 
                           error: str = None, processing_time: int = 0) -> bool:
        """記錄使用情況到 UsageLog Sheet"""
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
                
            # 使用修復版的記錄函數
            success = log_to_google_sheets(**log_data)
            
            if success:
                logger.info(f"使用記錄到 UsageLog 成功: {status}")
            else:
                logger.error(f"使用記錄到 UsageLog 失敗: {status}")
                
            return success
            
        except Exception as log_error:
            logger.warning(f"記錄使用情況失敗: {log_error}")
            return False
    
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
    """在應用中添加調試工具 - 增強版"""
    if st.sidebar.checkbox("🔧 顯示調試工具"):
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 系統診斷")
        
        # 使用次數同步測試
        if st.sidebar.button("🔄 強制同步使用次數"):
            try:
                from utils.session_manager import SessionManager
                session_manager = SessionManager()
                session_manager.force_sync_usage()
                st.sidebar.success("✅ 使用次數已同步")
                
                # 顯示同步後的信息
                stats = session_manager.get_usage_stats()
                st.sidebar.json(stats)
                
            except Exception as e:
                st.sidebar.error(f"❌ 同步失敗: {e}")
        
        # 回饋系統診斷
        if st.sidebar.button("🔍 診斷回饋系統"):
            try:
                from log_to_sheets import diagnose_feedback_system
                
                diagnosis = diagnose_feedback_system()
                st.sidebar.success("✅ 診斷完成")
                
                # 顯示關鍵信息
                if diagnosis.get("worksheet_available"):
                    st.sidebar.info("Feedback 工作表可用")
                else:
                    st.sidebar.error("❌ Feedback 工作表不可用")
                
                with st.sidebar.expander("詳細診斷"):
                    st.json(diagnosis)
                    
            except Exception as e:
                st.sidebar.error(f"❌ 診斷失敗: {e}")
        
        # 終極回饋測試
        if st.sidebar.button("🧪 終極回饋測試"):
            try:
                from log_to_sheets import test_feedback_logging_ultimate
                
                with st.spinner("執行終極測試..."):
                    results = test_feedback_logging_ultimate()
                
                success_count = sum(1 for r in results["results"] if r.get("success"))
                total_count = len(results["results"])
                
                if success_count == total_count:
                    st.sidebar.success(f"✅ 所有測試通過 ({success_count}/{total_count})")
                else:
                    st.sidebar.warning(f"⚠️ 部分測試失敗 ({success_count}/{total_count})")
                
                with st.sidebar.expander("測試詳情"):
                    st.json(results)
                    
            except Exception as e:
                st.sidebar.error(f"❌ 測試失敗: {e}")
        
        # 會話信息
        if st.sidebar.button("📊 顯示會話信息"):
            try:
                from utils.session_manager import SessionManager
                session_manager = SessionManager()
                session_info = session_manager.get_session_info()
                
                st.sidebar.success("會話信息:")
                st.sidebar.json(session_info)
                
            except Exception as e:
                st.sidebar.error(f"❌ 獲取會話信息失敗: {e}")
        
        # === 延遲測試控制 ===
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🧪 延遲測試控制")
        
        # 顯示當前設置
        current_delay = st.sidebar.slider(
            "設置延遲秒數", 
            min_value=0, 
            max_value=10, 
            value=5,
            help="調整 UsageLog 寫入後的等待時間"
        )
        
        if st.sidebar.button("🔧 應用延遲設置"):
            st.session_state.api_delay_seconds = current_delay
            st.sidebar.success(f"✅ 延遲設置為 {current_delay} 秒")
        
        # 顯示當前延遲設置
        if hasattr(st.session_state, 'api_delay_seconds'):
            st.sidebar.info(f"當前延遲：{st.session_state.api_delay_seconds} 秒")
        else:
            st.sidebar.info("當前延遲：5 秒（預設）")
        
        # 移除延遲測試
        if st.sidebar.button("❌ 移除延遲測試"):
            st.session_state.api_delay_seconds = 0
            st.sidebar.success("✅ 延遲測試已移除")

def main():
    """主函數"""
    try:
        app = RadiAIApp()
        app.run()
        debug_feedback_in_app()  # 使用增強版調試工具
    except Exception as e:
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
