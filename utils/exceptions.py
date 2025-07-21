"""
RadiAI.Care 錯誤分類系統
提供結構化的異常處理和錯誤分類
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RadiAIException(Exception):
    """RadiAI.Care 基礎異常類"""
    
    error_code: str = "UNKNOWN_ERROR"
    user_message: str = "發生未知錯誤"
    http_status: int = 500
    should_log: bool = True
    
    def __init__(self, 
                 message: Optional[str] = None,
                 user_message: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message or self.__class__.__name__
        self.user_message = user_message or self.__class__.user_message
        self.details = details or {}
        
        super().__init__(self.message)
        
        if self.should_log:
            logger.error(f"{self.error_code}: {self.message}", extra={"details": self.details})
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式（用於API響應）"""
        return {
            "error_code": self.error_code,
            "message": self.user_message,
            "details": self.details
        }


# 輸入驗證相關異常
class ValidationException(RadiAIException):
    """驗證異常基類"""
    error_code = "VALIDATION_ERROR"
    user_message = "輸入驗證失敗"
    http_status = 400


class EmptyInputException(ValidationException):
    """空輸入異常"""
    error_code = "EMPTY_INPUT"
    user_message = "請輸入報告內容或上傳文件"


class InvalidReportException(ValidationException):
    """無效報告異常"""
    error_code = "INVALID_REPORT"
    user_message = "上傳的內容似乎不是完整的放射科報告"


class ContentTooShortException(ValidationException):
    """內容過短異常"""
    error_code = "CONTENT_TOO_SHORT"
    user_message = "輸入內容過短，請確保包含完整的醫學報告內容"


class ContentTooLongException(ValidationException):
    """內容過長異常"""
    error_code = "CONTENT_TOO_LONG"
    user_message = "輸入內容超過限制，請分段處理"


class NoMedicalContentException(ValidationException):
    """無醫學內容異常"""
    error_code = "NO_MEDICAL_CONTENT"
    user_message = "內容中未發現明顯的醫學術語，請確認這是一份放射科報告"


# 文件處理相關異常
class FileException(RadiAIException):
    """文件處理異常基類"""
    error_code = "FILE_ERROR"
    user_message = "文件處理失敗"
    http_status = 400


class FileTooLargeException(FileException):
    """文件過大異常"""
    error_code = "FILE_TOO_LARGE"
    user_message = "文件過大，請上傳小於10MB的文件"


class UnsupportedFileTypeException(FileException):
    """不支持的文件類型異常"""
    error_code = "UNSUPPORTED_FILE_TYPE"
    user_message = "不支持的文件格式，請上傳PDF、TXT或DOCX文件"


class FileReadException(FileException):
    """文件讀取異常"""
    error_code = "FILE_READ_ERROR"
    user_message = "無法讀取文件內容，請確保文件未損壞"


class MaliciousFileException(FileException):
    """惡意文件異常"""
    error_code = "MALICIOUS_FILE"
    user_message = "檢測到潛在的安全風險，文件已被拒絕"
    should_log = True  # 必須記錄


# API相關異常
class APIException(RadiAIException):
    """API異常基類"""
    error_code = "API_ERROR"
    user_message = "服務暫時不可用"
    http_status = 503


class OpenAIException(APIException):
    """OpenAI API異常"""
    error_code = "OPENAI_ERROR"
    user_message = "AI服務暫時不可用，請稍後再試"


class RateLimitException(APIException):
    """速率限制異常"""
    error_code = "RATE_LIMIT"
    user_message = "請求過於頻繁，請稍等一分鐘後重試"
    http_status = 429


class TimeoutException(APIException):
    """超時異常"""
    error_code = "TIMEOUT"
    user_message = "請求超時，請檢查網絡連接後重試"
    http_status = 504


class NetworkException(APIException):
    """網絡異常"""
    error_code = "NETWORK_ERROR"
    user_message = "網絡連接問題，請檢查您的網絡連接"


# 配額相關異常
class QuotaException(RadiAIException):
    """配額異常基類"""
    error_code = "QUOTA_ERROR"
    user_message = "配額相關錯誤"
    http_status = 403


