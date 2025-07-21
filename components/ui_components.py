"""
RadiAI.Care UI 組件 - 增強版
包含防濫用系統的UI顯示
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
    
    def render_usage_tracker_enhanced(self, lang: Dict, usage_stats: Dict) -> int:
        """渲染使用次數追蹤（增強版）"""
        remaining = usage_stats['remaining']
        today_usage = usage_stats['today_usage']
        is_locked = usage_stats['is_locked']
        daily_limit = usage_stats.get('daily_limit', 3)
        is_incognito = usage_stats.get('is_incognito', False)
        security_issues = usage_stats.get('security_issues', [])
        
        st.markdown("### 📊 使用情況")
        
        # 顯示安全警告
        if is_incognito:
            st.warning("⚠️ 檢測到無痕/隱私模式！請使用正常瀏覽模式以使用免費服務。")
        
        if security_issues and len(security_issues) > 1:
            st.error("🚨 檢測到異常使用行為，每日限額已降低。")
        
        # 顯示用戶ID（部分隱藏）
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"用戶識別碼：{usage_stats['user_id']}")
        with col2:
            if daily_limit < 3:
                st.caption(f"⚠️ 限額降低至 {daily_limit} 次")
        
        # 主要統計顯示
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # 進度條
            progress = today_usage / daily_limit if daily_limit > 0 else 1.0
            st.progress(min(progress, 1.0))
            
            if is_locked:
                st.error(f"🔒 今日額度已用完（{today_usage}/{daily_limit}）")
            elif remaining > 0:
                if remaining == 1:
                    st.warning(f"⚠️ 今日還可使用 {remaining} 次免費翻譯（最後一次！）")
                else:
                    st.caption(f"今日還可使用 {remaining} 次免費翻譯")
            else:
                st.caption("免費額度已用完")
        
        with col2:
            if remaining > 0:
                st.metric("剩餘", remaining, delta=None)
            else:
                st.metric("剩餘", 0, delta="已用完", delta_color="inverse")
        
        with col3:
            st.metric("今日已用", f"{today_usage}/{daily_limit}")
        
        # 顯示重置時間
        if is_locked or today_usage >= daily_limit:
            from datetime import datetime, timedelta
            import pytz
            
            sydney_tz = pytz.timezone('Australia/Sydney')
            now = datetime.now(sydney_tz)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            hours_until_reset = (tomorrow - now).total_seconds() / 3600
            
            st.info(f"⏰ 額度將在 {int(hours_until_reset)} 小時後重置（澳洲東部時間午夜）")
        
        return remaining
    
    def render_quota_exceeded_enhanced(self, lang: Dict, reason: str):
        """渲染額度超額提示（增強版）"""
        st.error(f"🚫 {reason}")
        
        # 檢查是否因為安全問題
        if "無痕" in reason or "隱私模式" in reason:
            with st.container():
                st.markdown("""
                ### 🔒 無痕模式限制
                
                為了防止濫用，我們的免費服務不支援無痕/隱私瀏覽模式。
                
                **解決方案：**
                1. 🌐 關閉無痕/隱私模式，使用正常瀏覽器窗口
                2. 🔄 刷新頁面重新開始
                3. 💎 或升級到付費版本（不受此限制）
                """)
        
        elif "異常使用" in reason:
            with st.container():
                st.markdown("""
                ### 🚨 異常使用檢測
                
                系統檢測到異常使用模式，為保護服務質量，已限制您的使用。
                
                **可能原因：**
                - 使用自動化工具或腳本
                - 頻繁切換設備或瀏覽器
                - 嘗試繞過使用限制
                
                **解決方案：**
                請聯繫客服說明情況，或直接升級付費版本。
                """)
        
        else:
            # 正常的額度用完提示
            with st.container():
                st.markdown("""
                ### 📅 每日額度說明
                
                **免費用戶限制：**
                - 每個用戶（設備+瀏覽器）每天最多 3 次翻譯
                - 額度在每日午夜（澳洲東部時間）重置
                - 刷新頁面、清除緩存、更換瀏覽器都無法重置額度
                
                **💡 小提示：**
                明天您將獲得新的 3 次免費翻譯機會！
                """)
        
        # 付費選項
        with st.expander("💎 需要更多翻譯？升級專業版", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                #### 🚀 專業版功能：
                
                ✅ **無限次翻譯** - 不再有每日限制  
                ✅ **批量處理** - 一次上傳多個文件  
                ✅ **優先處理** - 更快的翻譯速度  
                ✅ **歷史記錄** - 查看所有翻譯記錄  
                ✅ **API 接入** - 整合到您的系統  
                ✅ **無瀏覽器限制** - 支援所有瀏覽模式  
                ✅ **多設備同步** - 跨設備使用  
                ✅ **專屬客服** - 優先技術支援
                """)
            
            with col2:
                st.markdown("""
                #### 💰 定價方案：
                
                **月付方案**
                - 個人版：$19.99/月
                - 團隊版：$49.99/月（5個用戶）
                - 企業版：聯繫我們
                
                **年付優惠**
                - 個人版：$199/年（省20%）
                - 團隊版：$499/年（省17%）
                
                **7天免費試用** 🎁
                """)
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🆓 開始免費試用", use_container_width=True, type="primary"):
                    st.info("請發送郵件至 support@radiai.care 申請試用")
            
            with col2:
                if st.button("💳 立即購買", use_container_width=True):
                    st.info("請訪問 www.radiai.care/pricing")
            
            with col3:
                if st.button("📧 聯繫銷售", use_container_width=True):
                    st.markdown("[發送郵件](mailto:sales@radiai.care?subject=RadiAI.Care專業版諮詢)")
        
        # 其他選項
        with st.expander("🔑 已有帳號？登入解鎖更多", expanded=False):
            st.markdown("""
            如果您已經購買了專業版，請登入您的帳號：
            """)
            
            email = st.text_input("電子郵件", placeholder="your@email.com")
            password = st.text_input("密碼", type="password", placeholder="********")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("登入", use_container_width=True, type="primary"):
                    st.warning("登入功能即將推出！請先使用免費試用。")
            with col2:
                if st.button("忘記密碼？", use_container_width=True):
                    st.info("請發送郵件至 support@radiai.care 重置密碼")
    
    def render_security_status(self, usage_stats: Dict):
        """渲染安全狀態（調試用）"""
        if st.checkbox("🔒 顯示安全狀態", key="show_security_status"):
            st.markdown("### 🛡️ 安全檢查")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**檢測項目：**")
                
                # 無痕模式檢測
                is_incognito = usage_stats.get('is_incognito', False)
                if is_incognito:
                    st.error("❌ 無痕/隱私模式")
                else:
                    st.success("✅ 正常瀏覽模式")
                
                # 用戶ID檢查
                user_id = usage_stats.get('user_id', '')
                if user_id and user_id != 'unknown':
                    st.success(f"✅ 用戶ID: {user_id}")
                else:
                    st.error("❌ 無效用戶ID")
                
                # 每日限額
                daily_limit = usage_stats.get('daily_limit', 3)
                if daily_limit == 3:
                    st.success("✅ 正常限額: 3次/天")
                else:
                    st.warning(f"⚠️ 限額降低: {daily_limit}次/天")
            
            with col2:
                st.markdown("**安全問題：**")
                
                security_issues = usage_stats.get('security_issues', [])
                if not security_issues:
                    st.success("✅ 未檢測到安全問題")
                else:
                    for issue in security_issues:
                        if issue == 'incognito_mode':
                            st.error("🚫 無痕模式")
                        elif issue == 'no_fingerprint':
                            st.warning("⚠️ 無設備指紋")
                        elif issue == 'invalid_user_id':
                            st.warning("⚠️ 用戶ID異常")
                        else:
                            st.warning(f"⚠️ {issue}")
    
    # ... 其他方法保持不變 ...
    
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
    
    # ... 其餘方法保持不變 ...
