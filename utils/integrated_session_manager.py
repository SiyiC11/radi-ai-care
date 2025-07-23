"""
RadiAI.Care - 整合的会话和反馈管理系统
将使用量限制、倒计时功能与反馈系统深度整合
"""

import streamlit as st
import hashlib
import time
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional, List
import pytz
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class UsageSession:
    """使用会话数据类"""
    session_id: str
    user_id: str
    device_id: str
    start_time: datetime
    daily_count: int = 0
    session_translations: List[str] = None
    last_activity: datetime = None
    total_processing_time: int = 0
    avg_satisfaction: float = 0.0
    feedback_count: int = 0
    
    def __post_init__(self):
        if self.session_translations is None:
            self.session_translations = []
        if self.last_activity is None:
            self.last_activity = self.start_time

@dataclass
class QuotaStatus:
    """配额状态数据类"""
    current_usage: int
    daily_limit: int
    remaining: int
    is_locked: bool
    reset_time: datetime
    usage_efficiency: float  # 基于反馈的使用效率评分
    satisfaction_bonus: int = 0  # 基于满意度的额外配额

class IntegratedSessionManager:
    """整合的会话管理器"""
    
    def __init__(self, sheets_manager):
        self.sheets_manager = sheets_manager
        self.sydney_tz = pytz.timezone('Australia/Sydney')
        self.base_daily_limit = 3
        self.session_cache = {}
        
        # 配额策略配置
        self.quota_policies = {
            'satisfaction_bonus': {
                'high_satisfaction': 1,    # 满意度 >= 4.5 额外 1 次
                'medium_satisfaction': 0,  # 满意度 3.5-4.4 无额外
                'low_satisfaction': 0      # 满意度 < 3.5 无额外
            },
            'feedback_contribution': {
                'detailed_feedback': 1,    # 提供详细反馈额外 1 次
                'quick_feedback': 0        # 快速反馈无额外
            },
            'usage_efficiency': {
                'high_efficiency': 1,      # 高效使用（少错误重试）额外 1 次
                'normal_efficiency': 0     # 正常使用无额外
            }
        }
    
    def init_session_state(self):
        """初始化会话状态"""
        # 基础会话信息
        defaults = {
            "language": "简体中文",
            "input_method": "text",
            "user_session_id": str(uuid.uuid4())[:8],
            "app_start_time": time.time(),
            "device_id": None,
            "permanent_user_id": None,
            "current_usage_session": None,
            "quota_status": None,
            "session_initialized": False,
            "feedback_history": [],
            "usage_efficiency_score": 1.0,
            "satisfaction_history": [],
            "bonus_quota_earned": 0,
            "last_sync_time": 0
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # 生成或获取设备和用户ID
        self._setup_user_identity()
        
        # 初始化当前会话
        self._init_current_session()
        
        # 更新配额状态
        self._update_quota_status()
        
        st.session_state.session_initialized = True
    
    def _setup_user_identity(self):
        """设置用户身份标识"""
        if not st.session_state.device_id:
            raw_data = f"{st.session_state.user_session_id}_{self._get_sydney_today()}"
            device_hash = hashlib.md5(raw_data.encode()).hexdigest()[:12]
            st.session_state.device_id = f"dev_{device_hash}"
        
        if not st.session_state.permanent_user_id:
            today = self._get_sydney_today()
            raw_data = f"{st.session_state.device_id}_{today}"
            user_hash = hashlib.sha256(raw_data.encode()).hexdigest()[:16]
            st.session_state.permanent_user_id = f"user_{user_hash}"
    
    def _init_current_session(self):
        """初始化当前使用会话"""
        if not st.session_state.current_usage_session:
            session = UsageSession(
                session_id=st.session_state.user_session_id,
                user_id=st.session_state.permanent_user_id,
                device_id=st.session_state.device_id,
                start_time=datetime.now(self.sydney_tz),
                daily_count=self._get_current_daily_count(),
                session_translations=[],
                last_activity=datetime.now(self.sydney_tz)
            )
            st.session_state.current_usage_session = session
        else:
            # 更新现有会话的每日计数
            session = st.session_state.current_usage_session
            session.daily_count = self._get_current_daily_count()
    
    def _get_current_daily_count(self) -> int:
        """从数据库获取当前每日使用计数"""
        try:
            today = self._get_sydney_today()
            user_id = st.session_state.permanent_user_id
            count = self.sheets_manager.get_user_usage_count(user_id, today)
            return count
        except Exception as e:
            logger.error(f"Failed to get daily count: {e}")
            return st.session_state.get('local_daily_count', 0)
    
    def _update_quota_status(self):
        """更新配额状态"""
        session = st.session_state.current_usage_session
        current_usage = session.daily_count if session else 0
        
        # 计算动态每日限额
        dynamic_limit = self._calculate_dynamic_daily_limit()
        
        # 计算下次重置时间
        reset_time = self._get_next_reset_time()
        
        # 计算使用效率
        efficiency = self._calculate_usage_efficiency()
        
        quota_status = QuotaStatus(
            current_usage=current_usage,
            daily_limit=dynamic_limit,
            remaining=max(0, dynamic_limit - current_usage),
            is_locked=current_usage >= dynamic_limit,
            reset_time=reset_time,
            usage_efficiency=efficiency,
            satisfaction_bonus=st.session_state.get('bonus_quota_earned', 0)
        )
        
        st.session_state.quota_status = quota_status
    
    def _calculate_dynamic_daily_limit(self) -> int:
        """计算动态每日限额"""
        base_limit = self.base_daily_limit
        bonus_quota = 0
        
        # 基于满意度的奖励配额
        satisfaction_history = st.session_state.get('satisfaction_history', [])
        if satisfaction_history:
            avg_satisfaction = sum(satisfaction_history) / len(satisfaction_history)
            if avg_satisfaction >= 4.5:
                bonus_quota += self.quota_policies['satisfaction_bonus']['high_satisfaction']
            elif avg_satisfaction >= 3.5:
                bonus_quota += self.quota_policies['satisfaction_bonus']['medium_satisfaction']
        
        # 基于反馈贡献的奖励配额
        feedback_history = st.session_state.get('feedback_history', [])
        detailed_feedback_count = len([f for f in feedback_history if f.get('type') == 'detailed'])
        if detailed_feedback_count >= 1:  # 至少提供过1次详细反馈
            bonus_quota += self.quota_policies['feedback_contribution']['detailed_feedback']
        
        # 基于使用效率的奖励配额
        efficiency_score = st.session_state.get('usage_efficiency_score', 1.0)
        if efficiency_score >= 0.9:  # 高效使用（少重试、少错误）
            bonus_quota += self.quota_policies['usage_efficiency']['high_efficiency']
        
        st.session_state.bonus_quota_earned = bonus_quota
        return base_limit + bonus_quota
    
    def _calculate_usage_efficiency(self) -> float:
        """计算使用效率评分"""
        session = st.session_state.current_usage_session
        if not session or not session.session_translations:
            return 1.0
        
        # 基于成功率和反馈质量计算效率
        total_translations = len(session.session_translations)
        avg_satisfaction = session.avg_satisfaction or 0
        
        # 效率评分 = 基础分 + 满意度奖励 - 重试惩罚
        base_score = 0.7
        satisfaction_bonus = (avg_satisfaction / 5) * 0.3
        
        efficiency = min(1.0, base_score + satisfaction_bonus)
        return efficiency
    
    def _get_sydney_today(self) -> str:
        """获取悉尼时区今日日期"""
        return datetime.now(self.sydney_tz).strftime('%Y-%m-%d')
    
    def _get_next_reset_time(self) -> datetime:
        """获取下次配额重置时间"""
        sydney_now = datetime.now(self.sydney_tz)
        next_reset = sydney_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    def can_use_translation(self) -> Tuple[bool, str]:
        """检查是否可以使用翻译服务"""
        self._update_quota_status()
        quota_status = st.session_state.quota_status
        
        if quota_status.is_locked:
            remaining_time = self._get_remaining_time_text(quota_status.reset_time)
            message = f"今日配额已用完 ({quota_status.current_usage}/{quota_status.daily_limit})。{remaining_time}"
            
            # 如果有奖励配额，提示如何获得
            if quota_status.satisfaction_bonus == 0:
                message += "\n💡 提示：提供详细反馈可获得额外配额！"
            
            return False, message
        
        return True, f"今日还可使用 {quota_status.remaining} 次（含奖励配额 {quota_status.satisfaction_bonus} 次）"
    
    def _get_remaining_time_text(self, reset_time: datetime) -> str:
        """获取剩余时间文本"""
        now = datetime.now(self.sydney_tz)
        remaining = reset_time - now
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"配额将在 {hours} 小时 {minutes} 分钟后重置"
        else:
            return f"配额将在 {minutes} 分钟后重置"
    
    def record_translation_usage(self, translation_id: str, text_hash: str, 
                                processing_time_ms: int = 0, file_type: str = "text",
                                content_length: int = 0) -> bool:
        """记录翻译使用"""
        try:
            session = st.session_state.current_usage_session
            
            # 更新会话信息
            session.session_translations.append(translation_id)
            session.last_activity = datetime.now(self.sydney_tz)
            session.total_processing_time += processing_time_ms
            session.daily_count += 1
            
            # 记录到数据库
            usage_data = {
                'user_id': session.user_id,
                'session_id': session.session_id,
                'translation_id': translation_id,
                'daily_count': session.daily_count,
                'session_count': len(session.session_translations),
                'processing_time_ms': processing_time_ms,
                'file_type': file_type,
                'content_length': content_length,
                'status': 'success',
                'language': st.session_state.get('language', 'zh_CN'),
                'device_info': session.device_id,
                'ip_hash': self._get_ip_hash(),
                'user_agent': self._get_user_agent(),
                'extra_data': {
                    'text_hash': text_hash,
                    'efficiency_score': st.session_state.get('usage_efficiency_score', 1.0),
                    'bonus_quota': st.session_state.get('bonus_quota_earned', 0)
                }
            }
            
            success = self.sheets_manager.log_usage(usage_data)
            
            if success:
                # 更新本地状态
                self._update_quota_status()
                logger.info(f"Successfully recorded translation usage: {translation_id}")
                return True
            else:
                # 失败时回滚本地状态
                session.daily_count -= 1
                session.session_translations.pop()
                logger.error(f"Failed to record translation usage: {translation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error recording translation usage: {e}")
            return False
    
    def record_feedback_and_update_quota(self, feedback_data: Dict[str, Any]) -> bool:
        """记录反馈并更新配额状态"""
        try:
            # 提取满意度评分
            overall_satisfaction = feedback_data.get('overall_satisfaction', 0)
            feedback_type = feedback_data.get('feedback_type', 'standard')
            
            # 更新满意度历史
            satisfaction_history = st.session_state.get('satisfaction_history', [])
            satisfaction_history.append(overall_satisfaction)
            st.session_state.satisfaction_history = satisfaction_history[-10:]  # 保留最近10次
            
            # 更新反馈历史
            feedback_history = st.session_state.get('feedback_history', [])
            feedback_summary = {
                'timestamp': datetime.now().isoformat(),
                'translation_id': feedback_data.get('translation_id', ''),
                'satisfaction': overall_satisfaction,
                'type': 'detailed' if len(feedback_data.get('detailed_comments', '')) > 50 else 'simple',
                'has_improvement_suggestions': len(feedback_data.get('improvement_areas', [])) > 0
            }
            feedback_history.append(feedback_summary)
            st.session_state.feedback_history = feedback_history[-20:]  # 保留最近20次
            
            # 更新会话的平均满意度
            session = st.session_state.current_usage_session
            if session:
                session.feedback_count += 1
                # 计算会话平均满意度
                session_feedbacks = [f['satisfaction'] for f in feedback_history if f.get('translation_id') in session.session_translations]
                if session_feedbacks:
                    session.avg_satisfaction = sum(session_feedbacks) / len(session_feedbacks)
            
            # 记录到数据库
            success = self.sheets_manager.log_feedback(feedback_data)
            
            if success:
                # 重新计算配额状态（可能获得奖励配额）
                old_limit = st.session_state.quota_status.daily_limit if st.session_state.quota_status else self.base_daily_limit
                self._update_quota_status()
                new_limit = st.session_state.quota_status.daily_limit
                
                # 如果获得了额外配额，通知用户
                if new_limit > old_limit:
                    bonus_earned = new_limit - old_limit
                    st.success(f"🎉 感谢您的反馈！您获得了 {bonus_earned} 次额外翻译机会！")
                    st.balloons()
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error recording feedback and updating quota: {e}")
            return False
    
    def get_enhanced_usage_stats(self) -> Dict[str, Any]:
        """获取增强的使用统计信息"""
        quota_status = st.session_state.quota_status
        session = st.session_state.current_usage_session
        
        if not quota_status or not session:
            return {}
        
        # 计算时间相关信息
        reset_time_info = self._get_reset_time_details(quota_status.reset_time)
        
        # 计算效率和满意度信息
        satisfaction_history = st.session_state.get('satisfaction_history', [])
        avg_satisfaction = sum(satisfaction_history) / len(satisfaction_history) if satisfaction_history else 0
        
        return {
            # 基础配额信息
            'today_usage': quota_status.current_usage,
            'remaining': quota_status.remaining,
            'daily_limit': quota_status.daily_limit,
            'base_limit': self.base_daily_limit,
            'bonus_quota': quota_status.satisfaction_bonus,
            'is_locked': quota_status.is_locked,
            
            # 用户身份信息
            'user_id': session.user_id[:8] + "****",
            'device_id': session.device_id,
            'session_id': session.session_id,
            
            # 时间信息
            'sydney_date': self._get_sydney_today(),
            'reset_time_hours': reset_time_info['hours'],
            'reset_time_minutes': reset_time_info['minutes'],
            'reset_time_text': reset_time_info['text'],
            'reset_timestamp': quota_status.reset_time.timestamp(),
            
            # 性能和满意度信息
            'avg_satisfaction': round(avg_satisfaction, 1),
            'usage_efficiency': quota_status.usage_efficiency,
            'total_processing_time': session.total_processing_time,
            'session_translation_count': len(session.session_translations),
            'feedback_count': session.feedback_count,
            
            # 奖励机制信息
            'quota_sources': {
                'base': self.base_daily_limit,
                'satisfaction_bonus': self._get_satisfaction_bonus(),
                'feedback_bonus': self._get_feedback_bonus(),
                'efficiency_bonus': self._get_efficiency_bonus()
            },
            
            # 系统状态
            'server_available': self.sheets_manager is not None,
            'last_sync': st.session_state.get('last_sync_time', 0),
            'data_source': 'integrated_system'
        }
    
    def _get_reset_time_details(self, reset_time: datetime) -> Dict[str, Any]:
        """获取重置时间详情"""
        now = datetime.now(self.sydney_tz)
        remaining = reset_time - now
        
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            text = f"{hours} 小时 {minutes} 分钟"
        else:
            text = f"{minutes} 分钟"
        
        return {
            'hours': hours,
            'minutes': minutes,
            'total_seconds': total_seconds,
            'text': text
        }
    
    def _get_satisfaction_bonus(self) -> int:
        """获取满意度奖励配额"""
        satisfaction_history = st.session_state.get('satisfaction_history', [])
        if not satisfaction_history:
            return 0
        
        avg_satisfaction = sum(satisfaction_history) / len(satisfaction_history)
        if avg_satisfaction >= 4.5:
            return self.quota_policies['satisfaction_bonus']['high_satisfaction']
        return 0
    
    def _get_feedback_bonus(self) -> int:
        """获取反馈奖励配额"""
        feedback_history = st.session_state.get('feedback_history', [])
        detailed_count = len([f for f in feedback_history if f.get('type') == 'detailed'])
        if detailed_count >= 1:
            return self.quota_policies['feedback_contribution']['detailed_feedback']
        return 0
    
    def _get_efficiency_bonus(self) -> int:
        """获取效率奖励配额"""
        efficiency_score = st.session_state.get('usage_efficiency_score', 1.0)
        if efficiency_score >= 0.9:
            return self.quota_policies['usage_efficiency']['high_efficiency']
        return 0
    
    def _get_ip_hash(self) -> str:
        """获取IP地址哈希（隐私保护）"""
        # 在实际部署中，应该从请求头获取真实IP
        # 这里使用会话ID作为替代
        return hashlib.md5(st.session_state.user_session_id.encode()).hexdigest()[:8]
    
    def _get_user_agent(self) -> str:
        """获取用户代理信息"""
        # 在实际部署中，应该从请求头获取
        return "Streamlit/Unknown"
    
    def restore_usage_on_failure(self, translation_id: str):
        """翻译失败时恢复使用次数"""
        try:
            session = st.session_state.current_usage_session
            if session and translation_id in session.session_translations:
                session.session_translations.remove(translation_id)
                session.daily_count = max(0, session.daily_count - 1)
                self._update_quota_status()
                logger.info(f"Restored usage for failed translation: {translation_id}")
        except Exception as e:
            logger.error(f"Error restoring usage: {e}")
    
    def get_quota_unlock_suggestions(self) -> List[Dict[str, Any]]:
        """获取解锁配额的建议"""
        suggestions = []
        
        # 检查满意度奖励
        satisfaction_history = st.session_state.get('satisfaction_history', [])
        if not satisfaction_history or sum(satisfaction_history) / len(satisfaction_history) < 4.5:
            suggestions.append({
                'type': 'satisfaction',
                'title': '提供高满意度反馈',
                'description': '平均满意度达到 4.5/5 可获得 1 次额外配额',
                'action': '在下次使用后给出高分评价',
                'potential_bonus': 1
            })
        
        # 检查详细反馈奖励
        feedback_history = st.session_state.get('feedback_history', [])
        detailed_feedback_count = len([f for f in feedback_history if f.get('type') == 'detailed'])
        if detailed_feedback_count == 0:
            suggestions.append({
                'type': 'detailed_feedback',
                'title': '提供详细反馈',
                'description': '提供详细的使用反馈和改进建议可获得额外配额',
                'action': '下次翻译后填写完整的反馈表单',
                'potential_bonus': 1
            })
        
        # 检查使用效率
        efficiency_score = st.session_state.get('usage_efficiency_score', 1.0)
        if efficiency_score < 0.9:
            suggestions.append({
                'type': 'efficiency',
                'title': '提高使用效率',
                'description': '减少重试次数和错误操作可获得效率奖励',
                'action': '仔细检查输入内容，避免重复翻译',
                'potential_bonus': 1
            })
        
        return suggestions
    
    def generate_text_hash(self, text: str) -> str:
        """生成文本哈希值"""
        normalized = ' '.join(text.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
