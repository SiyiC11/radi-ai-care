"""
RadiAI.Care 提示詞模板管理（增強版）
基於最新醫學 AI 研究優化的提示詞系統
"""

def get_prompt(language: str) -> str:
    """
    獲取優化的翻譯提示詞
    
    Args:
        language: 目標語言代碼 ("traditional_chinese", "simplified_chinese")
        
    Returns:
        完整的系統提示詞
    """
    
    prompts = {
        "traditional_chinese": """你是一位資深的醫學翻譯專家和醫療科普作家，擁有豐富的放射科報告解讀經驗，專門協助將英文放射科報告翻譯並解釋給中文使用者。

你的專業背景包括：
- 醫學影像學專業知識
- 中英文醫學術語對照經驗  
- 醫療健康科普寫作能力
- 澳洲醫療體系了解

請將以下英文放射科報告翻譯成繁體中文，並用專業且易懂的方式為患者和家屬進行科普解釋。

**重要格式要求：**
- 所有疾病名稱、病症名稱、異常發現必須用 **粗體** 標示
- 例如：**肺炎**、**結節**、**骨折**、**腫瘤**、**發炎**等
- 解剖結構正常時不需要加粗，只有異常發現才加粗
- 請確保醫學診斷術語的醒目顯示

請嚴格按照以下格式組織你的回應，使用繁體中文：

## 📋 完整報告翻譯
將英文報告完整翻譯成繁體中文，保持：
- 醫學術語的準確性和專業性
- 原文的邏輯結構和段落劃分
- 重要信息的完整性
- 澳洲醫療體系的術語習慣
- **所有疾病/異常發現名稱必須用粗體標示**

## 🔍 關鍵發現摘要
用3-6個清晰的要點總結報告中的主要發現：
• **[發現類別]**：用通俗語言描述具體發現（**疾病名稱用粗體**）
• **[發現類別]**：用通俗語言描述具體發現（**疾病名稱用粗體**）
• **[發現類別]**：用通俗語言描述具體發現（**疾病名稱用粗體**）

## 💡 重要醫學詞彙解釋
提取並詳細解釋5-8個關鍵醫學術語，使用以下格式：

**🔸 [醫學術語]**
*簡單定義*：用日常語言解釋這個詞的基本含義
*在此報告中的意義*：說明這個術語在當前檢查中代表什麼（**疾病相關詞彙用粗體**）

## ❓ 建議向醫師諮詢的問題
根據報告內容，提供3-5個具體實用的問題：

**🔹 關於檢查結果：**
- [具體問題1 - 針對主要發現，**疾病名稱用粗體**]
- [具體問題2 - 針對需要澄清的部分]

**🔹 關於後續處理：**
- [具體問題3 - 針對追蹤檢查]
- [具體問題4 - 針對治療選項]

**🔹 關於生活注意事項：**
- [具體問題5 - 針對日常護理]

## 📞 澳洲醫療系統資源
**如需進一步協助：**
- 🏥 **家庭醫師 (GP)**：首要聯繫人，協調所有醫療服務
- 📞 **健康直線 (Healthdirect)**：1800 022 222（24小時健康建議）
- 🆘 **緊急情況**：000（救護車、消防、警察）
- 💊 **藥物諮詢**：當地藥劑師或 Medicines Line 1300 MEDICINE

請嚴格遵循以下指導原則：

✅ **內容要求**
- 使用溫和、專業且充滿同理心的語調
- 將複雜醫學術語轉換為患者能理解的日常語言
- 確保翻譯的準確性，不可隨意簡化重要醫學信息
- 使用清晰的層次結構和適當的表情符號
- 結合澳洲醫療體系的實際情況
- **重要：所有疾病名稱、病症名稱、異常發現都必須用粗體（**名稱**）格式標示**

✅ **安全原則**
- 絕對不提供任何診斷結論或治療建議
- 如果報告中有模糊或不確定的地方，誠實說明並建議諮詢醫師
- 始終強調這只是翻譯和科普解釋，無法取代醫師的專業判斷
- 如發現可能的嚴重異常，溫和地建議及時就醫
- 提供澳洲醫療系統的實用資源信息

**重要提醒：**
你的目標是幫助患者理解他們的醫學報告，同時保持嚴格的醫療安全標準。始終記住你是翻譯和科普專家，而不是醫生。所有的解釋都應該鼓勵患者與醫療專業人員進行進一步的討論。""",

        "simplified_chinese": """你是一位资深的医学翻译专家和医疗科普作家，拥有丰富的放射科报告解读经验，专门协助将英文放射科报告翻译并解释给中文使用者。

你的专业背景包括：
- 医学影像学专业知识
- 中英文医学术语对照经验  
- 医疗健康科普写作能力
- 澳洲医疗体系了解

请将以下英文放射科报告翻译成简体中文，并用专业且易懂的方式为患者和家属进行科普解释。

**重要格式要求：**
- 所有疾病名称、病症名称、异常发现必须用 **粗体** 标示
- 例如：**肺炎**、**结节**、**骨折**、**肿瘤**、**发炎**等
- 解剖结构正常时不需要加粗，只有异常发现才加粗
- 请确保医学诊断术语的醒目显示

请严格按照以下格式组织你的回应，使用简体中文：

## 📋 完整报告翻译
将英文报告完整翻译成简体中文，保持：
- 医学术语的准确性和专业性
- 原文的逻辑结构和段落划分
- 重要信息的完整性
- 澳洲医疗体系的术语习惯
- **所有疾病/异常发现名称必须用粗体标示**

## 🔍 关键发现摘要
用3-5个清晰的要点总结报告中的主要发现：
• **[发现类别]**：用通俗语言描述具体发现（**疾病名称用粗体**）
• **[发现类别]**：用通俗语言描述具体发现（**疾病名称用粗体**）
• **[发现类别]**：用通俗语言描述具体发现（**疾病名称用粗体**）

## 💡 重要医学词汇解释
提取并详细解释5-8个关键医学术语，使用以下格式：

**🔸 [医学术语]**
*简单定义*：用日常语言解释这个词的基本含义
*在此报告中的意义*：说明这个术语在当前检查中代表什么（**疾病相关词汇用粗体**）

## ❓ 建议向医生咨询的问题
根据报告内容，提供3-5个具体实用的问题：

**🔹 关于检查结果：**
- [具体问题1 - 针对主要发现，**疾病名称用粗体**]
- [具体问题2 - 针对需要澄清的部分]

**🔹 关于后续处理：**
- [具体问题3 - 针对追踪检查]
- [具体问题4 - 针对治疗选项]

**🔹 关于生活注意事项：**
- [具体问题5 - 针对日常护理]

## 📞 澳洲医疗系统资源
**如需进一步协助：**
- 🏥 **家庭医生 (GP)**：首要联系人，协调所有医疗服务
- 📞 **健康直线 (Healthdirect)**：1800 022 222（24小时健康建议）
- 🆘 **紧急情况**：000（救护车、消防、警察）
- 💊 **药物咨询**：当地药剂师或 Medicines Line 1300 MEDICINE

请严格遵循以下指导原则：

✅ **内容要求**
- 使用温和、专业且充满同理心的语调
- 将复杂医学术语转换为患者能理解的日常语言
- 确保翻译的准确性，不可随意简化重要医学信息
- 使用清晰的层次结构和适当的表情符号
- 结合澳洲医疗体系的实际情况
- **重要：所有疾病名称、病症名称、异常发现都必须用粗体（**名称**）格式标示**

✅ **安全原则**
- 绝对不提供任何诊断结论或治疗建议
- 如果报告中有模糊或不确定的地方，诚实说明并建议咨询医师
- 始终强调这只是翻译和科普解释，无法取代医师的专业判断
- 如发现可能的严重异常，温和地建议及时就医
- 提供澳洲医疗系统的实用资源信息

**重要提醒：**
你的目标是帮助患者理解他们的医学报告，同时保持严格的医疗安全标准。始终记住你是翻译和科普专家，而不是医生。所有的解释都应该鼓励患者与医疗专业人员进行进一步的讨论。"""
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
            "🔍 正在分析報告結構和醫學術語...",
            "🔄 正在翻譯專業醫學內容...",
            "💡 正在生成通俗易懂的解釋...",
            "✨ 正在標示重要疾病名稱...",
            "🏥 正在整合澳洲醫療系統資源...",
            "❓ 正在準備實用的諮詢問題...",
            "✨ 正在優化格式和排版..."
        ],
        
        "simplified_chinese": [
            "🔍 正在分析报告结构和医学术语...",
            "🔄 正在翻译专业医学内容...",
            "💡 正在生成通俗易懂的解释...",
            "✨ 正在标示重要疾病名称...",
            "🏥 正在整合澳洲医疗系统资源...",
            "❓ 正在准备实用的咨询问题...",
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
            🔸 <strong>翻譯準確性</strong>：AI翻譯可能存在錯誤，請與醫師核實所有重要醫療資訊。
        </div>
        <div style="text-align: center; margin-top: 1rem; padding: 0.8rem; background: rgba(255, 193, 7, 0.1); border-radius: 8px; font-style: italic;">
            🆘 如有任何緊急醫療狀況，請立即撥打000或前往最近的急診室
        </div>
    </div>
</div>
        """,
        
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
            🔸 <strong>翻译准确性</strong>：AI翻译可能存在错误，请与医师核实所有重要医疗信息。
        </div>
        <div style="text-align: center; margin-top: 1rem; padding: 0.8rem; background: rgba(255, 193, 7, 0.1); border-radius: 8px; font-style: italic;">
            🆘 如有任何紧急医疗状况，请立即拨打000或前往最近的急诊室
        </div>
    </div>
</div>
        """
    }
    
    return disclaimers.get(language, disclaimers["simplified_chinese"])


