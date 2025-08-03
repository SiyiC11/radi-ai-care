"""
RadiAI.Care 主应用程序 - 完整版带反馈持久化
在翻译完成后添加简单的用户反馈收集功能，并保持翻译结果持久化
"""

import os
import time
import uuid
import logging
import hashlib
from datetime import datetime

# 必须首先导入 streamlit
import streamlit as st

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入配置模块
try:
    from config.settings import AppConfig, UIText, CSS_STYLES
    CONFIG_AVAILABLE = True
    logger.info("Config modules loaded successfully")
except ImportError as e:
    CONFIG_AVAILABLE = False
    logger.warning(f"配置模块不可用: {e}")

# 尝试导入工具模块
try:
    from utils.file_handler import FileHandler
    FILE_HANDLER_AVAILABLE = True
    logger.info("FileHandler loaded successfully")
except ImportError:
    FILE_HANDLER_AVAILABLE = False
    logger.warning("文件处理器不可用")

try:
    from utils.translator import Translator
    TRANSLATOR_AVAILABLE = True
    logger.info("Translator loaded successfully")
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("翻译器不可用")

try:
    from utils.comprehensive_sheets_manager import GoogleSheetsManager
    SHEETS_AVAILABLE = True
    logger.info("GoogleSheetsManager loaded successfully")
except ImportError:
    SHEETS_AVAILABLE = False
    logger.warning("Google Sheets 管理器不可用")

# 导入 Enhanced UI Components
try:
    from components import EnhancedUIComponents, create_ui_components
    UI_COMPONENTS_AVAILABLE = True
    logger.info("Enhanced UI Components loaded successfully")
except ImportError as e:
    UI_COMPONENTS_AVAILABLE = False
    logger.warning(f"Enhanced UI Components 不可用: {e}")

# 导入简单反馈组件
try:
    from simple_feedback_component import render_simple_feedback_form, get_feedback_metrics
    FEEDBACK_COMPONENT_AVAILABLE = True
    logger.info("Simple Feedback Component loaded successfully")
except ImportError as e:
    FEEDBACK_COMPONENT_AVAILABLE = False
    logger.warning(f"Simple Feedback Component 不可用: {e}")

# Streamlit 页面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能医疗翻译教育工具",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入基础CSS样式
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
    """基础配置类"""
    APP_TITLE = "RadiAI.Care"
    APP_SUBTITLE = "智能医疗翻译教育工具"
    APP_DESCRIPTION = "为澳洲华人社区提供专业医学文献翻译与教育服务"
    APP_VERSION = "4.2.0"
    MAX_FREE_TRANSLATIONS = 3
    SUPPORTED_FILE_TYPES = ("pdf", "txt", "docx")
    GOOGLE_SHEET_ID = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"

def get_language_config(language="简体中文"):
    """获取语言配置"""
    if CONFIG_AVAILABLE:
        try:
            config = UIText.get_language_config(language)
            # 确保页脚配置存在
            if 'footer_privacy_title' not in config:
                config.update(get_footer_config(language))
            return config
        except Exception as e:
            logger.warning(f"Failed to get language config: {e}")
    
    # 完整的备用语言配置
    return get_complete_language_config(language)

def get_footer_config(language):
    """获取页脚配置"""
    if language == "繁體中文":
        return {
            "footer_privacy_title": "隱私政策與使用條款",
            "footer_app_name": "智能醫療翻譯教育工具",
            "footer_service_desc": "為澳洲華人社群服務",
            "footer_privacy_text": "我們僅收集翻譯服務必要的資訊，所有數據採用加密傳輸和儲存，嚴格遵守澳洲隱私法（Privacy Act 1988）規定，絕不與第三方分享您的醫療資訊。",
            "footer_terms_text": "本服務僅提供醫學文獻翻譯和教育解釋，不構成任何醫療建議或診斷。用戶須為所有醫療決策自負責任，並應諮詢專業醫師意見。",
            "footer_disclaimer_text": "AI翻譯可能存在錯誤，請與醫師核實所有重要醫療資訊。緊急情況請撥打000或前往最近的急診室。",
            "footer_contact_text": "如有任何問題或建議，請聯繫 support@radiai.care | 本服務受澳洲法律管轄"
        }
    else:  # 简体中文
        return {
            "footer_privacy_title": "隐私政策与使用条款",
            "footer_app_name": "智能医疗翻译教育工具",
            "footer_service_desc": "为澳洲华人社区服务",
            "footer_privacy_text": "我们仅收集翻译服务必要的信息，所有数据采用加密传输和存储，严格遵守澳洲隐私法（Privacy Act 1988）规定，绝不与第三方分享您的医疗信息。",
            "footer_terms_text": "本服务仅提供医学文献翻译和教育解释，不构成任何医疗建议或诊断。用户须为所有医疗决策自负责任，并应咨询专业医师意见。",
            "footer_disclaimer_text": "AI翻译可能存在错误，请与医师核实所有重要医疗信息。紧急情况请拨打000或前往最近的急诊室。",
            "footer_contact_text": "如有任何问题或建议，请联系 support@radiai.care | 本服务受澳洲法律管辖"
        }

