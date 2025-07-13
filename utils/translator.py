import openai
import time
import logging
from typing import Optional, Dict, Any, Tuple
from utils.prompt_template import get_prompt

logger = logging.getLogger(__name__)

class TranslatorError(Exception):
    """Custom exception for translator errors"""
    pass

def validate_report(report: str) -> Tuple[bool, str]:
    """
    Validate if the report contains meaningful content
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not report or not report.strip():
        return False, "Empty report"
    
    # Check if report is too short (likely OCR error)
    if len(report.strip()) < 10:
        return False, "Report too short (< 10 characters)"
    
    # Check if report contains some medical-related keywords
    medical_keywords = [
        'scan', 'image', 'finding', 'examination', 'study', 'patient',
        'impression', 'conclusion', 'recommendation', 'normal', 'abnormal',
        'radiology', 'ct', 'mri', 'xray', 'x-ray', 'ultrasound', 'report',
        'chest', 'abdomen', 'brain', 'spine', 'bone', 'lung', 'heart',
        'liver', 'kidney', 'pelvis', 'head', 'neck', 'contrast', 'without'
    ]
    
    report_lower = report.lower()
    matching_keywords = [kw for kw in medical_keywords if kw in report_lower]
    
    if not matching_keywords:
        return False, "No medical terminology detected"
    
    # Check for minimum word count
    word_count = len(report.split())
    if word_count < 5:
        return False, f"Too few words ({word_count})"
    
    # Check if it's mostly numbers or special characters
    text_chars = sum(1 for c in report if c.isalpha())
    total_chars = len(report.replace(' ', ''))
    
    if total_chars > 0 and text_chars / total_chars < 0.3:
        return False, "Content appears to be mostly non-text"
    
    return True, f"Valid report with {len(matching_keywords)} medical terms"

def clean_report(report: str) -> str:
    """Clean and preprocess the report text"""
    if not report:
        return ""
    
    # Remove excessive whitespace
    cleaned = ' '.join(report.split())
    
    # Remove common OCR artifacts while preserving medical symbols
    artifacts_to_remove = [
        '|', '~', '`', '§', '±', '¿', '¡'  # Removed '°' as it might be temperature
    ]
    
    for artifact in artifacts_to_remove:
        cleaned = cleaned.replace(artifact, '')
    
    # Fix common OCR mistakes
    replacements = {
        ' I ': ' 1 ',  # Common OCR mistake
        ' l ': ' 1 ',  # Another common mistake
        ' O ': ' 0 ',  # Zero vs O
    }
    
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    return cleaned.strip()

def create_chat_completion(messages: list, model: str = "gpt-4o", max_retries: int = 3) -> Optional[str]:
    """Create chat completion with retry logic"""
    
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=2000
            )
            
            if response and "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                if content and content.strip():
                    logger.info(f"Successfully got AI response on attempt {attempt + 1}")
                    return content.strip()
                else:
                    logger.warning(f"Empty response from OpenAI on attempt {attempt + 1}")
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle rate limiting
            if "rate limit" in error_str or "quota" in error_str:
                logger.warning(f"Rate limit exceeded on attempt {attempt + 1}, waiting...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            # Handle API errors
            elif "api" in error_str or "invalid" in error_str:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                time.sleep(1)
                continue
                
            # Handle timeout
            elif "timeout" in error_str or "connection" in error_str:
                logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
                time.sleep(1)
                continue
                
            # Handle other errors
            else:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                time.sleep(1)
                continue
    
    return None

def format_explanation(explanation: str, language: str) -> str:
    """Format the explanation with proper HTML structure"""
    if not explanation:
        return ""
    
    # Add some basic HTML formatting if not present
    if not any(tag in explanation for tag in ['<h', '<p', '<div', '<ul', '<ol']):
        # Convert markdown-style headers to HTML
        lines = explanation.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Convert emoji headers to HTML
            if line.startswith('1️⃣') or line.startswith('2️⃣') or line.startswith('3️⃣'):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem; font-weight: bold;">{line}</h3>')
            elif line.startswith('【') and line.endswith('】'):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem; font-weight: bold;">{line}</h3>')
            elif line.startswith('**') and line.endswith('**'):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem; font-weight: bold;">{line[2:-2]}</h3>')
            elif line.startswith('## '):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem; font-weight: bold;">{line[3:]}</h3>')
            elif line.startswith('# '):
                formatted_lines.append(f'<h2 style="color: #1f77b4; margin-top: 1.5rem; font-weight: bold;">{line[2:]}</h2>')
            elif line.startswith('- '):
                formatted_lines.append(f'<p style="margin-left: 1rem; margin-bottom: 0.5rem;">• {line[2:]}</p>')
            elif line.startswith('* '):
                formatted_lines.append(f'<p style="margin-left: 1rem; margin-bottom: 0.5rem;">• {line[2:]}</p>')
            else:
                formatted_lines.append(f'<p style="margin-bottom: 1rem; line-height: 1.6;">{line}</p>')
        
        return '\n'.join(formatted_lines)
    
    return explanation

def add_safety_disclaimer(explanation: str, language: str) -> str:
    """Add safety disclaimer to the explanation"""
    disclaimers = {
        "繁體中文": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;'><strong>⚠️ 重要提醒：</strong>此解釋僅供參考，不能取代專業醫療建議。請務必與您的醫師討論報告內容和後續治療計劃。如有疑問或擔憂，請立即諮詢醫療專業人員。</div>",
        "简体中文": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;'><strong>⚠️ 重要提醒：</strong>此解释仅供参考，不能替代专业医疗建议。请务必与您的医师讨论报告内容和后续治疗计划。如有疑问或担忧，请立即咨询医疗专业人员。</div>",
        "English": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;'><strong>⚠️ Important Notice:</strong> This explanation is for reference only and cannot replace professional medical advice. Please discuss the report content and follow-up treatment plans with your physician. If you have any concerns or questions, please consult with a medical professional immediately.</div>"
    }
    
    disclaimer = disclaimers.get(language, disclaimers["简体中文"])
    return explanation + disclaimer

def explain_report(report: str, language: str) -> Tuple[str, Dict[str, Any]]:
    """
    Main function to explain radiology report
    
    Args:
        report: The radiology report text
        language: Target language for explanation
        
    Returns:
        Tuple of (formatted_explanation, simple_metrics)
        
    Raises:
        TranslatorError: If translation fails
    """
    start_time = time.time()
    
    # Simple metrics for backward compatibility
    metrics = {
        "success": False,
        "error_message": None
    }
    
    try:
        # Validate inputs
        if not report or not report.strip():
            raise TranslatorError("Empty report provided")
        
        if language not in ["繁體中文", "简体中文", "English"]:
            raise TranslatorError(f"Unsupported language: {language}")
        
        # Clean and validate report
        cleaned_report = clean_report(report)
        
        is_valid, validation_reason = validate_report(cleaned_report)
        
        if not is_valid:
            # Try to provide a helpful message based on language
            error_messages = {
                "繁體中文": f"❌ 無法識別有效的醫學報告內容：{validation_reason}。請確認上傳的是完整的放射科報告，並且圖片清晰可讀。",
                "简体中文": f"❌ 无法识别有效的医学报告内容：{validation_reason}。请确认上传的是完整的放射科报告，并且图片清晰可读。",
                "English": f"❌ Unable to identify valid medical report content: {validation_reason}. Please ensure you've uploaded a complete radiology report and that the image is clear and readable."
            }
            
            error_message = error_messages.get(language, error_messages["简体中文"])
            metrics["error_message"] = f"Validation failed: {validation_reason}"
            
            return f"<p>{error_message}</p>", metrics
        
        # Get system prompt
        system_prompt = get_prompt(language)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": cleaned_report}
        ]
        
        # Get explanation from OpenAI
        explanation = create_chat_completion(messages)
        
        if not explanation:
            raise TranslatorError("Failed to generate explanation after multiple attempts")
        
        # Format explanation
        formatted_explanation = format_explanation(explanation, language)
        
        # Add safety disclaimer
        final_explanation = add_safety_disclaimer(formatted_explanation, language)
        
        # Update metrics
        metrics["success"] = True
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Successfully generated explanation for {language} language. "
                   f"Processing time: {processing_time}ms")
        
        return final_explanation, metrics
        
    except TranslatorError as e:
        metrics["error_message"] = str(e)
        logger.error(f"TranslatorError: {e}")
        raise
    except Exception as e:
        metrics["error_message"] = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error in explain_report: {e}")
        raise TranslatorError(f"Failed to process report: {str(e)}")

def get_report_quality_score(report: str) -> Dict[str, Any]:
    """
    Analyze report quality and provide a score
    
    Args:
        report: The radiology report text
        
    Returns:
        Dictionary with quality metrics
    """
    if not report:
        return {"score": 0, "issues": ["Empty report"], "suggestions": []}
    
    issues = []
    suggestions = []
    score = 100
    
    # Check length
    if len(report) < 50:
        issues.append("Report is very short")
        suggestions.append("Ensure complete report is captured")
        score -= 20
    
    # Check for medical terminology
    medical_terms = [
        'impression', 'finding', 'examination', 'study', 'normal', 'abnormal',
        'ct', 'mri', 'xray', 'ultrasound', 'scan', 'image'
    ]
    
    found_terms = sum(1 for term in medical_terms if term.lower() in report.lower())
    if found_terms < 2:
        issues.append("Limited medical terminology detected")
        suggestions.append("Verify this is a complete medical report")
        score -= 15
    
    # Check for structure
    structure_indicators = ['impression:', 'findings:', 'conclusion:', 'technique:']
    found_structure = sum(1 for indicator in structure_indicators if indicator.lower() in report.lower())
    
    if found_structure == 0:
        issues.append("No clear report structure identified")
        suggestions.append("Look for sections like 'Findings' or 'Impression'")
        score -= 10
    
    # Check for excessive special characters (OCR artifacts)
    special_char_ratio = sum(1 for c in report if not c.isalnum() and c not in ' .,;:()-/') / len(report)
    if special_char_ratio > 0.1:
        issues.append("High number of special characters detected")
        suggestions.append("Image quality may be poor - try a clearer scan")
        score -= 15
    
    # Check word count
    word_count = len(report.split())
    if word_count < 10:
        issues.append("Very few words detected")
        suggestions.append("Ensure text is clearly visible in image")
        score -= 20
    
    return {
        "score": max(0, score),
        "word_count": word_count,
        "character_count": len(report),
        "medical_terms_found": found_terms,
        "structure_indicators": found_structure,
        "issues": issues,
        "suggestions": suggestions
    }
