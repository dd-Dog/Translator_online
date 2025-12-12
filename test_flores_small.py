"""
FLORES数据集小规模测试脚本
测试翻译和评估流程是否正常
包含详细的翻译阶段日志和报告生成
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
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


async def translate_with_detailed_logging(
    pipeline: TranslationPipeline,
    source_text: str,
    source_lang: str,
    target_lang: str = "zh"
) -> tuple[Any, Dict[str, Any]]:
    """
    执行翻译并记录每个阶段的详细日志
    
    Returns:
        tuple: (FinalTranslation结果, 详细日志字典)
    """
    detailed_log = {
        "stages": []
    }
    
    try:
        # 阶段1: 任务规划
        planner_model_name = pipeline.planner.model.model_name if hasattr(pipeline.planner, 'model') and hasattr(pipeline.planner.model, 'model_name') else "Unknown"
        print(f"\n{'─'*80}")
        print(f"📋 阶段1: 任务规划 (Planner)")
        print(f"{'─'*80}")
        print(f"使用模型: {planner_model_name}")
        print(f"输入:")
        print(f"  原文: {source_text[:300]}{'...' if len(source_text) > 300 else ''}")
        print(f"  源语言: {source_lang or '自动检测'}")
        print(f"  目标语言: {target_lang}")
        
        task_plan = await pipeline.planner.plan(source_text, source_lang, target_lang)
        
        stage1_log = {
            "stage": "任务规划 (Planner)",
            "model": planner_model_name,
            "input": {
                "text": source_text,
                "source_lang": source_lang,
                "target_lang": target_lang
            },
            "output": {
                "source_lang": task_plan.source_lang,
                "target_lang": task_plan.target_lang,
                "tasks_count": len(task_plan.tasks),
                "tasks": [
                    {
                        "segment_id": task.get('segment_id'),
                        "text": task.get('text', '')[:200] + ('...' if len(task.get('text', '')) > 200 else ''),
                        "needs_double_translation": task.get('needs_double_translation', False)
                    }
                    for task in task_plan.tasks
                ]
            }
        }
        detailed_log["stages"].append(stage1_log)
        
        print(f"输出:")
        print(f"  检测到的源语言: {task_plan.source_lang}")
        print(f"  任务数量: {len(task_plan.tasks)}")
        for i, task in enumerate(task_plan.tasks, 1):
            print(f"  任务{i}: {task.get('text', '')[:100]}{'...' if len(task.get('text', '')) > 100 else ''}")
        
        # 处理每个任务
        final_segments = []
        all_explainability_reports = []
        all_stage_logs = []
        
        for task_idx, task in enumerate(task_plan.tasks, 1):
            segment_id = task['segment_id']
            segment_text = task['text']
            needs_double = task.get('needs_double_translation', False)
            
            print(f"\n{'─'*80}")
            print(f"处理任务 {task_idx}/{len(task_plan.tasks)} (Segment ID: {segment_id})")
            print(f"{'─'*80}")
            
            task_stages = []
            
            # 阶段2: 主翻译（Translator-A）
            translator_a_model_name = pipeline.translator_a.model.model_name if hasattr(pipeline.translator_a, 'model') and hasattr(pipeline.translator_a.model, 'model_name') else "Unknown"
            print(f"\n📝 阶段2: 主翻译 (Translator-A)")
            print(f"使用模型: {translator_a_model_name}")
            print(f"输入: {segment_text[:200]}{'...' if len(segment_text) > 200 else ''}")
            
            draft_a = await pipeline.translator_a.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            stage2_log = {
                "stage": "主翻译 (Translator-A)",
                "model": translator_a_model_name,
                "input": segment_text,
                "output": draft_a.translated_text
            }
            task_stages.append(stage2_log)
            
            print(f"输出: {draft_a.translated_text[:200]}{'...' if len(draft_a.translated_text) > 200 else ''}")
            
            # 阶段3: 对照翻译（Translator-B）
            translator_b_model_name = pipeline.translator_b.model.model_name if hasattr(pipeline.translator_b, 'model') and hasattr(pipeline.translator_b.model, 'model_name') else "Unknown"
            print(f"\n📝 阶段3: 对照翻译 (Translator-B)")
            print(f"使用模型: {translator_b_model_name}")
            print(f"输入: {segment_text[:200]}{'...' if len(segment_text) > 200 else ''}")
            
            draft_b = await pipeline.translator_b.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            stage3_log = {
                "stage": "对照翻译 (Translator-B)",
                "model": translator_b_model_name,
                "input": segment_text,
                "output": draft_b.translated_text
            }
            task_stages.append(stage3_log)
            
            print(f"输出: {draft_b.translated_text[:200]}{'...' if len(draft_b.translated_text) > 200 else ''}")
            
            # 阶段4: 一致性检查
            checker_model_name = pipeline.checker.model.model_name if hasattr(pipeline.checker, 'model') and hasattr(pipeline.checker.model, 'model_name') else "Unknown"
            print(f"\n🔍 阶段4: 质量检查 (Checker)")
            print(f"使用模型: {checker_model_name}")
            print(f"输入:")
            print(f"  原文: {segment_text[:150]}{'...' if len(segment_text) > 150 else ''}")
            print(f"  翻译A: {draft_a.translated_text[:150]}{'...' if len(draft_a.translated_text) > 150 else ''}")
            print(f"  翻译B: {draft_b.translated_text[:150]}{'...' if len(draft_b.translated_text) > 150 else ''}")
            
            checker_report = await pipeline.checker.check(
                segment_text,
                draft_a,
                draft_b,
                segment_id
            )
            
            stage4_log = {
                "stage": "质量检查 (Checker)",
                "model": checker_model_name,
                "input": {
                    "source": segment_text,
                    "translation_a": draft_a.translated_text,
                    "translation_b": draft_b.translated_text
                },
                "output": {
                    "consistent": segment_id in checker_report.consistent_segments,
                    "has_conflicts": len(checker_report.conflicting_segments) > 0,
                    "conflicts_count": len(checker_report.conflicting_segments),
                    "quality_score": {
                        "adequacy": checker_report.quality_scores.get(segment_id, {}).adequacy if segment_id in checker_report.quality_scores else None,
                        "fluency": checker_report.quality_scores.get(segment_id, {}).fluency if segment_id in checker_report.quality_scores else None,
                        "terminology": checker_report.quality_scores.get(segment_id, {}).terminology if segment_id in checker_report.quality_scores else None,
                        "overall": checker_report.quality_scores.get(segment_id, {}).overall if segment_id in checker_report.quality_scores else None
                    } if segment_id in checker_report.quality_scores else None
                }
            }
            task_stages.append(stage4_log)
            
            if segment_id in checker_report.quality_scores:
                qs = checker_report.quality_scores[segment_id]
                print(f"输出:")
                print(f"  质量评分: {qs.overall:.4f} (adequacy: {qs.adequacy:.4f}, fluency: {qs.fluency:.4f}, terminology: {qs.terminology:.4f})")
                print(f"  一致性: {'一致' if segment_id in checker_report.consistent_segments else '存在冲突'}")
            
            # 选择最佳翻译
            best_draft = pipeline._select_best_draft(draft_a, draft_b, checker_report)
            print(f"  选择: {'翻译A' if best_draft == draft_a else '翻译B'}")
            
            # 阶段5: 风格化
            stylist_model_name = pipeline.stylist.model.model_name if hasattr(pipeline.stylist, 'model') and hasattr(pipeline.stylist.model, 'model_name') else "Unknown"
            print(f"\n🎨 阶段5: 风格化 (Stylist)")
            print(f"使用模型: {stylist_model_name}")
            print(f"输入: {best_draft.translated_text[:200]}{'...' if len(best_draft.translated_text) > 200 else ''}")
            
            stylist_result = await pipeline.stylist.style(
                best_draft.translated_text,
                segment_text
            )
            
            stage5_log = {
                "stage": "风格化 (Stylist)",
                "model": stylist_model_name,
                "input": best_draft.translated_text,
                "output": stylist_result.styled_text,
                "terminology_changes": stylist_result.terminology_changes,
                "style_changes": stylist_result.style_changes
            }
            task_stages.append(stage5_log)
            
            print(f"输出: {stylist_result.styled_text[:200]}{'...' if len(stylist_result.styled_text) > 200 else ''}")
            if stylist_result.terminology_changes:
                print(f"  术语变更: {len(stylist_result.terminology_changes)} 处")
            if stylist_result.style_changes:
                print(f"  风格变更: {len(stylist_result.style_changes)} 处")
            
            # 阶段6: 最终整合
            aggregator_model_name = pipeline.aggregator.model.model_name if hasattr(pipeline.aggregator, 'model') and hasattr(pipeline.aggregator.model, 'model_name') else "Unknown"
            print(f"\n🔧 阶段6: 最终整合 (Aggregator)")
            print(f"使用模型: {aggregator_model_name}")
            print(f"输入:")
            print(f"  原文: {segment_text[:150]}{'...' if len(segment_text) > 150 else ''}")
            print(f"  翻译A: {draft_a.translated_text[:150]}{'...' if len(draft_a.translated_text) > 150 else ''}")
            print(f"  翻译B: {draft_b.translated_text[:150]}{'...' if len(draft_b.translated_text) > 150 else ''}")
            print(f"  风格化结果: {stylist_result.styled_text[:150]}{'...' if len(stylist_result.styled_text) > 150 else ''}")
            
            final_result = await pipeline.aggregator.aggregate(
                segment_text,
                [draft_a, draft_b],
                checker_report,
                stylist_result,
                segment_id
            )
            
            stage6_log = {
                "stage": "最终整合 (Aggregator)",
                "model": aggregator_model_name,
                "input": {
                    "source": segment_text,
                    "draft_a": draft_a.translated_text,
                    "draft_b": draft_b.translated_text,
                    "styled_text": stylist_result.styled_text
                },
                "output": final_result.translated_text,
                "quality_score": {
                    "adequacy": final_result.explainability_report.final_quality_score.adequacy,
                    "fluency": final_result.explainability_report.final_quality_score.fluency,
                    "terminology": final_result.explainability_report.final_quality_score.terminology,
                    "overall": final_result.explainability_report.final_quality_score.overall
                } if final_result.explainability_report and final_result.explainability_report.final_quality_score else None
            }
            task_stages.append(stage6_log)
            
            print(f"输出: {final_result.translated_text[:200]}{'...' if len(final_result.translated_text) > 200 else ''}")
            if final_result.explainability_report and final_result.explainability_report.final_quality_score:
                qs = final_result.explainability_report.final_quality_score
                print(f"  最终质量评分: {qs.overall:.4f}")
            
            final_segments.append({
                'segment_id': segment_id,
                'text': final_result.translated_text
            })
            all_explainability_reports.append(final_result.explainability_report)
            all_stage_logs.append({
                "segment_id": segment_id,
                "stages": task_stages
            })
        
        # 合并所有段落
        final_text = ' '.join([seg['text'] for seg in final_segments])
        merged_explainability = pipeline._merge_explainability_reports(all_explainability_reports)
        
        from src.agents.workflow import FinalTranslation
        final_translation = FinalTranslation(
            translated_text=final_text,
            explainability_report=merged_explainability,
            source_lang=task_plan.source_lang,
            target_lang=task_plan.target_lang,
            processing_stages=[
                "Task Planning",
                "Primary Translation (Translator-A)",
                "Comparison Translation (Translator-B)",
                "Quality Checking",
                "Styling",
                "Final Aggregation"
            ]
        )
        
        detailed_log["stages"].extend(all_stage_logs)
        detailed_log["final_translation"] = final_text
        detailed_log["final_quality_score"] = {
            "adequacy": merged_explainability.final_quality_score.adequacy,
            "fluency": merged_explainability.final_quality_score.fluency,
            "terminology": merged_explainability.final_quality_score.terminology,
            "overall": merged_explainability.final_quality_score.overall
        } if merged_explainability.final_quality_score else None
        
        return final_translation, detailed_log
        
    except Exception as e:
        detailed_log["error"] = str(e)
        import traceback
        detailed_log["traceback"] = traceback.format_exc()
        raise


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
    print(f"原文 ({LANG_NAMES.get(source_lang, source_lang)}): {source_text}")
    print(f"参考翻译: {reference}")
    
    result = {
        "index": index,
        "source": source_text,
        "reference": reference,
        "translation": None,
        "translation_stages": None,
        "mqm_score": None,
        "evaluation": None,
        "error": None
    }
    
    # 步骤1: 翻译（带详细日志）
    print(f"\n[1/2] 执行翻译（详细日志模式）...")
    try:
        translation_result, detailed_log = await translate_with_detailed_logging(
            pipeline,
            source_text,
            source_lang,
            "zh"
        )
        
        result["translation"] = translation_result.translated_text
        result["translation_stages"] = detailed_log
        print(f"\n✅ 翻译完成")
        print(f"最终翻译: {translation_result.translated_text}")
        
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
            comet_score = eval_result.get('comet', 0)
            if comet_score > 0:
                print(f"  COMET: {comet_score:.4f}")
            bleurt_score = eval_result.get('bleurt', 0)
            # 显示BLEURT评分（即使为0也显示，以便调试）
            print(f"  BLEURT: {bleurt_score:.4f}" + (" (未计算)" if bleurt_score == 0 else ""))
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
    TEST_SAMPLES = 1  # 测试样本数（少量测试）
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
    
    # 生成详细报告
    print(f"\n{'='*80}")
    print("生成详细报告...")
    print(f"{'='*80}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "results" / "flores_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存JSON报告
    json_path = output_dir / f"test_report_{timestamp}.json"
    report_data = {
        "test_config": {
            "language": lang_name,
            "lang_code": TEST_LANG,
            "samples": TEST_SAMPLES,
            "dataset_type": DATASET_TYPE,
            "timestamp": timestamp
        },
        "summary": {
            "total_samples": len(results),
            "successful": successful,
            "failed": failed,
            "avg_final_score": avg_score if successful > 0 else None,
            "avg_metrics": {
                metric: sum([r["evaluation"].get(metric, 0) for r in results 
                           if r.get("evaluation") and r["evaluation"].get(metric, 0) > 0]) / 
                        len([r for r in results if r.get("evaluation") and r["evaluation"].get(metric, 0) > 0])
                for metric in metrics
                if len([r for r in results if r.get("evaluation") and r["evaluation"].get(metric, 0) > 0]) > 0
            }
        },
        "results": results
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON报告已保存: {json_path}")
    
    # 保存Markdown报告
    md_path = output_dir / f"test_report_{timestamp}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# FLORES数据集测试报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**语言对**: {lang_name} → 中文\n\n")
        f.write(f"**样本数量**: {len(results)}\n\n")
        f.write(f"**成功**: {successful} | **失败**: {failed}\n\n")
        
        if successful > 0:
            f.write(f"## 总体统计\n\n")
            f.write(f"- **平均综合评分**: {avg_score:.4f}\n\n")
            f.write(f"### 各指标平均分\n\n")
            for metric in metrics:
                metric_scores = [r["evaluation"].get(metric, 0) for r in results 
                               if r.get("evaluation") and r["evaluation"].get(metric, 0) > 0]
                if metric_scores:
                    avg_metric = sum(metric_scores) / len(metric_scores)
                    f.write(f"- **{metric.upper()}**: {avg_metric:.4f}\n")
            f.write("\n")
            
            # 评分汇总表格
            f.write(f"## 评分汇总\n\n")
            f.write(f"| 源语言 | 目标语言 | BLEU | COMET | BERTScore F1 | BLEURT | chrF | 综合评分 | MQM_ADEQUACY | MQM_FLUENCY | MQM_OVERALL | MQM_TERMINOLOGY |\n")
            f.write(f"| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
            
            # 计算当前语言对的平均分
            eval_results = [r["evaluation"] for r in results if r.get("evaluation")]
            if eval_results:
                # 计算各指标平均值
                avg_bleu = sum(e.get('bleu', 0) for e in eval_results) / len(eval_results)
                avg_comet = sum(e.get('comet', 0) for e in eval_results if e.get('comet', 0) > 0)
                comet_count = sum(1 for e in eval_results if e.get('comet', 0) > 0)
                avg_comet = avg_comet / comet_count if comet_count > 0 else 0.0
                avg_bertscore = sum(e.get('bertscore_f1', 0) for e in eval_results) / len(eval_results)
                avg_bleurt = sum(e.get('bleurt', 0) for e in eval_results if e.get('bleurt', 0) > 0)
                bleurt_count = sum(1 for e in eval_results if e.get('bleurt', 0) > 0)
                avg_bleurt = avg_bleurt / bleurt_count if bleurt_count > 0 else 0.0
                avg_chrf = sum(e.get('chrf', 0) for e in eval_results) / len(eval_results)
                avg_final = sum(e.get('final_score', 0) for e in eval_results) / len(eval_results)
                
                # MQM平均值
                mqm_results = [r.get("mqm_score") for r in results if r.get("mqm_score")]
                avg_mqm_adequacy = sum(m.get('adequacy', 0) for m in mqm_results) / len(mqm_results) if mqm_results else 0.0
                avg_mqm_fluency = sum(m.get('fluency', 0) for m in mqm_results) / len(mqm_results) if mqm_results else 0.0
                avg_mqm_overall = sum(m.get('overall', 0) for m in mqm_results) / len(mqm_results) if mqm_results else 0.0
                avg_mqm_terminology = sum(m.get('terminology', 0) for m in mqm_results) / len(mqm_results) if mqm_results else 0.0
                
                # 写入表格行
                f.write(f"| {lang_name} | Chinese | {avg_bleu:.4f} | {avg_comet:.4f} | {avg_bertscore:.4f} | {avg_bleurt:.4f} | {avg_chrf:.4f} | {avg_final:.4f} | {avg_mqm_adequacy:.4f} | {avg_mqm_fluency:.4f} | {avg_mqm_overall:.4f} | {avg_mqm_terminology:.4f} |\n")
                
                # 如果有多个语言对，这里可以添加汇总行
                # 目前只有一种语言，所以汇总行就是当前行的值
                f.write(f"| **汇总** | **平均值** | **{avg_bleu:.4f}** | **{avg_comet:.4f}** | **{avg_bertscore:.4f}** | **{avg_bleurt:.4f}** | **{avg_chrf:.4f}** | **{avg_final:.4f}** | **{avg_mqm_adequacy:.4f}** | **{avg_mqm_fluency:.4f}** | **{avg_mqm_overall:.4f}** | **{avg_mqm_terminology:.4f}** |\n")
            f.write("\n")
        
        f.write(f"## 详细结果\n\n")
        for r in results:
            f.write(f"### 样本 {r['index'] + 1}\n\n")
            f.write(f"**原文**: {r['source']}\n\n")
            f.write(f"**参考翻译**: {r['reference']}\n\n")
            f.write(f"**翻译结果**: {r['translation'] or '翻译失败'}\n\n")
            
            # 翻译阶段详情
            if r.get("translation_stages"):
                f.write(f"#### 翻译阶段详情\n\n")
                stages = r["translation_stages"]
                
                # 任务规划
                if stages.get("stages") and len(stages["stages"]) > 0:
                    plan_stage = stages["stages"][0]
                    if plan_stage.get("stage") == "任务规划 (Planner)":
                        f.write(f"##### 阶段1: 任务规划\n\n")
                        f.write(f"- **使用模型**: {plan_stage.get('model', 'Unknown')}\n")
                        f.write(f"- **检测到的源语言**: {plan_stage['output'].get('source_lang')}\n")
                        f.write(f"- **任务数量**: {plan_stage['output'].get('tasks_count')}\n")
                        f.write(f"- **任务列表**:\n")
                        for task in plan_stage['output'].get('tasks', []):
                            f.write(f"  - 任务 {task.get('segment_id')}: {task.get('text', '')[:100]}...\n")
                        f.write("\n")
                
                # 各任务的翻译阶段
                for task_log in stages.get("stages", []):
                    if isinstance(task_log, dict) and "segment_id" in task_log:
                        f.write(f"##### 任务 {task_log.get('segment_id')} 的翻译流程\n\n")
                        for stage in task_log.get("stages", []):
                            stage_name = stage.get("stage", "")
                            model_name = stage.get("model", "Unknown")
                            f.write(f"**{stage_name}** (模型: {model_name})\n\n")
                            if isinstance(stage.get("input"), str):
                                f.write(f"- 输入: {stage['input'][:200]}...\n")
                            elif isinstance(stage.get("input"), dict):
                                f.write(f"- 输入: {json.dumps(stage['input'], ensure_ascii=False, indent=2)}\n")
                            if isinstance(stage.get("output"), str):
                                f.write(f"- 输出: {stage['output'][:200]}...\n")
                            elif isinstance(stage.get("output"), dict):
                                f.write(f"- 输出: {json.dumps(stage['output'], ensure_ascii=False, indent=2)}\n")
                            f.write("\n")
            
            # MQM评分
            if r.get("mqm_score"):
                f.write(f"#### MQM评分\n\n")
                mqm = r["mqm_score"]
                f.write(f"- **总体**: {mqm.get('overall', 0):.4f}\n")
                f.write(f"- **充分性**: {mqm.get('adequacy', 0):.4f}\n")
                f.write(f"- **流畅性**: {mqm.get('fluency', 0):.4f}\n")
                f.write(f"- **术语准确性**: {mqm.get('terminology', 0):.4f}\n\n")
            
            # 评估结果
            if r.get("evaluation"):
                f.write(f"#### 评估结果\n\n")
                eval_data = r["evaluation"]
                f.write(f"- **BLEU**: {eval_data.get('bleu', 0):.4f}\n")
                comet_score = eval_data.get('comet', 0)
                if comet_score > 0:
                    f.write(f"- **COMET**: {comet_score:.4f}\n")
                bleurt_score = eval_data.get('bleurt', 0)
                # 始终显示BLEURT评分（即使为0）
                f.write(f"- **BLEURT**: {bleurt_score:.4f}" + (" (未计算)" if bleurt_score == 0 else "") + "\n")
                f.write(f"- **BERTScore**: {eval_data.get('bertscore_f1', 0):.4f}\n")
                f.write(f"- **ChrF**: {eval_data.get('chrf', 0):.4f}\n")
                f.write(f"- **综合评分**: {eval_data.get('final_score', 0):.4f}\n\n")
            
            if r.get("error"):
                f.write(f"**错误**: {r['error']}\n\n")
            
            f.write("---\n\n")
    
    print(f"✅ Markdown报告已保存: {md_path}")
    print(f"\n{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())

