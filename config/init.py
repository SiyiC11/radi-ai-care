"""
RadiAI.Care 配置模塊
統一管理應用程序的所有配置信息
"""

__version__ = "1.0.0"
__author__ = "RadiAI.Care Team"

# 導入主要配置類
try:
    from .settings import (
        AppConfig,
        UIText,
        CSS_STYLES,
        GOOGLE_SHEETS_CONFIG
    )
    
    # 導出所有配置
    __all__ = [
        'AppConfig',
        'UIText', 
        'CSS_STYLES',
        'GOOGLE_SHEETS_CONFIG'
    ]
    
    # 創建默認配置實例
    app_config = AppConfig()
    ui_text = UIText()
    
    # 配置驗證
    def validate_config():
        """驗證配置完整性"""
        errors = []
        
        # 檢查必需的配置項
        if not hasattr(app_config, 'APP_TITLE'):
            errors.append("缺少 APP_TITLE 配置")
        
        if not hasattr(app_config, 'MEDICAL_KEYWORDS'):
            errors.append("缺少 MEDICAL_KEYWORDS 配置")
        
        if not ui_text.LANGUAGE_CONFIG:
            errors.append("缺少語言配置")
        
        return errors
    
    # 自動驗證配置
    config_errors = validate_config()
    if config_errors:
        import logging
        logger = logging.getLogger(__name__)
        for error in config_errors:
            logger.warning(f"配置警告: {error}")

except ImportError as e:
    import logging
    logging.error(f"配置模塊導入失敗: {e}")
    
    # 提供最小配置以避免應用崩潰
    class MinimalConfig:
        APP_TITLE = "RadiAI.Care"
        APP_VERSION = "unknown"
        MAX_FREE_TRANSLATIONS = 3
        SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'docx']
    
    app_config = MinimalConfig()
    __all__ = ['app_config']

# 配置常量
CONFIG_VERSION = "1.0.0"
LAST_UPDATED = "2024-12-19"

def get_config_info():
    """獲取配置信息摘要"""
    try:
        return {
            "config_version": CONFIG_VERSION,
            "app_version": getattr(app_config, 'APP_VERSION', 'unknown'),
            "last_updated": LAST_UPDATED,
            "supported_languages": list(ui_text.LANGUAGE_CONFIG.keys()) if hasattr(ui_text, 'LANGUAGE_CONFIG') else [],
            "max_translations": getattr(app_config, 'MAX_FREE_TRANSLATIONS', 3),
            "supported_file_types": getattr(app_config, 'SUPPORTED_FILE_TYPES', [])
        }
    except Exception as e:
        return {"error": str(e)}