class QuotaExceededException(QuotaException):
    """配額超出異常"""
    error_code = "QUOTA_EXCEEDED"
    user_message = "您的免費翻譯額度已用完"
    
    def __init__(self, used: int = 0, limit: int = 3):
        super().__init__(
            message=f"Quota exceeded: {used}/{limit}",
            details={"used": used, "limit": limit}
        )


class DailyLimitException(QuotaException):
    """每日限制異常"""
    error_code = "DAILY_LIMIT"
    user_message = "您今日的使用次數已達上限，請明天再試"


# 安全相關異常
class SecurityException(RadiAIException):
    """安全異常基類"""
    error_code = "SECURITY_ERROR"
    user_message = "檢測到安全問題"
    http_status = 403
    should_log = True  # 安全異常必須記錄


class SuspiciousActivityException(SecurityException):
    """可疑活動異常"""
    error_code = "SUSPICIOUS_ACTIVITY"
    user_message = "檢測到異常活動，請求已被拒絕"


class BlockedIPException(SecurityException):
    """IP封鎖異常"""
    error_code = "BLOCKED_IP"
    user_message = "您的訪問已被限制"


# 系統相關異常
class SystemException(RadiAIException):
    """系統異常基類"""
    error_code = "SYSTEM_ERROR"
    user_message = "系統錯誤，請聯繫技術支持"
    http_status = 500


class ConfigurationException(SystemException):
    """配置異常"""
    error_code = "CONFIG_ERROR"
    user_message = "系統配置錯誤"


class DatabaseException(SystemException):
    """數據庫異常"""
    error_code = "DATABASE_ERROR"
    user_message = "數據服務暫時不可用"


# 異常處理工具
class ExceptionHandler:
    """統一的異常處理器"""
    
    @staticmethod
    def handle_exception(e: Exception) -> Dict[str, Any]:
        """
        處理異常並返回標準化的錯誤信息
        
        Args:
            e: 異常對象
            
        Returns:
            Dict: 錯誤信息字典
        """
        if isinstance(e, RadiAIException):
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.user_message,
                "details": e.details
            }
        else:
            # 處理未預期的異常
            logger.exception("Unexpected exception occurred")
            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "message": "發生未預期的錯誤，請稍後再試",
                "details": {}
            }
    
    @staticmethod
    def get_user_friendly_message(e: Exception) -> str:
        """
        獲取用戶友好的錯誤消息
        
        Args:
            e: 異常對象
            
        Returns:
            str: 用戶友好的錯誤消息
        """
        if isinstance(e, RadiAIException):
            return e.user_message
        
        # 處理常見的第三方異常
        error_str = str(e).lower()
        
        if "rate limit" in error_str:
            return "請求過於頻繁，請稍後再試"
        elif "timeout" in error_str:
            return "請求超時，請檢查網絡連接"
        elif "connection" in error_str or "network" in error_str:
            return "網絡連接錯誤，請檢查您的網絡"
        elif "api" in error_str or "openai" in error_str:
            return "AI服務暫時不可用"
        else:
            return "處理過程中發生錯誤，請稍後再試"


# 異常分類映射（用於統計和監控）
EXCEPTION_CATEGORIES = {
    "validation": [
        EmptyInputException,
        InvalidReportException,
        ContentTooShortException,
        ContentTooLongException,
        NoMedicalContentException
    ],
    "file": [
        FileTooLargeException,
        UnsupportedFileTypeException,
        FileReadException,
        MaliciousFileException
    ],
    "api": [
        OpenAIException,
        RateLimitException,
        TimeoutException,
        NetworkException
    ],
    "quota": [
        QuotaExceededException,
        DailyLimitException
    ],
    "security": [
        SuspiciousActivityException,
        BlockedIPException
    ],
    "system": [
        ConfigurationException,
        DatabaseException
    ]
}


def categorize_exception(e: Exception) -> str:
    """
    將異常分類
    
    Args:
        e: 異常對象
        
    Returns:
        str: 異常類別
    """
    for category, exception_types in EXCEPTION_CATEGORIES.items():
        if type(e) in exception_types:
            return category
    return "unknown"