"""
调试Checker评分输出
查看GPT-4实际返回的内容
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_checker_output():
    """测试Checker的实际输出"""
    print("=" * 70)
    print("调试Checker评分输出")
    print("=" * 70)
    
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    from src.agents.checker import Checker
    from src.agents.workflow import TranslationDraft
    
    # 创建Checker模型
    checker_model = OpenAIModel(
        model_name="gpt-4",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        use_openrouter=True
    )
    
    checker = Checker(checker_model)
    
    # 创建测试数据
    source_text = "Machine learning is a subset of artificial intelligence."
    
    draft_a = TranslationDraft(
        translated_text="机器学习是人工智能的一个子集。",
        model_name="gemini-2.5-flash",
        segment_id="seg_1"
    )
    
    draft_b = TranslationDraft(
        translated_text="机器学习是人工智能的一个子领域。",
        model_name="qwen-turbo",
        segment_id="seg_1"
    )
    
    print(f"\n测试数据:")
    print(f"  原文: {source_text}")
    print(f"  翻译A: {draft_a.translated_text}")
    print(f"  翻译B: {draft_b.translated_text}")
    
    print(f"\n正在调用Checker...")
    
    # 调用Checker
    report = await checker.check(source_text, draft_a, draft_b, "seg_1")
    
    # 显示结果
    print(f"\n最终CheckerReport:")
    print(f"  一致的段落: {report.consistent_segments}")
    print(f"  冲突的段落: {len(report.conflicting_segments)}")
    print(f"  遗漏: {len(report.omissions)}")
    print(f"  误解: {len(report.misinterpretations)}")
    
    if "seg_1" in report.quality_scores:
        score = report.quality_scores["seg_1"]
        print(f"\n质量评分:")
        print(f"  充分性: {score.adequacy}")
        print(f"  流畅性: {score.fluency}")
        print(f"  术语准确性: {score.terminology}")
        print(f"  总体: {score.overall}")
    else:
        print(f"\n⚠️  未找到质量评分")


if __name__ == "__main__":
    asyncio.run(test_checker_output())

