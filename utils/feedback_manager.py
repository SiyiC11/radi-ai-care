"""
RadiAI.Care 回饋管理系統 - 修復版
移除 st.rerun() 調用，修復回饋提交問題
"""

import streamlit as st
import time
import logging
from typing import Dict, Any, Optional
from config.settings import AppConfig

logger = logging.getLogger(__name__)

# 延遲導入避免循環依賴
def get_feedback_logger():
    try:
        from log_to_sheets import log_feedback_to_sheets
        return log_feedback_to_sheets
    except ImportError:
        return None


class FeedbackManager:
    """回饋管理器（修復版）"""
    
    def __init__(self):
        self.config = AppConfig()
        # 初始化回饋提交記錄
        if 'feedback_submitted_ids' not in st.session_state:
            st.session_state.feedback_submitted_ids = set()
    
    def render_feedback_section(self, lang: Dict, translation_id: str, 
                              report_text: str, file_type: str, validation_result: Dict):
        """
        渲染回饋收集介面
        
        Args:
            lang: 語言配置
            translation_id: 翻譯ID
            report_text: 報告文本
            file_type: 文件類型
            validation_result: 內容驗證結果
        """
        # 檢查是否已提交回饋
        if translation_id in st.session_state.get('feedback_submitted_ids', set()):
            st.success(f"✅ {lang.get('feedback_already', '已提交過回饋')}")
            st.info("💡 感謝您的寶貴意見！您的回饋將幫助我們改進服務質量。")
            return
        
        st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
        st.markdown(f"#### {lang['feedback_title']}")
        
        # 快速回饋按鈕
        self._render_quick_feedback(lang, translation_id, report_text, file_type, validation_result)
        
        # 詳細回饋表單
        with st.expander("📝 提供詳細回饋", expanded=False):
            self._render_detailed_feedback_form(lang, translation_id, report_text, file_type, validation_result)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_quick_feedback(self, lang: Dict, translation_id: str, 
                             report_text: str, file_type: str, validation_result: Dict):
        """渲染快速回饋按鈕"""
        st.markdown(f"**{lang['feedback_helpful']}**")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👍 有幫助", key=f"helpful_yes_{translation_id}", use_container_width=True):
                success = self._handle_quick_feedback(
                    translation_id, "positive", lang, 
                    report_text, file_type, validation_result
                )
                if success:
                    st.success(f"✅ {lang['feedback_submitted']}")
                    st.balloons()
                else:
                    st.error("❌ 提交失敗，請稍後再試")
        
        with col2:
            if st.button("👎 沒幫助", key=f"helpful_no_{translation_id}", use_container_width=True):
                success = self._handle_quick_feedback(
                    translation_id, "negative", lang,
                    report_text, file_type, validation_result
                )
                if success:
                    st.success(f"✅ {lang['feedback_submitted']}")
                    st.info("💭 我們會根據您的回饋改進服務，也歡迎提供詳細建議。")
                else:
                    st.error("❌ 提交失敗，請稍後再試")
    
    def _render_detailed_feedback_form(self, lang: Dict, translation_id: str, 
                                     report_text: str, file_type: str, validation_result: Dict):
        """渲染詳細回饋表單"""
        # 使用唯一的 form key
        form_key = f"feedback_form_{translation_id}_{int(time.time())}"
        
        with st.form(form_key, clear_on_submit=False):
            st.markdown("##### 📊 詳細評價（幫助我們改進）")
            
            # 評分指標
            col1, col2 = st.columns(2)
            with col1:
                clarity = st.slider(f"{lang['feedback_clarity']} (1=模糊 → 5=清晰)", 1, 5, 4, 
                                  key=f"clarity_{translation_id}")
                usefulness = st.slider(f"{lang['feedback_usefulness']} (1=無用 → 5=實用)", 1, 5, 4,
                                     key=f"usefulness_{translation_id}")
            with col2:
                accuracy = st.slider(f"{lang['feedback_accuracy']} (1=不準 → 5=準確)", 1, 5, 4,
                                   key=f"accuracy_{translation_id}")
                recommendation = st.slider(f"{lang['feedback_recommendation']} (0=不推薦 → 10=強烈推薦)", 0, 10, 8,
                                         key=f"recommendation_{translation_id}")
            
            # 問題類型選擇
            st.markdown("##### 🔍 遇到的問題")
            issues = st.multiselect(
                lang['feedback_issues'],
                [
                    "翻譯不準確或有錯誤", 
                    "醫學術語解釋不清楚", 
                    "格式排版不易閱讀",
                    "處理速度太慢", 
                    "缺少重要資訊",
                    "與原文意思不符",
                    "建議問題不實用",
                    "其他問題"
                ],
                default=[],
                key=f"issues_{translation_id}"
            )
            
            # 文字回饋
            col1, col2 = st.columns([2, 1])
            with col1:
                suggestion = st.text_area(
                    lang['feedback_suggestion'], 
                    height=80, 
                    max_chars=500,
                    placeholder="請描述具體的改進建議...",
                    key=f"suggestion_{translation_id}"
                )
            with col2:
                email = st.text_input(
                    lang['feedback_email'],
                    placeholder="example@email.com",
                    help="選填，僅用於產品改進聯繫",
                    key=f"email_{translation_id}"
                )
            
            # 提交按鈕
            submitted = st.form_submit_button(
                lang['feedback_submit'], 
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                success = self._handle_detailed_feedback(
                    translation_id, lang, clarity, usefulness, accuracy, 
                    recommendation, issues, suggestion, email, 
                    report_text, file_type, validation_result
                )
                
                if success:
                    st.success(f"✅ {lang['feedback_submitted']}")
                    st.balloons()
                    
                    # 顯示感謝信息
                    overall_satisfaction = (clarity + usefulness + accuracy) / 3
                    if overall_satisfaction >= 4:
                        st.info("🌟 感謝您的高度評價！我們會繼續努力提供更好的服務。")
                    elif overall_satisfaction < 3:
                        st.info("📝 感謝您的寶貴意見！我們會認真改進服務質量。")
                else:
                    st.error("❌ 提交失敗，請稍後再試")
    
    def _handle_quick_feedback(self, translation_id: str, sentiment: str, lang: Dict,
                             report_text: str, file_type: str, validation_result: Dict) -> bool:
        """處理快速回饋"""
        try:
            feedback_data = {
                'translation_id': translation_id,
                'language': st.session_state.language,
                'feedback_type': 'quick',
                'sentiment': sentiment,
                'clarity_score': 0,  # 快速回饋不評分
                'usefulness_score': 0,
                'accuracy_score': 0,
                'recommendation_score': 0,
                'overall_satisfaction': 0,
                'issues': '',
                'suggestion': '',
                'email': '',
                'report_length': len(report_text),
                'file_type': file_type,
                'medical_terms_detected': len(validation_result.get('found_terms', [])),
                'confidence_score': round(validation_result.get('confidence', 0), 2),
                'app_version': self.config.APP_VERSION,
                'device_id': st.session_state.get('device_id', 'unknown'),
                'session_id': st.session_state.get('user_session_id', 'unknown')
            }
            
            success = self._log_feedback(feedback_data)
            
            if success:
                # 標記為已提交（不使用 st.rerun()）
                st.session_state.feedback_submitted_ids.add(translation_id)
                logger.info(f"快速回饋提交成功: {translation_id}")
                return True
            else:
                logger.error(f"快速回饋提交失敗: {translation_id}")
                return False
                
        except Exception as e:
            logger.error(f"處理快速回饋失敗: {e}")
            return False
    
    def _handle_detailed_feedback(self, translation_id: str, lang: Dict, 
                                clarity: int, usefulness: int, accuracy: int, 
                                recommendation: int, issues: list, suggestion: str, 
                                email: str, report_text: str, file_type: str, 
                                validation_result: Dict) -> bool:
        """處理詳細回饋"""
        try:
            # 計算整體滿意度
            overall_satisfaction = round((clarity + usefulness + accuracy) / 3, 2)
            
            feedback_data = {
                'translation_id': translation_id,
                'language': st.session_state.language,
                'feedback_type': 'detailed',
                'sentiment': 'positive' if overall_satisfaction >= 3.5 else 'negative',
                'clarity_score': clarity,
                'usefulness_score': usefulness,
                'accuracy_score': accuracy,
                'recommendation_score': recommendation,
                'overall_satisfaction': overall_satisfaction,
                'issues': ';'.join(issues) if issues else '無',
                'suggestion': suggestion.strip() if suggestion else '無',
                'email': email.strip() if email else '',
                'report_length': len(report_text),
                'file_type': file_type,
                'medical_terms_detected': len(validation_result.get('found_terms', [])),
                'confidence_score': round(validation_result.get('confidence', 0), 2),
                'app_version': self.config.APP_VERSION,
                'device_id': st.session_state.get('device_id', 'unknown'),
                'session_id': st.session_state.get('user_session_id', 'unknown')
            }
            
            success = self._log_feedback(feedback_data)
            
            if success:
                # 標記為已提交（不使用 st.rerun()）
                st.session_state.feedback_submitted_ids.add(translation_id)
                logger.info(f"詳細回饋提交成功: {translation_id}")
                return True
            else:
                logger.error(f"詳細回饋提交失敗: {translation_id}")
                return False
                
        except Exception as e:
            logger.error(f"處理詳細回饋失敗: {e}")
            return False
    
    def _log_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """記錄回饋到 Google Sheets"""
        try:
            log_feedback_func = get_feedback_logger()
            if not log_feedback_func:
                logger.error("無法導入回饋記錄函數")
                return False
            
            success = log_feedback_func(**feedback_data)
            
            if success:
                logger.info(f"回饋記錄成功: {feedback_data['translation_id']}")
            else:
                logger.error(f"回饋記錄失敗: {feedback_data['translation_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"回饋記錄異常: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """獲取回饋統計信息"""
        submitted_count = len(st.session_state.get('feedback_submitted_ids', set()))
        translation_count = st.session_state.get('translation_count', 0)
        
        feedback_rate = (submitted_count / translation_count * 100) if translation_count > 0 else 0
        
        return {
            'total_feedbacks': submitted_count,
            'total_translations': translation_count,
            'feedback_rate': round(feedback_rate, 1)
        }
    
    def render_feedback_stats(self):
        """渲染回饋統計信息（供調試使用）"""
        if st.checkbox("顯示回饋統計", key="show_feedback_stats"):
            stats = self.get_feedback_stats()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("回饋次數", stats['total_feedbacks'])
            with col2:
                st.metric("翻譯次數", stats['total_translations'])
            with col3:
                st.metric("回饋率", f"{stats['feedback_rate']}%")
    
    def clear_feedback_history(self):
        """清除回饋歷史（僅用於測試）"""
        st.session_state.feedback_submitted_ids = set()
        logger.info("回饋歷史已清除")
    
    def export_feedback_summary(self) -> Dict[str, Any]:
        """導出回饋摘要（用於分析）"""
        return {
            'session_id': st.session_state.get('user_session_id', 'unknown'),
            'device_id': st.session_state.get('device_id', 'unknown'),
            'feedback_stats': self.get_feedback_stats(),
            'submitted_ids': list(st.session_state.get('feedback_submitted_ids', set())),
            'export_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
