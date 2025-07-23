"""
RadiAI.Care - 高级反馈收集系统
多维度满意度调查，深度用户洞察，智能反馈分析
"""

import streamlit as st
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class FeedbackMetrics:
    """反馈指标数据类"""
    overall_satisfaction: int = 0
    translation_quality: int = 0
    speed_rating: int = 0
    ease_of_use: int = 0
    feature_completeness: int = 0
    likelihood_to_recommend: int = 0
    comparison_rating: int = 0

@dataclass
class UserContext:
    """用户上下文数据类"""
    user_type: str = ""
    primary_use_case: str = ""
    usage_frequency: str = ""
    technical_level: str = ""
    medical_background: str = ""

@dataclass
class FeedbackData:
    """完整反馈数据类"""
    translation_id: str
    user_id: str
    metrics: FeedbackMetrics
    context: UserContext
    improvement_areas: List[str]
    specific_issues: List[str]
    feature_requests: List[str]
    detailed_comments: str = ""
    contact_email: str = ""
    follow_up_consent: bool = False
    submission_time: datetime = None

class AdvancedFeedbackCollector:
    """高级反馈收集器"""
    
    # 反馈选项配置
    FEEDBACK_CONFIG = {
        'satisfaction_metrics': {
            'overall_satisfaction': {
                'label': '整体满意度',
                'description': '您对 RadiAI.Care 的整体体验如何？',
                'scale_labels': ['非常不满意', '不满意', '一般', '满意', '非常满意']
            },
            'translation_quality': {
                'label': '翻译质量',
                'description': '翻译内容的准确性和专业程度',
                'scale_labels': ['很差', '较差', '一般', '良好', '优秀']
            },
            'speed_rating': {
                'label': '响应速度',
                'description': '从提交到获得结果的等待时间',
                'scale_labels': ['很慢', '较慢', '适中', '较快', '很快']
            },
            'ease_of_use': {
                'label': '易用性',
                'description': '界面操作的简单程度和用户体验',
                'scale_labels': ['很难用', '较难', '一般', '容易', '非常容易']
            },
            'feature_completeness': {
                'label': '功能完整性',
                'description': '功能是否满足您的医学报告翻译需求',
                'scale_labels': ['很不足', '不足', '基本够用', '较完整', '非常完整']
            },
            'likelihood_to_recommend': {
                'label': '推荐意愿',
                'description': '您向他人推荐这个工具的可能性',
                'scale_labels': ['绝不推荐', '不太可能', '可能', '很可能', '一定推荐']
            },
            'comparison_rating': {
                'label': '竞品比较',
                'description': '与其他翻译工具相比的优势',
                'scale_labels': ['远不如', '略差', '差不多', '略好', '远超过']
            }
        },
        
        'user_context': {
            'user_type': {
                'label': '用户类型',
                'options': ['患者', '患者家属', '医务人员', '医学生', '研究人员', '其他']
            },
            'primary_use_case': {
                'label': '主要用途',
                'options': [
                    '理解自己的检查报告', '为家人解读报告', '临床参考',
                    '学术研究', '教学用途', '第二意见参考', '其他'
                ]
            },
            'usage_frequency': {
                'label': '使用频率',
                'options': ['首次使用', '偶尔使用', '定期使用', '频繁使用']
            },
            'technical_level': {
                'label': '技术水平',
                'options': ['初学者', '一般用户', '熟练用户', '专业用户']
            },
            'medical_background': {
                'label': '医学背景',
                'options': ['无医学背景', '基础医学知识', '医学相关专业', '医疗从业者']
            }
        },
        
        'improvement_areas': [
            '翻译准确性', '响应速度', '界面设计', '功能扩展',
            '用户指导', '移动端体验', '文件支持', '多语言支持',
            '专业术语解释', '报告格式化', '历史记录', '导出功能'
        ],
        
        'common_issues': [
            '翻译错误或不准确', '专业术语解释不清', '处理速度太慢',
            '界面操作困难', '文件上传失败', '格式识别问题',
            '移动端显示异常', '功能缺失', '结果不完整', '系统错误'
        ],
        
        'feature_requests': [
            '批量文件处理', 'PDF标注功能', '语音播放', '报告对比',
            '历史记录管理', '收藏重要内容', '分享功能', '打印优化',
            '离线使用', '多语言切换', 'API接口', '专业版功能',
            '团队协作', '数据导出', '自定义设置', '通知提醒'
        ]
    }
    
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
    
    def render_comprehensive_feedback_form(self, translation_id: str, user_id: str, 
                                         language_code: str = "zh_CN") -> Optional[FeedbackData]:
        """渲染综合反馈表单"""
        
        # 检查是否已提交
        feedback_key = f"feedback_submitted_{translation_id}"
        if st.session_state.get(feedback_key, False):
            st.success("🙏 感谢您的详细反馈！您的意见对我们改进产品非常重要。")
            self._show_feedback_impact()
            return None
        
        st.markdown("---")
        st.markdown("## 💬 您的反馈对我们很重要")
        st.markdown("请花几分钟时间分享您的使用体验，帮助我们不断改进服务质量。")
        
        with st.expander("📊 满意度评价", expanded=True):
            metrics = self._render_satisfaction_metrics()
        
        with st.expander("👤 用户背景信息", expanded=True):
            context = self._render_user_context()
        
        with st.expander("🎯 改进建议", expanded=True):
            improvements = self._render_improvement_suggestions()
        
        with st.expander("💭 详细意见（可选）", expanded=False):
            additional_feedback = self._render_additional_feedback()
        
        # 提交按钮
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 提交反馈", type="primary", use_container_width=True):
                return self._process_feedback_submission(
                    translation_id, user_id, metrics, context, 
                    improvements, additional_feedback, language_code
                )
        
        return None
    
    def _render_satisfaction_metrics(self) -> FeedbackMetrics:
        """渲染满意度评价部分"""
        st.markdown("### 📈 满意度评价")
        st.markdown("请根据您的使用体验给出 1-5 分的评价：")
        
        metrics = FeedbackMetrics()
        config = self.FEEDBACK_CONFIG['satisfaction_metrics']
        
        # 使用列布局优化显示
        for i, (metric_key, metric_config) in enumerate(config.items()):
            if i % 2 == 0:
                col1, col2 = st.columns(2)
            
            current_col = col1 if i % 2 == 0 else col2
            
            with current_col:
                # 创建星级评分界面
                rating = st.select_slider(
                    f"**{metric_config['label']}**",
                    options=[1, 2, 3, 4, 5],
                    value=4,  # 默认较高评分
                    format_func=lambda x: f"{'⭐' * x} ({metric_config['scale_labels'][x-1]})",
                    help=metric_config['description'],
                    key=f"rating_{metric_key}"
                )
                setattr(metrics, metric_key, rating)
        
        # 实时反馈分析
        avg_score = sum(asdict(metrics).values()) / len(asdict(metrics))
        self._show_real_time_analysis(avg_score)
        
        return metrics
    
    def _render_user_context(self) -> UserContext:
        """渲染用户背景信息部分"""
        st.markdown("### 👥 关于您")
        st.markdown("了解您的背景有助于我们提供更好的服务：")
        
        context = UserContext()
        config = self.FEEDBACK_CONFIG['user_context']
        
        col1, col2 = st.columns(2)
        
        with col1:
            context.user_type = st.selectbox(
                "您的身份",
                config['user_type']['options'],
                key="user_type"
            )
            
            context.primary_use_case = st.selectbox(
                "主要使用目的",
                config['primary_use_case']['options'],
                key="primary_use_case"
            )
            
            context.usage_frequency = st.selectbox(
                "使用频率",
                config['usage_frequency']['options'],
                key="usage_frequency"
            )
        
        with col2:
            context.technical_level = st.selectbox(
                "技术熟练程度",
                config['technical_level']['options'],
                index=1,  # 默认"一般用户"
                key="technical_level"
            )
            
            context.medical_background = st.selectbox(
                "医学背景",
                config['medical_background']['options'],
                key="medical_background"
            )
        
        return context
    
    def _render_improvement_suggestions(self) -> Dict[str, List[str]]:
        """渲染改进建议部分"""
        st.markdown("### 🎯 改进建议")
        
        improvements = {}
        
        # 改进领域
        st.markdown("**您认为哪些方面最需要改进？** (可多选)")
        improvements['improvement_areas'] = st.multiselect(
            "改进领域",
            self.FEEDBACK_CONFIG['improvement_areas'],
            key="improvement_areas",
            label_visibility="collapsed"
        )
        
        # 遇到的具体问题
        st.markdown("**您在使用过程中遇到了哪些问题？** (可多选)")
        improvements['specific_issues'] = st.multiselect(
            "具体问题",
            self.FEEDBACK_CONFIG['common_issues'],
            key="specific_issues",
            label_visibility="collapsed"
        )
        
        # 功能需求
        st.markdown("**您希望我们增加哪些功能？** (可多选)")
        improvements['feature_requests'] = st.multiselect(
            "功能需求",
            self.FEEDBACK_CONFIG['feature_requests'],
            key="feature_requests",
            label_visibility="collapsed"
        )
        
        return improvements
    
    def _render_additional_feedback(self) -> Dict[str, Any]:
        """渲染附加反馈部分"""
        st.markdown("### 💭 详细反馈")
        
        additional = {}
        
        # 详细评论
        additional['detailed_comments'] = st.text_area(
            "请分享您的详细意见或建议",
            placeholder="例如：翻译质量很好，但希望能增加语音播放功能...",
            height=120,
            key="detailed_comments"
        )
        
        # 联系方式
        col1, col2 = st.columns(2)
        
        with col1:
            additional['contact_email'] = st.text_input(
                "联系邮箱（可选）",
                placeholder="用于重要问题的后续沟通",
                key="contact_email"
            )
        
        with col2:
            additional['follow_up_consent'] = st.checkbox(
                "同意后续联系",
                help="我们可能会就您的反馈进行后续沟通",
                key="follow_up_consent"
            )
        
        # 匿名选项
        additional['anonymous_feedback'] = st.checkbox(
            "匿名提交反馈",
            value=True,
            help="选择此项将不保存您的联系信息",
            key="anonymous_feedback"
        )
        
        return additional
    
    def _show_real_time_analysis(self, avg_score: float):
        """显示实时评分分析"""
        if avg_score >= 4.5:
            st.success(f"🌟 综合评分：{avg_score:.1f}/5 - 太棒了！感谢您的认可！")
        elif avg_score >= 3.5:
            st.info(f"👍 综合评分：{avg_score:.1f}/5 - 不错的体验！我们会继续努力！")
        elif avg_score >= 2.5:
            st.warning(f"📊 综合评分：{avg_score:.1f}/5 - 我们还有改进空间")
        else:
            st.error(f"😔 综合评分：{avg_score:.1f}/5 - 很抱歉没有达到您的期望")
    
    def _show_feedback_impact(self):
        """显示反馈影响和统计"""
        st.markdown("### 📈 您的反馈影响")
        
        # 模拟显示反馈统计（实际应从数据库获取）
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("本月反馈数", "1,234", "+56")
        
        with col2:
            st.metric("平均满意度", "4.2/5", "+0.1")
        
        with col3:
            st.metric("已修复问题", "23", "+3")
        
        st.info("💡 您的反馈已被产品团队收到，我们会认真分析并在未来版本中改进！")
    
    def _process_feedback_submission(self, translation_id: str, user_id: str, 
                                   metrics: FeedbackMetrics, context: UserContext,
                                   improvements: Dict[str, List[str]], 
                                   additional_feedback: Dict[str, Any],
                                   language_code: str) -> Optional[FeedbackData]:
        """处理反馈提交"""
        
        try:
            # 构建完整反馈数据
            feedback_data = FeedbackData(
                translation_id=translation_id,
                user_id=user_id if not additional_feedback.get('anonymous_feedback') else 'anonymous',
                metrics=metrics,
                context=context,
                improvement_areas=improvements.get('improvement_areas', []),
                specific_issues=improvements.get('specific_issues', []),
                feature_requests=improvements.get('feature_requests', []),
                detailed_comments=additional_feedback.get('detailed_comments', ''),
                contact_email=additional_feedback.get('contact_email', '') if not additional_feedback.get('anonymous_feedback') else '',
                follow_up_consent=additional_feedback.get('follow_up_consent', False),
                submission_time=datetime.now()
            )
            
            # 准备数据库记录格式
            db_data = {
                'translation_id': feedback_data.translation_id,
                'user_id': feedback_data.user_id,
                'overall_satisfaction': feedback_data.metrics.overall_satisfaction,
                'translation_quality': feedback_data.metrics.translation_quality,
                'speed_rating': feedback_data.metrics.speed_rating,
                'ease_of_use': feedback_data.metrics.ease_of_use,
                'feature_completeness': feedback_data.metrics.feature_completeness,
                'likelihood_to_recommend': feedback_data.metrics.likelihood_to_recommend,
                'comparison_rating': feedback_data.metrics.comparison_rating,
                'primary_use_case': feedback_data.context.primary_use_case,
                'user_type': feedback_data.context.user_type,
                'usage_frequency': feedback_data.context.usage_frequency,
                'improvement_areas': feedback_data.improvement_areas,
                'specific_issues': feedback_data.specific_issues,
                'feature_requests': feedback_data.feature_requests,
                'detailed_comments': feedback_data.detailed_comments,
                'contact_email': feedback_data.contact_email,
                'follow_up_consent': feedback_data.follow_up_consent,
                'device_info': self._get_device_info(),
                'language': language_code,
                'extra_metadata': {
                    'technical_level': feedback_data.context.technical_level,
                    'medical_background': feedback_data.context.medical_background,
                    'anonymous': additional_feedback.get('anonymous_feedback', False),
                    'submission_source': 'comprehensive_form'
                }
            }
            
            # 提交到数据库
            success = self.sheets_manager.log_feedback(db_data)
            
            if success:
                # 标记已提交
                st.session_state[f"feedback_submitted_{translation_id}"] = True
                
                # 显示成功消息
                self._show_submission_success(feedback_data)
                
                # 触发页面刷新显示感谢信息
                st.rerun()
                
                return feedback_data
            else:
                st.error("❌ 反馈提交失败，请稍后重试")
                return None
                
        except Exception as e:
            logger.error(f"Failed to process feedback submission: {e}")
            st.error("❌ 处理反馈时发生错误，请稍后重试")
            return None
    
    def _show_submission_success(self, feedback_data: FeedbackData):
        """显示提交成功信息"""
        st.balloons()
        
        avg_rating = sum(asdict(feedback_data.metrics).values()) / len(asdict(feedback_data.metrics))
        
        success_messages = {
            5: "🌟 完美评分！感谢您对 RadiAI.Care 的高度认可！",
            4: "⭐ 很高的评分！我们会继续保持和改进！",
            3: "👍 感谢您的中肯评价，我们会努力做得更好！",
            2: "📈 感谢您的宝贵意见，我们会重点改进相关问题！",
            1: "🔧 非常感谢您的耐心反馈，我们会认真对待每一个问题！"
        }
        
        rating_level = round(avg_rating)
        st.success(success_messages.get(rating_level, "感谢您的反馈！"))
        
        # 显示反馈摘要
        with st.expander("📋 您的反馈摘要", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**评分情况:**")
                metrics_dict = asdict(feedback_data.metrics)
                for key, value in metrics_dict.items():
                    label = self.FEEDBACK_CONFIG['satisfaction_metrics'][key]['label']
                    st.write(f"• {label}: {'⭐' * value} ({value}/5)")
            
            with col2:
                st.markdown("**用户信息:**")
                st.write(f"• 身份：{feedback_data.context.user_type}")
                st.write(f"• 用途：{feedback_data.context.primary_use_case}")
                st.write(f"• 频率：{feedback_data.context.usage_frequency}")
                
                if feedback_data.improvement_areas:
                    st.write(f"• 改进建议：{len(feedback_data.improvement_areas)} 项")
    
    def _get_device_info(self) -> str:
        """获取设备信息"""
        # 从session state获取设备信息
        device_info = {
            'type': st.session_state.get('device_type', 'unknown'),
            'browser': st.session_state.get('browser_info', 'unknown'),
            'screen': st.session_state.get('screen_info', 'unknown')
        }
        return json.dumps(device_info, ensure_ascii=False)
    
    def render_feedback_analytics_dashboard(self) -> None:
        """渲染反馈分析仪表板"""
        st.markdown("## 📊 反馈分析仪表板")
        
        try:
            # 获取分析数据
            analytics_data = self.sheets_manager.get_daily_analytics()
            
            if not analytics_data:
                st.info("📈 暂无足够数据显示分析结果")
                return
            
            # 显示关键指标
            self._render_key_metrics(analytics_data)
            
            # 显示满意度趋势
            self._render_satisfaction_trends()
            
            # 显示问题分布
            self._render_issue_distribution(analytics_data)
            
        except Exception as e:
            logger.error(f"Failed to render feedback analytics: {e}")
            st.error("分析数据加载失败")
    
    def _render_key_metrics(self, analytics_data: Dict[str, Any]):
        """渲染关键指标"""
        st.markdown("### 📈 关键指标")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "今日反馈数",
                analytics_data.get('feedback_count', 0),
                help="今日收到的反馈总数"
            )
        
        with col2:
            avg_satisfaction = analytics_data.get('avg_satisfaction', 0)
            st.metric(
                "平均满意度",
                f"{avg_satisfaction:.1f}/5",
                delta=f"{avg_satisfaction - 4.0:+.1f}",
                help="用户平均满意度评分"
            )
        
        with col3:
            quality_rating = analytics_data.get('avg_quality_rating', 0)
            st.metric(
                "翻译质量评分",
                f"{quality_rating:.1f}/5",
                delta=f"{quality_rating - 4.0:+.1f}",
                help="翻译质量平均评分"
            )
        
        with col4:
            response_rate = analytics_data.get('feedback_count', 0) / max(analytics_data.get('total_translations', 1), 1) * 100
            st.metric(
                "反馈率",
                f"{response_rate:.1f}%",
                help="用户反馈比例"
            )
    
    def _render_satisfaction_trends(self):
        """渲染满意度趋势图"""
        st.markdown("### 📊 满意度趋势")
        
        # 这里应该从数据库获取历史数据，现在用模拟数据
        dates = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
        satisfaction_scores = [4.1, 4.3, 4.2, 4.4, 4.5]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=satisfaction_scores,
            mode='lines+markers',
            name='满意度',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="用户满意度趋势",
            xaxis_title="日期",
            yaxis_title="满意度评分",
            yaxis=dict(range=[1, 5]),
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_issue_distribution(self, analytics_data: Dict[str, Any]):
        """渲染问题分布图"""
        st.markdown("### 🎯 常见问题分布")
        
        common_issues = analytics_data.get('common_issues', {})
        
        if common_issues:
            issues = list(common_issues.keys())[:10]  # 取前10个
            counts = [common_issues[issue] for issue in issues]
            
            fig = px.bar(
                x=counts,
                y=issues,
                orientation='h',
                title="用户反馈的常见问题",
                labels={'x': '反馈次数', 'y': '问题类型'}
            )
            
            fig.update_layout(
                template="plotly_white",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 暂无足够的问题反馈数据")

class SmartFeedbackIntegration:
    """智能反馈集成系统"""
    
    def __init__(self, sheets_manager, session_manager):
        self.sheets_manager = sheets_manager
        self.session_manager = session_manager
        self.feedback_collector = AdvancedFeedbackCollector(sheets_manager)
    
    def should_show_feedback_prompt(self, translation_id: str) -> bool:
        """判断是否应该显示反馈提示"""
        # 检查是否已经提交过反馈
        if st.session_state.get(f"feedback_submitted_{translation_id}", False):
            return False
        
        # 检查用户使用次数，首次用户或达到一定次数时提示
        usage_stats = self.session_manager.get_usage_stats()
        today_usage = usage_stats.get('today_usage', 0)
        
        # 策略：第一次使用后或每3次使用后提示反馈
        return today_usage == 1 or today_usage % 3 == 0
    
    def render_smart_feedback_flow(self, translation_id: str, user_id: str, 
                                  translation_quality_score: float = 0.0,
                                  processing_time_ms: int = 0) -> None:
        """渲染智能反馈流程"""
        
        # 根据翻译质量和处理时间智能调整反馈策略
        if translation_quality_score < 0.7 or processing_time_ms > 30000:
            # 质量较低或速度较慢时，重点收集改进意见
            self._render_improvement_focused_feedback(translation_id, user_id)
        else:
            # 正常情况下的标准反馈流程
            if self.should_show_feedback_prompt(translation_id):
                self.feedback_collector.render_comprehensive_feedback_form(
                    translation_id, user_id, st.session_state.get('language', 'zh_CN')
                )
    
    def _render_improvement_focused_feedback(self, translation_id: str, user_id: str):
        """渲染改进导向的反馈表单"""
        st.markdown("### 🔧 帮助我们改进")
        st.warning("我们注意到这次翻译可能没有达到最佳效果，您的反馈对我们很重要！")
        
        with st.form(f"quick_feedback_{translation_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                overall_rating = st.slider("整体体验", 1, 5, 3, key=f"quick_overall_{translation_id}")
                main_issue = st.selectbox(
                    "主要问题",
                    ["翻译不准确", "速度太慢", "格式问题", "界面问题", "其他"],
                    key=f"quick_issue_{translation_id}"
                )
            
            with col2:
                urgency = st.selectbox(
                    "问题严重程度",
                    ["轻微", "一般", "严重", "无法使用"],
                    key=f"quick_urgency_{translation_id}"
                )
                improvement_suggestion = st.text_area(
                    "改进建议",
                    placeholder="请简单描述问题和改进建议...",
                    key=f"quick_suggestion_{translation_id}"
                )
            
            submitted = st.form_submit_button("快速提交反馈", type="primary", use_container_width=True)
            
            if submitted:
                # 处理快速反馈
                quick_feedback_data = {
                    'translation_id': translation_id,
                    'user_id': user_id,
                    'overall_satisfaction': overall_rating,
                    'primary_issue': main_issue,
                    'urgency_level': urgency,
                    'improvement_suggestion': improvement_suggestion,
                    'feedback_type': 'quick_improvement',
                    'extra_metadata': {'trigger_reason': 'quality_concern'}
                }
                
                if self.sheets_manager.log_feedback(quick_feedback_data):
                    st.success("✅ 感谢您的反馈！我们会优先处理相关问题。")
                    st.session_state[f"feedback_submitted_{translation_id}"] = True
                else:
                    st.error("❌ 反馈提交失败，请稍后重试")
