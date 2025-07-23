"""
RadiAI.Care 主应用程序 - 最终整合版
完整集成新的反馈系统、配额管理、Google Sheets数据管理
"""

import os
import time
import uuid
import streamlit as st
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入配置模块
from config.settings import AppConfig, UIText, CSS_STYLES

# 导入新的核心管理系统
from utils.comprehensive_sheets_manager import GoogleSheetsManager
from utils.integrated_session_manager import IntegratedSessionManager
from utils.advanced_feedback_system import (
    AdvancedFeedbackCollector, 
    SmartFeedbackIntegration
)

# 导入保持不变的工具模块
from utils.file_handler import FileHandler
from utils.translator import Translator

# 导入新的UI组件系统
from components.enhanced_ui_components import EnhancedUIComponents

# Streamlit 页面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能医疗报告翻译助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 注入全局CSS样式
st.markdown(CSS_STYLES, unsafe_allow_html=True)

@st.cache_resource
def initialize_core_systems():
    """初始化核心系统组件（缓存以提高性能）"""
    try:
        # 基础配置
        config = AppConfig()
        
        # Google Sheets 管理器
        sheet_id = st.secrets.get("feedback_sheet_id", "")
        if not sheet_id:
            sheet_id = os.getenv("FEEDBACK_SHEET_ID", "")
        
        if not sheet_id:
            logger.error("未找到 Google Sheets ID")
            st.error("❌ 系统配置错误：缺少 Google Sheets ID")
            st.stop()
        
        sheets_manager = GoogleSheetsManager(sheet_id)
        logger.info("Google Sheets 管理器初始化成功")
        
        # 文件处理器和翻译器
        file_handler = FileHandler()
        translator = Translator()
        
        # UI组件系统
        ui = EnhancedUIComponents(config, file_handler)
        
        return {
            'config': config,
            'sheets_manager': sheets_manager,
            'file_handler': file_handler,
            'translator': translator,
            'ui': ui,
            'sheet_id': sheet_id
        }
        
    except Exception as e:
        logger.error(f"核心系统初始化失败: {e}")
        st.error(f"❌ 系统初始化错误: {e}")
        st.stop()

def initialize_session_systems(sheets_manager):
    """初始化会话相关系统（每次会话重新创建）"""
    try:
        # 整合的会话管理器
        session_manager = IntegratedSessionManager(sheets_manager)
        
        # 高级反馈收集器
        feedback_collector = AdvancedFeedbackCollector(sheets_manager)
        
        # 智能反馈集成系统
        smart_feedback = SmartFeedbackIntegration(sheets_manager, session_manager)
        
        return {
            'session_manager': session_manager,
            'feedback_collector': feedback_collector,
            'smart_feedback': smart_feedback
        }
        
    except Exception as e:
        logger.error(f"会话系统初始化失败: {e}")
        st.error(f"❌ 会话系统错误: {e}")
        st.stop()

def test_system_health(sheets_manager):
    """测试系统健康状态"""
    try:
        # 测试 Google Sheets 连接
        connection_test = sheets_manager.test_connection()
        
        if not connection_test['connected']:
            st.warning("⚠️ Google Sheets 连接异常，部分功能可能受限")
            logger.warning(f"Sheets connection issue: {connection_test.get('error')}")
            return False
        
        logger.info("系统健康检查通过")
        return True
        
    except Exception as e:
        logger.error(f"系统健康检查失败: {e}")
        st.warning("⚠️ 系统健康检查异常，继续使用基础功能")
        return False

def handle_translation_request(report_text: str, file_type: str, lang_cfg: dict,
                             core_systems: dict, session_systems: dict):
    """处理翻译请求的完整流程"""
    
    translator = core_systems['translator']
    session_manager = session_systems['session_manager']
    sheets_manager = core_systems['sheets_manager']
    ui = core_systems['ui']
    feedback_collector = session_systems['feedback_collector']
    smart_feedback = session_systems['smart_feedback']
    
    # 生成翻译ID和文本哈希
    translation_id = str(uuid.uuid4())
    text_hash = session_manager.generate_text_hash(report_text)
    
    try:
        # 验证内容
        validation = translator.validate_content(report_text)
        if not validation["is_valid"]:
            st.warning("⚠️ 无法确认内容为有效放射科报告，请再确认输入内容")
        
        # 记录使用开始
        content_length = len(report_text)
        start_time = time.time()
        
        # 翻译进度显示
        with st.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 执行翻译
                result = translator.translate_with_progress(
                    report_text, lang_cfg["code"], progress_bar, status_text
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                if result["success"]:
                    # 翻译成功处理
                    handle_translation_success(
                        translation_id, text_hash, result, processing_time_ms,
                        file_type, content_length, validation, lang_cfg,
                        core_systems, session_systems
                    )
                    
                else:
                    # 翻译失败处理
                    handle_translation_failure(
                        translation_id, result.get("error", "未知错误"),
                        processing_time_ms, file_type, content_length,
                        session_manager, sheets_manager
                    )
                    
            finally:
                # 清理进度显示
                progress_bar.empty()
                status_text.empty()
                
    except Exception as e:
        # 处理未预期的错误
        logger.error(f"翻译处理异常: {e}")
        session_manager.restore_usage_on_failure(translation_id)
        st.error(f"❌ 处理过程中发生错误: {e}")

def handle_translation_success(translation_id: str, text_hash: str, result: dict,
                             processing_time_ms: int, file_type: str, content_length: int,
                             validation: dict, lang_cfg: dict,
                             core_systems: dict, session_systems: dict):
    """处理翻译成功的情况"""
    
    session_manager = session_systems['session_manager']
    sheets_manager = core_systems['sheets_manager']
    ui = core_systems['ui']
    smart_feedback = session_systems['smart_feedback']
    
    # 记录成功的使用
    usage_success = session_manager.record_translation_usage(
        translation_id=translation_id,
        text_hash=text_hash,
        processing_time_ms=processing_time_ms,
        file_type=file_type,
        content_length=content_length
    )
    
    if not usage_success:
        logger.warning("使用记录失败，但翻译结果正常显示")
    
    # 显示翻译结果
    st.success("✅ 翻译完成")
    ui.render_translation_result(result["content"], lang_cfg)
    
    # 显示完成状态
    updated_usage_stats = session_manager.get_enhanced_usage_stats()
    remaining = updated_usage_stats.get('remaining', 0)
    
    if remaining > 0:
        remaining_msg = f"✅ 翻译完成！您今日还有 {remaining} 次使用机会。"
        if updated_usage_stats.get('bonus_quota', 0) > 0:
            remaining_msg += f"（含 {updated_usage_stats['bonus_quota']} 次奖励配额）"
        st.info(remaining_msg)
    else:
        st.warning("✅ 翻译完成！您今日的配额已全部使用。")
    
    # 计算翻译质量评分（基于验证结果）
    translation_quality = validation.get("confidence", 0.8)
    
    # 渲染智能反馈系统
    smart_feedback.render_smart_feedback_flow(
        translation_id=translation_id,
        user_id=st.session_state.get('permanent_user_id', ''),
        translation_quality_score=translation_quality,
        processing_time_ms=processing_time_ms
    )

def handle_translation_failure(translation_id: str, error_message: str,
                             processing_time_ms: int, file_type: str, content_length: int,
                             session_manager, sheets_manager):
    """处理翻译失败的情况"""
    
    # 恢复使用次数
    session_manager.restore_usage_on_failure(translation_id)
    
    # 记录失败日志
    try:
        failure_data = {
            'user_id': st.session_state.get('permanent_user_id', ''),
            'session_id': st.session_state.get('user_session_id', ''),
            'translation_id': translation_id,
            'daily_count': st.session_state.get('current_usage_session', {}).get('daily_count', 0),
            'session_count': 0,
            'processing_time_ms': processing_time_ms,
            'file_type': file_type,
            'content_length': content_length,
            'status': 'failed',
            'error_message': error_message,
            'extra_data': {'failure_reason': error_message}
        }
        sheets_manager.log_usage(failure_data)
    except Exception as e:
        logger.error(f"记录失败日志时出错: {e}")
    
    # 显示错误信息
    st.error(f"❌ 翻译失败: {error_message}")
    st.info("💡 您的使用次数已恢复，请检查输入内容后重试")

def render_debug_panel(core_systems: dict, session_systems: dict):
    """渲染调试面板（侧边栏）"""
    
    if not st.sidebar.checkbox("🔧 调试模式"):
        return
    
    st.sidebar.markdown("### 🔧 系统调试")
    
    session_manager = session_systems['session_manager']
    sheets_manager = core_systems['sheets_manager']
    
    # 显示系统状态
    if st.sidebar.button("📊 系统状态"):
        debug_info = session_manager.get_enhanced_usage_stats()
        st.sidebar.json(debug_info)
    
    # 测试连接
    if st.sidebar.button("🔌 测试连接"):
        connection_test = sheets_manager.test_connection()
        st.sidebar.json(connection_test)
    
    # 强制同步
    if st.sidebar.button("🔄 强制同步"):
        try:
            session_manager._update_quota_status()
            st.sidebar.success("同步完成")
        except Exception as e:
            st.sidebar.error(f"同步失败: {e}")
    
    # 重置使用次数（测试用）
    if st.sidebar.button("🔄 重置配额 (测试)", type="secondary"):
        if st.sidebar.button("确认重置", key="confirm_reset"):
            try:
                # 重置会话状态
                st.session_state.current_usage_session = None
                st.session_state.quota_status = None
                st.session_state.satisfaction_history = []
                st.session_state.feedback_history = []
                st.session_state.bonus_quota_earned = 0
                
                st.sidebar.success("配额已重置")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"重置失败: {e}")
    
    # 显示会话信息
    if st.sidebar.expander("💾 会话信息", expanded=False):
        session_info = {
            'user_id': st.session_state.get('permanent_user_id', '')[:12] + "****",
            'device_id': st.session_state.get('device_id', ''),
            'session_id': st.session_state.get('user_session_id', ''),
            'language': st.session_state.get('language', ''),
            'session_initialized': st.session_state.get('session_initialized', False)
        }
        st.sidebar.json(session_info)

