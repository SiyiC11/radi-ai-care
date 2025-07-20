"""
RadiAI.Care 文件處理模塊
統一處理各種文件格式的文本提取
"""

import fitz  # PyMuPDF for PDF
import docx  # python-docx for Word documents
import io
import logging
from typing import Optional, Tuple, Dict, Any
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class FileHandler:
    """文件處理類，支持多種格式的文本提取"""
    
    def __init__(self):
        self.config = AppConfig()
        self.supported_types = self.config.SUPPORTED_FILE_TYPES
        self.max_size_mb = self.config.FILE_SIZE_LIMIT_MB
    
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
    
    def extract_text(self, uploaded_file) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        從上傳的文件中提取文本
        
        Args:
            uploaded_file: Streamlit上傳的文件對象
            
        Returns:
            Tuple[Optional[str], Dict[str, Any]]: (提取的文本內容, 處理信息)
        """
        # 先驗證文件
        is_valid, error_msg = self.validate_file(uploaded_file)
        if not is_valid:
            logger.error(f"File validation failed: {error_msg}")
            return None, {"error": error_msg, "file_info": {}}
        
        file_extension = uploaded_file.name.lower().split('.')[-1]
        file_info = {
            "name": uploaded_file.name,
            "size_kb": round(len(uploaded_file.getvalue()) / 1024, 2),
            "type": file_extension
        }
        
        try:
            if file_extension == 'txt':
                text = self._extract_from_txt(uploaded_file)
            elif file_extension == 'pdf':
                text = self._extract_from_pdf(uploaded_file)
            elif file_extension in ['docx', 'doc']:
                text = self._extract_from_docx(uploaded_file)
            else:
                logger.error(f"Unsupported file type: {file_extension}")
                return None, {"error": f"不支持的文件類型: {file_extension}", "file_info": file_info}
            
            if text and text.strip():
                return text.strip(), {"file_info": file_info, "success": True}
            else:
                return None, {"error": "文件中沒有找到有效文本", "file_info": file_info}
                
        except Exception as e:
            logger.error(f"Text extraction failed for {file_extension}: {e}")
            return None, {"error": f"文本提取失敗: {str(e)}", "file_info": file_info}
    
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
                try:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode('big5')
                    return content.strip()
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode('latin-1')
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
        
        pdf_document.close()
        return "\n\n".join(text_parts)
    
    def _extract_from_docx(self, uploaded_file) -> str:
        """從DOCX文件提取文本"""
        document = docx.Document(uploaded_file)
        text_parts = []
        
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        return "\n\n".join(text_parts)
    
    def get_supported_formats_info(self) -> Dict[str, str]:
        """獲取支持格式的信息"""
        return {
            'pdf': 'PDF 文檔 - 支持掃描版和電子版',
            'txt': 'TXT 文本 - 純文字格式',
            'docx': 'DOCX 文檔 - Microsoft Word 格式'
        }
    
    def get_file_stats(self, uploaded_file) -> Dict[str, Any]:
        """獲取文件統計信息"""
        if not uploaded_file:
            return {}
        
        file_size_bytes = len(uploaded_file.getvalue())
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        return {
            'filename': uploaded_file.name,
            'size_bytes': file_size_bytes,
            'size_kb': round(file_size_bytes / 1024, 2),
            'size_mb': round(file_size_bytes / (1024 * 1024), 2),
            'extension': file_extension,
            'is_supported': file_extension in self.supported_types,
            'is_valid_size': file_size_bytes / (1024 * 1024) <= self.max_size_mb
        }
