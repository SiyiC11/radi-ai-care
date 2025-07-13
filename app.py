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
    
    .stats-container {
        background-color: #e8f5e8;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
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
        "success_message": "✅ 報告解析成功！",
        "file_size_info": "檔案大小：",
        "processing_time": "處理時間：",
        "characters_extracted": "提取字符數：",
        "stats_title": "📊 使用統計"
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
        "success_message": "✅ 报告解析成功！",
        "file_size_info": "文件大小：",
        "processing_time": "处理时间：",
        "characters_extracted": "提取字符数：",
        "stats_title": "📊 使用统计"
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
        "success_message": "✅ Report processed successfully!",
        "file_size_info": "File size: ",
        "processing_time": "Processing time: ",
        "characters_extracted": "Characters extracted: ",
        "stats_title": "📊 Usage Statistics"
    }
}

def initialize_session_state():
    """Initialize session state variables"""
    if "language" not in st.session_state:
        st.session_state.language = "简体中文"
    if "processed_report" not in st.session_state:
        st.session_state.processed_report = ""
    if "processing_history" not in st.session_state:
        st.session_state.processing_history = []
    if "total_characters_processed" not in st.session_state:
        st.session_state.total_characters_processed = 0

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

def get_file_size_mb(file_bytes: bytes) -> float:
    """Get file size in MB"""
    return len(file_bytes) / (1024 * 1024)

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

def process_uploaded_file(uploaded_file) -> Tuple[str, Optional[Image.Image], dict]:
    """Process uploaded file and extract text with metadata"""
    start_time = time.time()
    file_info = {
        'filename': uploaded_file.name,
        'file_type': determine_file_type(uploaded_file.name),
        'file_size_mb': 0,
        'processing_time_ms': 0,
        'ocr_used': False,
        'characters_extracted': 0
    }
    
    try:
        file_bytes = uploaded_file.read()
        file_info['file_size_mb'] = get_file_size_mb(file_bytes)
        
        filename = uploaded_file.name.lower()
        
        if filename.endswith(".txt"):
            text = file_bytes.decode("utf-8")
            file_info['characters_extracted'] = len(text)
            
        elif filename.endswith(".pdf"):
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                text = "\n".join([page.get_text() for page in doc])
                file_info['characters_extracted'] = len(text)
                
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(io.BytesIO(file_bytes))
            text = extract_text_from_image(image)
            file_info['ocr_used'] = True
            file_info['characters_extracted'] = len(text)
            
            processing_time = (time.time() - start_time) * 1000
            file_info['processing_time_ms'] = int(processing_time)
            
            return text, image, file_info
            
        else:
            text = ""
            
        processing_time = (time.time() - start_time) * 1000
        file_info['processing_time_ms'] = int(processing_time)
        
        return text, None, file_info
            
    except Exception as e:
        logger.error(f"File processing error: {e}")
        processing_time = (time.time() - start_time) * 1000
        file_info['processing_time_ms'] = int(processing_time)
        return "", None, file_info

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

def display_file_info(file_info: dict, lang_config: dict):
    """Display file processing information"""
    if file_info and any(file_info.values()):
        st.markdown("---")
        st.markdown("### 📄 文件信息")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if file_info.get('file_size_mb'):
                st.info(f"{lang_config['file_size_info']}{file_info['file_size_mb']:.2f} MB")
            if file_info.get('characters_extracted'):
                st.info(f"{lang_config['characters_extracted']}{file_info['characters_extracted']}")
        
        with col2:
            if file_info.get('processing_time_ms'):
                st.info(f"{lang_config['processing_time']}{file_info['processing_time_ms']} ms")
            if file_info.get('ocr_used'):
                st.info("🔍 OCR 文字識別已使用")

def display_main_mode():
    """Display main upload mode"""
    lang_config = LANGUAGES[st.session_state.language]
    report = ""
    uploaded_image = None
    file_info = {}
    
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
            report, uploaded_image, file_info = process_uploaded_file(uploaded_file)
            
            if uploaded_image:
                st.image(uploaded_image, caption=lang_config["uploaded_image"], 
                        use_container_width=True)
            
            # Display file processing info
            display_file_info(file_info, lang_config)
            
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
    
    # Generate explanation button
    if st.button(f"{lang_config['generate_button']}", key="generate_btn", 
                type="primary", use_container_width=True):
        if not report.strip():
            st.error(lang_config["error_no_content"])
        else:
            generate_explanation(report, file_info)

