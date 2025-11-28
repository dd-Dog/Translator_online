"""
工作流Pipeline使用示例
展示多阶段、多模型协作的翻译流程
"""

import asyncio
import os
from dotenv import load_dotenv
from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel

# 加载环境变量
load_dotenv()


async def example_pipeline_translation():
    """工作流翻译示例"""
    print("=" * 60)
    print("多阶段翻译工作流示例")
    print("=" * 60)
    
    # 创建各个模型
    planner_model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    translator_a_model = GeminiModel(
        model_name="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    translator_b_model = QwenModel(
        model_name="qwen-turbo",
        api_key=os.getenv("QWEN_API_KEY")
    )
    
    checker_model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    stylist_model = QwenModel(
        model_name="qwen-turbo",
        api_key=os.getenv("QWEN_API_KEY")
    )
    
    aggregator_model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 创建术语表（可选）
    glossary = {
        "machine learning": "机器学习",
        "artificial intelligence": "人工智能",
        "neural network": "神经网络"
    }
    
    # 创建工作流
    pipeline = TranslationPipeline(
        planner_model=planner_model,
        translator_a_model=translator_a_model,
        translator_b_model=translator_b_model,
        checker_model=checker_model,
        stylist_model=stylist_model,
        aggregator_model=aggregator_model,
        glossary=glossary,
        style="academic"  # 学术论文风格
    )
    
    # 执行翻译
    text = """
    Machine learning is a subset of artificial intelligence that enables 
    systems to learn and improve from experience without being explicitly 
    programmed. Neural networks are computational models inspired by the 
    structure and function of biological neural networks.
    """
    
    print(f"\n原文：\n{text}\n")
    print("开始翻译流程...\n")
    
    result = await pipeline.translate(
        text=text,
        source_lang="en",
        target_lang="zh"
    )
    
    print("=" * 60)
    print("最终翻译结果：")
    print("=" * 60)
    print(result.translated_text)
    
    print("\n" + "=" * 60)
    print("处理阶段：")
    print("=" * 60)
    for i, stage in enumerate(result.processing_stages, 1):
        print(f"{i}. {stage}")
    
    print("\n" + "=" * 60)
    print("可解释性报告：")
    print("=" * 60)
    
    if result.explainability_report.modifications:
        print("\n修改记录：")
        for mod in result.explainability_report.modifications[:5]:  # 只显示前5个
            print(f"  - [{mod['stage']}] {mod['original']} -> {mod['modified']}")
            print(f"    原因: {mod['reason']}")
    
    if result.explainability_report.quality_improvements:
        print("\n质量改进：")
        for metric, improvement in result.explainability_report.quality_improvements.items():
            print(f"  - {metric}: {improvement['before']:.2f} -> {improvement['after']:.2f} "
                  f"(改进: {improvement['improvement']:.2f})")
    
    if result.explainability_report.final_quality_score:
        score = result.explainability_report.final_quality_score
        print("\n最终质量评分：")
        print(f"  - 充分性: {score.adequacy:.2f}")
        print(f"  - 流畅性: {score.fluency:.2f}")
        print(f"  - 术语准确性: {score.terminology:.2f}")
        print(f"  - 总体: {score.overall:.2f}")


async def example_different_styles():
    """不同风格翻译示例"""
    print("\n" + "=" * 60)
    print("不同风格翻译示例")
    print("=" * 60)
    
    # 创建模型（简化，复用同一个模型）
    openai_model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    gemini_model = GeminiModel(
        model_name="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    qwen_model = QwenModel(
        model_name="qwen-turbo",
        api_key=os.getenv("QWEN_API_KEY")
    )
    
    text = "The meeting will be held tomorrow at 3 PM."
    
    styles = ["general", "academic", "official", "colloquial"]
    
    for style in styles:
        pipeline = TranslationPipeline(
            planner_model=openai_model,
            translator_a_model=gemini_model,
            translator_b_model=qwen_model,
            checker_model=openai_model,
            stylist_model=qwen_model,
            aggregator_model=openai_model,
            style=style
        )
        
        result = await pipeline.translate(text, source_lang="en", target_lang="zh")
        
        print(f"\n{style.upper()}风格：")
        print(f"  {result.translated_text}")


async def main():
    """运行所有示例"""
    if not all([
        os.getenv("OPENAI_API_KEY"),
        os.getenv("GEMINI_API_KEY"),
        os.getenv("QWEN_API_KEY")
    ]):
        print("错误: 请配置所有必需的API密钥（OPENAI_API_KEY, GEMINI_API_KEY, QWEN_API_KEY）")
        return
    
    await example_pipeline_translation()
    # await example_different_styles()  # 可选运行


if __name__ == "__main__":
    asyncio.run(main())

