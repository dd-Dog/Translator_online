"""
OpenAI模型接口实现
支持通过OpenRouter调用（国内可用）
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class OpenAIModel(BaseModel):
    """OpenAI模型实现（支持OpenRouter）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None, 
                 use_openrouter: bool = False, **kwargs):
        """
        初始化OpenAI模型
        
        Args:
            model_name: 模型名称（如gpt-4, gpt-3.5-turbo，使用OpenRouter时格式为openai/gpt-4）
            api_key: API密钥（OpenAI API密钥或OpenRouter API密钥）
            base_url: 自定义API地址（可选，使用OpenRouter时自动设置为OpenRouter地址）
            use_openrouter: 是否使用OpenRouter（默认False，使用OpenAI官方API）
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        self.use_openrouter = use_openrouter
        
        if use_openrouter:
            # 使用OpenRouter
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            # OpenRouter模型名称格式：openai/gpt-4
            # 如果已经是完整格式，直接使用；否则添加openai/前缀
            if model_name.startswith("openai/"):
                self.openrouter_model = model_name
            else:
                self.openrouter_model = f"openai/{model_name}"
        else:
            # 使用OpenAI官方API
            self.base_url = base_url
            self.openrouter_model = None
        
        # 创建OpenAI客户端
        client_kwargs = {
            "api_key": api_key,
        }
        
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        if use_openrouter:
            # OpenRouter需要额外的headers
            client_kwargs["default_headers"] = {
                "HTTP-Referer": kwargs.get("http_referer", "https://github.com/dd-Dog/Translator_online"),
                "X-Title": kwargs.get("x_title", "Translator Agent")
            }
        
        self.client = OpenAI(**client_kwargs)
    
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
            
            # 选择模型名称
            model_to_use = self.openrouter_model if self.use_openrouter else self.model_name
            
            # 调用API
            response = self.client.chat.completions.create(
                model=model_to_use,
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
                model_name=model_to_use,
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

