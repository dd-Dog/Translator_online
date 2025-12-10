"""
评估器环境测试脚本
测试评估器环境配置和所有评估模型是否正常工作
不包含翻译功能，仅测试评估器
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional
import yaml

# 添加共享评估库路径
current_file = Path(__file__).resolve()
evaluator_lib = current_file.parent.parent.parent / "translation_evaluator"
if not evaluator_lib.exists():
    evaluator_lib = current_file.parent.parent.parent.parent / "translation_evaluator"

# 使用评估器环境配置工具
import importlib.util
evaluator_env_path = Path(__file__).parent / "src" / "utils" / "evaluator_env.py"
spec = importlib.util.spec_from_file_location("evaluator_env", evaluator_env_path)
evaluator_env_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator_env_module)
setup_evaluator_environment = evaluator_env_module.setup_evaluator_environment

print("=" * 80)
print("评估器环境测试")
print("=" * 80)

# 设置评估器环境
evaluator_python_path, setup_success = setup_evaluator_environment(evaluator_lib)

if not setup_success:
    print("[ERROR] 评估器环境设置失败")
    sys.exit(1)

# 检查当前 Python 是否是指定环境的 Python
if evaluator_python_path:
    current_python = Path(sys.executable).resolve()
    expected_python = evaluator_python_path.resolve()
    
    if current_python != expected_python:
        print(f"\n[WARN] ⚠️  当前 Python 环境不匹配！")
        print(f"  当前 Python: {current_python}")
        print(f"  配置的环境: {expected_python}")
        print(f"\n  请在正确的环境中运行脚本：")
        print(f"  conda activate translator_eval")
        print(f"  或直接使用: {expected_python} {Path(__file__).name}")
        print(f"\n  或者，如果 COMET/BLEURT 已安装在当前环境，可以忽略此警告。")
        print("\n" + "=" * 80)
        
        # 尝试从配置的环境路径导入 COMET 和 BLEURT
        print("\n尝试从配置的环境导入 COMET 和 BLEURT...")
        try:
            # 添加环境的 site-packages 到路径
            if os.name == "nt":  # Windows
                env_root = expected_python.parent.parent
                site_packages = env_root / "Lib" / "site-packages"
            else:  # Linux/Mac
                env_root = expected_python.parent.parent
                import sys
                site_packages = env_root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
            
            if site_packages.exists():
                sys.path.insert(0, str(site_packages))
                print(f"[OK] 已添加环境 site-packages: {site_packages}")
        except Exception as e:
            print(f"[WARN] 无法添加环境路径: {e}")

# 导入评估库
print("\n[1/5] 测试评估库导入...")
try:
    from translation_evaluator import UnifiedEvaluator, PaperGradeScore
    print("[OK] 评估库导入成功")
except ImportError as e:
    print(f"[ERROR] 评估库导入失败: {e}")
    sys.exit(1)

# 测试 COMET 和 BLEURT 是否可用
print("\n检查 COMET 和 BLEURT 是否可用...")
try:
    import comet
    print("[OK] COMET 模块可用")
except ImportError:
    print("[WARN] COMET 模块不可用（可能未安装或不在当前环境）")

try:
    import bleurt
    print("[OK] BLEURT 模块可用")
    # 检查 TensorFlow（BLEURT 的依赖）
    try:
        import tensorflow
        print(f"[OK] TensorFlow 已安装（版本: {tensorflow.__version__}）")
    except ImportError:
        print("[WARN] ⚠️  BLEURT 需要 TensorFlow，但未安装")
        print("       请安装: pip install tensorflow 或 pip install tensorflow-cpu")
except ImportError:
    print("[WARN] BLEURT 模块不可用（可能未安装或不在当前环境）")

# 测试样本（不需要翻译，直接使用示例文本）
print("\n[2/5] 准备测试样本...")
test_samples = [
    {
        'source': "Machine learning is a subset of artificial intelligence.",
        'translation': "机器学习是人工智能的一个子集。",
        'reference': "机器学习是人工智能的一个子集。"
    },
    {
        'source': "The quick brown fox jumps over the lazy dog.",
        'translation': "那只敏捷的棕色狐狸跳过了懒惰的狗。",
        'reference': "敏捷的棕色狐狸跳过懒惰的狗。"
    },
    {
        'source': "Natural language processing enables computers to understand human language.",
        'translation': "自然语言处理使计算机能够理解人类语言。",
        'reference': "自然语言处理使计算机能够理解人类语言。"
    }
]
print(f"[OK] 准备了 {len(test_samples)} 个测试样本")

# 初始化评估器
print("\n[3/5] 初始化评估器（所有模型）...")
try:
    evaluator = UnifiedEvaluator(
        use_bleu=True,
        use_comet=True,
        use_bleurt=True,
        use_bertscore=True,
        use_mqm=True,
        use_chrf=True
    )
    evaluator.initialize()
    print("[OK] 评估器初始化完成")
except Exception as e:
    print(f"[ERROR] 评估器初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 检查各模型状态
print("\n评估器模型状态:")
print(f"  BLEU: {'[启用]' if evaluator.use_bleu else '[禁用]'}")
print(f"  COMET: {'[启用]' if evaluator.use_comet and evaluator.comet_scorer else '[未安装]'}")
print(f"  BLEURT: {'[启用]' if evaluator.use_bleurt and evaluator.bleurt_scorer else '[未安装]'}")
print(f"  BERTScore: {'[启用]' if evaluator.use_bertscore and evaluator.bertscore_scorer else '[禁用]'}")
print(f"  MQM: {'[启用]' if evaluator.use_mqm else '[禁用]'}")
print(f"  ChrF: {'[启用]' if evaluator.use_chrf and evaluator.chrf_scorer else '[禁用]'}")

# 测试评估功能
print("\n[4/5] 测试评估功能...")
print("=" * 80)

results = {
    'bleu': [],
    'comet': [],
    'bleurt': [],
    'bertscore': [],
    'chrf': [],
    'final': []
}

for i, sample in enumerate(test_samples, 1):
    print(f"\n样本 {i}/{len(test_samples)}")
    print(f"  原文: {sample['source']}")
    print(f"  翻译: {sample['translation']}")
    print(f"  参考: {sample['reference']}")
    
    try:
        # 执行评估
        score = evaluator.score(
            source=sample['source'],
            translation=sample['translation'],
            reference=sample['reference'],
            mqm_score=None  # 不提供MQM，使用默认值
        )
        
        # 收集结果
        results['bleu'].append(score.bleu)
        results['comet'].append(score.comet)
        results['bleurt'].append(score.bleurt)
        results['bertscore'].append(score.bertscore_f1)
        results['chrf'].append(score.chrf)
        results['final'].append(score.final_score)
        
        print(f"  [OK] 评估完成")
        print(f"    BLEU: {score.bleu:.4f}")
        if score.comet > 0:
            print(f"    COMET: {score.comet:.4f}")
        if score.bleurt > 0:
            print(f"    BLEURT: {score.bleurt:.4f}")
        print(f"    BERTScore: {score.bertscore_f1:.4f}")
        print(f"    ChrF: {score.chrf:.4f}")
        print(f"    综合评分: {score.final_score:.4f}")
        
    except Exception as e:
        print(f"  [ERROR] 评估失败: {e}")
        import traceback
        traceback.print_exc()

# 计算平均值
print("\n[5/5] 测试结果总结...")
print("=" * 80)

def avg(lst):
    return sum(lst) / len(lst) if lst else 0.0

summary = {
    'total_samples': len(test_samples),
    'successful': len(results['final']),
    'avg_bleu': avg(results['bleu']),
    'avg_comet': avg(results['comet']),
    'avg_bleurt': avg(results['bleurt']),
    'avg_bertscore': avg(results['bertscore']),
    'avg_chrf': avg(results['chrf']),
    'avg_final': avg(results['final'])
}

print(f"\n测试样本数: {summary['total_samples']}")
print(f"成功评估: {summary['successful']}")
print(f"\n平均分数:")
print(f"  BLEU: {summary['avg_bleu']:.4f}")
print(f"  COMET: {summary['avg_comet']:.4f} {'(未安装)' if summary['avg_comet'] == 0 else ''}")
print(f"  BLEURT: {summary['avg_bleurt']:.4f} {'(未安装)' if summary['avg_bleurt'] == 0 else ''}")
print(f"  BERTScore: {summary['avg_bertscore']:.4f}")
print(f"  ChrF: {summary['avg_chrf']:.4f}")
print(f"  综合评分: {summary['avg_final']:.4f}")

# 环境信息
print("\n" + "=" * 80)
print("环境信息")
print("=" * 80)
if evaluator_python_path:
    print(f"评估器 Python 路径: {evaluator_python_path}")
    print(f"评估器环境: {evaluator_python_path.parent.parent.name}")
else:
    print("使用当前 Python 环境")
print(f"当前 Python: {sys.executable}")
print(f"评估库路径: {evaluator_lib}")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)

