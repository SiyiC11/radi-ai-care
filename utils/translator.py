"""
RadiAI.Care 翻譯引擎
提供專業的醫學報告翻譯和內容驗證功能
"""

import time
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
import os
from config.settings import AppConfig
from utils.prompt_template import get_prompt, create_enhanced_disclaimer, get_processing_steps

logger = logging.getLogger(__name__)

class ContentValidator:
    """內容驗證器"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.medical_keywords = config.MEDICAL_KEYWORDS
        self.min_length = config.MIN_TEXT_LENGTH
        self.max_length = config.MAX_TEXT_LENGTH
    
    def validate_content(self, text: str) -> Dict[str, Any]:
        """
        驗證文本內容是否為有效的醫學報告
        
        Args:
            text: 待驗證的文本
            
        Returns:
            Dict: 驗證結果
        """
        if not text or not text.strip():
            return {
                "is_valid": False,
                "confidence": 0.0,
                "found_terms": [],
                "issues": ["文本為空"],
                "suggestions": ["請輸入有效的文本內容"],
                "structure_score": 0
            }
        
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
        found_terms = self._find_medical_terms(text)
        
        # 結構化指標檢測
        structure_score = self._analyze_structure(text)
        
        # 計算信心度
        confidence = self._calculate_confidence(found_terms, structure_score, len(text))
        
        # 驗證標準
        is_valid = len(found_terms) >= 2 and len(text) >= self.min_length
        
        if len(found_terms) < 2:
            issues.append("醫學術語過少")
            suggestions.append("請確認這是醫學報告")
        
        if structure_score == 0:
            issues.append("缺少報告結構")
            suggestions.append("請包含完整的報告段落")
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "found_terms": found_terms,
            "issues": issues,
            "suggestions": suggestions,
            "structure_score": structure_score,
            "term_categories": self._categorize_terms(found_terms)
        }
    
    def _find_medical_terms(self, text: str) -> List[str]:
        """查找醫學術語"""
        text_lower = text.lower()
        found_terms = []
        
        for term in self.medical_keywords:
            if term in text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))  # 去重
    
    def _analyze_structure(self, text: str) -> int:
        """分析文本結構（0-100分）"""
        text_lower = text.lower()
        
        # 檢查報告結構指標
        structure_indicators = [
            'impression:', 'findings:', 'technique:', 'clinical history:',
            'examination:', 'study:', 'conclusion:', 'recommendation:',
            'images show', 'no evidence of', 'consistent with'
        ]
        
        found_indicators = sum(1 for indicator in structure_indicators if indicator in text_lower)
        
        # 基於找到的結構指標計算分數
        if found_indicators >= 3:
            return 100
        elif found_indicators == 2:
            return 80
        elif found_indicators == 1:
            return 60
        else:
            return 0
    
    def _calculate_confidence(self, found_terms: List[str], structure_score: int, text_length: int) -> float:
        """計算內容信心度"""
        # 術語密度得分
        term_score = min(len(found_terms) * 0.1, 0.6)
        
        # 結構得分
        structure_normalized = structure_score / 100 * 0.3
        
        # 長度適宜性得分
        if text_length < self.min_length:
            length_score = 0
        elif text_length > self.max_length:
            length_score = 0.05
        else:
            length_score = 0.1
        
        total_confidence = term_score + structure_normalized + length_score
        return min(total_confidence, 1.0)
    
    def _categorize_terms(self, found_terms: List[str]) -> Dict[str, List[str]]:
        """分類找到的醫學術語"""
        categories = {
            'examination_types': [],
            'anatomy': [],
            'findings': [],
            'procedures': []
        }
        
        examination_terms = ['scan', 'ct', 'mri', 'xray', 'x-ray', 'ultrasound', 'mammogram']
        anatomy_terms = ['chest', 'abdomen', 'brain', 'spine', 'lung', 'heart', 'liver']
        finding_terms = ['lesion', 'mass', 'nodule', 'opacity', 'normal', 'abnormal']
        
        for term in found_terms:
            if term in examination_terms:
                categories['examination_types'].append(term)
            elif term in anatomy_terms:
                categories['anatomy'].append(term)
            elif term in finding_terms:
                categories['findings'].append(term)
            else:
                categories['procedures'].append(term)
        
        return categories

class Translator:
    """增強型翻譯器"""
    
    def __init__(self):
        self.config = AppConfig()
        self.validator = ContentValidator(self.config)
        self._init_openai_client()
    
    def _init_openai_client(self):
        """初始化 OpenAI 客戶端"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API密鑰未設置")
        self.client = OpenAI(api_key=api_key)
    
    def validate_content(self, text: str) -> Dict[str, Any]:
        """驗證內容"""
        return self.validator.validate_content(text)
    
    def translate_with_progress(self, report_text: str, language_code: str, 
                              progress_bar, status_text) -> Dict[str, Any]:
        """
        帶進度顯示的翻譯功能
        
        Args:
            report_text: 報告文本
            language_code: 語言代碼
            progress_bar: Streamlit 進度條
            status_text: Streamlit 狀態文本
            
        Returns:
            Dict: 翻譯結果
        """
        try:
            # 獲取處理步驟
            steps = get_processing_steps(language_code)
            
            for i, step_text in enumerate(steps):
                status_text.markdown(f"**🔄 {step_text}**")
                progress_bar.progress(int((i + 1) / len(steps) * 85))
                time.sleep(0.8)
            
            # 執行翻譯
            status_text.markdown("**🤖 AI 正在生成解讀結果...**")
            progress_bar.progress(95)
            
            result_text, disclaimer_html = self._perform_translation(report_text, language_code)
            
            progress_bar.progress(100)
            time.sleep(0.3)
            
            return {
                "success": True,
                "content": result_text,
                "disclaimer": disclaimer_html,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Translation with progress failed: {e}")
            return {
                "success": False,
                "content": None,
                "disclaimer": None,
                "error": str(e)
            }
    
    def _perform_translation(self, report_text: str, language_code: str) -> tuple:
        """執行實際的翻譯"""
        try:
            system_prompt = get_prompt(language_code)
            
            # 添加上下文增強
            enhanced_prompt = f"""
            {system_prompt}
            
            請特別注意以下要點：
            1. 醫學術語的準確翻譯和本地化
            2. 保持原始報告的結構和邏輯
            3. 提供通俗易懂的解釋，但不簡化重要資訊
            4. 標明任何不確定或需要專業確認的內容
            """
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": f"請翻譯並解釋以下放射科報告：\n\n{report_text}"}
                ],
                temperature=self.config.OPENAI_TEMPERATURE,
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                timeout=self.config.OPENAI_TIMEOUT
            )
            
            result_text = response.choices[0].message.content.strip()
            disclaimer_html = create_enhanced_disclaimer(language_code)
            
            return result_text, disclaimer_html
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg:
                raise Exception("API請求過於頻繁，請稍後重試")
            elif "timeout" in error_msg:
                raise Exception("請求超時，請檢查網路連線後重試")
            elif "api" in error_msg or "openai" in error_msg:
                raise Exception("AI服務暫時不可用，請稍後重試")
            else:
                raise Exception(f"翻譯失敗：{str(e)}")
    
    def estimate_translation_time(self, text_length: int) -> str:
        """估算翻譯時間"""
        if text_length < 500:
            return "10-20秒"
        elif text_length < 1500:
            return "20-40秒"
        else:
            return "40-60秒"
    
    def get_translation_quality_score(self, original_text: str, translated_text: str) -> int:
        """評估翻譯質量分數（0-100）"""
        score = 100
        
        # 基本長度檢查
        original_words = len(original_text.split())
        translated_chars = len(translated_text)
        
        # 翻譯長度合理性
        if translated_chars < original_words * 1.5:
            score -= 30
        elif translated_chars > original_words * 6:
            score -= 20
        
        # 結構完整性檢查
        required_sections = ["📋", "🔍", "💡", "❓"]
        missing_sections = sum(1 for section in required_sections if section not in translated_text)
        score -= missing_sections * 15
        
        return max(0, score)
