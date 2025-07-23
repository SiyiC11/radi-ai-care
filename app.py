"""
RadiAI.Care 主应用程序 - 修复版
确保语法正确，渐进式功能启用
"""

import os
import time
import uuid
import logging
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
except ImportError as e:
    CONFIG_AVAILABLE = False
    logger.warning(f"配置模块不可用: {e}")

# 尝试导入工具模块
try:
    from utils.file_handler import FileHandler
    FILE_HANDLER_AVAILABLE = True
except ImportError:
    FILE_HANDLER_AVAILABLE = False
    logger.warning("文件处理器不可用")

try:
    from utils.translator import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("翻译器不可用")

# 尝试导入UI组件
try:
    from components.ui_components import UIComponents
    UI_COMPONENTS_AVAILABLE = True
except ImportError:
    UI_COMPONENTS_AVAILABLE = False
    logger.warning("UI组件不可用")

# Streamlit 页面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能医疗报告翻译助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入基础CSS样式
if CONFIG_AVAILABLE:
    try:
        st.markdown(CSS_STYLES, unsafe_allow_html=True)
    except:
        pass
else:
    st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }
    .main-title { color: #0d74b8; font-weight: bold; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

class BasicConfig:
    """基础配置类"""
    APP_TITLE = "RadiAI.Care"
    APP_SUBTITLE = "智能医疗报告翻译助手"
    APP_DESCRIPTION = "为澳洲华人社区提供专业医学报告翻译服务"
    APP_VERSION = "4.2.0"
    MAX_FREE_TRANSLATIONS = 3
    SUPPORTED_FILE_TYPES = ("pdf", "txt", "docx")

def get_language_config(language="简体中文"):
    """获取语言配置"""
    if CONFIG_AVAILABLE:
        try:
            return UIText.get_language_config(language)
        except:
            pass
    
    # 备用语言配置
    return {
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
    }

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

def render_header(lang_cfg):
    """渲染页面头部"""
    st.markdown('<div class="main-title">' + lang_cfg["app_title"] + '</div>', unsafe_allow_html=True)
    st.markdown(f"**{lang_cfg['app_subtitle']}**")
    st.info(lang_cfg["app_description"])

def render_language_selection(lang_cfg):
    """渲染语言选择"""
    st.markdown(f"### {lang_cfg['lang_selection']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("繁體中文", key="lang_traditional", use_container_width=True,
                    type="primary" if st.session_state.language == "繁體中文" else "secondary"):
            st.session_state.language = "繁體中文"
            st.rerun()
    with col2:
        if st.button("简体中文", key="lang_simplified", use_container_width=True,
                    type="primary" if st.session_state.language == "简体中文" else "secondary"):
            st.session_state.language = "简体中文"
            st.rerun()

def render_disclaimer(lang_cfg):
    """渲染免责声明"""
    st.markdown("### ⚠️ " + lang_cfg['disclaimer_title'])
    
    for i, item in enumerate(lang_cfg["disclaimer_items"], 1):
        st.markdown(f"**{i}.** {item}")
    
    st.warning("🆘 紧急情况请立即拨打 000")

def render_usage_status():
    """渲染使用状态"""
    current_usage = st.session_state.translation_count
    daily_limit = st.session_state.daily_limit
    remaining = daily_limit - current_usage
    
    st.markdown("### 📊 使用状态")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("今日已用", f"{current_usage}/{daily_limit}")
    with col2:
        st.metric("剩余次数", remaining)
    with col3:
        if remaining > 0:
            st.metric("状态", "✅ 可用")
        else:
            st.metric("状态", "🚫 已满")
    
    return remaining

def render_input_section(lang_cfg):
    """渲染输入区域"""
    st.markdown("### 📝 输入报告")
    
    # 选择输入方式
    input_method = st.radio("选择输入方式:", ["文字输入", "文件上传"], horizontal=True)
    
    if input_method == "文字输入":
        report_text = st.text_area(
            "请输入英文放射科报告：",
            height=200,
            placeholder=lang_cfg["input_placeholder"]
        )
        file_type = "manual"
    else:
        uploaded_file = st.file_uploader(
            lang_cfg["file_upload"],
            type=['pdf', 'txt', 'docx'],
            help=lang_cfg["supported_formats"]
        )
        
        if uploaded_file:
            if FILE_HANDLER_AVAILABLE:
                try:
                    file_handler = FileHandler()
                    extracted_text, result = file_handler.extract_text(uploaded_file)
                    if extracted_text:
                        st.success("✅ 文件上传成功")
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
                st.error("❌ 文件处理功能不可用，请使用文字输入")
                report_text = ""
                file_type = "unavailable"
        else:
            report_text = ""
            file_type = "none"
    
    return report_text, file_type

def handle_translation(report_text, file_type, lang_cfg):
    """处理翻译请求"""
    if not TRANSLATOR_AVAILABLE:
        st.error("❌ 翻译功能不可用，请检查系统配置")
        return
    
    try:
        translator = Translator()
        
        # 验证内容
        validation = translator.validate_content(report_text)
        if not validation["is_valid"]:
            st.warning("⚠️ 内容可能不是完整的放射科报告")
        
        # 执行翻译
        with st.spinner("正在翻译中..."):
            start_time = time.time()
            
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
            
            # 显示结果
            st.success("✅ 翻译完成")
            st.markdown("### 📄 翻译结果")
            st.markdown(result["content"])
            
            # 显示剩余次数
            remaining = st.session_state.daily_limit - st.session_state.translation_count
            if remaining > 0:
                st.info(f"今日还可使用 {remaining} 次")
            else:
                st.warning("今日配额已用完")
            
            # 简单反馈收集
            render_simple_feedback()
            
        else:
            st.error(f"❌ 翻译失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        st.error(f"❌ 翻译处理错误: {e}")

def render_simple_feedback():
    """渲染简单反馈"""
    with st.expander("💬 快速反馈", expanded=False):
        st.markdown("您的评价对我们很重要！")
        
        col1, col2 = st.columns(2)
        with col1:
            rating = st.slider("满意度评分", 1, 5, 4, help="1=很差，5=很好")
        with col2:
            if st.button("提交评分", type="primary"):
                st.success("感谢您的评分！")
                st.balloons()

def render_quota_exceeded():
    """渲染配额超额界面"""
    st.error("🚫 今日免费配额已用完，请明天再来")
    st.info("💡 升级专业版可获得无限翻译次数")
    
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
                st.info("发送邮件至 trial@radiai.care")
        with col2:
            if st.button("💳 立即升级", use_container_width=True):
                st.info("访问 radiai.care/upgrade")

def render_debug_panel():
    """渲染调试面板"""
    if st.sidebar.checkbox("🔧 调试模式"):
        st.sidebar.markdown("### 🔧 系统调试")
        
        # 显示系统状态
        if st.sidebar.button("📊 系统状态"):
            debug_info = {
                'translation_count': st.session_state.translation_count,
                'daily_limit': st.session_state.daily_limit,
                'language': st.session_state.language,
                'session_id': st.session_state.user_session_id,
                'modules_available': {
                    'config': CONFIG_AVAILABLE,
                    'translator': TRANSLATOR_AVAILABLE,
                    'file_handler': FILE_HANDLER_AVAILABLE,
                    'ui_components': UI_COMPONENTS_AVAILABLE
                }
            }
            st.sidebar.json(debug_info)
        
        # 重置配额
        if st.sidebar.button("🔄 重置配额"):
            st.session_state.translation_count = 0
            st.sidebar.success("配额已重置")
            st.rerun()

def main():
    """主应用程序函数"""
    try:
        # 初始化会话状态
        initialize_session_state()
        
        # 获取语言配置
        lang_cfg = get_language_config(st.session_state.language)
        
        # 渲染界面
        render_header(lang_cfg)
        render_language_selection(lang_cfg)
        
        # 重新获取语言配置（可能已更改）
        lang_cfg = get_language_config(st.session_state.language)
        render_disclaimer(lang_cfg)
        
        # 显示使用状态
        remaining = render_usage_status()
        
        # 检查配额
        if remaining <= 0:
            render_quota_exceeded()
            render_debug_panel()
            return
        
        # 输入区域
        report_text, file_type = render_input_section(lang_cfg)
        
        # 翻译按钮
        if report_text and report_text.strip():
            if st.button(lang_cfg["translate_button"], type="primary", use_container_width=True):
                handle_translation(report_text, file_type, lang_cfg)
        else:
            st.warning(lang_cfg["error_empty_input"])
        
        # 页脚
        st.markdown("---")
        st.markdown("RadiAI.Care v4.2.0 - 智能医疗报告翻译助手")
        
        # 调试面板
        render_debug_panel()
        
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
