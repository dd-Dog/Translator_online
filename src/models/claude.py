"""
Anthropic Claude模型接口实现
通过OpenRouter调用（国内可用）
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class ClaudeModel(BaseModel):
    """Anthropic Claude模型实现（通过OpenRouter）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        初始化Claude模型
        
        Args:
            model_name: 模型名称（如claude-3-opus，使用OpenRouter时格式为anthropic/claude-3-opus）
            api_key: OpenRouter API密钥
            base_url: API基础URL（默认使用OpenRouter）
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        
        # OpenRouter配置
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        # OpenRouter模型名称格式：anthropic/claude-3.5-haiku
        # 如果已经是完整格式，直接使用；否则尝试转换
        if model_name.startswith("anthropic/"):
            self.openrouter_model = model_name
        elif model_name.startswith("claude"):
            # 兼容旧格式：claude-3-opus -> anthropic/claude-3-opus
            self.openrouter_model = f"anthropic/{model_name}"
        else:
            self.openrouter_model = model_name
        
        # 创建OpenAI兼容客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            default_headers={
                "HTTP-Referer": kwargs.get("http_referer", "https://github.com/dd-Dog/Translator_online"),
                "X-Title": kwargs.get("x_title", "Translator Agent")
            }
        )
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        使用Claude进行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(request)
            
            # 调用OpenRouter API
            response = self.client.chat.completions.create(
                model=self.openrouter_model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            translated_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else None
            
            return TranslationResponse(
                translated_text=translated_text,
                model_name=self.model_name,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            return TranslationResponse(
                translated_text="",
                model_name=self.model_name,
                error=str(e)
            )
    
    def _build_prompt(self, request: TranslationRequest) -> str:
        """构建翻译提示词"""
        lang_map = {
            "zh": "Chinese",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean",
            "fr": "French",
            "de": "German",
            "es": "Spanish"
        }
        
        target_lang_name = lang_map.get(request.target_lang, request.target_lang)
        
        prompt = f"Translate the following text to {target_lang_name}:\n\n{request.text}"
        
        if request.context:
            prompt += f"\n\nContext: {request.context}"
        
        if request.source_lang != "auto":
            source_lang_name = lang_map.get(request.source_lang, request.source_lang)
            prompt = f"Translate the following {source_lang_name} text to {target_lang_name}:\n\n{request.text}"
        
        return prompt
    
    def validate_config(self) -> bool:
        """验证Claude配置"""
        return bool(self.api_key and self.model_name)

