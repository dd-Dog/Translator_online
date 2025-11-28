"""
Google Gemini模型接口实现
"""

import os
from typing import Optional
import google.generativeai as genai
from .base import BaseModel, TranslationRequest, TranslationResponse


class GeminiModel(BaseModel):
    """Google Gemini模型实现"""
    
    def __init__(self, model_name: str, api_key: str, **kwargs):
        """
        初始化Gemini模型
        
        Args:
            model_name: 模型名称（如gemini-pro）
            api_key: Gemini API密钥
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        使用Gemini进行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(request)
            
            # 配置生成参数
            generation_config = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
            }
            
            # 调用API
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            translated_text = response.text.strip()
            
            return TranslationResponse(
                translated_text=translated_text,
                model_name=self.model_name
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
        """验证Gemini配置"""
        return bool(self.api_key and self.model_name)

