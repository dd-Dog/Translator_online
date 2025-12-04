"""
测试不同翻译风格
"""

import asyncio
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_config():
    """加载配置"""
    with open("config/models.yaml", 'r', encoding='utf-8') as f:
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


async def test_styles():
    """测试不同风格"""
    print("\n" + "=" * 70)
    print("🎨 测试不同翻译风格")
    print("=" * 70)
    
    # 加载风格配置
    styles_config_path = Path("config/styles.yaml")
    if not styles_config_path.exists():
        print("❌ styles.yaml 配置文件不存在")
        return
    
    with open(styles_config_path, 'r', encoding='utf-8') as f:
        styles_config = yaml.safe_load(f)
    
    available_styles = styles_config.get('styles', {})
    print(f"\n✓ 加载了 {len(available_styles)} 种风格配置:")
    for style_key, style_info in available_styles.items():
        print(f"  - {style_key}: {style_info.get('name', style_key)}")
    
    # 创建模型
    config = load_config()
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    print("\n🔧 创建模型...")
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
    
    if not all([planner, translator_a, translator_b, checker, stylist, aggregator]):
        print("❌ 部分模型创建失败")
        return
    
    print("✓ 所有模型创建成功")
    
    # 测试文本
    test_texts = {
        "technology": "Machine learning is a subset of artificial intelligence.",
        "business": "The company will announce its quarterly earnings tomorrow.",
        "academic": "This study examines the impact of neural networks on image recognition.",
        "colloquial": "Hey, what's up? How are you doing today?"
    }
    
    # 风格列表
    styles_to_test = ["general", "native", "business", "academic", "technical", "colloquial"]
    
    # 选择测试文本
    print(f"\n请选择测试文本:")
    print(f"  1. Technology: {test_texts['technology']}")
    print(f"  2. Business: {test_texts['business']}")
    print(f"  3. Academic: {test_texts['academic']}")
    print(f"  4. Colloquial: {test_texts['colloquial']}")
    print(f"  5. 自定义输入")
    
    choice = input("\n请选择 (1-5, 默认1): ").strip() or "1"
    
    if choice == "1":
        text = test_texts["technology"]
    elif choice == "2":
        text = test_texts["business"]
    elif choice == "3":
        text = test_texts["academic"]
    elif choice == "4":
        text = test_texts["colloquial"]
    elif choice == "5":
        text = input("请输入文本: ").strip()
    else:
        text = test_texts["technology"]
    
    print(f"\n测试文本: {text}")
    
    # 测试不同风格
    from src.agents.pipeline import TranslationPipeline
    
    results = {}
    
    for style in styles_to_test:
        if style not in available_styles:
            continue
        
        print(f"\n{'='*70}")
        print(f"🎨 测试风格: {available_styles[style].get('name', style)}")
        print(f"{'='*70}")
        print(f"说明: {available_styles[style].get('description', '')}")
        
        pipeline = TranslationPipeline(
            planner_model=planner,
            translator_a_model=translator_a,
            translator_b_model=translator_b,
            checker_model=checker,
            stylist_model=stylist,
            aggregator_model=aggregator,
            glossary={},
            style=style,
            verbose=False
        )
        
        try:
            result = await pipeline.translate(
                text=text,
                source_lang="en",
                target_lang="zh"
            )
            
            results[style] = result.translated_text
            
            print(f"✅ 翻译结果: {result.translated_text}")
            if result.explainability_report.final_quality_score:
                score = result.explainability_report.final_quality_score
                print(f"   质量评分: {score.overall:.2f}")
            
        except Exception as e:
            print(f"❌ 翻译失败: {e}")
            results[style] = None
    
    # 对比不同风格
    print(f"\n{'='*70}")
    print("📊 不同风格对比")
    print(f"{'='*70}")
    print(f"\n原文: {text}\n")
    
    for style, translation in results.items():
        if translation:
            style_name = available_styles[style].get('name', style)
            print(f"【{style_name}】")
            print(f"  {translation}\n")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"style_comparison_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"原文: {text}\n\n")
        f.write("=" * 70 + "\n")
        f.write("不同风格翻译对比\n")
        f.write("=" * 70 + "\n\n")
        
        for style, translation in results.items():
            if translation:
                style_name = available_styles[style].get('name', style)
                f.write(f"【{style_name}】\n")
                f.write(f"{translation}\n\n")
    
    print(f"✓ 对比结果已保存到: {filename}")


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(test_styles())

