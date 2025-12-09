"""
V2专业评估 - 带详细日志（修复编码版本）
直接将日志写入UTF-8文件，避免控制台编码问题
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import statistics
import sys
import io

# 修复Windows控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()


class LogWriter:
    """日志写入器，确保UTF-8编码"""
    def __init__(self, file_path: str):
        self.file = open(file_path, 'w', encoding='utf-8', errors='replace')
        self.console = sys.stdout
    
    def write(self, text: str):
        """同时写入文件和控制台"""
        self.file.write(text)
        self.file.flush()
        # 控制台输出（简化，避免编码问题）
        if not text.startswith('\x1b'):  # 跳过ANSI颜色码
            try:
                self.console.write(text)
            except:
                pass
    
    def flush(self):
        self.file.flush()
        self.console.flush()
    
    def close(self):
        self.file.close()


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


async def evaluate_10_samples_verbose_fixed():
    """带详细日志的10条样本评估（修复编码版本）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"V2_evaluation_verbose_log_{timestamp}.txt"
    
    # 创建日志写入器
    log = LogWriter(log_file)
    
    # 保存原始print
    import builtins
    original_print = builtins.print
    
    # 重定向print到日志写入器
    def log_print(*args, **kwargs):
        output = ' '.join(str(arg) for arg in args)
        if kwargs.get('end', '\n') == '\n':
            output += '\n'
        log.write(output)
    
    builtins.print = log_print
    
    print("=" * 80)
    print("V2专业评估系统 - 详细日志模式（UTF-8编码）")
    print("=" * 80)
    
    # 初始化专业评估模型（开发模式）
    from src.evaluation.combined_scorer import CombinedQualityScorer
    
    print("\n【1/3】初始化专业评估模型（开发模式）")
    print("-" * 80)
    scorer = CombinedQualityScorer(
        use_comet=False,      # 开发模式：不使用COMET
        use_bleurt=False,     # 开发模式：不使用BLEURT
        use_bertscore=True    # 开发模式：使用BERTScore
    )
    print("正在初始化BERTScore...")
    scorer.initialize()
    print("✓ BERTScore已就绪")
    
    # 加载测试数据
    print("\n【2/3】加载测试数据")
    print("-" * 80)
    test_data = load_test_data()
    test_samples = test_data[:10]  # 取前10条
    print(f"✓ 加载 {len(test_samples)} 条测试样本")
    
    # 创建翻译pipeline（使用verbose版本）
    print("\n【3/3】创建翻译系统")
    print("-" * 80)
    config = load_config()
    if not config:
        print("❌ 无法加载配置文件")
        log.close()
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
        log.close()
        return
    
    # 使用verbose版本的pipeline
    from src.agents.pipeline_verbose import VerboseTranslationPipeline
    
    pipeline = VerboseTranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        glossary=style_config.get('glossary', {}),
        style=style_config.get('default', 'general')
    )
    print("✓ 翻译系统创建成功（详细日志模式）")
    
    # 开始评估
    print("\n" + "=" * 80)
    print("开始评估（详细日志模式）")
    print("=" * 80)
    
    results = []
    import time
    start_time = time.time()
    
    for i, item in enumerate(test_samples, 1):
        print("\n" + "=" * 80)
        print(f"[{i}/10] 评估样本 {item['id']}")
        print("=" * 80)
        
        source = item['source']
        reference = item['reference']
        domain = item.get('domain', 'general')
        
        print(f"\n样本信息:")
        print(f"  领域: {domain}")
        print(f"  原文: {source}")
        print(f"  参考翻译: {reference}")
        
        try:
            # 翻译（verbose模式会自动打印详细过程）
            print("\n" + "-" * 80)
            print("翻译过程")
            print("-" * 80)
            result = await pipeline.translate(
                text=source,
                source_lang=item.get('source_lang', 'auto'),
                target_lang=item.get('target_lang', 'zh')
            )
            
            translation = result.translated_text
            print(f"\n✓ 最终翻译: {translation}")
            
            # 获取MQM评分详情
            print("\n" + "-" * 80)
            print("MQM评分详情")
            print("-" * 80)
            mqm_score = None
            if result.explainability_report.final_quality_score:
                score = result.explainability_report.final_quality_score
                mqm_score = {
                    'adequacy': score.adequacy,
                    'fluency': score.fluency,
                    'terminology': score.terminology,
                    'overall': score.overall
                }
                print(f"  充分性 (Adequacy): {score.adequacy:.4f}")
                print(f"  流畅性 (Fluency): {score.fluency:.4f}")
                print(f"  术语准确性 (Terminology): {score.terminology:.4f}")
                print(f"  总体评分 (Overall): {score.overall:.4f}")
            
            # 专业评估（详细过程）
            print("\n" + "-" * 80)
            print("专业评估过程（BERTScore）")
            print("-" * 80)
            print("  正在计算BLEU分数...")
            print("  正在计算BERTScore F1...")
            print("  正在整合MQM评分...")
            print("  正在计算综合评分...")
            
            comprehensive_score = scorer.score(
                source=source,
                translation=translation,
                reference=reference,
                mqm_score=mqm_score
            )
            
            print("\n" + "-" * 80)
            print("评估结果汇总")
            print("-" * 80)
            print(f"  BLEU分数: {comprehensive_score.bleu:.4f}")
            if comprehensive_score.bertscore_f1 > 0:
                print(f"  BERTScore F1: {comprehensive_score.bertscore_f1:.4f}")
                print(f"    - 说明: 语义相似度评分，值越高表示语义越接近")
            print(f"  MQM总体评分: {comprehensive_score.mqm_overall:.4f}")
            
            # 计算综合评分的详细过程
            print(f"\n  综合评分计算过程:")
            print(f"    开发模式权重分配:")
            print(f"      - BERTScore: 50%")
            print(f"      - MQM: 30%")
            print(f"      - BLEU: 20%")
            
            bertscore_weight = 0.50
            mqm_weight = 0.30
            bleu_weight = 0.20
            
            if comprehensive_score.bertscore_f1 > 0:
                bertscore_contribution = comprehensive_score.bertscore_f1 * bertscore_weight
                print(f"    BERTScore贡献: {comprehensive_score.bertscore_f1:.4f} × {bertscore_weight:.0%} = {bertscore_contribution:.4f}")
            
            mqm_contribution = comprehensive_score.mqm_overall * mqm_weight
            print(f"    MQM贡献: {comprehensive_score.mqm_overall:.4f} × {mqm_weight:.0%} = {mqm_contribution:.4f}")
            
            bleu_contribution = comprehensive_score.bleu * bleu_weight
            print(f"    BLEU贡献: {comprehensive_score.bleu:.4f} × {bleu_weight:.0%} = {bleu_contribution:.4f}")
            
            print(f"    " + "-" * 60)
            final_calc = (comprehensive_score.bertscore_f1 * bertscore_weight if comprehensive_score.bertscore_f1 > 0 else 0) + \
                        mqm_contribution + bleu_contribution
            total_weight = (bertscore_weight if comprehensive_score.bertscore_f1 > 0 else 0) + mqm_weight + bleu_weight
            if total_weight < 1.0:
                final_calc = final_calc / total_weight
            print(f"    综合评分 = {final_calc:.4f}")
            print(f"    (实际系统计算: {comprehensive_score.final_score:.4f})")
            
            print(f"\n  ✓ 最终综合评分: {comprehensive_score.final_score:.4f}")
            
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
        
        print(f"\n{'='*80}\n")
    
    elapsed_time = time.time() - start_time
    
    # 生成总结
    print("=" * 80)
    print("评估总结")
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
    
    if valid_results:
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
    
    # 恢复原始print
    builtins.print = original_print
    
    log.close()
    
    print(f"\n{'='*80}")
    print(f"✓ 详细日志已保存到: {log_file}")
    print(f"✓ 文件编码: UTF-8")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(evaluate_10_samples_verbose_fixed())

