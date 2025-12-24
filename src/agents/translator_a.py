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
        
        # 调试：记录原始响应和错误
        if not response.translated_text or not response.translated_text.strip():
            import sys
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            try:
                from loguru import logger
            except ImportError:
                logger = None
            
            if logger:
                logger.warning(f"[TranslatorA] 原始响应为空或仅包含空白字符")
                logger.warning(f"[TranslatorA] 使用模型: {response.model_name if hasattr(response, 'model_name') else '未知'}")
                if hasattr(response, 'error') and response.error:
                    logger.error(f"[TranslatorA] API错误信息: {response.error}")
                    # 检查常见的错误类型
                    error_str = str(response.error)
                    if '402' in error_str or 'Insufficient Balance' in error_str or '余额不足' in error_str:
                        logger.error(f"[TranslatorA] ⚠️  API余额不足！请检查账户余额并充值")
                    elif '401' in error_str or 'Unauthorized' in error_str or 'Invalid API key' in error_str:
                        logger.error(f"[TranslatorA] ⚠️  API密钥无效！请检查.env文件中的API密钥配置")
                    elif '429' in error_str or 'Rate limit' in error_str:
                        logger.error(f"[TranslatorA] ⚠️  请求频率过高！请稍后重试")
                    elif '500' in error_str or 'Internal Server Error' in error_str:
                        logger.error(f"[TranslatorA] ⚠️  服务器内部错误！请稍后重试")
                    else:
                        logger.error(f"[TranslatorA] ⚠️  未知错误，请检查错误信息")
                else:
                    logger.warning(f"[TranslatorA] response.translated_text: {repr(response.translated_text)}")
        
        # 解析翻译结果和自检报告
        translated_text, self_check = self._parse_response(response.translated_text, text)
        
        # 如果解析后仍为空，使用原始响应的第一行
        if not translated_text or not translated_text.strip():
            if response.translated_text:
                # 尝试直接使用原始响应
                translated_text = response.translated_text.strip()
                # 如果包含"翻译："，尝试提取
                if "翻译" in translated_text:
                    lines = translated_text.split('\n')
                    for line in lines:
                        if "翻译" in line:
                            translated_text = line.split("翻译")[-1].split("：")[-1].split(":")[-1].strip()
                            break
        
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
        
        if not response_text or not response_text.strip():
            return "", None
        
        # 提取翻译结果
        translation_match = re.search(r'翻译[：:]\s*(.+?)(?=自检报告|$)', response_text, re.DOTALL)
        if translation_match:
            translated_text = translation_match.group(1).strip()
        else:
            # 如果没有找到"翻译："标记，尝试其他方式
            # 先尝试第一行
            first_line = response_text.split('\n')[0].strip()
            if first_line and len(first_line) > 0:
                translated_text = first_line
            else:
                # 如果第一行也是空的，尝试整个文本
                translated_text = response_text.strip()
        
        # 如果还是空的，返回空字符串
        if not translated_text:
            translated_text = ""
        
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

