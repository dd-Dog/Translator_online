"""
加权策略：根据模型权重加权选择最佳翻译结果
"""

from typing import List, Dict
from src.models.base import TranslationRequest, TranslationResponse
from .base import BaseStrategy


class WeightedStrategy(BaseStrategy):
    """
    加权策略
    根据预定义的模型权重，选择加权得分最高的翻译结果
    """
    
    def __init__(self, model_weights: Dict[str, float] = None, **kwargs):
        """
        初始化加权策略
        
        Args:
            model_weights: 模型权重字典，格式：{model_name: weight}
        """
        super().__init__(**kwargs)
        self.model_weights = model_weights or {}
        # 如果没有提供权重，默认均等权重
        self.default_weight = 1.0
    
    async def combine_translations(
        self,
        request: TranslationRequest,
        responses: List[TranslationResponse]
    ) -> TranslationResponse:
        """
        使用加权机制合并翻译结果
        
        Args:
            request: 原始翻译请求
            responses: 多个模型的翻译响应列表
            
        Returns:
            TranslationResponse: 合并后的翻译响应
        """
        valid_responses = self.filter_valid_responses(responses)
        
        if not valid_responses:
            return TranslationResponse(
                translated_text="",
                error="没有有效的翻译响应"
            )
        
        # 计算每个翻译的加权得分
        translation_scores: Dict[str, float] = {}
        translation_responses: Dict[str, TranslationResponse] = {}
        
        for response in valid_responses:
            # 获取模型权重
            weight = self.model_weights.get(response.model_name, self.default_weight)
            
            # 累加相同翻译的权重
            if response.translated_text in translation_scores:
                translation_scores[response.translated_text] += weight
            else:
                translation_scores[response.translated_text] = weight
                translation_responses[response.translated_text] = response
        
        # 选择得分最高的翻译
        best_translation = max(translation_scores.items(), key=lambda x: x[1])
        best_text = best_translation[0]
        best_score = best_translation[1]
        
        # 计算总权重用于归一化置信度
        total_weight = sum(self.model_weights.get(r.model_name, self.default_weight) 
                          for r in valid_responses)
        confidence = best_score / total_weight if total_weight > 0 else 0.0
        
        best_response = translation_responses[best_text]
        
        return TranslationResponse(
            translated_text=best_text,
            confidence=confidence,
            model_name=f"Weighted(score={best_score:.2f})",
            source_lang=best_response.source_lang
        )

