"""
测试带详细日志的Pipeline
"""

import asyncio
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_config():
    """加载配置"""
    config_path = Path("config/models.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_model(model_config: dict, model_type: str):
    """创建模型"""
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    
    api_key = os.getenv(model_config.get('api_key_env'))
    if not api_key:
        return None
    
    model_name = model_config.get('model')
    params = model_config.get('params', {})
    base_url = model_config.get('base_url')
    use_openrouter = model_config.get('use_openrouter', False)
    
    if model_type == 'openai':
        return OpenAIModel(model_name, api_key, base_url, use_openrouter, **params)
    elif model_type == 'gemini':
        return GeminiModel(model_name, api_key, base_url, use_openrouter, **params)
    elif model_type == 'qwen':
        return QwenModel(model_name, api_key, base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1", **params)


async def test_verbose():
    """测试详细日志模式"""
    print("\n" + "=" * 70)
    print("🔍 详细日志模式测试")
    print("=" * 70)
    
    # 加载配置
    config = load_config()
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    style_config = config.get('style', {})
    
    # 创建模型
    planner = create_model(
        models_config.get(workflow_config.get('planner', {}).get('model', 'openai'), {}),
        workflow_config.get('planner', {}).get('model', 'openai')
    )
    translator_a = create_model(
        models_config.get(workflow_config.get('translator_a', {}).get('model', 'gemini'), {}),
        workflow_config.get('translator_a', {}).get('model', 'gemini')
    )
    translator_b = create_model(
        models_config.get(workflow_config.get('translator_b', {}).get('model', 'qwen'), {}),
        workflow_config.get('translator_b', {}).get('model', 'qwen')
    )
    checker = create_model(
        models_config.get(workflow_config.get('checker', {}).get('model', 'openai'), {}),
        workflow_config.get('checker', {}).get('model', 'openai')
    )
    stylist = create_model(
        models_config.get(workflow_config.get('stylist', {}).get('model', 'qwen'), {}),
        workflow_config.get('stylist', {}).get('model', 'qwen')
    )
    aggregator = create_model(
        models_config.get(workflow_config.get('aggregator', {}).get('model', 'openai'), {}),
        workflow_config.get('aggregator', {}).get('model', 'openai')
    )
    
    # 创建详细日志Pipeline
    from src.agents.pipeline_verbose import VerboseTranslationPipeline
    
    pipeline = VerboseTranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        glossary={"AI": "人工智能", "ML": "机器学习"},
        style="general",
        verbose=True  # 启用详细日志
    )
    
    # 测试翻译
    text = "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
    
    result = await pipeline.translate(
        text=text,
        source_lang="en",
        target_lang="zh"
    )
    
    print(f"\n{'='*70}")
    print("✅ 测试完成")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_verbose())

