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
    page_title="RadiAI.Care - 你的放射報告翻譯助手",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Language options
LANGUAGES = {
    "簡體中文": "simplified_chinese",
    "繁體中文": "traditional_chinese"
}

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Base styling */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header h3 {
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.95;
        margin-bottom: 0;
    }
    
    /* Mobile responsive header */
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem 1rem;
        }
        .main-header h1 {
            font-size: 1.8rem;
        }
        .main-header h3 {
            font-size: 1rem;
        }
    }
    
    /* Language selector styling */
    .language-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    
    /* Disclaimer box */
    .disclaimer-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        color: #856404;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.2);
    }
    
    /* Input sections */
    .input-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* File upload area */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #5a67d8;
        background: #f0f4ff;
    }
    
    /* Result container */
    .result-container {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1.5rem 0;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 8px 25px rgba(31, 119, 180, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Info boxes */
    .stInfo {
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
    }
    
    .stSuccess {
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
    
    .stError {
        border-radius: 10px;
        border-left: 4px solid #dc3545;
    }
    
    .stWarning {
        border-radius: 10px;
        border-left: 4px solid #ffc107;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    /* Footer styling */
    .footer-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 2rem;
        border: 1px solid #e9ecef;
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main-container {
            padding: 0.5rem;
        }
        
        .disclaimer-box, .input-section, .result-container {
            margin: 1rem 0;
            padding: 1rem;
        }
        
        .stButton > button {
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
        }
        
        .stRadio > div {
            flex-direction: column;
        }
    }
    
    /* Loading spinner customization */
    .stSpinner > div {
        border-top-color: #667eea;
    }
    
    /* Hide Streamlit menu and footer */
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
        background: #c1c1c1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #a8a8a8;
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

def translate_and_explain_report(report_text, language):
    """Enhanced translation with key terms explanation and suggested questions using modern OpenAI API"""
    try:
        # Build system prompt based on selected language
        if language == "simplified_chinese":
            system_prompt = """你是一位專業的醫學翻譯專家。請按照以下格式處理英文放射科報告：

**重要說明：你只提供翻譯服務，絕不提供任何醫療診斷、建議或醫學意見。**

請按以下格式組織回應：

## 📋 中文翻譯
[將完整報告翻譯成簡體中文，保持醫學術語的準確性]

## 🔍 重點医学词汇解释
[提取報告中的5-8個關鍵醫學術語，用簡單語言解釋其含義，幫助患者理解]

## ❓ 建議咨詢醫生的問題
[根據報告內容，建議3-5個患者可以向醫生詢問的問題，幫助患者更好地與醫生溝通]

**格式要求：**
- 使用簡體中文
- 醫學術語解釋要通俗易懂
- 建議的問題要具體且實用
- 絕對不能包含任何診斷性語言
- 強調所有醫療決策需由專業醫師做出"""

        else:  # traditional_chinese
            system_prompt = """你是一位專業的醫學翻譯專家。請按照以下格式處理英文放射科報告：

**重要說明：你只提供翻譯服務，絕不提供任何醫療診斷、建議或醫學意見。**

請按以下格式組織回應：

## 📋 中文翻譯
[將完整報告翻譯成繁體中文，保持醫學術語的準確性]

## 🔍 重點醫學詞彙解釋
[提取報告中的5-8個關鍵醫學術語，用簡單語言解釋其含義，幫助患者理解]

## ❓ 建議諮詢醫師的問題
[根據報告內容，建議3-5個患者可以向醫師詢問的問題，幫助患者更好地與醫師溝通]

**格式要求：**
- 使用繁體中文
- 醫學術語解釋要通俗易懂
- 建議的問題要具體且實用
- 絕對不能包含任何診斷性語言
- 強調所有醫療決策需由專業醫師做出"""

        # Use modern OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Using latest and most capable model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請翻譯並解釋以下放射科報告：\n\n{report_text}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content.strip()
        
        # Add additional disclaimer
        disclaimer = "\n\n---\n**⚠️ 重要提醒：以上內容僅為翻譯服務，不構成任何醫療建議。所有醫療決策請諮詢專業醫師。**"
        
        return result + disclaimer
    
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return f"翻譯過程中發生錯誤：{str(e)}\n\n請檢查網絡連接或稍後重試。"

def main():
    # Header with enhanced styling
    st.markdown('''
    <div class="main-header">
        <h1>🩺 RadiAI.Care</h1>
        <h3>你的放射報告翻譯助手</h3>
    </div>
    ''', unsafe_allow_html=True)
    
    # Language Selection with enhanced styling
    st.markdown('<div class="language-section">', unsafe_allow_html=True)
    st.markdown("### 🌐 選擇輸出語言")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_language = st.selectbox(
            "請選擇您偏好的中文輸出：",
            options=list(LANGUAGES.keys()),
            index=0,
            help="選擇翻譯結果的中文類型"
        )
    
    with col2:
        # Show some stats if available
        if 'translation_count' in st.session_state:
            st.metric("本次使用次數", st.session_state.translation_count)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Disclaimer
    disclaimer_text = """
    <div class="disclaimer-box">
        <div style="text-align: center; margin-bottom: 1rem;">
            <strong>⚠️ 重要法律聲明</strong>
        </div>
        
        <div style="display: grid; gap: 0.8rem;">
            <div>🔹 <strong>純翻譯服務</strong>：本工具僅提供語言翻譯，絕不提供醫療建議、診斷或治療建議</div>
            <div>🔹 <strong>準確性限制</strong>：AI翻譯可能存在錯誤，請務必與專業醫師核實所有醫療資訊</div>
            <div>🔹 <strong>醫療決策</strong>：請勿將翻譯結果用於任何醫療決策，所有醫療問題請諮詢合格醫師</div>
            <div>🔹 <strong>緊急情況</strong>：如有緊急醫療需求，請立即撥打000或前往最近的急診室</div>
        </div>
    </div>
    """
    
    st.markdown(disclaimer_text, unsafe_allow_html=True)
    
    # Usage tracking and limits
    if 'translation_count' not in st.session_state:
        st.session_state.translation_count = 0
    
    MAX_FREE_TRANSLATIONS = 3
    remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
    
    # Progress bar for usage
    progress = st.session_state.translation_count / MAX_FREE_TRANSLATIONS
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        if remaining > 0:
            st.success(f"剩餘: {remaining} 次")
        else:
            st.error("額度用完")
    with col3:
        st.info(f"已用: {st.session_state.translation_count}/{MAX_FREE_TRANSLATIONS}")
    
    if remaining <= 0:
        st.error("🚫 免費翻譯額度已用完。感謝您的使用！")
        st.info("💡 如需更多翻譯服務，請聯繫我們了解付費方案。")
        st.stop()
    
    # Input method selection with enhanced UI
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown("### 📝 選擇輸入方式")
    
    input_method = st.radio(
        "請選擇您偏好的輸入方式：",
        ["✍️ 直接輸入文字", "📁 上傳文件"],
        horizontal=True,
        help="您可以直接貼上報告文字，或上傳PDF、Word、TXT文件"
    )
    
    report_text = ""
    file_type = "manual"
    
    if input_method == "✍️ 直接輸入文字":
        st.markdown("#### 📋 輸入您的英文放射科報告")
        report_text = st.text_area(
            "請將完整的英文放射科報告貼在下方：",
            height=200,
            placeholder="""請貼上您的英文放射科報告，例如：

CHEST CT SCAN
CLINICAL HISTORY: Shortness of breath
TECHNIQUE: Axial CT images of the chest...
FINDINGS: The lungs demonstrate...
IMPRESSION: ...

請確保包含完整的報告內容以獲得最佳翻譯效果。""",
            help="支援各種格式的英文放射科報告"
        )
        
    else:
        st.markdown("#### 📂 上傳報告文件")
        
        # File upload with enhanced styling
        uploaded_file = st.file_uploader(
            "選擇您的報告文件",
            type=['pdf', 'txt', 'docx'],
            help="支援PDF、TXT、Word文檔格式，文件大小限制10MB",
            label_visibility="collapsed"
        )
        
        # File format info
        with st.expander("📋 支援的文件格式說明"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📄 PDF**<br>掃描或電子版報告", unsafe_allow_html=True)
            with col2:
                st.markdown("**📝 TXT**<br>純文字報告", unsafe_allow_html=True) 
            with col3:
                st.markdown("**📑 DOCX**<br>Word文檔報告", unsafe_allow_html=True)
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.lower().split('.')[-1]
            
            with st.spinner("🔄 正在讀取文件內容..."):
                extracted_text = extract_text_from_file(uploaded_file)
                
                if extracted_text:
                    report_text = extracted_text
                    
                    # File info display
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("文件大小", f"{len(uploaded_file.getvalue())/1024:.1f} KB")
                    with col2:
                        st.metric("提取字符", f"{len(extracted_text):,}")
                    with col3:
                        st.metric("文件類型", file_type.upper())
                    
                    st.success("✅ 文件讀取成功！")
                    
                    # Preview with better formatting
                    with st.expander("👀 預覽提取的內容"):
                        preview_text = extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text
                        st.text_area("內容預覽", value=preview_text, height=150, disabled=True)
                        
                else:
                    st.error("❌ 文件讀取失敗，請檢查文件格式或嘗試其他文件")
                    file_type = "failed"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Translation button with enhanced styling
    st.markdown("### 🚀 開始翻譯")
    
    if st.button("🔄 翻譯並解釋報告", type="primary", use_container_width=True):
        if not report_text.strip():
            st.error("❌ 請輸入報告內容或上傳有效文件")
        elif len(report_text.strip()) < 20:
            st.error("❌ 輸入內容太短，請確保輸入完整的醫學報告")
        else:
            # Medical content validation
            medical_keywords = ['scan', 'ct', 'mri', 'xray', 'x-ray', 'examination', 
                              'findings', 'impression', 'study', 'image', 'report',
                              'clinical', 'patient', 'technique', 'contrast']
            has_medical_content = any(keyword.lower() in report_text.lower() for keyword in medical_keywords)
            
            if not has_medical_content:
                st.warning("⚠️ 內容似乎不包含醫學術語，翻譯結果可能不夠準確")
            
            # Processing with animated progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Simulate processing steps
                for i, step in enumerate(["正在分析報告內容...", "正在翻譯醫學術語...", "正在生成解釋...", "正在整理建議問題..."]):
                    status_text.text(step)
                    progress_bar.progress((i + 1) * 25)
                    time.sleep(0.5)
                
                # Perform actual translation
                result = translate_and_explain_report(report_text, LANGUAGES[selected_language])
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display result with enhanced formatting
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown(f"### 📋 翻譯結果 ({selected_language})")
                st.markdown(result)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Log usage to Google Sheets (using your original function)
                try:
                    input_method_clean = "text_input" if input_method == "✍️ 直接輸入文字" else "file_upload"
                    log_to_google_sheets(
                        language=selected_language,
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
                    st.success(f"🎉 翻譯完成！您還有 {new_remaining} 次免費翻譯機會")
                else:
                    st.balloons()
                    st.info("🌟 您已用完所有免費翻譯！感謝使用 RadiAI.Care")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ 翻譯過程中發生錯誤：{str(e)}")
                
                # Log error
                try:
                    input_method_clean = "text_input" if input_method == "✍️ 直接輸入文字" else "file_upload"
                    log_to_google_sheets(
                        language=selected_language,
                        report_length=len(report_text),
                        file_type=file_type,
                        processing_status="error"
                    )
                except:
                    pass
    
    # Enhanced Footer
    st.markdown("---")
    st.markdown('<div class="footer-section">', unsafe_allow_html=True)
    
    # Footer with tabs
    tab1, tab2, tab3 = st.tabs(["📞 需要幫助", "🔒 隱私保護", "⚠️ 重要提醒"])
    
    with tab1:
        st.markdown("""
        **如何獲得最佳翻譯效果？**
        - 確保報告內容完整，包含所有段落
        - 建議的問題僅供參考，請根據實際情況調整
        - 如對翻譯有疑問，請向您的醫師確認
        
        **技術支援**
        - 本服務處於測試階段，持續改進中
        - 如遇技術問題，請稍後重試
        """)
    
    with tab2:
        st.markdown("""
        **您的隱私受到保護**
        - ✅ 不保存任何醫療報告內容
        - ✅ 翻譯完成後數據立即清除
        - ✅ 僅記錄匿名使用統計
        - ⚠️ 請勿在報告中包含身份證號等個人資訊
        
        **數據處理**
        - 使用加密連接傳輸數據
        - 符合澳洲隱私法規要求
        """)
    
    with tab3:
        st.markdown("""
        **再次重要提醒**
        - 🚫 本工具**僅提供翻譯服務**
        - 🚫 **不提供**診斷、治療建議或醫療意見
        - ✅ **務必**向專業醫師諮詢所有醫療問題
        - 🆘 緊急情況請立即撥打 **000**
        
        **法律聲明**
        - 使用本服務即表示同意上述條款
        - 所有醫療決策責任歸屬於用戶和其醫療團隊
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Version info (small)
    st.markdown(
        '<div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">'
        'RadiAI.Care MVP v2.0 | Made with ❤️ for the Australian Chinese Community'
        '</div>', 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
