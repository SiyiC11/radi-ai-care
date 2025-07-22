"""
RadiAI.Care - 修復版全域設定檔
======================================================
1. AppConfig  : 應用程式營運相關參數（添加缺失屬性）
2. UIText     : 多語系介面文字（完整中英對照）
3. CSS_STYLES : Streamlit 全局樣式
4. 添加隱私政策和使用條款內容
"""

import streamlit as st
import base64
from pathlib import Path
from typing import Tuple, Dict, Any


class AppConfig:
    """應用程式配置（修復版）"""
    
    # 基本應用信息
    APP_TITLE = "RadiAI.Care"
    APP_SUBTITLE = "智能醫療報告翻譯助手"
    APP_DESCRIPTION = "為澳洲華人社群提供專業醫學報告翻譯與科普解釋服務"
    APP_VERSION = "4.2.0"
    APP_ICON = "🏥"
    
    # 使用限制
    MAX_FREE_TRANSLATIONS = 3
    MIN_TEXT_LENGTH = 50
    MAX_TEXT_LENGTH = 15000
    FILE_SIZE_LIMIT_MB = 10
    
    # 支援的文件格式
    SUPPORTED_FILE_TYPES = ("pdf", "txt", "docx", "doc")
    
    # 醫學關鍵詞
    MEDICAL_KEYWORDS = (
        "ct", "mri", "x-ray", "xray", "ultrasound", "scan", "examination",
        "lesion", "mass", "nodule", "opacity", "density", "abnormal", "normal",
        "brain", "chest", "abdomen", "spine", "lung", "heart", "liver", "kidney",
        "thorax", "pelvis", "impression", "findings", "technique", "conclusion",
        "radiologist", "contrast", "enhancement", "fracture", "inflammation"
    )
    
    # OpenAI 設定
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_TEMPERATURE = 0.2
    OPENAI_MAX_TOKENS = 2048
    OPENAI_TIMEOUT = 60
    
    # Google Sheets 設定
    GOOGLE_SHEET_ID = "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4"
    USAGE_LOG_SHEET = "UsageLog"
    FEEDBACK_SHEET = "Feedback"
    
    # Logo 快取
    _logo_cache = None
    
    def get_logo_base64(self) -> Tuple[str, str]:
        """獲取 Logo 的 Base64 編碼"""
        if self._logo_cache:
            return self._logo_cache
        
        # 嘗試多個可能的 Logo 路徑
        possible_paths = [
            "assets/llogo.png",
            "assets/llogo",
            "llogo.png", 
            "llogo",
            "static/logo.png"
        ]
        
        for logo_path in possible_paths:
            path = Path(logo_path)
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        logo_data = base64.b64encode(f.read()).decode()
                    
                    # 根據副檔名確定 MIME 類型
                    if path.suffix.lower() in ['.png']:
                        mime_type = "image/png"
                    elif path.suffix.lower() in ['.jpg', '.jpeg']:
                        mime_type = "image/jpeg"
                    else:
                        mime_type = "image/png"  # 預設
                    
                    self._logo_cache = (logo_data, mime_type)
                    return self._logo_cache
                except Exception:
                    continue
        
        # 如果找不到 Logo，使用預設圖示
        # 建立一個簡單的 SVG logo
        default_svg = """
        <svg width="60" height="60" xmlns="http://www.w3.org/2000/svg">
            <rect width="60" height="60" rx="12" fill="#0d74b8"/>
            <text x="30" y="40" font-family="Arial" font-size="24" fill="white" text-anchor="middle">🏥</text>
        </svg>
        """
        logo_data = base64.b64encode(default_svg.encode()).decode()
        self._logo_cache = (logo_data, "image/svg+xml")
        return self._logo_cache