def get_error_messages(language: str) -> dict:
    """
    獲取錯誤訊息
    
    Args:
        language: 目標語言代碼
        
    Returns:
        錯誤訊息字典
    """
    
    messages = {
        "traditional_chinese": {
            "empty_input": "請輸入報告內容或上傳檔案",
            "content_too_short": "內容過短，請確保包含完整的醫學報告內容",
            "content_too_long": "內容過長，請分段處理",
            "no_medical_terms": "內容中未發現明顯的醫學術語，請確認這是一份放射科報告",
            "translation_failed": "翻譯失敗，請稍後重試",
            "api_error": "AI服務暫時不可用，請稍後重試",
            "rate_limit": "請求過於頻繁，請稍後重試",
            "timeout": "請求超時，請檢查網路連線後重試"
        },
        
        "simplified_chinese": {
            "empty_input": "请输入报告内容或上传文件",
            "content_too_short": "内容过短，请确保包含完整的医学报告内容",
            "content_too_long": "内容过长，请分段处理",
            "no_medical_terms": "内容中未发现明显的医学术语，请确认这是一份放射科报告",
            "translation_failed": "翻译失败，请稍后重试",
            "api_error": "AI服务暂时不可用，请稍后重试",
            "rate_limit": "请求过于频繁，请稍后重试",
            "timeout": "请求超时，请检查网络连接后重试"
        }
    }
    
    return messages.get(language, messages["simplified_chinese"])


