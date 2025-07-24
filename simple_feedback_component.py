"""
RadiAI.Care - 簡單反饋組件
用於收集用戶的文字反饋並存儲到 UsageLog 表中
"""

import streamlit as st
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def render_simple_feedback_form(translation_id: str, sheets_manager, lang_cfg: Dict[str, str]) -> bool:
    """
    渲染簡單的用戶反饋表單
    
    Args:
        translation_id: 翻譯ID，用於關聯反饋
        sheets_manager: Google Sheets 管理器實例
        lang_cfg: 語言配置字典
        
    Returns:
        bool: 是否成功提交反饋
    """
    
    # 檢查是否已經提交過反饋
    feedback_key = f"feedback_submitted_{translation_id}"
    if st.session_state.get(feedback_key, False):
        st.info("✅ 感謝您已經提交的寶貴建議！")
        return True
    
    # 根據語言選擇標題和說明文字
    if lang_cfg.get('code') == 'traditional_chinese':
        title = "💭 幫助我們改進學習體驗"
        description = "您的建議將幫助我們優化這個醫學翻譯教育工具"
        name_placeholder = "您的称呼（选填）"
        name_example = "例：医学生小王"
        feedback_label = "请分享您的使用体验或改进建议"
        feedback_placeholder = "例：希望增加医学术语发音功能，或翻译速度可以更快一些..."
        submit_button = "💌 送出建议"
        success_message = "✅ 感谢您的宝贵建议！我们会持续优化 RadiAI.Care！"
    
    with st.expander(title, expanded=False):
        st.markdown(f"*{description}*")
        
        with st.form(f"simple_feedback_form_{translation_id}"):
            # 用户姓名输入
            user_name = st.text_input(
                name_placeholder,
                placeholder=name_example,
                key=f"feedback_name_{translation_id}"
            )
            
            # 用户反馈输入
            user_feedback = st.text_area(
                feedback_label,
                placeholder=feedback_placeholder,
                height=100,
                key=f"feedback_text_{translation_id}"
            )
            
            # 提交按钮
            submitted = st.form_submit_button(submit_button, use_container_width=True)
            
            if submitted:
                if user_feedback.strip():  # 确保反馈内容不为空
                    success = _submit_feedback_to_sheets(
                        translation_id=translation_id,
                        user_name=user_name.strip(),
                        user_feedback=user_feedback.strip(),
                        sheets_manager=sheets_manager
                    )
                    
                    if success:
                        st.success(success_message)
                        st.balloons()
                        # 标记已提交反馈
                        st.session_state[feedback_key] = True
                        # 稍后刷新页面以显示感谢信息
                        st.rerun()
                        return True
                    else:
                        st.error("❌ 反馈提交失败，请稍后重试")
                        return False
                else:
                    st.warning("⚠️ 请填写您的建议后再提交")
                    return False
    
    return False

