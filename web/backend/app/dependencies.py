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
from src.models.doubao import DoubaoModel
from src.agents.pipeline import TranslationPipeline
from app.config import app_config, security_config


def load_models_config() -> dict:
    """加载模型配置"""
    if app_config.MODELS_CONFIG.exists():
        with open(app_config.MODELS_CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def create_model(model_config: dict, model_type: str, api_key: Optional[str] = None) -> Optional[object]:
    """
    创建模型实例
    
    Args:
        model_config: 模型配置字典
        model_type: 模型类型（openai, gemini, qwen, deepseek, doubao等）
        api_key: API密钥（如果提供，将使用此密钥而不是环境变量）
                 如果传入空字符串，表示强制使用空key（会失败），不会回退到环境变量
    """
    if not model_config.get('enabled', False):
        return None
    
    # 如果提供了api_key（包括空字符串），直接使用；否则从环境变量读取
    # 注意：如果api_key是空字符串，表示用户明确传入了空值，不应该回退到环境变量
    api_key_source = "用户传入"  # 记录API_KEY来源，用于调试
    if api_key is None:
        # 没有提供api_key，从环境变量读取
        api_key_env = model_config.get('api_key_env', '')
        api_key = os.getenv(api_key_env)
        api_key_source = f"环境变量({api_key_env})"
    # 如果api_key不是None（包括空字符串），直接使用，不读取环境变量
    # 这样确保用户传入的配置（即使是错误的）会被使用
    
    if not api_key:
        print(f"[模型创建] {model_type}: API_KEY为空，无法创建模型")
        return None
    
    # 打印API_KEY来源信息（用于调试）
    api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
    print(f"[模型创建] {model_type}: API_KEY来源={api_key_source}, api_key={api_key_preview}")
    
    model_name = model_config.get('model', '')
    base_url = model_config.get('base_url', '')
    use_openrouter = model_config.get('use_openrouter', False)
    params = model_config.get('params', {})
    
    try:
        model_instance = None
        if model_type == 'openai':
            model_instance = OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'gemini':
            model_instance = GeminiModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'qwen':
            model_instance = QwenModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
        elif model_type == 'deepseek':
            model_instance = DeepSeekModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
        elif model_type == 'doubao':
            model_instance = DoubaoModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **params
            )
        
        # 打印模型创建信息（用于调试）
        if model_instance:
            api_key_preview = api_key[:8] + '...' if len(api_key) > 8 else api_key
            actual_base_url = getattr(model_instance, 'base_url', base_url or '默认')
            print(f"[模型创建] 类型: {model_type}, 模型名: {model_name}, base_url: {actual_base_url}, api_key: {api_key_preview}")
        
        return model_instance
    except Exception as e:
        print(f"创建模型失败 {model_type}: {e}")
        return None


