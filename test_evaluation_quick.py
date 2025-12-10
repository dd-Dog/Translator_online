"""
快速测试评估模块
使用固定文本测试评估功能是否正常（不进行翻译）
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.evaluation_service import create_evaluation_service


def test_evaluation_service():
    """测试评估服务"""
    print("=" * 80)
    print("评估模块快速测试")
    print("=" * 80)
    
    # 测试样本（固定文本，不需要翻译）
    test_samples = [
        {
            "source": "Machine learning is a subset of artificial intelligence.",
            "translation": "机器学习是人工智能的一个子集。",
            "reference": "机器学习是人工智能的一个子集。",
            "description": "完全匹配"
        },
        {
            "source": "The quick brown fox jumps over the lazy dog.",
            "translation": "那只敏捷的棕色狐狸跳过了懒惰的狗。",
            "reference": "敏捷的棕色狐狸跳过懒惰的狗。",
            "description": "部分匹配"
        },
        {
            "source": "Natural language processing enables computers to understand human language.",
            "translation": "自然语言处理使计算机能够理解人类语言。",
            "reference": "自然语言处理使计算机能够理解人类语言。",
            "description": "完全匹配"
        }
    ]
    
    # 创建评估服务
    print("\n[1/3] 初始化评估服务...")
    eval_service = None
    
    # 尝试API模式
    try:
        eval_service = create_evaluation_service(use_api=True)
        if eval_service and eval_service.is_available():
            print("📡 使用API模式")
            print("✅ 评估API服务连接成功")
        else:
            print("📡 尝试API模式...")
            print("⚠️  评估API服务不可用")
            print("   尝试切换到本地模式...")
            eval_service = None
    except Exception as e:
        print(f"⚠️  API模式初始化失败: {e}")
        print("   尝试切换到本地模式...")
        eval_service = None
    
    # 如果API模式不可用，尝试本地模式
    if eval_service is None or not eval_service.is_available():
        try:
            print("\n💻 尝试本地模式...")
            eval_service = create_evaluation_service(use_api=False)
            if eval_service and eval_service.is_available():
                print("✅ 本地评估器初始化成功")
            else:
                print("❌ 本地评估器不可用")
                print("\n请选择以下方式之一:")
                print("  1. 启动评估API服务:")
                print("     conda activate translator_eval")
                print("     python eval_server.py")
                print("  2. 配置本地评估环境:")
                print("     参考 docs/评估器环境配置指南.md")
                return False
        except Exception as e:
            print(f"❌ 本地模式初始化失败: {e}")
            print("\n请选择以下方式之一:")
            print("  1. 启动评估API服务:")
            print("     conda activate translator_eval")
            print("     python eval_server.py")
            print("  2. 配置本地评估环境:")
            print("     参考 docs/评估器环境配置指南.md")
            import traceback
            traceback.print_exc()
            return False
    
    # 测试评估功能
    print("\n[2/3] 测试评估功能...")
    print("-" * 80)
    
    success_count = 0
    fail_count = 0
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n样本 {i}/{len(test_samples)}: {sample['description']}")
        print(f"  原文: {sample['source']}")
        print(f"  翻译: {sample['translation']}")
        print(f"  参考: {sample['reference']}")
        
        try:
            result = eval_service.evaluate(
                translation=sample['translation'],
                reference=sample['reference'],
                source=sample['source']
            )
            
            if result:
                success_count += 1
                print(f"  ✅ 评估成功")
                print(f"     BLEU: {result['bleu']:.4f}")
                if result['comet'] > 0:
                    print(f"     COMET: {result['comet']:.4f}")
                if result['bleurt'] > 0:
                    print(f"     BLEURT: {result['bleurt']:.4f}")
                print(f"     BERTScore: {result['bertscore_f1']:.4f}")
                print(f"     ChrF: {result['chrf']:.4f}")
                print(f"     综合评分: {result['final_score']:.4f}")
            else:
                fail_count += 1
                print(f"  ❌ 评估失败（返回None）")
        except Exception as e:
            fail_count += 1
            print(f"  ❌ 评估异常: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print("\n[3/3] 测试结果总结...")
    print("=" * 80)
    print(f"总样本数: {len(test_samples)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    
    if success_count == len(test_samples):
        print("\n✅ 所有测试通过！评估模块运行正常。")
        return True
    elif success_count > 0:
        print(f"\n⚠️  部分测试通过 ({success_count}/{len(test_samples)})")
        return False
    else:
        print("\n❌ 所有测试失败，请检查评估服务配置。")
        return False


if __name__ == "__main__":
    success = test_evaluation_service()
    sys.exit(0 if success else 1)

