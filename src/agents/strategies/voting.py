"""
投票策略：多个模型翻译结果投票选择最佳结果
"""

from typing import List
from collections import Counter
from src.models.base import TranslationRequest, TranslationResponse
from .base import BaseStrategy


class VotingStrategy(BaseStrategy):
    """
    投票策略
    通过统计多个模型翻译结果，选择出现次数最多的结果
    """
    
    def __init__(self, min_models: int = 2, similarity_threshold: float = 0.8, **kwargs):
        """
        初始化投票策略
        
        Args:
            min_models: 最少需要的模型数量
            similarity_threshold: 相似度阈值（用于判断是否为相同翻译）
        """
        super().__init__(**kwargs)
        self.min_models = min_models
        self.similarity_threshold = similarity_threshold
    
    async def combine_translations(
        self,
        request: TranslationRequest,
        responses: List[TranslationResponse]
    ) -> TranslationResponse:
        """
        使用投票机制合并翻译结果
        
        Args:
            request: 原始翻译请求
            responses: 多个模型的翻译响应列表
            
        Returns:
            TranslationResponse: 合并后的翻译响应
        """
        valid_responses = self.filter_valid_responses(responses)
        
        if len(valid_responses) < self.min_models:
            # 如果有效响应不足，返回第一个有效响应或错误
            if valid_responses:
                return valid_responses[0]
            else:
                return TranslationResponse(
                    translated_text="",
                    error=f"需要至少{self.min_models}个模型响应，但只有{len(valid_responses)}个有效响应"
                )
        
        # 简单的投票：选择出现次数最多的翻译
        # 注意：这里使用精确匹配，未来可以改进为相似度匹配
        translations = [r.translated_text for r in valid_responses]
        counter = Counter(translations)
        
        # 获取得票最多的翻译
        most_common = counter.most_common(1)[0]
        best_translation = most_common[0]
        vote_count = most_common[1]
        
        # 计算置信度（得票数 / 总模型数）
        confidence = vote_count / len(valid_responses)
        
        # 找到对应的响应（用于获取其他信息）
        best_response = next(r for r in valid_responses if r.translated_text == best_translation)
        
        return TranslationResponse(
            translated_text=best_translation,
            confidence=confidence,
            model_name=f"Voting({vote_count}/{len(valid_responses)})",
            source_lang=best_response.source_lang
        )

