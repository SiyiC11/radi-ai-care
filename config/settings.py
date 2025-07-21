# CSS 樣式配置（修復手機白色文字問題）
CSS_STYLES = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
    
    /* 全局樣式 */
    .stApp {{
        font-family: 'Inter','Noto Sans SC',-apple-system,BlinkMacSystemFont,sans-serif;
        background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 55%, #f2fbfe 100%);
        min-height: 100vh;
    }}
    
    /* 確保所有文字顏色在各種背景下都可見 */
    .stApp p, .stApp span, .stApp div, .stApp label {{
        color: #1a1a1a !important;
    }}
    
    /* 主容器 */
    .main-container {{
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(6px);
        border-radius: 20px;
        padding: 2rem 2.2rem 2.4rem;
        margin: 1rem auto;
        max-width: 880px;
        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);
        color: #1a1a1a !important;
    }}
    
    .warning-title {{
        text-align: center;
        font-weight: bold;
        color: #bf360c !important;
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
        color: #d84315 !important;
        font-weight: 500;
    }}
    
    .warning-footer {{
        text-align: center;
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(255, 193, 7, 0.1);
        border-radius: 8px;
        font-style: italic;
        color: #f57c00 !important;
        font-weight: 600;
        border: 1px dashed #ff9800;
    }}
</style>
""" 0 10px 30px rgba(40,85,120,0.12);
        border: 1px solid #e3eef5;
        color: #1a1a1a !important;
    }}
    
    /* 標題區域 */
    .title-section {{
        text-align: center;
        padding: 2rem 0 1.7rem;
        margin-bottom: 1.2rem;
        background: linear-gradient(145deg,#f4fcff 0%,#e5f4fb 100%);
        border-radius: 18px;
        border: 1px solid #d4e8f2;
        color: #1a1a1a !important;
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
        color: #256084 !important;
        font-weight: 600;
        margin-bottom: .3rem;
    }}
    
    .description {{
        font-size: .95rem;
        color: #4c7085 !important;
        max-width: 520px;
        margin: 0 auto;
        line-height: 1.55;
    }}
    
    /* 輸入區域 */
    .input-section {{
        background: #f3faff;
        border-radius: 18px;
        padding: 1.4rem 1.3rem 1.2rem;
        margin: 1rem 0 1.2rem;
        border: 1.5px solid #d2e8f3;
        box-shadow: 0 4px 12px rgba(13,116,184,.06);
        color: #1a1a1a !important;
    }}
    
    /* 確保輸入框文字顏色 */
    .stTextArea textarea, .stTextInput input {{
        color: #1a1a1a !important;
        background-color: rgba(255, 255, 255, 0.95) !important;
    }}
    
    /* 按鈕樣式 */
    .stButton > button {{
        background: linear-gradient(90deg,#0d7ec4 0%,#1b9dd8 50%,#15a4e7 100%);
        color: #ffffff !important;
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
    
    /* 結果容器 */
    .result-container {{
        background: linear-gradient(145deg,#f2fbff 0%,#e3f4fa 100%);
        border-radius: 18px;
        padding: 1.8rem 1.6rem 1.6rem;
        margin: 1.4rem 0 1.2rem;
        border-left: 5px solid #1292cf;
        box-shadow: 0 6px 20px rgba(9,110,160,0.12);
        color: #1a1a1a !important;
    }}
    
    /* 回饋容器 */
    .feedback-container {{
        background: #ffffffea;
        border: 1px solid #d8ecf4;
        border-radius: 16px;
        padding: 1.3rem;
        margin-top: 1.2rem;
        box-shadow: 0 4px 14px rgba(20,120,170,0.08);
        color: #1a1a1a !important;
    }}
    
    /* 進度條 */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg,#0d86c8 0%,#18a4e2 100%);
        border-radius: 10px;
    }}
    
    /* 標籤和說明文字 */
    .stMarkdown, .stText {{
        color: #1a1a1a !important;
    }}
    
    /* 指標和統計 */
    .metric-value {{
        color: #1a1a1a !important;
    }}
    
    /* 展開器 */
    .streamlit-expanderHeader {{
        color: #1a1a1a !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
    }}
    
    /* 標籤頁 */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: #1a1a1a !important;
    }}
    
    /* 警告和提示框 */
    .stAlert {{
        color: #1a1a1a !important;
    }}
    
    /* 隱藏 Streamlit 元素 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* 響應式設計 - 移動設備優化 */
    @media (max-width: 768px) {{
        .main-title {{ font-size: 2.15rem; }}
        .subtitle {{ font-size: 1.05rem; }}
        .main-container {{ 
            margin: .55rem; 
            padding: 1.15rem;
            background: rgba(255,255,255,0.98) !important;
        }}
        
        /* 確保移動設備上的文字顏色 */
        .stApp p, .stApp span, .stApp div, .stApp label {{
            color: #1a1a1a !important;
            -webkit-text-fill-color: #1a1a1a !important;
        }}
        
        /* 移動設備上的輸入框 */
        .stTextArea textarea, .stTextInput input {{
            color: #1a1a1a !important;
            background-color: #ffffff !important;
            -webkit-text-fill-color: #1a1a1a !important;
        }}
        
        /* 移動設備上的按鈕文字 */
        .stButton > button {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }}
    }}
    
    /* 高對比度模式 */
    @media (prefers-contrast: high) {{
        .stApp p, .stApp span, .stApp div, .stApp label {{
            color: #000000 !important;
        }}
        
        .main-container {{
            background: #ffffff !important;
            border: 2px solid #000000 !important;
        }}
    }}
    
    /* 深色模式支援 */
    @media (prefers-color-scheme: dark) {{
        .stApp p, .stApp span, .stApp div, .stApp label {{
            color: #1a1a1a !important;
        }}
        
        .main-container {{
            background: rgba(255,255,255,0.98) !important;
        }}
        
        .stTextArea textarea, .stTextInput input {{
            color: #1a1a1a !important;
            background-color: #ffffff !important;
        }}
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
        box-shadow:
