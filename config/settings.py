"""
RadiAI.Care ── 全域設定檔
======================================================
1. AppConfig  : 應用程式營運相關參數
2. UIText     : 多語系介面文字
3. CSS_STYLES : Streamlit 全局樣式（已修正手機白字問題）
4. inject_css : 在 Streamlit 中注入 CSS 的輔助函式
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import streamlit as st


# ────────────────────────────────────────────────────
# 1. 應用程式設定
# ────────────────────────────────────────────────────
@dataclass(slots=True, frozen=True)
class AppConfig:
    """核心參數：如需修改請集中於此。"""
    # 免費用戶每日可執行翻譯次數
    max_free_usage: int = 3
    # Google Sheet 金鑰（填入自己表單的 ID）
    google_sheet_id: str = "1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # 工作表名稱
    usage_log_sheet: str = "usagelog"
    feedback_sheet: str = "feedback"
    SUPPORTED_FILE_TYPES: Tuple[str, ...] = ("pdf", "txt", "docx", "doc")
    FILE_SIZE_LIMIT_MB: int = 10            # 依需求調整 (單位：MB)

# ────────────────────────────────────────────────────
# 2. 多語系介面文字
# ────────────────────────────────────────────────────
UIText: dict[str, dict[str, str]] = {
    "coming_soon": {
        "zh_tw": "功能即將上線，敬請期待…",
        "zh_cn": "功能即将上线，敬请期待…",
        "en": "Coming soon…",
    },
    "error_generic": {
        "zh_tw": "系統發生錯誤，請稍後再試",
        "zh_cn": "系统发生错误，请稍后再试",
        "en": "An error occurred, please try again later",
    },
    # 其他介面字串可依需求再擴充
}


# ────────────────────────────────────────────────────
# 3. 全域 CSS 樣式（修復深色模式／手機白字）
# ────────────────────────────────────────────────────
CSS_STYLES: str = """
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


# ────────────────────────────────────────────────────
# 4. 輔助函式：在 Streamlit 注入 CSS
# ────────────────────────────────────────────────────
def inject_css() -> None:
    """將全域樣式注入目前的 Streamlit 頁面。"""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
