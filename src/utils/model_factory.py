"""
模型工厂：从配置文件创建模型实例
"""

import os
from typing import Dict, Optional
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
from src.models.deepseek import DeepSeekModel
from src.models.claude import ClaudeModel


def create_model_from_config(model_config: Dict, model_type: str):
    """
    从配置创建模型实例
    
    Args:
        model_config: 模型配置字典
        model_type: 模型类型（openai, gemini, qwen, deepseek, claude）
        
    Returns:
        BaseModel: 模型实例，如果配置无效则返回None
    """
    if not model_config.get('enabled', False):
        return None
    
    api_key_env = model_config.get('api_key_env')
    if not api_key_env:
        return None
    
    api_key = os.getenv(api_key_env)
    if not api_key:
        return None
    
    model_name = model_config.get('model')
    if not model_name:
        return None
    
    params = model_config.get('params', {})
    base_url = model_config.get('base_url')
    
    try:
        if model_type == 'openai':
            model = OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
        elif model_type == 'gemini':
            use_openrouter = model_config.get('use_openrouter', True)
            model = GeminiModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'qwen':
            model = QwenModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                **params
            )
        elif model_type == 'deepseek':
            model = DeepSeekModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://api.deepseek.com",
                **params
            )
        elif model_type == 'claude':
            model = ClaudeModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://openrouter.ai/api/v1",
                **params
            )
        else:
            return None
        
        if model.validate_config():
            return model
        else:
            return None
            
    except Exception as e:
        print(f"创建模型 {model_type} 失败: {e}")
        return None

