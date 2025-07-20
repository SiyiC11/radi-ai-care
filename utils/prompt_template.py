# utils/prompt_template.py
"""
RadiAI.Care 提示詞模板管理
統一管理所有AI翻譯相關的提示詞和消息模板
"""

def get_prompt(language: str) -> str:
    """
    獲取翻譯提示詞
    
    Args:
        language: 目標語言代碼 ("traditional_chinese", "simplified_chinese")
        
    Returns:
        完整的系統提示詞
    """
    
    prompts = {
        "traditional_chinese": """你是一位資深的醫學翻譯專家和醫療科普作家，擁有豐富的放射科報告解讀經驗，專門協助將英文放射科報告翻譯並解釋給中文使用者。

請將以下英文放射科報告翻譯成繁體中文，並用專業且易懂的方式為患者和家屬進行科普解釋。

請嚴格按照以下格式組織你的回應，使用繁體中文：

## 📋 完整報告翻譯
將英文報告完整翻譯成繁體中文，保持：
- 醫學術語的準確性和專業性
- 原文的邏輯結構和段落劃分
- 重要信息的完整性

## 🔍 關鍵發現摘要
用3-5個清晰的要點總結報告中的主要發現：
• **[發現類別]**：用通俗語言描述具體發現
• **[發現類別]**：用通俗語言描述具體發現
• **[發現類別]**：用通俗語言描述具體發現

## 💡 重要醫學詞彙解釋
提取並詳細解釋5-8個關鍵醫學術語，使用以下格式：

**🔸 [醫學術語]**
*簡單定義*：用日常語言解釋這個詞的基本含義
*在此報告中的意義*：說明這個術語在當前檢查中代表什麼

## ❓ 建議向醫師諮詢的問題
根據報告內容，提供3-5個具體實用的問題：

**🔹 關於檢查結果：**
- [具體問題1]
- [具體問題2]

**🔹 關於後續治療：**
- [具體問題3]
- [具體問題4]

**🔹 關於日常注意事項：**
- [具體問題5]

請嚴格遵循以下指導原則：

✅ **內容要求**
- 使用溫和、專業且充滿同理心的語調
- 將複雜醫學術語轉換為患者能理解的日常語言
- 確保翻譯的準確性，不可隨意簡化重要醫學信息
- 使用清晰的層次結構和適當的表情符號

✅ **安全原則**
- 絕對不提供任何診斷結論或治療建議
- 如果報告中有模糊或不確定的地方，誠實說明並建議諮詢醫師
- 始終強調這只是翻譯和科普解釋，無法取代醫師的專業判斷
- 如發現可能的嚴重異常，溫和地建議及時就醫

**重要提醒：**
你的目標是幫助患者理解他們的醫學報告，同時保持嚴格的醫療安全標準。始終記住你是翻譯和科普專家，而不是醫生。所有的解釋都應該鼓勵患者與醫療專業人員進行進一步的討論。""",

        "simplified_chinese": """你是一位资深的医学翻译专家和医疗科普作家，拥有丰富的放射科报告解读经验，专门协助将英文放射科报告翻译并解释给中文使用者。

请将以下英文放射科报告翻译成简体中文，并用专业且易懂的方式为患者和家属进行科普解释。

请严格按照以下格式组织你的回应，使用简体中文：

## 📋 完整报告翻译
将英文报告完整翻译成简体中文，保持：
- 医学术语的准确性和专业性
- 原文的逻辑结构和段落划分
- 重要信息的完整性

## 🔍 关键发现摘要
用3-5个清晰的要点总结报告中的主要发现：
• **[发现类别]**：用通俗语言描述具体发现
• **[发现类别]**：用通俗语言描述具体发现
• **[发现类别]**：用通俗语言描述具体发现

## 💡 重要医学词汇解释
提取并详细解释5-8个关键医学术语，使用以下格式：

**🔸 [医学术语]**
*简单定义*：用日常语言解释这个词的基本含义
*在此报告中的意义*：说明这个术语在当前检查中代表什么

## ❓ 建议向医生咨询的问题
根据报告内容，提供3-5个具体实用的问题：

**🔹 关于检查结果：**
- [具体问题1]
- [具体问题2]

**🔹 关于后续治疗：**
- [具体问题3]
- [具体问题4]

**🔹 关于日常注意事项：**
- [具体问题5]

请严格遵循以下指导原则：

✅ **内容要求**
- 使用温和、专业且充满同理心的语调
- 将复杂医学术语转换为患者能理解的日常语言
- 确保翻译的准确性，不可随意简化重要医学信息
- 使用清晰的层次结构和适当的表情符号

✅ **安全原则**
- 绝对不提供任何诊断结论或治疗建议
- 如果报告中有模糊或不确定的地方，诚实说明并建议咨询医师
- 始终强调这只是翻译和科普解释，无法取代医师的专业判断
- 如发现可能的严重异常，温和地建议及时就医

**重要提醒：**
你的目标是帮助患者理解他们的医学报告，同时保持严格的医疗安全标准。始终记住你是翻译和科普专家，而不是医生。所有的解释都应该鼓勵患者与医疗专业人员进行进一步的讨论。"""
    }
    
    return prompts.get(language, prompts["simplified_chinese"])

