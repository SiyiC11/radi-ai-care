import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import logging
import fitz  # PyMuPDF for PDF
import docx  # python-docx for Word documents
import io
import base64
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="RadiAI.Care - 智能醫療報告助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Multi-language configuration
LANGUAGE_CONFIG = {
    "繁體中文": {
        "code": "traditional_chinese",
        "app_title": "RadiAI.Care",
        "app_subtitle": "🩺 智能醫療報告解讀助手",
        "app_description": "將英文放射科報告轉譯為易懂的中文解釋",
        "lang_selection": "🌍 選擇語言",
        "disclaimer_title": "⚠️ 重要法律聲明",
        "disclaimer_translation": "純翻譯服務：本工具僅提供語言翻譯，絕不提供醫療建議、診斷或治療建議",
        "disclaimer_accuracy": "準確性限制：AI翻譯可能存在錯誤，請務必與專業醫師核實所有醫療資訊",
        "disclaimer_decision": "醫療決策：請勿將翻譯結果用於任何醫療決策，所有醫療問題請諮詢合格醫師",
        "disclaimer_emergency": "緊急情況：如有緊急醫療需求，請立即撥打000或前往最近的急診室",
        "usage_remaining": "剩餘",
        "usage_used": "已用",
        "usage_times": "次",
        "usage_quota_finished": "🎯 免費翻譯額度已用完。感謝您的使用！",
        "usage_quota_info": "如需更多翻譯服務，請聯繫我們了解付費方案。",
        "input_method": "📝 選擇輸入方式",
        "input_text": "✍️ 直接輸入文字",
        "input_file": "📁 上傳文件",
        "input_placeholder": "請將完整的英文放射科報告貼在下方：",
        "input_help": "請貼上您的英文放射科報告，例如：\n\nCHEST CT SCAN\nCLINICAL HISTORY: Shortness of breath\nTECHNIQUE: Axial CT images of the chest...\nFINDINGS: The lungs demonstrate...\nIMPRESSION: ...\n\n請確保包含完整的報告內容以獲得最佳翻譯效果。",
        "file_upload": "📂 選擇您的報告文件",
        "file_formats": "支援的文件格式說明",
        "file_pdf": "📄 PDF - 掃描或電子版報告",
        "file_txt": "📝 TXT - 純文字報告", 
        "file_docx": "📑 DOCX - Word文檔報告",
        "file_success": "✅ 文件讀取成功！",
        "file_preview": "👀 預覽提取的內容",
        "file_content": "內容預覽",
        "file_error": "❌ 文件讀取失敗，請檢查文件格式或嘗試其他文件",
        "translate_button": "🚀 開始智能解讀",
        "error_no_content": "請輸入報告內容或上傳有效文件",
        "error_too_short": "輸入內容太短，請確保輸入完整的醫學報告",
        "warning_no_medical": "內容似乎不包含醫學術語，翻譯結果可能不夠準確",
        "processing_analyze": "🔍 正在分析報告內容...",
        "processing_translate": "🔄 正在翻譯醫學術語...",
        "processing_explain": "💡 正在生成智能解釋...",
        "processing_questions": "❓正在整理建議問題...",
        "result_title": "📋 智能解讀結果",
        "translation_complete": "🎉 解讀完成！您還有",
        "translation_remaining": "次免費翻譯機會",
        "translation_finished": "🌟 您已用完所有免費翻譯！感謝使用 RadiAI.Care",
        "error_occurred": "翻譯過程中發生錯誤：",
        "tab_help": "💡 使用指南",
        "tab_privacy": "🔒 隱私保護",
        "tab_reminder": "⚠️ 重要提醒",
        "help_title": "如何獲得最佳解讀效果？",
        "help_content": "✅ 確保報告內容完整，包含所有段落\n✅ 建議的問題僅供參考，請根據實際情況調整\n✅ 如對翻譯有疑問，請向您的醫師確認",
        "help_support": "🛠️ 技術支援",
        "help_support_content": "本服務處於測試階段，持續改進中\n如遇技術問題，請稍後重試",
        "privacy_title": "您的隱私受到保護",
        "privacy_content": "✅ 不保存任何醫療報告內容\n✅ 翻譯完成後數據立即清除\n✅ 僅記錄匿名使用統計\n⚠️ 請勿在報告中包含身份證號等個人資訊",
        "privacy_processing": "數據處理",
        "privacy_processing_content": "使用加密連接傳輸數據\n符合澳洲隱私法規要求",
        "reminder_title": "再次重要提醒",
        "reminder_content": "🚫 本工具**僅提供翻譯服務**\n🚫 **不提供**診斷、治療建議或醫療意見\n✅ **務必**向專業醫師諮詢所有醫療問題\n🆘 緊急情況請立即撥打 **000**",
        "legal_title": "法律聲明",
        "legal_content": "使用本服務即表示同意上述條款\n所有醫療決策責任歸屬於用戶和其醫療團隊"
    },
    "简体中文": {
        "code": "simplified_chinese",
        "app_title": "RadiAI.Care",
        "app_subtitle": "🩺 智能医疗报告解读助手",
        "app_description": "将英文放射科报告转译为易懂的中文解释",
        "lang_selection": "🌍 选择语言",
        "disclaimer_title": "⚠️ 重要法律声明",
        "disclaimer_translation": "纯翻译服务：本工具仅提供语言翻译，绝不提供医疗建议、诊断或治疗建议",
        "disclaimer_accuracy": "准确性限制：AI翻译可能存在错误，请务必与专业医师核实所有医疗信息",
        "disclaimer_decision": "医疗决策：请勿将翻译结果用于任何医疗决策，所有医疗问题请咨询合格医师",
        "disclaimer_emergency": "紧急情况：如有紧急医疗需求，请立即拨打000或前往最近的急诊室",
        "usage_remaining": "剩余",
        "usage_used": "已用",
        "usage_times": "次",
        "usage_quota_finished": "🎯 免费翻译额度已用完。感谢您的使用！",
        "usage_quota_info": "如需更多翻译服务，请联系我们了解付费方案。",
        "input_method": "📝 选择输入方式",
        "input_text": "✍️ 直接输入文字",
        "input_file": "📁 上传文件",
        "input_placeholder": "请将完整的英文放射科报告贴在下方：",
        "input_help": "请贴上您的英文放射科报告，例如：\n\nCHEST CT SCAN\nCLINICAL HISTORY: Shortness of breath\nTECHNIQUE: Axial CT images of the chest...\nFINDINGS: The lungs demonstrate...\nIMPRESSION: ...\n\n请确保包含完整的报告内容以获得最佳翻译效果。",
        "file_upload": "📂 选择您的报告文件",
        "file_formats": "支持的文件格式说明",
        "file_pdf": "📄 PDF - 扫描或电子版报告",
        "file_txt": "📝 TXT - 纯文字报告", 
        "file_docx": "📑 DOCX - Word文档报告",
        "file_success": "✅ 文件读取成功！",
        "file_preview": "👀 预览提取的内容",
        "file_content": "内容预览",
        "file_error": "❌ 文件读取失败，请检查文件格式或尝试其他文件",
        "translate_button": "🚀 开始智能解读",
        "error_no_content": "请输入报告内容或上传有效文件",
        "error_too_short": "输入内容太短，请确保输入完整的医学报告",
        "warning_no_medical": "内容似乎不包含医学术语，翻译结果可能不够准确",
        "processing_analyze": "🔍 正在分析报告内容...",
        "processing_translate": "🔄 正在翻译医学术语...",
        "processing_explain": "💡 正在生成智能解释...",
        "processing_questions": "❓正在整理建议问题...",
        "result_title": "📋 智能解读结果",
        "translation_complete": "🎉 解读完成！您还有",
        "translation_remaining": "次免费翻译机会",
        "translation_finished": "🌟 您已用完所有免费翻译！感谢使用 RadiAI.Care",
        "error_occurred": "翻译过程中发生错误：",
        "tab_help": "💡 使用指南",
        "tab_privacy": "🔒 隐私保护",
        "tab_reminder": "⚠️ 重要提醒",
        "help_title": "如何获得最佳解读效果？",
        "help_content": "✅ 确保报告内容完整，包含所有段落\n✅ 建议的问题仅供参考，请根据实际情况调整\n✅ 如对翻译有疑问，请向您的医师确认",
        "help_support": "🛠️ 技术支持",
        "help_support_content": "本服务处于测试阶段，持续改进中\n如遇技术问题，请稍后重试",
        "privacy_title": "您的隐私受到保护",
        "privacy_content": "✅ 不保存任何医疗报告内容\n✅ 翻译完成后数据立即清除\n✅ 仅记录匿名使用统计\n⚠️ 请勿在报告中包含身份证号等个人信息",
        "privacy_processing": "数据处理",
        "privacy_processing_content": "使用加密连接传输数据\n符合澳洲隐私法规要求",
        "reminder_title": "再次重要提醒",
        "reminder_content": "🚫 本工具**仅提供翻译服务**\n🚫 **不提供**诊断、治疗建议或医疗意见\n✅ **务必**向专业医师咨询所有医疗问题\n🆘 紧急情况请立即拨打 **000**",
        "legal_title": "法律声明",
        "legal_content": "使用本服务即表示同意上述条款\n所有医疗决策责任归属于用户和其医疗团队"
    }
}

