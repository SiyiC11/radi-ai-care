import openai
import time
import logging
from typing import Optional, Dict, Any
from utils.prompt_template import get_prompt

logger = logging.getLogger(__name__)

class TranslatorError(Exception):
    """Custom exception for translator errors"""
    pass

def validate_report(report: str) -> bool:
    """Validate if the report contains meaningful content"""
    if not report or not report.strip():
        return False
    
    # Check if report is too short (likely OCR error)
    if len(report.strip()) < 10:
        return False
    
    # Check if report contains some medical-related keywords
    medical_keywords = [
        'scan', 'image', 'finding', 'examination', 'study', 'patient',
        'impression', 'conclusion', 'recommendation', 'normal', 'abnormal',
        'radiology', 'ct', 'mri', 'xray', 'x-ray', 'ultrasound'
    ]
    
    report_lower = report.lower()
    has_medical_content = any(keyword in report_lower for keyword in medical_keywords)
    
    return has_medical_content

def clean_report(report: str) -> str:
    """Clean and preprocess the report text"""
    if not report:
        return ""
    
    # Remove excessive whitespace
    cleaned = ' '.join(report.split())
    
    # Remove common OCR artifacts
    artifacts_to_remove = [
        '|', '~', '`', '§', '±', '°', '¿', '¡'
    ]
    
    for artifact in artifacts_to_remove:
        cleaned = cleaned.replace(artifact, '')
    
    # Fix common OCR character substitutions
    substitutions = {
        '0': 'o',  # Only in specific contexts
        '1': 'l',  # Only in specific contexts  
        '5': 's',  # Only in specific contexts
        '8': 'B',  # Only in specific contexts
    }
    
    # Apply substitutions carefully to avoid breaking numbers
    # This is a simplified approach - in practice, you'd want more sophisticated logic
    
    return cleaned.strip()

def create_chat_completion(messages: list, model: str = "gpt-4o", max_retries: int = 3) -> Optional[str]:
    """Create chat completion with retry logic"""
    
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=2000,
                timeout=30
            )
            
            if response and "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                if content and content.strip():
                    return content.strip()
                else:
                    logger.warning(f"Empty response from OpenAI on attempt {attempt + 1}")
            
        except openai.error.RateLimitError as e:
            logger.warning(f"Rate limit exceeded on attempt {attempt + 1}, waiting...")
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except openai.error.APIError as e:
            logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
            time.sleep(1)
            
        except openai.error.Timeout as e:
            logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            time.sleep(1)
    
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
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem;">{line}</h3>')
            elif line.startswith('【') and line.endswith('】'):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem;">{line}</h3>')
            elif line.startswith('## '):
                formatted_lines.append(f'<h3 style="color: #1f77b4; margin-top: 1.5rem;">{line[3:]}</h3>')
            elif line.startswith('# '):
                formatted_lines.append(f'<h2 style="color: #1f77b4; margin-top: 1.5rem;">{line[2:]}</h2>')
            elif line.startswith('- '):
                formatted_lines.append(f'<p style="margin-left: 1rem;">• {line[2:]}</p>')
            else:
                formatted_lines.append(f'<p style="margin-bottom: 1rem;">{line}</p>')
        
        return '\n'.join(formatted_lines)
    
    return explanation

def add_safety_disclaimer(explanation: str, language: str) -> str:
    """Add safety disclaimer to the explanation"""
    disclaimers = {
        "繁體中文": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1rem;'><strong>⚠️ 重要提醒：</strong>此解釋僅供參考，不能取代專業醫療建議。請務必與您的醫師討論報告內容和後續治療計劃。</div>",
        "简体中文": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1rem;'><strong>⚠️ 重要提醒：</strong>此解释仅供参考，不能替代专业医疗建议。请务必与您的医师讨论报告内容和后续治疗计划。</div>",
        "English": "\n\n<div style='border: 2px solid #ff9800; background-color: #fff3e0; padding: 1rem; border-radius: 8px; margin-top: 1rem;'><strong>⚠️ Important Notice:</strong> This explanation is for reference only and cannot replace professional medical advice. Please discuss the report content and follow-up treatment plans with your physician.</div>"
    }
    
    disclaimer = disclaimers.get(language, disclaimers["简体中文"])
    return explanation + disclaimer

def explain_report(report: str, language: str) -> str:
    """
    Main function to explain radiology report
    
    Args:
        report: The radiology report text
        language: Target language for explanation
        
    Returns:
        Formatted explanation string
        
    Raises:
        TranslatorError: If translation fails
    """
    try:
        # Validate inputs
        if not report or not report.strip():
            raise TranslatorError("Empty report provided")
        
        if language not in ["繁體中文", "简体中文", "English"]:
            raise TranslatorError(f"Unsupported language: {language}")
        
        # Clean and validate report
        cleaned_report = clean_report(report)
        
        if not validate_report(cleaned_report):
            # Try to provide a helpful message based on language
            if language == "繁體中文":
                return "<p>❌ 無法識別有效的醫學報告內容。請確認上傳的是完整的放射科報告，並且圖片清晰可讀。</p>"
            elif language == "简体中文":
                return "<p>❌ 无法识别有效的医学报告内容。请确认上传的是完整的放射科报告，并且图片清晰可读。</p>"
            else:
                return "<p>❌ Unable to identify valid medical report content. Please ensure you've uploaded a complete radiology report and that the image is clear and readable.</p>"
        
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
        
        logger.info(f"Successfully generated explanation for {language} language")
        return final_explanation
        
    except TranslatorError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in explain_report: {e}")
        raise TranslatorError(f"Failed to process report: {str(e)}")

def get_usage_stats() -> Dict[str, Any]:
    """Get usage statistics (placeholder for future implementation)"""
    return {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_response_time": 0
    }
