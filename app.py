import streamlit as st
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from PIL import Image
import pytesseract
import fitz  # for PDF
import io
import cv2
import numpy as np
from utils.translator import explain_report, get_report_quality_score
import logging
from typing import Optional, Tuple
import base64
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page configuration
st.set_page_config(
    page_title="Radi.AI Care",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile experience
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    
    .language-selector {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-bottom: 2rem;
    }
    
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .result-container {
        background-color: #f0f8ff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffecb5;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        .language-selector {
            flex-direction: column;
            align-items: center;
        }
    }
</style>
""", unsafe_allow_html=True)

# Language configurations
LANGUAGES = {
    "繁體中文": {
        "title": "🩺 Radi.AI Care - 報告翻譯助手",
        "upload_label": "上傳檔案或圖片",
        "upload_help": "請上傳圖片或報告（支援 .jpg, .png, .pdf, .txt）",
        "manual_input": "或直接貼上英文報告：",
        "generate_button": "🔍 生成解說",
        "processing": "AI 正在生成...",
        "uploaded_image": "你上傳的圖片",
        "extracted_text": "提取的文字內容：",
        "warning": "⚠️ 此工具僅供參考，請務必諮詢專業醫師",
        "error_no_content": "❌ 請上傳檔案或輸入報告內容",
        "error_processing": "❌ 處理過程中發生錯誤：",
        "error_ocr": "❌ 圖片文字識別失敗，請嘗試更清晰的圖片",
        "success_message": "✅ 報告解析成功！"
    },
    "简体中文": {
        "title": "🩺 Radi.AI Care - 报告翻译助手",
        "upload_label": "上传文件或图片",
        "upload_help": "请上传图片或报告（支持 .jpg, .png, .pdf, .txt）",
        "manual_input": "或者直接粘贴英文报告：",
        "generate_button": "🔍 生成解说",
        "processing": "AI 正在生成...",
        "uploaded_image": "你上传的图片",
        "extracted_text": "提取的文字内容：",
        "warning": "⚠️ 此工具仅供参考，请务必咨询专业医师",
        "error_no_content": "❌ 请上传文件或输入报告内容",
        "error_processing": "❌ 处理过程中发生错误：",
        "error_ocr": "❌ 图片文字识别失败，请尝试更清晰的图片",
        "success_message": "✅ 报告解析成功！"
    },
    "English": {
        "title": "🩺 Radi.AI Care - Report Translation Assistant",
        "upload_label": "Upload File or Image",
        "upload_help": "Please upload an image or report (supports .jpg, .png, .pdf, .txt)",
        "manual_input": "Or paste your English radiology report directly:",
        "generate_button": "🔍 Generate Explanation",
        "processing": "AI is generating...",
        "uploaded_image": "Your Uploaded Image",
        "extracted_text": "Extracted Text Content:",
        "warning": "⚠️ This tool is for reference only. Please consult a professional physician",
        "error_no_content": "❌ Please upload a file or enter report content",
        "error_processing": "❌ Error occurred during processing: ",
        "error_ocr": "❌ Failed to recognize text from image. Please try a clearer image",
        "success_message": "✅ Report processed successfully!"
    }
}

def initialize_session_state():
    """Initialize session state variables"""
    if "language" not in st.session_state:
        st.session_state.language = "简体中文"

def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for better OCR results"""
    try:
        # Convert PIL Image to numpy array
        img_np = np.array(image)
        
        # Convert to grayscale
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np
            
        # Apply adaptive thresholding for better text extraction
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return Image.fromarray(binary)
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        return image

def extract_text_from_image(image: Image.Image) -> str:
    """Extract text from image using OCR"""
    try:
        # Preprocess image
        processed_image = preprocess_image(image)
        
        # Try multiple OCR configurations
        configs = [
            '--psm 6',  # Single uniform block
            '--psm 4',  # Single column of text
            '--psm 3',  # Default
        ]
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(processed_image, config=config)
                if text.strip():
                    return text.strip()
            except:
                continue
                
        return ""
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return ""

def determine_file_type(filename: str) -> str:
    """Determine file type from filename"""
    filename_lower = filename.lower()
    if filename_lower.endswith('.pdf'):
        return 'pdf'
    elif filename_lower.endswith(('.jpg', '.jpeg', '.png')):
        return 'image'
    elif filename_lower.endswith('.txt'):
        return 'text'
    else:
        return 'unknown'

