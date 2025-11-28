"""
主翻译Agent类
协调多个模型和策略完成翻译任务
"""

import asyncio
from typing import List, Dict, Optional
from src.models.base import BaseModel, TranslationRequest, TranslationResponse
from src.agents.strategies.base import BaseStrategy
from src.agents.strategies.voting import VotingStrategy
from src.agents.strategies.weighted import WeightedStrategy


class TranslatorAgent:
    """多模型翻译Agent"""
    
    def __init__(
        self,
        models: List[BaseModel],
        strategy: Optional[BaseStrategy] = None,
        strategy_type: str = "voting",
        strategy_config: Optional[Dict] = None
    ):
        """
        初始化翻译Agent
        
        Args:
            models: 模型列表
            strategy: 翻译策略实例（如果提供，将使用此策略）
            strategy_type: 策略类型（"voting" 或 "weighted"）
            strategy_config: 策略配置字典
        """
        self.models = models
        self.strategy = strategy or self._create_strategy(strategy_type, strategy_config or {})
    
    def _create_strategy(self, strategy_type: str, config: Dict) -> BaseStrategy:
        """创建策略实例"""
        if strategy_type == "voting":
            return VotingStrategy(**config)
        elif strategy_type == "weighted":
            return WeightedStrategy(**config)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh",
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> TranslationResponse:
        """
        执行翻译
        
        Args:
            text: 待翻译文本
            source_lang: 源语言（"auto"表示自动检测）
            target_lang: 目标语言
            context: 上下文信息（可选）
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            TranslationResponse: 翻译响应
        """
        # 创建翻译请求
        request = TranslationRequest(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 并发调用所有模型
        tasks = [model.translate(request) for model in self.models]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常响应
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # 创建错误响应
                error_response = TranslationResponse(
                    translated_text="",
                    model_name=self.models[i].model_name,
                    error=str(response)
                )
                valid_responses.append(error_response)
            else:
                valid_responses.append(response)
        
        # 使用策略合并结果
        final_response = await self.strategy.combine_translations(request, valid_responses)
        
        return final_response
    
    def add_model(self, model: BaseModel):
        """添加模型"""
        self.models.append(model)
    
    def remove_model(self, model_name: str):
        """移除模型"""
        self.models = [m for m in self.models if m.model_name != model_name]
    
    def get_model_count(self) -> int:
        """获取模型数量"""
        return len(self.models)

