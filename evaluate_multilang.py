"""
多语言评估 - 测试日语和法语翻译成中文
每种语言5条样本
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import statistics
from collections import defaultdict

load_dotenv()


def load_test_data():
    """加载多语言测试数据"""
    with open("test_data/multilang_sample.json", 'r', encoding='utf-8') as f:
        return json.load(f)


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


async def evaluate_multilang():
    """多语言评估"""
    print("\n" + "=" * 80)
    print("🌍 多语言翻译评估 - 日语和法语 → 中文")
    print("=" * 80)
    
    # 初始化专业评估模型（开发模式）
    from src.evaluation.combined_scorer import CombinedQualityScorer
    
    print("\n【1/3】初始化专业评估模型（开发模式）...")
    scorer = CombinedQualityScorer(
        use_comet=False,
        use_bleurt=False,
        use_bertscore=True
    )
    scorer.initialize()
    print("✓ BERTScore已就绪")
    
    # 加载测试数据
    print("\n【2/3】加载测试数据...")
    test_data = load_test_data()
    
    # 按语言分组
    lang_groups = defaultdict(list)
    for item in test_data:
        lang_groups[item['source_lang']].append(item)
    
    print(f"✓ 加载测试数据:")
    for lang, items in lang_groups.items():
        lang_name = {"ja": "日语", "fr": "法语"}.get(lang, lang)
        print(f"  {lang_name} ({lang}): {len(items)} 条")
    
    # 创建翻译pipeline
    print("\n【3/3】创建翻译系统...")
    config = load_config()
    if not config:
        print("❌ 无法加载配置文件")
        return
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    style_config = config.get('style', {})
    
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
        print("❌ 部分模型创建失败")
        return
    
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
    print("✓ 翻译系统创建成功")
    
    # 开始评估
    print("\n" + "=" * 80)
    print("开始评估...")
    print("=" * 80)
    
    all_results = []
    import time
    start_time = time.time()
    
    # 按语言评估
    for lang, items in sorted(lang_groups.items()):
        lang_name = {"ja": "日语", "fr": "法语"}.get(lang, lang)
        print(f"\n{'='*80}")
        print(f"📝 评估 {lang_name} ({lang}) → 中文")
        print(f"{'='*80}")
        
        lang_results = []
        
        for i, item in enumerate(items, 1):
            print(f"\n[{i}/{len(items)}] 评估中...")
            print(f"原文 ({lang}): {item['source']}")
            print(f"参考翻译: {item['reference']}")
            
            try:
                # 翻译
                print("正在翻译...")
                result = await pipeline.translate(
                    text=item['source'],
                    source_lang=item.get('source_lang', 'auto'),
                    target_lang=item.get('target_lang', 'zh')
                )
                
                translation = result.translated_text
                print(f"系统翻译: {translation}")
                
                # 获取MQM评分
                mqm_score = None
                if result.explainability_report.final_quality_score:
                    score = result.explainability_report.final_quality_score
                    mqm_score = {
                        'adequacy': score.adequacy,
                        'fluency': score.fluency,
                        'terminology': score.terminology,
                        'overall': score.overall
                    }
                
                # 专业评估
                comprehensive_score = scorer.score(
                    source=item['source'],
                    translation=translation,
                    reference=item['reference'],
                    mqm_score=mqm_score
                )
                
                print(f"评估结果:")
                print(f"  BLEU: {comprehensive_score.bleu:.4f}")
                if comprehensive_score.bertscore_f1 > 0:
                    print(f"  BERTScore F1: {comprehensive_score.bertscore_f1:.4f}")
                print(f"  MQM Overall: {comprehensive_score.mqm_overall:.4f}")
                print(f"  🎯 综合评分: {comprehensive_score.final_score:.4f}")
                
                lang_results.append({
                    'id': item['id'],
                    'source_lang': lang,
                    'domain': item.get('domain', 'general'),
                    'source': item['source'],
                    'reference': item['reference'],
                    'translation': translation,
                    'scores': {
                        'bleu': comprehensive_score.bleu,
                        'bertscore_f1': comprehensive_score.bertscore_f1,
                        'mqm_overall': comprehensive_score.mqm_overall,
                        'final_score': comprehensive_score.final_score
                    }
                })
                
            except Exception as e:
                print(f"❌ 翻译失败: {e}")
                lang_results.append({
                    'id': item['id'],
                    'source_lang': lang,
                    'source': item['source'],
                    'reference': item['reference'],
                    'translation': None,
                    'error': str(e)
                })
        
        all_results.extend(lang_results)
    
    elapsed_time = time.time() - start_time
    
    # 生成报告
    print("\n" + "=" * 80)
    print("📊 评估总结")
    print("=" * 80)
    
    # 按语言统计
    for lang, lang_name in [("ja", "日语"), ("fr", "法语")]:
        lang_results = [r for r in all_results if r.get('source_lang') == lang and r.get('translation')]
        if not lang_results:
            continue
        
        print(f"\n【{lang_name} ({lang})】")
        print(f"  样本数: {len(lang_results)}")
        
        bleu_scores = [r['scores']['bleu'] for r in lang_results]
        bertscore_scores = [r['scores']['bertscore_f1'] for r in lang_results if r['scores']['bertscore_f1'] > 0]
        mqm_scores = [r['scores']['mqm_overall'] for r in lang_results]
        final_scores = [r['scores']['final_score'] for r in lang_results]
        
        print(f"  平均BLEU: {statistics.mean(bleu_scores):.4f}")
        if bertscore_scores:
            print(f"  平均BERTScore: {statistics.mean(bertscore_scores):.4f}")
        print(f"  平均MQM: {statistics.mean(mqm_scores):.4f}")
        print(f"  平均综合评分: {statistics.mean(final_scores):.4f}")
        print(f"  评分范围: {min(final_scores):.4f} - {max(final_scores):.4f}")
    
    # 总体统计
    valid_results = [r for r in all_results if r.get('translation')]
    print(f"\n【总体统计】")
    print(f"  总样本数: {len(all_results)}")
    print(f"  成功翻译: {len(valid_results)}")
    print(f"  成功率: {len(valid_results)/len(all_results)*100:.1f}%")
    print(f"  总耗时: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
    
    if valid_results:
        all_bleu = [r['scores']['bleu'] for r in valid_results]
        all_bertscore = [r['scores']['bertscore_f1'] for r in valid_results if r['scores']['bertscore_f1'] > 0]
        all_mqm = [r['scores']['mqm_overall'] for r in valid_results]
        all_final = [r['scores']['final_score'] for r in valid_results]
        
        print(f"\n【所有语言平均】")
        print(f"  平均BLEU: {statistics.mean(all_bleu):.4f}")
        if all_bertscore:
            print(f"  平均BERTScore: {statistics.mean(all_bertscore):.4f}")
        print(f"  平均MQM: {statistics.mean(all_mqm):.4f}")
        print(f"  平均综合评分: {statistics.mean(all_final):.4f}")
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"multilang_evaluation_{timestamp}.json"
    md_file = f"multilang_evaluation_{timestamp}.md"
    
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'languages': list(lang_groups.keys()),
            'total_samples': len(all_results),
            'successful': len(valid_results),
            'total_time_seconds': elapsed_time
        },
        'by_language': {},
        'summary': {},
        'results': all_results
    }
    
    # 按语言统计
    for lang, lang_name in [("ja", "日语"), ("fr", "法语")]:
        lang_results = [r for r in valid_results if r.get('source_lang') == lang]
        if lang_results:
            lang_final = [r['scores']['final_score'] for r in lang_results]
            lang_bleu = [r['scores']['bleu'] for r in lang_results]
            lang_bertscore = [r['scores']['bertscore_f1'] for r in lang_results if r['scores']['bertscore_f1'] > 0]
            
            report['by_language'][lang] = {
                'name': lang_name,
                'count': len(lang_results),
                'avg_final_score': statistics.mean(lang_final) if lang_final else 0,
                'avg_bleu': statistics.mean(lang_bleu) if lang_bleu else 0,
                'avg_bertscore': statistics.mean(lang_bertscore) if lang_bertscore else 0
            }
    
    # 总体统计
    if valid_results:
        report['summary'] = {
            'avg_bleu': statistics.mean(all_bleu) if all_bleu else 0,
            'avg_bertscore': statistics.mean(all_bertscore) if all_bertscore else 0,
            'avg_mqm': statistics.mean(all_mqm) if all_mqm else 0,
            'avg_final_score': statistics.mean(all_final) if all_final else 0
        }
    
    # 保存JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 多语言翻译评估报告\n\n")
        f.write(f"**评估时间**: {report['metadata']['timestamp']}\n\n")
        f.write(f"**测试语言**: {', '.join([{'ja': '日语', 'fr': '法语'}.get(l, l) for l in report['metadata']['languages']])}\n\n")
        
        f.write("## 📊 总体统计\n\n")
        f.write(f"- 总样本数: {report['metadata']['total_samples']}\n")
        f.write(f"- 成功翻译: {report['metadata']['successful']}\n")
        f.write(f"- 成功率: {report['metadata']['successful']/report['metadata']['total_samples']*100:.1f}%\n")
        f.write(f"- 总耗时: {report['metadata']['total_time_seconds']:.1f}秒\n\n")
        
        if report['summary']:
            f.write("## 📈 评估指标\n\n")
            f.write(f"- 平均BLEU: {report['summary']['avg_bleu']:.4f}\n")
            f.write(f"- 平均BERTScore: {report['summary']['avg_bertscore']:.4f}\n")
            f.write(f"- 平均MQM: {report['summary']['avg_mqm']:.4f}\n")
            f.write(f"- 平均综合评分: {report['summary']['avg_final_score']:.4f}\n\n")
        
        f.write("## 🌍 按语言统计\n\n")
        for lang, stats in report['by_language'].items():
            f.write(f"### {stats['name']} ({lang})\n\n")
            f.write(f"- 样本数: {stats['count']}\n")
            f.write(f"- 平均综合评分: {stats['avg_final_score']:.4f}\n")
            f.write(f"- 平均BLEU: {stats['avg_bleu']:.4f}\n")
            f.write(f"- 平均BERTScore: {stats['avg_bertscore']:.4f}\n\n")
        
        f.write("## 📝 详细结果\n\n")
        f.write("| ID | 源语言 | 原文 | 参考翻译 | 系统翻译 | BLEU | BERTScore | MQM | 综合评分 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        
        for r in report['results']:
            if r.get('translation'):
                source_short = r['source'][:30] + '...' if len(r['source']) > 30 else r['source']
                ref_short = r['reference'][:30] + '...' if len(r['reference']) > 30 else r['reference']
                trans_short = r['translation'][:30] + '...' if len(r['translation']) > 30 else r['translation']
                lang_name = {'ja': '日语', 'fr': '法语'}.get(r['source_lang'], r['source_lang'])
                f.write(f"| {r['id']} | {lang_name} | {source_short} | {ref_short} | {trans_short} | "
                       f"{r['scores']['bleu']:.3f} | {r['scores']['bertscore_f1']:.3f} | "
                       f"{r['scores']['mqm_overall']:.3f} | **{r['scores']['final_score']:.3f}** |\n")
            else:
                lang_name = {'ja': '日语', 'fr': '法语'}.get(r.get('source_lang', ''), '')
                f.write(f"| {r['id']} | {lang_name} | {r['source'][:30]} | {r['reference'][:30]} | ❌失败 | - | - | - | - |\n")
    
    print(f"\n{'='*80}")
    print(f"✓ JSON报告已保存到: {json_file}")
    print(f"✓ Markdown报告已保存到: {md_file}")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(evaluate_multilang())

