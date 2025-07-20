# utils/translator.py
"""
RadiAI.Care 翻譯引擎
提供專業的醫學報告翻譯和內容驗證功能
"""

import openai
import time
import logging
from typing import Optional, Dict, Any, Tuple, List
import re
import json
from dataclasses import dataclass
from enum import Enum

# 設置日誌
logger = logging.getLogger(__name__)

class TranslationQuality(Enum):
    """翻譯質量等級"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"

class ContentType(Enum):
    """內容類型"""
    RADIOLOGY_REPORT = "radiology_report"
    MEDICAL_DOCUMENT = "medical_document"
    GENERAL_TEXT = "general_text"
    INVALID = "invalid"

@dataclass
class TranslationResult:
    """翻譯結果數據類"""
    success: bool
    translated_text: str
    quality_score: int
    quality_level: TranslationQuality
    processing_time_ms: int
    word_count: int
    medical_terms_found: List[str]
    warnings: List[str]
    errors: List[str]
    metadata: Dict[str, Any]

@dataclass
class ValidationResult:
    """內容驗證結果數據類"""
    is_valid: bool
    content_type: ContentType
    confidence_score: float
    issues: List[str]
    suggestions: List[str]
    medical_terms: List[str]
    structure_score: int
    readability_score: int

class MedicalTermsDatabase:
    """醫學術語數據庫"""
    
    # 常見放射科術語
    RADIOLOGY_TERMS = {
        'scan', 'ct', 'mri', 'xray', 'x-ray', 'ultrasound', 'mammogram',
        'examination', 'study', 'image', 'imaging', 'radiological',
        'findings', 'impression', 'conclusion', 'recommendation',
        'technique', 'protocol', 'contrast', 'enhancement',
        'normal', 'abnormal', 'unremarkable', 'significant',
        'lesion', 'mass', 'nodule', 'opacity', 'density',
        'attenuation', 'intensity', 'signal', 'enhancement'
    }
    
    # 解剖結構術語
    ANATOMY_TERMS = {
        'chest', 'thorax', 'lung', 'pulmonary', 'cardiac', 'heart',
        'abdomen', 'abdominal', 'liver', 'hepatic', 'kidney', 'renal',
        'brain', 'cerebral', 'spine', 'spinal', 'vertebral',
        'pelvis', 'pelvic', 'head', 'neck', 'limb', 'joint',
        'bone', 'osseous', 'soft tissue', 'muscle', 'vessel',
        'artery', 'vein', 'lymph', 'node'
    }
    
    # 病理術語
    PATHOLOGY_TERMS = {
        'fracture', 'inflammation', 'infection', 'tumor', 'cancer',
        'metastasis', 'edema', 'hemorrhage', 'infarction',
        'stenosis', 'obstruction', 'dilation', 'hypertrophy',
        'atrophy', 'calcification', 'fibrosis', 'necrosis'
    }
    
    @classmethod
    def get_all_terms(cls) -> set:
        """獲取所有醫學術語"""
        return cls.RADIOLOGY_TERMS | cls.ANATOMY_TERMS | cls.PATHOLOGY_TERMS
    
    @classmethod
    def categorize_terms(cls, found_terms: List[str]) -> Dict[str, List[str]]:
        """分類找到的醫學術語"""
        categories = {
            'radiology': [],
            'anatomy': [],
            'pathology': [],
            'other': []
        }
        
        for term in found_terms:
            term_lower = term.lower()
            if term_lower in cls.RADIOLOGY_TERMS:
                categories['radiology'].append(term)
            elif term_lower in cls.ANATOMY_TERMS:
                categories['anatomy'].append(term)
            elif term_lower in cls.PATHOLOGY_TERMS:
                categories['pathology'].append(term)
            else:
                categories['other'].append(term)
        
        return categories

class ContentValidator:
    """內容驗證器"""
    
    def __init__(self):
        self.min_length = 20
        self.max_length = 50000
        self.medical_terms_db = MedicalTermsDatabase()
    
    def validate_content(self, text: str) -> ValidationResult:
        """
        驗證文本內容
        
        Args:
            text: 待驗證的文本
            
        Returns:
            ValidationResult: 驗證結果
        """
        if not text or not text.strip():
            return ValidationResult(
                is_valid=False,
                content_type=ContentType.INVALID,
                confidence_score=0.0,
                issues=["文本為空"],
                suggestions=["請輸入有效的文本內容"],
                medical_terms=[],
                structure_score=0,
                readability_score=0
            )
        
        text = text.strip()
        issues = []
        suggestions = []
        
        # 基本長度檢查
        if len(text) < self.min_length:
            issues.append(f"文本過短（少於{self.min_length}字符）")
            suggestions.append("請提供更完整的報告內容")
        
        if len(text) > self.max_length:
            issues.append(f"文本過長（超過{self.max_length}字符）")
            suggestions.append("請分段處理或精簡內容")
        
        # 醫學術語檢測
        medical_terms = self._find_medical_terms(text)
        
        # 內容類型識別
        content_type, confidence = self._identify_content_type(text, medical_terms)
        
        # 結構分析
        structure_score = self._analyze_structure(text)
        
        # 可讀性分析
        readability_score = self._analyze_readability(text)
        
        # 整體驗證
        is_valid = self._is_content_valid(
            text, medical_terms, structure_score, readability_score
        )
        
        if not medical_terms:
            issues.append("未檢測到醫學術語")
            suggestions.append("請確認這是醫學報告")
        
        return ValidationResult(
            is_valid=is_valid,
            content_type=content_type,
            confidence_score=confidence,
            issues=issues,
            suggestions=suggestions,
            medical_terms=medical_terms,
            structure_score=structure_score,
            readability_score=readability_score
        )
    
    def _find_medical_terms(self, text: str) -> List[str]:
        """查找醫學術語"""
        text_lower = text.lower()
        found_terms = []
        
        for term in self.medical_terms_db.get_all_terms():
            if term in text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))  # 去重
    
    def _identify_content_type(self, text: str, medical_terms: List[str]) -> Tuple[ContentType, float]:
        """識別內容類型"""
        text_lower = text.lower()
        
        # 放射科報告特徵
        radiology_indicators = [
            'impression:', 'findings:', 'technique:', 'clinical history:',
            'examination:', 'study:', 'images show', 'no evidence of'
        ]
        
        radiology_score = sum(1 for indicator in radiology_indicators if indicator in text_lower)
        medical_terms_score = len(medical_terms)
        
        if radiology_score >= 2 and medical_terms_score >= 3:
            return ContentType.RADIOLOGY_REPORT, 0.9
        elif radiology_score >= 1 and medical_terms_score >= 2:
            return ContentType.RADIOLOGY_REPORT, 0.7
        elif medical_terms_score >= 3:
            return ContentType.MEDICAL_DOCUMENT, 0.6
        elif medical_terms_score >= 1:
            return ContentType.MEDICAL_DOCUMENT, 0.4
        else:
            return ContentType.GENERAL_TEXT, 0.2
    
    def _analyze_structure(self, text: str) -> int:
        """分析文本結構（0-100分）"""
        score = 100
        
        # 檢查段落結構
        lines = text.split('\n')
        if len(lines) < 3:
            score -= 20
        
        # 檢查標題結構
        headers = ['impression', 'findings', 'technique', 'clinical', 'examination']
        found_headers = sum(1 for header in headers if header.lower() in text.lower())
        
        if found_headers == 0:
            score -= 30
        elif found_headers < 2:
            score -= 15
        
        # 檢查句子結構
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 3:
            score -= 15
        
        return max(0, score)
    
    def _analyze_readability(self, text: str) -> int:
        """分析文本可讀性（0-100分）"""
        score = 100
        
        # 字符質量檢查
        total_chars = len(text)
        alpha_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars > 0:
            alpha_ratio = alpha_chars / total_chars
            if alpha_ratio < 0.3:
                score -= 40
            elif alpha_ratio < 0.5:
                score -= 20
        
        # 單詞長度檢查
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length < 2:
                score -= 30
        
        return max(0, score)
    
    def _is_content_valid(self, text: str, medical_terms: List[str], 
                         structure_score: int, readability_score: int) -> bool:
        """判斷內容是否有效"""
        if len(text) < self.min_length:
            return False
        
        if len(medical_terms) < 1:
            return False
        
        if structure_score < 30:
            return False
        
        if readability_score < 20:
            return False
        
        return True

class TranslatorError(Exception):
    """翻譯器自定義異常"""
    pass

class EnhancedTranslator:
    """增強型翻譯器"""
    
    def __init__(self, openai_client, max_retries: int = 3):
        self.client = openai_client
        self.max_retries = max_retries
        self.validator = ContentValidator()
        self.medical_terms_db = MedicalTermsDatabase()
    
    def translate_medical_report(self, 
                               report_text: str, 
                               target_language: str,
                               system_prompt: str) -> TranslationResult:
        """
        翻譯醫學報告
        
        Args:
            report_text: 原始報告文本
            target_language: 目標語言
            system_prompt: 系統提示詞
            
        Returns:
            TranslationResult: 翻譯結果
        """
        start_time = time.time()
        
        try:
            # 預處理和驗證
            cleaned_text = self._preprocess_text(report_text)
            validation_result = self.validator.validate_content(cleaned_text)
            
            if not validation_result.is_valid:
                return TranslationResult(
                    success=False,
                    translated_text="",
                    quality_score=0,
                    quality_level=TranslationQuality.FAILED,
                    processing_time_ms=self._get_processing_time(start_time),
                    word_count=len(cleaned_text.split()),
                    medical_terms_found=validation_result.medical_terms,
                    warnings=validation_result.suggestions,
                    errors=validation_result.issues,
                    metadata={"validation_result": validation_result}
                )
            
            # 執行翻譯
            translated_text = self._perform_translation(
                cleaned_text, system_prompt
            )
            
            # 質量評估
            quality_score, quality_level = self._assess_quality(
                cleaned_text, translated_text, validation_result
            )
            
            # 生成結果
            processing_time = self._get_processing_time(start_time)
            
            return TranslationResult(
                success=True,
                translated_text=translated_text,
                quality_score=quality_score,
                quality_level=quality_level,
                processing_time_ms=processing_time,
                word_count=len(cleaned_text.split()),
                medical_terms_found=validation_result.medical_terms,
                warnings=[],
                errors=[],
                metadata={
                    "validation_result": validation_result,
                    "target_language": target_language
                }
            )
            
        except Exception as e:
            logger.error(f"翻譯過程中發生錯誤: {e}")
            return TranslationResult(
                success=False,
                translated_text="",
                quality_score=0,
                quality_level=TranslationQuality.FAILED,
                processing_time_ms=self._get_processing_time(start_time),
                word_count=0,
                medical_terms_found=[],
                warnings=[],
                errors=[str(e)],
                metadata={}
            )
    
    def _preprocess_text(self, text: str) -> str:
        """預處理文本"""
        if not text:
            return ""
        
        # 移除過多的空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 修正常見的OCR錯誤
        ocr_fixes = {
            r'\bl\b': '1',  # 單獨的 l 替換為 1
            r'\bO\b': '0',  # 單獨的 O 替換為 0
            r'rn': 'm',     # rn 組合經常被誤識別為 m
            r'(\d)\s*-\s*(\d)': r'\1-\2',  # 修復數字間的連字符
        }
        
        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _perform_translation(self, text: str, system_prompt: str) -> str:
        """執行翻譯"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"請翻譯並解釋以下放射科報告：\n\n{text}"}
                    ],
                    temperature=0.3,
                    max_tokens=2500,
                    timeout=30
                )
                
                result = response.choices[0].message.content.strip()
                
                if result:
                    logger.info(f"翻譯成功，嘗試次數：{attempt + 1}")
                    return result
                else:
                    logger.warning(f"翻譯返回空結果，嘗試次數：{attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"翻譯嘗試 {attempt + 1} 失敗: {e}")
                
                if attempt < self.max_retries - 1:
                    # 指數退避
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise TranslatorError(f"翻譯失敗，已重試 {self.max_retries} 次")
        
        raise TranslatorError("翻譯失敗")
    
    def _assess_quality(self, 
                       original_text: str, 
                       translated_text: str,
                       validation_result: ValidationResult) -> Tuple[int, TranslationQuality]:
        """評估翻譯質量"""
        score = 100
        
        # 基於原文質量
        if validation_result.structure_score < 50:
            score -= 20
        
        if validation_result.readability_score < 50:
            score -= 15
        
        # 翻譯長度檢查
        original_words = len(original_text.split())
        translated_words = len(translated_text.split())
        
        if translated_words < original_words * 0.5:
            score -= 30
        elif translated_words > original_words * 3:
            score -= 20
        
        # 結構完整性檢查
        if "📋" not in translated_text or "🔍" not in translated_text:
            score -= 25
        
        if "💡" not in translated_text or "❓" not in translated_text:
            score -= 25
        
        # 確定質量等級
        if score >= 90:
            quality_level = TranslationQuality.EXCELLENT
        elif score >= 75:
            quality_level = TranslationQuality.GOOD
        elif score >= 60:
            quality_level = TranslationQuality.ACCEPTABLE
        elif score >= 30:
            quality_level = TranslationQuality.POOR
        else:
            quality_level = TranslationQuality.FAILED
        
        return max(0, score), quality_level
    
    def _get_processing_time(self, start_time: float) -> int:
        """獲取處理時間（毫秒）"""
        return int((time.time() - start_time) * 1000)

# 便捷函數
def create_translator(openai_client) -> EnhancedTranslator:
    """創建翻譯器實例"""
    return EnhancedTranslator(openai_client)

def validate_medical_content(text: str) -> ValidationResult:
    """驗證醫學內容的便捷函數"""
    validator = ContentValidator()
    return validator.validate_content(text)

def get_medical_terms(text: str) -> Dict[str, List[str]]:
    """獲取醫學術語的便捷函數"""
    validator = ContentValidator()
    found_terms = validator._find_medical_terms(text)
    return MedicalTermsDatabase.categorize_terms(found_terms)

# 向後兼容的函數
def translate_and_explain_report(report_text: str, language_code: str, 
                                openai_client, system_prompt: str) -> str:
    """
    向後兼容的翻譯函數
    
    Args:
        report_text: 報告文本
        language_code: 語言代碼
        openai_client: OpenAI 客戶端
        system_prompt: 系統提示詞
        
    Returns:
        str: 翻譯結果文本
    """
    try:
        translator = EnhancedTranslator(openai_client)
        result = translator.translate_medical_report(
            report_text, language_code, system_prompt
        )
        
        if result.success:
            return result.translated_text
        else:
            error_msg = "; ".join(result.errors) if result.errors else "未知錯誤"
            return f"❌ 翻譯失敗：{error_msg}"
            
    except Exception as e:
        logger.error(f"翻譯函數錯誤: {e}")
        return f"❌ 翻譯過程中發生錯誤：{str(e)}"