def get_complete_language_config(language):
    """获取完整的语言配置"""
    base_config = {
        "简体中文": {
            "code": "simplified_chinese",
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能医疗翻译教育工具",
            "app_description": "为澳洲华人社区提供专业医学文献翻译与教育服务",
            "disclaimer_title": "重要教育工具声明",
            "disclaimer_items": [
                "本工具为医学文献翻译和教育工具，不构成医疗建议",
                "所有内容仅供学习和教育参考",
                "请咨询专业医师进行医疗决策",
                "AI翻译可能存在错误，请核实重要信息",
                "紧急情况请拨打000"
            ],
            "input_placeholder": "请输入英文医学文献内容...",
            "file_upload": "上传文件",
            "supported_formats": "支持PDF、TXT、DOCX格式",
            "translate_button": "开始翻译学习",
            "error_empty_input": "请输入内容",
            "lang_selection": "选择语言"
        },
        "繁體中文": {
            "code": "traditional_chinese",
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能醫療翻譯教育工具",
            "app_description": "為澳洲華人社群提供專業醫學文獻翻譯與教育服務",
            "disclaimer_title": "重要教育工具聲明",
            "disclaimer_items": [
                "本工具為醫學文獻翻譯和教育工具，不構成醫療建議",
                "所有內容僅供學習和教育參考",
                "請諮詢專業醫師進行醫療決策",
                "AI翻譯可能存在錯誤，請核實重要資訊",
                "緊急情況請撥打000"
            ],
            "input_placeholder": "請輸入英文醫學文獻內容...",
            "file_upload": "上傳文件",
            "supported_formats": "支持PDF、TXT、DOCX格式",
            "translate_button": "開始翻譯學習",
            "error_empty_input": "請輸入內容",
            "lang_selection": "選擇語言"
        }
    }
    
    # 获取基础配置并添加页脚配置
    config = base_config.get(language, base_config["简体中文"])
    config.update(get_footer_config(language))
    return config

def initialize_session_state():
    """初始化会话状态"""
    if 'translation_count' not in st.session_state:
        st.session_state.translation_count = 0
    if 'daily_limit' not in st.session_state:
        st.session_state.daily_limit = 3
    if 'language' not in st.session_state:
        st.session_state.language = "简体中文"
    if 'user_session_id' not in st.session_state:
        st.session_state.user_session_id = str(uuid.uuid4())[:8]
    if 'permanent_user_id' not in st.session_state:
        # 生成持久用户ID
        today = datetime.now().strftime('%Y-%m-%d')
        raw_data = f"{st.session_state.user_session_id}_{today}"
        user_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
        st.session_state.permanent_user_id = f"user_{user_hash}"
    if 'feedback_count' not in st.session_state:
        st.session_state.feedback_count = 0
    
    # 初始化翻译结果相关状态
    if 'current_translation' not in st.session_state:
        st.session_state.current_translation = None
    if 'show_translation_result' not in st.session_state:
        st.session_state.show_translation_result = False
    
    # 初始化配置对象
    if 'app_config' not in st.session_state:
        st.session_state.app_config = AppConfig() if CONFIG_AVAILABLE else BasicConfig()
    
    # 初始化 UI 组件
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
    """使用 UI 组件渲染，如果失败则使用备用方法"""
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
    """备用标题渲染（无 logo）"""
    st.markdown('<div class="main-title">' + lang_cfg["app_title"] + '</div>', unsafe_allow_html=True)
    st.markdown(f"**{lang_cfg['app_subtitle']}**")
    st.info(lang_cfg["app_description"])