def get_processing_steps(language: str) -> list:
    """
    獲取處理步驟描述
    
    Args:
        language: 目標語言代碼
        
    Returns:
        處理步驟列表
    """
    
    steps = {
        "traditional_chinese": [
            "🔍 正在分析報告結構和內容...",
            "🔄 正在翻譯專業醫學術語...",
            "💡 正在生成通俗易懂的解釋...",
            "❓ 正在整理實用的諮詢問題...",
            "✨ 正在優化格式和排版..."
        ],
        
        "simplified_chinese": [
            "🔍 正在分析报告结构和内容...",
            "🔄 正在翻译专业医学术语...",
            "💡 正在生成通俗易懂的解释...",
            "❓ 正在整理实用的咨询问题...",
            "✨ 正在优化格式和排版..."
        ]
    }
    
    return steps.get(language, steps["simplified_chinese"])

def create_enhanced_disclaimer(language: str) -> str:
    """
    創建增強的免責聲明
    
    Args:
        language: 目標語言代碼
        
    Returns:
        格式化的免責聲明HTML
    """
    
    disclaimers = {
        "traditional_chinese": """

<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border: 2px solid #ff9800; border-radius: 12px; padding: 1.5rem; margin-top: 2rem; box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);">
    <div style="text-align: center; font-weight: bold; color: #bf360c; font-size: 1.1rem; margin-bottom: 1rem;">
        ⚠️ 重要醫療免責聲明
    </div>
    <div style="color: #d84315; font-weight: 500; line-height: 1.6;">
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>純翻譯服務</strong>：以上內容僅為醫學報告的翻譯和科普解釋，不構成任何醫療建議、診斷或治療建議。
        </div>
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>專業諮詢</strong>：所有醫療決策請務必諮詢您的主治醫師或其他醫療專業人員。
        </div>
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>緊急情況</strong>：如有任何緊急醫療狀況，請立即撥打000或前往最近的急診室。
        </div>
        <div style="text-align: center; margin-top: 1rem; font-style: italic;">
            您的健康是最重要的，請勿僅依賴此翻譯做出醫療決定。
        </div>
    </div>
</div>""",

        "simplified_chinese": """

<div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); border: 2px solid #ff9800; border-radius: 12px; padding: 1.5rem; margin-top: 2rem; box-shadow: 0 4px 15px rgba(255, 152, 0, 0.15);">
    <div style="text-align: center; font-weight: bold; color: #bf360c; font-size: 1.1rem; margin-bottom: 1rem;">
        ⚠️ 重要医疗免责声明
    </div>
    <div style="color: #d84315; font-weight: 500; line-height: 1.6;">
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>纯翻译服务</strong>：以上内容仅为医学报告的翻译和科普解释，不构成任何医疗建议、诊断或治疗建议。
        </div>
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>专业咨询</strong>：所有医疗决策请务必咨询您的主治医师或其他医疗专业人员。
        </div>
        <div style="margin-bottom: 0.8rem;">
            🔸 <strong>紧急情况</strong>：如有任何紧急医疗状况，请立即拨打000或前往最近的急诊室。
        </div>
        <div style="text-align: center; margin-top: 1rem; font-style: italic;">
            您的健康是最重要的，请勿仅依赖此翻译做出医疗决定。
        </div>
    </div>
</div>"""
    }
    
    return disclaimers.get(language, disclaimers["simplified_chinese"])

