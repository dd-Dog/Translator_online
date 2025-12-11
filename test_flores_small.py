"""
FLORES数据集小规模测试脚本
测试翻译和评估流程是否正常
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import yaml
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.pipeline import TranslationPipeline
from src.models.openai import OpenAIModel
from src.models.gemini import GeminiModel
from src.models.qwen import QwenModel
from src.models.deepseek import DeepSeekModel
from src.utils.evaluation_service import create_evaluation_service

load_dotenv()

# FLORES语言代码映射
FLORES_LANG_MAP = {
    "en": "eng_Latn",
    "de": "deu_Latn",
    "vi": "vie_Latn",
    "km": "khm_Khmr",
    "ms": "zsm_Latn",
    "zh": "zho_Hans"
}

# 语言名称映射
LANG_NAMES = {
    "en": "英语",
    "de": "德语",
    "vi": "越南语",
    "km": "柬埔寨语",
    "ms": "马来语",
    "zh": "中文"
}


def load_flores_data(lang_code: str, dataset_type: str = "dev", max_samples: int = 5) -> List[str]:
    """加载少量FLORES数据用于测试"""
    flores_code = FLORES_LANG_MAP.get(lang_code)
    if not flores_code:
        raise ValueError(f"不支持的语言代码: {lang_code}")
    
    data_dir = Path(__file__).parent / "datasets" / "flores200_dataset" / dataset_type
    file_path = data_dir / f"{flores_code}.{dataset_type}"
    
    if not file_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    
    texts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_samples:
                break
            line = line.strip()
            if line:
                texts.append(line)
    
    return texts


def create_pipeline(model_config: Optional[Dict] = None) -> TranslationPipeline:
    """创建翻译Pipeline"""
    config_path = Path(__file__).parent / "config" / "models.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    if model_config:
        planner_type = model_config.get('planner', workflow_config.get('planner', {}).get('model', 'deepseek'))
        translator_a_type = model_config.get('translator_a', workflow_config.get('translator_a', {}).get('model', 'deepseek'))
        translator_b_type = model_config.get('translator_b', workflow_config.get('translator_b', {}).get('model', 'qwen'))
        checker_type = model_config.get('checker', workflow_config.get('checker', {}).get('model', 'deepseek'))
        stylist_type = model_config.get('stylist', workflow_config.get('stylist', {}).get('model', 'qwen'))
        aggregator_type = model_config.get('aggregator', workflow_config.get('aggregator', {}).get('model', 'deepseek'))
    else:
        # 处理workflow配置可能是字典或字符串的情况
        planner_cfg = workflow_config.get('planner', {})
        planner_type = planner_cfg.get('model', 'deepseek') if isinstance(planner_cfg, dict) else planner_cfg or 'deepseek'
        
        translator_a_cfg = workflow_config.get('translator_a', {})
        translator_a_type = translator_a_cfg.get('model', 'deepseek') if isinstance(translator_a_cfg, dict) else translator_a_cfg or 'deepseek'
        
        translator_b_cfg = workflow_config.get('translator_b', {})
        translator_b_type = translator_b_cfg.get('model', 'qwen') if isinstance(translator_b_cfg, dict) else translator_b_cfg or 'qwen'
        
        checker_cfg = workflow_config.get('checker', {})
        checker_type = checker_cfg.get('model', 'deepseek') if isinstance(checker_cfg, dict) else checker_cfg or 'deepseek'
        
        stylist_cfg = workflow_config.get('stylist', {})
        stylist_type = stylist_cfg.get('model', 'qwen') if isinstance(stylist_cfg, dict) else stylist_cfg or 'qwen'
        
        aggregator_cfg = workflow_config.get('aggregator', {})
        aggregator_type = aggregator_cfg.get('model', 'deepseek') if isinstance(aggregator_cfg, dict) else aggregator_cfg or 'deepseek'
    
    def create_model(model_type):
        model_cfg = models_config.get(model_type, {})
        if not model_cfg.get('enabled', False):
            print(f"  ❌ 模型 {model_type} 未启用")
            return None
        
        api_key_env = model_cfg.get('api_key_env')
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not api_key:
            print(f"  ❌ 未找到 {model_type} API密钥（环境变量: {api_key_env}）")
            return None
        
        model_name = model_cfg.get('model')
        params = model_cfg.get('params', {})
        base_url = model_cfg.get('base_url')
        use_openrouter = model_cfg.get('use_openrouter', False)
        
        if model_type == 'openai':
            return OpenAIModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type == 'gemini':
            return GeminiModel(model_name, api_key, base_url, use_openrouter, **params)
        elif model_type in ['qwen', 'qwen_plus']:
            return QwenModel(model_name, api_key, base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1", **params)
        elif model_type in ['deepseek', 'deepseek_v3']:
            return DeepSeekModel(model_name, api_key, base_url or "https://api.deepseek.com", **params)
        return None
    
    print(f"\n📋 模型配置:")
    print(f"  Planner: {planner_type}")
    print(f"  Translator-A: {translator_a_type}")
    print(f"  Translator-B: {translator_b_type}")
    print(f"  Checker: {checker_type}")
    print(f"  Stylist: {stylist_type}")
    print(f"  Aggregator: {aggregator_type}")
    print(f"\n🔧 初始化模型...")
    
    planner = create_model(planner_type)
    translator_a = create_model(translator_a_type)
    translator_b = create_model(translator_b_type)
    checker = create_model(checker_type)
    stylist = create_model(stylist_type)
    aggregator = create_model(aggregator_type)
    
    if not all([planner, translator_a, translator_b, checker, stylist, aggregator]):
        raise ValueError("部分模型创建失败，请检查配置和API密钥")
    
    print(f"  ✅ 所有模型初始化成功")
    
    return TranslationPipeline(
        planner_model=planner,
        translator_a_model=translator_a,
        translator_b_model=translator_b,
        checker_model=checker,
        stylist_model=stylist,
        aggregator_model=aggregator,
        glossary={},
        style='general'
    )


async def test_single_sample(
    pipeline: TranslationPipeline,
    eval_service,
    source_text: str,
    reference: str,
    source_lang: str,
    index: int
) -> Dict:
    """测试单个样本的翻译和评估"""
    print(f"\n{'='*80}")
    print(f"样本 {index + 1}")
    print(f"{'='*80}")
    print(f"原文 ({LANG_NAMES.get(source_lang, source_lang)}): {source_text[:200]}{'...' if len(source_text) > 200 else ''}")
    print(f"参考翻译: {reference[:200]}{'...' if len(reference) > 200 else ''}")
    
    result = {
        "index": index,
        "source": source_text,
        "reference": reference,
        "translation": None,
        "mqm_score": None,
        "evaluation": None,
        "error": None
    }
    
    # 步骤1: 翻译
    print(f"\n[1/2] 执行翻译...")
    try:
        translation_result = await pipeline.translate(
            text=source_text,
            source_lang=source_lang,
            target_lang="zh"
        )
        
        result["translation"] = translation_result.translated_text
        print(f"✅ 翻译完成")
        print(f"翻译结果: {translation_result.translated_text[:200]}{'...' if len(translation_result.translated_text) > 200 else ''}")
        
        # 提取MQM评分
        if translation_result.explainability_report and translation_result.explainability_report.final_quality_score:
            qs = translation_result.explainability_report.final_quality_score
            result["mqm_score"] = {
                "adequacy": qs.adequacy,
                "fluency": qs.fluency,
                "terminology": qs.terminology,
                "overall": qs.overall
            }
            print(f"MQM评分: {qs.overall:.4f} (adequacy: {qs.adequacy:.4f}, fluency: {qs.fluency:.4f}, terminology: {qs.terminology:.4f})")
        
    except Exception as e:
        result["error"] = f"翻译失败: {str(e)}"
        print(f"❌ 翻译失败: {e}")
        import traceback
        traceback.print_exc()
        return result
    
    # 步骤2: 评估
    print(f"\n[2/2] 执行评估...")
    try:
        eval_result = eval_service.evaluate(
            translation=result["translation"],
            reference=reference,
            source=source_text,
            mqm_score=result.get("mqm_score")
        )
        
        if eval_result:
            result["evaluation"] = eval_result
            print(f"✅ 评估完成")
            print(f"评估结果:")
            print(f"  BLEU: {eval_result.get('bleu', 0):.4f}")
            if eval_result.get('comet', 0) > 0:
                print(f"  COMET: {eval_result.get('comet', 0):.4f}")
            if eval_result.get('bleurt', 0) > 0:
                print(f"  BLEURT: {eval_result.get('bleurt', 0):.4f}")
            print(f"  BERTScore: {eval_result.get('bertscore_f1', 0):.4f}")
            print(f"  ChrF: {eval_result.get('chrf', 0):.4f}")
            print(f"  综合评分: {eval_result.get('final_score', 0):.4f}")
        else:
            result["error"] = "评估失败（返回None）"
            print(f"❌ 评估失败（返回None）")
    except Exception as e:
        result["error"] = f"评估失败: {str(e)}"
        print(f"❌ 评估失败: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def main():
    """主函数"""
    print("=" * 80)
    print("FLORES数据集小规模测试")
    print("=" * 80)
    
    # 配置参数
    TEST_LANG = "en"  # 测试语言（英语）
    TEST_SAMPLES = 3  # 测试样本数（少量测试）
    DATASET_TYPE = "dev"
    
    lang_name = LANG_NAMES.get(TEST_LANG, TEST_LANG)
    print(f"\n测试配置:")
    print(f"  语言: {lang_name} ({TEST_LANG})")
    print(f"  样本数: {TEST_SAMPLES}")
    print(f"  数据集: {DATASET_TYPE}")
    
    # 步骤1: 初始化评估服务
    print(f"\n[步骤1/4] 初始化评估服务...")
    try:
        eval_service = create_evaluation_service()
        if not eval_service or not eval_service.is_available():
            print("❌ 评估服务不可用")
            print("   请确保评估API服务已启动，或检查本地评估环境配置")
            return
        print("✅ 评估服务已就绪")
        if eval_service.use_api:
            print("   📡 使用API模式")
        else:
            print("   💻 使用本地模式")
    except Exception as e:
        print(f"❌ 评估服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤2: 创建翻译Pipeline
    print(f"\n[步骤2/4] 创建翻译Pipeline...")
    try:
        pipeline = create_pipeline()
        print("✅ 翻译Pipeline已就绪")
    except Exception as e:
        print(f"❌ 翻译Pipeline初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤3: 加载测试数据
    print(f"\n[步骤3/4] 加载测试数据...")
    try:
        sources = load_flores_data(TEST_LANG, DATASET_TYPE, TEST_SAMPLES)
        references = load_flores_data("zh", DATASET_TYPE, TEST_SAMPLES)
        
        if len(sources) != len(references):
            print(f"⚠️  源文本和参考翻译数量不匹配: {len(sources)} vs {len(references)}")
            min_len = min(len(sources), len(references))
            sources = sources[:min_len]
            references = references[:min_len]
        
        print(f"✅ 已加载 {len(sources)} 条样本")
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤4: 测试翻译和评估
    print(f"\n[步骤4/4] 开始测试翻译和评估...")
    results = []
    
    for i, (source, reference) in enumerate(zip(sources, references)):
        result = await test_single_sample(
            pipeline,
            eval_service,
            source,
            reference,
            TEST_LANG,
            i
        )
        results.append(result)
        
        # 样本间短暂休息
        if i < len(sources) - 1:
            print(f"\n等待 1 秒后继续下一个样本...")
            await asyncio.sleep(1)
    
    # 总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r.get("evaluation") is not None)
    failed = len(results) - successful
    
    print(f"总样本数: {len(results)}")
    print(f"成功: {successful}")
    print(f"失败: {failed}")
    
    if successful > 0:
        scores = [r["evaluation"]["final_score"] for r in results if r.get("evaluation")]
        avg_score = sum(scores) / len(scores)
        print(f"\n平均综合评分: {avg_score:.4f}")
        
        # 各指标平均分
        metrics = ["bleu", "comet", "bleurt", "bertscore_f1", "chrf"]
        print(f"\n各指标平均分:")
        for metric in metrics:
            metric_scores = [r["evaluation"].get(metric, 0) for r in results 
                           if r.get("evaluation") and r["evaluation"].get(metric, 0) > 0]
            if metric_scores:
                avg_metric = sum(metric_scores) / len(metric_scores)
                print(f"  {metric.upper()}: {avg_metric:.4f}")
    
    # 检查是否有错误
    errors = [r for r in results if r.get("error")]
    if errors:
        print(f"\n⚠️  发现 {len(errors)} 个错误:")
        for r in errors:
            print(f"  样本 {r['index'] + 1}: {r['error']}")
    else:
        print(f"\n✅ 所有测试通过！流程正常。")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())