def _submit_feedback_to_sheets(translation_id: str, user_name: str, user_feedback: str, sheets_manager) -> bool:
    """
    提交反馈到 Google Sheets
    
    Args:
        translation_id: 翻译ID
        user_name: 用户姓名
        user_feedback: 用户反馈内容
        sheets_manager: Google Sheets 管理器实例
        
    Returns:
        bool: 是否成功提交
    """
    try:
        # 构建反馈数据
        feedback_data = {
            'user_id': st.session_state.get('permanent_user_id', ''),
            'session_id': st.session_state.get('user_session_id', ''),
            'translation_id': translation_id,
            'daily_count': st.session_state.get('translation_count', 0),
            'session_count': len(st.session_state.get('session_translations', [])),
            'user_name': user_name,
            'user_feedback': user_feedback,
            'language': st.session_state.get('language', 'zh_CN'),
            'device_info': _get_device_info(),
            'ip_hash': _get_ip_hash(),
            'user_agent': _get_user_agent(),
            'extra_data': {
                'feedback_type': 'simple_text',
                'app_version': '4.2.0',
                'submission_source': 'main_app',
                'feedback_length': len(user_feedback),
                'has_user_name': bool(user_name.strip())
            }
        }
        
        # 使用专门的反馈记录方法
        success = sheets_manager.log_feedback_to_usage(feedback_data)
        
        if success:
            logger.info(f"Successfully submitted simple feedback for translation: {translation_id}")
            
            # 更新session state中的反馈统计
            if 'feedback_count' not in st.session_state:
                st.session_state.feedback_count = 0
            st.session_state.feedback_count += 1
            
            return True
        else:
            logger.error(f"Failed to submit feedback for translation: {translation_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return False

def _get_device_info() -> str:
    """获取设备信息"""
    # 从 session state 获取设备信息，如果没有则返回默认值
    device_type = st.session_state.get('device_type', 'web')
    browser_info = st.session_state.get('browser_info', 'unknown')
    return f"{device_type}_{browser_info}"

def _get_ip_hash() -> str:
    """获取IP地址哈希（隐私保护）"""
    # 使用会话ID生成一个隐私保护的哈希值
    session_id = st.session_state.get('user_session_id', 'unknown')
    return hashlib.md5(session_id.encode()).hexdigest()[:8]

def _get_user_agent() -> str:
    """获取用户代理信息"""
    # 在 Streamlit 环境中，我们无法直接获取真实的 User Agent
    # 返回一个标识 Streamlit 应用的字符串
    return "RadiAI.Care/4.2.0 (Streamlit Web App)"

def render_feedback_summary(sheets_manager) -> None:
    """
    渲染反馈统计摘要（可选功能，用于管理员查看）
    
    Args:
        sheets_manager: Google Sheets 管理器实例
    """
    try:
        # 获取今日分析数据
        analytics = sheets_manager.get_daily_analytics()
        
        if analytics:
            with st.expander("📊 今日反馈统计", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "简单反馈数", 
                        analytics.get('simple_feedback_count', 0),
                        help="用户通过简单反馈表单提交的建议数量"
                    )
                
                with col2:
                    st.metric(
                        "详细反馈数", 
                        analytics.get('detailed_feedback_count', 0),
                        help="用户通过详细反馈表单提交的反馈数量"
                    )
                
                with col3:
                    st.metric(
                        "总反馈数", 
                        analytics.get('feedback_count', 0),
                        help="今日收到的所有反馈总数"
                    )
                
                # 显示一些反馈样本
                feedback_samples = analytics.get('simple_feedback_samples', [])
                if feedback_samples:
                    st.markdown("**最近的用户建议：**")
                    for i, feedback in enumerate(feedback_samples[:3], 1):
                        st.markdown(f"{i}. {feedback}")
                        
    except Exception as e:
        logger.error(f"Error rendering feedback summary: {e}")
        st.error("无法加载反馈统计数据")

def get_feedback_metrics() -> Dict[str, Any]:
    """
    获取当前session的反馈相关指标
    
    Returns:
        Dict: 反馈指标数据
    """
    return {
        'session_feedback_count': st.session_state.get('feedback_count', 0),
        'has_submitted_feedback': any(
            key.startswith('feedback_submitted_') 
            for key in st.session_state.keys()
        ),
        'total_translations': st.session_state.get('translation_count', 0),
        'feedback_rate': (
            st.session_state.get('feedback_count', 0) / 
            max(st.session_state.get('translation_count', 1), 1)
        )
    }

# 测试函数
def test_feedback_component():
    """测试反馈组件功能"""
    print("=== 测试反馈组件功能 ===")
    
    # 模拟session state
    test_session = {
        'permanent_user_id': 'test_user_123',
        'user_session_id': 'session_456',
        'translation_count': 2,
        'language': 'simplified_chinese'
    }
    
    # 测试数据构建
    test_translation_id = "trans_test_789"
    test_user_name = "测试用户"
    test_feedback = "希望增加语音播放功能"
    
    print(f"测试翻译ID: {test_translation_id}")
    print(f"测试用户名: {test_user_name}")
    print(f"测试反馈: {test_feedback}")
    
    # 测试设备信息生成
    device_info = "web_unknown"  # 模拟_get_device_info()的输出
    ip_hash = hashlib.md5("session_456".encode()).hexdigest()[:8]
    user_agent = "RadiAI.Care/4.2.0 (Streamlit Web App)"
    
    print(f"\n生成的元数据:")
    print(f"设备信息: {device_info}")
    print(f"IP哈希: {ip_hash}")
    print(f"用户代理: {user_agent}")
    
    # 构建完整的反馈数据结构
    feedback_data = {
        'user_id': test_session['permanent_user_id'],
        'session_id': test_session['user_session_id'],
        'translation_id': test_translation_id,
        'daily_count': test_session['translation_count'],
        'session_count': 1,
        'user_name': test_user_name,
        'user_feedback': test_feedback,
        'language': test_session['language'],
        'device_info': device_info,
        'ip_hash': ip_hash,
        'user_agent': user_agent,
        'extra_data': {
            'feedback_type': 'simple_text',
            'app_version': '4.2.0',
            'submission_source': 'main_app',
            'feedback_length': len(test_feedback),
            'has_user_name': bool(test_user_name.strip())
        }
    }
    
    print(f"\n完整反馈数据结构:")
    for key, value in feedback_data.items():
        if key == 'extra_data':
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ 反馈组件测试完成")
    return True

if __name__ == "__main__":
    test_feedback_component()稱呼（選填）"
        name_example = "例：醫學生小王"
        feedback_label = "請分享您的使用體驗或改進建議"
        feedback_placeholder = "例：希望增加醫學術語發音功能，或翻譯速度可以更快一些..."
        submit_button = "💌 送出建議"
        success_message = "✅ 感謝您的寶貴建議！我們會持續優化 RadiAI.Care！"
    else:  # 简体中文
        title = "💭 帮助我们改进学习体验"
        description = "您的建议将帮助我们优化这个医学翻译教育工具"
        name_placeholder = "您的