def get_error_messages(language: str) -> dict:
    """
    獲取錯誤消息
    
    Args:
        language: 目標語言代碼
        
    Returns:
        錯誤消息字典
    """
    
    error_messages = {
        "traditional_chinese": {
            "invalid_report": "❌ 上傳的內容似乎不是完整的放射科報告。請確認您上傳的是包含檢查發現和醫師結論的完整醫學報告文件。",
            "file_too_large": "❌ 檔案過大。請壓縮圖片或上傳小於10MB的檔案。",
            "unsupported_format": "❌ 不支援的檔案格式。請上傳PDF、TXT或DOCX檔案。",
            "content_too_short": "❌ 內容過短。請確保包含完整的醫學報告內容。",
            "no_medical_content": "⚠️ 內容中未發現明顯的醫學術語。請確認這是一份放射科報告。",
            "api_error": "❌ AI服務暫時不可用。請稍後再試，或檢查網絡連接。",
            "processing_error": "❌ 處理過程中發生錯誤。請稍後再試，如問題持續，請聯繫技術支援。"
        },
        
        "simplified_chinese": {
            "invalid_report": "❌ 上传的内容似乎不是完整的放射科报告。请确认您上传的是包含检查发现和医师结论的完整医学报告文件。",
            "file_too_large": "❌ 文件过大。请压缩图片或上传小于10MB的文件。",
            "unsupported_format": "❌ 不支持的文件格式。请上传PDF、TXT或DOCX文件。",
            "content_too_short": "❌ 内容过短。请确保包含完整的医学报告内容。",
            "no_medical_content": "⚠️ 内容中未发现明显的医学术语。请确认这是一份放射科报告。",
            "api_error": "❌ AI服务暂时不可用。请稍后再试，或检查网络连接。",
            "processing_error": "❌ 处理过程中发生错误。请稍后再试，如问题持续，请联系技术支持。"
        }
    }
    
    return error_messages.get(language, error_messages["simplified_chinese"])

def get_success_messages(language: str) -> dict:
    """
    獲取成功消息
    
    Args:
        language: 目標語言代碼
        
    Returns:
        成功消息字典
    """
    
    success_messages = {
        "traditional_chinese": {
            "file_uploaded": "✅ 文件上傳成功！正在處理內容...",
            "text_received": "✅ 文字內容已接收！準備開始翻譯...",
            "translation_started": "🚀 開始智能解讀您的報告...",
            "translation_complete": "🎉 解讀完成！希望這些解釋對您有幫助。",
            "validation_passed": "✅ 報告內容驗證通過，包含有效的醫學信息。"
        },
        
        "simplified_chinese": {
            "file_uploaded": "✅ 文件上传成功！正在处理内容...",
            "text_received": "✅ 文字内容已接收！准备开始翻译...",
            "translation_started": "🚀 开始智能解读您的报告...",
            "translation_complete": "🎉 解读完成！希望这些解释对您有帮助。",
            "validation_passed": "✅ 报告内容验证通过，包含有效的医学信息。"
        }
    }
    
    return success_messages.get(language, success_messages["simplified_chinese"])
