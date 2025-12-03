"""
快速测试翻译能力
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 检查必要的API密钥
def check_api_keys():
    """检查API密钥是否配置"""
    required_keys = {
        "OPENAI_API_KEY": "OpenAI (用于Planner, Checker, Aggregator)",
        "OPENROUTER_API_KEY": "OpenRouter (用于Gemini和Claude)",
        "QWEN_API_KEY": "Qwen (用于Translator-B和Stylist)"
    }
    
    missing = []
    for key, desc in required_keys.items():
        if not os.getenv(key):
            missing.append(f"  - {key} ({desc})")
    
    if missing:
        print("❌ 缺少以下API密钥:")
        for item in missing:
            print(item)
        print("\n请确保 .env 文件存在并包含所有必需的API密钥")
        return False
    
    print("✓ 所有必需的API密钥已配置")
    return True


async def test_simple_translation():
    """测试简单翻译（使用简单模式）"""
    print("\n" + "=" * 60)
    print("测试1: 简单翻译模式（多模型投票）")
    print("=" * 60)
    
    from src.agents.translator import TranslatorAgent
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    
    # 创建模型
    models = []
    
    if os.getenv("OPENAI_API_KEY"):
        models.append(OpenAIModel(
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        ))
    
    if os.getenv("OPENROUTER_API_KEY"):
        models.append(GeminiModel(
            model_name="google/gemini-2.5-flash",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            use_openrouter=True
        ))
    
    if os.getenv("QWEN_API_KEY"):
        models.append(QwenModel(
            model_name="qwen-turbo",
            api_key=os.getenv("QWEN_API_KEY")
        ))
    
    if not models:
        print("❌ 没有可用的模型")
        return
    
    # 创建Agent
    agent = TranslatorAgent(
        models=models,
        strategy_type="voting",
        strategy_config={"min_models": 1}
    )
    
    # 测试翻译
    test_texts = [
        "Hello, how are you?",
        "Machine learning is a subset of artificial intelligence.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    for text in test_texts:
        print(f"\n原文: {text}")
        result = await agent.translate(text, source_lang="en", target_lang="zh")
        
        if result.error:
            print(f"❌ 错误: {result.error}")
        else:
            print(f"翻译: {result.translated_text}")
            if result.confidence:
                print(f"置信度: {result.confidence:.2%}")


async def test_pipeline_translation():
    """测试完整工作流翻译"""
    print("\n" + "=" * 60)
    print("测试2: 完整工作流翻译（多阶段协作）")
    print("=" * 60)
    
    from src.agents.pipeline import TranslationPipeline
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    
    # 检查API密钥
    if not all([os.getenv("OPENAI_API_KEY"), 
                os.getenv("OPENROUTER_API_KEY"), 
                os.getenv("QWEN_API_KEY")]):
        print("⚠️  需要所有API密钥才能运行完整工作流")
        print("   跳过此测试...")
        return
    
    # 创建模型
    planner_model = OpenAIModel(
        model_name="gpt-3.5-turbo",  # 使用gpt-3.5-turbo降低成本
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    translator_a_model = GeminiModel(
        model_name="google/gemini-2.5-flash",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    translator_b_model = QwenModel(
        model_name="qwen-turbo",
        api_key=os.getenv("QWEN_API_KEY")
    )
    
    checker_model = OpenAIModel(
        model_name="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    stylist_model = QwenModel(
        model_name="qwen-turbo",
        api_key=os.getenv("QWEN_API_KEY")
    )
    
    aggregator_model = OpenAIModel(
        model_name="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 创建工作流
    pipeline = TranslationPipeline(
        planner_model=planner_model,
        translator_a_model=translator_a_model,
        translator_b_model=translator_b_model,
        checker_model=checker_model,
        stylist_model=stylist_model,
        aggregator_model=aggregator_model,
        glossary={"AI": "人工智能", "ML": "机器学习"},
        style="general"
    )
    
    # 测试翻译
    text = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
    
    print(f"\n原文: {text}")
    print("\n开始翻译流程...")
    
    result = await pipeline.translate(
        text=text,
        source_lang="en",
        target_lang="zh"
    )
    
    print(f"\n✓ 翻译完成!")
    print(f"最终翻译: {result.translated_text}")
    
    if result.explainability_report.modifications:
        print(f"\n修改记录数: {len(result.explainability_report.modifications)}")
    
    if result.explainability_report.final_quality_score:
        score = result.explainability_report.final_quality_score
        print(f"\n质量评分:")
        print(f"  充分性: {score.adequacy:.2f}")
        print(f"  流畅性: {score.fluency:.2f}")
        print(f"  术语准确性: {score.terminology:.2f}")
        print(f"  总体: {score.overall:.2f}")


async def main():
    """主函数"""
    print("=" * 60)
    print("翻译能力快速测试")
    print("=" * 60)
    
    # 检查API密钥
    if not check_api_keys():
        print("\n请先配置API密钥:")
        print("1. 复制 .env.example 为 .env")
        print("2. 编辑 .env 文件，填入你的API密钥")
        return
    
    # 测试简单翻译
    await test_simple_translation()
    
    # 测试完整工作流（可选）
    print("\n" + "=" * 60)
    user_input = input("\n是否测试完整工作流翻译？(需要更多API调用，输入 y 继续，其他跳过): ")
    if user_input.lower() == 'y':
        await test_pipeline_translation()
    else:
        print("跳过完整工作流测试")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

