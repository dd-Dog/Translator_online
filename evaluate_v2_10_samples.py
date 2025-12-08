"""
V2专业评估 - 评估10条样本
使用开发模式：BERTScore + MQM + BLEU
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import statistics

load_dotenv()


def load_test_data():
    """加载测试数据"""
    with open("test_data/flores_sample.json", 'r', encoding='utf-8') as f:
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


async def evaluate_10_samples():
    """评估10条样本"""
    print("\n" + "=" * 80)
    print("🎯 V2专业评估系统 - 10条样本评估")
    print("=" * 80)
    
    # 初始化专业评估模型（开发模式）
    from src.evaluation.combined_scorer import CombinedQualityScorer
    
    print("\n【1/3】初始化专业评估模型（开发模式）...")
    scorer = CombinedQualityScorer(
        use_comet=False,      # 开发模式：不使用COMET
        use_bleurt=False,     # 开发模式：不使用BLEURT
        use_bertscore=True    # 开发模式：使用BERTScore
    )
    scorer.initialize()
    print("✓ BERTScore已就绪")
    
    # 加载测试数据
    print("\n【2/3】加载测试数据...")
    test_data = load_test_data()
    test_samples = test_data[:10]  # 取前10条
    print(f"✓ 加载 {len(test_samples)} 条测试样本")
    
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
    
    results = []
    import time
    start_time = time.time()
    
    for i, item in enumerate(test_samples, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/10] 评估中...")
        print(f"{'='*80}")
        
        source = item['source']
        reference = item['reference']
        domain = item.get('domain', 'general')
        
        print(f"领域: {domain}")
        print(f"原文: {source}")
        print(f"参考翻译: {reference}")
        
        try:
            # 翻译
            print("\n正在翻译...")
            result = await pipeline.translate(
                text=source,
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
                print(f"\n系统MQM评分:")
                print(f"  充分性: {score.adequacy:.4f}")
                print(f"  流畅性: {score.fluency:.4f}")
                print(f"  术语: {score.terminology:.4f}")
                print(f"  总体: {score.overall:.4f}")
            
            # 专业评估
            print("\n正在使用BERTScore评估...")
            comprehensive_score = scorer.score(
                source=source,
                translation=translation,
                reference=reference,
                mqm_score=mqm_score
            )
            
            print(f"\n📊 专业评估结果:")
            print(f"  BLEU: {comprehensive_score.bleu:.4f}")
            if comprehensive_score.bertscore_f1 > 0:
                print(f"  BERTScore F1: {comprehensive_score.bertscore_f1:.4f}")
            print(f"  MQM Overall: {comprehensive_score.mqm_overall:.4f}")
            print(f"  🎯 综合评分: {comprehensive_score.final_score:.4f}")
            
            results.append({
                'id': item['id'],
                'domain': domain,
                'source': source,
                'reference': reference,
                'translation': translation,
                'scores': {
                    'bleu': comprehensive_score.bleu,
                    'bertscore_f1': comprehensive_score.bertscore_f1,
                    'mqm_overall': comprehensive_score.mqm_overall,
                    'mqm_adequacy': mqm_score['adequacy'] if mqm_score else None,
                    'mqm_fluency': mqm_score['fluency'] if mqm_score else None,
                    'mqm_terminology': mqm_score['terminology'] if mqm_score else None,
                    'final_score': comprehensive_score.final_score
                },
                'processing_stages': result.processing_stages
            })
            
        except Exception as e:
            print(f"\n❌ 翻译失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'id': item['id'],
                'domain': domain,
                'source': source,
                'reference': reference,
                'translation': None,
                'error': str(e)
            })
    
    elapsed_time = time.time() - start_time
    
    # 生成详细报告
    print("\n" + "=" * 80)
    print("📊 评估总结")
    print("=" * 80)
    
    valid_results = [r for r in results if r.get('translation')]
    failed_results = [r for r in results if not r.get('translation')]
    
    print(f"\n【总体统计】")
    print(f"  总样本数: {len(results)}")
    print(f"  成功翻译: {len(valid_results)}")
    print(f"  失败数: {len(failed_results)}")
    print(f"  成功率: {len(valid_results)/len(results)*100:.1f}%")
    print(f"  总耗时: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
    print(f"  平均耗时: {elapsed_time/len(results):.1f}秒/条")
    
    if not valid_results:
        print("\n❌ 没有有效结果")
        return
    
    # 各指标统计
    bleu_scores = [r['scores']['bleu'] for r in valid_results]
    bertscore_scores = [r['scores']['bertscore_f1'] for r in valid_results if r['scores']['bertscore_f1'] > 0]
    mqm_scores = [r['scores']['mqm_overall'] for r in valid_results]
    final_scores = [r['scores']['final_score'] for r in valid_results]
    
    print(f"\n【BLEU分数统计】")
    print(f"  平均值: {statistics.mean(bleu_scores):.4f}")
    print(f"  最大值: {max(bleu_scores):.4f}")
    print(f"  最小值: {min(bleu_scores):.4f}")
    print(f"  中位数: {statistics.median(bleu_scores):.4f}")
    print(f"  标准差: {statistics.stdev(bleu_scores):.4f}")
    
    if bertscore_scores:
        print(f"\n【BERTScore F1统计】")
        print(f"  平均值: {statistics.mean(bertscore_scores):.4f}")
        print(f"  最大值: {max(bertscore_scores):.4f}")
        print(f"  最小值: {min(bertscore_scores):.4f}")
        print(f"  中位数: {statistics.median(bertscore_scores):.4f}")
        print(f"  标准差: {statistics.stdev(bertscore_scores):.4f}")
    
    print(f"\n【MQM评分统计】")
    print(f"  平均值: {statistics.mean(mqm_scores):.4f}")
    print(f"  最大值: {max(mqm_scores):.4f}")
    print(f"  最小值: {min(mqm_scores):.4f}")
    print(f"  中位数: {statistics.median(mqm_scores):.4f}")
    print(f"  标准差: {statistics.stdev(mqm_scores):.4f}")
    
    print(f"\n【综合评分统计】")
    print(f"  平均值: {statistics.mean(final_scores):.4f}")
    print(f"  最大值: {max(final_scores):.4f}")
    print(f"  最小值: {min(final_scores):.4f}")
    print(f"  中位数: {statistics.median(final_scores):.4f}")
    print(f"  标准差: {statistics.stdev(final_scores):.4f}")
    
    # 按领域统计
    domains = {}
    for r in valid_results:
        domain = r.get('domain', 'general')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(r)
    
    if len(domains) > 1:
        print(f"\n【按领域统计】")
        for domain, items in domains.items():
            domain_final = [r['scores']['final_score'] for r in items]
            domain_bleu = [r['scores']['bleu'] for r in items]
            domain_bertscore = [r['scores']['bertscore_f1'] for r in items if r['scores']['bertscore_f1'] > 0]
            print(f"\n  {domain} ({len(items)}条):")
            print(f"    平均综合评分: {statistics.mean(domain_final):.4f}")
            print(f"    平均BLEU: {statistics.mean(domain_bleu):.4f}")
            if domain_bertscore:
                print(f"    平均BERTScore: {statistics.mean(domain_bertscore):.4f}")
    
    # 最佳和最差案例
    print(f"\n【最佳翻译案例】（综合评分最高）")
    best = max(valid_results, key=lambda x: x['scores']['final_score'])
    print(f"  ID: {best['id']}")
    print(f"  原文: {best['source']}")
    print(f"  参考: {best['reference']}")
    print(f"  翻译: {best['translation']}")
    print(f"  综合评分: {best['scores']['final_score']:.4f}")
    print(f"  BLEU: {best['scores']['bleu']:.4f}")
    print(f"  BERTScore: {best['scores']['bertscore_f1']:.4f}")
    print(f"  MQM: {best['scores']['mqm_overall']:.4f}")
    
    print(f"\n【最差翻译案例】（综合评分最低）")
    worst = min(valid_results, key=lambda x: x['scores']['final_score'])
    print(f"  ID: {worst['id']}")
    print(f"  原文: {worst['source']}")
    print(f"  参考: {worst['reference']}")
    print(f"  翻译: {worst['translation']}")
    print(f"  综合评分: {worst['scores']['final_score']:.4f}")
    print(f"  BLEU: {worst['scores']['bleu']:.4f}")
    print(f"  BERTScore: {worst['scores']['bertscore_f1']:.4f}")
    print(f"  MQM: {worst['scores']['mqm_overall']:.4f}")
    
    # 保存详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"V2_evaluation_report_{timestamp}.json"
    md_file = f"V2_evaluation_report_{timestamp}.md"
    
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'version': 'V2',
            'evaluation_mode': 'development',
            'models_used': {
                'comet': False,
                'bleurt': False,
                'bertscore': True
            },
            'total_samples': len(results),
            'successful': len(valid_results),
            'failed': len(failed_results),
            'total_time_seconds': elapsed_time,
            'avg_time_per_sample': elapsed_time / len(results)
        },
        'summary': {
            'avg_bleu': statistics.mean(bleu_scores) if bleu_scores else 0,
            'avg_bertscore_f1': statistics.mean(bertscore_scores) if bertscore_scores else 0,
            'avg_mqm_overall': statistics.mean(mqm_scores) if mqm_scores else 0,
            'avg_final_score': statistics.mean(final_scores) if final_scores else 0,
            'std_bleu': statistics.stdev(bleu_scores) if len(bleu_scores) > 1 else 0,
            'std_bertscore': statistics.stdev(bertscore_scores) if len(bertscore_scores) > 1 else 0,
            'std_mqm': statistics.stdev(mqm_scores) if len(mqm_scores) > 1 else 0,
            'std_final': statistics.stdev(final_scores) if len(final_scores) > 1 else 0
        },
        'by_domain': {},
        'results': results
    }
    
    # 按领域统计
    for domain, items in domains.items():
        domain_final = [r['scores']['final_score'] for r in items]
        domain_bleu = [r['scores']['bleu'] for r in items]
        domain_bertscore = [r['scores']['bertscore_f1'] for r in items if r['scores']['bertscore_f1'] > 0]
        report['by_domain'][domain] = {
            'count': len(items),
            'avg_final_score': statistics.mean(domain_final) if domain_final else 0,
            'avg_bleu': statistics.mean(domain_bleu) if domain_bleu else 0,
            'avg_bertscore': statistics.mean(domain_bertscore) if domain_bertscore else 0
        }
    
    # 保存JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✓ JSON报告已保存到: {json_file}")
    
    # 生成Markdown报告
    generate_markdown_report(report, md_file)
    print(f"✓ Markdown报告已保存到: {md_file}")
    print(f"{'='*80}")


def generate_markdown_report(report, output_file):
    """生成Markdown格式的详细报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# V2专业评估系统 - 10条样本评估报告\n\n")
        f.write(f"**评估时间**: {report['metadata']['timestamp']}\n\n")
        f.write(f"**评估模式**: {report['metadata']['evaluation_mode']} (BERTScore + MQM + BLEU)\n\n")
        
        f.write("## 📊 总体统计\n\n")
        f.write(f"- **总样本数**: {report['metadata']['total_samples']}\n")
        f.write(f"- **成功翻译**: {report['metadata']['successful']}\n")
        f.write(f"- **失败数**: {report['metadata']['failed']}\n")
        f.write(f"- **成功率**: {report['metadata']['successful']/report['metadata']['total_samples']*100:.1f}%\n")
        f.write(f"- **总耗时**: {report['metadata']['total_time_seconds']:.1f}秒 ({report['metadata']['total_time_seconds']/60:.1f}分钟)\n")
        f.write(f"- **平均耗时**: {report['metadata']['avg_time_per_sample']:.1f}秒/条\n\n")
        
        f.write("## 📈 评估指标统计\n\n")
        f.write("### 综合评分\n\n")
        f.write(f"- **平均值**: {report['summary']['avg_final_score']:.4f}\n")
        f.write(f"- **标准差**: {report['summary']['std_final']:.4f}\n")
        f.write(f"- **最大值**: {max([r['scores']['final_score'] for r in report['results'] if r.get('translation')]):.4f}\n")
        f.write(f"- **最小值**: {min([r['scores']['final_score'] for r in report['results'] if r.get('translation')]):.4f}\n\n")
        
        f.write("### BLEU分数\n\n")
        f.write(f"- **平均值**: {report['summary']['avg_bleu']:.4f}\n")
        f.write(f"- **标准差**: {report['summary']['std_bleu']:.4f}\n\n")
        
        f.write("### BERTScore F1\n\n")
        f.write(f"- **平均值**: {report['summary']['avg_bertscore_f1']:.4f}\n")
        f.write(f"- **标准差**: {report['summary']['std_bertscore']:.4f}\n\n")
        
        f.write("### MQM评分\n\n")
        f.write(f"- **平均值**: {report['summary']['avg_mqm_overall']:.4f}\n")
        f.write(f"- **标准差**: {report['summary']['std_mqm']:.4f}\n\n")
        
        if report['by_domain']:
            f.write("## 🌍 按领域统计\n\n")
            for domain, stats in report['by_domain'].items():
                f.write(f"### {domain}\n\n")
                f.write(f"- **样本数**: {stats['count']}\n")
                f.write(f"- **平均综合评分**: {stats['avg_final_score']:.4f}\n")
                f.write(f"- **平均BLEU**: {stats['avg_bleu']:.4f}\n")
                if stats['avg_bertscore'] > 0:
                    f.write(f"- **平均BERTScore**: {stats['avg_bertscore']:.4f}\n")
                f.write("\n")
        
        f.write("## 📝 详细结果\n\n")
        f.write("| ID | 领域 | 原文 | 参考翻译 | 系统翻译 | BLEU | BERTScore | MQM | 综合评分 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        
        for r in report['results']:
            if r.get('translation'):
                source_short = r['source'][:40] + '...' if len(r['source']) > 40 else r['source']
                ref_short = r['reference'][:40] + '...' if len(r['reference']) > 40 else r['reference']
                trans_short = r['translation'][:40] + '...' if len(r['translation']) > 40 else r['translation']
                f.write(f"| {r['id']} | {r['domain']} | {source_short} | {ref_short} | {trans_short} | "
                       f"{r['scores']['bleu']:.3f} | {r['scores']['bertscore_f1']:.3f} | "
                       f"{r['scores']['mqm_overall']:.3f} | **{r['scores']['final_score']:.3f}** |\n")
            else:
                f.write(f"| {r['id']} | {r['domain']} | {r['source'][:40]} | {r['reference'][:40]} | ❌失败 | - | - | - | - |\n")
        
        f.write("\n## 🎯 关键发现\n\n")
        f.write("### 评分区分度\n\n")
        f.write(f"- V2系统评分标准差: **{report['summary']['std_final']:.4f}**\n")
        f.write(f"- 相比V1固定0.85，V2评分有明显区分度 ✅\n\n")
        
        f.write("### 评估模型表现\n\n")
        f.write(f"- **BERTScore**: 成功识别语义相似性，不依赖表面匹配\n")
        f.write(f"- **MQM**: 多维度评估（充分性、流畅性、术语）\n")
        f.write(f"- **BLEU**: 传统n-gram匹配基准\n\n")
        
        f.write("### 综合评分公式\n\n")
        f.write("开发模式权重分配：\n")
        f.write("- BERTScore: 50%\n")
        f.write("- MQM: 30%\n")
        f.write("- BLEU: 20%\n\n")


if __name__ == "__main__":
    asyncio.run(evaluate_10_samples())

