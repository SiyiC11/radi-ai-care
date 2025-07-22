"""
RadiAI.Care UI 組件 - 修復版
修復硬編碼中文問題，完全使用語言配置
"""

import streamlit as st
from typing import Dict, Tuple
from config.settings import AppConfig, UIText
from utils.file_handler import FileHandler

class UIComponents:
    """UI 組件管理器（修復版）"""
    
    def __init__(self):
        self.config = AppConfig()
        self.file_handler = FileHandler()
    
    def render_header(self, lang: Dict):
        """渲染標題和 Logo"""
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
            </div>
            ''', unsafe_allow_html=True)
    
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
        """渲染法律聲明"""
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

        # 使用語言配置的緊急情況文字
        emergency_text = "🔒 您的健康和安全是我們最關心的事項，請務必遵循以上指導原則。"
        if lang["code"] == "simplified_chinese":
            emergency_text = "🔒 您的健康和安全是我们最关心的事项，请务必遵循以上指导原则。"
        
        emergency_contact = "🆘 緊急情況處理："
        emergency_911 = "🚨 緊急醫療：立即撥打 000"
        emergency_hospital = "🏥 就醫建議：前往最近的急診室"
        emergency_gp = "👨‍⚕️ 專業諮詢：聯繫您的家庭醫師 (GP)"
        
        if lang["code"] == "simplified_chinese":
            emergency_contact = "🆘 紧急情况处理："
            emergency_911 = "🚨 紧急医疗：立即拨打 000"
            emergency_hospital = "🏥 就医建议：前往最近的急诊室"
            emergency_gp = "👨‍⚕️ 专业咨询：联系您的家庭医师 (GP)"

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
            {emergency_text}
        </div>

        <div style="margin-top: 1rem;">
            <hr>
            <strong>{emergency_contact}</strong><br>
            {emergency_911}<br>
            {emergency_hospital}<br>
            {emergency_gp}
        </div>
        """, unsafe_allow_html=True)
    
    def render_usage_tracker_enhanced(self, lang: Dict, usage_stats: Dict) -> int:
        """渲染使用次數追蹤（增強版）"""
        remaining = usage_stats['remaining']
        today_usage = usage_stats['today_usage']
        is_locked = usage_stats['is_locked']
        daily_limit = usage_stats.get('daily_limit', 3)
        
        # 使用語言配置
        usage_title = "📊 使用情況" if lang["code"] == "traditional_chinese" else "📊 使用情况"
        user_id_text = "用戶識別碼：" if lang["code"] == "traditional_chinese" else "用户识别码："
        
        st.markdown(f"### {usage_title}")
        
        # 顯示用戶ID（部分隱藏）
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"{user_id_text}{usage_stats['user_id']}")
        with col2:
            if daily_limit < 3:
                limit_text = f"⚠️ 限額降低至 {daily_limit} 次" if lang["code"] == "traditional_chinese" else f"⚠️ 限额降低至 {daily_limit} 次"
                st.caption(limit_text)
        
        # 主要統計顯示
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # 進度條
            progress = today_usage / daily_limit if daily_limit > 0 else 1.0
            st.progress(min(progress, 1.0))
            
            if is_locked:
                locked_text = f"🔒 今日額度已用完（{today_usage}/{daily_limit}）" if lang["code"] == "traditional_chinese" else f"🔒 今日额度已用完（{today_usage}/{daily_limit}）"
                st.error(locked_text)
            elif remaining > 0:
                if remaining == 1:
                    last_chance_text = f"⚠️ 今日還可使用 {remaining} 次免費翻譯（最後一次！）" if lang["code"] == "traditional_chinese" else f"⚠️ 今日还可使用 {remaining} 次免费翻译（最后一次！）"
                    st.warning(last_chance_text)
                else:
                    remaining_text = f"今日還可使用 {remaining} 次免費翻譯" if lang["code"] == "traditional_chinese" else f"今日还可使用 {remaining} 次免费翻译"
                    st.caption(remaining_text)
            else:
                quota_used_text = "免費額度已用完" if lang["code"] == "traditional_chinese" else "免费额度已用完"
                st.caption(quota_used_text)
        
        with col2:
            remaining_label = "剩餘" if lang["code"] == "traditional_chinese" else "剩余"
            used_up_label = "已用完" if lang["code"] == "traditional_chinese" else "已用完"
            
            if remaining > 0:
                st.metric(remaining_label, remaining, delta=None)
            else:
                st.metric(remaining_label, 0, delta=used_up_label, delta_color="inverse")
        
        with col3:
            today_used_label = "今日已用" if lang["code"] == "traditional_chinese" else "今日已用"
            st.metric(today_used_label, f"{today_usage}/{daily_limit}")
        
        # 顯示重置時間
        if is_locked or today_usage >= daily_limit:
            from datetime import datetime, timedelta
            import pytz
            
            sydney_tz = pytz.timezone('Australia/Sydney')
            now = datetime.now(sydney_tz)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            hours_until_reset = (tomorrow - now).total_seconds() / 3600
            
            reset_text = f"⏰ 額度將在 {int(hours_until_reset)} 小時後重置（澳洲東部時間午夜）" if lang["code"] == "traditional_chinese" else f"⏰ 额度将在 {int(hours_until_reset)} 小时后重置（澳洲东部时间午夜）"
            st.info(reset_text)
        
        return remaining
    
    def render_quota_exceeded_enhanced(self, lang: Dict, reason: str):
        """渲染額度超額提示（增強版）"""
        st.error(f"🚫 {reason}")
        
        # 正常的額度用完提示
        with st.container():
            daily_quota_title = "📅 每日額度說明" if lang["code"] == "traditional_chinese" else "📅 每日额度说明"
            
            free_user_limit = "**免費用戶限制：**" if lang["code"] == "traditional_chinese" else "**免费用户限制：**"
            limit_desc_1 = "- 每個用戶（設備+瀏覽器）每天最多 3 次翻譯" if lang["code"] == "traditional_chinese" else "- 每个用户（设备+浏览器）每天最多 3 次翻译"
            limit_desc_2 = "- 額度在每日午夜（澳洲東部時間）重置" if lang["code"] == "traditional_chinese" else "- 额度在每日午夜（澳洲东部时间）重置"
            limit_desc_3 = "- 刷新頁面、清除緩存、更換瀏覽器都無法重置額度" if lang["code"] == "traditional_chinese" else "- 刷新页面、清除缓存、更换浏览器都无法重置额度"
            
            tip_title = "**💡 小提示：**" if lang["code"] == "traditional_chinese" else "**💡 小提示：**"
            tip_desc = "明天您將獲得新的 3 次免費翻譯機會！" if lang["code"] == "traditional_chinese" else "明天您将获得新的 3 次免费翻译机会！"
            
            st.markdown(f"""
            ### {daily_quota_title}
            
            {free_user_limit}
            {limit_desc_1}
            {limit_desc_2}
            {limit_desc_3}
            
            {tip_title}
            {tip_desc}
            """)
        
        # 付費選項
        upgrade_title = "💎 需要更多翻譯？升級專業版" if lang["code"] == "traditional_chinese" else "💎 需要更多翻译？升级专业版"
        
        with st.expander(upgrade_title, expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                pro_features_title = "#### 🚀 專業版功能：" if lang["code"] == "traditional_chinese" else "#### 🚀 专业版功能："
                
                if lang["code"] == "traditional_chinese":
                    features_text = """
                    ✅ **無限次翻譯** - 不再有每日限制  
                    ✅ **批量處理** - 一次上傳多個文件  
                    ✅ **優先處理** - 更快的翻譯速度  
                    ✅ **歷史記錄** - 查看所有翻譯記錄  
                    ✅ **API 接入** - 整合到您的系統  
                    ✅ **無瀏覽器限制** - 支援所有瀏覽模式  
                    ✅ **多設備同步** - 跨設備使用  
                    ✅ **專屬客服** - 優先技術支援
                    """
                else:
                    features_text = """
                    ✅ **无限次翻译** - 不再有每日限制  
                    ✅ **批量处理** - 一次上传多个文件  
                    ✅ **优先处理** - 更快的翻译速度  
                    ✅ **历史记录** - 查看所有翻译记录  
                    ✅ **API 接入** - 整合到您的系统  
                    ✅ **无浏览器限制** - 支持所有浏览模式  
                    ✅ **多设备同步** - 跨设备使用  
                    ✅ **专属客服** - 优先技术支持
                    """
                
                st.markdown(pro_features_title)
                st.markdown(features_text)
            
            with col2:
                pricing_title = "#### 💰 定價方案：" if lang["code"] == "traditional_chinese" else "#### 💰 定价方案："
                
                if lang["code"] == "traditional_chinese":
                    pricing_text = """
                    **月付方案**
                    - 個人版：$19.99/月
                    - 團隊版：$49.99/月（5個用戶）
                    - 企業版：聯繫我們
                    
                    **年付優惠**
                    - 個人版：$199/年（省20%）
                    - 團隊版：$499/年（省17%）
                    
                    **7天免費試用** 🎁
                    """
                else:
                    pricing_text = """
                    **月付方案**
                    - 个人版：$19.99/月
                    - 团队版：$49.99/月（5个用户）
                    - 企业版：联系我们
                    
                    **年付优惠**
                    - 个人版：$199/年（省20%）
                    - 团队版：$499/年（省17%）
                    
                    **7天免费试用** 🎁
                    """
                
                st.markdown(pricing_title)
                st.markdown(pricing_text)
            
            st.markdown("---")
            
            # 按鈕文字
            if lang["code"] == "traditional_chinese":
                btn_trial = "🆓 開始免費試用"
                btn_buy = "💳 立即購買"
                btn_contact = "📧 聯繫銷售"
                trial_msg = "請發送郵件至 support@radiai.care 申請試用"
                buy_msg = "請訪問 www.radiai.care/pricing"
            else:
                btn_trial = "🆓 开始免费试用"
                btn_buy = "💳 立即购买"
                btn_contact = "📧 联系销售"
                trial_msg = "请发送邮件至 support@radiai.care 申请试用"
                buy_msg = "请访问 www.radiai.care/pricing"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(btn_trial, use_container_width=True, type="primary"):
                    st.info(trial_msg)
            
            with col2:
                if st.button(btn_buy, use_container_width=True):
                    st.info(buy_msg)
            
            with col3:
                if st.button(btn_contact, use_container_width=True):
                    st.markdown("[發送郵件](mailto:sales@radiai.care?subject=RadiAI.Care專業版諮詢)")
    
    def render_input_section(self, lang: Dict) -> Tuple[str, str]:
        """渲染輸入區塊"""
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        # 輸入方式選擇
        tab1, tab2 = st.tabs([f"📝 {lang.get('input_text', '文字輸入')}", f"📁 {lang['file_upload']}"])
        
        report_text = ""
        file_type = "manual"
        
        with tab1:
            # 文字輸入
            report_text = st.text_area(
                lang.get('input_label', '請輸入英文放射科報告：'),
                height=200,
                placeholder=lang['input_placeholder'],
                help=lang.get('input_help', '支援直接複製貼上醫學報告文字')
            )
            file_type = "manual"
        
        with tab2:
            # 文件上傳
            uploaded_file = st.file_uploader(
                lang['file_upload'],
                type=list(self.config.SUPPORTED_FILE_TYPES),
                help=lang['supported_formats']
            )
            
            if uploaded_file:
                with st.spinner(lang.get('file_processing', '正在處理文件...')):
                    extracted_text, result = self.file_handler.extract_text(uploaded_file)
                    
                    if extracted_text:
                        st.success(lang['file_uploaded'])
                        
                        # 顯示提取的內容預覽
                        with st.expander(lang.get('file_preview', '文件內容預覽'), expanded=False):
                            st.text_area(
                                lang.get('extracted_content', '提取的內容：'),
                                value=extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else ""),
                                height=150,
                                disabled=True
                            )
                        
                        report_text = extracted_text
                        file_type = result.get("file_info", {}).get("type", "unknown")
                    else:
                        error_msg = result.get("error", lang['error_file_read'])
                        st.error(f"❌ {error_msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return report_text, file_type
    
    def render_translate_button(self, lang: Dict, report_text: str) -> bool:
        """渲染翻譯按鈕"""
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
        """渲染翻譯結果"""
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        
        success_msg = lang.get('translation_complete', '🎉 翻譯完成！')
        st.success(success_msg)
        
        # 顯示翻譯結果
        st.markdown(result_content)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_completion_status_enhanced(self, lang: Dict, usage_stats: Dict):
        """渲染完成狀態"""
        remaining = usage_stats['remaining']
        
        if remaining > 0:
            remaining_msg = f"✅ 翻譯完成！您今日還有 {remaining} 次免費使用機會。" if lang["code"] == "traditional_chinese" else f"✅ 翻译完成！您今日还有 {remaining} 次免费使用机会。"
            st.info(remaining_msg)
        else:
            quota_used_msg = "✅ 翻譯完成！您今日的免費額度已用完。" if lang["code"] == "traditional_chinese" else "✅ 翻译完成！您今日的免费额度已用完。"
            st.warning(quota_used_msg)
    
    def render_footer(self, lang: Dict):
        """渲染頁腳"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"📧 {lang['footer_support']}: support@radiai.care")
        with col2:
            st.markdown(f"🔒 {lang['footer_privacy']}")
        with col3:
            st.markdown(f"📋 {lang['footer_terms']}")
    
    def render_version_info(self):
        """渲染版本信息"""
        st.markdown(f"<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 1rem;'>RadiAI.Care {self.config.APP_VERSION}</div>", unsafe_allow_html=True)
