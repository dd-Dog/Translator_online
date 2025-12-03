"""
基线评估 - 在测试数据集上评估翻译系统
生成详细的评估报告
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

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
    """计算BLEU分数（字符级）"""
    # 简化版BLEU：基于字符匹配
    ref_chars = set(reference)
    cand_chars = set(candidate)
    
    # 计算精确率
    if not cand_chars:
        return 0.0
    
    precision = len(ref_chars & cand_chars) / len(cand_chars)
    
    # 计算召回率
    if not ref_chars:
        return 0.0
    
    recall = len(ref_chars & cand_chars) / len(ref_chars)
    
    # F1分数
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def calculate_char_error_rate(candidate: str, reference: str) -> float:
    """计算字符错误率（CER）"""
    # 简化版：基于长度差异
    len_diff = abs(len(candidate) - len(reference))
    max_len = max(len(candidate), len(reference))
    
    if max_len == 0:
        return 0.0
    
    return len_diff / max_len


async def evaluate_on_testset(pipeline, test_data: list):
    """在测试集上评估"""
    print("=" * 70)
    print("开始评估")
    print("=" * 70)
    
    results = []
    total = len(test_data)
    
    for i, item in enumerate(test_data):
        print(f"\n{'='*70}")
        print(f"[{i+1}/{total}] 评估中...")
        print(f"{'='*70}")
        
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
            
            # 计算指标
            bleu = calculate_bleu(translation, reference)
            cer = calculate_char_error_rate(translation, reference)
            
            # 获取系统评分
            system_score = None
            if result.explainability_report.final_quality_score:
                score = result.explainability_report.final_quality_score
                system_score = {
                    'adequacy': score.adequacy,
                    'fluency': score.fluency,
                    'terminology': score.terminology,
                    'overall': score.overall
                }
            
            print(f"\n评估指标:")
            print(f"  BLEU: {bleu:.4f}")
            print(f"  CER: {cer:.4f}")
            if system_score:
                print(f"  系统评分: {system_score['overall']:.2f}")
                print(f"    - 充分性: {system_score['adequacy']:.2f}")
                print(f"    - 流畅性: {system_score['fluency']:.2f}")
                print(f"    - 术语: {system_score['terminology']:.2f}")
            
            results.append({
                'id': item['id'],
                'domain': domain,
                'source': source,
                'reference': reference,
                'translation': translation,
                'bleu': bleu,
                'cer': cer,
                'system_score': system_score,
                'processing_stages': result.processing_stages
            })
            
        except Exception as e:
            print(f"\n❌ 翻译失败: {e}")
            results.append({
                'id': item['id'],
                'domain': domain,
                'source': source,
                'reference': reference,
                'translation': None,
                'error': str(e)
            })
    
    return results


def generate_evaluation_report(results, output_file: str = None):
    """生成详细的评估报告"""
    if not results:
        print("没有结果可分析")
        return
    
    print("\n" + "=" * 70)
    print("📊 详细评估报告")
    print("=" * 70)
    
    # 过滤有效结果
    valid_results = [r for r in results if r.get('translation')]
    failed_results = [r for r in results if not r.get('translation')]
    
    print(f"\n【总体统计】")
    print(f"  总样本数: {len(results)}")
    print(f"  成功翻译: {len(valid_results)}")
    print(f"  失败数: {len(failed_results)}")
    print(f"  成功率: {len(valid_results)/len(results)*100:.1f}%")
    
    if not valid_results:
        print("\n没有有效结果")
        return
    
    # BLEU统计
    bleu_scores = [r['bleu'] for r in valid_results]
    print(f"\n【BLEU分数统计】")
    print(f"  平均值: {sum(bleu_scores)/len(bleu_scores):.4f}")
    print(f"  最大值: {max(bleu_scores):.4f}")
    print(f"  最小值: {min(bleu_scores):.4f}")
    print(f"  中位数: {sorted(bleu_scores)[len(bleu_scores)//2]:.4f}")
    
    # CER统计
    cer_scores = [r['cer'] for r in valid_results]
    print(f"\n【字符错误率（CER）统计】")
    print(f"  平均值: {sum(cer_scores)/len(cer_scores):.4f}")
    print(f"  最大值: {max(cer_scores):.4f}")
    print(f"  最小值: {min(cer_scores):.4f}")
    
    # 系统评分统计
    system_scores = [r['system_score']['overall'] for r in valid_results if r.get('system_score')]
    if system_scores:
        print(f"\n【系统MQM评分统计】")
        print(f"  平均值: {sum(system_scores)/len(system_scores):.4f}")
        print(f"  最大值: {max(system_scores):.4f}")
        print(f"  最小值: {min(system_scores):.4f}")
        print(f"  中位数: {sorted(system_scores)[len(system_scores)//2]:.4f}")
        
        # 各维度统计
        adequacy_scores = [r['system_score']['adequacy'] for r in valid_results if r.get('system_score')]
        fluency_scores = [r['system_score']['fluency'] for r in valid_results if r.get('system_score')]
        terminology_scores = [r['system_score']['terminology'] for r in valid_results if r.get('system_score')]
        
        print(f"\n  各维度平均分:")
        print(f"    充分性: {sum(adequacy_scores)/len(adequacy_scores):.4f}")
        print(f"    流畅性: {sum(fluency_scores)/len(fluency_scores):.4f}")
        print(f"    术语准确性: {sum(terminology_scores)/len(terminology_scores):.4f}")
    
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
            domain_bleu = [r['bleu'] for r in items]
            domain_system = [r['system_score']['overall'] for r in items if r.get('system_score')]
            print(f"\n  {domain} ({len(items)}条):")
            print(f"    平均BLEU: {sum(domain_bleu)/len(domain_bleu):.4f}")
            if domain_system:
                print(f"    平均系统评分: {sum(domain_system)/len(domain_system):.4f}")
    
    # 相关性分析
    if system_scores and len(system_scores) == len(bleu_scores):
        try:
            # 简单相关性计算
            mean_bleu = sum(bleu_scores) / len(bleu_scores)
            mean_system = sum(system_scores) / len(system_scores)
            
            numerator = sum((b - mean_bleu) * (s - mean_system) 
                          for b, s in zip(bleu_scores, system_scores))
            
            denom_bleu = sum((b - mean_bleu) ** 2 for b in bleu_scores) ** 0.5
            denom_system = sum((s - mean_system) ** 2 for s in system_scores) ** 0.5
            
            if denom_bleu > 0 and denom_system > 0:
                correlation = numerator / (denom_bleu * denom_system)
                
                print(f"\n【相关性分析】")
                print(f"  BLEU与系统评分的相关系数: {correlation:.4f}")
                if correlation > 0.7:
                    print(f"  相关性: 强相关 ✓")
                elif correlation > 0.4:
                    print(f"  相关性: 中等相关")
                else:
                    print(f"  相关性: 弱相关 ⚠️")
        except:
            pass
    
    # 最佳和最差案例
    print(f"\n【最佳翻译案例】（BLEU最高）")
    best = max(valid_results, key=lambda x: x['bleu'])
    print(f"  原文: {best['source']}")
    print(f"  参考: {best['reference']}")
    print(f"  翻译: {best['translation']}")
    print(f"  BLEU: {best['bleu']:.4f}")
    
    print(f"\n【最差翻译案例】（BLEU最低）")
    worst = min(valid_results, key=lambda x: x['bleu'])
    print(f"  原文: {worst['source']}")
    print(f"  参考: {worst['reference']}")
    print(f"  翻译: {worst['translation']}")
    print(f"  BLEU: {worst['bleu']:.4f}")
    
    # 保存详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_file:
        output_file = f"evaluation_report_{timestamp}.json"
    
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_samples': len(results),
            'successful': len(valid_results),
            'failed': len(failed_results)
        },
        'summary': {
            'avg_bleu': sum(bleu_scores)/len(bleu_scores) if bleu_scores else 0,
            'avg_cer': sum(cer_scores)/len(cer_scores) if cer_scores else 0,
            'avg_system_score': sum(system_scores)/len(system_scores) if system_scores else 0,
        },
        'by_domain': {},
        'details': results
    }
    
    # 按领域统计
    for domain, items in domains.items():
        domain_bleu = [r['bleu'] for r in items]
        domain_system = [r['system_score']['overall'] for r in items if r.get('system_score')]
        report['by_domain'][domain] = {
            'count': len(items),
            'avg_bleu': sum(domain_bleu)/len(domain_bleu) if domain_bleu else 0,
            'avg_system_score': sum(domain_system)/len(domain_system) if domain_system else 0
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ 详细评估报告已保存到: {output_file}")
    print(f"{'='*70}")
    
    # 生成Markdown报告
    md_file = output_file.replace('.json', '.md')
    generate_markdown_report(report, md_file)
    print(f"✓ Markdown报告已保存到: {md_file}")


def generate_markdown_report(report, output_file):
    """生成Markdown格式的报告"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 翻译系统评估报告\n\n")
        f.write(f"**评估时间**: {report['metadata']['timestamp']}\n\n")
        
        f.write("## 总体统计\n\n")
        f.write(f"- 总样本数: {report['metadata']['total_samples']}\n")
        f.write(f"- 成功翻译: {report['metadata']['successful']}\n")
        f.write(f"- 失败数: {report['metadata']['failed']}\n")
        f.write(f"- 成功率: {report['metadata']['successful']/report['metadata']['total_samples']*100:.1f}%\n\n")
        
        f.write("## 评估指标\n\n")
        f.write(f"- 平均BLEU: {report['summary']['avg_bleu']:.4f}\n")
        f.write(f"- 平均CER: {report['summary']['avg_cer']:.4f}\n")
        f.write(f"- 平均系统评分: {report['summary']['avg_system_score']:.4f}\n\n")
        
        if report['by_domain']:
            f.write("## 按领域统计\n\n")
            for domain, stats in report['by_domain'].items():
                f.write(f"### {domain}\n\n")
                f.write(f"- 样本数: {stats['count']}\n")
                f.write(f"- 平均BLEU: {stats['avg_bleu']:.4f}\n")
                f.write(f"- 平均系统评分: {stats['avg_system_score']:.4f}\n\n")
        
        f.write("## 详细结果\n\n")
        f.write("| ID | 领域 | BLEU | 系统评分 | 原文 | 翻译 |\n")
        f.write("|---|---|---|---|---|---|\n")
        
        for r in report['details']:
            if r.get('translation'):
                bleu = r['bleu']
                score = r['system_score']['overall'] if r.get('system_score') else 0
                source_short = r['source'][:30] + '...' if len(r['source']) > 30 else r['source']
                trans_short = r['translation'][:30] + '...' if len(r['translation']) > 30 else r['translation']
                f.write(f"| {r['id']} | {r['domain']} | {bleu:.3f} | {score:.2f} | {source_short} | {trans_short} |\n")


async def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("翻译系统基线评估")
    print("=" * 70)
    
    # 加载测试数据
    test_data_path = Path("test_data/flores_sample.json")
    if not test_data_path.exists():
        print(f"❌ 测试数据文件不存在: {test_data_path}")
        return
    
    with open(test_data_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    print(f"\n✓ 加载测试数据: {len(test_data)} 条")
    
    # 加载配置并创建工作流
    config = load_config()
    if not config:
        print("❌ 无法加载配置文件")
        return
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    style_config = config.get('style', {})
    
    print("\n🔧 创建模型...")
    
    # 创建模型
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
    
    # 评估
    results = await evaluate_on_testset(pipeline, test_data)
    
    # 生成报告
    generate_evaluation_report(results)


if __name__ == "__main__":
    asyncio.run(main())

