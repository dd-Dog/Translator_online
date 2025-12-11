"""
FLORES数据集批量翻译和评估脚本
支持多种语言到中文的翻译，批量处理以减少token消耗
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
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
    "km": "khm_Khmr",  # 柬埔寨语（高棉语）
    "ms": "zsm_Latn",  # 马来语
    "zh": "zho_Hans"   # 中文（简体）
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


def load_flores_data(lang_code: str, dataset_type: str = "dev", max_samples: Optional[int] = None) -> List[str]:
    """
    加载FLORES数据集
    
    Args:
        lang_code: 语言代码（如 "en", "de", "vi"）
        dataset_type: 数据集类型（"dev" 或 "devtest"）
        max_samples: 最大样本数（None表示全部）
        
    Returns:
        List[str]: 文本列表
    """
    flores_code = FLORES_LANG_MAP.get(lang_code)
    if not flores_code:
        raise ValueError(f"不支持的语言代码: {lang_code}")
    
    data_dir = Path(__file__).parent / "datasets" / "flores200_dataset" / dataset_type
    file_path = data_dir / f"{flores_code}.{dataset_type}"
    
    if not file_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    
    texts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                texts.append(line)
                if max_samples and len(texts) >= max_samples:
                    break
    
    return texts


def load_reference_translations(lang_code: str, dataset_type: str = "dev", max_samples: Optional[int] = None) -> List[str]:
    """加载中文参考翻译"""
    return load_flores_data("zh", dataset_type, max_samples)


def create_pipeline(model_config: Optional[Dict] = None) -> TranslationPipeline:
    """
    创建翻译Pipeline
    
    Args:
        model_config: 可选的模型配置字典，格式：
            {
                "planner": "deepseek",  # 或 "qwen", "qwen_plus"
                "translator_a": "deepseek",
                "translator_b": "qwen",
                "checker": "deepseek",
                "stylist": "qwen",
                "aggregator": "deepseek"
            }
            如果为None，从config/models.yaml读取
    """
    config_path = Path(__file__).parent / "config" / "models.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    models_config = config.get('models', {})
    workflow_config = config.get('workflow', {})
    
    # 如果提供了model_config，使用它；否则从workflow配置读取
    if model_config:
        planner_type = model_config.get('planner', workflow_config.get('planner', 'deepseek'))
        translator_a_type = model_config.get('translator_a', workflow_config.get('translator_a', 'deepseek'))
        translator_b_type = model_config.get('translator_b', workflow_config.get('translator_b', 'qwen'))
        checker_type = model_config.get('checker', workflow_config.get('checker', 'deepseek'))
        stylist_type = model_config.get('stylist', workflow_config.get('stylist', 'qwen'))
        aggregator_type = model_config.get('aggregator', workflow_config.get('aggregator', 'deepseek'))
    else:
        planner_type = workflow_config.get('planner', 'deepseek')
        translator_a_type = workflow_config.get('translator_a', 'deepseek')
        translator_b_type = workflow_config.get('translator_b', 'qwen')
        checker_type = workflow_config.get('checker', 'deepseek')
        stylist_type = workflow_config.get('stylist', 'qwen')
        aggregator_type = workflow_config.get('aggregator', 'deepseek')
    
    def create_model(model_type):
        model_cfg = models_config.get(model_type, {})
        if not model_cfg.get('enabled', False):
            print(f"⚠️  模型 {model_type} 未启用")
            return None
        
        api_key_env = model_cfg.get('api_key_env')
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not api_key:
            print(f"⚠️  未找到 {model_type} API密钥（环境变量: {api_key_env}）")
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
    
    print(f"\n模型配置:")
    print(f"  Planner: {planner_type}")
    print(f"  Translator-A: {translator_a_type}")
    print(f"  Translator-B: {translator_b_type}")
    print(f"  Checker: {checker_type}")
    print(f"  Stylist: {stylist_type}")
    print(f"  Aggregator: {aggregator_type}")
    
    planner = create_model(planner_type)
    translator_a = create_model(translator_a_type)
    translator_b = create_model(translator_b_type)
    checker = create_model(checker_type)
    stylist = create_model(stylist_type)
    aggregator = create_model(aggregator_type)
    
    if not all([planner, translator_a, translator_b, checker, stylist, aggregator]):
        raise ValueError("部分模型创建失败，请检查配置和API密钥")
    
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


async def translate_batch(
    pipeline: TranslationPipeline,
    texts: List[str],
    source_lang: str,
    target_lang: str = "zh",
    batch_size: int = 10
) -> List[Dict]:
    """
    批量翻译
    
    Args:
        pipeline: 翻译Pipeline
        texts: 待翻译文本列表
        source_lang: 源语言代码
        target_lang: 目标语言代码
        batch_size: 批次大小
        
    Returns:
        List[Dict]: 翻译结果列表
    """
    results = []
    total = len(texts)
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"\n{'='*80}")
        print(f"批次 {batch_num}/{total_batches} (样本 {i+1}-{min(i+batch_size, total)})")
        print(f"{'='*80}")
        
        batch_results = []
        for j, text in enumerate(batch):
            sample_num = i + j + 1
            print(f"\n[样本 {sample_num}/{total}]")
            print(f"原文: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            try:
                result = await pipeline.translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                batch_results.append({
                    "index": sample_num - 1,
                    "source": text,
                    "translation": result.translated_text,
                    "mqm_score": {
                        "adequacy": result.explainability_report.final_quality_score.adequacy,
                        "fluency": result.explainability_report.final_quality_score.fluency,
                        "terminology": result.explainability_report.final_quality_score.terminology,
                        "overall": result.explainability_report.final_quality_score.overall
                    } if result.explainability_report and result.explainability_report.final_quality_score else None,
                    "error": None
                })
                
                print(f"翻译: {result.translated_text[:100]}{'...' if len(result.translated_text) > 100 else ''}")
                if result.explainability_report and result.explainability_report.final_quality_score:
                    print(f"MQM评分: {result.explainability_report.final_quality_score.overall:.4f}")
                
            except Exception as e:
                print(f"❌ 翻译失败: {e}")
                batch_results.append({
                    "index": sample_num - 1,
                    "source": text,
                    "translation": None,
                    "mqm_score": None,
                    "error": str(e)
                })
        
        results.extend(batch_results)
        
        # 批次间短暂休息，避免API限流
        if i + batch_size < total:
            print(f"\n等待 2 秒后继续下一批次...")
            await asyncio.sleep(2)
    
    return results


async def evaluate_batch(
    eval_service,
    translations: List[Dict],
    references: List[str]
) -> List[Dict]:
    """
    批量评估
    
    Args:
        eval_service: 评估服务
        translations: 翻译结果列表
        references: 参考翻译列表
        
    Returns:
        List[Dict]: 评估结果列表
    """
    results = []
    total = len(translations)
    
    print(f"\n{'='*80}")
    print(f"开始评估 {total} 个样本...")
    print(f"{'='*80}")
    
    for i, trans in enumerate(translations):
        if trans.get("error") or not trans.get("translation"):
            results.append({
                "index": trans["index"],
                "evaluation": None,
                "error": "翻译失败，跳过评估"
            })
            continue
        
        print(f"\n[评估 {i+1}/{total}]")
        print(f"翻译: {trans['translation'][:100]}{'...' if len(trans['translation']) > 100 else ''}")
        
        try:
            eval_result = eval_service.evaluate(
                translation=trans["translation"],
                reference=references[trans["index"]],
                source=trans["source"],
                mqm_score=trans.get("mqm_score")
            )
            
            if eval_result:
                results.append({
                    "index": trans["index"],
                    "evaluation": eval_result,
                    "error": None
                })
                print(f"综合评分: {eval_result['final_score']:.4f}")
            else:
                results.append({
                    "index": trans["index"],
                    "evaluation": None,
                    "error": "评估失败"
                })
                print("❌ 评估失败")
        except Exception as e:
            print(f"❌ 评估异常: {e}")
            results.append({
                "index": trans["index"],
                "evaluation": None,
                "error": str(e)
            })
    
    return results


def save_results(
    lang_code: str,
    translations: List[Dict],
    evaluations: List[Dict],
    output_dir: Path
):
    """保存结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lang_name = LANG_NAMES.get(lang_code, lang_code)
    
    # 合并结果
    combined_results = []
    for trans, eval_result in zip(translations, evaluations):
        combined_results.append({
            "index": trans["index"],
            "source": trans["source"],
            "translation": trans["translation"],
            "reference": None,  # 将在后面填充
            "mqm_score": trans.get("mqm_score"),
            "evaluation": eval_result.get("evaluation"),
            "error": trans.get("error") or eval_result.get("error")
        })
    
    # 保存JSON
    json_path = output_dir / f"flores_{lang_code}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "language": lang_name,
            "lang_code": lang_code,
            "timestamp": timestamp,
            "total_samples": len(combined_results),
            "results": combined_results
        }, f, ensure_ascii=False, indent=2)
    
    # 保存Markdown报告
    md_path = output_dir / f"flores_{lang_code}_{timestamp}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# FLORES数据集评估报告 - {lang_name}到中文\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**语言对**: {lang_name} → 中文\n\n")
        f.write(f"**样本数量**: {len(combined_results)}\n\n")
        
        # 统计信息
        successful = sum(1 for r in combined_results if r["evaluation"] is not None)
        f.write(f"**成功评估**: {successful}/{len(combined_results)}\n\n")
        
        if successful > 0:
            scores = [r["evaluation"]["final_score"] for r in combined_results if r["evaluation"]]
            avg_score = sum(scores) / len(scores)
            f.write(f"**平均综合评分**: {avg_score:.4f}\n\n")
            
            # 各指标平均分
            metrics = ["bleu", "comet", "bleurt", "bertscore_f1", "chrf"]
            f.write("## 各指标平均分\n\n")
            for metric in metrics:
                metric_scores = [r["evaluation"].get(metric, 0) for r in combined_results if r["evaluation"] and r["evaluation"].get(metric, 0) > 0]
                if metric_scores:
                    avg_metric = sum(metric_scores) / len(metric_scores)
                    f.write(f"- **{metric.upper()}**: {avg_metric:.4f}\n")
            f.write("\n")
        
        # 详细结果
        f.write("## 详细结果\n\n")
        for r in combined_results:
            f.write(f"### 样本 {r['index'] + 1}\n\n")
            f.write(f"**原文**: {r['source']}\n\n")
            f.write(f"**翻译**: {r['translation'] or '翻译失败'}\n\n")
            if r.get("evaluation"):
                eval_data = r["evaluation"]
                f.write("**评估结果**:\n\n")
                f.write(f"- BLEU: {eval_data.get('bleu', 0):.4f}\n")
                if eval_data.get('comet', 0) > 0:
                    f.write(f"- COMET: {eval_data.get('comet', 0):.4f}\n")
                if eval_data.get('bleurt', 0) > 0:
                    f.write(f"- BLEURT: {eval_data.get('bleurt', 0):.4f}\n")
                f.write(f"- BERTScore: {eval_data.get('bertscore_f1', 0):.4f}\n")
                f.write(f"- ChrF: {eval_data.get('chrf', 0):.4f}\n")
                f.write(f"- 综合评分: {eval_data.get('final_score', 0):.4f}\n\n")
            if r.get("error"):
                f.write(f"**错误**: {r['error']}\n\n")
            f.write("---\n\n")
    
    print(f"\n✅ 结果已保存:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


async def main():
    """主函数"""
    # 配置参数
    LANGUAGES = ["en", "de", "vi", "km", "ms"]  # 要测试的语言
    DATASET_TYPE = "dev"  # 使用dev数据集
    MAX_SAMPLES = 50  # 每种语言最多测试50条（可根据需要调整）
    BATCH_SIZE = 10  # 每批翻译10条
    
    print("=" * 80)
    print("FLORES数据集批量翻译和评估")
    print("=" * 80)
    print(f"测试语言: {[LANG_NAMES.get(l, l) for l in LANGUAGES]}")
    print(f"数据集类型: {DATASET_TYPE}")
    print(f"每种语言样本数: {MAX_SAMPLES}")
    print(f"批次大小: {BATCH_SIZE}")
    print("=" * 80)
    
    # 创建输出目录
    output_dir = Path(__file__).parent / "results" / "flores_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化评估服务
    print("\n[1/3] 初始化评估服务...")
    eval_service = create_evaluation_service()
    if not eval_service or not eval_service.is_available():
        print("❌ 评估服务不可用")
        return
    print("✅ 评估服务已就绪")
    
    # 创建翻译Pipeline
    print("\n[2/3] 初始化翻译Pipeline...")
    try:
        # 可以使用自定义模型配置，例如：
        # model_config = {
        #     "planner": "deepseek",
        #     "translator_a": "deepseek",
        #     "translator_b": "qwen",
        #     "checker": "deepseek",
        #     "stylist": "qwen",
        #     "aggregator": "deepseek"
        # }
        # pipeline = create_pipeline(model_config)
        # 如果不提供model_config，将从config/models.yaml读取
        pipeline = create_pipeline()
        print("✅ 翻译Pipeline已就绪")
    except Exception as e:
        print(f"❌ 翻译Pipeline初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 处理每种语言
    for lang_code in LANGUAGES:
        lang_name = LANG_NAMES.get(lang_code, lang_code)
        print(f"\n{'='*80}")
        print(f"处理语言: {lang_name} ({lang_code})")
        print(f"{'='*80}")
        
        try:
            # 加载数据
            print(f"\n加载 {lang_name} 数据...")
            sources = load_flores_data(lang_code, DATASET_TYPE, MAX_SAMPLES)
            references = load_reference_translations(lang_code, DATASET_TYPE, MAX_SAMPLES)
            
            if len(sources) != len(references):
                print(f"⚠️  源文本和参考翻译数量不匹配: {len(sources)} vs {len(references)}")
                min_len = min(len(sources), len(references))
                sources = sources[:min_len]
                references = references[:min_len]
            
            print(f"✅ 已加载 {len(sources)} 条样本")
            
            # 批量翻译
            print(f"\n开始批量翻译（批次大小: {BATCH_SIZE}）...")
            translations = await translate_batch(
                pipeline,
                sources,
                source_lang=lang_code,
                target_lang="zh",
                batch_size=BATCH_SIZE
            )
            
            # 批量评估
            print(f"\n开始批量评估...")
            evaluations = await evaluate_batch(
                eval_service,
                translations,
                references
            )
            
            # 保存结果
            print(f"\n保存结果...")
            save_results(lang_code, translations, evaluations, output_dir)
            
        except Exception as e:
            print(f"❌ 处理 {lang_name} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*80}")
    print("所有语言处理完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())

