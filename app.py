import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import logging
import fitz  # PyMuPDF for PDF
import docx  # python-docx for Word documents
import io
import uuid

# Import custom modules
try:
    from utils.prompt_template import get_prompt, create_enhanced_disclaimer, get_processing_steps
    from log_to_sheets import log_to_google_sheets
except ImportError:
    # Fallback imports for development
    st.error("⚠️ 請確保 utils/prompt_template.py 和 log_to_sheets.py 文件存在")
    st.stop()

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

# Configuration constants
MAX_FREE_TRANSLATIONS = 3
SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'docx']
FILE_SIZE_LIMIT_MB = 10
MIN_TEXT_LENGTH = 20
MEDICAL_KEYWORDS = [
    'scan', 'ct', 'mri', 'xray', 'x-ray', 'examination', 
    'findings', 'impression', 'study', 'image', 'report',
    'clinical', 'patient', 'technique', 'contrast', 'diagnosis',
    'radiology', 'radiologist', 'chest', 'abdomen', 'brain'
]

# Initialize OpenAI client with caching
@st.cache_resource
def get_openai_client():
    """Initialize and cache OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OpenAI API密鑰未設置，請檢查環境變量")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Language configuration
LANGUAGE_CONFIG = {
    "繁體中文": {
        "code": "traditional_chinese",
        "flag":" ",
        "app_title": "RadiAI.Care",
        "app_subtitle": "🩺 智能醫療報告解讀助手",
        "app_description": "將英文放射科報告轉譯為易懂的中文解釋",
        "lang_selection": "🌍 選擇語言",
        "disclaimer_title": "⚠️ 重要法律聲明",
        "disclaimer_items": [
            "純翻譯服務：本工具僅提供語言翻譯，絕不提供醫療建議、診斷或治療建議",
            "準確性限制：AI翻譯可能存在錯誤，請務必與專業醫師核實所有醫療資訊", 
            "醫療決策：請勿將翻譯結果用於任何醫療決策，所有醫療問題請諮詢合格醫師",
            "緊急情況：如有緊急醫療需求，請立即撥打000或前往最近的急診室"
        ],
        "input_method": "📝 選擇輸入方式",
        "input_text": "✍️ 直接輸入文字",
        "input_file": "📁 上傳文件",
        "input_placeholder": "請將完整的英文放射科報告貼在下方：",
        "input_help": "請貼上您的英文放射科報告，例如：\n\nCHEST CT SCAN\nCLINICAL HISTORY: Shortness of breath\nTECHNIQUE: Axial CT images...\nFINDINGS: The lungs demonstrate...\nIMPRESSION: ...\n\n請確保包含完整的報告內容以獲得最佳翻譯效果。",
        "file_upload": "📂 選擇您的報告文件",
        "file_formats": "支援的文件格式",
        "file_pdf": "📄 PDF - 掃描或電子版報告",
        "file_txt": "📝 TXT - 純文字報告", 
        "file_docx": "📑 DOCX - Word文檔報告",
        "file_success": "✅ 文件讀取成功！",
        "file_preview": "👀 預覽提取的內容",
        "file_error": "❌ 文件讀取失敗，請檢查文件格式或嘗試其他文件",
        "translate_button": "🚀 開始智能解讀",
        "result_title": "📋 智能解讀結果",
        "translation_complete": "🎉 解讀完成！您還有",
        "translation_remaining": "次免費翻譯機會",
        "translation_finished": "🌟 您已用完所有免費翻譯！感謝使用 RadiAI.Care",
        "error_no_content": "請輸入報告內容或上傳有效文件",
        "error_too_short": "輸入內容太短，請確保輸入完整的醫學報告",
        "warning_no_medical": "內容似乎不包含醫學術語，翻譯結果可能不夠準確",
        "usage_remaining": "剩餘",
        "usage_used": "已用",
        "usage_times": "次",
        "quota_finished": "🎯 免費翻譯額度已用完。感謝您的使用！",
        "quota_info": "如需更多翻譯服務，請聯繫我們了解付費方案。",
        "tab_help": "💡 使用指南",
        "tab_privacy": "🔒 隱私保護",
        "tab_reminder": "⚠️ 重要提醒"
    },
    "简体中文": {
        "code": "simplified_chinese",
        "flag":" ",
        "app_title": "RadiAI.Care",
        "app_subtitle": "🩺 智能医疗报告解读助手",
        "app_description": "将英文放射科报告转译为易懂的中文解释",
        "lang_selection": "🌍 选择语言",
        "disclaimer_title": "⚠️ 重要法律声明",
        "disclaimer_items": [
            "纯翻译服务：本工具仅提供语言翻译，绝不提供医疗建议、诊断或治疗建议",
            "准确性限制：AI翻译可能存在错误，请务必与专业医师核实所有医疗信息",
            "医疗决策：请勿将翻译结果用于任何医疗决策，所有医疗问题请咨询合格医师",
            "紧急情况：如有紧急医疗需求，请立即拨打000或前往最近的急诊室"
        ],
        "input_method": "📝 选择输入方式",
        "input_text": "✍️ 直接输入文字",
        "input_file": "📁 上传文件",
        "input_placeholder": "请将完整的英文放射科报告贴在下方：",
        "input_help": "请贴上您的英文放射科报告，例如：\n\nCHEST CT SCAN\nCLINICAL HISTORY: Shortness of breath\nTECHNIQUE: Axial CT images...\nFINDINGS: The lungs demonstrate...\nIMPRESSION: ...\n\n请确保包含完整的报告内容以获得最佳翻译效果。",
        "file_upload": "📂 选择您的报告文件",
        "file_formats": "支持的文件格式",
        "file_pdf": "📄 PDF - 扫描或电子版报告",
        "file_txt": "📝 TXT - 纯文字报告", 
        "file_docx": "📑 DOCX - Word文档报告",
        "file_success": "✅ 文件读取成功！",
        "file_preview": "👀 预览提取的内容",
        "file_error": "❌ 文件读取失败，请检查文件格式或尝试其他文件",
        "translate_button": "🚀 开始智能解读",
        "result_title": "📋 智能解读结果",
        "translation_complete": "🎉 解读完成！您还有",
        "translation_remaining": "次免费翻译机会",
        "translation_finished": "🌟 您已用完所有免费翻译！感谢使用 RadiAI.Care",
        "error_no_content": "请输入报告内容或上传有效文件",
        "error_too_short": "输入内容太短，请确保输入完整的医学报告",
        "warning_no_medical": "内容似乎不包含医学术语，翻译结果可能不够准确",
        "usage_remaining": "剩余",
        "usage_used": "已用",
        "usage_times": "次",
        "quota_finished": "🎯 免费翻译额度已用完。感谢您的使用！",
        "quota_info": "如需更多翻译服务，请联系我们了解付费方案。",
        "tab_help": "💡 使用指南",
        "tab_privacy": "🔒 隐私保护",
        "tab_reminder": "⚠️ 重要提醒"
    }
}

def init_session_state():
    """Initialize session state variables"""
    if 'language' not in st.session_state:
        st.session_state.language = "简体中文"
    if 'translation_count' not in st.session_state:
        st.session_state.translation_count = 0
    if 'input_method' not in st.session_state:
        st.session_state.input_method = "text"

def load_css():
    """Load enhanced CSS styling"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #d0e8f2 0%, #ffffff 100%);
            min-height: 100vh;
        }
        
        .main-container {
            background: white;
            border-radius: 20px;
            margin: 1rem auto;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 800px;
        }
        
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
        
        .input-section {
            background: #f8f9ff;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 2px solid #e1e8ff;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
        }
        
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
        
        .result-container {
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
            border-radius: 15px;
            padding: 2rem;
            margin: 1.5rem 0;
            border-left: 5px solid #1f77b4;
            box-shadow: 0 8px 25px rgba(31, 119, 180, 0.1);
        }
        
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
        
        .stProgress > div > div > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
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
        
        @media (max-width: 768px) {
            .main-title { font-size: 2.2rem; }
            .subtitle { font-size: 1.1rem; }
            .main-container { margin: 0.5rem; padding: 1rem; }
            .disclaimer-item { font-size: 0.9rem; }
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
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
    """Extract text from uploaded files with comprehensive error handling"""
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        # Check file size
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        if file_size_mb > FILE_SIZE_LIMIT_MB:
            logger.error(f"File too large: {file_size_mb:.2f}MB")
            return None
        
        if file_extension == 'txt':
            # Handle TXT files with encoding detection
            try:
                content = uploaded_file.read().decode('utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    content = uploaded_file.read().decode('gbk')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    content = uploaded_file.read().decode('big5')
            return content.strip()
            
        elif file_extension == 'pdf':
            # Handle PDF files
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text_parts = []
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            pdf_document.close()
            return "\n\n".join(text_parts).strip() if text_parts else ""
            
        elif file_extension in ['docx', 'doc']:
            # Handle Word documents
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text_parts = []
            
            # Extract paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(" | ".join(row_text))
            
            return "\n".join(text_parts).strip() if text_parts else ""
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            return None
            
    except Exception as e:
        logger.error(f"File extraction error: {e}")
        return None

def validate_medical_content(text):
    """Validate if text contains medical terminology"""
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return False
    
    text_lower = text.lower()
    matching_keywords = [kw for kw in MEDICAL_KEYWORDS if kw in text_lower]
    return len(matching_keywords) >= 2

def translate_report(report_text, language_code):
    """Main translation function with comprehensive error handling"""
    try:
        system_prompt = get_prompt(language_code)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請翻譯並解釋以下放射科報告：\n\n{report_text}"}
            ],
            temperature=0.3,
            max_tokens=2500,
            timeout=30
        )
        
        result = response.choices[0].message.content.strip()
        disclaimer = create_enhanced_disclaimer(language_code)
        
        return result + disclaimer
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            return "❌ API請求過於頻繁，請稍後重試。"
        elif "timeout" in error_msg.lower():
            return "❌ 請求超時，請檢查網絡連接後重試。"
        elif "api" in error_msg.lower():
            return "❌ API服務暫時不可用，請稍後重試。"
        else:
            return f"❌ 翻譯過程中發生錯誤：{error_msg}\n\n請檢查網絡連接或稍後重試。"