def process_uploaded_file(uploaded_file) -> Tuple[str, Optional[Image.Image], str]:
    """Process uploaded file and extract text"""
    try:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name.lower()
        file_type = determine_file_type(uploaded_file.name)
        
        if filename.endswith(".txt"):
            text = file_bytes.decode("utf-8")
            return text, None, file_type
                
        elif filename.endswith(".pdf"):
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                text = "\n".join([page.get_text() for page in doc])
                return text, None, file_type
                
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(io.BytesIO(file_bytes))
            text = extract_text_from_image(image)
            return text, image, file_type
        else:
            return "", None, "unknown"
            
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return "", None, "unknown"

def display_language_selector():
    """Display language selection buttons"""
    st.markdown("### 🌐 請選擇語言 / Choose Language")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("繁體中文", key="lang_tc", use_container_width=True):
            st.session_state.language = "繁體中文"
            st.rerun()
    
    with col2:
        if st.button("简体中文", key="lang_sc", use_container_width=True):
            st.session_state.language = "简体中文"
            st.rerun()
    
    with col3:
        if st.button("English", key="lang_en", use_container_width=True):
            st.session_state.language = "English"
            st.rerun()

def display_header():
    """Display app header"""
    # Display logo if exists
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=160)
    
    lang_config = LANGUAGES[st.session_state.language]
    st.markdown(f'<div class="main-header"><h1>{lang_config["title"]}</h1></div>', 
                unsafe_allow_html=True)

def display_disclaimer():
    """Display medical disclaimer"""
    lang_config = LANGUAGES[st.session_state.language]
    st.markdown(f'<div class="warning-box">{lang_config["warning"]}</div>', 
                unsafe_allow_html=True)

def display_main_mode():
    """Display main upload mode"""
    lang_config = LANGUAGES[st.session_state.language]
    report = ""
    uploaded_image = None
    file_type = "manual"
    
    # File upload section
    st.markdown(f'<div class="upload-area">', unsafe_allow_html=True)
    st.subheader(f"📤 {lang_config['upload_label']}")
    
    uploaded_file = st.file_uploader(
        lang_config["upload_help"],
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        key="file_upload"
    )
    
    if uploaded_file:
        with st.spinner(lang_config["processing"]):
            report, uploaded_image, file_type = process_uploaded_file(uploaded_file)
            
            if uploaded_image:
                st.image(uploaded_image, caption=lang_config["uploaded_image"], 
                        use_container_width=True)
            
            if report.strip():
                st.success(lang_config["success_message"])
                
                # Show extracted text in expandable section
                with st.expander(lang_config["extracted_text"]):
                    st.text_area("", value=report, height=150, disabled=True)
            else:
                st.error(lang_config["error_ocr"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Manual input section
    st.markdown("---")
    st.markdown(f"### ✏️ {lang_config['manual_input']}")
    manual_input = st.text_area("", value=report, height=200, key="manual_input", 
                               placeholder="Paste your radiology report here...")
    
    if manual_input:
        report = manual_input
        file_type = "manual"
    
    # Generate explanation button
    if st.button(f"{lang_config['generate_button']}", key="generate_btn", 
                type="primary", use_container_width=True):
        if not report.strip():
            st.error(lang_config["error_no_content"])
        else:
            generate_explanation(report, file_type)

def generate_explanation(report: str, file_type: str = "manual"):
    """Generate AI explanation for the report"""
    lang_config = LANGUAGES[st.session_state.language]
    
    try:
        with st.spinner(lang_config["processing"]):
            # Call the explain_report function
            result, metrics = explain_report(report, st.session_state.language)
            
            # Display the result
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(result, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Log usage silently (no UI feedback)
            try:
                from log_to_sheets import log_to_google_sheets
                log_to_google_sheets(
                    language=st.session_state.language,
                    report_length=len(report),
                    file_type=file_type
                )
            except Exception as log_error:
                # Log error but don't show to user
                logger.warning(f"Failed to log usage: {log_error}")
            
    except Exception as e:
        logger.error(f"Generation error: {e}")
        st.error(f"{lang_config['error_processing']}{str(e)}")
        
        # Log failed attempt silently
        try:
            from log_to_sheets import log_to_google_sheets
            log_to_google_sheets(
                language=st.session_state.language,
                report_length=len(report),
                file_type=file_type
            )
        except Exception as log_error:
            logger.warning(f"Failed to log error: {log_error}")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display language selector
    display_language_selector()
    
    # Display disclaimer
    display_disclaimer()
    
    # Display main upload mode
    display_main_mode()

if __name__ == "__main__":
    main()
