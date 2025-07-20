"""
RadiAI.Care UI 組件模塊
統一管理所有用戶界面組件和渲染邏輯
"""

__version__ = "1.0.0"
__author__ = "RadiAI.Care Team"

# 導入 UI 組件
try:
    from .ui_components import UIComponents
    
    # 導出 UI 組件
    __all__ = [
        'UIComponents',
        'create_ui_components',
        'get_component_registry',
        'validate_ui_components'
    ]
    
    # UI 組件工廠函數
    def create_ui_components():
        """創建 UI 組件實例"""
        return UIComponents()
    
    # UI 組件註冊表
    COMPONENT_REGISTRY = {
        'header': 'render_header',
        'language_selection': 'render_language_selection', 
        'disclaimer': 'render_disclaimer',
        'usage_tracker': 'render_usage_tracker',
        'input_section': 'render_input_section',
        'translate_button': 'render_translate_button',
        'translation_result': 'render_translation_result',
        'completion_status': 'render_completion_status',
        'footer': 'render_footer',
        'version_info': 'render_version_info',
        'quota_exceeded': 'render_quota_exceeded'
    }
    
    def get_component_registry():
        """獲取組件註冊表"""
        return COMPONENT_REGISTRY.copy()
    
    def validate_ui_components():
        """驗證 UI 組件完整性"""
        ui = UIComponents()
        missing_methods = []
        
        for component_name, method_name in COMPONENT_REGISTRY.items():
            if not hasattr(ui, method_name):
                missing_methods.append(f"{component_name}: {method_name}")
        
        return {
            "is_valid": len(missing_methods) == 0,
            "missing_methods": missing_methods,
            "total_components": len(COMPONENT_REGISTRY),
            "available_components": len(COMPONENT_REGISTRY) - len(missing_methods)
        }
    
    # UI 主題和樣式管理
    class ThemeManager:
        """UI 主題管理器"""
        
        THEMES = {
            'default': {
                'primary_color': '#0d74b8',
                'secondary_color': '#29a3d7', 
                'background_gradient': 'linear-gradient(135deg, #e0f7fa 0%, #ffffff 55%, #f2fbfe 100%)',
                'card_background': 'rgba(255,255,255,0.95)',
                'text_color': '#256084'
            },
            'dark': {
                'primary_color': '#1e88e5',
                'secondary_color': '#42a5f5',
                'background_gradient': 'linear-gradient(135deg, #263238 0%, #37474f 55%, #455a64 100%)',
                'card_background': 'rgba(55,71,79,0.95)',
                'text_color': '#e1f5fe'
            },
            'high_contrast': {
                'primary_color': '#000000',
                'secondary_color': '#333333',
                'background_gradient': 'linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%)',
                'card_background': '#ffffff',
                'text_color': '#000000'
            }
        }
        
        @classmethod
        def get_theme(cls, theme_name='default'):
            """獲取主題配置"""
            return cls.THEMES.get(theme_name, cls.THEMES['default'])
        
        @classmethod
        def list_themes(cls):
            """列出所有可用主題"""
            return list(cls.THEMES.keys())
    
    # 組件狀態管理
    class ComponentStateManager:
        """組件狀態管理器"""
        
        def __init__(self):
            self.component_states = {}
        
        def set_component_state(self, component_name: str, state: dict):
            """設置組件狀態"""
            self.component_states[component_name] = state
        
        def get_component_state(self, component_name: str, default=None):
            """獲取組件狀態"""
            return self.component_states.get(component_name, default or {})
        
        def clear_component_state(self, component_name: str):
            """清除組件狀態"""
            if component_name in self.component_states:
                del self.component_states[component_name]
        
        def clear_all_states(self):
            """清除所有組件狀態"""
            self.component_states.clear()
    
    # 創建全局實例
    theme_manager = ThemeManager()
    component_state_manager = ComponentStateManager()
    
    # 添加到導出列表
    __all__.extend([
        'ThemeManager', 
        'ComponentStateManager',
        'theme_manager',
        'component_state_manager'
    ])
    
    # 組件性能監控
    class ComponentPerformanceMonitor:
        """組件性能監控器"""
        
        def __init__(self):
            self.render_times = {}
            self.render_counts = {}
        
        def start_timing(self, component_name: str):
            """開始計時"""
            import time
            self.render_times[component_name] = time.time()
        
        def end_timing(self, component_name: str):
            """結束計時並記錄"""
            import time
            if component_name in self.render_times:
                elapsed = time.time() - self.render_times[component_name]
                
                if component_name not in self.render_counts:
                    self.render_counts[component_name] = {
                        'total_time': 0,
                        'count': 0,
                        'avg_time': 0
                    }
                
                stats = self.render_counts[component_name]
                stats['total_time'] += elapsed
                stats['count'] += 1
                stats['avg_time'] = stats['total_time'] / stats['count']
                
                del self.render_times[component_name]
                return elapsed
            return 0
        
        def get_performance_stats(self):
            """獲取性能統計"""
            return self.render_counts.copy()
        
        def reset_stats(self):
            """重置統計數據"""
            self.render_times.clear()
            self.render_counts.clear()
    
    # 創建性能監控實例
    performance_monitor = ComponentPerformanceMonitor()
    __all__.append('performance_monitor')
    
    # 組件初始化檢查
    _validation_result = validate_ui_components()
    if not _validation_result['is_valid']:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"UI 組件驗證失敗: {_validation_result['missing_methods']}")