def render_language_selection(lang):
    """Render language selection buttons"""
    st.markdown(f'<div style="text-align: center; margin: 1.5rem 0;"><h4>{lang["lang_selection"]}</h4></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"{LANGUAGE_CONFIG['繁體中文']['flag']} 繁體中文", 
                    key="lang_traditional",
                    use_container_width=True,
                    type="primary" if st.session_state.language == "繁體中文" else "secondary"):
            st.session_state.language = "繁體中文"
            st.rerun()
    
    with col2:
        if st.button(f"{LANGUAGE_CONFIG['简体中文']['flag']} 简体中文", 
                    key="lang_simplified",
                    use_container_width=True,
                    type="primary" if st.session_state.language == "简体中文" else "secondary"):
            st.session_state.language = "简体中文"
            st.rerun()

def render_disclaimer(lang):
    """Render enhanced disclaimer section"""
    disclaimer_html = f'''
    <div class="disclaimer-container">
        <div class="disclaimer-title">{lang["disclaimer_title"]}</div>
    '''
    
    for i, item in enumerate(lang["disclaimer_items"], 1):
        disclaimer_html += f'''
        <div class="disclaimer-item">
            <strong>🔸 重要聲明 {i}</strong><br>
            {item}
        </div>
        '''
    
    disclaimer_html += '</div>'
    st.markdown(disclaimer_html, unsafe_allow_html=True)

