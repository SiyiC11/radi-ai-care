"""
RadiAI.Care - 簡單反饋組件
創建新的FB工作表專門記錄用戶反饋
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def render_simple_feedback_form(translation_id: str, sheets_manager, lang_cfg: Dict[str, str]) -> bool:
    """
    渲染簡單的用戶反饋表單，記錄到新的FB工作表
    
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
                    success = _save_feedback_to_new_sheet(
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


def _save_feedback_to_new_sheet(translation_id: str, user_name: str, user_feedback: str, sheets_manager) -> bool:
    """
    保存反馈到新的FB工作表
    
    Args:
        translation_id: 翻译ID
        user_name: 用户姓名
        user_feedback: 用户反馈内容
        sheets_manager: Google Sheets 管理器实例
        
    Returns:
        bool: 是否成功保存
    """
    try:
        logger.info("开始保存反馈到FB工作表")
        
        # 获取或创建FB工作表
        fb_worksheet = _get_or_create_fb_worksheet(sheets_manager)
        if not fb_worksheet:
            logger.error("无法获取或创建FB工作表")
            return False
        
        # 准备反馈数据
        current_time = datetime.now()
        feedback_row = [
            current_time.strftime('%Y-%m-%d'),  # A列: 日期
            current_time.strftime('%H:%M:%S'),  # B列: 时间
            translation_id,                     # C列: 翻译ID
            user_name if user_name else "匿名用户",  # D列: 用户姓名
            user_feedback,                      # E列: 反馈内容
            st.session_state.get('language', 'zh_CN'),  # F列: 语言
            st.session_state.get('permanent_user_id', ''),  # G列: 用户ID
            current_time.isoformat()            # H列: 完整时间戳
        ]
        
        # 添加反馈到工作表
        fb_worksheet.append_row(feedback_row)
        
        logger.info(f"成功保存反馈到FB工作表: {translation_id}")
        return True
        
    except Exception as e:
        logger.error(f"保存反馈到FB工作表时发生错误: {e}")
        return False


def _get_or_create_fb_worksheet(sheets_manager):
    """
    获取或创建FB工作表
    
    Args:
        sheets_manager: Google Sheets 管理器实例
        
    Returns:
        工作表对象或None
    """
    try:
        # 方法1: 如果sheets_manager有spreadsheet属性
        if hasattr(sheets_manager, 'spreadsheet'):
            spreadsheet = sheets_manager.spreadsheet
            
            # 检查是否已经存在FB工作表
            try:
                fb_worksheet = spreadsheet.worksheet('FB')
                logger.info("找到现有的FB工作表")
                return fb_worksheet
            except:
                # FB工作表不存在，创建新的
                logger.info("FB工作表不存在，正在创建...")
                fb_worksheet = spreadsheet.add_worksheet(title='FB', rows=1000, cols=10)
                
                # 设置表头
                headers = [
                    '日期',         # A列
                    '时间',         # B列  
                    '翻译ID',       # C列
                    '用户姓名',     # D列
                    '反馈内容',     # E列
                    '语言',         # F列
                    '用户ID',       # G列
                    '时间戳'        # H列
                ]
                fb_worksheet.append_row(headers)
                
                logger.info("成功创建FB工作表并设置表头")
                return fb_worksheet
        
        # 方法2: 如果sheets_manager有service和spreadsheet_id属性
        elif hasattr(sheets_manager, 'service') and hasattr(sheets_manager, 'spreadsheet_id'):
            service = sheets_manager.service
            spreadsheet_id = sheets_manager.spreadsheet_id
            
            # 获取所有工作表
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if 'FB' in sheet_names:
                # FB工作表已存在
                logger.info("找到现有的FB工作表")
                # 返回工作表引用（需要用gspread重新获取）
                import gspread
                gc = gspread.service_account()
                spreadsheet = gc.open_by_key(spreadsheet_id)
                return spreadsheet.worksheet('FB')
            else:
                # 创建新的FB工作表
                logger.info("正在创建FB工作表...")
                batch_update_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': 'FB',
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': 10
                                }
                            }
                        }
                    }]
                }
                
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=batch_update_body
                ).execute()
                
                # 添加表头
                headers = [['日期', '时间', '翻译ID', '用户姓名', '反馈内容', '语言', '用户ID', '时间戳']]
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='FB!A1:H1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                
                logger.info("成功创建FB工作表")
                
                # 返回工作表引用
                import gspread
                gc = gspread.service_account()
                spreadsheet = gc.open_by_key(spreadsheet_id)
                return spreadsheet.worksheet('FB')
        
        # 方法3: 尝试通过其他属性访问
        else:
            logger.error("无法识别sheets_manager的类型")
            return None
            
    except Exception as e:
        logger.error(f"获取或创建FB工作表时发生错误: {e}")
        return None


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
