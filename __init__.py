"""
RadiAI.Care - 智能醫療報告翻譯助手
為澳洲華人社區打造的專業醫學報告翻譯服務

主要功能：
- 英文放射科報告的中文翻譯
- 醫學術語的通俗化解釋
- 專業的醫療科普服務
- 完整的用戶回饋系統
"""

__version__ = "4.2.0"
__author__ = "RadiAI.Care Team"
__email__ = "support@radiai.care"
__license__ = "MIT"
__description__ = "RadiAI.Care - 智能醫療報告翻譯助手"

# 應用元信息
APP_METADATA = {
    "name": "RadiAI.Care",
    "version": __version__,
    "author": __author__,
    "description": __description__,
    "license": __license__,
    "target_audience": "澳洲華人社區",
    "primary_function": "醫學報告翻譯",
    "supported_languages": ["繁體中文", "简体中文"],
    "supported_formats": ["PDF", "TXT", "DOCX"],
    "ai_model": "GPT-4o",
    "framework": "Streamlit"
}

# 導入核心模塊（可選，用於包級別的訪問）
try:
    from config import app_config, ui_text
    from utils import (
        SessionManager, FileHandler, Translator, 
        FeedbackManager, get_prompt
    )
    from components import UIComponents, create_ui_components
    
    # 提供便捷的頂級導入
    __all__ = [
        # 配置
        'app_config',
        'ui_text',
        
        # 核心工具
        'SessionManager',
        'FileHandler', 
        'Translator',
        'FeedbackManager',
        
        # UI 組件
        'UIComponents',
        'create_ui_components',
        
        # 提示詞
        'get_prompt',
        
        # 元信息
        'APP_METADATA',
        'get_app_info',
        'check_system_health'
    ]
    
    def get_app_info():
        """獲取應用程序信息"""
        return APP_METADATA.copy()
    
    def check_system_health():
        """檢查系統健康狀態"""
        health_status = {
            "app_version": __version__,
            "modules": {},
            "overall_status": "healthy"
        }
        
        # 檢查各個模塊
        try:
            from config import validate_config
            config_errors = validate_config()
            health_status["modules"]["config"] = {
                "status": "healthy" if not config_errors else "warning",
                "errors": config_errors
            }
        except Exception as e:
            health_status["modules"]["config"] = {
                "status": "error",
                "error": str(e)
            }
        
        try:
            from utils import check_module_health
            utils_health = check_module_health()
            failed_utils = [k for k, v in utils_health.items() if not v]
            health_status["modules"]["utils"] = {
                "status": "healthy" if not failed_utils else "warning",
                "failed_components": failed_utils
            }
        except Exception as e:
            health_status["modules"]["utils"] = {
                "status": "error", 
                "error": str(e)
            }
        
        try:
            from components import validate_ui_components
            ui_validation = validate_ui_components()
            health_status["modules"]["components"] = {
                "status": "healthy" if ui_validation["is_valid"] else "warning",
                "missing_methods": ui_validation.get("missing_methods", [])
            }
        except Exception as e:
            health_status["modules"]["components"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 確定整體狀態
        module_statuses = [module["status"] for module in health_status["modules"].values()]
        if "error" in module_statuses:
            health_status["overall_status"] = "error"
        elif "warning" in module_statuses:
            health_status["overall_status"] = "warning"
        
        return health_status

except ImportError as e:
    import logging
    logging.warning(f"部分模塊導入失敗，僅提供基本功能: {e}")
    
    # 最小導出
    __all__ = ['APP_METADATA', 'get_app_info']
    
    def get_app_info():
        return APP_METADATA.copy()

# 系統要求檢查
def check_system_requirements():
    """檢查系統要求"""
    import sys
    import platform
    
    requirements = {
        "python_version": {
            "required": "3.8+",
            "current": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "satisfied": sys.version_info >= (3, 8)
        },
        "platform": {
            "current": platform.system(),
            "supported": ["Windows", "Darwin", "Linux"],
            "satisfied": platform.system() in ["Windows", "Darwin", "Linux"]
        }
    }
    
    # 檢查關鍵依賴
    critical_dependencies = [
        "streamlit", "openai", "PyMuPDF", "python-docx", 
        "gspread", "oauth2client", "pytz"
    ]
    
    requirements["dependencies"] = {}
    for dep in critical_dependencies:
        try:
            __import__(dep)
            requirements["dependencies"][dep] = {
                "status": "installed",
                "satisfied": True
            }
        except ImportError:
            requirements["dependencies"][dep] = {
                "status": "missing",
                "satisfied": False
            }
    
    # 整體滿足度
    all_satisfied = (
        requirements["python_version"]["satisfied"] and
        requirements["platform"]["satisfied"] and
        all(dep["satisfied"] for dep in requirements["dependencies"].values())
    )
    
    requirements["overall_satisfied"] = all_satisfied
    
    return requirements

# 環境變量檢查
def check_environment_variables():
    """檢查必需的環境變量"""
    import os
    
    required_env_vars = {
        "OPENAI_API_KEY": {
            "required": True,
            "description": "OpenAI API 密鑰",
            "present": bool(os.getenv("OPENAI_API_KEY"))
        },
        "GOOGLE_SHEET_SECRET_B64": {
            "required": True, 
            "description": "Google Sheets 服務帳戶密鑰（Base64編碼）",
            "present": bool(os.getenv("GOOGLE_SHEET_SECRET_B64"))
        }
    }
    
    missing_vars = [
        var for var, info in required_env_vars.items() 
        if info["required"] and not info["present"]
    ]
    
    return {
        "variables": required_env_vars,
        "missing_required": missing_vars,
        "all_present": len(missing_vars) == 0
    }

# 完整的應用診斷
def run_full_diagnostics():
    """運行完整的應用診斷"""
    diagnostics = {
        "app_info": get_app_info(),
        "system_requirements": check_system_requirements(),
        "environment_variables": check_environment_variables(),
        "timestamp": None
    }
    
    # 添加系統健康檢查（如果可用）
    if 'check_system_health' in globals():
        diagnostics["system_health"] = check_system_health()
    
    # 添加時間戳
    from datetime import datetime
    diagnostics["timestamp"] = datetime.now().isoformat()
    
    return diagnostics

# 將診斷函數添加到導出列表
if '__all__' in globals():
    __all__.extend([
        'check_system_