def render_usage_tracker(lang):
    """Render usage tracking progress"""
    remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
    progress = st.session_state.translation_count / MAX_FREE_TRANSLATIONS
    
    st.markdown(f"### 📊 使用情況追蹤")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        if remaining > 0:
            st.success(f"✅ {remaining} {lang['usage_times']}")
        else:
            st.error("❌ 已用完")
    with col3:
        st.info(f"📈 {st.session_state.translation_count}/{MAX_FREE_TRANSLATIONS}")
    
    return remaining

def render_input_section(lang):
    """Render input method selection and content input"""
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown(f'### {lang["input_method"]}')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(lang["input_text"], 
                    key="input_text_btn",
                    use_container_width=True,
                    type="primary" if st.session_state.input_method == "text" else "secondary"):
            st.session_state.input_method = "text"
    
    with col2:
        if st.button(lang["input_file"], 
                    key="input_file_btn",
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
        
        uploaded_file = st.file_uploader(
            lang["file_upload"],
            type=SUPPORTED_FILE_TYPES,
            help=f"📋 支援{', '.join([t.upper() for t in SUPPORTED_FILE_TYPES])}格式，文件大小限制{FILE_SIZE_LIMIT_MB}MB",
            label_visibility="collapsed"
        )
        
        # File format info
        with st.expander(f"📋 {lang['file_formats']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**{lang['file_pdf']}**")
            with col2:
                st.markdown(f"**{lang['file_txt']}**") 
            with col3:
                st.markdown(f"**{lang['file_docx']}**")
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.lower().split('.')[-1]
            
            with st.spinner("🔄 正在讀取文件內容..."):
                extracted_text = extract_text_from_file(uploaded_file)
                
                if extracted_text:
                    report_text = extracted_text
                    st.success(f"✅ {lang['file_success']}")
                    
                    with st.expander(f"👀 {lang['file_preview']}"):
                        preview_text = extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text
                        st.text_area("內容預覽", value=preview_text, height=150, disabled=True)
                else:
                    st.error(f"❌ {lang['file_error']}")
                    file_type = "failed"
    
    st.markdown('</div>', unsafe_allow_html=True)
    return report_text, file_type

def render_translation_process(report_text, file_type, lang):
    """Handle translation process with progress indication"""
    if not report_text.strip():
        st.error(f"❌ {lang['error_no_content']}")
        return False
    
    if len(report_text.strip()) < MIN_TEXT_LENGTH:
        st.error(f"❌ {lang['error_too_short']}")
        return False
    
    # Medical content validation
    if not validate_medical_content(report_text):
        st.warning(f"⚠️ {lang['warning_no_medical']}")
    
    # Processing with animated progress
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        # Get processing steps
        steps = get_processing_steps(lang["code"])
        
        for i, step_text in enumerate(steps):
            status_text.markdown(f"**{step_text}**")
            progress_bar.progress((i + 1) * 20)
            time.sleep(0.8)
        
        # Perform translation
        result = translate_report(report_text, lang["code"])
        
        # Clear progress indicators
        progress_container.empty()
        
        # Display result
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown(f"### {lang['result_title']} ({st.session_state.language})")
        st.markdown(result, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Log usage
        try:
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
            st.success(f"{lang['translation_complete']} {new_remaining} {lang['translation_remaining']}")
        else:
            st.balloons()
            st.success(f"{lang['translation_finished']}")
        
        return True
        
    except Exception as e:
        progress_container.empty()
        st.error(f"❌ 翻譯過程中發生錯誤：{str(e)}")
        
        # Log error
        try:
            log_to_google_sheets(
                language=st.session_state.language,
                report_length=len(report_text),
                file_type=file_type,
                processing_status="error"
            )
        except Exception:
            pass
        
        return False

def render_footer_tabs(lang):
    """Render footer information tabs"""
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs([
        f"{lang['tab_help']}", 
        f"{lang['tab_privacy']}", 
        f"{lang['tab_reminder']}"
    ])
    
    with tab1:
        st.markdown("""
        ### 如何獲得最佳解讀效果？
        
        ✅ **完整報告**：確保報告內容完整，包含所有段落和sections  
        ✅ **清晰圖片**：如果上傳圖片，請確保文字清晰可見  
        ✅ **正確格式**：支援PDF、TXT、DOCX格式文件  
        ✅ **參考建議**：翻譯結果中的建議問題僅供參考，請根據實際情況調整  
        ✅ **醫師確認**：如對翻譯有疑問，請向您的醫師確認
        
        ### 🛠️ 技術支援
        
        📞 **服務狀態**：本服務處於測試階段，持續改進中  
        🔄 **問題處理**：如遇技術問題，請稍後重試  
        📧 **意見反饋**：歡迎提供使用建議和意見反饋
        """)
    
    with tab2:
        st.markdown("""
        ### 您的隱私受到全面保護
        
        🔒 **數據安全**  
        ✅ 不保存任何醫療報告內容  
        ✅ 翻譯完成後數據立即清除  
        ✅ 僅記錄匿名使用統計以改進服務  
        ✅ 所有數據傳輸均使用加密連接
        
        ⚠️ **隱私提醒**  
        🚫 請勿在報告中包含身份證號、醫保號等個人敏感信息  
        🚫 建議移除患者姓名、地址等可識別信息  
        ✅ 本工具專注於醫學內容翻譯，不需要個人身份信息
        
        ### 📋 法規合規
        
        ✅ 符合澳洲隱私法規要求  
        ✅ 遵循GDPR數據保護標準  
        ✅ 符合醫療數據處理最佳實踐
        """)
    
    with tab3:
        st.markdown("""
        ### 🚨 再次重要提醒
        
        **關於本工具的功能範圍：**
        
        ✅ **我們提供**：英文放射科報告的中文翻譯和通俗解釋  
        ✅ **我們提供**：醫學術語的科普解釋  
        ✅ **我們提供**：建議向醫師諮詢的問題清單
        
        🚫 **我們不提供**：任何醫療診斷或診斷建議  
        🚫 **我們不提供**：治療方案或醫療決策建議  
        🚫 **我們不提供**：醫療意見或健康指導  
        🚫 **我們不提供**：緊急醫療服務
        
        ### ⚕️ 醫療安全提醒
        
        🏥 **專業諮詢**：所有醫療問題務必諮詢合格醫師  
        🆘 **緊急情況**：如有緊急醫療需求，請立即撥打 **000**  
        📞 **健康熱線**：如需健康咨詢，請聯繫當地醫療機構  
        ⚖️ **法律責任**：所有醫療決策責任歸屬於用戶和其醫療團隊
        
        ### 📄 服務條款
        
        使用本服務即表示您已閱讀、理解並同意上述所有條款和聲明。
        """)

def main():
    """Main application function with comprehensive error handling"""
    try:
        # Initialize session state
        init_session_state()
        
        # Load CSS
        load_css()
        
        # Get current language configuration
        lang = LANGUAGE_CONFIG[st.session_state.language]
        
        # Main container
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Title section
        st.markdown(f'''
        <div class="title-section">
            <div class="main-title">{lang["app_title"]}</div>
            <div class="subtitle">{lang["app_subtitle"]}</div>
            <div class="description">{lang["app_description"]}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Language selection
        render_language_selection(lang)
        
        # Update language configuration after selection
        lang = LANGUAGE_CONFIG[st.session_state.language]
        
        # Disclaimer
        render_disclaimer(lang)
        
        # Usage tracking
        remaining = render_usage_tracker(lang)
        
        if remaining <= 0:
            st.error(f"🚫 {lang['quota_finished']}")
            st.info(f"💡 {lang['quota_info']}")
            st.stop()
        
        # Input section
        report_text, file_type = render_input_section(lang)
        
        # Translation button and process
        if st.button(f"{lang['translate_button']}", type="primary", use_container_width=True):
            render_translation_process(report_text, file_type, lang)
        
        # Footer tabs
        render_footer_tabs(lang)
        
        # Version info
        st.markdown(
            '''
            <div style="text-align: center; color: #666; font-size: 0.85rem; margin-top: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;">
                <strong>RadiAI.Care v3.1 Final</strong> | 為澳洲華人社區打造 ❤️<br>
                <small>Powered by GPT-4o | Built with Streamlit | Made with ❤️</small>
            </div>
            ''', 
            unsafe_allow_html=True
        )
        
        # Close main container
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ 應用程序發生錯誤：{str(e)}")
        st.error("請刷新頁面或稍後重試。如問題持續，請聯繫技術支援。")

if __name__ == "__main__":
    main()