def get_pipeline(model_configs: Optional[dict] = None) -> Optional[TranslationPipeline]:
    """
    获取翻译Pipeline实例
    
    Args:
        model_configs: 可选的模型配置字典，格式为:
            {
                'planner': {'model_type': 'deepseek', 'api_key': 'xxx'},
                'translator_a': {'model_type': 'deepseek', 'api_key': 'xxx'},
                ...
            }
            如果提供，将使用这些配置而不是从yaml文件读取
    """
    config = load_models_config()
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    # 如果提供了model_configs，使用提供的配置；否则从yaml读取
    if model_configs and len(model_configs) > 0:
        planner_model_type = model_configs.get('planner', {}).get('model_type', 'deepseek')
        translator_a_model_type = model_configs.get('translator_a', {}).get('model_type', 'deepseek')
        translator_b_model_type = model_configs.get('translator_b', {}).get('model_type', 'qwen')
        checker_model_type = model_configs.get('checker', {}).get('model_type', 'deepseek')
        stylist_model_type = model_configs.get('stylist', {}).get('model_type', 'qwen')
        aggregator_model_type = model_configs.get('aggregator', {}).get('model_type', 'deepseek')
        
        planner_api_key = model_configs.get('planner', {}).get('api_key')
        translator_a_api_key = model_configs.get('translator_a', {}).get('api_key')
        translator_b_api_key = model_configs.get('translator_b', {}).get('api_key')
        checker_api_key = model_configs.get('checker', {}).get('api_key')
        stylist_api_key = model_configs.get('stylist', {}).get('api_key')
        aggregator_api_key = model_configs.get('aggregator', {}).get('api_key')
    else:
        # 从yaml配置读取
        # workflow_config中的值可能是字符串（如 'deepseek'）或字典（如 {'model': 'deepseek'}）
        planner_config = workflow_config.get('planner', 'deepseek')
        planner_model_type = planner_config if isinstance(planner_config, str) else planner_config.get('model', 'deepseek')
        
        translator_a_config = workflow_config.get('translator_a', 'deepseek')
        translator_a_model_type = translator_a_config if isinstance(translator_a_config, str) else translator_a_config.get('model', 'deepseek')
        
        translator_b_config = workflow_config.get('translator_b', 'qwen')
        translator_b_model_type = translator_b_config if isinstance(translator_b_config, str) else translator_b_config.get('model', 'qwen')
        
        checker_config = workflow_config.get('checker', 'deepseek')
        checker_model_type = checker_config if isinstance(checker_config, str) else checker_config.get('model', 'deepseek')
        
        stylist_config = workflow_config.get('stylist', 'qwen')
        stylist_model_type = stylist_config if isinstance(stylist_config, str) else stylist_config.get('model', 'qwen')
        
        aggregator_config = workflow_config.get('aggregator', 'deepseek')
        aggregator_model_type = aggregator_config if isinstance(aggregator_config, str) else aggregator_config.get('model', 'deepseek')
        
        planner_api_key = None
        translator_a_api_key = None
        translator_b_api_key = None
        checker_api_key = None
        stylist_api_key = None
        aggregator_api_key = None
    
    # 创建模型实例
    # 如果提供了model_configs，必须使用提供的api_key（即使是错误的），不能回退到环境变量
    planner_model = create_model(models_config.get(planner_model_type, {}), planner_model_type, planner_api_key)
    translator_a_model = create_model(models_config.get(translator_a_model_type, {}), translator_a_model_type, translator_a_api_key)
    translator_b_model = create_model(models_config.get(translator_b_model_type, {}), translator_b_model_type, translator_b_api_key)
    checker_model = create_model(models_config.get(checker_model_type, {}), checker_model_type, checker_api_key)
    stylist_model = create_model(models_config.get(stylist_model_type, {}), stylist_model_type, stylist_api_key)
    aggregator_model = create_model(models_config.get(aggregator_model_type, {}), aggregator_model_type, aggregator_api_key)
    
    # 如果提供了model_configs但模型创建失败，说明API_KEY有问题
    if model_configs and len(model_configs) > 0:
        failed_stages = []
        if not planner_model:
            failed_stages.append(f"planner (model_type: {planner_model_type}, api_key: {planner_api_key[:8] if planner_api_key and len(planner_api_key) > 8 else 'N/A'}...)")
        if not translator_a_model:
            failed_stages.append(f"translator_a (model_type: {translator_a_model_type}, api_key: {translator_a_api_key[:8] if translator_a_api_key and len(translator_a_api_key) > 8 else 'N/A'}...)")
        if not translator_b_model:
            failed_stages.append(f"translator_b (model_type: {translator_b_model_type}, api_key: {translator_b_api_key[:8] if translator_b_api_key and len(translator_b_api_key) > 8 else 'N/A'}...)")
        if not checker_model:
            failed_stages.append(f"checker (model_type: {checker_model_type}, api_key: {checker_api_key[:8] if checker_api_key and len(checker_api_key) > 8 else 'N/A'}...)")
        if not stylist_model:
            failed_stages.append(f"stylist (model_type: {stylist_model_type}, api_key: {stylist_api_key[:8] if stylist_api_key and len(stylist_api_key) > 8 else 'N/A'}...)")
        if not aggregator_model:
            failed_stages.append(f"aggregator (model_type: {aggregator_model_type}, api_key: {aggregator_api_key[:8] if aggregator_api_key and len(aggregator_api_key) > 8 else 'N/A'}...)")
        
        if failed_stages:
            error_msg = f"使用前端配置创建模型失败，以下阶段的API_KEY可能无效或模型未启用: {', '.join(failed_stages)}"
            print(f"[错误] {error_msg}")
            raise RuntimeError(error_msg)
    
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


def get_or_create_pipeline(model_configs: Optional[dict] = None) -> TranslationPipeline:
    """
    获取或创建Pipeline实例
    
    Args:
        model_configs: 可选的模型配置字典，如果提供，将创建新的Pipeline实例
                      如果不提供，将使用缓存的单例实例
    
    Returns:
        TranslationPipeline: 翻译Pipeline实例
    """
    global _pipeline
    
    # 如果提供了model_configs，创建新的Pipeline实例（不使用缓存）
    if model_configs:
        pipeline = get_pipeline(model_configs)
        if pipeline is None:
            raise RuntimeError("无法创建翻译Pipeline，请检查模型配置")
        return pipeline
    
    # 否则使用单例模式
    if _pipeline is None:
        _pipeline = get_pipeline()
        if _pipeline is None:
            raise RuntimeError("无法创建翻译Pipeline，请检查模型配置")
    return _pipeline

