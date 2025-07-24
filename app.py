"""
RadiAI.Care 完整主應用程序 - 用户版
整合 Enhanced UI Components 和 Google Sheets 資料記錄
"""

import os
import time
import uuid
import logging
import hashlib
from datetime import datetime

# 必須首先導入 streamlit
import streamlit as st

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 嘗試導入配置模塊
try:
    from config.settings import AppConfig, UIText, CSS_STYLES
    CONFIG_AVAILABLE = True
    logger.info("Config modules loaded successfully")
except ImportError as e:
    CONFIG_AVAILABLE = False
    logger.warning(f"配置模塊不可用: {e}")

# 嘗試導入工具模塊
try:
    from utils.file_handler import FileHandler
    FILE_HANDLER_AVAILABLE = True
    logger.info("FileHandler loaded successfully")
except ImportError:
    FILE_HANDLER_AVAILABLE = False
    logger.warning("文件處理器不可用")

try:
    from utils.translator import Translator
    TRANSLATOR_AVAILABLE = True
    logger.info("Translator loaded successfully")
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("翻譯器不可用")

try:
    from utils.comprehensive_sheets_manager import GoogleSheetsManager
    SHEETS_AVAILABLE = True
    logger.info("GoogleSheetsManager loaded successfully")
except ImportError:
    SHEETS_AVAILABLE = False
    logger.warning("Google Sheets 管理器不可用")

# 導入 Enhanced UI Components
try:
    from components import EnhancedUIComponents, create_ui_components
    UI_COMPONENTS_AVAILABLE = True
    logger.info("Enhanced UI Components loaded successfully")
except ImportError as e:
    UI_COMPONENTS_AVAILABLE = False
    logger.warning(f"Enhanced UI Components 不可用: {e}")

# Streamlit 頁面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能醫療報告翻譯助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入基礎CSS樣式
if CONFIG_AVAILABLE:
    try:
        st.markdown(CSS_STYLES, unsafe_allow_html=True)
        logger.info("CSS styles injected successfully")
    except Exception as e:
        logger.warning(f"CSS injection failed: {e}")
