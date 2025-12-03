"""
快速开始 - 仅使用OpenRouter测试翻译
只需要配置 OPENROUTER_API_KEY
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def quick_test():
    """快速测试 - 只使用OpenRouter的Gemini"""
    print("=" * 60)
    print("快速翻译测试（使用OpenRouter Gemini）")
    print("=" * 60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key or api_key.startswith("your_"):
        print("❌ 请先配置有效的 OPENROUTER_API_KEY")
        print("   编辑 .env 文件，将 OPENROUTER_API_KEY 替换为你的真实密钥")
        print("   获取地址: https://openrouter.ai/keys")
        return
    
    from src.models.gemini import GeminiModel
    from src.models.base import TranslationRequest
    
    print(f"✓ 使用 OpenRouter API密钥: {api_key[:20]}...")
    
    try:
        # 创建Gemini模型
        model = GeminiModel(
            model_name="google/gemini-2.5-flash",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            use_openrouter=True,
            http_referer="https://github.com/dd-Dog/Translator_online",
            x_title="Translator Test"
        )
        
        # 测试文本
        test_texts = [
            "Hello, how are you?",
            "Machine learning is a subset of artificial intelligence.",
            "The future of AI is promising."
        ]
        
        for text in test_texts:
            print(f"\n{'='*60}")
            print(f"原文: {text}")
            print("正在翻译...")
            
            request = TranslationRequest(
                text=text,
                source_lang="en",
                target_lang="zh"
            )
            
            result = await model.translate(request)
            
            if result.error:
                print(f"❌ 错误: {result.error}")
                if "401" in result.error or "User not found" in result.error:
                    print("\n提示: OpenRouter API密钥可能无效或账户未激活")
                    print("请检查:")
                    print("  1. API密钥是否正确")
                    print("  2. 是否在 https://openrouter.ai/ 注册并激活账户")
                    print("  3. 账户是否有余额")
                break
            else:
                print(f"✓ 翻译: {result.translated_text}")
                if result.tokens_used:
                    print(f"  Token使用: {result.tokens_used}")
        
        print(f"\n{'='*60}")
        print("测试完成！")
        
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(quick_test())

