"""
Google Gemini模型接口实现
支持通过OpenRouter调用（国内可用）
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class GeminiModel(BaseModel):
    """Google Gemini模型实现（通过OpenRouter）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None, 
                 use_openrouter: bool = True, **kwargs):
        """
        初始化Gemini模型
        
        Args:
            model_name: 模型名称（如gemini-pro，使用OpenRouter时格式为google/gemini-pro）
            api_key: API密钥（OpenRouter API密钥）
            base_url: API基础URL（默认使用OpenRouter）
            use_openrouter: 是否使用OpenRouter（默认True，国内推荐）
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        self.use_openrouter = use_openrouter
        
        if use_openrouter:
            # 使用OpenRouter
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            # OpenRouter模型名称格式：google/gemini-2.5-flash
            # 如果已经是完整格式，直接使用；否则尝试转换
            if model_name.startswith("google/"):
                self.openrouter_model = model_name
            elif model_name.startswith("gemini"):
                # 兼容旧格式：gemini-pro -> google/gemini-2.5-flash
                self.openrouter_model = f"google/{model_name}"
            else:
                self.openrouter_model = model_name
        else:
            # 直接使用Gemini API（需要google-generativeai库）
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model_name)
                self.base_url = None
            except ImportError:
                raise ImportError("需要安装google-generativeai库：pip install google-generativeai")
        
        # 创建OpenAI兼容客户端（用于OpenRouter）
        if use_openrouter:
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
        使用Gemini进行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        try:
            if self.use_openrouter:
                # 通过OpenRouter调用
                prompt = self._build_prompt(request)
                
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
            else:
                # 直接使用Gemini API
                prompt = self._build_prompt(request)
                generation_config = {
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                }
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

