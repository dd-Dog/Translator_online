"""
按照config/models.yaml配置测试完整工作流
"""

import asyncio
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def load_config():
    """加载配置文件"""
    config_path = Path("config/models.yaml")
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_model_from_config(model_config: dict, model_type: str):
    """从配置创建模型实例"""
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    from src.models.claude import ClaudeModel
    from src.models.deepseek import DeepSeekModel
    
    if not model_config.get('enabled', False):
        return None
    
    api_key_env = model_config.get('api_key_env')
    if not api_key_env:
        return None
    
    api_key = os.getenv(api_key_env)
    if not api_key:
        print(f"⚠️  未找到环境变量: {api_key_env}")
        return None
    
    model_name = model_config.get('model')
    if not model_name:
        return None
    
    params = model_config.get('params', {})
    base_url = model_config.get('base_url')
    use_openrouter = model_config.get('use_openrouter', False)
    
    try:
        if model_type == 'openai':
            model = OpenAIModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'gemini':
            model = GeminiModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                use_openrouter=use_openrouter,
                **params
            )
        elif model_type == 'qwen':
            model = QwenModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                **params
            )
        elif model_type == 'deepseek':
            model = DeepSeekModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://api.deepseek.com",
                **params
            )
        elif model_type == 'claude':
            model = ClaudeModel(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url or "https://openrouter.ai/api/v1",
                **params
            )
        else:
            return None
        
        if model.validate_config():
            return model
        else:
            print(f"⚠️  {model_type} 模型配置验证失败")
            return None
            
    except Exception as e:
        print(f"❌ 创建 {model_type} 模型失败: {e}")
        return None


