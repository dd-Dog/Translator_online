"""
翻译策略基类
"""

from abc import ABC, abstractmethod
from typing import List
from src.models.base import TranslationRequest, TranslationResponse


class BaseStrategy(ABC):
    """翻译策略基类"""
    
    def __init__(self, **kwargs):
        """初始化策略"""
        self.config = kwargs
    
    @abstractmethod
    async def combine_translations(
        self,
        request: TranslationRequest,
        responses: List[TranslationResponse]
    ) -> TranslationResponse:
        """
        合并多个模型的翻译结果
        
        Args:
            request: 原始翻译请求
            responses: 多个模型的翻译响应列表
            
        Returns:
            TranslationResponse: 合并后的翻译响应
        """
        pass
    
    def filter_valid_responses(self, responses: List[TranslationResponse]) -> List[TranslationResponse]:
        """
        过滤有效的翻译响应（去除错误响应）
        
        Args:
            responses: 翻译响应列表
            
        Returns:
            List[TranslationResponse]: 有效的翻译响应列表
        """
        return [r for r in responses if r.error is None and r.translated_text]