def get_success_messages(language: str) -> dict:
    """
    獲取成功訊息
    
    Args:
        language: 目標語言代碼
        
    Returns:
        成功訊息字典
    """
    
    messages = {
        "traditional_chinese": {
            "translation_complete": "🎉 翻譯完成！",
            "file_uploaded": "✅ 檔案上傳成功",
            "validation_passed": "✅ 內容驗證通過",
            "feedback_submitted": "感謝您的回饋！"
        },
        
        "simplified_chinese": {
            "translation_complete": "🎉 翻译完成！",
            "file_uploaded": "✅ 文件上传成功",
            "validation_passed": "✅ 内容验证通过",
            "feedback_submitted": "感谢您的反馈！"
        }
    }
    
    return messages.get(language, messages["simplified_chinese"])


def get_medical_terminology_guide(language: str) -> dict:
    """
    獲取醫學術語指南
    
    Args:
        language: 目標語言代碼
        
    Returns:
        醫學術語指南字典
    """
    
    guides = {
        "traditional_chinese": {
            "imaging_types": {
                "CT": "電腦斷層掃描",
                "MRI": "磁共振影像",
                "X-ray": "X光檢查",
                "Ultrasound": "超音波檢查"
            },
            "anatomy": {
                "chest": "胸部",
                "abdomen": "腹部",
                "brain": "腦部",
                "spine": "脊椎"
            },
            "findings": {
                "normal": "正常",
                "abnormal": "異常",
                "lesion": "病變",
                "mass": "腫塊"
            }
        },
        
        "simplified_chinese": {
            "imaging_types": {
                "CT": "电脑断层扫描",
                "MRI": "磁共振影像",
                "X-ray": "X光检查",
                "Ultrasound": "超声波检查"
            },
            "anatomy": {
                "chest": "胸部",
                "abdomen": "腹部",
                "brain": "脑部",
                "spine": "脊椎"
            },
            "findings": {
                "normal": "正常",
                "abnormal": "异常",
                "lesion": "病变",
                "mass": "肿块"
            }
        }
    }
    
    return guides.get(language, guides["simplified_chinese"])


def validate_prompt_response(response_text: str, language: str) -> dict:
    """
    驗證提示詞回應的質量
    
    Args:
        response_text: AI回應文本
        language: 語言代碼
        
    Returns:
        驗證結果字典
    """
    
    required_sections = ["📋", "🔍", "💡", "❓", "📞"]
    found_sections = sum(1 for section in required_sections if section in response_text)
    
    # 檢查粗體標記
    bold_count = response_text.count("**")
    has_bold_formatting = bold_count >= 4  # 至少有兩對粗體標記
    
    # 檢查長度
    is_adequate_length = len(response_text) >= 500
    
    # 質量評分
    quality_score = 0
    if found_sections >= 4:
        quality_score += 40
    if has_bold_formatting:
        quality_score += 30
    if is_adequate_length:
        quality_score += 30
    
    return {
        "quality_score": quality_score,
        "found_sections": found_sections,
        "required_sections": len(required_sections),
        "has_bold_formatting": has_bold_formatting,
        "is_adequate_length": is_adequate_length,
        "word_count": len(response_text.split()),
        "character_count": len(response_text)
    }
