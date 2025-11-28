"""
大模型基类
定义统一的模型接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class TranslationRequest:
    """翻译请求数据类"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    context: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000


@dataclass
class TranslationResponse:
    """翻译响应数据类"""
    translated_text: str
    source_lang: Optional[str] = None
    confidence: Optional[float] = None
    model_name: str = ""
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class BaseModel(ABC):
    """大模型基类，所有模型实现必须继承此类"""
    
    def __init__(self, model_name: str, api_key: str, **kwargs):
        """
        初始化模型
        
        Args:
            model_name: 模型名称
            api_key: API密钥
            **kwargs: 其他模型特定参数
        """
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        执行翻译
        
        Args:
            request: 翻译请求
            
        Returns:
            TranslationResponse: 翻译响应
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model_name": self.model_name,
            "provider": self.__class__.__name__,
            "config": self.config
        }