def main():
    """主应用程序函数"""
    
    try:
        # 初始化核心系统
        core_systems = initialize_core_systems()
        
        # 测试系统健康状态
        system_healthy = test_system_health(core_systems['sheets_manager'])
        
        # 初始化会话系统
        session_systems = initialize_session_systems(core_systems['sheets_manager'])
        
        # 初始化会话状态
        session_systems['session_manager'].init_session_state()
        
        # 获取语言配置
        lang_cfg = UIText.get_language_config(st.session_state.language)
        
        # 渲染界面组件
        ui = core_systems['ui']
        ui.render_header(lang_cfg)
        ui.render_language_selection(lang_cfg)
        
        # 重新获取语言配置（可能已更改）
        lang_cfg = UIText.get_language_config(st.session_state.language)
        ui.render_disclaimer(lang_cfg)
        
        # 显示智能使用仪表板
        usage_stats = session_systems['session_manager'].get_enhanced_usage_stats()
        can_use, reason = session_systems['session_manager'].can_use_translation()
        
        remaining = ui.render_intelligent_usage_dashboard(
            usage_stats, 
            session_systems['feedback_collector'],
            session_systems['session_manager']
        )
        
        # 如果配额已用完，显示特殊界面
        if not can_use:
            st.markdown("---")
            st.error(f"🚫 {reason}")
            
            # 显示获得额外配额的方法
            unlock_suggestions = session_systems['session_manager'].get_quota_unlock_suggestions()
            if unlock_suggestions:
                st.markdown("### 💡 获得额外配额")
                for suggestion in unlock_suggestions:
                    with st.expander(f"🎯 {suggestion['title']} (+{suggestion['potential_bonus']} 次)"):
                        st.markdown(f"**说明：** {suggestion['description']}")
                        st.markdown(f"**操作：** {suggestion['action']}")
            
            # 显示升级选项
            with st.expander("🚀 升级专业版 - 解除所有限制", expanded=False):
                st.markdown("""
                **专业版特权：**
                - ♾️ 无限翻译次数
                - ⚡ 优先处理
                - 📊 详细统计
                - 🔄 批量处理
                - 📱 移动优化
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
