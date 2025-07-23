"""
RadiAI.Care - 最终版增强UI组件
深度整合反馈系统、配额管理、实时倒计时的完整用户界面
"""

import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px

class EnhancedUIComponents:
    """增强版UI组件系统"""
    
    def __init__(self, config, file_handler):
        self.config = config
        self.file_handler = file_handler
    
    def render_intelligent_usage_dashboard(self, usage_stats: Dict[str, Any], 
                                         feedback_collector, session_manager) -> int:
        """渲染智能使用仪表板"""
        
        st.markdown("### 📊 智能使用管理")
        
        # 主要指标卡片
        self._render_usage_metrics_cards(usage_stats)
        
        # 配额状态和倒计时
        if usage_stats['is_locked']:
            self._render_quota_locked_status(usage_stats, session_manager)
        else:
            self._render_active_quota_status(usage_stats)
        
        # 奖励配额系统
        self._render_bonus_quota_system(usage_stats, session_manager)
        
        # 实时倒计时（如果需要）
        if usage_stats['is_locked'] or usage_stats['remaining'] == 0:
            self._render_advanced_countdown_timer(usage_stats)
        
        return usage_stats['remaining']
    
    def _render_usage_metrics_cards(self, usage_stats: Dict[str, Any]):
        """渲染使用指标卡片"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 今日使用情况
            usage_ratio = usage_stats['today_usage'] / usage_stats['daily_limit']
            delta_color = "inverse" if usage_ratio >= 1.0 else "normal"
            st.metric(
                "今日使用",
                f"{usage_stats['today_usage']}/{usage_stats['daily_limit']}",
                delta=f"{usage_stats['remaining']} 剩余",
                delta_color=delta_color
            )
        
        with col2:
            # 配额组成
            bonus_quota = usage_stats.get('bonus_quota', 0)
            if bonus_quota > 0:
                st.metric(
                    "配额构成",
                    f"基础 {usage_stats['base_limit']} + 奖励 {bonus_quota}",
                    delta="🎁 已获得奖励",
                    delta_color="normal"
                )
            else:
                st.metric(
                    "基础配额",
                    usage_stats['base_limit'],
                    delta="可通过反馈获得奖励",
                    delta_color="off"
                )
        
        with col3:
            # 满意度评分
            avg_satisfaction = usage_stats.get('avg_satisfaction', 0)
            if avg_satisfaction > 0:
                satisfaction_stars = "⭐" * int(avg_satisfaction)
                st.metric(
                    "平均满意度",
                    f"{avg_satisfaction}/5 {satisfaction_stars}",
                    delta=f"基于 {usage_stats.get('feedback_count', 0)} 次反馈",
                    delta_color="normal"
                )
            else:
                st.metric(
                    "满意度评分",
                    "暂无评分",
                    delta="欢迎提供反馈",
                    delta_color="off"
                )
        
        with col4:
            # 使用效率
            efficiency = usage_stats.get('usage_efficiency', 1.0)
            efficiency_pct = int(efficiency * 100)
            efficiency_emoji = "🚀" if efficiency >= 0.9 else "📈" if efficiency >= 0.7 else "⚡"
            st.metric(
                "使用效率",
                f"{efficiency_pct}% {efficiency_emoji}",
                delta="高效使用可获奖励",
                delta_color="normal" if efficiency >= 0.9 else "off"
            )
    
    def _render_active_quota_status(self, usage_stats: Dict[str, Any]):
        """渲染活跃配额状态"""
        remaining = usage_stats['remaining']
        total_limit = usage_stats['daily_limit']
        used = usage_stats['today_usage']
        
        # 进度条显示
        progress = used / total_limit if total_limit > 0 else 0
        
        # 根据剩余量设置不同的显示样式
        if remaining > 2:
            st.success(f"✅ 配额充足：今日还可使用 {remaining} 次翻译")
            st.progress(progress, text=f"已使用 {used}/{total_limit}")
        elif remaining > 0:
            st.warning(f"⚠️ 配额偏少：今日还可使用 {remaining} 次翻译")
            st.progress(progress, text=f"已使用 {used}/{total_limit} - 请合理安排使用")
        else:
            st.info("ℹ️ 所有配额即将用完，考虑提供反馈获得奖励配额")
            st.progress(1.0, text=f"已使用 {used}/{total_limit}")
    
    def _render_quota_locked_status(self, usage_stats: Dict[str, Any], session_manager):
        """渲染配额锁定状态"""
        st.error(f"🔒 今日配额已用完 ({usage_stats['today_usage']}/{usage_stats['daily_limit']})")
        
        # 显示解锁建议
        unlock_suggestions = session_manager.get_quota_unlock_suggestions()
        
        if unlock_suggestions:
            st.markdown("### 💡 获得额外配额的方法")
            
            for suggestion in unlock_suggestions:
                with st.expander(f"🎯 {suggestion['title']} (+{suggestion['potential_bonus']} 次)", expanded=True):
                    st.markdown(f"**说明：** {suggestion['description']}")
                    st.markdown(f"**操作：** {suggestion['action']}")
                    
                    if suggestion['type'] == 'satisfaction':
                        st.info("💡 在下次翻译完成后，请给出真实的高分评价")
                    elif suggestion['type'] == 'detailed_feedback':
                        st.info("💡 详细反馈包括：改进建议、遇到的问题、功能需求等")
                    elif suggestion['type'] == 'efficiency':
                        st.info("💡 避免重复提交、仔细检查输入内容可提高效率")
        
        # 升级选项
        with st.expander("🚀 升级专业版 - 无限制使用", expanded=False):
            self._render_upgrade_preview()
    
    def _render_bonus_quota_system(self, usage_stats: Dict[str, Any], session_manager):
        """渲染奖励配额系统"""
        quota_sources = usage_stats.get('quota_sources', {})
        bonus_total = sum([
            quota_sources.get('satisfaction_bonus', 0),
            quota_sources.get('feedback_bonus', 0),
            quota_sources.get('efficiency_bonus', 0)
        ])
        
        if bonus_total > 0 or any(quota_sources.get(k, 0) > 0 for k in ['satisfaction_bonus', 'feedback_bonus', 'efficiency_bonus']):
            st.markdown("#### 🎁 奖励配额系统")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sat_bonus = quota_sources.get('satisfaction_bonus', 0)
                status = "✅ 已获得" if sat_bonus > 0 else "⭕ 未获得"
                st.metric(
                    "满意度奖励",
                    f"{sat_bonus} 次",
                    delta=status,
                    delta_color="normal" if sat_bonus > 0 else "off"
                )
                if sat_bonus == 0:
                    st.caption("平均满意度 ≥ 4.5 获得")
            
            with col2:
                fb_bonus = quota_sources.get('feedback_bonus', 0)
                status = "✅ 已获得" if fb_bonus > 0 else "⭕ 未获得"
                st.metric(
                    "反馈奖励",
                    f"{fb_bonus} 次",
                    delta=status,
                    delta_color="normal" if fb_bonus > 0 else "off"
                )
                if fb_bonus == 0:
                    st.caption("提供详细反馈获得")
            
            with col3:
                eff_bonus = quota_sources.get('efficiency_bonus', 0)
                status = "✅ 已获得" if eff_bonus > 0 else "⭕ 未获得"
                st.metric(
                    "效率奖励",
                    f"{eff_bonus} 次",
                    delta=status,
                    delta_color="normal" if eff_bonus > 0 else "off"
                )
                if eff_bonus == 0:
                    st.caption("使用效率 ≥ 90% 获得")
    
    def _render_advanced_countdown_timer(self, usage_stats: Dict[str, Any]):
        """渲染高级倒计时器"""
        reset_hours = usage_stats.get('reset_time_hours', 0)
        reset_minutes = usage_stats.get('reset_time_minutes', 0)
        reset_timestamp = usage_stats.get('reset_timestamp', 0)
        
        # 创建倒计时容器
        countdown_container = st.container()
        
        with countdown_container:
            # 倒计时显示区域
            timer_placeholder = st.empty()
            
            # JavaScript 实时倒计时
            countdown_html = f"""
            <div id="advanced-countdown-container" style="
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                margin: 15px 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            ">
                <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px;">
                    <span style="font-size: 24px;">⏰</span>
                    <h3 style="margin: 0; font-weight: 600;">配额重置倒计时</h3>
                </div>
                
                <div id="timer-display" style="
                    font-size: 32px;
                    font-weight: bold;
                    margin: 15px 0;
                    padding: 15px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                ">
                    {reset_hours:02d}:{reset_minutes:02d}:00
                </div>
                
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div style="text-align: center;">
                        <div id="hours-display" style="font-size: 20px; font-weight: bold;">{reset_hours:02d}</div>
                        <div style="font-size: 12px; opacity: 0.8;">小时</div>
                    </div>
                    <div style="text-align: center;">
                        <div id="minutes-display" style="font-size: 20px; font-weight: bold;">{reset_minutes:02d}</div>
                        <div style="font-size: 12px; opacity: 0.8;">分钟</div>
                    </div>
                    <div style="text-align: center;">
                        <div id="seconds-display" style="font-size: 20px; font-weight: bold;">00</div>
                        <div style="font-size: 12px; opacity: 0.8;">秒</div>
                    </div>
                </div>
                
                <div style="margin-top: 15px; font-size: 14px; opacity: 0.9;">
                    🇦🇺 澳洲东部时间午夜自动重置
                </div>
                
                <div id="reset-progress" style="
                    width: 100%;
                    height: 4px;
                    background: rgba(255,255,255,0.2);
                    border-radius: 2px;
                    margin-top: 15px;
                    overflow: hidden;
                ">
                    <div id="progress-bar" style="
                        height: 100%;
                        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
                        transition: width 1s ease;
                        border-radius: 2px;
                    "></div>
                </div>
            </div>

            <script>
            function updateAdvancedCountdown() {{
                try {{
                    const now = new Date();
                    const sydney = new Date(now.toLocaleString("en-US", {{timeZone: "Australia/Sydney"}}));
                    
                    // 计算到下一个午夜的时间
                    const tomorrow = new Date(sydney);
                    tomorrow.setDate(tomorrow.getDate() + 1);
                    tomorrow.setHours(0, 0, 0, 0);
                    
                    const diff = tomorrow.getTime() - sydney.getTime();
                    
                    if (diff > 0) {{
                        const hours = Math.floor(diff / (1000 * 60 * 60));
                        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                        
                        // 更新主计时器
                        const timerDisplay = document.getElementById('timer-display');
                        if (timerDisplay) {{
                            timerDisplay.innerHTML = 
                                String(hours).padStart(2, '0') + ':' + 
                                String(minutes).padStart(2, '0') + ':' + 
                                String(seconds).padStart(2, '0');
                        }}
                        
                        // 更新分项显示
                        const hoursDisplay = document.getElementById('hours-display');
                        const minutesDisplay = document.getElementById('minutes-display');
                        const secondsDisplay = document.getElementById('seconds-display');
                        
                        if (hoursDisplay) hoursDisplay.innerHTML = String(hours).padStart(2, '0');
                        if (minutesDisplay) minutesDisplay.innerHTML = String(minutes).padStart(2, '0');
                        if (secondsDisplay) secondsDisplay.innerHTML = String(seconds).padStart(2, '0');
                        
                        // 更新进度条
                        const totalSecondsInDay = 24 * 60 * 60;
                        const remainingSeconds = hours * 3600 + minutes * 60 + seconds;
                        const progressPercent = ((totalSecondsInDay - remainingSeconds) / totalSecondsInDay) * 100;
                        
                        const progressBar = document.getElementById('progress-bar');
                        if (progressBar) {{
                            progressBar.style.width = progressPercent + '%';
                        }}
                        
                        // 在最后一分钟添加闪烁效果
                        const container = document.getElementById('advanced-countdown-container');
                        if (container) {{
                            if (hours === 0 && minutes === 0 && seconds <= 60) {{
                                container.style.animation = 'pulse 1s infinite';
                            }} else {{
                                container.style.animation = 'none';
                            }}
                        }}
                        
                    }} else {{
                        // 时间到了
                        const container = document.getElementById('advanced-countdown-container');
                        if (container) {{
                            container.innerHTML = `
                                <div style="text-align: center; padding: 20px;">
                                    <div style="font-size: 48px; margin-bottom: 10px;">🎉</div>
                                    <h3 style="color: #4CAF50; margin: 10px 0;">配额已重置！</h3>
                                    <p style="margin: 10px 0;">您的免费翻译次数已恢复</p>
                                    <button onclick="window.location.reload()" style="
                                        background: #4CAF50;
                                        color: white;
                                        border: none;
                                        padding: 10px 20px;
                                        border-radius: 5px;
                                        cursor: pointer;
                                        font-size: 16px;
                                    ">刷新页面</button>
                                </div>
                            `;
                        }}
                    }}
                }} catch (error) {{
                    console.error('Countdown update error:', error);
                }}
            }}
            
            // CSS动画定义
            const style = document.createElement('style');
            style.textContent = `
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.02); }}
                }}
            `;
            document.head.appendChild(style);
            
            // 立即更新一次
            updateAdvancedCountdown();
            
            // 每秒更新
            const countdownInterval = setInterval(updateAdvancedCountdown, 1000);
            
            // 页面卸载时清理
            window.addEventListener('beforeunload', function() {{
                clearInterval(countdownInterval);
            }});
            </script>
            """
            
            timer_placeholder.markdown(countdown_html, unsafe_allow_html=True)
    
    def _render_upgrade_preview(self):
        """渲染升级预览"""
        st.markdown("""
        **🚀 专业版特权：**
        - ♾️ 无限翻译次数
        - ⚡ 优先处理队列
        - 📊 详细使用统计
        - 🔄 批量文件处理
        - 📱 移动端优化
        - 🛡️ 数据安全保障
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆓 7天免费试用", use_container_width=True):
                st.info("请发送邮件至 trial@radiai.care")
        with col2:
            if st.button("💳 立即升级", use_container_width=True):
                st.info("访问 radiai.care/upgrade")
    
    def render_integrated_feedback_interface(self, translation_id: str, user_id: str,
                                           feedback_collector, session_manager,
                                           translation_quality: float = 0.0,
                                           processing_time: int = 0) -> None:
        """渲染整合的反馈界面"""
        
        # 检查是否需要显示反馈
        smart_integration = feedback_collector.SmartFeedbackIntegration if hasattr(feedback_collector, 'SmartFeedbackIntegration') else None
        
        if smart_integration and smart_integration.should_show_feedback_prompt(translation_id):
            st.markdown("---")
            
            # 智能反馈流程
            if translation_quality < 0.7 or processing_time > 30000:
                self._render_quick_improvement_feedback(translation_id, user_id, session_manager)
            else:
                self._render_comprehensive_feedback_flow(translation_id, user_id, feedback_collector, session_manager)
        
        # 始终显示简化的满意度收集
        self._render_minimal_satisfaction_collector(translation_id, user_id, session_manager)
    
    def _render_quick_improvement_feedback(self, translation_id: str, user_id: str, session_manager):
        """渲染快速改进反馈"""
        st.markdown("### 🔧 快速反馈")
        st.info("我们发现这次体验可能不够完美，您的反馈将帮助我们快速改进！")
        
        with st.form(f"quick_feedback_{translation_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                satisfaction = st.slider("体验评分", 1, 5, 3, help="1=很差，5=很好")
                main_issue = st.selectbox(
                    "主要问题",
                    ["翻译不准确", "速度太慢", "格式问题", "界面问题", "文件处理问题", "其他"],
                )
            
            with col2:
                urgency = st.selectbox("重要程度", ["一般", "重要", "紧急"])
                suggestion = st.text_area(
                    "改进建议",
                    placeholder="简单描述问题和建议...",
                    height=80
                )
            
            if st.form_submit_button("🚀 提交快速反馈", type="primary", use_container_width=True):
                feedback_data = {
                    'translation_id': translation_id,
                    'user_id': user_id,
                    'overall_satisfaction': satisfaction,
                    'feedback_type': 'quick_improvement',
                    'primary_issue': main_issue,
                    'urgency_level': urgency,
                    'detailed_comments': suggestion,
                    'extra_metadata': {
                        'trigger': 'quality_concern',
                        'submission_type': 'quick'
                    }
                }
                
                success = session_manager.record_feedback_and_update_quota(feedback_data)
                if success:
                    st.session_state[f"feedback_submitted_{translation_id}"] = True
                    st.rerun()
                else:
                    st.error("反馈提交失败，请稍后重试")
    
    def _render_comprehensive_feedback_flow(self, translation_id: str, user_id: str, 
                                          feedback_collector, session_manager):
        """渲染综合反馈流程"""
        feedback_collector.render_comprehensive_feedback_form(translation_id, user_id)
    
    def _render_minimal_satisfaction_collector(self, translation_id: str, user_id: str, session_manager):
        """渲染最小化满意度收集器"""
        # 检查是否已提交任何形式的反馈
        if st.session_state.get(f"feedback_submitted_{translation_id}", False):
            return
        
        # 简化的满意度收集
        with st.expander("⭐ 快速评价（可获得奖励配额）", expanded=False):
            st.markdown("只需 5 秒钟，您的评价对我们很重要！")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            rating = None
            for i, col in enumerate([col1, col2, col3, col4, col5], 1):
                with col:
                    if st.button(f"{'⭐' * i}", key=f"rating_{i}_{translation_id}", 
                                use_container_width=True, 
                                help=f"{i} 星评价"):
                        rating = i
                        break
            
            if rating:
                # 立即处理评分
                feedback_data = {
                    'translation_id': translation_id,
                    'user_id': user_id,
                    'overall_satisfaction': rating,
                    'feedback_type': 'quick_rating',
                    'extra_metadata': {
                        'submission_type': 'minimal',
                        'interface': 'star_rating'
                    }
                }
                
                success = session_manager.record_feedback_and_update_quota(feedback_data)
                if success:
                    st.session_state[f"feedback_submitted_{translation_id}"] = True
                    
                    # 根据评分显示不同的感谢信息
                    if rating >= 4:
                        st.success(f"🌟 感谢您的 {rating} 星好评！")
                        st.balloons()
                    elif rating == 3:
                        st.info("👍 感谢您的评价！我们会继续努力改进。")
                    else:
                        st.warning("😔 感谢您的诚实反馈，我们会认真改进相关问题。")
                    
                    st.rerun()
    
    def render_feedback_impact_visualization(self, sheets_manager):
        """渲染反馈影响可视化"""
        try:
            # 获取分析数据
            analytics = sheets_manager.get_daily_analytics()
            
            if not analytics:
                st.info("📊 反馈数据收集中...")
                return
            
            st.markdown("### 📈 用户反馈影响")
            
            # 关键指标展示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("今日反馈", analytics.get('feedback_count', 0), 
                         help="用户主动提供的反馈数量")
            
            with col2:
                avg_sat = analytics.get('avg_satisfaction', 0)
                st.metric("平均满意度", f"{avg_sat:.1f}/5",
                         delta=f"{avg_sat - 4.0:+.1f}",
                         help="所有反馈的平均满意度评分")
            
            with col3:
                quality_rating = analytics.get('avg_quality_rating', 0)
                st.metric("翻译质量", f"{quality_rating:.1f}/5",
                         help="用户对翻译质量的平均评分")
            
            with col4:
                total_users = analytics.get('unique_users', 0)
                feedback_rate = (analytics.get('feedback_count', 0) / max(total_users, 1)) * 100
                st.metric("反馈参与率", f"{feedback_rate:.1f}%",
                         help="提供反馈的用户比例")
            
            # 问题分布图表
            if analytics.get('common_issues'):
                st.markdown("#### 🎯 主要问题分布")
                issues_data = analytics['common_issues']
                
                fig = px.pie(
                    values=list(issues_data.values())[:5],
                    names=list(issues_data.keys())[:5],
                    title="用户反馈的主要问题"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"反馈分析加载失败: {e}")
    
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
        """渲染输入部分"""
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        
        if 'input_method' not in st.session_state:
            st.session_state.input_method = 'text'
        
        st.markdown("### 📝 选择输入方式")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 文字输入", key="input_text_btn", use_container_width=True,
                        type="primary" if st.session_state.input_method == 'text' else "secondary"):
                st.session_state.input_method = 'text'
                st.rerun()
        
        with col2:
            if st.button("📁 上传文件", key="input_file_btn", use_container_width=True,
                        type="primary" if st.session_state.input_method == 'file' else "secondary"):
                st.session_state.input_method = 'file'
                st.rerun()
        
        st.markdown("---")
        
        report_text = ""
        file_type = "manual"
        
        if st.session_state.input_method == 'text':
            st.markdown("#### 📝 请输入英文放射科报告")
            report_text = st.text_area(
                lang.get('input_label', '请输入英文放射科报告：'),
                height=200,
                placeholder=lang['input_placeholder'],
                key="text_input_area"
            )
            file_type = "manual"
        
        elif st.session_state.input_method == 'file':
            st.markdown("#### 📁 上传报告文件")
            uploaded_file = st.file_uploader(
                lang['file_upload'],
                type=list(self.config.SUPPORTED_FILE_TYPES),
                help=lang['supported_formats'],
                key="file_uploader"
            )
            
            if uploaded_file:
                with st.spinner("正在处理文件..."):
                    extracted_text, result = self.file_handler.extract_text(uploaded_file)
                    
                    if extracted_text:
                        st.success("✅ 文件上传成功")
                        
                        with st.expander("📄 文件内容预览", expanded=False):
                            preview_text = extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else "")
                            st.text_area("提取的内容：", value=preview_text, height=150, disabled=True)
                        
                        report_text = extracted_text
                        file_type = result.get("file_info", {}).get("type", "unknown")
                    else:
                        st.error(f"❌ {result.get('error', '文件处理失败')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return report_text, file_type

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