def generate_explanation(report: str, file_info: dict = None):
    """Generate AI explanation for the report with enhanced logging"""
    lang_config = LANGUAGES[st.session_state.language]
    
    try:
        start_time = time.time()
        
        with st.spinner(lang_config["processing"]):
            # Get quality score for the report
            quality_info = get_report_quality_score(report)
            
            # Show quality assessment if score is low
            if quality_info["score"] < 70:
                st.warning(f"⚠️ Report quality score: {quality_info['score']}/100")
                if quality_info["suggestions"]:
                    with st.expander("💡 Quality Improvement Suggestions"):
                        for suggestion in quality_info["suggestions"]:
                            st.write(f"• {suggestion}")
            
            # Call the enhanced explain_report function
            result, metrics = explain_report(report, st.session_state.language)
            
            total_processing_time_ms = int((time.time() - start_time) * 1000)
            
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(result, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enhanced logging with comprehensive metrics
            try:
                from log_to_sheets import log_to_google_sheets
                
                # Prepare comprehensive logging data
                log_data = {
                    'language': st.session_state.language,
                    'report_length': len(report),
                    'processing_time_ms': total_processing_time_ms,
                    'ai_response_time_ms': metrics.get('ai_response_time_ms', 0),
                    'success': metrics.get('success', True),
                    'error_message': metrics.get('error_message'),
                    'user_data': f"session_{int(time.time())}",  # Anonymous session ID
                    'file_type': file_info.get('file_type', 'manual') if file_info else 'manual',
                    'file_size_mb': file_info.get('file_size_mb', 0.0) if file_info else 0.0,
                    'ocr_used': file_info.get('ocr_used', False) if file_info else False,
                    'characters_extracted': file_info.get('characters_extracted', len(report)) if file_info else len(report),
                    'result_length': metrics.get('result_length', len(result))
                }
                
                log_success = log_to_google_sheets(**log_data)
                
                if log_success:
                    logger.info(f"Successfully logged comprehensive usage data: {log_data['language']}")
                else:
                    logger.warning("Failed to log usage to Google Sheets")
                    
            except Exception as log_error:
                logger.warning(f"Failed to log usage: {log_error}")
                
            # Store in session history with enhanced metrics
            enhanced_history_item = {
                'timestamp': datetime.now(),
                'language': st.session_state.language,
                'report_length': len(report),
                'processing_time_ms': total_processing_time_ms,
                'ai_response_time_ms': metrics.get('ai_response_time_ms', 0),
                'file_info': file_info,
                'result_length': len(result),
                'success': True,
                'quality_score': quality_info["score"],
                'validation_result': metrics.get('validation_result'),
                'metrics': metrics
            }
            
            st.session_state.processing_history.append(enhanced_history_item)
            
            # Update total characters processed
            st.session_state.total_characters_processed += len(report)
            
            # Display processing metrics in an expandable section
            with st.expander("📊 Processing Metrics"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Time", f"{total_processing_time_ms}ms")
                    st.metric("Quality Score", f"{quality_info['score']}/100")
                
                with col2:
                    st.metric("AI Response Time", f"{metrics.get('ai_response_time_ms', 0)}ms")
                    st.metric("Words Processed", quality_info['word_count'])
                
                with col3:
                    st.metric("Result Length", f"{len(result)} chars")
                    if file_info and file_info.get('file_size_mb'):
                        st.metric("File Size", f"{file_info['file_size_mb']:.2f}MB")
            
    except Exception as e:
        logger.error(f"Generation error: {e}")
        
        # Log failed attempt with detailed error info
        try:
            from log_to_sheets import log_to_google_sheets
            log_to_google_sheets(
                language=st.session_state.language,
                report_length=len(report),
                processing_time_ms=int((time.time() - start_time) * 1000),
                success=False,
                error_message=str(e),
                file_type=file_info.get('file_type', 'manual') if file_info else 'manual',
                file_size_mb=file_info.get('file_size_mb', 0.0) if file_info else 0.0,
                ocr_used=file_info.get('ocr_used', False) if file_info else False,
                user_data=f"failed_session_{int(time.time())}"
            )
        except Exception as log_error:
            logger.warning(f"Failed to log error: {log_error}")
            
        st.error(f"{lang_config['error_processing']}{str(e)}")
        
        # Store failed attempt in history
        st.session_state.processing_history.append({
            'timestamp': datetime.now(),
            'language': st.session_state.language,
            'report_length': len(report),
            'processing_time_ms': int((time.time() - start_time) * 1000),
            'file_info': file_info,
            'success': False,
            'error_message': str(e)
        })

def display_usage_stats():
    """Display comprehensive usage statistics in sidebar"""
    if st.session_state.processing_history:
        lang_config = LANGUAGES[st.session_state.language]
        
        with st.sidebar:
            st.markdown(f"### {lang_config['stats_title']}")
            
            df = pd.DataFrame(st.session_state.processing_history)
            
            # Total statistics
            total_reports = len(df)
            successful_reports = len(df[df.get('success', True) == True])
            failed_reports = total_reports - successful_reports
            total_chars = st.session_state.total_characters_processed
            
            # Calculate averages
            avg_processing_time = df['processing_time_ms'].mean() if not df.empty else 0
            avg_ai_time = df['ai_response_time_ms'].mean() if 'ai_response_time_ms' in df.columns else 0
            avg_quality_score = df['quality_score'].mean() if 'quality_score' in df.columns else 0
            
            # Display key metrics
            st.markdown("#### 📈 Key Metrics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Reports", total_reports)
                st.metric("Success Rate", f"{(successful_reports/total_reports)*100:.1f}%" if total_reports > 0 else "0%")
                st.metric("Total Characters", f"{total_chars:,}")
            
            with col2:
                st.metric("Avg Processing", f"{avg_processing_time:.0f}ms")
                st.metric("Avg AI Response", f"{avg_ai_time:.0f}ms")
                if avg_quality_score > 0:
                    st.metric("Avg Quality Score", f"{avg_quality_score:.1f}/100")
            
            # Language distribution
            if not df.empty:
                st.markdown("#### 🌐 Languages")
                lang_counts = df['language'].value_counts()
                for lang, count in lang_counts.items():
                    percentage = (count / total_reports) * 100
                    st.progress(percentage/100, text=f"{lang}: {count} ({percentage:.1f}%)")
                
                # File type distribution
                file_types = []
                for history_item in st.session_state.processing_history:
                    file_info = history_item.get('file_info')
                    if file_info and file_info.get('file_type'):
                        file_types.append(file_info['file_type'])
                    else:
                        file_types.append('manual')
                
                if file_types:
                    st.markdown("#### 📁 File Types")
                    type_counts = pd.Series(file_types).value_counts()
                    for file_type, count in type_counts.items():
                        percentage = (count / len(file_types)) * 100
                        st.progress(percentage/100, text=f"{file_type}: {count} ({percentage:.1f}%)")
                
                # Recent activity
                st.markdown("#### 🕒 Recent Activity")
                recent_items = df.tail(5)
                for _, item in recent_items.iterrows():
                    timestamp = item.get('timestamp', 'Unknown')
                    if hasattr(timestamp, 'strftime'):
                        time_str = timestamp.strftime('%H:%M')
                    else:
                        time_str = str(timestamp)[:5] if str(timestamp) else 'Unknown'
                    
                    success_icon = "✅" if item.get('success', True) else "❌"
                    lang = item.get('language', 'Unknown')[:2]
                    chars = item.get('report_length', 0)
                    
                    st.text(f"{success_icon} {time_str} | {lang} | {chars} chars")
            
            # Error summary (if any failures)
            if failed_reports > 0:
                st.markdown("#### ⚠️ Recent Errors")
                failed_items = df[df.get('success', True) == False].tail(3)
                for _, item in failed_items.iterrows():
                    error_msg = item.get('error_message', 'Unknown error')[:50]
                    st.error(f"❌ {error_msg}...")
            
            # Export data option
            if total_reports > 0:
                st.markdown("#### 💾 Export Data")
                if st.button("📊 Download Session Stats", use_container_width=True):
                    # Create downloadable CSV
                    export_df = df[['timestamp', 'language', 'report_length', 'processing_time_ms', 'success']].copy()
                    csv = export_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"radiai_session_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )

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
    
    # Display main upload mode (camera mode removed)
    display_main_mode()
    
    # Display usage statistics in sidebar
    display_usage_stats()

if __name__ == "__main__":
    main()
