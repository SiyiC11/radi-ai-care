if uploaded_file:
                # 检查是否是新文件或内容已处理
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if ('last_processed_file' not in st.session_state or 
                    st.session_state.last_processed_file != file_id or
                    not st.session_state.enhanced_ui_file_content):
                    
                    # 处理新文件
                    with st.spinner("正在处理文件..."):
                        try:
                            if self.file_handler:
                                extracted_text, result = self.file_handler.extract_text(uploaded_file)
                            else:
                                # 如果没有file_handler，尝试简单的文本提取
                                try:
                                    import PyMuPDF as fitz
                                    if uploaded_file.type == "application/pdf":
                                        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                                        text_parts = []
                                        for page_num in range(pdf_document.page_count):
                                            page = pdf_document[page_num]
                                            page_text = page.get_text()
                                            if page_text.strip():
                                                text_parts.append(page_text)
                                        pdf_document.close()
                                        extracted_text = "\n\n".join(text_parts)
                                        result = {"file_info": {"type": "application/pdf"}}
                                    else:
                                        # 对于非PDF文件，尝试直接读取
                                        uploaded_file.seek(0)
                                        content = uploaded_file.read()
                                        try:
                                            extracted_text = content.decode('utf-8')
                                            result = {"file_info": {"type": "text/plain"}}
                                        except:
                                            extracted_text = ""
                                            result = {"error": "无法解析文件"}
                                except ImportError:
                                    # 如果PyMuPDF不可用，返回错误
                                    extracted_text = ""
                                    result = {"error": "文件处理器不可用"}
                            
                            if extracted_text and extracted_text.strip():
                                # 成功提取文本
                                st.session_state.enhanced_ui_file_content = extracted_text
                                st.session_state.enhanced_ui_file_type = result.get("file_info", {}).get("type", "unknown")
                                st.session_state.last_processed_file = file_id
                                
                                # 存储到多个 session state 键，确保主应用能找到
                                st.session_state['uploaded_file_content'] = extracted_text
                                st.session_state['uploaded_file_content_type'] = st.session_state.enhanced_ui_file_type
                                st.session_state['file_content'] = extracted_text
                                st.session_state['extracted_text'] = extracted_text
                                st.session_state['report_text'] = extracted_text
                                st.session_state['text_input_area'] = extracted_text
                                
                                logger.info(f"Enhanced UI: Successfully extracted {len(extracted_text)} characters from file")
                                
                            else:
                                # 文件处理失败
                                error_msg = result.get('error', '无法提取文件内容')
                                st.error(f"❌ {error_msg}")
                                st.session_state.enhanced_ui_file_content = ""
                                st.session_state.enhanced_ui_file_type = ""
                                logger.error(f"Enhanced UI: File extraction failed - {error_msg}")
                                
                        except Exception as e:
                            st.error(f"❌ 文件处理错误: {str(e)}")
                            st.session_state.enhanced_ui_file_content = ""
                            st.session_state.enhanced_ui_file_type = ""
                            logger.error(f"Enhanced UI: File processing exception - {str(e)}")
                
                # 显示处理结果
                if st.session_state.enhanced_ui_file_content:
                    st.success("✅ 文件上传成功")
                    
                    with st.expander("📄 文件内容预览", expanded=False):
                        preview_text = st.session_state.enhanced_ui_file_content[:1000]
                        if len(st.session_state.enhanced_ui_file_content) > 1000:
                            preview_text += "..."
                        st.text_area("提取的内容：", value=preview_text, height=150, disabled=True)
                    
                    # 返回文件内容
                    st.markdown('</div>', unsafe_allow_html=True)
                    return st.session_state.enhanced_ui_file_content, st.session_state.enhanced_ui_file_type
                else:
                    # 文件处理失败，返回空内容
                    st.markdown('</div>', unsafe_allow_html=True)
                    return "", "error""""
RadiAI.Care - 修复版增强UI组件
确保文件上传后将内容存储到 session state
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedUIComponents:
    """增强版UI组件系统 - 修复版"""
    
    def __init__(self, config, file_handler):
        self.config = config
        self.file_handler = file_handler
    
    def render_header(self, lang: Dict):
        """渲染标题"""
        try:
            logo_data, mime_type = self.config.get_logo_base64()
            data_uri = f"data:{mime_type};base64,{logo_data}"
            
            st.markdown(f'''
            <div class="title-section">
                <div class="logo-container">
                    <img src="{data_uri}" width="60" height="60" alt="RadiAI.Care Logo" 
                         style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                </div>
                <div class="main-title">{lang["app_title"]}</div>
                <div class="subtitle">{lang["app_subtitle"]}</div>
                <div class="description">{lang["app_description"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception:
            st.markdown(f'''
            <div class="title-section">
                <div class="logo-container">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏥</div>
                </div>
                <div class="main-title">{lang["app_title"]}</div>
                <div class="subtitle">{lang["app_subtitle"]}</div>
                <div class="description">{lang["app_description"]}</div>
            </div>
            ''', unsafe_allow_html=True)

    def render_language_selection(self, lang: Dict):
        """渲染语言选择"""
        st.markdown(f'<div style="text-align:center; margin:1.5rem 0;"><h4>{lang["lang_selection"]}</h4></div>', 
                   unsafe_allow_html=True)
        
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

    def render_disclaimer(self, lang: Dict):
        """渲染免责声明"""
        st.markdown(f"""
        <div style="
            background-color: #fff3cd;
            border-left: 6px solid #ff9800;
            padding: 1.2rem;
            border-radius: 8px;
            margin-top: 1.5rem;
            box-shadow: 0 2px 8px rgba(255,152,0,0.1);
        ">
            <div style="font-weight: bold; font-size: 1.1rem; color: #bf360c;">
                ⚠️ {lang['disclaimer_title']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(lang["disclaimer_items"], 1):
            st.markdown(f"""
            <div style="
                margin: 0.8rem 0;
                padding: 1rem 1.2rem;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 12px;
                border-left: 5px solid #ff9800;
                box-shadow: 0 2px 8px rgba(255, 152, 0, 0.1);
                font-size: 0.95rem;
                line-height: 1.6;
                color: #d84315;
                font-weight: 500;
            ">
                <strong style="color: #bf360c;">📌 {i}.</strong> {item}
            </div>
            """, unsafe_allow_html=True)

    def render_input_section(self, lang: Dict) -> Tuple[str, str]:
        """渲染输入部分 - 修复版，确保返回内容"""
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # 初始化 session state 中的输入相关键
        if 'enhanced_ui_input_method' not in st.session_state:
            st.session_state.enhanced_ui_input_method = 'text'
        if 'enhanced_ui_text_content' not in st.session_state:
            st.session_state.enhanced_ui_text_content = ""
        if 'enhanced_ui_file_content' not in st.session_state:
            st.session_state.enhanced_ui_file_content = ""
        if 'enhanced_ui_file_type' not in st.session_state:
            st.session_state.enhanced_ui_file_type = ""
        
        st.markdown("### 📝 选择输入方式")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 文字输入", key="enhanced_input_text_btn", use_container_width=True,
                        type="primary" if st.session_state.enhanced_ui_input_method == 'text' else "secondary"):
                st.session_state.enhanced_ui_input_method = 'text'
                # 清空文件内容
                st.session_state.enhanced_ui_file_content = ""
                st.session_state.enhanced_ui_file_type = ""
                st.rerun()
        
        with col2:
            if st.button("📁 上传文件", key="enhanced_input_file_btn", use_container_width=True,
                        type="primary" if st.session_state.enhanced_ui_input_method == 'file' else "secondary"):
                st.session_state.enhanced_ui_input_method = 'file'
                # 清空文本内容
                st.session_state.enhanced_ui_text_content = ""
                st.rerun()
        
        st.markdown("---")
        
        if st.session_state.enhanced_ui_input_method == 'text':
            st.markdown("#### 📝 请输入英文放射科报告")
            text_input = st.text_area(
                lang.get('input_label', '请输入英文放射科报告：'),
                height=200,
                placeholder=lang['input_placeholder'],
                key="enhanced_text_input_area",
                value=st.session_state.enhanced_ui_text_content
            )
            
            # 实时更新 session state
            if text_input != st.session_state.enhanced_ui_text_content:
                st.session_state.enhanced_ui_text_content = text_input
                # 同时存储到我们检查的键中
                st.session_state['text_input_area'] = text_input
                st.session_state['report_text'] = text_input
            
            # 返回文本内容
            st.markdown('</div>', unsafe_allow_html=True)
            return text_input, "manual"
        
        elif st.session_state.enhanced_ui_input_method == 'file':
            st.markdown("#### 📁 上传报告文件")
            uploaded_file = st.file_uploader(
                lang['file_upload'],
                type=list(self.config.SUPPORTED_FILE_TYPES),
                help=lang['supported_formats'],
                key="enhanced_file_uploader"
            )
            
            if uploaded_file:
                # 检查是否是新文件或内容已处理
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                
                if ('last_processed_file' not in st.session_state or 
                    st.session_state.last_processed_file != file_id or
                    not st.session_state.enhanced_ui_file_content):
                    
                    # 处理新文件
                    with st.spinner("正在处理文件..."):
                        try:
                            extracted_text, result = self.file_handler.extract_text(uploaded_file)
                            
                            if extracted_text and extracted_text.strip():
                                # 成功提取文本
                                st.session_state.enhanced_ui_file_content = extracted_text
                                st.session_state.enhanced_ui_file_type = result.get("file_info", {}).get("type", "unknown")
                                st.session_state.last_processed_file = file_id
                                
                                # 存储到多个 session state 键，确保主应用能找到
                                st.session_state['uploaded_file_content'] = extracted_text
                                st.session_state['uploaded_file_content_type'] = st.session_state.enhanced_ui_file_type
                                st.session_state['file_content'] = extracted_text
                                st.session_state['extracted_text'] = extracted_text
                                st.session_state['report_text'] = extracted_text
                                st.session_state['text_input_area'] = extracted_text
                                
                                logger.info(f"Enhanced UI: Successfully extracted {len(extracted_text)} characters from file")
                                
                            else:
                                # 文件处理失败
                                error_msg = result.get('error', '无法提取文件内容')
                                st.error(f"❌ {error_msg}")
                                st.session_state.enhanced_ui_file_content = ""
                                st.session_state.enhanced_ui_file_type = ""
                                logger.error(f"Enhanced UI: File extraction failed - {error_msg}")
                                
                        except Exception as e:
                            st.error(f"❌ 文件处理错误: {str(e)}")
                            st.session_state.enhanced_ui_file_content = ""
                            st.session_state.enhanced_ui_file_type = ""
                            logger.error(f"Enhanced UI: File processing exception - {str(e)}")
                
                # 显示处理结果
                if st.session_state.enhanced_ui_file_content:
                    st.success("✅ 文件上传成功")
                    
                    with st.expander("📄 文件内容预览", expanded=False):
                        preview_text = st.session_state.enhanced_ui_file_content[:1000]
                        if len(st.session_state.enhanced_ui_file_content) > 1000:
                            preview_text += "..."
                        st.text_area("提取的内容：", value=preview_text, height=150, disabled=True)
                    
                    # 返回文件内容
                    st.markdown('</div>', unsafe_allow_html=True)
                    return st.session_state.enhanced_ui_file_content, st.session_state.enhanced_ui_file_type
                else:
                    # 文件处理失败，返回空内容
                    st.markdown('</div>', unsafe_allow_html=True)
                    return "", "error"
            
            else:
                # 没有文件上传
                if st.session_state.enhanced_ui_file_content:
                    # 之前有文件内容，现在文件被移除了
                    st.info("📄 之前上传的文件内容仍然可用")
                    with st.expander("📄 文件内容预览", expanded=False):
                        preview_text = st.session_state.enhanced_ui_file_content[:1000]
                        if len(st.session_state.enhanced_ui_file_content) > 1000:
                            preview_text += "..."
                        st.text_area("提取的内容：", value=preview_text, height=150, disabled=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    return st.session_state.enhanced_ui_file_content, st.session_state.enhanced_ui_file_type
                else:
                    st.markdown('</div>', unsafe_allow_html=True)
                    return "", "none"
        
        # 默认返回
        st.markdown('</div>', unsafe_allow_html=True)
        return "", "none"

    def get_current_input(self) -> Tuple[str, str]:
        """获取当前输入内容的方法"""
        if st.session_state.enhanced_ui_input_method == 'text':
            return st.session_state.enhanced_ui_text_content, "manual"
        elif st.session_state.enhanced_ui_input_method == 'file':
            return st.session_state.enhanced_ui_file_content, st.session_state.enhanced_ui_file_type
        return "", "none"

    def render_translate_button(self, lang: Dict, report_text: str) -> bool:
        """渲染翻译按钮"""
        if not report_text or not report_text.strip():
            st.warning(f"⚠️ {lang['error_empty_input']}")
            return False
        
        return st.button(
            lang['translate_button'],
            type="primary",
            use_container_width=True,
            disabled=len(report_text.strip()) < 10
        )

    def render_translation_result(self, result_content: str, lang: Dict):
        """渲染翻译结果"""
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.success(lang.get('translation_complete', '🎉 翻译完成！'))
        st.markdown(result_content)
        st.markdown('</div>', unsafe_allow_html=True)

    def render_footer(self, lang: Dict):
        """渲染页脚"""
        st.markdown("---")
        
        privacy_text = lang.get('privacy_summary', '我们仅收集必要信息，符合澳洲隐私法规定。')
        terms_text = lang.get('terms_summary', '本服务仅提供翻译，不构成医疗建议。')
        
        st.markdown(f"""
        <div style="
            font-size: 0.75rem;
            color: #666;
            text-align: center;
            padding: 1rem 0;
            background: rgba(0,0,0,0.02);
            border-radius: 8px;
        ">
            <div><strong>🔒 隐私政策：</strong>{privacy_text}</div>
            <div><strong>⚖️ 使用条款：</strong>{terms_text}</div>
        </div>
        """, unsafe_allow_html=True)

    def render_version_info(self):
        """渲染版本信息"""
        st.markdown(
            f"<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;'>"
            f"RadiAI.Care {self.config.APP_VERSION}</div>", 
            unsafe_allow_html=True
        )
