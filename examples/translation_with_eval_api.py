"""
翻译与评估API集成示例
演示如何使用翻译系统并通过API调用评估服务
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
from src.utils.evaluation_service import create_evaluation_service

load_dotenv()


async def main():
    """主函数"""
    print("=" * 80)
    print("翻译与评估API集成示例")
    print("=" * 80)
    
    # 1. 创建翻译Pipeline
    print("\n[1/4] 初始化翻译Pipeline...")
    
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    models_config = config.get('models', {})
    
    def create_model(model_type):
        model_cfg = models_config.get(model_type, {})
        api_key_env = model_cfg.get('api_key_env')
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not api_key:
            print(f"⚠️  未找到 {model_type} API密钥")
            return None
        
        model_name = model_cfg.get('model')
        params = model_cfg.get('params', {})
        base_url = model_cfg.get('base_url')
        use_openrouter = model_cfg.get('use_openrouter', False)
        
        if model_type == 'openai':
            return OpenAIModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'gemini':
            return GeminiModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'qwen':
            return QwenModel(model_name, api_key, base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1", **params)
        return None
    
    planner = create_model('openai')
    translator_a = create_model('gemini')
    translator_b = create_model('qwen')
    checker = create_model('openai')
    stylist = create_model('qwen')
    aggregator = create_model('openai')
    
    if not all([planner, translator_a, translator_b, checker, stylist, aggregator]):
        print("❌ 部分模型创建失败，请检查配置")
        return
    
    pipeline = TranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        glossary={},
        style='general'
    )
    print("✅ 翻译Pipeline初始化完成")
    
    # 2. 创建评估服务（API模式）
    print("\n[2/4] 初始化评估服务（API模式）...")
    eval_service = create_evaluation_service(use_api=True)
    
    if eval_service is None:
        print("❌ 评估服务初始化失败")
        return
    
    if not eval_service.is_available():
        print("⚠️  评估API服务不可用，请确保服务已启动")
        print("   启动命令: python eval_server.py")
        print("   或参考: docs/API服务使用指南.md")
        return
    
    print("✅ 评估服务已就绪")
    
    # 3. 执行翻译
    print("\n[3/4] 执行翻译...")
    test_text = "Machine learning is a subset of artificial intelligence."
    reference = "机器学习是人工智能的一个子集。"
    
    print(f"原文: {test_text}")
    print(f"参考翻译: {reference}")
    
    result = await pipeline.translate(
        text=test_text,
        source_lang="en",
        target_lang="zh"
    )
    
    print(f"翻译结果: {result.translated_text}")
    
    # 4. 评估翻译质量
    print("\n[4/4] 评估翻译质量...")
    
    # 提取MQM评分（如果可用）
    mqm_score = None
    if result.explainability_report and result.explainability_report.final_quality_score:
        qs = result.explainability_report.final_quality_score
        mqm_score = {
            "adequacy": qs.adequacy,
            "fluency": qs.fluency,
            "terminology": qs.terminology,
            "overall": qs.overall
        }
    
    eval_result = eval_service.evaluate(
        translation=result.translated_text,
        reference=reference,
        source=test_text,
        mqm_score=mqm_score
    )
    
    if eval_result:
        print("\n评估结果:")
        print(f"  BLEU: {eval_result['bleu']:.4f}")
        print(f"  COMET: {eval_result['comet']:.4f}")
        print(f"  BERTScore: {eval_result['bertscore_f1']:.4f}")
        print(f"  ChrF: {eval_result['chrf']:.4f}")
        if mqm_score:
            print(f"  MQM: {eval_result['mqm_overall']:.4f}")
        print(f"  综合评分: {eval_result['final_score']:.4f}")
    else:
        print("❌ 评估失败")
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

