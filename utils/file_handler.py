# utils/file_handler.py
"""
文件處理模塊
統一處理各種文件格式的文本提取
"""

import fitz  # PyMuPDF for PDF
import docx  # python-docx for Word documents
import io
import logging
from typing import Optional, Tuple
from config.settings import SUPPORTED_FILES, LIMITS

logger = logging.getLogger(__name__)

class FileHandler:
    """文件處理類，支持多種格式的文本提取"""
    
    def __init__(self):
        self.supported_types = SUPPORTED_FILES["types"]
        self.max_size_mb = LIMITS["file_size_limit_mb"]
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """
        驗證上傳文件的有效性
        
        Args:
            uploaded_file: Streamlit上傳的文件對象
            
        Returns:
            Tuple[bool, str]: (是否有效, 錯誤信息)
        """
        if uploaded_file is None:
            return False, "沒有選擇文件"
        
        # 檢查文件大小
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > self.max_size_mb:
            return False, f"文件過大，請上傳小於{self.max_size_mb}MB的文件"
        
        # 檢查文件類型
        file_extension = uploaded_file.name.lower().split('.')[-1]
        if file_extension not in self.supported_types:
            return False, f"不支持的文件格式，請上傳{', '.join(self.supported_types).upper()}文件"
        
        return True, ""
    
    def extract_text(self, uploaded_file) -> Optional[str]:
        """
        從上傳的文件中提取文本
        
        Args:
            uploaded_file: Streamlit上傳的文件對象
            
        Returns:
            Optional[str]: 提取的文本內容，失敗時返回None
        """
        # 先驗證文件
        is_valid, error_msg = self.validate_file(uploaded_file)
        if not is_valid:
            logger.error(f"File validation failed: {error_msg}")
            return None
        
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        try:
            if file_extension == 'txt':
                return self._extract_from_txt(uploaded_file)
            elif file_extension == 'pdf':
                return self._extract_from_pdf(uploaded_file)
            elif file_extension in ['docx', 'doc']:
                return self._extract_from_docx(uploaded_file)
            else:
                logger.error(f"Unsupported file type: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file_extension}: {e}")
            return None
    
    def _extract_from_txt(self, uploaded_file) -> str:
        """從TXT文件提取文本"""
        try:
            content = uploaded_file.read().decode('utf-8')
            return content.strip()
        except UnicodeDecodeError:
            # 嘗試其他編碼
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('gbk')
                return content.strip()
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('big5')
                return content.strip()
    
    def _extract_from_pdf(self, uploaded_file) -> str:
        """從PDF文件提取文本"""
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text_parts = []
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            page_text = page.get_text()
            if page_text.strip():  # 只添加非空頁面
                text_parts.append(page_text)