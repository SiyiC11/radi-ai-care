"""
RadiAI.Care 應用程序配置文件
統一管理所有配置信息，便於維護和更新
"""

import base64
import os
from pathlib import Path

class AppConfig:
    """應用程序基本配置"""
    
    APP_TITLE = "RadiAI.Care - 智能醫療報告助手"
    APP_ICON = "🏥"
    APP_VERSION = "v4.2-模塊化版"
    APP_DESCRIPTION = "為澳洲華人社區打造的醫療報告翻譯服務"
    
    # 功能限制
    MAX_FREE_TRANSLATIONS = 3
    FILE_SIZE_LIMIT_MB = 10
    MIN_TEXT_LENGTH = 20
    MAX_TEXT_LENGTH = 50000
    PREVIEW_LENGTH = 600
    
    # 支持的文件類型
    SUPPORTED_FILE_TYPES = ['pdf', 'txt', 'docx']
    
    # OpenAI 配置
    OPENAI_MODEL = "gpt-4o"
    OPENAI_TEMPERATURE = 0.2
    OPENAI_MAX_TOKENS = 3000
    OPENAI_TIMEOUT = 45
    
    # 醫學關鍵詞（基於最新研究優化）
    MEDICAL_KEYWORDS = [
        # 放射科檢查類型
        'scan', 'ct', 'mri', 'xray', 'x-ray', 'examination', 'ultrasound', 'mammogram',
        'pet scan', 'bone scan', 'angiogram', 'fluoroscopy', 'tomography',
        
        # 報告結構
        'findings', 'impression', 'study', 'image', 'report', 'conclusion',
        'clinical', 'patient', 'technique', 'contrast', 'diagnosis', 'recommendation',
        
        # 專業人員
        'radiology', 'radiologist', 'radiologic', 'radiological',
        
        # 解剖結構
        'chest', 'thorax', 'abdomen', 'brain', 'spine', 'pelvis', 'head', 'neck',
        'lung', 'heart', 'liver', 'kidney', 'bone', 'joint', 'muscle', 'vessel',
        
        # 病理術語
        'normal', 'abnormal', 'lesion', 'mass', 'nodule', 'opacity', 'density',
        'enhancement', 'attenuation', 'signal', 'intensity', 'edema', 'inflammation'
    ]
    
    @staticmethod
    def get_logo_base64():
        """返回 Logo 的 base64 編碼，優先使用上傳的圖片文件"""
        
        # 定義可能的 logo 文件路徑和擴展名
        possible_paths = [
            "assets/llogo",
            "assets/llogo.png", 
            "assets/llogo.jpg",
            "assets/llogo.jpeg",
            "assets/llogo.svg",
            "assets/llogo.gif",
            "llogo",
            "llogo.png",
            "llogo.jpg", 
            "llogo.jpeg",
            "llogo.svg",
            "llogo.gif"
        ]
        
        # 嘗試找到並讀取 logo 文件
        for logo_path in possible_paths:
            try:
                # 使用 Path 對象處理路徑
                path_obj = Path(logo_path)
                
                # 檢查文件是否存在
                if path_obj.exists() and path_obj.is_file():
                    # 讀取文件內容
                    with open(path_obj, "rb") as f:
                        file_content = f.read()
                    
                    # 根據文件擴展名確定 MIME 類型
                    file_extension = path_obj.suffix.lower()
                    if file_extension in ['.png']:
                        mime_type = 'image/png'
                    elif file_extension in ['.jpg', '.jpeg']:
                        mime_type = 'image/jpeg'
                    elif file_extension in ['.svg']:
                        mime_type = 'image/svg+xml'
                    elif file_extension in ['.gif']:
                        mime_type = 'image/gif'
                    else:
                        # 如果沒有擴展名，嘗試 PNG 格式
                        mime_type = 'image/png'
                    
                    # 編碼為 base64
                    encoded_image = base64.b64encode(file_content).decode()
                    
                    print(f"✅ 成功加載 logo 文件: {logo_path}")
                    return encoded_image, mime_type
                    
            except Exception as e:
                print(f"⚠️ 無法讀取 logo 文件 {logo_path}: {e}")
                continue
        
        # 如果找不到圖片文件，使用默認的 SVG logo
        print("📝 使用默認 SVG logo")
        return AppConfig._get_default_svg_logo(), 'image/svg+xml'
    
    @staticmethod
    def _get_default_svg_logo():
        """返回默認的 SVG logo（備用方案）"""
        logo_svg = """
        <svg width="60" height="60" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <!-- 外層橙色對話氣泡 -->
            <path d="M40 40 Q40 20 60 20 L160 20 Q180 20 180 40 L180 120 Q180 140 160 140 L80 140 L50 170 L50 140 Q40 140 40 120 Z" 
                  fill="#FF6B35" stroke="none"/>
            
            <!-- 內層白色區域 -->
            <path d="M55 50 Q55 35 70 35 L150 35 Q165 35 165 50 L165 110 Q165 125 150 125 L85 125 L65 145 L65 125 Q55 125 55 110 Z" 
                  fill="white" stroke="none"/>
            
            <!-- 中心的同心圓圖標 -->
            <g transform="translate(110, 85)">
                <!-- 最外圓 -->
                <circle cx="0" cy="0" r="35" fill="none" stroke="#4DD0E1" stroke-width="6"/>
                <!-- 中圓 -->
                <circle cx="0" cy="0" r="25" fill="none" stroke="#4DD0E1" stroke-width="5"/>
                <!-- 內圓 -->
                <circle cx="0" cy="0" r="15" fill="none" stroke="#4DD0E1" stroke-width="4"/>
                <!-- 中心圓 -->
                <circle cx="0" cy="0" r="6" fill="#4DD0E1"/>
                <!-- 底部缺口 -->
                <path d="M -15 10 Q 0 25 15 10" fill="white" stroke="none"/>
            </g>
        </svg>
        """
        return base64.b64encode(logo_svg.encode()).decode()