# Initialize session state for language
if 'language' not in st.session_state:
    st.session_state.language = "简体中文"

# Initialize session state for translation count
if 'translation_count' not in st.session_state:
    st.session_state.translation_count = 0

# Get current language configuration
lang = LANGUAGE_CONFIG[st.session_state.language]

# Google Sheets logging (keeping your original structure)
def log_to_google_sheets(language: str, 
                        report_length: int, 
                        file_type: str = "manual",
                        processing_status: str = "success",
                        **kwargs) -> bool:
    """
    Log usage data to your existing Google Sheets
    Using the same sheet ID and structure from your original code
    """
    try:
        # Get base64 encoded secret
        b64_secret = os.environ.get("GOOGLE_SHEET_SECRET_B64")
        if not b64_secret:
            logger.warning("GOOGLE_SHEET_SECRET_B64 environment variable not found")
            return False

        # Decode and parse service account info
        service_account_info = json.loads(base64.b64decode(b64_secret))
        
        # Define scopes and create credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scopes)

        # Initialize client and get sheet
        gspread_client = gspread.authorize(creds)
        sheet_id = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"  # Your original sheet ID
        sheet = gspread_client.open_by_key(sheet_id)
        
        # Use your original worksheet name
        try:
            worksheet = sheet.worksheet("UsageLog")
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title="UsageLog", rows="1000", cols="7")
            # Initialize headers matching your original structure
            headers = [
                "Date & Time",
                "Language", 
                "Report Length",
                "File Type",
                "Session ID",
                "User ID",
                "Processing Status"
            ]
            worksheet.append_row(headers)
        
        # Get Sydney time (your original timezone)
        sydney_tz = pytz.timezone("Australia/Sydney")
        current_datetime = datetime.now(sydney_tz).strftime("%Y-%m-%d %H:%M:%S")
        
        # Create session and user IDs
        session_id = str(uuid.uuid4())[:8]
        user_id = f"user_{str(uuid.uuid4())[:8]}"
        
        # Prepare row data matching your original format
        row_data = [
            current_datetime,    # Date & Time
            language,           # Language
            report_length,      # Report Length  
            file_type,          # File Type
            session_id,         # Session ID
            user_id,            # User ID
            processing_status   # Processing Status
        ]
        
        # Log to worksheet
        worksheet.append_row(row_data)
        
        logger.info(f"Successfully logged usage: {language}, {report_length} chars, {file_type}, {processing_status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log usage: {e}")
        return False

