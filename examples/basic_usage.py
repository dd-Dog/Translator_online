"""
基础使用示例
"""

import asyncio
import os
from dotenv import load_dotenv
from src.agents.translator import TranslatorAgent
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel

# 加载环境变量
load_dotenv()


async def example_single_model():
    """单模型翻译示例"""
    print("=" * 50)
    print("示例1: 单模型翻译")
    print("=" * 50)
    
    # 使用OpenAI模型
    openai_model = OpenAIModel(
        model_name="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    agent = TranslatorAgent(models=[openai_model])
    
    text = "Hello, world!"
    result = await agent.translate(text, source_lang="en", target_lang="zh")
    
    print(f"原文: {text}")
    print(f"翻译: {result.translated_text}")
    print(f"模型: {result.model_name}")


async def example_multi_model_voting():
    """多模型投票策略示例"""
    print("\n" + "=" * 50)
    print("示例2: 多模型投票策略")
    print("=" * 50)
    
    # 创建多个模型
    models = []
    
    if os.getenv("OPENAI_API_KEY"):
        models.append(OpenAIModel(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        ))
    
    if os.getenv("GEMINI_API_KEY"):
        models.append(GeminiModel(
            model_name="gemini-pro",
            api_key=os.getenv("GEMINI_API_KEY")
        ))
    
    if not models:
        print("错误: 请配置至少一个API密钥")
        return
    
    # 使用投票策略
    agent = TranslatorAgent(
        models=models,
        strategy_type="voting",
        strategy_config={"min_models": 1}
    )
    
    text = "The future of artificial intelligence is promising."
    result = await agent.translate(text, source_lang="en", target_lang="zh")
    
    print(f"原文: {text}")
    print(f"翻译: {result.translated_text}")
    print(f"置信度: {result.confidence:.2%}" if result.confidence else "")
    print(f"使用模型数: {len(models)}")


async def example_weighted_strategy():
    """加权策略示例"""
    print("\n" + "=" * 50)
    print("示例3: 加权策略")
    print("=" * 50)
    
    models = []
    model_weights = {}
    
    if os.getenv("OPENAI_API_KEY"):
        openai_model = OpenAIModel(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        models.append(openai_model)
        model_weights["gpt-3.5-turbo"] = 0.6
    
    if os.getenv("GEMINI_API_KEY"):
        gemini_model = GeminiModel(
            model_name="gemini-pro",
            api_key=os.getenv("GEMINI_API_KEY")
        )
        models.append(gemini_model)
        model_weights["gemini-pro"] = 0.4
    
    if not models:
        print("错误: 请配置至少一个API密钥")
        return
    
    # 使用加权策略
    agent = TranslatorAgent(
        models=models,
        strategy_type="weighted",
        strategy_config={"model_weights": model_weights}
    )
    
    text = "Machine learning algorithms can learn from data."
    result = await agent.translate(text, source_lang="en", target_lang="zh")
    
    print(f"原文: {text}")
    print(f"翻译: {result.translated_text}")
    print(f"置信度: {result.confidence:.2%}" if result.confidence else "")


async def example_batch_translation():
    """批量翻译示例"""
    print("\n" + "=" * 50)
    print("示例4: 批量翻译")
    print("=" * 50)
    
    models = []
    if os.getenv("OPENAI_API_KEY"):
        models.append(OpenAIModel(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        ))
    if os.getenv("GEMINI_API_KEY"):
        models.append(GeminiModel(
            model_name="gemini-pro",
            api_key=os.getenv("GEMINI_API_KEY")
        ))
    
    if not models:
        print("错误: 请配置至少一个API密钥")
        return
    
    agent = TranslatorAgent(models=models, strategy_type="voting")
    
    texts = [
        "Good morning!",
        "How are you?",
        "Thank you very much.",
        "See you later!"
    ]
    
    print("批量翻译结果:")
    for text in texts:
        result = await agent.translate(text, source_lang="en", target_lang="zh")
        print(f"  {text} -> {result.translated_text}")


async def main():
    """运行所有示例"""
    await example_single_model()
    await example_multi_model_voting()
    await example_weighted_strategy()
    await example_batch_translation()


if __name__ == "__main__":
    asyncio.run(main())

