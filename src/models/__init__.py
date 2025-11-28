"""
大模型接口模块
支持多种在线大模型API
"""

from .base import BaseModel
from .openai import OpenAIModel
from .gemini import GeminiModel
from .qwen import QwenModel
from .deepseek import DeepSeekModel

__all__ = [
    "BaseModel",
    "OpenAIModel",
    "GeminiModel",
    "QwenModel",
    "DeepSeekModel",
]

