"""
豆包（Doubao）模型接口实现
字节跳动大模型
"""

import os
from typing import Optional
from openai import OpenAI
from .base import BaseModel, TranslationRequest, TranslationResponse


class DoubaoModel(BaseModel):
    """豆包模型实现（通过OpenAI兼容接口）"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3", **kwargs):
        """
        初始化豆包模型
        
        Args:
            model_name: 模型名称（如doubao-pro-32k, doubao-lite-4k, doubao-pro-128k）
            api_key: 豆包 API密钥
            base_url: API基础URL（默认使用火山引擎）
            **kwargs: 其他参数
        """
        super().__init__(model_name, api_key, **kwargs)
        self.base_url = base_url  # 保存base_url以便后续查询
        # 确保api_key不为None，避免OpenAI SDK回退到环境变量
        if not api_key:
            raise ValueError("Doubao API_KEY不能为空")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        # 验证客户端实际使用的API_KEY（用于调试）
        actual_api_key = getattr(self.client, 'api_key', None) or getattr(self.client, '_client', {}).get('api_key', None)
        if actual_api_key and actual_api_key != api_key:
            import warnings
            warnings.warn(f"Doubao客户端实际使用的API_KEY与传入的不同！传入: {api_key[:8]}..., 实际: {actual_api_key[:8] if actual_api_key else 'None'}...")
    
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        使用豆包进行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(request)
            
            # 在调用前记录实际使用的API_KEY（用于调试）
            import os
            env_api_key = os.getenv('DOUBAO_API_KEY', '')
            if env_api_key and env_api_key != self.api_key:
                print(f"[Doubao API调用警告] 环境变量中存在DOUBAO_API_KEY，但使用的是用户传入的API_KEY: {self.api_key[:8]}...")
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的翻译助手，擅长自然流畅的中文表达。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=request.temperature if hasattr(request, 'temperature') else self.config.get('temperature', 0.3),
                max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else self.config.get('max_tokens', 2000)
            )
            
            translated_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else None
            
            return TranslationResponse(
                translated_text=translated_text,
                model_name=self.model_name,
                tokens_used=tokens_used
            )
            
        except Exception as e:
            error_msg = str(e)
            # 检查是否是API_KEY相关的错误
            if "401" in error_msg or "Unauthorized" in error_msg or "Invalid API key" in error_msg or "authentication" in error_msg.lower():
                print(f"[Doubao API错误] API_KEY验证失败！使用的API_KEY: {self.api_key[:8]}...")
                print(f"[Doubao API错误] 错误详情: {error_msg}")
            return TranslationResponse(
                translated_text="",
                model_name=self.model_name,
                error=error_msg
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
        
        if hasattr(request, 'context') and request.context:
            prompt += f"\n\n上下文：{request.context}"
        
        if request.source_lang != "auto":
            source_lang_name = lang_map.get(request.source_lang, request.source_lang)
            prompt = f"请将以下{source_lang_name}文本翻译成{target_lang_name}，要求翻译自然流畅：\n\n{request.text}"
        
        return prompt
    
    def validate_config(self) -> bool:
        """验证豆包配置"""
        return bool(self.api_key and self.model_name)

