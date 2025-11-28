"""
OpenAI模型接口实现
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class OpenAIModel(BaseModel):
    """OpenAI模型实现"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        初始化OpenAI模型
        
        Args:
            model_name: 模型名称（如gpt-4, gpt-3.5-turbo）
            api_key: OpenAI API密钥
            base_url: 自定义API地址（可选，用于代理）
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        使用OpenAI进行翻译
        
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
        """验证OpenAI配置"""
        return bool(self.api_key and self.model_name)

