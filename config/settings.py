# config/settings.py
"""
RadiAI.Care 應用程序配置文件
將所有配置信息集中管理，便於維護和更新
"""

# 應用程序基本配置
APP_CONFIG = {
    "page_title": "RadiAI.Care - 智能醫療報告助手",
    "page_icon": "🏥",
    "layout": "centered",
    "version": "v3.1",
    "description": "為澳洲華人社區打造的醫療報告翻譯服務"
}

# 功能限制配置
LIMITS = {
    "max_free_translations": 3,
    "file_size_limit_mb": 10,
    "min_text_length": 20,
    "max_text_length": 10000,
    "preview_length": 800
}

# 支持的文件類型
SUPPORTED_FILES = {
    "types": ['pdf', 'txt', 'docx'],
    "descriptions": {
        "pdf": "📄 PDF - 掃描或電子版報告",
        "txt": "📝 TXT - 純文字報告", 
        "docx": "📑 DOCX - Word文檔報告"
    }
}

# OpenAI API 配置
OPENAI_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 2500,
    "timeout": 30
}

# 醫學關鍵詞列表（用於內容驗證）
MEDICAL_KEYWORDS = [
    'scan', 'ct', 'mri', 'xray', 'x-ray', 'examination', 
    'findings', 'impression', 'study', 'image', 'report',
    'clinical', 'patient', 'technique', 'contrast', 'diagnosis',
    'radiology', 'radiologist', 'chest', 'abdomen', 'brain',
    'spine', 'bone', 'lung', 'heart', 'liver', 'kidney'
]

# Google Sheets 配置
GOOGLE_SHEETS_CONFIG = {
    "sheet_id": "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4",
    "worksheet_name": "UsageLog",
    "timezone": "Australia/Sydney",
    "headers": [
        "Date & Time",
        "Language", 
        "Report Length",
        "File Type",
        "Session ID",
        "User ID",
        "Processing Status"
    ]
}

# 多語言支持配置
SUPPORTED_LANGUAGES = {
    "繁體中文": {
        "code": "traditional_chinese",
        "flag": "🇹🇼",
        "name": "繁體中文"
    },
    "简体中文": {
        "code": "simplified_chinese", 
        "flag": "🇨🇳",
        "name": "简体中文"
    }
}

# UI 文本配置
UI_TEXTS = {
    "繁體中文": {
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
        "input_help": "請貼上您的英文放射科報告，確保包含完整的報告內容以獲得最佳翻譯效果。",
        "file_upload": "📂 選擇您的報告文件",
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
        "input_help": "请贴上您的英文放射科报告，确保包含完整的报告内容以获得最佳翻译效果。",
        "file_upload": "📂 选择您的报告文件",
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

# CSS 樣式配置
CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

.stApp {
    font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

@media (max-width: 768px) {
    .main-title { font-size: 2.2rem; }
    .subtitle { font-size: 1.1rem; }
    .main-container { margin: 0.5rem; padding: 1rem; }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}
"""

# 環境變量配置
ENV_VARS = {
    "required": [
        "OPENAI_API_KEY",
        "GOOGLE_SHEET_SECRET_B64"
    ],
    "optional": [
        "DEBUG",
        "LOG_LEVEL"
    ]
}

# 日誌配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["console"]
}