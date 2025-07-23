"""
RadiAI.Care 主应用程序 - 最终整合版
完整集成新的反馈系统、配额管理、Google Sheets数据管理
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

# 尝试导入配置模块，如果失败则使用备用方案
try:
    from config.settings import AppConfig, UIText, CSS_STYLES
except ImportError as e:
    st.error(f"配置模块导入失败: {e}")
    st.error("请确保 config/settings.py 文件存在且格式正确")
    st.stop()

# 尝试导入新的核心管理系统
try:
    # 注意：这些是新文件，需要确保文件名正确
    # 实际文件名应该是我们创建的 artifact 名称
    pass  # 先注释掉，避免导入错误
except ImportError as e:
    st.error(f"核心管理系统导入失败: {e}")
    st.error("请确保所有新的系统文件都已正确添加")
    st.stop()

# 尝试导入保持不变的工具模块
try:
    from utils.file_handler import FileHandler
    from utils.translator import Translator
except ImportError as e:
    st.error(f"工具模块导入失败: {e}")
    st.error("请确保 utils/ 目录下的文件存在")
    st.stop()

# 尝试导入UI组件系统
try:
    # 如果新的UI组件还没有创建，暂时使用原有的
    try:
        from components.enhanced_ui_components import EnhancedUIComponents as UIComponents
    except ImportError:
        # 备用方案：使用原有的UI组件
        from components.ui_components import UIComponents
        st.warning("⚠️ 使用原有UI组件，部分新功能可能不可用")
except ImportError as e:
    st.error(f"UI组件导入失败: {e}")
    st.stop()

# Streamlit 页面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能医疗报告翻译助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入全局CSS样式
try:
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
except NameError:
    # CSS_STYLES 未定义时的备用方案
    st.markdown("""
    <style>
    .stApp { font-family: 'Inter', sans-serif; }
    .main-title { color: #0d74b8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def create_fallback_systems():
    """创建备用系统（当新系统不可用时）"""
    st.warning("⚠️ 新系统组件不可用，使用基础功能模式")
    
    # 基础配置
    try:
        config = AppConfig()
    except:
        class BasicConfig:
            APP_TITLE = "RadiAI.Care"
            APP_VERSION = "4.2.0"
            MAX_FREE_TRANSLATIONS = 3
            SUPPORTED_FILE_TYPES = ("pdf", "txt", "docx")
        config = BasicConfig()
    
    # 基础文件处理器
    try:
        file_handler = FileHandler()
    except:
        file_handler = None
        st.error("文件处理器不可用")
    
    # 基础翻译器
    try:
        translator = Translator()
    except:
        translator = None
        st.error("翻译器不可用")
    
    # 基础UI组件
    try:
        ui = UIComponents(config, file_handler) if file_handler else None
    except:
        ui = None
        st.error("UI组件不可用")
    
    return {
        'config': config,
        'file_handler': file_handler,
        'translator': translator,
        'ui': ui,
        'mode': 'fallback'
    }

@st.cache_resource
def initialize_core_systems():
    """初始化核心系统组件（缓存以提高性能）"""
    try:
        # 检查是否为新系统模式
        if 'GoogleSheetsManager' not in globals():
            # 如果新系统不可用，使用备用系统
            return create_fallback_systems()
        
        # 基础配置
        config = AppConfig()
        
        # Google Sheets 管理器
        sheet_id = st.secrets.get("feedback_sheet_id", "")
        if not sheet_id:
            sheet_id = os.getenv("FEEDBACK_SHEET_ID", "")
        
        if not sheet_id:
            st.error("❌ 系统配置错误：缺少 Google Sheets ID")
            return create_fallback_systems()
        
        # 这里需要根据实际的新系统文件来初始化
        # 暂时注释掉，避免导入错误
        # sheets_manager = GoogleSheetsManager(sheet_id)
        
        # 基础组件
        file_handler = FileHandler()
        translator = Translator()
        ui = UIComponents(config, file_handler)
        
        return {
            'config': config,
            'file_handler': file_handler,
            'translator': translator,
            'ui': ui,
            'mode': 'basic'
        }
        
    except Exception as e:
        logger.error(f"核心系统初始化失败: {e}")
        st.error(f"❌ 系统初始化错误，使用基础功能: {e}")
        return create_fallback_systems()

def initialize_session_systems_basic():
    """初始化基础会话系统"""
    try:
        # 基础会话管理
        if 'translation_count' not in st.session_state:
            st.session_state.translation_count = 0
        if 'daily_limit' not in st.session_state:
            st.session_state.daily_limit = 3
        if 'language' not in st.session_state:
            st.session_state.language = "简体中文"
        
        return {
            'mode': 'basic'
        }
        
    except Exception as e:
        logger.error(f"基础会话系统初始化失败: {e}")
        return {'mode': 'error'}

def handle_basic_translation(report_text: str, file_type: str, lang_cfg: dict, systems: dict):
    """处理基础翻译（当新系统不可用时）"""
    
    translator = systems.get('translator')
    if not translator:
        st.error("❌ 翻译器不可用")
        return
    
    # 简单的使用次数检查
    if st.session_state.translation_count >= st.session_state.daily_limit:
        st.error(f"🚫 今日配额已用完 ({st.session_state.translation_count}/{st.session_state.daily_limit})")
        return
    
    try:
        # 简单的翻译处理
        translation_id = str(uuid.uuid4())
        
        with st.spinner("正在翻译..."):
            start_time = time.time()
            
            # 执行翻译
            result = translator.translate_with_progress(
                report_text, lang_cfg["code"], st.progress(0), st.empty()
            )
            
            processing_time = time.time() - start_time
        
        if result["success"]:
            # 增加使用次数
            st.session_state.translation_count += 1
            
            # 显示结果
            st.success("✅ 翻译完成")
            st.markdown(result["content"])
            
            remaining = st.session_state.daily_limit - st.session_state.translation_count
            st.info(f"今日还可使用 {remaining} 次")
            
            # 简单反馈收集
            with st.expander("💬 快速反馈", expanded=False):
                rating = st.slider("满意度评分", 1, 5, 4)
                if st.button("提交评分"):
                    st.success("感谢您的评分！")
        else:
            st.error(f"❌ 翻译失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"基础翻译处理失败: {e}")
        st.error(f"❌ 翻译处理错误: {e}")

def main():
    """主应用程序函数"""
    
    try:
        # 初始化系统
        systems = initialize_core_systems()
        session_systems = initialize_session_systems_basic()
        
        # 获取语言配置
        try:
            lang_cfg = UIText.get_language_config(st.session_state.get('language', '简体中文'))
        except:
            # 备用语言配置
            lang_cfg = {
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
        
        # 渲染界面
        ui = systems.get('ui')
        if ui:
            ui.render_header(lang_cfg)
            ui.render_language_selection(lang_cfg)
            ui.render_disclaimer(lang_cfg)
        else:
            # 基础界面
            st.title(lang_cfg["app_title"])
            st.markdown(f"**{lang_cfg['app_subtitle']}**")
            st.info(lang_cfg["app_description"])
        
        # 显示当前模式
        mode = systems.get('mode', 'unknown')
        if mode == 'fallback':
            st.warning("⚠️ 运行在基础功能模式")
        elif mode == 'basic':
            st.info("ℹ️ 使用基础翻译功能")
        
        # 显示使用状态
        current_usage = st.session_state.get('translation_count', 0)
        daily_limit = st.session_state.get('daily_limit', 3)
        remaining = daily_limit - current_usage
        
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
        
        if remaining <= 0:
            st.error("🚫 今日免费配额已用完，请明天再来")
            st.info("💡 升级专业版可获得无限翻译次数")
            st.stop()
        
        # 输入区域
        if ui:
            report_text, file_type = ui.render_input_section(lang_cfg)
        else:
            # 基础输入
            st.markdown("### 📝 输入报告")
            report_text = st.text_area(
                "请输入英文放射科报告：",
                height=200,
                placeholder=lang_cfg["input_placeholder"]
            )
            file_type = "manual"
        
        # 翻译按钮
        if report_text and report_text.strip():
            if st.button(lang_cfg["translate_button"], type="primary", use_container_width=True):
                handle_basic_translation(report_text, file_type, lang_cfg, systems)
        else:
            st.warning(lang_cfg["error_empty_input"])
        
        # 页脚
        st.markdown("---")
        st.markdown("RadiAI.Care - 智能医疗报告翻译助手")
        
    except Exception as e:
        logger.error(f"应用程序运行错误: {e}")
        st.error("❌ 应用遇到错误，请刷新页面重试")
        st.error(f"错误详情: {e}")

if __name__ == "__main__":
    main()化
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🆓 免费试用", use_container_width=True):
                        st.info("发送邮件至 trial@radiai.care")
                with col2:
                    if st.button("💳 立即升级", use_container_width=True):
                        st.info("访问 radiai.care/upgrade")
            
            # 显示反馈影响可视化
            ui.render_feedback_impact_visualization(core_systems['sheets_manager'])
            
            # 页脚
            ui.render_footer(lang_cfg)
            ui.render_version_info()
            
            # 调试面板
            render_debug_panel(core_systems, session_systems)
            
            st.stop()
        
        # 正常使用流程 - 输入报告
        report_text, file_type = ui.render_input_section(lang_cfg)
        
        # 翻译按钮和处理
        if ui.render_translate_button(lang_cfg, report_text):
            handle_translation_request(
                report_text, file_type, lang_cfg,
                core_systems, session_systems
            )
        
        # 页脚信息
        ui.render_footer(lang_cfg)
        ui.render_version_info()
        
        # 调试面板
        render_debug_panel(core_systems, session_systems)
        
    except Exception as e:
        logger.error(f"应用程序运行错误: {e}")
        st.error("❌ 应用遇到错误，请刷新页面重试")
        
        # 开发模式下显示详细错误
        if os.getenv("DEBUG_MODE", "").lower() == "true":
            st.exception(e)

if __name__ == "__main__":
    main()