def render_language_selection_fallback(lang_cfg):
    """备用语言选择"""
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
    """备用免责声明"""
    st.markdown("### ⚠️ " + lang_cfg['disclaimer_title'])
    
    for i, item in enumerate(lang_cfg["disclaimer_items"], 1):
        st.markdown(f"**{i}.** {item}")
    
    st.warning("🆘 緊急情況請立即撥打 000")

def render_usage_status():
    """渲染使用状态"""
    current_usage = st.session_state.translation_count
    daily_limit = st.session_state.daily_limit
    remaining = daily_limit - current_usage
    feedback_count = st.session_state.get('feedback_count', 0)
    
    st.markdown("### 📊 使用状态")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日已用", f"{current_usage}/{daily_limit}")
    with col2:
        st.metric("剩余次数", remaining)
    with col3:
        if remaining > 0:
            st.metric("状态", "✅ 可用")
        else:
            st.metric("状态", "🚫 已满")
    with col4:
        st.metric("反馈次数", feedback_count)
    
    return remaining

def render_input_section(lang_cfg):
    """渲染输入区域"""
    # 尝试使用 Enhanced UI Components
    ui_components = st.session_state.get('ui_components')
    
    if ui_components and hasattr(ui_components, 'render_input_section'):
        try:
            # 调用 Enhanced UI Components，现在它会返回内容
            result = ui_components.render_input_section(lang_cfg)
            
            # Enhanced UI 现在应该返回 (text, file_type) 元组
            if isinstance(result, tuple) and len(result) == 2:
                report_text, file_type = result
                logger.info(f"Enhanced UI returned: text_length={len(report_text) if report_text else 0}, file_type={file_type}")
                
                # 如果有内容，也存储到标准的 session state 键中
                if report_text and report_text.strip():
                    st.session_state['current_report_text'] = report_text
                    st.session_state['current_file_type'] = file_type
                
                return report_text, file_type
            else:
                logger.warning(f"Enhanced UI returned unexpected format: {type(result)}")
                # 回退到检查 session state
                pass
                
        except Exception as e:
            logger.error(f"Enhanced UI Components failed: {e}")
            # 如果Enhanced UI失败，回退到备用实现
    
    # 如果Enhanced UI没有返回正确内容，检查session state
    if ui_components:
        # 尝试从Enhanced UI存储的session state键获取内容
        for text_key in ['text_input_area', 'report_text', 'uploaded_file_content', 'file_content', 'extracted_text']:
            if text_key in st.session_state and st.session_state[text_key]:
                text_content = st.session_state[text_key]
                file_type = st.session_state.get(f'{text_key}_type', 'manual')
                logger.info(f"Found content in session state: {text_key} = {len(text_content)} chars")
                return text_content, file_type
        
        # 如果Enhanced UI有get_current_input方法，尝试调用
        if hasattr(ui_components, 'get_current_input'):
            try:
                current_input = ui_components.get_current_input()
                if current_input and isinstance(current_input, tuple) and len(current_input) == 2:
                    text_content, file_type = current_input
                    if text_content and text_content.strip():
                        logger.info(f"Enhanced UI get_current_input returned: {len(text_content)} chars")
                        return text_content, file_type
            except Exception as e:
                logger.warning(f"Enhanced UI get_current_input failed: {e}")
        
        # Enhanced UI 可用但没有找到内容
        logger.warning("Enhanced UI rendered but no content found")
        return "", "enhanced_ui_no_content"
    
    # 备用实现
    logger.info("Using fallback input section")
    st.markdown("### 📝 输入文献")
    
    # 选择输入方式
    input_method = st.radio("选择输入方式:", ["文字输入", "文件上传"], horizontal=True, key="input_method_fallback")
    
    if input_method == "文字输入":
        report_text = st.text_area(
            "请输入英文医学文献内容：",
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
                    st.success("✅ 文件上传成功")
                    with st.expander("📄 文件内容预览", expanded=False):
                        preview_text = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
                        st.text_area("提取的内容：", value=preview_text, height=150, disabled=True)
                    report_text = extracted_text
                    file_type = uploaded_file.type
                else:
                    st.error("❌ 文件处理失败")
                    report_text = ""
                    file_type = "unknown"
            except Exception as e:
                st.error(f"❌ 文件处理错误: {e}")
                report_text = ""
                file_type = "error"
        else:
            if uploaded_file is None:
                report_text = ""
                file_type = "none"
            elif not FILE_HANDLER_AVAILABLE:
                st.error("❌ 文件处理功能不可用，请使用文字输入")
                report_text = ""
                file_type = "unavailable"
            else:
                report_text = ""
                file_type = "processing"
    
    return report_text, file_type

def handle_translation(report_text, file_type, lang_cfg):
    """处理翻译请求 - 带结果持久化"""
    if not TRANSLATOR_AVAILABLE:
        st.error("❌ 翻译功能不可用，请检查系统配置")
        return
    
    try:
        translator = Translator()
        
        # 生成翻译ID
        translation_id = str(uuid.uuid4())[:16]
        text_hash = hashlib.md5(report_text.encode()).hexdigest()[:16]
        
        # 验证内容
        validation = translator.validate_content(report_text)
        if not validation["is_valid"]:
            st.warning("⚠️ 内容可能不是完整的医学文献")
        
        # 执行翻译
        start_time = time.time()
        
        with st.spinner("正在翻译中..."):
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            result = translator.translate_with_progress(
                report_text, lang_cfg["code"], progress_bar, status_text
            )
            
            processing_time = time.time() - start_time
        
        if result["success"]:
            # 增加使用次数
            st.session_state.translation_count += 1
            
            # 记录到 Google Sheets
            log_usage_to_sheets(
                translation_id=translation_id,
                text_hash=text_hash,
                processing_time=processing_time,
                file_type=file_type,
                content_length=len(report_text),
                lang_cfg=lang_cfg,
                validation=validation
            )
            
            # ========== 保存翻译结果到 session_state ==========
            st.session_state['current_translation'] = {
                'translation_id': translation_id,
                'raw_text': report_text,
                'translated_text': result["content"],
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat(),
                'lang_cfg': lang_cfg,
                'file_type': file_type
            }
            
            # 设置标志表示有新的翻译结果
            st.session_state['show_translation_result'] = True
            
            # 存储翻译结果到session state（用于反馈）
            st.session_state['last_translation_id'] = translation_id
            st.session_state['last_raw_text'] = report_text
            st.session_state['last_translated_text'] = result["content"]
            st.session_state['last_processing_time'] = processing_time
            
            # 强制页面重新运行以显示结果
            st.rerun()
            
        else:
            st.error(f"❌ 翻译失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        st.error(f"❌ 翻译处理错误: {e}")
        logger.error(f"翻译错误: {e}")

def render_translation_result():
    """渲染保存的翻译结果"""
    if st.session_state.get('show_translation_result') and st.session_state.get('current_translation'):
        translation_data = st.session_state['current_translation']
        
        # 显示结果
        st.success("✅ 翻译完成")
        st.markdown("### 📄 翻译结果")
        st.markdown(translation_data['translated_text'])
        
        # 显示剩余次数
        remaining = st.session_state.daily_limit - st.session_state.translation_count
        if remaining > 0:
            st.info(f"今日还可使用 {remaining} 次")
        else:
            st.warning("今日配额已用完")
        
        # 显示反馈表单
        render_simple_feedback_section(
            translation_data['translation_id'], 
            translation_data['lang_cfg']
        )

def render_simple_feedback_section(translation_id, lang_cfg):
    """渲染简单反馈区域"""
    if FEEDBACK_COMPONENT_AVAILABLE and st.session_state.get('sheets_manager'):
        try:
            # 使用反馈组件
            result = render_simple_feedback_form(
                translation_id=translation_id,
                sheets_manager=st.session_state.sheets_manager,
                lang_cfg=lang_cfg
            )
        except Exception as e:
            logger.error(f"反馈组件渲染失败: {e}")
            # 回退到简单的反馈收集
            render_fallback_feedback(translation_id, lang_cfg)
    else:
        # 如果反馈组件不可用，使用简单的反馈收集
        render_fallback_feedback(translation_id, lang_cfg)

def render_fallback_feedback(translation_id, lang_cfg):
    """备用反馈收集"""
    feedback_key = f"feedback_submitted_{translation_id}"
    if not st.session_state.get(feedback_key, False):
        with st.expander("💬 快速反馈", expanded=False):
            st.markdown("您的评价对我们很重要！")
            
            # 不使用st.form，直接使用普通控件
            user_feedback = st.text_area(
                "请分享您的使用体验或建议",
                placeholder="例：翻译质量不错，希望增加语音播放功能...",
                height=80,
                key=f"fallback_feedback_text_{translation_id}"
            )
            
            submitted = st.button(
                "提交反馈", 
                use_container_width=True,
                key=f"fallback_submit_{translation_id}"
            )
            
            if submitted and user_feedback.strip():
                # 简单记录反馈
                st.session_state[feedback_key] = True
                st.session_state.feedback_count += 1
                st.success("✅ 感谢您的反馈！")
                st.balloons()
                logger.info(f"Fallback feedback submitted for {translation_id}")

def log_usage_to_sheets(translation_id, text_hash, processing_time, file_type, content_length, lang_cfg, validation):
    """记录使用资料到 Google Sheets"""
    if not st.session_state.get('sheets_manager'):
        logger.warning("Google Sheets 管理器不可用，跳过资料记录")
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
            },
            'user_name': '',  # 初始为空，反馈时会填入
            'user_feedback': ''  # 初始为空，反馈时会填入
        }
        
        sheets_result = st.session_state.sheets_manager.log_usage(usage_data)
        
        if sheets_result:
            logger.info(f"成功记录使用资料: {translation_id}")
        else:
            logger.error(f"记录使用资料失败: {translation_id}")
            
    except Exception as e:
        logger.error(f"记录使用资料时出错: {e}")

