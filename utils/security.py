"""
RadiAI.Care 安全性管理模組
提供輸入消毒、文件驗證等安全功能
"""

import re
import hashlib
import logging
import time
from typing import Optional, Tuple, Dict
import bleach
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityManager:
    """安全性管理器"""
    
    # 允許的HTML標籤（保守策略：不允許任何標籤）
    ALLOWED_TAGS = []
    
    # 允許的文件類型和對應的魔術數字
    FILE_SIGNATURES = {
        'pdf': [b'%PDF'],
        'docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'txt': None  # 純文字沒有特定的魔術數字
    }
    
    # 最大文件大小（bytes）
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        消毒用戶輸入，防止XSS和其他注入攻擊
        
        Args:
            text: 原始輸入文本
            
        Returns:
            str: 消毒後的安全文本
        """
        if not text:
            return ""
        
        try:
            # 1. 使用bleach清理HTML
            cleaned = bleach.clean(
                text, 
                tags=SecurityManager.ALLOWED_TAGS, 
                strip=True
            )
            
            # 2. 移除控制字符（保留換行和製表符）
            cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cleaned)
            
            # 3. 移除潛在的腳本標籤（額外保護）
            script_patterns = [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>.*?</iframe>',
                r'<object[^>]*>.*?</object>',
                r'<embed[^>]*>'
            ]
            
            for pattern in script_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
            
            # 4. 限制連續空白字符
            cleaned = re.sub(r'\s{3,}', '  ', cleaned)
            
            # 5. 確保文本不會太長（防止DoS）
            if len(cleaned) > 100000:  # 100K字符限制
                cleaned = cleaned[:100000]
                logger.warning("Input text truncated due to length limit")
            
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {e}")
            # 發生錯誤時返回空字串（最安全的選擇）
            return ""
    
    @staticmethod
    def validate_file_content(file_content: bytes, file_extension: str) -> Tuple[bool, str]:
        """
        驗證文件內容的安全性
        
        Args:
            file_content: 文件二進制內容
            file_extension: 文件擴展名
            
        Returns:
            Tuple[bool, str]: (是否安全, 錯誤訊息)
        """
        # 1. 檢查文件大小
        if len(file_content) > SecurityManager.MAX_FILE_SIZE:
            return False, "文件大小超過限制（10MB）"
        
        if len(file_content) == 0:
            return False, "文件內容為空"
        
        # 2. 檢查文件類型
        if file_extension not in SecurityManager.FILE_SIGNATURES:
            return False, f"不支持的文件類型：{file_extension}"
        
        # 3. 驗證文件魔術數字（除了txt）
        if file_extension != 'txt':
            signatures = SecurityManager.FILE_SIGNATURES.get(file_extension, [])
            if signatures:
                file_header = file_content[:8]  # 讀取前8個字節
                valid_signature = False
                
                for signature in signatures:
                    if file_header.startswith(signature):
                        valid_signature = True
                        break
                
                if not valid_signature:
                    return False, "文件格式驗證失敗：文件內容與擴展名不符"
        
        # 4. 掃描潛在的惡意內容
        if SecurityManager._scan_malicious_content(file_content):
            return False, "檢測到潛在的惡意內容"
        
        return True, ""
    
    @staticmethod
    def _scan_malicious_content(content: bytes) -> bool:
        """
        掃描潛在的惡意內容
        
        Args:
            content: 文件內容
            
        Returns:
            bool: 是否檢測到惡意內容
        """
        try:
            # 嘗試解碼為文本進行檢查
            text_content = content.decode('utf-8', errors='ignore').lower()
            
            # 檢查常見的惡意模式
            malicious_patterns = [
                r'<script',
                r'javascript:',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__',
                r'subprocess',
                r'os\.system',
                r'cmd\.exe',
                r'/bin/sh',
                r'powershell'
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, text_content):
                    logger.warning(f"Detected potentially malicious pattern: {pattern}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error scanning for malicious content: {e}")
            # 掃描出錯時保守處理
            return True
        
        return False
    
    @staticmethod
    def generate_file_hash(file_content: bytes) -> str:
        """
        生成文件內容的哈希值
        
        Args:
            file_content: 文件內容
            
        Returns:
            str: SHA256哈希值
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        消毒文件名，防止路徑遍歷攻擊
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 安全的文件名
        """
        # 移除路徑分隔符
        filename = filename.replace('/', '').replace('\\', '')
        
        # 移除特殊字符，只保留字母、數字、點、橫線和下劃線
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # 確保文件名不會太長
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        # 防止特殊文件名
        if filename.lower() in ['con', 'prn', 'aux', 'nul', 'com1', 'lpt1']:
            filename = f"safe_{filename}"
        
        return filename
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        驗證電子郵件格式
        
        Args:
            email: 電子郵件地址
            
        Returns:
            bool: 是否為有效格式
        """
        if not email:
            return True  # 空郵件是允許的（選填欄位）
        
        # 基本的電子郵件正則表達式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def mask_sensitive_data(text: str) -> str:
        """
        遮蔽敏感數據（如電話號碼、身份證號等）
        
        Args:
            text: 原始文本
            
        Returns:
            str: 遮蔽後的文本
        """
        # 澳洲電話號碼模式
        phone_patterns = [
            (r'\b(?:0[2-8]\d{8}|\+61[2-8]\d{8}|04\d{8}|\+614\d{8})\b', 'PHONE_MASKED'),
            (r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', 'CARD_MASKED'),  # 信用卡
            (r'\b\d{3}-\d{3}-\d{3}\b', 'TAX_FILE_MASKED'),  # TFN格式
        ]
        
        masked_text = text
        for pattern, replacement in phone_patterns:
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text
    
    @staticmethod
    def check_content_safety(text: str) -> Dict[str, any]:
        """
        檢查內容安全性並返回詳細報告
        
        Args:
            text: 要檢查的文本
            
        Returns:
            Dict: 安全檢查結果
        """
        result = {
            'is_safe': True,
            'warnings': [],
            'sanitized_text': text,
            'has_sensitive_data': False
        }
        
        # 1. 基本消毒
        sanitized = SecurityManager.sanitize_input(text)
        if sanitized != text:
            result['warnings'].append("內容已被消毒處理")
            result['sanitized_text'] = sanitized
        
        # 2. 檢查敏感數據
        if re.search(r'\b(?:0[2-8]\d{8}|04\d{8})\b', text):
            result['has_sensitive_data'] = True
            result['warnings'].append("檢測到可能的電話號碼")
        
        # 3. 檢查長度
        if len(text) > 50000:
            result['warnings'].append("文本過長，可能影響處理效能")
        
        # 4. 檢查是否包含可執行代碼
        code_patterns = ['exec(', 'eval(', '__import__', 'subprocess']
        for pattern in code_patterns:
            if pattern in text:
                result['is_safe'] = False
                result['warnings'].append(f"檢測到潛在的可執行代碼：{pattern}")
        
        return result


class IPTracker:
    """IP追蹤器（用於防止濫用）"""
    
    def __init__(self):
        self.usage_records = {}
        self.blocked_ips = set()
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """檢查IP是否被允許使用服務"""
        if ip_address in self.blocked_ips:
            return False
        
        # 檢查使用頻率
        current_time = time.time()
        if ip_address in self.usage_records:
            recent_uses = [t for t in self.usage_records[ip_address] if current_time - t < 3600]
            if len(recent_uses) > 10:  # 每小時最多10次
                logger.warning(f"IP {ip_address} exceeded rate limit")
                return False
        
        return True
    
    def record_usage(self, ip_address: str):
        """記錄IP使用"""
        if ip_address not in self.usage_records:
            self.usage_records[ip_address] = []
        self.usage_records[ip_address].append(time.time())
        
        # 清理舊記錄
        current_time = time.time()
        self.usage_records[ip_address] = [
            t for t in self.usage_records[ip_address] 
            if current_time - t < 86400  # 保留24小時內的記錄
        ]