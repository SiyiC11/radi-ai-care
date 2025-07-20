"""
RadiAI.Care UI 組件
統一管理所有 UI 元素的渲染（支援圖片 Logo）
"""

import streamlit as st
from typing import Dict, Tuple
from config.settings import AppConfig, UIText
from utils.file_handler import FileHandler

class UIComponents:
    """UI 組件管理器"""
    
    def __init__(self):
        self.config = AppConfig()
        self.file_handler = FileHandler()
    
    def render_header(self, lang: Dict):
        """渲染標題和 Logo（支援圖片文件）"""
        try:
            # 獲取 logo 數據和 MIME 類型
            logo_data, mime_type = self.config.get_logo_base64()
            
            # 創建完整的 data URI
            data_uri = f"data:{mime_type};base64,{logo_data}"
            
            st.markdown(f'''
            <div class="title-section">
                <div class="logo-container">
                    <img src="{data_uri}" width="60" height="60" alt="RadiAI.Care Logo" style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                </div>
                <div class="main-title">{lang["app_title"]}</div>
                <div class="subtitle">{lang["app_subtitle"]}</div>
                <div class="description">{lang["app_description"]}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            # 如果 logo 加載失敗，使用純文字版本
            st.markdown(f'''
            <div class="title-section">
                <div class="logo-container">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏥</div>
                </div>
                <div class="main-title">{lang["app_title"]}</div>
                <div class="subtitle">{lang["app_subtitle"]}</div>
                <div class="description">{lang["app_description"]}</div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 0.5rem;">
                    ⚠️ Logo 載入失敗，使用默認圖標
                </div>
            </div>
            ''', unsafe_allow_html=True)
            print(f"Logo 渲染錯誤: {e}")
    
    def render_language_selection(self, lang: Dict):
        """渲染語言選擇按鈕"""
        st.markdown(f'<div style="text-align:center; margin:1.5rem 0;"><h4>{lang["lang_selection"]}</h4></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("繁體中文", 
                        key="lang_traditional", 
                        use_container_width=True,
                        type="primary" if st.session_state.language == "繁體中文" else "secondary"):
                st.session_state.language = "繁體中文"
                st.rerun()
        with col2:
            if st.button("简体中文", 
                        key="lang_simplified", 
                        use_container_width=True,
                        type="primary" if st.session_state.language == "简体中文" else "secondary"):
                st.session_state.language = "简体中文"
                st.rerun()
    
    def render_disclaimer(self, lang: Dict):
        """渲染法律聲明（永遠顯示，無折疊）"""

        # 標題 + 警示
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

        # 法律聲明條款逐條顯示
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

        # 底部提醒與緊急資訊
        st.markdown("""
        <div style="
            text-align: center;
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(255, 193, 7, 0.1);
            border-radius: 8px;
            font-style: italic;
            color: #f57c00;
            font-weight: 600;
            border: 1px dashed #ff9800;
        ">
            🔒 您的健康和安全是我們最關心的事項，請務必遵循以上指導原則。
        </div>

        <div style="margin-top: 1rem;">
            <hr>
            <strong>🆘 緊急情況處理：</strong><br>
            🚨 <strong>緊急醫療</strong>：立即撥打 <strong>000</strong><br>
            🏥 <strong>就醫建議</strong>：前往最近的急診室<br>
            👨‍⚕️ <strong>專業諮詢</strong>：聯繫您的家庭醫師 (GP)
        </div>
        """, unsafe_allow_html=True)
    
    def render_disclaimer_alternative(self, lang: Dict):
        """渲染法律聲明（備用 HTML 版本）"""
        
        # 如果需要更美觀的顯示，可以使用這個版本
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #fff8e1 0%, #ffefd5 100%);
            border: 2px solid #ff9800;
            border-radius: 16px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
        ">
            <div style="
                text-align: center;
                font-weight: bold;
                color: #bf360c;
                font-size: 1.2rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
            ">
                ⚠️ {lang["disclaimer_title"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 使用 Streamlit 原生組件渲染聲明項目
        for i, item in enumerate(lang["disclaimer_items"], 1):
            st.markdown(f"""
            <div style="
                margin: 0.8rem 0;
                padding: 1rem 1.2rem;
                background: rgba(255, 255, 255, 0.9);
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
        
        # 添加底部提醒
        st.markdown(f"""
        <div style="
            text-align: center;
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(255, 193, 7, 0.1);
            border-radius: 8px;
            font-style: italic;
            color: #f57c00;
            font-weight: 600;
            border: 1px dashed #ff9800;
        ">
            🔒 您的健康和安全是我們最關心的事項 🔒
        </div>
        """, unsafe_allow_html=True)
    
    def render_usage_tracker(self, lang: Dict) -> int:
        """渲染使用次數追蹤"""
        remaining = self.config.MAX_FREE_TRANSLATIONS - st.session_state.translation_count
        progress = st.session_state.translation_count / self.config.MAX_FREE_TRANSLATIONS
        
        st.markdown("### 📊 使用情況")
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.progress(progress)
            if remaining > 0:
                st.caption(f"還可使用 {remaining} 次免費翻譯")
            else:
                st.caption("免費額度已用完")
        
        with col2:
            if remaining > 0:
                st.metric("剩餘", remaining)
            else:
                st.metric("剩餘", 0, delta="已用完")
        
        with col3:
            st.metric("總計", f"{st.session_state.translation_count}/{self.config.MAX_FREE_TRANSLATIONS}")
        
        return remaining
    
    def render_quota_exceeded(self, lang: Dict):
        """渲染額度超額提示"""
        st.error(f"🚫 {lang['quota_finished']}")
        st.info("💡 如需更多翻譯服務，請聯繫我們了解付費方案。")
        
        with st.expander("📞 聯繫我們", expanded=True):
            st.markdown("""
            #### 💼 商業合作與付費服務：
            
            📧 **Email**: support@radiai.care  
            🌐 **官網**: www.radiai.care  
            📱 **服務時間**: 週一至週五 9:00-17:00 (AEST)
            
            #### 🚀 付費版本功能：
            - ✅ 無限次數翻譯服務
            - ✅ 批量文件處理功能  
            - ✅ 專業醫療術語定制
            - ✅ 優先技術支援服務
            - ✅ API 接入服務
            """)
    
    def render_input_section(self, lang: Dict) -> Tuple[str, str]:
        """渲染輸入區塊"""
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.markdown(f'### {lang["input_method"]}')
        
        # 輸入方式選擇
        col1, col2 = st.columns(2)
        with col1:
            if st.button(lang["input_text"], 
                        key="input_text_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.input_method == "text" else "secondary"):
                st.session_state.input_method = "text"
        with col2:
            if st.button(lang["input_file"], 
                        key="input_file_btn", 
                        use_container_width=True,
                        type="primary" if st.session_state.input_method == "file" else "secondary"):
                st.session_state.input_method = "file"
        
        report_text = ""
        file_type = "manual"
        
        if st.session_state.input_method == "text":
            report_text, file_type = self._render_text_input(lang)
        else:
            report_text, file_type = self._render_file_input(lang)
        
        st.markdown('</div>', unsafe_allow_html=True)
        return report_text, file_type
    
    def _render_text_input(self, lang: Dict) -> Tuple[str, str]:
        """渲染文本輸入區域"""
        st.markdown("#### 📝 輸入報告內容")
        report_text = st.text_area(
            lang["input_placeholder"],
            height=250,
            placeholder="例如：CHEST CT SCAN\nCLINICAL HISTORY: ...\nFINDINGS: ...\nIMPRESSION: ...",
            label_visibility="collapsed",
            max_chars=self.config.MAX_TEXT_LENGTH
        )
        
        # 實時內容分析
        if report_text:
            from utils.translator import Translator
            translator = Translator()
            validation = translator.validate_content(report_text)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"字符數: {len(report_text)}")
            with col2:
                st.caption(f"醫學術語: {len(validation['found_terms'])}")
            with col3:
                confidence = validation['confidence']
                confidence_color = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
                st.caption(f"信心度: {confidence_color} {confidence:.1%}")
        
        return report_text, "manual"
    
    def _render_file_input(self, lang: Dict) -> Tuple[str, str]:
        """渲染文件輸入區域"""
        st.markdown("#### 📂 上傳報告文件")
        
        uploaded_file = st.file_uploader(
            lang["file_upload"],
            type=self.config.SUPPORTED_FILE_TYPES,
            help=f"支援 {', '.join([t.upper() for t in self.config.SUPPORTED_FILE_TYPES])} 格式，限制 {self.config.FILE_SIZE_LIMIT_MB}MB",
            label_visibility="collapsed"
        )
        
        # 文件格式說明
        self._render_file_format_info()
        
        if uploaded_file is not None:
            return self._process_uploaded_file(uploaded_file, lang)
        
        return "", "manual"
    
    def _render_file_format_info(self):
        """渲染文件格式說明"""
        with st.expander("📋 支援格式說明", expanded=False):
            formats_info = self.file_handler.get_supported_formats_info()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**{formats_info['pdf']}**")
            with col2:
                st.markdown(f"**{formats_info['txt']}**")
            with col3:
                st.markdown(f"**{formats_info['docx']}**")
    
    def _process_uploaded_file(self, uploaded_file, lang: Dict) -> Tuple[str, str]:
        """處理上傳的文件"""
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        with st.spinner("🔄 處理文件中..."):
            extracted_text, processing_info = self.file_handler.extract_text(uploaded_file)
            
            if extracted_text:
                st.success(f"✅ {lang['file_success']}")
                
                # 文件資訊顯示
                file_info = processing_info.get('file_info', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"📁 {file_info.get('name', 'unknown')}")
                with col2:
                    st.caption(f"📏 {file_info.get('size_kb', 0)} KB")
                with col3:
                    st.caption(f"📝 {len(extracted_text)} 字符")
                
                # 內容預覽
                with st.expander("👀 預覽內容", expanded=False):
                    preview = (extracted_text[:self.config.PREVIEW_LENGTH] + "...") if len(extracted_text) > self.config.PREVIEW_LENGTH else extracted_text
                    st.text_area("", value=preview, height=120, disabled=True)
                    
                    # 內容驗證結果
                    from utils.translator import Translator
                    translator = Translator()
                    validation = translator.validate_content(extracted_text)
                    
                    if validation['found_terms']:
                        st.success(f"✅ 檢測到 {len(validation['found_terms'])} 個醫學術語")
                    else:
                        st.warning("⚠️ 未檢測到明顯的醫學術語")
                
                return extracted_text, file_extension
            else:
                error_msg = processing_info.get('error', '未知錯誤')
                st.error(f"❌ {lang['file_error']}")
                st.error(f"詳細錯誤：{error_msg}")
                return "", "failed"
    
    def render_translate_button(self, lang: Dict, report_text: str) -> bool:
        """渲染翻譯按鈕"""
        button_disabled = not report_text.strip() or len(report_text.strip()) < self.config.MIN_TEXT_LENGTH
        button_help = f"請輸入至少 {self.config.MIN_TEXT_LENGTH} 個字符的有效報告內容" if button_disabled else "點擊開始智能解讀"
        
        return st.button(
            f"{lang['translate_button']}", 
            type="primary", 
            use_container_width=True,
            disabled=button_disabled,
            help=button_help
        )
    
    def render_translation_result(self, content: str, lang: Dict):
        """渲染翻譯結果"""
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown(f"### {lang['result_title']}")
        st.markdown(content)
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_completion_status(self, lang: Dict, remaining: int):
        """渲染完成狀態"""
        if remaining > 0:
            st.success(f"{lang['translation_complete']} {remaining} {lang['translation_remaining']}")
        else:
            st.balloons()
            st.success("🌟 您已用完所有免費翻譯！感謝使用 RadiAI.Care")
    
    def render_footer(self, lang: Dict):
        """渲染底部資訊"""
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["💡 使用指南", "🔒 隱私保護", "⚠️ 重要提醒"])
        
        with tab1:
            self._render_usage_guide()
        
        with tab2:
            self._render_privacy_info()
        
        with tab3:
            self._render_medical_reminders()
    
    def _render_usage_guide(self):
        """渲染使用指南"""
        st.markdown("""
        ### 📋 使用指南
        
        **🎯 獲得最佳翻譯效果：**
        
        ✅ **完整報告**：確保包含所有必要段落（Findings、Impression 等）  
        ✅ **清晰內容**：文件清晰，文字可讀  
        ✅ **醫學術語**：包含放射科相關專業術語  
        ✅ **結構完整**：包含檢查方法、發現、結論等完整結構  
        
        **📝 支援格式：**
        - **PDF**：掃描版或電子版醫學報告
        - **TXT**：純文字格式報告  
        - **DOCX**：Word 文檔格式報告
        
        **🔍 內容驗證：**
        - 系統會自動檢測醫學術語
        - 評估內容的醫學相關性
        - 提供信心度參考指標
        """)
    
    def _render_privacy_info(self):
        """渲染隱私信息"""
        st.markdown("""
        ### 🛡️ 隱私保護承諾
        
        **🔒 數據安全：**
        
        ✅ **即時處理**：報告內容處理完成後立即清除  
        ✅ **不存儲內容**：不保存任何醫學報告原文  
        ✅ **匿名統計**：僅記錄匿名使用統計數據  
        ✅ **加密傳輸**：所有數據傳輸使用 HTTPS 加密  
        
        **⚠️ 隱私建議：**
        
        🚫 **移除敏感資訊**：建議去除姓名、身份證號等個人資訊  
        🚫 **避免地址**：不要包含住址、電話等聯繫方式  
        ✅ **專注醫學內容**：保留醫學檢查相關內容即可  
        
        **📋 合規標準：**
        - 符合澳洲隱私法 (Privacy Act 1988)
        - 遵循國際數據保護標準
        - 醫療數據處理最佳實踐
        """)
    
    def _render_medical_reminders(self):
        """渲染醫療提醒"""
        st.markdown("""
        ### ⚠️ 醫療安全重要提醒
        
        **✅ 我們提供的服務：**
        
        🔹 **語言翻譯**：英文醫學報告的準確中文翻譯  
        🔹 **術語解釋**：醫學專業術語的通俗化解釋  
        🔹 **結構整理**：報告內容的邏輯性整理  
        🔹 **諮詢建議**：向醫師諮詢的參考問題清單  
        
        **🚫 我們不提供的服務：**
        
        ❌ **醫療診斷**：任何形式的疾病診斷或診斷建議  
        ❌ **治療建議**：藥物處方或治療方案建議  
        ❌ **醫療決策**：影響醫療選擇的決策性建議  
        ❌ **緊急醫療**：急救指導或緊急醫療服務  
        
        **🆘 緊急情況處理：**
        
        📞 **緊急醫療**：立即撥打 **000**  
        🏥 **急診就醫**：前往最近的急診室  
        👨‍⚕️ **專業諮詢**：聯繫您的主治醫師或專科醫師  
        
        **⚖️ 法律責任聲明：**
        
        所有醫療決策的最終責任歸屬於患者本人和其醫療團隊。本工具僅作為語言翻譯輔助，不承擔任何醫療責任。
        """)
    
    def render_version_info(self):
        """渲染版本信息"""
        total_translations = st.session_state.get('translation_count', 0)
        st.markdown(f'''
        <div style="text-align: center; color: #587488; font-size: 0.85rem; margin-top: 2rem; 
                    padding: 1.5rem; background: linear-gradient(135deg, #f2f9fc 0%, #e8f4f8 100%); 
                    border: 1px solid #d6e7ef; border-radius: 12px;">
            <div style="margin-bottom: 0.5rem;">
                <strong>RadiAI.Care {self.config.APP_VERSION}</strong> | 為澳洲華人社區打造 ❤️
            </div>
            <div style="font-size: 0.75rem; opacity: 0.8;">
                Powered by GPT-4o | Built with Streamlit | 您已完成 {total_translations} 次翻譯
            </div>
            <div style="font-size: 0.7rem; margin-top: 0.5rem; opacity: 0.6;">
                安全 · 準確 · 易用 | 基於最新醫學 AI 研究構建
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    def render_logo_debug_info(self):
        """渲染 Logo 調試信息（僅在開發模式下顯示）"""
        if st.checkbox("🔧 顯示 Logo 調試信息", key="debug_logo"):
            try:
                logo_data, mime_type = self.config.get_logo_base64()
                st.info(f"✅ Logo 加載成功")
                st.text(f"MIME 類型: {mime_type}")
                st.text(f"數據長度: {len(logo_data)} 字符")
                
                # 顯示 Logo 預覽
                data_uri = f"data:{mime_type};base64,{logo_data}"
                st.markdown(f'<img src="{data_uri}" width="100" height="100" style="border: 1px solid #ccc; border-radius: 8px;">', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Logo 加載失敗: {e}")
                st.text("請檢查 assets/llogo 文件是否存在且格式正確")