def render_quota_exceeded():
    """渲染配额超额界面"""
    st.error("🚫 今日免费配额已用完，请明天再来")
    st.info("💡 升级专业版可获得无限翻译次数")
    
    # 显示反馈统计
    if FEEDBACK_COMPONENT_AVAILABLE:
        try:
            feedback_metrics = get_feedback_metrics()
            if feedback_metrics['total_translations'] > 0:
                feedback_rate = feedback_metrics['feedback_rate'] * 100
                st.metric("您的反馈贡献", f"{feedback_rate:.1f}%", 
                         help="您提供反馈的比例，感谢您的参与！")
        except Exception as e:
            logger.error(f"获取反馈统计失败: {e}")
    
    # 升级选项
    with st.expander("🚀 升级专业版", expanded=False):
        st.markdown("**专业版特权：**")
        st.markdown("- ♾️ 无限翻译次数")
        st.markdown("- ⚡ 优先处理")
        st.markdown("- 📊 详细统计")
        st.markdown("- 🔄 批量处理")
        st.markdown("- 📱 移动优化")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆓 免费试用", use_container_width=True):
                st.info("发送邮件至 siyic46@gmail.com")
        with col2:
            if st.button("💳 立即升级", use_container_width=True):
                st.info("coming soon")

def render_footer():
    """渲染页脚信息"""
    # 获取当前语言配置
    lang_cfg = get_language_config(st.session_state.language)
    
    # 隐私政策和使用条款
    st.markdown(f"""
    <div style="
        text-align: center;
        color: #666;
        font-size: 0.7rem;
        margin: 2rem 0 1rem 0;
        padding: 1rem 1.2rem;
        background: linear-gradient(145deg, #f2fbff 0%, #e3f4fa 100%);
        border-radius: 15px;
        border: 1px solid #d4e8f2;
        box-shadow: 0 2px 8px rgba(13,116,184,0.08);
    ">
        <div style="
            font-size: 0.7rem;
            color: #4c7085;
            margin-bottom: 0.7rem;
            opacity: 0.9;
            font-weight: 500;
            letter-spacing: 0.5px;
        ">
            🔒 {lang_cfg['footer_privacy_title']}
        </div>
        <div style="
            font-size: 0.65rem;
            color: #777;
            line-height: 1.3;
            margin-top: 0.5rem;
        ">
            <strong>{"隐私保护" if st.session_state.language == "简体中文" else "隱私保護"}：</strong>{lang_cfg['footer_privacy_text']}
            <br><br>
            <strong>{"服务条款" if st.session_state.language == "简体中文" else "服務條款"}：</strong>{lang_cfg['footer_terms_text']}
            <br><br>
            <strong>{"免责声明" if st.session_state.language == "简体中文" else "免責聲明"}：</strong>{lang_cfg['footer_disclaimer_text']}
            <br><br>
            <strong>{"联系我们" if st.session_state.language == "简体中文" else "聯繫我們"}：</strong>{lang_cfg['footer_contact_text']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 版本信息
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 1rem 1.5rem;
        margin: 1.5rem 0 0.5rem 0;
        background: linear-gradient(145deg, #f4fcff 0%, #e5f4fb 100%);
        border-radius: 15px;
        border: 1px solid #d4e8f2;
        box-shadow: 0 4px 12px rgba(13,116,184,0.06);
    ">
        <div style="
            font-size: 0.85rem;
            color: #0d74b8;
            margin-bottom: 0.3rem;
        ">
            🏥 RadiAI.Care v4.2.0
        </div>
        <div style="
            font-size: 0.7rem;
            color: #4c7085;
            line-height: 1.4;
        ">
            {lang_cfg['footer_app_name']} | {lang_cfg['footer_service_desc']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """主应用程序函数"""
    try:
        # 初始化会话状态
        initialize_session_state()
        
        # 获取语言配置
        lang_cfg = get_language_config(st.session_state.language)
        
        # 渲染页面标题 - 优先使用 Enhanced UI Components
        header_success = render_with_ui_components('render_header', lang_cfg)
        if not header_success:
            render_header_fallback(lang_cfg)
            logger.info("Using fallback header rendering")
        else:
            logger.info("Using Enhanced UI Components for header")
        
        # 渲染语言选择 - 优先使用 Enhanced UI Components
        lang_success = render_with_ui_components('render_language_selection', lang_cfg)
        if not lang_success:
            render_language_selection_fallback(lang_cfg)
            logger.info("Using fallback language selection")
        else:
            logger.info("Using Enhanced UI Components for language selection")
        
        # 重新获取语言配置（可能已更改）
        lang_cfg = get_language_config(st.session_state.language)
        
        # 渲染免责声明 - 优先使用 Enhanced UI Components
        disclaimer_success = render_with_ui_components('render_disclaimer', lang_cfg)
        if not disclaimer_success:
            render_disclaimer_fallback(lang_cfg)
            logger.info("Using fallback disclaimer rendering")
        else:
            logger.info("Using Enhanced UI Components for disclaimer")
        
        # 显示使用状态
        remaining = render_usage_status()
        
        # 检查配额
        if remaining <= 0:
            render_quota_exceeded()
            render_footer()
            return
        
        # ========== 显示保存的翻译结果（在输入之前） ==========
        render_translation_result()
        
        # 只有在没有翻译结果时才显示输入区域
        if not (st.session_state.get('show_translation_result') and st.session_state.get('current_translation')):
            # 输入区域
            report_text, file_type = render_input_section(lang_cfg)
            
            # 添加调试信息
            logger.info(f"render_input_section returned: text_length={len(report_text) if report_text else 0}, file_type={file_type}")
            
            # 翻译按钮
            if report_text and report_text.strip():
                if st.button(lang_cfg["translate_button"], type="primary", use_container_width=True):
                    handle_translation(report_text, file_type, lang_cfg)
            else:
                # 显示调试信息
                if file_type in ["enhanced_ui", "processing"]:
                    st.info("📋 文件处理中，请稍等...")
                else:
                    st.warning(lang_cfg["error_empty_input"])
        else:
            # 如果有翻译结果，显示"开始新翻译"按钮
            if st.button("🔄 开始新翻译", type="secondary", use_container_width=True):
                # 清除翻译结果，重新显示输入区域
                st.session_state['show_translation_result'] = False
                st.session_state['current_translation'] = None
                st.rerun()
        
        # 渲染页脚
        render_footer()
        
    except Exception as e:
        logger.error(f"应用程序运行错误: {e}")
        st.error("❌ 应用遇到错误，请刷新页面重试")
        
        # 显示详细错误信息
        with st.expander("🔍 错误详情", expanded=False):
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()

