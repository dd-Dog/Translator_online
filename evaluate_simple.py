"""
简化评估脚本 - 开发模式
只使用BERTScore（轻量级，快速）
"""

import asyncio
import os
import yaml
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def load_evaluation_config(mode: str = "development"):
    """加载评估配置"""
    config_path = Path("config/evaluation.yaml")
    if not config_path.exists():
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config.get('modes', {}).get(mode, {})


def create_scorer(mode: str = "development"):
    """根据模式创建评估器"""
    eval_config = load_evaluation_config(mode)
    if not eval_config:
        print("使用默认配置")
        eval_config = {
            'models': {
                'use_comet': False,
                'use_bleurt': False,
                'use_bertscore': True
            }
        }
    
    models_config = eval_config.get('models', {})
    
    print(f"\n评估模式: {eval_config.get('name', mode)}")
    print(f"说明: {eval_config.get('description', '')}")
    print(f"\n使用的模型:")
    print(f"  BERTScore: {models_config.get('use_bertscore', False)}")
    print(f"  COMET: {models_config.get('use_comet', False)}")
    print(f"  BLEURT: {models_config.get('use_bleurt', False)}")
    print(f"\n预期性能: {eval_config.get('performance', {})}")
    
    from src.evaluation.combined_scorer import CombinedQualityScorer
    
    scorer = CombinedQualityScorer(
        use_comet=models_config.get('use_comet', False),
        use_bleurt=models_config.get('use_bleurt', False),
        use_bertscore=models_config.get('use_bertscore', True),
        comet_model=models_config.get('comet_model', 'Unbabel/wmt22-cometkiwi-da')
    )
    
    return scorer, eval_config


async def quick_test():
    """快速测试评估功能"""
    print("\n" + "=" * 70)
    print("🚀 快速评估测试（开发模式）")
    print("=" * 70)
    
    # 创建评估器
    scorer, config = create_scorer(mode="development")
    
    print("\n初始化评估模型...")
    scorer.initialize()
    
    # 测试数据
    test_cases = [
        {
            "source": "Machine learning is a subset of artificial intelligence.",
            "translation": "机器学习是人工智能的一个子集。",
            "reference": "机器学习是人工智能的一个子集。"
        },
        {
            "source": "The future of AI is promising.",
            "translation": "人工智能的未来充满希望。",
            "reference": "AI的未来很有前景。"
        },
        {
            "source": "Hello, how are you?",
            "translation": "你好，你怎么样？",
            "reference": "你好吗？"
        }
    ]
    
    print(f"\n{'='*70}")
    print("开始评估测试...")
    print(f"{'='*70}")
    
    import time
    start_time = time.time()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/3]")
        print(f"原文: {case['source']}")
        print(f"翻译: {case['translation']}")
        print(f"参考: {case['reference']}")
        
        # 评估
        score = scorer.score(
            source=case['source'],
            translation=case['translation'],
            reference=case['reference'],
            mqm_score={'overall': 0.90}  # 模拟MQM评分
        )
        
        print(f"\n评估结果:")
        print(f"  BLEU: {score.bleu:.4f}")
        if score.bertscore_f1 > 0:
            print(f"  BERTScore F1: {score.bertscore_f1:.4f}")
        if score.comet > 0:
            print(f"  COMET: {score.comet:.4f}")
        print(f"  MQM: {score.mqm_overall:.4f}")
        print(f"  🎯 综合评分: {score.final_score:.4f}")
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*70}")
    print(f"✓ 测试完成")
    print(f"{'='*70}")
    print(f"总耗时: {elapsed:.2f}秒")
    print(f"平均: {elapsed/3:.2f}秒/句")


if __name__ == "__main__":
    asyncio.run(quick_test())