else:
    st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }
    .main-title { color: #0d74b8; font-weight: bold; text-align: center; }
    
    /* 页脚样式 */
    .footer-info {
        text-align: center;
        color: #666;
        font-size: 0.7rem;
        margin: 2rem 0 1rem 0;
        padding: 1rem 1.2rem;
        background: linear-gradient(145deg, #f2fbff 0%, #e3f4fa 100%);
        border-radius: 15px;
        border: 1px solid #d4e8f2;
        box-shadow: 0 2px 8px rgba(13,116,184,0.08);
    }
    
    .version-info {
        text-align: center;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0 0.5rem 0;
        background: linear-gradient(145deg, #f4fcff 0%, #e5f4fb 100%);
        border-radius: 15px;
        border: 1px solid #d4e8f2;
        box-shadow: 0 4px 12px rgba(13,116,184,0.06);
    }
    
    .version-title {
        font-size: 0.85rem;
        color: #0d74b8;
        margin-bottom: 0.3rem;
    }
    
    .version-subtitle {
        font-size: 0.7rem;
        color: #4c7085;
        line-height: 1.4;
    }
    
    .legal-text {
        font-size: 0.65rem;
        color: #777;
        line-height: 1.3;
        margin-top: 0.5rem;
    }
    
    .privacy-title {
        font-size: 0.6rem;
        color: #4c7085;
        margin-bottom: 0.7rem;
        opacity: 0.9;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

class BasicConfig:
    """基礎配置類"""
    APP_TITLE = "RadiAI.Care"
    APP_SUBTITLE = "智能醫療報告翻譯助手"
    APP_DESCRIPTION = "為澳洲華人社區提供專業醫學報告翻譯服務"
    APP_VERSION = "4.2.0"
    MAX_FREE_TRANSLATIONS = 3
    SUPPORTED_FILE_TYPES = ("pdf", "txt", "docx")
    GOOGLE_SHEET_ID = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"

def get_language_config(language="简体中文"):
    """獲取語言配置"""
    if CONFIG_AVAILABLE:
        try:
            config = UIText.get_language_config(language)
            # 确保页脚配置存在
            if 'footer_privacy_title' not in config:
                config.update(get_footer_config(language))
            return config
        except Exception as e:
            logger.warning(f"Failed to get language config: {e}")
    
    # 完整的備用語言配置
    return get_complete_language_config(language)

def get_footer_config(language):
    """获取页脚配置"""
    if language == "繁體中文":
        return {
            "footer_privacy_title": "隱私政策與使用條款",
            "footer_app_name": "智能醫療報告翻譯助手",
            "footer_service_desc": "為澳洲華人社群服務",
            "footer_privacy_text": "我們僅收集翻譯服務必要的資訊，所有數據採用加密傳輸和儲存，嚴格遵守澳洲隱私法（Privacy Act 1988）規定，絕不與第三方分享您的醫療資訊。",
            "footer_terms_text": "本服務僅提供醫學報告翻譯和科普解釋，不構成任何醫療建議或診斷。用戶須為所有醫療決策自負責任，並應諮詢專業醫師意見。",
            "footer_disclaimer_text": "AI翻譯可能存在錯誤，請與醫師核實所有重要醫療資訊。緊急情況請撥打000或前往最近的急診室。",
            "footer_contact_text": "如有任何問題或建議，請聯繫 support@radiai.care | 本服務受澳洲法律管轄"
        }
    else:  # 简体中文
        return {
            "footer_privacy_title": "隐私政策与使用条款",
            "footer_app_name": "智能医疗报告翻译助手",
            "footer_service_desc": "为澳洲华人社区服务",
            "footer_privacy_text": "我们仅收集翻译服务必要的信息，所有数据采用加密传输和存储，严格遵守澳洲隐私法（Privacy Act 1988）规定，绝不与第三方分享您的医疗信息。",
            "footer_terms_text": "本服务仅提供医学报告翻译和科普解释，不构成任何医疗建议或诊断。用户须为所有医疗决策自负责任，并应咨询专业医师意见。",
            "footer_disclaimer_text": "AI翻译可能存在错误，请与医师核实所有重要医疗信息。紧急情况请拨打000或前往最近的急诊室。",
            "footer_contact_text": "如有任何问题或建议，请联系 support@radiai.care | 本服务受澳洲法律管辖"
        }

def get_complete_language_config(language):
    """获取完整的语言配置"""
    base_config = {
        "简体中文": {
            "code": "simplified_chinese",
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能医疗报告翻译助手",
            "app_description": "为澳洲华人社区提供专业医学报告翻译服务",
            "disclaimer_title": "重要医疗免责声明",
            "disclaimer_items": [
                "本工具仅提供翻译服务，不构成医疗建议",
                "请咨询专业医师进行医疗决策",
                "AI翻译可能存在错误",
                "紧急情况请拨打000"
            ],
            "input_placeholder": "请输入英文放射科报告...",
            "file_upload": "上传文件",
            "supported_formats": "支持PDF、TXT、DOCX格式",
            "translate_button": "开始翻译",
            "error_empty_input": "请输入内容",
            "lang_selection": "选择语言"
        },
        "繁體中文": {
            "code": "traditional_chinese",
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能醫療報告翻譯助手",
            "app_description": "為澳洲華人社群提供專業醫學報告翻譯服務",
            "disclaimer_title": "重要醫療免責聲明",
            "disclaimer_items": [
                "本工具僅提供翻譯服務，不構成醫療建議",
                "請諮詢專業醫師進行醫療決策",
                "AI翻譯可能存在錯誤",
                "緊急情況請撥打000"
            ],
            "input_placeholder": "請輸入英文放射科報告...",
            "file_upload": "上傳文件",
            "supported_formats": "支持PDF、TXT、DOCX格式",
            "translate_button": "開始翻譯",
            "error_empty_input": "請輸入內容",
            "lang_selection": "選擇語言"
        }
    }
    
    # 获取基础配置并添加页脚配置
    config = base_config.get(language, base_config["简体中文"])
    config.update(get_footer_config(language))
    return config

def initialize_session_state():
    """初始化會話狀態"""
    if 'translation_count' not in st.session_state:
        st.session_state.translation_count = 0
    if 'daily_limit' not in st.session_state:
        st.session_state.daily_limit = 3
    if 'language' not in st.session_state:
        st.session_state.language = "简体中文"
    if 'user_session_id' not in st.session_state:
        st.session_state.user_session_id = str(uuid.uuid4())[:8]
    if 'permanent_user_id' not in st.session_state:
        # 生成持久用戶ID
        today = datetime.now().strftime('%Y-%m-%d')
        raw_data = f"{st.session_state.user_session_id}_{today}"
        user_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
        st.session_state.permanent_user_id = f"user_{user_hash}"
    
    # 初始化配置對象
    if 'app_config' not in st.session_state:
        st.session_state.app_config = AppConfig() if CONFIG_AVAILABLE else BasicConfig()
    
    # 初始化 UI 組件
    if 'ui_components' not in st.session_state and UI_COMPONENTS_AVAILABLE:
        try:
            config = st.session_state.app_config
            file_handler = FileHandler() if FILE_HANDLER_AVAILABLE else None
            st.session_state.ui_components = create_ui_components(config, file_handler)
            logger.info("UI components initialized successfully")
        except Exception as e:
            st.session_state.ui_components = None
            logger.error(f"UI components initialization failed: {e}")
    
    # 初始化 Google Sheets 管理器
    if 'sheets_manager' not in st.session_state and SHEETS_AVAILABLE:
        try:
            config = st.session_state.app_config
            sheet_id = getattr(config, 'GOOGLE_SHEET_ID', BasicConfig.GOOGLE_SHEET_ID)
            st.session_state.sheets_manager = GoogleSheetsManager(sheet_id)
            logger.info("Google Sheets 管理器初始化成功")
        except Exception as e:
            st.session_state.sheets_manager = None
            logger.error(f"Google Sheets 初始化失敗: {e}")
    elif not SHEETS_AVAILABLE:
        st.session_state.sheets_manager = None

def render_with_ui_components(component_method, *args, **kwargs):
    """使用 UI 組件渲染，如果失敗則使用備用方法"""
    ui_components = st.session_state.get('ui_components')
    
    if ui_components and hasattr(ui_components, component_method):
        try:
            method = getattr(ui_components, component_method)
            method(*args, **kwargs)
            return True
        except Exception as e:
            logger.error(f"UI component method {component_method} failed: {e}")
            return False
    else:
        logger.warning(f"UI component method {component_method} not available, using fallback")
        return False

def render_header_fallback(lang_cfg):
    """備用標題渲染（無 logo）"""
    st.markdown('<div class="main-title">' + lang_cfg["app_title"] + '</div>', unsafe_allow_html=True)
    st.markdown(f"**{lang_cfg['app_subtitle']}**")
    st.info(lang_cfg["app_description"])

def render_language_selection_fallback(lang_cfg):
    """備用語言選擇"""
    st.markdown(f"### {lang_cfg['lang_selection']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("繁體中文", key="lang_traditional_fallback", use_container_width=True,
                    type="primary" if st.session_state.language == "繁體中文" else "secondary"):
            st.session_state.language = "繁體中文"
            st.rerun()
    with col2:
        if st.button("简体中文", key="lang_simplified_fallback", use_container_width=True,
                    type="primary" if st.session_state.language == "简体中文" else "secondary"):
            st.session_state.language = "简体中文"
            st.rerun()

def render_disclaimer_fallback(lang_cfg):
    """備用免責聲明"""
    st.markdown("### ⚠️ " + lang_cfg['disclaimer_title'])
    
    for i, item in enumerate(lang_cfg["disclaimer_items"], 1):
        st.markdown(f"**{i}.** {item}")
    
    st.warning("🆘 緊急情況請立即撥打 000")

def render_usage_status():
    """渲染使用狀態"""
    current_usage = st.session_state.translation_count
    daily_limit = st.session_state.daily_limit
    remaining = daily_limit - current_usage
    
    st.markdown("### 📊 使用狀態")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今日已用", f"{current_usage}/{daily_limit}")
    with col2:
        st.metric("剩餘次數", remaining)
    with col3:
        if remaining > 0:
            st.metric("狀態", "✅ 可用")
        else:
            st.metric("狀態", "🚫 已滿")
    
    return remaining

def render_input_section(lang_cfg):
    """渲染輸入區域"""
    # 嘗試使用 Enhanced UI Components
    input_success = render_with_ui_components('render_input_section', lang_cfg)
    
    if input_success:
        logger.info("Using Enhanced UI Components for input section")
        return "", "enhanced_ui"
    
    # 備用實現
    logger.info("Using fallback input section")
    st.markdown("### 📝 輸入報告")
    
    # 選擇輸入方式
    input_method = st.radio("選擇輸入方式:", ["文字輸入", "文件上傳"], horizontal=True, key="input_method_fallback")
    
    if input_method == "文字輸入":
        report_text = st.text_area(
            "請輸入英文放射科報告：",
            height=200,
            placeholder=lang_cfg["input_placeholder"],
            key="text_input_fallback"
        )
        file_type = "manual"
    else:
        uploaded_file = st.file_uploader(
            lang_cfg["file_upload"],
            type=['pdf', 'txt', 'docx'],
            help=lang_cfg["supported_formats"],
            key="file_uploader_fallback"
        )
        
        if uploaded_file and FILE_HANDLER_AVAILABLE:
            try:
                file_handler = FileHandler()
                extracted_text, result = file_handler.extract_text(uploaded_file)
                if extracted_text:
                    st.success("✅ 文件上傳成功")
                    with st.expander("📄 文件內容預覽", expanded=False):
                        preview_text = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
                        st.text_area("提取的內容：", value=preview_text, height=150, disabled=True)
                    report_text = extracted_text
                    file_type = uploaded_file.type
                else:
                    st.error("❌ 文件處理失敗")
                    report_text = ""
                    file_type = "unknown"
            except Exception as e:
                st.error(f"❌ 文件處理錯誤: {e}")
                report_text = ""
                file_type = "error"
        else:
            if not FILE_HANDLER_AVAILABLE:
                st.error("❌ 文件處理功能不可用，請使用文字輸入")
            report_text = ""
            file_type = "none"
    
    return report_text, file_type

def handle_translation(report_text, file_type, lang_cfg):
    """處理翻譯請求"""
    if not TRANSLATOR_AVAILABLE:
        st.error("❌ 翻譯功能不可用，請檢查系統配置")
        return
    
    try:
        translator = Translator()
        
        # 生成翻譯ID
        translation_id = str(uuid.uuid4())[:16]
        text_hash = hashlib.md5(report_text.encode()).hexdigest()[:16]
        
        # 驗證內容
        validation = translator.validate_content(report_text)
        if not validation["is_valid"]:
            st.warning("⚠️ 內容可能不是完整的放射科報告")
        
        # 執行翻譯
        start_time = time.time()
        
        with st.spinner("正在翻譯中..."):
            # 創建進度條
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            result = translator.translate_with_progress(
                report_text, lang_cfg["code"], progress_bar, status_text
            )
            
            processing_time = time.time() - start_time
        
        if result["success"]:
            # 增加使用次數
            st.session_state.translation_count += 1
            
            # 記錄到 Google Sheets
            log_usage_to_sheets(
                translation_id=translation_id,
                text_hash=text_hash,
                processing_time=processing_time,
                file_type=file_type,
                content_length=len(report_text),
                lang_cfg=lang_cfg,
                validation=validation
            )
            
            # 顯示結果
            st.success("✅ 翻譯完成")
            st.markdown("### 📄 翻譯結果")
            st.markdown(result["content"])
            
            # 顯示剩餘次數
            remaining = st.session_state.daily_limit - st.session_state.translation_count
            if remaining > 0:
                st.info(f"今日還可使用 {remaining} 次")
            else:
                st.warning("今日配額已用完")
            
            # 簡單反饋收集
            render_simple_feedback(translation_id)
            
        else:
            st.error(f"❌ 翻譯失敗: {result.get('error', '未知錯誤')}")
            
    except Exception as e:
        st.error(f"❌ 翻譯處理錯誤: {e}")
        logger.error(f"翻譯錯誤: {e}")

def log_usage_to_sheets(translation_id, text_hash, processing_time, file_type, content_length, lang_cfg, validation):
    """記錄使用資料到 Google Sheets"""
    if not st.session_state.get('sheets_manager'):
        logger.warning("Google Sheets 管理器不可用，跳過資料記錄")
        return
    
    try:
        usage_data = {
            'user_id': st.session_state.permanent_user_id,
            'session_id': st.session_state.user_session_id,
            'translation_id': translation_id,
            'daily_count': st.session_state.translation_count,
            'session_count': 1,
            'processing_time_ms': int(processing_time * 1000),
            'file_type': file_type,
            'content_length': content_length,
            'status': 'success',
            'language': lang_cfg["code"],
            'device_info': 'streamlit_web',
            'ip_hash': hashlib.md5(st.session_state.user_session_id.encode()).hexdigest()[:8],
            'user_agent': 'Streamlit/Unknown',
            'error_message': '',
            'ai_model': 'gpt-4o-mini',
            'api_cost': 0,
            'extra_data': {
                'text_hash': text_hash,
                'validation_confidence': validation.get('confidence', 0),
                'validation_is_valid': validation.get('is_valid', False),
                'found_medical_terms': len(validation.get('found_terms', [])),
                'app_version': BasicConfig.APP_VERSION
            }
        }
        
        sheets_result = st.session_state.sheets_manager.log_usage(usage_data)
        
        if sheets_result:
            logger.info(f"成功記錄使用資料: {translation_id}")
        else:
            logger.error(f"記錄使用資料失敗: {translation_id}")
            
    except Exception as e:
        logger.error(f"記錄使用資料時出錯: {e}")

def render_simple_feedback(translation_id):
    """渲染簡單反饋"""
    with st.expander("💬 快速反饋", expanded=False):
        st.markdown("您的評價對我們很重要！")
        
        col1, col2 = st.columns(2)
        with col1:
            rating = st.slider("滿意度評分", 1, 5, 4, help="1=很差，5=很好", key=f"rating_{translation_id}")
        with col2:
            if st.button("提交評分", type="primary", key=f"submit_{translation_id}"):
                # 記錄反饋到 Sheets
                log_feedback_to_sheets(translation_id, rating)
                st.success("感謝您的評分！")
                st.balloons()

def log_feedback_to_sheets(translation_id, rating):
    """記錄反饋到 Google Sheets"""
    if not st.session_state.get('sheets_manager'):
        return
    
    try:
        feedback_data = {
            'translation_id': translation_id,
            'user_id': st.session_state.permanent_user_id,
            'overall_satisfaction': rating,
            'translation_quality': rating,
            'speed_rating': rating,
            'ease_of_use': rating,
            'feature_completeness': rating,
            'likelihood_to_recommend': rating,
            'primary_use_case': '理解檢查報告',
            'user_type': '患者/家屬',
            'improvement_areas': [],
            'specific_issues': [],
            'feature_requests': [],
            'detailed_comments': '',
            'contact_email': '',
            'follow_up_consent': False,
            'device_info': 'streamlit_web',
            'language': st.session_state.language,
            'usage_frequency': '偶爾使用',
            'comparison_rating': rating,
            'extra_metadata': {
                'feedback_type': 'quick_rating',
                'submission_method': 'slider',
                'app_version': BasicConfig.APP_VERSION
            }
        }
        
        result = st.session_state.sheets_manager.log_feedback(feedback_data)
        
        if result:
            logger.info(f"成功記錄反饋: {translation_id}, 評分: {rating}")
        else:
            logger.error(f"記錄反饋失敗: {translation_id}")
            
    except Exception as e:
        logger.error(f"記錄反饋時出錯: {e}")

def render_quota_exceeded():
    """渲染配額超額界面"""
    st.error("🚫 今日免費配額已用完，請明天再來")
    st.info("💡 升級專業版可獲得無限翻譯次數")
    
    # 升級選項
    with st.expander("🚀 升級專業版", expanded=False):
        st.markdown("**專業版特權：**")
        st.markdown("- ♾️ 無限翻譯次數")
        st.markdown("- ⚡ 優先處理")
        st.markdown("- 📊 詳細統計")
        st.markdown("- 🔄 批量處理")
        st.markdown("- 📱 移動優化")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆓 免費試用", use_container_width=True):
                st.info("發送郵件至 trial@radiai.care")
        with col2:
            if st.button("💳 立即升級", use_container_width=True):
                st.info("訪問 radiai.care/upgrade")

def render_footer():
    """渲染頁腳信息"""
    # 获取当前语言配置
    lang_cfg = get_language_config(st.session_state.language)
    
    # 隱私政策和使用條款
    st.markdown(f"""
    <div class="footer-info">
        <div class="privacy-title">
            🔒 {lang_cfg['footer_privacy_title']}
        </div>
        <div class="legal-text">
            <strong>{"隱私保護" if st.session_state.language == "繁體中文" else "隐私保护"}：</strong>{lang_cfg['footer_privacy_text']}
            <br><br>
            <strong>{"服務條款" if st.session_state.language == "繁體中文" else "服务条款"}：</strong>{lang_cfg['footer_terms_text']}
            <br><br>
            <strong>{"免責聲明" if st.session_state.language == "繁體中文" else "免责声明"}：</strong>{lang_cfg['footer_disclaimer_text']}
            <br><br>
            <strong>{"聯繫我們" if st.session_state.language == "繁體中文" else "联系我们"}：</strong>{lang_cfg['footer_contact_text']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 版本信息 - 与标题区域相似的设计
    st.markdown(f"""
    <div class="version-info">
        <div class="version-title">
            🏥 RadiAI.Care v4.2.0
        </div>
        <div class="version-subtitle">
            {lang_cfg['footer_app_name']} | {lang_cfg['footer_service_desc']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """主應用程序函數"""
    try:
        # 初始化會話狀態
        initialize_session_state()
        
        # 獲取語言配置
        lang_cfg = get_language_config(st.session_state.language)
        
        # 渲染頁面標題 - 優先使用 Enhanced UI Components
        header_success = render_with_ui_components('render_header', lang_cfg)
        if not header_success:
            render_header_fallback(lang_cfg)
            logger.info("Using fallback header rendering")
        else:
            logger.info("Using Enhanced UI Components for header")
        
        # 渲染語言選擇 - 優先使用 Enhanced UI Components
        lang_success = render_with_ui_components('render_language_selection', lang_cfg)
        if not lang_success:
            render_language_selection_fallback(lang_cfg)
            logger.info("Using fallback language selection")
        else:
            logger.info("Using Enhanced UI Components for language selection")
        
        # 重新獲取語言配置（可能已更改）
        lang_cfg = get_language_config(st.session_state.language)
        
        # 渲染免責聲明 - 優先使用 Enhanced UI Components
        disclaimer_success = render_with_ui_components('render_disclaimer', lang_cfg)
        if not disclaimer_success:
            render_disclaimer_fallback(lang_cfg)
            logger.info("Using fallback disclaimer rendering")
        else:
            logger.info("Using Enhanced UI Components for disclaimer")
        
        # 顯示使用狀態
        remaining = render_usage_status()
        
        # 檢查配額
        if remaining <= 0:
            render_quota_exceeded()
            render_footer()
            return
        
        # 輸入區域
        report_text, file_type = render_input_section(lang_cfg)
        
        # 翻譯按鈕
        if report_text and report_text.strip():
            if st.button(lang_cfg["translate_button"], type="primary", use_container_width=True):
                handle_translation(report_text, file_type, lang_cfg)
        else:
            st.warning(lang_cfg["error_empty_input"])
        
        # 渲染頁腳
        render_footer()
        
    except Exception as e:
        logger.error(f"應用程序運行錯誤: {e}")
        st.error("❌ 應用遇到錯誤，請刷新頁面重試")
        
        # 顯示詳細錯誤信息
        with st.expander("🔍 錯誤詳情", expanded=False):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