# Enhanced CSS for better mobile and desktop experience
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
    
    /* Base styling */
    .stApp {
        font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Main container */
    .main-container {
        background: white;
        border-radius: 20px;
        margin: 1rem;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        max-width: 800px;
        margin: 1rem auto;
    }
    
    /* Enhanced title section */
    .title-section {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
        border-radius: 15px;
        border: 1px solid #e1e8ff;
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #4a5568;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .description {
        font-size: 1rem;
        color: #718096;
        font-weight: 400;
        max-width: 500px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* Language selection styling */
    .language-section {
        text-align: center;
        margin: 1.5rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 12px;
    }
    
    .language-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    /* Enhanced disclaimer styling */
    .disclaimer-container {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border: 2px solid #ff9800;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
    }
    
    .disclaimer-title {
        text-align: center;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #bf360c;
    }
    
    .disclaimer-item {
        margin-bottom: 0.8rem;
        padding: 0.8rem;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #d84315;
        font-weight: 500;
    }
    
    /* Usage tracking styling */
    .usage-container {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #c8e6c9;
    }
    
    /* Input section styling */
    .input-section {
        background: #f8f9ff;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #e1e8ff;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    /* File upload styling */
    .stFileUploader > div {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #5a67d8;
        background: linear-gradient(135deg, #f0f4ff 0%, #dce7ff 100%);
        transform: translateY(-2px);
    }
    
    /* Result container styling */
    .result-container {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1.5rem 0;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 8px 25px rgba(31, 119, 180, 0.1);
    }
    
    /* Enhanced button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        width: 100%;
        margin: 1rem 0;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e1e8ff;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        padding: 1rem;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        border-radius: 12px;
        border-left: 4px solid #28a745;
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
    }
    
    .stError {
        border-radius: 12px;
        border-left: 4px solid #dc3545;
        background: linear-gradient(135deg, #ffeaea 0%, #fff0f0 100%);
    }
    
    .stWarning {
        border-radius: 12px;
        border-left: 4px solid #ffc107;
        background: linear-gradient(135deg, #fff8e1 0%, #fffbf0 100%);
    }
    
    .stInfo {
        border-radius: 12px;
        border-left: 4px solid #17a2b8;
        background: linear-gradient(135deg, #e1f7fa 0%, #f0fcff 100%);
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.2rem;
        }
        .subtitle {
            font-size: 1.1rem;
        }
        .main-container {
            margin: 0.5rem;
            padding: 1rem;
        }
        .disclaimer-item {
            font-size: 0.9rem;
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46a3 100%);
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded PDF, TXT, or DOCX files"""
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        if file_extension == 'txt':
            # Handle TXT files
            content = uploaded_file.read().decode('utf-8')
            return content
            
        elif file_extension == 'pdf':
            # Handle PDF files
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text()
            pdf_document.close()
            return text
            
        elif file_extension in ['docx', 'doc']:
            # Handle Word documents
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
            
        else:
            return None
            
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        return None

def translate_and_explain_report(report_text, language_code):
    """Enhanced translation with better formatting and explanations"""
    try:
        # Build system prompt based on selected language
        if language_code == "simplified_chinese":
            system_prompt = """你是一位專業的醫學翻譯專家和醫療科普作者。請按照以下格式處理英文放射科報告：

**重要說明：你只提供翻譯和科普解釋服務，絕不提供任何醫療診斷、建議或醫學意見。**

請按以下格式組織回應，使用簡體中文：

## 📋 報告翻譯
[將完整報告翻譯成簡體中文，保持醫學術語的準確性。使用清晰的段落結構，保持原文的邏輯性]

## 🔍 關鍵發現總結
[用3-5個要點總結報告中的主要發現，使用通俗易懂的語言]

## 💡 醫學詞彙解釋
[提取並解釋5-8個關鍵醫學術語，格式如下：]
**術語名稱**：通俗易懂的解釋，說明在這個檢查中的意義

## ❓ 建議向醫生咨詢的問題
[根據報告內容，建議3-5個具體且實用的問題，幫助患者與醫生更好地溝通]

**格式要求：**
- 使用簡體中文
- 醫學術語解釋要通俗易懂，避免過於技術性的描述
- 建議的問題要具體且實用
- 絕對不能包含任何診斷性語言
- 強調所有醫療決策需由專業醫師做出
- 使用清晰的格式和適當的表情符號使內容更易讀"""

        else:  # traditional_chinese
            system_prompt = """你是一位專業的醫學翻譯專家和醫療科普作者。請按照以下格式處理英文放射科報告：

**重要說明：你只提供翻譯和科普解釋服務，絕不提供任何醫療診斷、建議或醫學意見。**

請按以下格式組織回應，使用繁體中文：

## 📋 報告翻譯
[將完整報告翻譯成繁體中文，保持醫學術語的準確性。使用清晰的段落結構，保持原文的邏輯性]

## 🔍 關鍵發現總結
[用3-5個要點總結報告中的主要發現，使用通俗易懂的語言]

## 💡 醫學詞彙解釋
[提取並解釋5-8個關鍵醫學術語，格式如下：]
**術語名稱**：通俗易懂的解釋，說明在這個檢查中的意義

## ❓ 建議向醫師諮詢的問題
[根據報告內容，建議3-5個具體且實用的問題，幫助患者與醫師更好地溝通]

**格式要求：**
- 使用繁體中文
- 醫學術語解釋要通俗易懂，避免過於技術性的描述
- 建議的問題要具體且實用
- 絕對不能包含任何診斷性語言
- 強調所有醫療決策需由專業醫師做出
- 使用清晰的格式和適當的表情符號使內容更易讀"""

        # Use modern OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Using latest and most capable model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請翻譯並解釋以下放射科報告：\n\n{report_text}"}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Add enhanced disclaimer with better formatting
        disclaimer = """
---
<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border: 2px solid #ff9800; border-radius: 12px; padding: 1rem; margin-top: 1.5rem;">
<div style="text-align: center; font-weight: bold; color: #bf360c; margin-bottom: 0.5rem;">⚠️ 重要提醒</div>
<div style="color: #d84315; font-weight: 500; text-align: center;">
以上內容僅為翻譯和科普解釋服務，不構成任何醫療建議。<br>
所有醫療決策請務必諮詢專業醫師。
</div>
</div>
"""
        
        return result + disclaimer
    
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"❌ 翻譯過程中發生錯誤：{str(e)}\n\n請檢查網絡連接或稍後重試。"

def main():
    global lang
    
    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Enhanced title section
    st.markdown(f'''
    <div class="title-section">
        <div class="main-title">{lang["app_title"]}</div>
        <div class="subtitle">{lang["app_subtitle"]}</div>
        <div class="description">{lang["app_description"]}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Language selection
    st.markdown(f'''
    <div class="language-section">
        <div class="language-title">{lang["lang_selection"]}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🇹🇼 繁體中文", 
                    key="lang_traditional",
                    use_container_width=True,
                    type="primary" if st.session_state.language == "繁體中文" else "secondary"):
            st.session_state.language = "繁體中文"
            st.rerun()
    
    with col2:
        if st.button("🇨🇳 简体中文", 
                    key="lang_simplified",
                    use_container_width=True,
                    type="primary" if st.session_state.language == "简体中文" else "secondary"):
            st.session_state.language = "简体中文"
            st.rerun()
    
    # Update language configuration after selection
    lang = LANGUAGE_CONFIG[st.session_state.language]
    
    # Enhanced Disclaimer
    st.markdown(f'''
    <div class="disclaimer-container">
        <div class="disclaimer-title">{lang["disclaimer_title"]}</div>
        <div class="disclaimer-item">
            <strong>🔸 純翻譯服務</strong><br>
            {lang["disclaimer_translation"]}
        </div>
        <div class="disclaimer-item">
            <strong>🔸 準確性限制</strong><br>
            {lang["disclaimer_accuracy"]}
        </div>
        <div class="disclaimer-item">
            <strong>🔸 醫療決策</strong><br>
            {lang["disclaimer_decision"]}
        </div>
        <div class="disclaimer-item">
            <strong>🔸 緊急情況</strong><br>
            {lang["disclaimer_emergency"]}
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Usage tracking with enhanced styling
    MAX_FREE_TRANSLATIONS = 3
    remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
    
    st.markdown('<div class="usage-container">', unsafe_allow_html=True)
    progress = st.session_state.translation_count / MAX_FREE_TRANSLATIONS
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        if remaining > 0:
            st.success(f"✅ {remaining} {lang['usage_times']}")
        else:
            st.error("❌ 已用完")
    with col3:
        st.info(f"📊 {st.session_state.translation_count}/{MAX_FREE_TRANSLATIONS}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if remaining <= 0:
        st.error(f"🚫 {lang['usage_quota_finished']}")
        st.info(f"💡 {lang['usage_quota_info']}")
        st.stop()
    
    # Input method selection
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{lang["input_method"]}</div>', unsafe_allow_html=True)
    
    # Initialize input method in session state
    if 'input_method' not in st.session_state:
        st.session_state.input_method = "text"
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(lang["input_text"], 
                    key="input_text",
                    use_container_width=True,
                    type="primary" if st.session_state.input_method == "text" else "secondary"):
            st.session_state.input_method = "text"
    
    with col2:
        if st.button(lang["input_file"], 
                    key="input_file",
                    use_container_width=True,
                    type="primary" if st.session_state.input_method == "file" else "secondary"):
            st.session_state.input_method = "file"
    
    report_text = ""
    file_type = "manual"
    
    if st.session_state.input_method == "text":
        st.markdown("#### 📝 輸入報告內容")
        report_text = st.text_area(
            lang["input_placeholder"],
            height=250,
            placeholder=lang["input_help"],
            help="💡 支援各種格式的英文放射科報告",
            label_visibility="collapsed"
        )
        
    else:
        st.markdown("#### 📂 上傳報告文件")
        
        # File upload
        uploaded_file = st.file_uploader(
            lang["file_upload"],
            type=['pdf', 'txt', 'docx'],
            help="📋 支援PDF、TXT、Word文檔格式，文件大小限制10MB",
            label_visibility="collapsed"
        )
        
        # File format info
        with st.expander(f"📋 {lang['file_formats']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**{lang['file_pdf']}**", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{lang['file_txt']}**", unsafe_allow_html=True) 
            with col3:
                st.markdown(f"**{lang['file_docx']}**", unsafe_allow_html=True)
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.lower().split('.')[-1]
            
            with st.spinner("🔄 正在讀取文件內容..."):
                extracted_text = extract_text_from_file(uploaded_file)
                
                if extracted_text:
                    report_text = extracted_text
                    st.success(f"✅ {lang['file_success']}")
                    
                    # Preview with better formatting (removed file info display)
                    with st.expander(f"👀 {lang['file_preview']}"):
                        preview_text = extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text
                        st.text_area(lang["file_content"], value=preview_text, height=150, disabled=True)
                        
                else:
                    st.error(f"❌ {lang['file_error']}")
                    file_type = "failed"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced translation button
    if st.button(f"{lang['translate_button']}", type="primary", use_container_width=True):
        if not report_text.strip():
            st.error(f"❌ {lang['error_no_content']}")
        elif len(report_text.strip()) < 20:
            st.error(f"❌ {lang['error_too_short']}")
        else:
            # Medical content validation
            medical_keywords = ['scan', 'ct', 'mri', 'xray', 'x-ray', 'examination', 
                              'findings', 'impression', 'study', 'image', 'report',
                              'clinical', 'patient', 'technique', 'contrast']
            has_medical_content = any(keyword.lower() in report_text.lower() for keyword in medical_keywords)
            
            if not has_medical_content:
                st.warning(f"⚠️ {lang['warning_no_medical']}")
            
            # Enhanced processing with animated progress
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # Enhanced processing steps
                steps = [
                    (lang["processing_analyze"], 25),
                    (lang["processing_translate"], 50), 
                    (lang["processing_explain"], 75),
                    (lang["processing_questions"], 100)
                ]
                
                for step_text, progress_value in steps:
                    status_text.markdown(f"**{step_text}**")
                    progress_bar.progress(progress_value)
                    time.sleep(0.8)
                
                # Perform actual translation
                result = translate_and_explain_report(report_text, lang["code"])
                
                # Clear progress indicators
                progress_container.empty()
                
                # Display result with enhanced formatting
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown(f"### 📋 {lang['result_title']} ({st.session_state.language})")
                st.markdown(result, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Log usage to Google Sheets
                try:
                    input_method_clean = "text_input" if st.session_state.input_method == "text" else "file_upload"
                    log_to_google_sheets(
                        language=st.session_state.language,
                        report_length=len(report_text),
                        file_type=file_type,
                        processing_status="success"
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log usage: {log_error}")
                
                # Update counter
                st.session_state.translation_count += 1
                
                # Show completion status
                new_remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
                if new_remaining > 0:
                    st.success(f"🎉 {lang['translation_complete']} {new_remaining} {lang['translation_remaining']}")
                else:
                    st.balloons()
                    st.success(f"🌟 {lang['translation_finished']}")
                
            except Exception as e:
                progress_container.empty()
                st.error(f"❌ {lang['error_occurred']}{str(e)}")
                
                # Log error
                try:
                    input_method_clean = "text_input" if st.session_state.input_method == "text" else "file_upload"
                    log_to_google_sheets(
                        language=st.session_state.language,
                        report_length=len(report_text),
                        file_type=file_type,
                        processing_status="error"
                    )
                except:
                    pass
    
    # Enhanced Footer with better styling
    st.markdown("---")
    
    # Footer with tabs
    tab1, tab2, tab3 = st.tabs([
        f"{lang['tab_help']}", 
        f"{lang['tab_privacy']}", 
        f"{lang['tab_reminder']}"
    ])
    
    with tab1:
        st.markdown(f"""
        ### {lang['help_title']}
        
        {lang['help_content']}
        
        ### {lang['help_support']}
        
        {lang['help_support_content']}
        """)
    
    with tab2:
        st.markdown(f"""
        ### {lang['privacy_title']}
        
        {lang['privacy_content']}
        
        ### {lang['privacy_processing']}
        
        {lang['privacy_processing_content']}
        """)
    
    with tab3:
        st.markdown(f"""
        ### {lang['reminder_title']}
        
        {lang['reminder_content']}
        
        ### {lang['legal_title']}
        
        {lang['legal_content']}
        """)
    
    # Enhanced version info
    st.markdown(
        '''
        <div style="text-align: center; color: #666; font-size: 0.85rem; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <strong>RadiAI.Care v3.0</strong> | 為澳洲華人社區打造 ❤️<br>
            <small>Powered by GPT-4o | Made with Streamlit</small>
        </div>
        ''', 
        unsafe_allow_html=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close main container

if __name__ == "__main__":
    main()
