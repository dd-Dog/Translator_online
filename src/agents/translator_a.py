"""
Translator-A Agent - 主译
使用Gemini进行多语言通用机器翻译
"""

from typing import Optional
from src.models.base import BaseModel, TranslationRequest, TranslationResponse
from src.agents.workflow import TranslationDraft, SelfCheckReport


class TranslatorA:
    """主译Agent（使用Gemini）"""
    
    def __init__(self, model: BaseModel):
        """
        初始化主译Agent
        
        Args:
            model: 翻译模型（通常是Gemini）
        """
        self.model = model
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        segment_id: Optional[str] = None
    ) -> TranslationDraft:
        """
        执行主翻译
        
        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            segment_id: 段落ID（可选）
            
        Returns:
            TranslationDraft: 翻译草稿（包含翻译文本和自检报告）
        """
        # 构建翻译提示词（包含自检要求）
        prompt = self._build_translation_prompt(text, source_lang, target_lang)
        
        request = TranslationRequest(
            text=prompt,
            source_lang=source_lang,
            target_lang=target_lang,
            temperature=0.3
        )
        
        response = await self.model.translate(request)
        
        # 解析翻译结果和自检报告
        translated_text, self_check = self._parse_response(response.translated_text, text)
        
        return TranslationDraft(
            translated_text=translated_text,
            self_check_report=self_check,
            model_name=self.model.model_name,
            segment_id=segment_id
        )
    
    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """构建翻译提示词"""
        lang_map = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español"
        }
        
        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)
        
        prompt = f"""请将以下{source_lang_name}文本翻译成{target_lang_name}。

原文：
{text}

要求：
1. 提供准确、流畅的翻译
2. 保持原文的语气和风格
3. 对于不确定的翻译，请标记出来

请按以下格式返回：
翻译：[翻译结果]

自检报告：
- 不确定的段落：[如果有，列出不确定的部分及原因]
- 置信度：[整体置信度，0-1之间]
- 建议：[任何建议或注意事项]
"""
        return prompt
    
    def _parse_response(self, response_text: str, original_text: str) -> tuple:
        """解析响应，提取翻译和自检报告"""
        import re
        
        # 提取翻译结果
        translation_match = re.search(r'翻译[：:]\s*(.+?)(?=自检报告|$)', response_text, re.DOTALL)
        translated_text = translation_match.group(1).strip() if translation_match else response_text.split('\n')[0].strip()
        
        # 提取自检报告
        self_check = None
        uncertain_match = re.search(r'不确定的段落[：:]\s*(.+?)(?=置信度|建议|$)', response_text, re.DOTALL)
        confidence_match = re.search(r'置信度[：:]\s*([0-9.]+)', response_text)
        suggestions_match = re.search(r'建议[：:]\s*(.+?)$', response_text, re.DOTALL)
        
        if uncertain_match or confidence_match:
            uncertain_segments = []
            if uncertain_match:
                uncertain_text = uncertain_match.group(1).strip()
                if uncertain_text and uncertain_text != "无" and uncertain_text != "无不确定段落":
                    uncertain_segments.append({
                        'text': uncertain_text,
                        'reason': '模型标记为不确定'
                    })
            
            confidence = 0.8  # 默认值
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1))
                except:
                    pass
            
            suggestions = []
            if suggestions_match:
                suggestions_text = suggestions_match.group(1).strip()
                if suggestions_text:
                    suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
            
            self_check = SelfCheckReport(
                uncertain_segments=uncertain_segments,
                confidence_scores={'overall': confidence},
                suggestions=suggestions
            )
        
        return translated_text, self_check

