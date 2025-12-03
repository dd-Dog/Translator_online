"""
在标准数据集上评估翻译系统
"""

import asyncio
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()


def load_config():
    """加载配置文件"""
    config_path = Path("config/models.yaml")
    if not config_path.exists():
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_model_from_config(model_config: dict, model_type: str):
    """从配置创建模型实例"""
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    
    if not model_config.get('enabled', False):
        return None
    
    api_key_env = model_config.get('api_key_env')
    api_key = os.getenv(api_key_env) if api_key_env else None
    if not api_key:
        return None
    
    model_name = model_config.get('model')
    params = model_config.get('params', {})
    base_url = model_config.get('base_url')
    use_openrouter = model_config.get('use_openrouter', False)
    
    try:
        if model_type == 'openai':
            return OpenAIModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'gemini':
            return GeminiModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'qwen':
            return QwenModel(model_name, api_key, base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1", **params)
    except:
        return None


def calculate_bleu(candidate: str, reference: str) -> float:
    """计算BLEU分数（简化版）"""
    try:
        from nltk.translate.bleu_score import sentence_bleu
        from nltk.tokenize import word_tokenize
        
        # 中文按字符分词
        ref_tokens = list(reference)
        cand_tokens = list(candidate)
        
        score = sentence_bleu([ref_tokens], cand_tokens)
        return score
    except:
        # 如果nltk未安装，返回简单的字符匹配率
        common = sum(1 for c in candidate if c in reference)
        return common / max(len(reference), 1)


async def evaluate_on_flores(pipeline, num_samples: int = 100):
    """在FLORES-200数据集上评估"""
    print("=" * 60)
    print("在 FLORES-200 数据集上评估")
    print("=" * 60)
    
    try:
        from datasets import load_dataset
        
        print(f"\n正在加载 FLORES-200 数据集...")
        dataset = load_dataset("facebook/flores", "eng_Latn-zho_Hans")
        test_data = dataset['devtest']
        
        print(f"✓ 数据集加载成功，共 {len(test_data)} 条")
        print(f"  将测试前 {num_samples} 条\n")
        
    except Exception as e:
        print(f"❌ 加载数据集失败: {e}")
        print("   请先安装: pip install datasets")
        return None
    
    results = []
    
    for i, item in enumerate(test_data[:num_samples]):
        source = item['sentence_eng_Latn']
        reference = item['sentence_zho_Hans']
        
        print(f"\n[{i+1}/{num_samples}] 翻译中...")
        print(f"  原文: {source[:60]}...")
        
        try:
            # 使用系统翻译
            result = await pipeline.translate(
                text=source,
                source_lang="en",
                target_lang="zh"
            )
            
            translation = result.translated_text
            
            # 计算BLEU
            bleu = calculate_bleu(translation, reference)
            
            # 获取系统评分
            system_score = 0.0
            if result.explainability_report.final_quality_score:
                system_score = result.explainability_report.final_quality_score.overall
            
            results.append({
                'id': i + 1,
                'source': source,
                'reference': reference,
                'translation': translation,
                'bleu': bleu,
                'system_score': system_score
            })
            
            print(f"  ✓ BLEU: {bleu:.4f}, 系统评分: {system_score:.2f}")
            
        except Exception as e:
            print(f"  ❌ 翻译失败: {e}")
            continue
    
    return results


def analyze_results(results):
    """分析评估结果"""
    if not results:
        print("没有结果可分析")
        return
    
    print("\n" + "=" * 60)
    print("📊 评估结果分析")
    print("=" * 60)
    
    bleu_scores = [r['bleu'] for r in results]
    system_scores = [r['system_score'] for r in results]
    
    print(f"\n【BLEU分数统计】")
    print(f"  平均值: {sum(bleu_scores)/len(bleu_scores):.4f}")
    print(f"  最大值: {max(bleu_scores):.4f}")
    print(f"  最小值: {min(bleu_scores):.4f}")
    print(f"  中位数: {sorted(bleu_scores)[len(bleu_scores)//2]:.4f}")
    
    print(f"\n【系统评分统计】")
    print(f"  平均值: {sum(system_scores)/len(system_scores):.4f}")
    print(f"  最大值: {max(system_scores):.4f}")
    print(f"  最小值: {min(system_scores):.4f}")
    print(f"  中位数: {sorted(system_scores)[len(system_scores)//2]:.4f}")
    
    # 相关性分析
    try:
        import numpy as np
        correlation = np.corrcoef(bleu_scores, system_scores)[0, 1]
        print(f"\n【相关性分析】")
        print(f"  BLEU与系统评分的相关系数: {correlation:.4f}")
        if correlation > 0.7:
            print(f"  相关性: 强相关 ✓")
        elif correlation > 0.4:
            print(f"  相关性: 中等相关")
        else:
            print(f"  相关性: 弱相关 ⚠️")
    except:
        print(f"\n  (需要numpy计算相关性)")
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_samples': len(results),
                'avg_bleu': sum(bleu_scores)/len(bleu_scores),
                'avg_system_score': sum(system_scores)/len(system_scores),
            },
            'details': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 详细结果已保存到: {filename}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("翻译系统数据集评估")
    print("=" * 60)
    
    # 加载配置并创建工作流
    config = load_config()
    if not config:
        print("❌ 无法加载配置文件")
        return
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    style_config = config.get('style', {})
    
    print("\n🔧 创建模型...")
    
    # 创建模型（简化版，只创建必要的模型）
    planner = create_model_from_config(
        models_config.get(workflow_config.get('planner', {}).get('model', 'openai'), {}),
        workflow_config.get('planner', {}).get('model', 'openai')
    )
    translator_a = create_model_from_config(
        models_config.get(workflow_config.get('translator_a', {}).get('model', 'gemini'), {}),
        workflow_config.get('translator_a', {}).get('model', 'gemini')
    )
    translator_b = create_model_from_config(
        models_config.get(workflow_config.get('translator_b', {}).get('model', 'qwen'), {}),
        workflow_config.get('translator_b', {}).get('model', 'qwen')
    )
    checker = create_model_from_config(
        models_config.get(workflow_config.get('checker', {}).get('model', 'openai'), {}),
        workflow_config.get('checker', {}).get('model', 'openai')
    )
    stylist = create_model_from_config(
        models_config.get(workflow_config.get('stylist', {}).get('model', 'qwen'), {}),
        workflow_config.get('stylist', {}).get('model', 'qwen')
    )
    aggregator = create_model_from_config(
        models_config.get(workflow_config.get('aggregator', {}).get('model', 'openai'), {}),
        workflow_config.get('aggregator', {}).get('model', 'openai')
    )
    
    if not all([planner, translator_a, translator_b, checker, stylist, aggregator]):
        print("❌ 部分模型创建失败，请检查配置和API密钥")
        return
    
    print("✓ 所有模型创建成功")
    
    # 创建工作流
    from src.agents.pipeline import TranslationPipeline
    
    pipeline = TranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        glossary=style_config.get('glossary', {}),
        style=style_config.get('default', 'general')
    )
    
    print("✓ 工作流创建成功\n")
    
    # 选择数据集
    print("请选择数据集:")
    print("  1. FLORES-200 (推荐，100条)")
    print("  2. 自定义测试（手动输入）")
    
    choice = input("\n请输入选项 (1-2，默认1): ").strip() or "1"
    
    if choice == "1":
        # FLORES-200评估
        num_samples = int(input("请输入测试样本数量 (默认100): ").strip() or "100")
        results = await evaluate_on_flores(pipeline, num_samples)
        
        if results:
            analyze_results(results)
    else:
        # 自定义测试
        print("\n请输入要翻译的文本:")
        text = input().strip()
        if text:
            result = await pipeline.translate(text, source_lang="auto", target_lang="zh")
            print(f"\n翻译结果: {result.translated_text}")
            if result.explainability_report.final_quality_score:
                score = result.explainability_report.final_quality_score
                print(f"系统评分: {score.overall:.2f}")


if __name__ == "__main__":
    asyncio.run(main())

