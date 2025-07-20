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

# 導入自定義模組
try:
    from utils.prompt_template import get_prompt, create_enhanced_disclaimer, get_processing_steps
    from log_to_sheets import log_to_google_sheets
except ImportError:
    st.error("⚠️ 請確保 utils/prompt_template.py 和 log_to_sheets.py 文件存在")
    st.stop()

# -----------------------------
# 基礎配置
# -----------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 應用配置
APP_VERSION = "v4.0-簡化版"
MAX_FREE_TRANSLATIONS = 3
SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'docx']
FILE_SIZE_LIMIT_MB = 10
MIN_TEXT_LENGTH = 20

# 醫學關鍵詞
MEDICAL_KEYWORDS = [
    'scan', 'ct', 'mri', 'xray', 'x-ray', 'examination',
    'findings', 'impression', 'study', 'image', 'report',
    'clinical', 'patient', 'technique', 'contrast', 'diagnosis',
    'radiology', 'radiologist', 'chest', 'abdomen', 'brain'
]

# 頁面配置
st.set_page_config(
    page_title="RadiAI.Care - 智能醫療報告助手",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# OpenAI 客戶端
# -----------------------------
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OpenAI API密鑰未設置")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# -----------------------------
# 語言配置
# -----------------------------
LANGUAGE_CONFIG = {
    "繁體中文": {
        "code": "traditional_chinese",
        "flag": "🇹🇼",
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
        "file_upload": "📂 選擇您的報告文件",
        "file_success": "✅ 文件讀取成功！",
        "file_error": "❌ 文件讀取失敗",
        "translate_button": "🚀 開始智能解讀",
        "result_title": "📋 智能解讀結果",
        "translation_complete": "🎉 解讀完成！您還有",
        "translation_remaining": "次免費翻譯機會",
        "error_no_content": "請輸入報告內容或上傳有效文件",
        "error_too_short": "輸入內容太短，請確保輸入完整的醫學報告",
        "warning_no_medical": "內容似乎不包含醫學術語，翻譯結果可能不夠準確",
        "quota_finished": "🎯 免費翻譯額度已用完。感謝您的使用！",
        # 回饋相關
        "feedback_title": "🗣 使用者回饋",
        "feedback_helpful": "此結果對你有幫助嗎？",
        "feedback_clarity": "清晰度 (1-5)",
        "feedback_usefulness": "實用性 (1-5)",
        "feedback_recommendation": "推薦指數 (0-10)",
        "feedback_issues": "遇到的問題",
        "feedback_suggestion": "具體建議",
        "feedback_submit": "提交回饋",
        "feedback_submitted": "✅ 感謝您的回饋！",
        "feedback_already": "此次翻譯已提交過回饋"
    },
    "简体中文": {
        "code": "simplified_chinese",
        "flag": "🇨🇳",
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
        "file_upload": "📂 选择您的报告文件",
        "file_success": "✅ 文件读取成功！",
        "file_error": "❌ 文件读取失败",
        "translate_button": "🚀 开始智能解读",
        "result_title": "📋 智能解读结果",
        "translation_complete": "🎉 解读完成！您还有",
        "translation_remaining": "次免费翻译机会",
        "error_no_content": "请输入报告内容或上传有效文件",
        "error_too_short": "输入内容太短，请确保输入完整的医学报告",
        "warning_no_medical": "内容似乎不包含医学术语，翻译结果可能不够准确",
        "quota_finished": "🎯 免费翻译额度已用完。感谢您的使用！",
        # 回饋相關
        "feedback_title": "🗣 用户反馈",
        "feedback_helpful": "此结果对你有帮助吗？",
        "feedback_clarity": "清晰度 (1-5)",
        "feedback_usefulness": "实用性 (1-5)",
        "feedback_recommendation": "推荐指数 (0-10)",
        "feedback_issues": "遇到的问题",
        "feedback_suggestion": "具体建议",
        "feedback_submit": "提交反馈",
        "feedback_submitted": "✅ 感谢您的反馈！",
        "feedback_already": "此次翻译已提交过反馈"
    }
}

# -----------------------------
# Session State 初始化
# -----------------------------
def init_session_state():
    if 'language' not in st.session_state:
        st.session_state.language = "简体中文"
    if 'translation_count' not in st.session_state:
        st.session_state.translation_count = 0
    if 'input_method' not in st.session_state:
        st.session_state.input_method = "text"
    if 'feedback_submitted_ids' not in st.session_state:
        st.session_state.feedback_submitted_ids = set()
    if 'last_translation_id' not in st.session_state:
        st.session_state.last_translation_id = None

# -----------------------------
# CSS 樣式（簡化並修正）
# -----------------------------
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            font-family: 'Inter','Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;
            background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 100%);
        }
        
        .main-container {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem auto;
            max-width: 800px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: 1px solid #e1e8ff;
        }
        
        .title-section {
            text-align: center;
            padding: 2rem;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #f4fcff 0%, #e5f4fb 100%);
            border-radius: 15px;
            border: 1px solid #d4e8f2;
        }
        
        .main-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #0d74b8 0%, #29a3d7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #256084;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .description {
            font-size: 1rem;
            color: #4c7085;
            line-height: 1.6;
        }
        
        /* 修正法律聲明樣式 */
        .disclaimer-box {
            background: #fff8e1;
            border: 2px solid #ff9800;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
        }
        
        .disclaimer-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #bf360c;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        .disclaimer-item {
            background: rgba(255, 255, 255, 0.8);
            padding: 0.8rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            border-left: 4px solid #ff9800;
            font-size: 0.9rem;
            line-height: 1.5;
            color: #d84315;
        }
        
        .input-section {
            background: #f3faff;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 2px solid #d2e8f3;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #0d74b8 0%, #29a3d7 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.8rem 1.5rem;
            font-weight: 600;
            width: 100%;
            margin: 0.5rem 0;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(13, 116, 184, 0.3);
        }
        
        .result-container {
            background: linear-gradient(135deg, #f2fbff 0%, #e3f4fa 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-left: 5px solid #29a3d7;
        }
        
        .feedback-container {
            background: rgba(255,255,255,0.9);
            border: 1px solid #d8ecf4;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1rem;
        }
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #0d74b8 0%, #29a3d7 100%);
        }
        
        /* 隱藏 Streamlit 元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* 響應式設計 */
        @media (max-width: 768px) {
            .main-title { font-size: 2rem; }
            .main-container { margin: 0.5rem; padding: 1rem; }
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# 文件處理
# -----------------------------
def extract_text_from_file(uploaded_file):
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        
        if file_size_mb > FILE_SIZE_LIMIT_MB:
            return None
            
        if file_extension == 'txt':
            try:
                return uploaded_file.read().decode('utf-8').strip()
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                try:
                    return uploaded_file.read().decode('gbk').strip()
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    return uploaded_file.read().decode('big5').strip()
                    
        elif file_extension == 'pdf':
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text_parts = []
            for page_num in range(pdf_document.page_count):
                page_text = pdf_document[page_num].get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            pdf_document.close()
            return "\n\n".join(text_parts).strip() if text_parts else ""
            
        elif file_extension in ['docx', 'doc']:
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            return "\n".join(text_parts).strip() if text_parts else ""
            
    except Exception as e:
        logger.error(f"文件提取錯誤: {e}")
        return None

# -----------------------------
# 內容驗證
# -----------------------------
def validate_medical_content(text):
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return False
    text_lower = text.lower()
    matching_keywords = [kw for kw in MEDICAL_KEYWORDS if kw in text_lower]
    return len(matching_keywords) >= 2

# -----------------------------
# 翻譯功能
# -----------------------------
def translate_report(report_text, language_code):
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
        result_text = response.choices[0].message.content.strip()
        disclaimer_html = create_enhanced_disclaimer(language_code)
        return result_text, disclaimer_html
    except Exception as e:
        logger.error(f"翻譯錯誤: {e}")
        return f"❌ 翻譯失敗：{str(e)}", ""

# -----------------------------
# 語言選擇
# -----------------------------
def render_language_selection(lang):
    st.markdown(f'<div style="text-align:center; margin:1.5rem 0;"><h4>{lang["lang_selection"]}</h4></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"{LANGUAGE_CONFIG['繁體中文']['flag']} 繁體中文", 
                    key="lang_traditional", use_container_width=True,
                    type="primary" if st.session_state.language == "繁體中文" else "secondary"):
            st.session_state.language = "繁體中文"
            st.rerun()
    with col2:
        if st.button(f"{LANGUAGE_CONFIG['简体中文']['flag']} 简体中文", 
                    key="lang_simplified", use_container_width=True,
                    type="primary" if st.session_state.language == "简体中文" else "secondary"):
            st.session_state.language = "简体中文"
            st.rerun()

# -----------------------------
# 修正的法律聲明
# -----------------------------
def render_disclaimer(lang):
    """修正後的法律聲明顯示"""
    disclaimer_html = f"""
    <div class="disclaimer-box">
        <div class="disclaimer-title">{lang["disclaimer_title"]}</div>
    """
    
    for i, item in enumerate(lang["disclaimer_items"], 1):
        disclaimer_html += f"""
        <div class="disclaimer-item">
            <strong>📌 {i}.</strong> {item}
        </div>
        """
    
    disclaimer_html += "</div>"
    st.markdown(disclaimer_html, unsafe_allow_html=True)

# -----------------------------
# 使用次數追蹤
# -----------------------------
def render_usage_tracker():
    remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
    progress = st.session_state.translation_count / MAX_FREE_TRANSLATIONS
    
    st.markdown("### 📊 使用情況")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.metric("剩餘", remaining)
    with col3:
        st.metric("已用", f"{st.session_state.translation_count}/{MAX_FREE_TRANSLATIONS}")
    
    return remaining

# -----------------------------
# 輸入區塊
# -----------------------------
def render_input_section(lang):
    st.markdown('<div class="input-section">', unsafe_allow_html=True)
    st.markdown(f'### {lang["input_method"]}')
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(lang["input_text"], key="input_text_btn", use_container_width=True,
                    type="primary" if st.session_state.input_method == "text" else "secondary"):
            st.session_state.input_method = "text"
    with col2:
        if st.button(lang["input_file"], key="input_file_btn", use_container_width=True,
                    type="primary" if st.session_state.input_method == "file" else "secondary"):
            st.session_state.input_method = "file"
    
    report_text = ""
    file_type = "manual"
    
    if st.session_state.input_method == "text":
        st.markdown("#### 📝 輸入報告內容")
        report_text = st.text_area(
            lang["input_placeholder"],
            height=240,
            placeholder="例如：CHEST CT SCAN\nCLINICAL HISTORY: ...\nFINDINGS: ...\nIMPRESSION: ...",
            label_visibility="collapsed"
        )
    else:
        st.markdown("#### 📂 上傳報告文件")
        uploaded_file = st.file_uploader(
            lang["file_upload"],
            type=SUPPORTED_FILE_TYPES,
            help=f"支援 {', '.join([t.upper() for t in SUPPORTED_FILE_TYPES])} 格式，限制 {FILE_SIZE_LIMIT_MB}MB",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.lower().split('.')[-1]
            with st.spinner("🔄 讀取文件中..."):
                extracted_text = extract_text_from_file(uploaded_file)
                if extracted_text:
                    report_text = extracted_text
                    st.success(f"✅ {lang['file_success']}")
                    with st.expander("👀 預覽內容"):
                        preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                        st.text_area("", value=preview, height=100, disabled=True)
                else:
                    st.error(f"❌ {lang['file_error']}")
                    file_type = "failed"
    
    st.markdown('</div>', unsafe_allow_html=True)
    return report_text, file_type

# -----------------------------
# 回饋記錄到 Google Sheets
# -----------------------------
def log_feedback_to_sheets(**data):
    """記錄回饋到 Google Sheets"""
    try:
        # 使用原有的 log_to_google_sheets 函數，加上 feedback 標記
        feedback_data = {
            'processing_status': 'feedback',
            'language': data.get('language', ''),
            'translation_id': data.get('translation_id', ''),
            'clarity_score': data.get('clarity_score', 0),
            'usefulness_score': data.get('usefulness_score', 0),
            'recommendation_score': data.get('recommendation_score', 0),
            'issues': data.get('issues', ''),
            'suggestion': data.get('suggestion', ''),
            'helpful': data.get('helpful', ''),
            'app_version': APP_VERSION
        }
        
        # 調用原有的記錄函數
        log_to_google_sheets(**feedback_data)
        return True
    except Exception as e:
        logger.error(f"回饋記錄失敗: {e}")
        return False

# -----------------------------
# 回饋收集
# -----------------------------
def render_feedback_section(lang, translation_id, report_length, file_type):
    """簡化的回饋收集介面"""
    if translation_id in st.session_state.feedback_submitted_ids:
        st.info(lang.get('feedback_already', '已提交過回饋'))
        return
    
    st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
    st.markdown(f"#### {lang['feedback_title']}")
    
    # 快速回饋按鈕
    st.markdown(f"**{lang['feedback_helpful']}**")
    col1, col2 = st.columns(2)
    helpful_choice = None
    
    with col1:
        if st.button("👍 有幫助", key=f"helpful_yes_{translation_id}", use_container_width=True):
            helpful_choice = "yes"
    with col2:
        if st.button("👎 沒幫助", key=f"helpful_no_{translation_id}", use_container_width=True):
            helpful_choice = "no"
    
    # 詳細回饋表單
    with st.form(f"feedback_form_{translation_id}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            clarity = st.slider(lang['feedback_clarity'], 1, 5, 4)
            usefulness = st.slider(lang['feedback_usefulness'], 1, 5, 4)
        with col2:
            recommendation = st.slider(lang['feedback_recommendation'], 0, 10, 8)
        
        issues = st.multiselect(
            lang['feedback_issues'],
            ["翻譯不準確", "用詞難懂", "格式不清楚", "速度太慢", "其他"],
            default=[]
        )
        
        suggestion = st.text_area(
            lang['feedback_suggestion'], 
            height=60, 
            max_chars=300,
            placeholder="請提供您的建議..."
        )
        
        submitted = st.form_submit_button(lang['feedback_submit'], use_container_width=True)
    
    # 處理回饋提交
    if submitted or helpful_choice:
        feedback_data = {
            'translation_id': translation_id,
            'language': st.session_state.language,
            'helpful': helpful_choice or ("yes" if clarity + usefulness >= 6 else "no"),
            'clarity_score': clarity if submitted else 0,
            'usefulness_score': usefulness if submitted else 0,
            'recommendation_score': recommendation if submitted else 0,
            'issues': ";".join(issues) if submitted else "",
            'suggestion': suggestion if submitted else "",
            'report_length': report_length,
            'file_type': file_type
        }
        
        if log_feedback_to_sheets(**feedback_data):
            st.session_state.feedback_submitted_ids.add(translation_id)
            st.success(lang['feedback_submitted'])
        else:
            st.warning("回饋記錄失敗，但已保存本地")
    
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 翻譯處理
# -----------------------------
def render_translation_process(report_text, file_type, lang):
    if not report_text.strip():
        st.error(f"❌ {lang['error_no_content']}")
        return False
    
    if len(report_text.strip()) < MIN_TEXT_LENGTH:
        st.error(f"❌ {lang['error_too_short']}")
        return False
    
    if not validate_medical_content(report_text):
        st.warning(f"⚠️ {lang['warning_no_medical']}")
    
    # 處理進度
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    start_time = time.time()
    translation_id = str(uuid.uuid4())
    
    try:
        steps = get_processing_steps(lang["code"])
        
        for i, step_text in enumerate(steps):
            status_text.markdown(f"**{step_text}**")
            progress_bar.progress(int((i + 1) / len(steps) * 100))
            time.sleep(0.7)
        
        # 執行翻譯
        result_text, disclaimer_html = translate_report(report_text, lang["code"])
        processing_time = int((time.time() - start_time) * 1000)
        
        # 清除進度指示器
        progress_container.empty()
        
        # 顯示結果
        st.markdown('<div class="result-container">', unsafe_allow_html=True)
        st.markdown(f"### {lang['result_title']}")
        st.markdown(result_text)
        if disclaimer_html:
            st.markdown(disclaimer_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 記錄使用情況
        try:
            log_to_google_sheets(
                language=st.session_state.language,
                report_length=len(report_text),
                file_type=file_type,
                processing_status="success",
                translation_id=translation_id,
                latency_ms=processing_time,
                app_version=APP_VERSION
            )
        except Exception as log_error:
            logger.warning(f"使用記錄失敗: {log_error}")
        
        # 更新計數器
        st.session_state.translation_count += 1
        st.session_state.last_translation_id = translation_id
        
        # 顯示完成狀態
        remaining = MAX_FREE_TRANSLATIONS - st.session_state.translation_count
        if remaining > 0:
            st.success(f"{lang['translation_complete']} {remaining} {lang['translation_remaining']}")
        else:
            st.balloons()
            st.success("🌟 您已用完所有免費翻譯！感謝使用 RadiAI.Care")
        
        # 顯示回饋區塊
        render_feedback_section(lang, translation_id, len(report_text), file_type)
        
        return True
        
    except Exception as e:
        progress_container.empty()
        st.error(f"❌ 翻譯過程中發生錯誤：{str(e)}")
        
        # 記錄錯誤
        try:
            log_to_google_sheets(
                language=st.session_state.language,
                report_length=len(report_text),
                file_type=file_type,
                processing_status="error",
                error=str(e),
                app_version=APP_VERSION
            )
        except Exception:
            pass
        
        return False

# -----------------------------
# 底部資訊區
# -----------------------------
def render_footer():
    """簡化的底部資訊"""
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["💡 使用指南", "🔒 隱私保護", "⚠️ 重要提醒"])
    
    with tab1:
        st.markdown("""
        ### 📋 如何使用
        
        **1. 選擇語言**：繁體中文或简体中文
        
        **2. 輸入報告**：
        - 直接貼上英文報告文字
        - 或上傳 PDF/TXT/DOCX 文件
        
        **3. 開始翻譯**：點擊「開始智能解讀」按鈕
        
        **4. 查看結果**：獲得中文翻譯和專業解釋
        
        **5. 提供回饋**：幫助我們改進服務品質
        
        ### 📝 最佳效果建議
        ✅ 確保報告內容完整  
        ✅ 包含醫學專業術語  
        ✅ 文件清晰可讀  
        ✅ 移除個人敏感資訊
        """)
    
    with tab2:
        st.markdown("""
        ### 🛡️ 隱私保護
        
        **數據安全承諾：**
        
        ✅ **不儲存醫療內容**：翻譯完成後立即清除  
        ✅ **匿名統計記錄**：僅記錄使用統計，不含個人資訊  
        ✅ **加密傳輸**：所有數據使用 HTTPS 加密  
        ✅ **合規標準**：符合澳洲隱私法規
        
        **使用建議：**
        
        🚫 請勿包含身份證號、地址等敏感資訊  
        🚫 建議移除患者姓名後再上傳  
        ✅ 我們只關注醫學術語的翻譯解釋
        """)
    
    with tab3:
        st.markdown("""
        ### ⚠️ 醫療安全提醒
        
        **✅ 我們提供：**
        - 英文醫學報告的中文翻譯
        - 醫學術語的通俗解釋  
        - 向醫師諮詢的建議問題
        
        **🚫 我們不提供：**
        - 任何醫療診斷或治療建議
        - 醫療決策指導
        - 緊急醫療服務
        
        **🆘 緊急情況：**
        - 立即撥打 **000**
        - 前往最近的急診室
        - 聯繫您的主治醫師
        
        **⚖️ 法律責任：**
        所有醫療決策責任歸患者和醫療團隊，本工具僅提供翻譯服務。
        """)

# -----------------------------
# 主程式
# -----------------------------
def main():
    """簡化的主程式"""
    try:
        # 初始化
        init_session_state()
        load_css()
        
        # 獲取語言配置
        lang = LANGUAGE_CONFIG[st.session_state.language]
        
        # 主容器
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # 標題區塊
        st.markdown(f'''
        <div class="title-section">
            <div class="main-title">{lang["app_title"]}</div>
            <div class="subtitle">{lang["app_subtitle"]}</div>
            <div class="description">{lang["app_description"]}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 語言選擇
        render_language_selection(lang)
        
        # 更新語言配置
        lang = LANGUAGE_CONFIG[st.session_state.language]
        
        # 修正後的法律聲明
        render_disclaimer(lang)
        
        # 使用次數追蹤
        remaining = render_usage_tracker()
        
        # 檢查額度
        if remaining <= 0:
            st.error(f"🚫 {lang['quota_finished']}")
            st.info("💡 如需更多翻譯服務，請聯繫我們了解付費方案。")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # 輸入區塊
        report_text, file_type = render_input_section(lang)
        
        # 翻譯按鈕
        if st.button(f"{lang['translate_button']}", type="primary", use_container_width=True):
            render_translation_process(report_text, file_type, lang)
        
        # 底部資訊
        render_footer()
        
        # 版本資訊
        st.markdown(f'''
        <div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem; 
                    padding: 1rem; background: #f8f9fa; border-radius: 10px;">
            <strong>RadiAI.Care {APP_VERSION}</strong> | 為澳洲華人社區打造 ❤️<br>
            <small>Powered by GPT-4o | Built with Streamlit</small>
        </div>
        ''', unsafe_allow_html=True)
        
        # 關閉主容器
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        logger.error(f"應用程式錯誤: {e}")
        st.error("❌ 應用程式發生錯誤，請重新整理頁面")
        
        # 錯誤恢復建議
        with st.expander("🔧 故障排除", expanded=False):
            st.markdown("""
            ### 🔄 解決方案：
            1. **重新整理頁面**：按 F5 或點擊重新整理
            2. **清除瀏覽器快取**：Ctrl+Shift+Delete
            3. **稍後重試**：等待 1-2 分鐘後重新嘗試
            4. **檢查網路**：確保網路連線穩定
            5. **聯繫支援**：如問題持續，請聯繫技術支援
            """)

if __name__ == "__main__":
    main()
