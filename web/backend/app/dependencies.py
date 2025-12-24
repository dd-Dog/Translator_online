"""
依赖注入
"""
import os
import yaml
from pathlib import Path
from typing import Optional
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
from src.models.deepseek import DeepSeekModel
from src.agents.pipeline import TranslationPipeline
from app.config import app_config, security_config


def load_models_config() -> dict:
    """加载模型配置"""
    if app_config.MODELS_CONFIG.exists():
        with open(app_config.MODELS_CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def create_model(model_config: dict, model_type: str) -> Optional[object]:
    """创建模型实例"""
    if not model_config.get('enabled', False):
        return None
    
    api_key_env = model_config.get('api_key_env', '')
    api_key = os.getenv(api_key_env)
    
    if not api_key:
        return None
    
    model_name = model_config.get('model', '')
    base_url = model_config.get('base_url', '')
    use_openrouter = model_config.get('use_openrouter', False)
    params = model_config.get('params', {})
    
    try:
        if model_type == 'openai':
            return OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'gemini':
            return GeminiModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'qwen':
            return QwenModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
        elif model_type == 'deepseek':
            return DeepSeekModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
    except Exception as e:
        print(f"创建模型失败 {model_type}: {e}")
        return None


def get_pipeline() -> Optional[TranslationPipeline]:
    """获取翻译Pipeline实例"""
    config = load_models_config()
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    # 获取工作流配置
    planner_model_type = workflow_config.get('planner', {}).get('model', 'deepseek')
    translator_a_model_type = workflow_config.get('translator_a', {}).get('model', 'deepseek')
    translator_b_model_type = workflow_config.get('translator_b', {}).get('model', 'qwen')
    checker_model_type = workflow_config.get('checker', {}).get('model', 'deepseek')
    stylist_model_type = workflow_config.get('stylist', {}).get('model', 'qwen')
    aggregator_model_type = workflow_config.get('aggregator', {}).get('model', 'deepseek')
    
    # 创建模型实例
    planner_model = create_model(models_config.get(planner_model_type, {}), planner_model_type)
    translator_a_model = create_model(models_config.get(translator_a_model_type, {}), translator_a_model_type)
    translator_b_model = create_model(models_config.get(translator_b_model_type, {}), translator_b_model_type)
    checker_model = create_model(models_config.get(checker_model_type, {}), checker_model_type)
    stylist_model = create_model(models_config.get(stylist_model_type, {}), stylist_model_type)
    aggregator_model = create_model(models_config.get(aggregator_model_type, {}), aggregator_model_type)
    
    if not all([planner_model, translator_a_model, translator_b_model, 
                checker_model, stylist_model, aggregator_model]):
        return None
    
    return TranslationPipeline(
        planner_model=planner_model,
        translator_a_model=translator_a_model,
        translator_b_model=translator_b_model,
        checker_model=checker_model,
        stylist_model=stylist_model,
        aggregator_model=aggregator_model,
        style="general",
        verbose=False
    )


# 全局Pipeline实例（懒加载）
_pipeline: Optional[TranslationPipeline] = None


def get_or_create_pipeline() -> TranslationPipeline:
    """获取或创建Pipeline实例（单例模式）"""
    global _pipeline
    if _pipeline is None:
        _pipeline = get_pipeline()
        if _pipeline is None:
            raise RuntimeError("无法创建翻译Pipeline，请检查模型配置")
    return _pipeline