class UIText:
    """多語言UI文本配置"""
    
    LANGUAGE_CONFIG = {
        "繁體中文": {
            "code": "traditional_chinese",
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
            "feedback_helpful": "此結果對您有幫助嗎？",
            "feedback_clarity": "清晰度評分",
            "feedback_usefulness": "實用性評分",
            "feedback_accuracy": "準確性評分", 
            "feedback_recommendation": "推薦指數",
            "feedback_issues": "遇到的問題",
            "feedback_suggestion": "具體建議或改進意見",
            "feedback_email": "Email（選填，用於後續改進聯繫）",
            "feedback_submit": "提交回饋",
            "feedback_submitted": "✅ 感謝您的寶貴回饋！",
            "feedback_already": "此次翻譯已提交過回饋"
        },
        "简体中文": {
            "code": "simplified_chinese",
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
            "feedback_helpful": "此结果对您有帮助吗？",
            "feedback_clarity": "清晰度评分",
            "feedback_usefulness": "实用性评分",
            "feedback_accuracy": "准确性评分",
            "feedback_recommendation": "推荐指数",
            "feedback_issues": "遇到的问题",
            "feedback_suggestion": "具体建议或改进意见",
            "feedback_email": "Email（选填，用于后续改进联系）",
            "feedback_submit": "提交反馈",
            "feedback_submitted": "✅ 感谢您的宝贵反馈！",
            "feedback_already": "此次翻译已提交过反馈"
        }
    }
    
    @classmethod
    def get_language_config(cls, language: str) -> dict:
        """獲取指定語言的配置"""
        return cls.LANGUAGE_CONFIG.get(language, cls.LANGUAGE_CONFIG["简体中文"])

