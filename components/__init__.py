"""
RadiAI.Care UI 組件模塊 - 修復版
統一管理所有用戶界面組件和渲染邏輯
"""

__version__ = "1.0.0"
__author__ = "RadiAI.Care Team"

import logging
logger = logging.getLogger(__name__)

# 修復導入 - 使用正確的文件名
try:
    from .enhanced_ui_components import EnhancedUIComponents
    ENHANCED_UI_AVAILABLE = True
    logger.info("Enhanced UI Components loaded successfully")
except ImportError as e:
    ENHANCED_UI_AVAILABLE = False
    logger.warning(f"Enhanced UI Components not available: {e}")
    
    # 提供備用的基礎 UI 組件
    class BasicUIComponents:
        """基礎 UI 組件（備用）"""
        
        def __init__(self, config=None, file_handler=None):
            self.config = config
            self.file_handler = file_handler
        
        def render_header(self, lang):
            import streamlit as st
            st.markdown(f"# 🏥 {lang.get('app_title', 'RadiAI.Care')}")
            st.markdown(f"**{lang.get('app_subtitle', '智能醫療報告翻譯助手')}**")
            st.info(lang.get('app_description', '為澳洲華人社區提供專業醫學報告翻譯服務'))
        
        def render_language_selection(self, lang):
            import streamlit as st
            st.markdown("### 選擇語言")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("繁體中文", key="lang_trad", use_container_width=True):
                    st.session_state.language = "繁體中文"
                    st.rerun()
            with col2:
                if st.button("简体中文", key="lang_simp", use_container_width=True):
                    st.session_state.language = "简体中文"
                    st.rerun()
        
        def render_disclaimer(self, lang):
            import streamlit as st
            st.warning("⚠️ 重要：本工具僅提供翻譯服務，不構成醫療建議")
    
    EnhancedUIComponents = BasicUIComponents

# 導出主要組件
__all__ = [
    'EnhancedUIComponents',
    'create_ui_components',
    'validate_ui_components'
]

def create_ui_components(config=None, file_handler=None):
    """創建 UI 組件實例的工廠函數"""
    try:
        return EnhancedUIComponents(config, file_handler)
    except Exception as e:
        logger.error(f"Failed to create UI components: {e}")
        # 返回基礎組件作為備用
        return BasicUIComponents(config, file_handler)

def validate_ui_components():
    """驗證 UI 組件完整性"""
    validation_result = {
        "enhanced_ui_available": ENHANCED_UI_AVAILABLE,
        "can_create_instance": False,
        "available_methods": []
    }
    
    try:
        # 嘗試創建實例
        ui = create_ui_components()
        validation_result["can_create_instance"] = True
        
        # 檢查可用方法
        methods = [method for method in dir(ui) if not method.startswith('_')]
        validation_result["available_methods"] = methods
        
        logger.info(f"UI components validation passed: {len(methods)} methods available")
        
    except Exception as e:
        logger.error(f"UI components validation failed: {e}")
        validation_result["error"] = str(e)
    
    return validation_result

# 初始化檢查
_validation = validate_ui_components()
logger.info(f"Components module initialized - Enhanced UI: {ENHANCED_UI_AVAILABLE}")
