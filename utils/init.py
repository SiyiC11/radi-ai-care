# utils/__init__.py
"""
RadiAI.Care 工具模塊
提供翻譯、文件處理、數據記錄等功能
"""

__version__ = "1.0.0"
__author__ = "RadiAI.Care Team"

# 導入主要函數，便於外部調用
try:
    from .prompt_template import (
        get_prompt,
        create_enhanced_disclaimer,
        get_processing_steps,
        get_error_messages,
        get_success_messages
    )
    
    # 導出所有可用函數
    __all__ = [
        'get_prompt',
        'create_enhanced_disclaimer', 
        'get_processing_steps',
        'get_error_messages',
        'get_success_messages'
    ]
    
except ImportError as e:
    # 如果導入失敗，記錄錯誤但不阻止模塊加載
    import logging
    logging.warning(f"部分 utils 模塊導入失敗: {e}")
    __all__ = []