async def test_workflow_from_config():
    """按照配置文件测试完整工作流"""
    print("=" * 60)
    print("按照 config/models.yaml 配置测试完整工作流")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config:
        return
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    style_config = config.get('style', {})
    
    print("\n📋 工作流配置:")
    print(f"  Planner: {workflow_config.get('planner', {}).get('model', 'N/A')}")
    print(f"  Translator-A: {workflow_config.get('translator_a', {}).get('model', 'N/A')}")
    print(f"  Translator-B: {workflow_config.get('translator_b', {}).get('model', 'N/A')}")
    print(f"  Checker: {workflow_config.get('checker', {}).get('model', 'N/A')}")
    print(f"  Stylist: {workflow_config.get('stylist', {}).get('model', 'N/A')}")
    print(f"  Aggregator: {workflow_config.get('aggregator', {}).get('model', 'N/A')}")
    
    # 创建各个模型
    print("\n🔧 创建模型实例...")
    
    planner_model_name = workflow_config.get('planner', {}).get('model', 'openai')
    planner_config = models_config.get(planner_model_name, {})
    planner_model = create_model_from_config(planner_config, planner_model_name)
    if not planner_model:
        print(f"❌ 无法创建 Planner 模型 ({planner_model_name})")
        return
    print(f"  ✓ Planner: {planner_model_name} ({planner_model.model_name})")
    
    translator_a_model_name = workflow_config.get('translator_a', {}).get('model', 'gemini')
    translator_a_config = models_config.get(translator_a_model_name, {})
    translator_a_model = create_model_from_config(translator_a_config, translator_a_model_name)
    if not translator_a_model:
        print(f"❌ 无法创建 Translator-A 模型 ({translator_a_model_name})")
        return
    print(f"  ✓ Translator-A: {translator_a_model_name} ({translator_a_model.model_name})")
    
    translator_b_model_name = workflow_config.get('translator_b', {}).get('model', 'qwen')
    translator_b_config = models_config.get(translator_b_model_name, {})
    translator_b_model = create_model_from_config(translator_b_config, translator_b_model_name)
    if not translator_b_model:
        print(f"❌ 无法创建 Translator-B 模型 ({translator_b_model_name})")
        return
    print(f"  ✓ Translator-B: {translator_b_model_name} ({translator_b_model.model_name})")
    
    checker_model_name = workflow_config.get('checker', {}).get('model', 'openai')
    checker_config = models_config.get(checker_model_name, {})
    checker_model = create_model_from_config(checker_config, checker_model_name)
    if not checker_model:
        print(f"❌ 无法创建 Checker 模型 ({checker_model_name})")
        return
    print(f"  ✓ Checker: {checker_model_name} ({checker_model.model_name})")
    
    stylist_model_name = workflow_config.get('stylist', {}).get('model', 'qwen')
    stylist_config = models_config.get(stylist_model_name, {})
    stylist_model = create_model_from_config(stylist_config, stylist_model_name)
    if not stylist_model:
        print(f"❌ 无法创建 Stylist 模型 ({stylist_model_name})")
        return
    print(f"  ✓ Stylist: {stylist_model_name} ({stylist_model.model_name})")
    
    aggregator_model_name = workflow_config.get('aggregator', {}).get('model', 'openai')
    aggregator_config = models_config.get(aggregator_model_name, {})
    aggregator_model = create_model_from_config(aggregator_config, aggregator_model_name)
    if not aggregator_model:
        print(f"❌ 无法创建 Aggregator 模型 ({aggregator_model_name})")
        return
    print(f"  ✓ Aggregator: {aggregator_model_name} ({aggregator_model.model_name})")
    
    # 创建工作流
    print("\n🚀 创建工作流...")
    from src.agents.pipeline import TranslationPipeline
    
    glossary = style_config.get('glossary', {})
    default_style = style_config.get('default', 'general')
    
    pipeline = TranslationPipeline(
        planner_model=planner_model,
        translator_a_model=translator_a_model,
        translator_b_model=translator_b_model,
        checker_model=checker_model,
        stylist_model=stylist_model,
        aggregator_model=aggregator_model,
        glossary=glossary,
        style=default_style
    )
    print("  ✓ 工作流创建成功")
    
    # 获取用户输入
    print(f"\n{'='*60}")
    print("翻译配置")
    print(f"{'='*60}")
    
    # 1. 设置目标语言
    print("\n请选择目标语言:")
    print("  1. 中文 (zh)")
    print("  2. 英文 (en)")
    print("  3. 日文 (ja)")
    print("  4. 韩文 (ko)")
    print("  5. 法文 (fr)")
    print("  6. 德文 (de)")
    print("  7. 西班牙文 (es)")
    print("  8. 自定义")
    
    lang_choice = input("\n请输入选项 (1-8，默认1): ").strip() or "1"
    
    lang_map = {
        "1": "zh", "2": "en", "3": "ja", "4": "ko",
        "5": "fr", "6": "de", "7": "es"
    }
    
    if lang_choice == "8":
        target_lang = input("请输入目标语言代码 (如: zh, en, ja等): ").strip() or "zh"
    else:
        target_lang = lang_map.get(lang_choice, "zh")
    
    print(f"✓ 目标语言: {target_lang}")
    
    # 2. 设定翻译原文内容
    print(f"\n{'='*60}")
    print("输入翻译原文")
    print(f"{'='*60}")
    print("请输入要翻译的文本（支持多行，输入空行结束）:")
    
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    
    if not lines:
        # 如果没有输入，使用默认示例
        text = "Machine learning is a subset of artificial intelligence."
        print(f"\n使用默认示例文本: {text}")
    else:
        text = "\n".join(lines)
    
    print(f"\n✓ 原文内容 ({len(text)} 字符):")
    print(f"  {text[:100]}{'...' if len(text) > 100 else ''}")
    
    # 3. 开始翻译
    print(f"\n{'='*60}")
    print("开始完整工作流翻译...")
    print(f"{'='*60}")
    print("(这需要调用多个模型，可能需要一些时间)\n")
    
    try:
        result = await pipeline.translate(
            text=text,
            source_lang="auto",  # 自动检测源语言
            target_lang=target_lang
        )
        
        # 4. 输出详细结果
        print(f"\n{'='*60}")
        print("📊 翻译结果详情")
        print(f"{'='*60}")
        
        # 4.1 基本信息
        print(f"\n【基本信息】")
        print(f"  源语言: {result.source_lang}")
        print(f"  目标语言: {result.target_lang}")
        print(f"  原文长度: {len(text)} 字符")
        print(f"  译文长度: {len(result.translated_text)} 字符")
        
        # 4.2 处理阶段
        print(f"\n【处理阶段】")
        for j, stage in enumerate(result.processing_stages, 1):
            print(f"  {j}. {stage}")
        
        # 4.3 最终翻译结果
        print(f"\n【最终翻译结果】")
        print(f"  {result.translated_text}")
        
        # 4.4 质量评分详情
        if result.explainability_report.final_quality_score:
            score = result.explainability_report.final_quality_score
            print(f"\n【质量评分详情】")
            print(f"  充分性 (Adequacy): {score.adequacy:.2f} / 1.00")
            print(f"    - 评估翻译是否完整传达了原文意思")
            print(f"  流畅性 (Fluency): {score.fluency:.2f} / 1.00")
            print(f"    - 评估翻译是否自然流畅")
            print(f"  术语准确性 (Terminology): {score.terminology:.2f} / 1.00")
            print(f"    - 评估专业术语是否准确")
            print(f"  总体评分: {score.overall:.2f} / 1.00")
            
            # 评分等级
            if score.overall >= 0.9:
                level = "优秀"
            elif score.overall >= 0.8:
                level = "良好"
            elif score.overall >= 0.7:
                level = "中等"
            else:
                level = "需改进"
            print(f"  评分等级: {level}")
        
        # 4.5 修改记录详情
        if result.explainability_report.modifications:
            print(f"\n【修改记录详情】")
            print(f"  总修改数: {len(result.explainability_report.modifications)}")
            
            # 按阶段分组
            by_stage = {}
            for mod in result.explainability_report.modifications:
                stage = mod.get('stage', 'Unknown')
                if stage not in by_stage:
                    by_stage[stage] = []
                by_stage[stage].append(mod)
            
            for stage, mods in by_stage.items():
                print(f"\n  {stage} ({len(mods)} 处修改):")
                for mod in mods[:5]:  # 每个阶段最多显示5个
                    print(f"    - {mod.get('reason', 'N/A')[:60]}...")
                if len(mods) > 5:
                    print(f"    ... 还有 {len(mods) - 5} 处修改")
        
        # 4.6 质量改进详情
        if result.explainability_report.quality_improvements:
            print(f"\n【质量改进详情】")
            for metric, improvement in result.explainability_report.quality_improvements.items():
                before = improvement.get('before', 0)
                after = improvement.get('after', 0)
                imp = improvement.get('improvement', 0)
                print(f"  {metric}:")
                print(f"    改进前: {before:.2f}")
                print(f"    改进后: {after:.2f}")
                print(f"    提升: {imp:+.2f}")
        
        # 4.7 输出到文件（可选）
        print(f"\n{'='*60}")
        save_choice = input("是否保存详细结果到文件? (y/n，默认n): ").strip().lower()
        if save_choice == 'y':
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"translation_result_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("翻译结果详情\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"源语言: {result.source_lang}\n")
                f.write(f"目标语言: {result.target_lang}\n\n")
                f.write(f"原文:\n{text}\n\n")
                f.write(f"最终翻译:\n{result.translated_text}\n\n")
                f.write(f"处理阶段:\n")
                for j, stage in enumerate(result.processing_stages, 1):
                    f.write(f"  {j}. {stage}\n")
                f.write(f"\n质量评分:\n")
                if result.explainability_report.final_quality_score:
                    score = result.explainability_report.final_quality_score
                    f.write(f"  充分性: {score.adequacy:.2f}\n")
                    f.write(f"  流畅性: {score.fluency:.2f}\n")
                    f.write(f"  术语准确性: {score.terminology:.2f}\n")
                    f.write(f"  总体: {score.overall:.2f}\n")
                if result.explainability_report.modifications:
                    f.write(f"\n修改记录 ({len(result.explainability_report.modifications)} 处):\n")
                    for mod in result.explainability_report.modifications:
                        f.write(f"  [{mod.get('stage', 'N/A')}] {mod.get('reason', 'N/A')}\n")
            
            print(f"  ✓ 结果已保存到: {filename}")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_workflow_from_config())