class UIText:
    """多語系文字配置（修復版）"""
    
    LANGUAGE_CONFIG = {
        "繁體中文": {
            "code": "traditional_chinese",
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能醫療報告翻譯助手",
            "app_description": "為澳洲華人社群提供專業醫學報告翻譯與科普解釋服務",
            
            # 語言選擇
            "lang_selection": "選擇語言 / Choose Language",
            
            # 免責聲明
            "disclaimer_title": "重要醫療免責聲明",
            "disclaimer_items": [
                "本工具僅提供醫學報告的翻譯和科普解釋，不構成任何醫療建議、診斷或治療建議",
                "所有醫療決策請務必諮詢您的主治醫師或其他醫療專業人員",
                "AI翻譯可能存在錯誤，請與醫師核實所有重要醫療資訊",
                "如有任何緊急醫療狀況，請立即撥打000或前往最近的急診室"
            ],
            
            # 輸入相關
            "input_placeholder": "請輸入您的英文放射科報告內容...",
            "file_upload": "或上傳報告檔案",
            "supported_formats": "支援格式：PDF、TXT、DOCX",
            
            # 按鈕
            "translate_button": "🚀 開始智能解讀",
            "processing": "正在處理中...",
            
            # 使用量追蹤
            "usage_today": "今日已使用",
            "usage_remaining": "剩餘次數",
            "usage_quota_exceeded": "今日免費額度已用完",
            "usage_reset_time": "額度將在明日午夜重置（澳洲東部時間）",
            
            # 錯誤訊息
            "error_empty_input": "請輸入報告內容或上傳檔案",
            "error_file_too_large": "檔案過大，請上傳小於10MB的檔案",
            "error_unsupported_format": "不支援的檔案格式",
            "error_content_too_short": "內容過短，請確保包含完整的醫學報告內容",
            "warning_no_medical": "內容中未發現明顯的醫學術語，請確認這是一份放射科報告",
            
            # 成功訊息
            "translation_complete": "🎉 翻譯完成！",
            "file_uploaded": "✅ 檔案上傳成功",
            
            # 回饋相關
            "feedback_title": "💬 您的回饋",
            "feedback_helpful": "這個翻譯對您有幫助嗎？",
            "feedback_clarity": "清晰度評分",
            "feedback_usefulness": "實用性評分", 
            "feedback_accuracy": "準確性評分",
            "feedback_recommendation": "推薦指數",
            "feedback_issues": "遇到的問題",
            "feedback_suggestion": "改進建議",
            "feedback_email": "電子郵件（選填）",
            "feedback_submit": "提交回饋",
            "feedback_submitted": "感謝您的回饋！",
            "feedback_already": "您已經提交過回饋了",
            
            # 底部資訊
            "footer_support": "技術支援",
            "footer_privacy": "隱私政策",
            "footer_terms": "使用條款",
            
            # 隱私政策內容
            "privacy_summary": "我們僅收集翻譯服務必要的資訊，符合澳洲隱私法規定。",
            "privacy_details": [
                "我們僅收集翻譯服務必要的資訊，包括您的報告內容和使用回饋。",
                "所有數據採用加密傳輸和儲存，符合澳洲隱私法（Privacy Act 1988）規定。",
                "我們不會與任何第三方分享您的個人醫療資訊。",
                "您可隨時要求查看、更正或刪除您的個人資訊。",
                "如有隱私相關疑問，請聯繫 privacy@radiai.care。"
            ],
            
            # 使用條款內容
            "terms_summary": "本服務僅提供醫學報告翻譯，不構成醫療建議。",
            "terms_details": [
                "本服務僅提供醫學報告翻譯和科普解釋，不構成任何醫療建議或診斷。",
                "用戶須為所有醫療決策自負責任，並應諮詢專業醫師的意見。",
                "我們保留隨時修改、暫停或終止服務的權利。",
                "用戶承諾合法使用本服務，不得用於任何違法或不當目的。",
                "本服務受澳洲法律管轄，如有爭議以澳洲法院管轄為準。"
            ]
        },
        
        "简体中文": {
            "code": "simplified_chinese", 
            "app_title": "RadiAI.Care",
            "app_subtitle": "智能医疗报告翻译助手",
            "app_description": "为澳洲华人社区提供专业医学报告翻译与科普解释服务",
            
            # 语言选择
            "lang_selection": "选择语言 / Choose Language",
            
            # 免责声明
            "disclaimer_title": "重要医疗免责声明",
            "disclaimer_items": [
                "本工具仅提供医学报告的翻译和科普解释，不构成任何医疗建议、诊断或治疗建议",
                "所有医疗决策请务必咨询您的主治医师或其他医疗专业人员",
                "AI翻译可能存在错误，请与医师核实所有重要医疗信息",
                "如有任何紧急医疗状况，请立即拨打000或前往最近的急诊室"
            ],
            
            # 输入相关
            "input_placeholder": "请输入您的英文放射科报告内容...",
            "file_upload": "或上传报告文件",
            "supported_formats": "支持格式：PDF、TXT、DOCX",
            
            # 按钮
            "translate_button": "🚀 开始智能解读",
            "processing": "正在处理中...",
            
            # 使用量追踪
            "usage_today": "今日已使用",
            "usage_remaining": "剩余次数",
            "usage_quota_exceeded": "今日免费额度已用完",
            "usage_reset_time": "额度将在明日午夜重置（澳洲东部时间）",
            
            # 错误信息
            "error_empty_input": "请输入报告内容或上传文件",
            "error_file_too_large": "文件过大，请上传小于10MB的文件",
            "error_unsupported_format": "不支持的文件格式",
            "error_content_too_short": "内容过短，请确保包含完整的医学报告内容",
            "warning_no_medical": "内容中未发现明显的医学术语，请确认这是一份放射科报告",
            
            # 成功信息
            "translation_complete": "🎉 翻译完成！",
            "file_uploaded": "✅ 文件上传成功",
            
            # 反馈相关
            "feedback_title": "💬 您的反馈",
            "feedback_helpful": "这个翻译对您有帮助吗？",
            "feedback_clarity": "清晰度评分",
            "feedback_usefulness": "实用性评分",
            "feedback_accuracy": "准确性评分", 
            "feedback_recommendation": "推荐指数",
            "feedback_issues": "遇到的问题",
            "feedback_suggestion": "改进建议",
            "feedback_email": "电子邮件（选填）",
            "feedback_submit": "提交反馈",
            "feedback_submitted": "感谢您的反馈！",
            "feedback_already": "您已经提交过反馈了",
            
            # 底部信息
            "footer_support": "技术支持",
            "footer_privacy": "隐私政策", 
            "footer_terms": "使用条款",
            
            # 隐私政策内容
            "privacy_summary": "我们仅收集翻译服务必要的信息，符合澳洲隐私法规定。",
            "privacy_details": [
                "我们仅收集翻译服务必要的信息，包括您的报告内容和使用反馈。",
                "所有数据采用加密传输和存储，符合澳洲隐私法（Privacy Act 1988）规定。",
                "我们不会与任何第三方分享您的个人医疗信息。",
                "您可随时要求查看、更正或删除您的个人信息。",
                "如有隐私相关疑问，请联系 privacy@radiai.care。"
            ],
            
            # 使用条款内容
            "terms_summary": "本服务仅提供医学报告翻译，不构成医疗建议。",
            "terms_details": [
                "本服务仅提供医学报告翻译和科普解释，不构成任何医疗建议或诊断。",
                "用户须为所有医疗决策自负责任，并应咨询专业医师的意见。",
                "我们保留随时修改、暂停或终止服务的权利。",
                "用户承诺合法使用本服务，不得用于任何违法或不当目的。",
                "本服务受澳洲法律管辖，如有争议以澳洲法院管辖为准。"
            ]
        }
    }
    
    @classmethod
    def get_language_config(cls, language: str) -> Dict[str, str]:
        """獲取指定語言的配置"""
        return cls.LANGUAGE_CONFIG.get(language, cls.LANGUAGE_CONFIG["简体中文"])


# Google Sheets 配置
GOOGLE_SHEETS_CONFIG = {
    "scopes": [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly"
    ],
    "sheet_id": "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4",
    "usage_sheet": "UsageLog",
    "feedback_sheet": "Feedback"
}


# CSS 樣式（保持原有的樣式）
CSS_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

/* ===== 全局樣式 ===== */
.stApp {
    font-family: 'Inter','Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;
    background: linear-gradient(135deg,#e0f7fa 0%,#ffffff 55%,#f2fbfe 100%);
    min-height: 100vh;
}
.stApp p, .stApp span, .stApp div, .stApp label { color:#1a1a1a !important; }

/* ===== 主容器 ===== */
.main-container{
    background:rgba(255,255,255,0.95);
    backdrop-filter:blur(6px);
    border-radius:20px;
    padding:2rem 2.2rem 2.4rem;
    margin:1rem auto;
    max-width:880px;
    box-shadow:0 10px 30px rgba(40,85,120,0.12);
    border:1px solid #e3eef5;
    color:#1a1a1a !important;
}

/* ===== 警告區塊 ===== */
.warning-title{
    text-align:center;font-weight:bold;color:#bf360c !important;
    font-size:1.2rem;margin-bottom:1rem;display:flex;
    align-items:center;justify-content:center;gap:.5rem;
}
.warning-item{
    margin:.8rem 0;padding:1rem 1.2rem;background:rgba(255,255,255,0.9);
    border-radius:12px;border-left:5px solid #ff9800;
    box-shadow:0 2px 8px rgba(255,152,0,0.1);
    font-size:.95rem;line-height:1.6;color:#d84315 !important;font-weight:500;
}
.warning-footer{
    text-align:center;margin-top:1rem;padding:1rem;
    background:rgba(255,193,7,0.1);border-radius:8px;font-style:italic;
    color:#f57c00 !important;font-weight:600;border:1px dashed #ff9800;
}

/* ===== 標題區 ===== */
.title-section{
    text-align:center;padding:2rem 0 1.7rem;margin-bottom:1.2rem;
    background:linear-gradient(145deg,#f4fcff 0%,#e5f4fb 100%);
    border-radius:18px;border:1px solid #d4e8f2;color:#1a1a1a !important;
}
.logo-container{display:flex;justify-content:center;align-items:center;margin-bottom:1rem;}
.main-title{
    font-size:2.7rem;font-weight:700;
    background:linear-gradient(90deg,#0d74b8 0%,#29a3d7 60%,#1b90c8 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;margin-bottom:.4rem;letter-spacing:-1px;
}
.subtitle{font-size:1.25rem;color:#256084 !important;font-weight:600;margin-bottom:.3rem;}
.description{font-size:.95rem;color:#4c7085 !important;max-width:520px;margin:0 auto;line-height:1.55;}

/* ===== 輸入區 ===== */
.input-section{
    background:#f3faff;border-radius:18px;padding:1.4rem 1.3rem 1.2rem;
    margin:1rem 0 1.2rem;border:1.5px solid #d2e8f3;
    box-shadow:0 4px 12px rgba(13,116,184,.06);color:#1a1a1a !important;
}
.stTextArea textarea,.stTextInput input{
    color:#1a1a1a !important;background-color:rgba(255,255,255,0.95) !important;
}

/* ===== 按鈕 ===== */
.stButton>button{
    background:linear-gradient(90deg,#0d7ec4 0%,#1b9dd8 50%,#15a4e7 100%);
    color:#ffffff !important;border:none;border-radius:14px;padding:.85rem 1.4rem;
    font-weight:600;font-size:1.05rem;box-shadow:0 4px 14px rgba(23,124,179,.35);
    transition:all .28s ease;width:100%;margin:.4rem 0 .2rem;
}
.stButton>button:hover{transform:translateY(-3px);box-shadow:0 8px 22px rgba(23,124,179,.45);}

/* ===== 結果區 ===== */
.result-container{
    background:linear-gradient(145deg,#f2fbff 0%,#e3f4fa 100%);
    border-radius:18px;padding:1.8rem 1.6rem 1.6rem;margin:1.4rem 0 1.2rem;
    border-left:5px solid #1292cf;box-shadow:0 6px 20px rgba(9,110,160,0.12);
    color:#1a1a1a !important;
}

/* ===== 回饋區 ===== */
.feedback-container{
    background:#ffffffea;border:1px solid #d8ecf4;border-radius:16px;
    padding:1.3rem;margin-top:1.2rem;box-shadow:0 4px 14px rgba(20,120,170,0.08);
    color:#1a1a1a !important;
}

/* ===== 隱私政策和使用條款樣式 ===== */
.privacy-terms-summary{
    font-size:0.85rem;color:#666 !important;text-align:center;
    margin:1rem 0;padding:0.5rem;font-style:italic;
}
.privacy-terms-link{
    color:#0d74b8 !important;text-decoration:underline;cursor:pointer;
    font-weight:500;
}
.privacy-terms-content{
    background:#f8f9fa;border-radius:8px;padding:1rem;margin-top:0.5rem;
    border-left:3px solid #0d74b8;font-size:0.9rem;line-height:1.5;
}

/* ===== 進度條 ===== */
.stProgress>div>div>div>div{background:linear-gradient(90deg,#0d86c8 0%,#18a4e2 100%);border-radius:10px;}

/* ===== 介面標籤 ===== */
.stMarkdown,.stText,.metric-value{color:#1a1a1a !important;}
.streamlit-expanderHeader{color:#1a1a1a !important;background-color:rgba(255,255,255,0.8) !important;}
.stTabs[data-baseweb="tab-list"]{background-color:transparent;}
.stTabs [data-baseweb="tab"]{color:#1a1a1a !important;}
.stAlert{color:#1a1a1a !important;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}.stDeployButton{display:none;}

/* ===== 響應式：手機優化 ===== */
@media(max-width:768px){
    .main-title{font-size:2.15rem;}
    .subtitle{font-size:1.05rem;}
    .main-container{margin:.55rem;padding:1.15rem;background:rgba(255,255,255,0.98)!important;}
    .stTextArea textarea,.stTextInput input{
        color:#1a1a1a !important;background-color:#ffffff !important;-webkit-text-fill-color:#1a1a1a !important;
    }
    .stButton>button{color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;}
}

/* ===== 高對比度 ===== */
@media(prefers-contrast:high){
    .stApp p,.stApp span,.stApp div,.stApp label{color:#000 !important;}
    .main-container{background:#fff !important;border:2px solid #000 !important;}
}

/* ===== 深色模式 ===== */
@media(prefers-color-scheme:dark){
    .stApp p,.stApp span,.stApp div,.stApp label{color:#1a1a1a !important;}
    .main-container{background:rgba(255,255,255,0.98)!important;}
    .stTextArea textarea,.stTextInput input{color:#1a1a1a !important;background-color:#ffffff !important;}
}

/* ===== 滾動條 ===== */
::-webkit-scrollbar{width:8px;}
::-webkit-scrollbar-track{background:#f1f1f1;border-radius:10px;}
::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#0d84c5,#16a4e4);border-radius:10px;}
::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#0a75b0,#1192ce);}
</style>
"""


def inject_css() -> None:
    """將全域樣式注入目前的 Streamlit 頁面"""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
