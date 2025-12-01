"""
测试OpenRouter配置
验证Gemini和Claude是否能正常通过OpenRouter调用
"""

import asyncio
import os
from dotenv import load_dotenv
from src.models.gemini import GeminiModel
from src.models.claude import ClaudeModel

# 加载环境变量
load_dotenv()


async def test_gemini():
    """测试Gemini通过OpenRouter"""
    print("=" * 60)
    print("测试 Gemini (通过OpenRouter)")
    print("=" * 60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到 OPENROUTER_API_KEY")
        print("   请确保 .env 文件存在并包含 OPENROUTER_API_KEY")
        return False
    
    print(f"✓ 找到API密钥: {api_key[:20]}...")
    
    try:
        model = GeminiModel(
            model_name="google/gemini-2.5-flash",  # 使用OpenRouter支持的模型ID
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            use_openrouter=True,
            http_referer="https://github.com/dd-Dog/Translator_online",
            x_title="Translator Agent Test"
        )
        
        print("✓ Gemini模型初始化成功")
        
        # 测试翻译
        from src.models.base import TranslationRequest
        
        request = TranslationRequest(
            text="Hello, how are you?",
            source_lang="en",
            target_lang="zh",
            temperature=0.3,
            max_tokens=100
        )
        
        print("\n正在调用Gemini API...")
        response = await model.translate(request)
        
        if response.error:
            print(f"❌ 错误: {response.error}")
            return False
        
        print(f"✓ 翻译成功!")
        print(f"  原文: {request.text}")
        print(f"  翻译: {response.translated_text}")
        print(f"  模型: {response.model_name}")
        if response.tokens_used:
            print(f"  Token使用: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_claude():
    """测试Claude通过OpenRouter"""
    print("\n" + "=" * 60)
    print("测试 Claude (通过OpenRouter)")
    print("=" * 60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到 OPENROUTER_API_KEY")
        return False
    
    print(f"✓ 找到API密钥: {api_key[:20]}...")
    
    try:
        model = ClaudeModel(
            model_name="anthropic/claude-3.5-haiku",  # 使用OpenRouter支持的模型ID
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            http_referer="https://github.com/dd-Dog/Translator_online",
            x_title="Translator Agent Test"
        )
        
        print("✓ Claude模型初始化成功")
        
        # 测试翻译
        from src.models.base import TranslationRequest
        
        request = TranslationRequest(
            text="The future of AI is promising.",
            source_lang="en",
            target_lang="zh",
            temperature=0.3,
            max_tokens=100
        )
        
        print("\n正在调用Claude API...")
        response = await model.translate(request)
        
        if response.error:
            print(f"❌ 错误: {response.error}")
            return False
        
        print(f"✓ 翻译成功!")
        print(f"  原文: {request.text}")
        print(f"  翻译: {response.translated_text}")
        print(f"  模型: {response.model_name}")
        if response.tokens_used:
            print(f"  Token使用: {response.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("OpenRouter 配置测试")
    print("=" * 60)
    print()
    
    # 检查环境变量
    print("检查环境变量...")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print(f"✓ OPENROUTER_API_KEY: {openrouter_key[:20]}...")
    else:
        print("❌ OPENROUTER_API_KEY 未设置")
        print("   请确保 .env 文件存在并包含 OPENROUTER_API_KEY")
        print("   可以运行: copy .env.example .env")
        return
    
    print()
    
    # 测试Gemini
    gemini_ok = await test_gemini()
    
    # 测试Claude
    claude_ok = await test_claude()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"Gemini: {'✓ 通过' if gemini_ok else '❌ 失败'}")
    print(f"Claude: {'✓ 通过' if claude_ok else '❌ 失败'}")
    
    if gemini_ok and claude_ok:
        print("\n🎉 所有测试通过！OpenRouter配置正确。")
    elif gemini_ok or claude_ok:
        print("\n⚠️  部分测试通过，请检查失败的模型配置。")
    else:
        print("\n❌ 测试失败，请检查:")
        print("   1. .env 文件是否存在并包含正确的 OPENROUTER_API_KEY")
        print("   2. API密钥是否有效")
        print("   3. 网络连接是否正常")


if __name__ == "__main__":
    asyncio.run(main())

