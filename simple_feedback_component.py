"""
RadiAI.Care - 簡單反饋組件
直接更新Google Sheet最新記錄的反饋字段
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def render_simple_feedback_form(translation_id: str, sheets_manager, lang_cfg: Dict[str, str]) -> bool:
    """
    渲染簡單的用戶反饋表單，直接更新最新記錄
    
    Args:
        translation_id: 翻譯ID
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
        name_placeholder = "您的稱呼（選填）"
        name_example = "例：醫學生小王"
        feedback_label = "請分享您的使用體驗或改進建議"
        feedback_placeholder = "例：希望增加醫學術語發音功能，或翻譯速度可以更快一些..."
        submit_button = "💌 送出建議"
        success_message = "✅ 感謝您的寶貴建議！我們會持續優化 RadiAI.Care！"
    else:  # 简体中文
        title = "💭 帮助我们改进学习体验"
        description = "您的建议将帮助我们优化这个医学翻译教育工具"
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
                    success = _update_latest_record_with_feedback(
                        user_name=user_name.strip(),
                        user_feedback=user_feedback.strip(),
                        sheets_manager=sheets_manager
                    )
                    
                    if success:
                        st.success(success_message)
                        st.balloons()
                        # 标记已提交反馈
                        st.session_state[feedback_key] = True
                        # 更新反馈统计
                        if 'feedback_count' not in st.session_state:
                            st.session_state.feedback_count = 0
                        st.session_state.feedback_count += 1
                        # 刷新页面显示感谢信息
                        st.rerun()
                        return True
                    else:
                        st.error("❌ 反馈提交失败，请稍后重试")
                        return False
                else:
                    st.warning("⚠️ 请填写您的建议后再提交")
                    return False
    
    return False


def _update_latest_record_with_feedback(user_name: str, user_feedback: str, sheets_manager) -> bool:
    """
    直接更新Google Sheet最新记录的反馈字段
    
    Args:
        user_name: 用户姓名
        user_feedback: 用户反馈内容
        sheets_manager: Google Sheets 管理器实例
        
    Returns:
        bool: 是否成功更新
    """
    try:
        logger.info("开始更新最新记录的反馈信息")
        
        # 方法1: 如果sheets_manager有update_latest_record方法
        if hasattr(sheets_manager, 'update_latest_record'):
            feedback_data = {
                'user_name': user_name,
                'user_feedback': user_feedback
            }
            success = sheets_manager.update_latest_record(feedback_data)
            if success:
                logger.info("使用update_latest_record方法成功更新反馈")
                return True
        
        # 方法2: 如果sheets_manager有worksheet属性，直接操作
        if hasattr(sheets_manager, 'worksheet') or hasattr(sheets_manager, 'usage_sheet'):
            try:
                # 获取工作表
                worksheet = getattr(sheets_manager, 'worksheet', None) or getattr(sheets_manager, 'usage_sheet', None)
                if worksheet:
                    # 获取所有记录，找到最新的一行
                    all_records = worksheet.get_all_records()
                    if all_records:
                        # 最新记录是最后一行
                        last_row_index = len(all_records) + 1  # +1因为有表头
                        
                        # T列 = User Name, U列 = User Feedback
                        worksheet.update(f'T{last_row_index}', user_name)  # 用户姓名列 (T列)
                        worksheet.update(f'U{last_row_index}', user_feedback)  # 反馈内容列 (U列)
                        
                        logger.info(f"直接更新第{last_row_index}行的反馈信息成功")
                        return True
            except Exception as e:
                logger.error(f"直接操作工作表失败: {e}")
        
        # 方法3: 使用通用的update方法
        if hasattr(sheets_manager, 'update_feedback'):
            success = sheets_manager.update_feedback(user_name, user_feedback)
            if success:
                logger.info("使用update_feedback方法成功更新反馈")
                return True
        
        # 方法4: 如果有service属性，直接使用Google Sheets API
        if hasattr(sheets_manager, 'service') and hasattr(sheets_manager, 'spreadsheet_id'):
            try:
                # 获取表格数据以确定最后一行
                range_name = 'UsageLog!A:A'  # 假设工作表名为UsageLog
                result = sheets_manager.service.spreadsheets().values().get(
                    spreadsheetId=sheets_manager.spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                last_row = len(values)  # 最后一行号
                
                # 更新反馈字段（T列是用户名，U列是反馈）
                feedback_range = f'UsageLog!T{last_row}:U{last_row}'
                feedback_values = [[user_name, user_feedback]]
                
                sheets_manager.service.spreadsheets().values().update(
                    spreadsheetId=sheets_manager.spreadsheet_id,
                    range=feedback_range,
                    valueInputOption='RAW',
                    body={'values': feedback_values}
                ).execute()
                
                logger.info(f"使用API直接更新第{last_row}行反馈成功")
                return True
                
            except Exception as e:
                logger.error(f"使用API更新反馈失败: {e}")
        
        logger.error("所有更新方法都失败了")
        return False
        
    except Exception as e:
        logger.error(f"更新反馈时发生错误: {e}")
        return False


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
