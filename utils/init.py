"""
RadiAI.Care 工具模塊
提供翻譯、文件處理、會話管理等核心功能
"""

__version__ = "1.0.0"
__author__ = "RadiAI.Care Team"

# 導入核心工具類
try:
    from .session_manager import SessionManager
    from .file_handler import FileHandler
    from .translator import Translator, ContentValidator
    from .feedback_manager import FeedbackManager
    from .prompt_template import (
        get_prompt,
        create_enhanced_disclaimer,
        get_processing_steps,
        get_error_messages,
        get_success_messages,
        get_medical_terminology_guide,
        validate_prompt_response
    )
    
    # 導出所有工具類和函數
    __all__ = [
        # 核心類
        'SessionManager',
        'FileHandler', 
        'Translator',
        'ContentValidator',
        'FeedbackManager',
        
        # 提示詞函數
        'get_prompt',
        'create_enhanced_disclaimer',
        'get_processing_steps',
        'get_error_messages',
        'get_success_messages',
        'get_medical_terminology_guide',
        'validate_prompt_response',
        
        # 工廠函數
        'create_session_manager',
        'create_file_handler',
        'create_translator',
        'create_feedback_manager'
    ]
    
    # 工廠函數，用於創建工具實例
    def create_session_manager():
        """創建會話管理器實例"""
        return SessionManager()
    
    def create_file_handler():
        """創建文件處理器實例"""
        return FileHandler()
    
    def create_translator():
        """創建翻譯器實例"""
        return Translator()
    
    def create_feedback_manager():
        """創建回饋管理器實例"""
        return FeedbackManager()
    
    # 工具類註冊表（用於動態管理）
    TOOL_REGISTRY = {
        'session_manager': SessionManager,
        'file_handler': FileHandler,
        'translator': Translator,
        'content_validator': ContentValidator,
        'feedback_manager': FeedbackManager
    }
    
    def get_tool_class(tool_name: str):
        """根據名稱獲取工具類"""
        return TOOL_REGISTRY.get(tool_name)
    
    def list_available_tools():
        """列出所有可用的工具"""
        return list(TOOL_REGISTRY.keys())
    
    # 模塊初始化檢查
    def check_module_health():
        """檢查模塊健康狀態"""
        health_status = {
            'session_manager': False,
            'file_handler': False,
            'translator': False,
            'feedback_manager': False,
            'prompt_template': False
        }
        
        try:
            # 測試每個模塊是否可以正常實例化
            SessionManager()
            health_status['session_manager'] = True
        except Exception:
            pass
        
        try:
            FileHandler()
            health_status['file_handler'] = True
        except Exception:
            pass
        
        try:
            Translator()
            health_status['translator'] = True
        except Exception:
            pass
        
        try:
            FeedbackManager()
            health_status['feedback_manager'] = True
        except Exception:
            pass
        
        try:
            get_prompt('simplified_chinese')
            health_status['prompt_template'] = True
        except Exception:
            pass
        
        return health_status
    
    # 自動健康檢查
    _health_status = check_module_health()
    _failed_modules = [module for module, status in _health_status.items() if not status]
    
    if _failed_modules:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"以下模塊初始化失敗: {', '.join(_failed_modules)}")

except ImportError as e:
    import logging
    logging.error(f"工具模塊導入失敗: {e}")
    
    # 提供最小工具集以避免應用崩潰
    class MinimalSessionManager:
        def init_session_state(self):
            pass
    
    class MinimalFileHandler:
        def extract_text(self, file):
            return None, {"error": "文件處理不可用"}
    
    def get_prompt(language):
        return "工具模塊不可用，請檢查安裝。"
    
    # 最小導出
    __all__ = ['MinimalSessionManager', 'MinimalFileHandler', 'get_prompt']

# 版本兼容性檢查
def check_compatibility():
    """檢查模塊間的兼容性"""
    try:
        import sys
        python_version = sys.version_info
        
        if python_version < (3, 8):
            return False, "需要 Python 3.8 或更高版本"
        
        # 檢查必需的依賴
        required_packages = [
            'streamlit', 'openai', 'fitz', 'docx', 
            'gspread', 'oauth2client', 'pytz'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return False, f"缺少依賴包: {', '.join(missing_packages)}"
        
        return True, "所有依賴檢查通過"
        
    except Exception as e:
        return False, f"兼容性檢查失敗: {str(e)}"

# 工具模塊元信息
MODULE_INFO = {
    "name": "RadiAI.Care Utils",
    "version": __version__,
    "author": __author__,
    "description": "RadiAI.Care 核心工具模塊",
    "components": [
        "SessionManager - 會話狀態管理",
        "FileHandler - 文件處理和文本提取", 
        "Translator - AI翻譯引擎",
        "ContentValidator - 內容驗證器",
        "FeedbackManager - 用戶回饋管理",
        "PromptTemplate - 提示詞模板系統"
    ]
}

def get_module_info():
    """獲取模塊信息"""
    return MODULE_INFO

# 調試和診斷函數
def diagnose_utils():
    """診斷工具模塊狀態"""
    import sys
    import platform
    
    diagnosis = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "module_version": __version__,
        "health_status": check_module_health() if 'check_module_health' in globals() else {},
        "compatibility": check_compatibility(),
        "available_tools": list_available_tools() if 'list_available_tools' in globals() else []
    }
    
    return diagnosis