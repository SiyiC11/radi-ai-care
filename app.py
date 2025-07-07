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
from utils.translator import explain_report

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Radi.AI Care", layout="centered")

# 📱 裝置偵測（隱藏 UI）
import streamlit.components.v1 as components
components.html("""
    <script>
        const isMobile = /Mobi|Android/i.test(navigator.userAgent);
        window.parent.postMessage(isMobile ? "mobile" : "desktop", "*");
    </script>
""", height=0)

is_mobile = False
if "mobile" in st.session_state.get("device", ""):
    is_mobile = True

st.image("assets/logo.png", width=100 if is_mobile else 160)

# 🌐 語言切換
st.markdown("### 🌐 請選擇語言 / Choose Language")
col1, col2, col3 = st.columns(3)
default_lang = "简体中文"
if "language" not in st.session_state:
    st.session_state.language = default_lang
with col1:
    if st.button("繁體中文"):
        st.session_state.language = "繁體中文"
with col2:
    if st.button("简体中文"):
        st.session_state.language = "简体中文"
with col3:
    if st.button("English"):
        st.session_state.language = "English"
language = st.session_state.language
titles = {
    "简体中文": "🩺 Radi.AI Care - 报告翻译助手",
    "繁體中文": "🩺 Radi.AI Care - 報告翻譯助手",
    "English": "🩺 Radi.AI Care - Report Translation Assistant"
}
st.title(titles[language])

# 🧠 預備文字輸出內容
report = ""

# 模式切換
if "mode" not in st.session_state:
    st.session_state.mode = "main"

def back_to_main():
    st.session_state.mode = "main"

# 📤 上傳檔案模式
if st.session_state.mode == "main":
    st.subheader("📤 上傳檔案或圖片")
    uploaded_file = st.file_uploader(
        "請上傳圖片或報告（支援 .jpg, .png, .pdf, .txt）",
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        key="combined_upload"
    )

    if uploaded_file:
        filename = uploaded_file.name.lower()
        if filename.endswith(".txt"):
            report = uploaded_file.read().decode("utf-8")
        elif filename.endswith(".pdf"):
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                report = "\n".join([page.get_text() for page in doc])
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(uploaded_file)
            st.image(image, caption="你上傳的圖片", use_container_width=True)
            report = pytesseract.image_to_string(image, lang="eng")

    st.markdown("---")
    if st.button("📸 拍照上傳"):
        st.session_state.mode = "camera"

# 📸 拍照模式
elif st.session_state.mode == "camera":
    st.subheader("📸 拍照上傳模式")
    camera_image = st.camera_input("請使用手機或設備拍照")
    if camera_image:
        st.image(camera_image, caption="你拍攝的圖片", use_container_width=True)
        image = Image.open(camera_image)
        report = pytesseract.image_to_string(image, lang="eng")
    st.button("⬅️ 返回主頁", on_click=back_to_main)

# 手動輸入欄
st.markdown("或者直接粘贴英文报告：" if language == "简体中文" else
            "或直接貼上英文報告：" if language == "繁體中文" else
            "Or paste your English radiology report directly:")
manual_input = st.text_area("", value=report, height=200)
if manual_input:
    report = manual_input

# 🔍 AI 解說
if st.button("🔍 生成解說" if language != "English" else "🔍 Generate Explanation") and report:
    with st.spinner("AI 正在生成..." if language != "English" else "AI is generating..."):
        result = explain_report(report, language)
        st.markdown(result, unsafe_allow_html=True)
        with open("log.csv", "a") as log:
            log.write(datetime.now().isoformat() + "\n")