# CSS 樣式配置
CSS_STYLES = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
    
    .stApp {{
        font-family: 'Inter','Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;
        background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 55%, #f2fbfe 100%);
        min-height: 100vh;
    }}
    
    .main-container {{
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(6px);
        border-radius: 20px;
        padding: 2rem 2.2rem 2.4rem;
        margin: 1rem auto;
        max-width: 880px;
        box-shadow: 0 10px 30px rgba(40,85,120,0.12);
        border: 1px solid #e3eef5;
    }}
    
    .title-section {{
        text-align: center;
        padding: 2rem 0 1.7rem;
        margin-bottom: 1.2rem;
        background: linear-gradient(145deg,#f4fcff 0%,#e5f4fb 100%);
        border-radius: 18px;
        border: 1px solid #d4e8f2;
    }}
    
    .logo-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1rem;
    }}
    
    .main-title {{
        font-size: 2.7rem;
        font-weight: 700;
        background: linear-gradient(90deg,#0d74b8 0%,#29a3d7 60%,#1b90c8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: .4rem;
        letter-spacing: -1px;
    }}
    
    .subtitle {{
        font-size: 1.25rem;
        color: #256084;
        font-weight: 600;
        margin-bottom: .3rem;
    }}
    
    .description {{
        font-size: .95rem;
        color: #4c7085;
        max-width: 520px;
        margin: 0 auto;
        line-height: 1.55;
    }}
    
    .input-section {{
        background: #f3faff;
        border-radius: 18px;
        padding: 1.4rem 1.3rem 1.2rem;
        margin: 1rem 0 1.2rem;
        border: 1.5px solid #d2e8f3;
        box-shadow: 0 4px 12px rgba(13,116,184,.06);
    }}
    
    .stButton > button {{
        background: linear-gradient(90deg,#0d7ec4 0%,#1b9dd8 50%,#15a4e7 100%);
        color: #fff;
        border: none;
        border-radius: 14px;
        padding: .85rem 1.4rem;
        font-weight: 600;
        font-size: 1.05rem;
        box-shadow: 0 4px 14px rgba(23,124,179,.35);
        transition: all .28s ease;
        width: 100%;
        margin: .4rem 0 .2rem;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 22px rgba(23,124,179,.45);
    }}
    
    .result-container {{
        background: linear-gradient(145deg,#f2fbff 0%,#e3f4fa 100%);
        border-radius: 18px;
        padding: 1.8rem 1.6rem 1.6rem;
        margin: 1.4rem 0 1.2rem;
        border-left: 5px solid #1292cf;
        box-shadow: 0 6px 20px rgba(9,110,160,0.12);
    }}
    
    .feedback-container {{
        background: #ffffffea;
        border: 1px solid #d8ecf4;
        border-radius: 16px;
        padding: 1.3rem;
        margin-top: 1.2rem;
        box-shadow: 0 4px 14px rgba(20,120,170,0.08);
    }}
    
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg,#0d86c8 0%,#18a4e2 100%);
        border-radius: 10px;
    }}
    
    /* 隱藏 Streamlit 元素 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* 響應式設計 */
    @media (max-width: 768px) {{
        .main-title {{ font-size: 2.15rem; }}
        .subtitle {{ font-size: 1.05rem; }}
        .main-container {{ margin: .55rem; padding: 1.15rem; }}
    }}
    
    /* 滾動條樣式 */
    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-track {{ background: #f1f1f1; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb {{ 
        background: linear-gradient(180deg,#0d84c5,#16a4e4); 
        border-radius: 10px; 
    }}
    ::-webkit-scrollbar-thumb:hover {{ 
        background: linear-gradient(180deg,#0a75b0,#1192ce); 
    }}
    
    /* 自定義警告框樣式 */
    .custom-warning {{
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border: 2px solid #ff9800;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
    }}
    
    .warning-title {{
        text-align: center;
        font-weight: bold;
        color: #bf360c;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }}
    
    .warning-item {{
        margin: 0.8rem 0;
        padding: 1rem 1.2rem;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        border-left: 5px solid #ff9800;
        box-shadow: 0 2px 8px rgba(255, 152, 0, 0.1);
        font-size: 0.95rem;
        line-height: 1.6;
        color: #d84315;
        font-weight: 500;
    }}
    
    .warning-footer {{
        text-align: center;
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(255, 193, 7, 0.1);
        border-radius: 8px;
        font-style: italic;
        color: #f57c00;
        font-weight: 600;
        border: 1px dashed #ff9800;
    }}
</style>
"""

# Google Sheets 配置
GOOGLE_SHEETS_CONFIG = {
    "sheet_id": "1L0sFu5X3oFB3bnAKxhw8PhLJjHq0AjRcMLJEniAgrb4",
    "worksheet_name": "UsageLog",
    "feedback_worksheet_name": "Feedback",
    "timezone": "Australia/Sydney"
}
