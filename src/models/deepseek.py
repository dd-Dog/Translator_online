"""
DeepSeek模型接口实现
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class DeepSeekModel(BaseModel):
    """DeepSeek模型实现（通过OpenAI兼容接口）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str = "https://api.deepseek.com", **kwargs):
        """
        初始化DeepSeek模型
        
        Args:
            model_name: 模型名称（如deepseek-chat, deepseek-coder）
            api_key: DeepSeek API密钥
            base_url: API基础URL
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        使用DeepSeek进行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(request)
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，擅长自然流畅的中文表达。"},
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
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español"
        }
        
        target_lang_name = lang_map.get(request.target_lang, request.target_lang)
        
        prompt = f"请将以下文本翻译成{target_lang_name}，要求翻译自然流畅，符合目标语言的表达习惯：\n\n{request.text}"
        
        if request.context:
            prompt += f"\n\n上下文：{request.context}"
        
        if request.source_lang != "auto":
            source_lang_name = lang_map.get(request.source_lang, request.source_lang)
            prompt = f"请将以下{source_lang_name}文本翻译成{target_lang_name}，要求翻译自然流畅：\n\n{request.text}"
        
        return prompt
    
    def validate_config(self) -> bool:
        """验证DeepSeek配置"""
        return bool(self.api_key and self.model_name)