except ImportError as e:
    import logging
    logging.error(f"UI 組件模塊導入失敗: {e}")
    
    # 提供最小 UI 組件以避免應用崩潰
    class MinimalUIComponents:
        """最小 UI 組件"""
        
        def render_header(self, lang):
            import streamlit as st
            st.title("RadiAI.Care")
        
        def render_language_selection(self, lang):
            import streamlit as st
            st.write("語言選擇不可用")
        
        def render_disclaimer(self, lang):
            import streamlit as st
            st.warning("重要：本工具僅提供翻譯服務，不提供醫療建議")
    
    def create_ui_components():
        return MinimalUIComponents()
    
    __all__ = ['MinimalUIComponents', 'create_ui_components']

# 組件模塊元信息
COMPONENT_MODULE_INFO = {
    "name": "RadiAI.Care UI Components",
    "version": __version__,
    "author": __author__,
    "description": "RadiAI.Care 用戶界面組件系統",
    "features": [
        "響應式 UI 組件",
        "多主題支持",
        "組件狀態管理",
        "性能監控",
        "組件驗證"
    ],
    "components": list(COMPONENT_REGISTRY.keys()) if 'COMPONENT_REGISTRY' in globals() else []
}

def get_component_module_info():
    """獲取組件模塊信息"""
    return COMPONENT_MODULE_INFO

# 診斷函數
def diagnose_components():
    """診斷組件模塊狀態"""
    diagnosis = {
        "module_info": get_component_module_info(),
        "validation_result": validate_ui_components() if 'validate_ui_components' in globals() else {},
        "available_themes": ThemeManager.list_themes() if 'ThemeManager' in globals() else [],
        "performance_stats": performance_monitor.get_performance_stats() if 'performance_monitor' in globals() else {}
    }
    
    return diagnosis

# 組件工具函數
def render_component_safely(component_func, *args, **kwargs):
    """安全渲染組件（帶錯誤處理）"""
    try:
        if 'performance_monitor' in globals():
            component_name = getattr(component_func, '__name__', 'unknown')
            performance_monitor.start_timing(component_name)
            
        result = component_func(*args, **kwargs)
        
        if 'performance_monitor' in globals():
            performance_monitor.end_timing(component_name)
            
        return result
        
    except Exception as e:
        import logging
        import streamlit as st
        
        logger = logging.getLogger(__name__)
        logger.error(f"組件渲染失敗: {e}")
        
        st.error(f"組件渲染出錯: {str(e)}")
        return None

# 添加到導出列表
if 'render_component_safely' not in globals().get('__all__', []):
    __all__ = globals().get('__all__', []) + ['render_component_safely']
