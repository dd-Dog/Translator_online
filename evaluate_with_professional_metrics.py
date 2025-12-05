"""
使用专业评估模型进行评估
集成COMET、BLEURT、BERTScore等
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def load_test_data():
    """加载测试数据"""
    with open("test_data/flores_sample.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def create_pipeline():
    """创建翻译pipeline"""
    from src.models.openai import OpenAIModel
    from src.models.gemini import GeminiModel
    from src.models.qwen import QwenModel
    from src.agents.pipeline import TranslationPipeline
    
    # 加载配置
    with open("config/models.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    # 创建模型（简化）
    def create_model(model_type):
        model_cfg = models_config.get(model_type, {})
        api_key = os.getenv(model_cfg.get('api_key_env'))
        model_name = model_cfg.get('model')
        base_url = model_cfg.get('base_url')
        use_openrouter = model_cfg.get('use_openrouter', False)
        params = model_cfg.get('params', {})
        
        if model_type == 'openai':
            return OpenAIModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'gemini':
            return GeminiModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'qwen':
            return QwenModel(model_name, api_key, base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1", **params)
    
    planner = create_model('openai')
    translator_a = create_model('gemini')
    translator_b = create_model('qwen')
    checker = create_model('openai')
    stylist = create_model('qwen')
    aggregator = create_model('openai')
    
    return TranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        style="general"
    )


async def evaluate_with_pro_metrics():
    """使用专业评估模型评估"""
    print("\n" + "=" * 70)
    print("🎓 专业评估模型评估")
    print("=" * 70)
    
    # 初始化专业评估模型
    from src.evaluation.combined_scorer import CombinedQualityScorer
    
    scorer = CombinedQualityScorer(
        use_comet=True,
        use_bleurt=False,  # BLEURT安装复杂，默认关闭
        use_bertscore=True
    )
    
    print("\n初始化专业评估模型...")
    scorer.initialize()
    
    # 加载测试数据
    test_data = load_test_data()
    print(f"\n✓ 加载测试数据: {len(test_data)} 条")
    
    # 创建翻译pipeline
    print("\n创建翻译系统...")
    pipeline = create_pipeline()
    print("✓ 翻译系统创建成功")
    
    # 评估
    results = []
    
    for i, item in enumerate(test_data[:5]):  # 先测试5条
        print(f"\n{'='*70}")
        print(f"[{i+1}/5] 评估中...")
        print(f"{'='*70}")
        
        source = item['source']
        reference = item['reference']
        
        print(f"原文: {source}")
        print(f"参考: {reference}")
        
        try:
            # 翻译
            print("\n正在翻译...")
            result = await pipeline.translate(source, source_lang="en", target_lang="zh")
            translation = result.translated_text
            
            print(f"翻译: {translation}")
            
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
            print("\n正在使用专业模型评估...")
            comprehensive_score = scorer.score(
                source=source,
                translation=translation,
                reference=reference,
                mqm_score=mqm_score
            )
            
            print(f"\n📊 评估结果:")
            print(f"  BLEU: {comprehensive_score.bleu:.4f}")
            if comprehensive_score.comet > 0:
                print(f"  COMET: {comprehensive_score.comet:.4f}")
            if comprehensive_score.bertscore_f1 > 0:
                print(f"  BERTScore F1: {comprehensive_score.bertscore_f1:.4f}")
            if comprehensive_score.bleurt > 0:
                print(f"  BLEURT: {comprehensive_score.bleurt:.4f}")
            print(f"  MQM Overall: {comprehensive_score.mqm_overall:.4f}")
            print(f"  🎯 综合评分: {comprehensive_score.final_score:.4f}")
            
            results.append({
                'id': item['id'],
                'source': source,
                'reference': reference,
                'translation': translation,
                'scores': {
                    'bleu': comprehensive_score.bleu,
                    'comet': comprehensive_score.comet,
                    'bertscore_f1': comprehensive_score.bertscore_f1,
                    'bleurt': comprehensive_score.bleurt,
                    'mqm_overall': comprehensive_score.mqm_overall,
                    'final_score': comprehensive_score.final_score
                }
            })
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    # 生成报告
    print("\n" + "=" * 70)
    print("📊 评估总结")
    print("=" * 70)
    
    if results:
        avg_bleu = sum(r['scores']['bleu'] for r in results) / len(results)
        avg_comet = sum(r['scores']['comet'] for r in results if r['scores']['comet'] > 0) / len([r for r in results if r['scores']['comet'] > 0]) if any(r['scores']['comet'] > 0 for r in results) else 0
        avg_bertscore = sum(r['scores']['bertscore_f1'] for r in results if r['scores']['bertscore_f1'] > 0) / len([r for r in results if r['scores']['bertscore_f1'] > 0]) if any(r['scores']['bertscore_f1'] > 0 for r in results) else 0
        avg_mqm = sum(r['scores']['mqm_overall'] for r in results) / len(results)
        avg_final = sum(r['scores']['final_score'] for r in results) / len(results)
        
        print(f"\n平均分数:")
        print(f"  BLEU: {avg_bleu:.4f}")
        if avg_comet > 0:
            print(f"  COMET: {avg_comet:.4f}")
        if avg_bertscore > 0:
            print(f"  BERTScore F1: {avg_bertscore:.4f}")
        print(f"  MQM Overall: {avg_mqm:.4f}")
        print(f"  🎯 综合评分: {avg_final:.4f}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"professional_evaluation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_samples': len(results),
                    'models_used': {
                        'comet': scorer.use_comet,
                        'bleurt': scorer.use_bleurt,
                        'bertscore': scorer.use_bertscore
                    }
                },
                'summary': {
                    'avg_bleu': avg_bleu,
                    'avg_comet': avg_comet,
                    'avg_bertscore': avg_bertscore,
                    'avg_mqm': avg_mqm,
                    'avg_final': avg_final
                },
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 详细结果已保存到: {filename}")


if __name__ == "__main__":
    asyncio.run(evaluate_with_pro_metrics())

