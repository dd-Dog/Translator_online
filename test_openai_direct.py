"""
直接测试OpenAI模型调用
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    from src.models.openai import OpenAIModel
    from src.models.base import TranslationRequest
    
    model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    # 测试1: 简单翻译
    print("测试1: 简单翻译")
    request1 = TranslationRequest(
        text="Hello, how are you?",
        source_lang="en",
        target_lang="zh",
        temperature=0.3
    )
    
    result1 = await model.translate(request1)
    print(f"结果: {result1.translated_text}")
    print(f"错误: {result1.error}")
    
    # 测试2: JSON请求
    print("\n测试2: JSON请求")
    json_prompt = """Please evaluate the translation quality and return ONLY JSON format:

{
    "quality_scores": {
        "adequacy": 0.9,
        "fluency": 0.85
    }
}

Do not include any other text."""
    
    request2 = TranslationRequest(
        text=json_prompt,
        source_lang="en",
        target_lang="en",
        temperature=0.2
    )
    
    result2 = await model.translate(request2)
    print(f"结果: {result2.translated_text}")
    print(f"错误: {result2.error}")

asyncio.run(test())

