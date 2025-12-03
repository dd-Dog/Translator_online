"""
翻译Agent主入口文件
示例用法
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

from src.agents.translator import TranslatorAgent
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.utils.logger import setup_logger

# 加载环境变量
load_dotenv()

# 设置日志
logger = setup_logger(log_level="INFO", log_file="logs/translator.log")


def load_models_config() -> dict:
    """加载模型配置"""
    config_path = Path("config/models.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def create_models() -> list:
    """创建模型实例列表"""
    models = []
    config = load_models_config()
    models_config = config.get('models', {})
    
    # OpenAI模型（通过OpenRouter）
    if models_config.get('openai', {}).get('enabled', False):
        api_key = os.getenv(models_config['openai'].get('api_key_env', 'OPENROUTER_API_KEY'))
        if api_key:
            openai_config = models_config['openai']
            use_openrouter = openai_config.get('use_openrouter', True)
            model = OpenAIModel(
                model_name=openai_config['model'],
                api_key=api_key,
                base_url=openai_config.get('base_url'),
                use_openrouter=use_openrouter,
                **openai_config.get('params', {})
            )
            if model.validate_config():
                models.append(model)
                logger.info(f"已加载模型: OpenAI {model.model_name} (通过OpenRouter: {use_openrouter})")
            else:
                logger.warning("OpenAI模型配置无效")
        else:
            logger.warning("未找到OpenAI API密钥（请设置OPENROUTER_API_KEY）")
    
    # Gemini模型（通过OpenRouter）
    if models_config.get('gemini', {}).get('enabled', False):
        api_key = os.getenv(models_config['gemini'].get('api_key_env', 'OPENROUTER_API_KEY'))
        if api_key:
            gemini_config = models_config['gemini']
            use_openrouter = gemini_config.get('use_openrouter', True)
            model = GeminiModel(
                model_name=gemini_config['model'],
                api_key=api_key,
                base_url=gemini_config.get('base_url'),
                use_openrouter=use_openrouter,
                **gemini_config.get('params', {})
            )
            if model.validate_config():
                models.append(model)
                logger.info(f"已加载模型: Gemini {model.model_name} (通过OpenRouter: {use_openrouter})")
            else:
                logger.warning("Gemini模型配置无效")
        else:
            logger.warning("未找到Gemini API密钥（请设置OPENROUTER_API_KEY）")
    
    return models


async def main():
    """主函数"""
    logger.info("初始化翻译Agent...")
    
    # 创建模型
    models = create_models()
    
    if not models:
        logger.error("没有可用的模型，请检查配置和API密钥")
        return
    
    # 加载策略配置
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            app_config = yaml.safe_load(f)
        strategy_config = app_config.get('strategy', {})
        strategy_type = strategy_config.get('type', 'voting')
        strategy_params = strategy_config.get('params', {})
    else:
        strategy_type = 'voting'
        strategy_params = {}
    
    # 如果是加权策略，加载模型权重
    if strategy_type == 'weighted':
        models_config = load_models_config()
        model_weights = models_config.get('model_weights', {})
        strategy_params['model_weights'] = model_weights
    
    # 创建翻译Agent
    agent = TranslatorAgent(
        models=models,
        strategy_type=strategy_type,
        strategy_config=strategy_params
    )
    
    logger.info(f"翻译Agent初始化完成，使用{len(models)}个模型，策略类型: {strategy_type}")
    
    # 示例翻译
    test_texts = [
        "Hello, how are you?",
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence."
    ]
    
    for text in test_texts:
        logger.info(f"\n翻译文本: {text}")
        result = await agent.translate(
            text=text,
            source_lang="en",
            target_lang="zh"
        )
        
        if result.error:
            logger.error(f"翻译失败: {result.error}")
        else:
            logger.info(f"翻译结果: {result.translated_text}")
            if result.confidence:
                logger.info(f"置信度: {result.confidence:.2%}")


if __name__ == "__main__":
    asyncio.run(main())

