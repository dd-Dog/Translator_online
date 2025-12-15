"""
FLORES数据集批量翻译和评估脚本
支持多种语言到中文的翻译，批量处理以减少token消耗
"""

from __future__ import annotations

import asyncio
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import yaml
import logging
from logging.handlers import RotatingFileHandler
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

# 全局日志对象
logger = None

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


def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    设置日志配置，同时输出到控制台和文件
    
    Args:
        log_dir: 日志文件目录（如果为None，使用默认目录）
        
    Returns:
        logging.Logger: 配置好的日志对象
    """
    if log_dir is None:
        log_dir = Path(__file__).parent / "logs" / "flores_batch"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建日志文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"flores_batch_{timestamp}.log"
    
    # 创建logger
    logger = logging.getLogger("flores_batch")
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式
    detailed_format = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
    simple_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 文件handler（详细格式，包含所有级别）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(detailed_format, date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台handler（简化格式，INFO级别以上）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(simple_format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"日志系统已初始化，日志文件: {log_file}")
    logger.info("=" * 80)
    
    return logger


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
            print(f"[WARN] 模型 {model_type} 未启用")
            return None
        
        api_key_env = model_cfg.get('api_key_env')
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        if not api_key:
            print(f"[WARN] 未找到 {model_type} API密钥（环境变量: {api_key_env}）")
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
    
    print(f"\n[INFO] 模型配置:")
    print(f"  Planner: {planner_type}")
    print(f"  Translator-A: {translator_a_type}")
    print(f"  Translator-B: {translator_b_type}")
    print(f"  Checker: {checker_type}")
    print(f"  Stylist: {stylist_type}")
    print(f"  Aggregator: {aggregator_type}")
    print(f"\n[INFO] 初始化模型...")
    
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


async def translate_single(
    pipeline: TranslationPipeline,
    text: str,
    index: int,
    source_lang: str,
    target_lang: str,
    total: int,
    temp_writer: Optional['TranslationTempWriter'] = None
) -> Dict:
    """
    翻译单个文本（用于并发批量翻译）
    
    Args:
        pipeline: 翻译Pipeline
        text: 待翻译文本
        index: 文本索引
        source_lang: 源语言代码
        target_lang: 目标语言代码
        total: 总样本数
        
    Returns:
        Dict: 翻译结果
    """
    sample_num = index + 1
    start_time = datetime.now()
    
    try:
        logger.debug(f"[翻译阶段] 样本 {sample_num}/{total} 开始翻译")
        result = await pipeline.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        translation_text = result.translated_text
        logger.info(f"[翻译阶段] 样本 {sample_num}/{total} 翻译完成，耗时 {elapsed_time:.2f} 秒")
        logger.debug(f"[翻译阶段] 样本 {sample_num} 翻译结果: {translation_text}")
        
        # 记录MQM评分
        mqm_score = None
        if result.explainability_report and result.explainability_report.final_quality_score:
            mqm_score = {
                "adequacy": result.explainability_report.final_quality_score.adequacy,
                "fluency": result.explainability_report.final_quality_score.fluency,
                "terminology": result.explainability_report.final_quality_score.terminology,
                "overall": result.explainability_report.final_quality_score.overall
            }
            logger.debug(f"[翻译阶段] 样本 {sample_num} MQM评分: 充分性={mqm_score['adequacy']:.4f}, "
                      f"流畅性={mqm_score['fluency']:.4f}, 术语={mqm_score['terminology']:.4f}, "
                      f"总体={mqm_score['overall']:.4f}")
        
        result_dict = {
            "index": index,
            "source": text,
            "translation": translation_text,
            "mqm_score": mqm_score,
            "error": None,
            "translation_time": elapsed_time
        }
        
        # 实时写入到临时文件
        if temp_writer:
            temp_writer.write_translation(result_dict)
        
        return result_dict
    except Exception as e:
        elapsed_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"[翻译阶段] 样本 {sample_num}/{total} 翻译失败，耗时 {elapsed_time:.2f} 秒: {error_msg}")
        logger.exception(f"[翻译阶段] 样本 {sample_num} 异常详情:")
        
        result_dict = {
            "index": index,
            "source": text,
            "translation": None,
            "mqm_score": None,
            "error": error_msg,
            "translation_time": elapsed_time
        }
        
        # 实时写入错误结果
        if temp_writer:
            temp_writer.write_translation(result_dict)
        
        return result_dict


async def translate_batch(
    pipeline: TranslationPipeline,
    texts: List[str],
    source_lang: str,
    target_lang: str = "zh",
    batch_size: int = 10,
    temp_writer: Optional['TranslationTempWriter'] = None
) -> List[Dict]:
    """
    批量翻译（真正的并发批量处理）
    
    Args:
        pipeline: 翻译Pipeline
        texts: 待翻译文本列表
        source_lang: 源语言代码
        target_lang: 目标语言代码
        batch_size: 批次大小（每批并发翻译的数量）
        
    Returns:
        List[Dict]: 翻译结果列表
    """
    results = []
    total = len(texts)
    
    logger.info(f"[翻译阶段] 开始批量翻译: 总样本数={total}, 批次大小={batch_size}, 源语言={source_lang}, 目标语言={target_lang}")
    print(f"\n[翻译阶段] 开始批量翻译: 总样本数={total}, 批次大小={batch_size}")
    
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info("=" * 80)
        logger.info(f"[翻译阶段] 批次 {batch_num}/{total_batches} (样本 {i+1}-{min(i+batch_size, total)})")
        logger.info("=" * 80)
        print(f"\n{'='*80}")
        print(f"批次 {batch_num}/{total_batches} (样本 {i+1}-{min(i+batch_size, total)})")
        print(f"{'='*80}")
        
        # 创建并发任务
        batch_start_time = datetime.now()
        tasks = [
            translate_single(pipeline, text, i + j, source_lang, target_lang, total, temp_writer)
            for j, text in enumerate(batch)
        ]
        
        # 并发执行批量翻译
        logger.info(f"[翻译阶段] 批次 {batch_num} 开始并发翻译 {len(tasks)} 个样本...")
        print(f"并发翻译 {len(tasks)} 个样本...")
        batch_results = await asyncio.gather(*tasks)
        
        batch_elapsed = (datetime.now() - batch_start_time).total_seconds()
        logger.info(f"[翻译阶段] 批次 {batch_num} 完成，耗时 {batch_elapsed:.2f} 秒")
        
        # 显示批次结果摘要
        batch_successful = sum(1 for r in batch_results if r.get("translation") is not None)
        print(f"批次 {batch_num} 完成: 成功 {batch_successful}/{len(batch_results)}, 耗时 {batch_elapsed:.2f} 秒")
        
        # 显示每个样本的简要信息
        for result in batch_results:
            sample_num = result["index"] + 1
            if result.get("translation"):
                print(f"  [样本 {sample_num}] ✓ {result['translation'][:50]}{'...' if len(result['translation']) > 50 else ''}")
            else:
                print(f"  [样本 {sample_num}] ✗ 翻译失败: {result.get('error', '未知错误')}")
        
        results.extend(batch_results)
        
        # 批次间短暂休息，避免API限流
        if i + batch_size < total:
            logger.info(f"[翻译阶段] 批次 {batch_num} 完成，等待 2 秒后继续下一批次...")
            print(f"\n等待 2 秒后继续下一批次...")
            await asyncio.sleep(2)
    
    # 统计翻译结果
    successful = sum(1 for r in results if r.get("translation") is not None)
    failed = total - successful
    logger.info(f"[翻译阶段] 批量翻译完成: 成功={successful}, 失败={failed}, 总计={total}")
    print(f"\n[翻译阶段] 批量翻译完成: 成功={successful}, 失败={failed}, 总计={total}")
    
    return results


async def evaluate_batch(
    eval_service,
    translations: List[Dict],
    references: List[str],
    eval_writer: Optional['EvaluationTempWriter'] = None
) -> List[Dict]:
    """
    批量评估（支持实时保存和断点恢复）
    
    Args:
        eval_service: 评估服务
        translations: 翻译结果列表
        references: 参考翻译列表
        eval_writer: 评估结果实时写入器（可选）
        
    Returns:
        List[Dict]: 评估结果列表
    """
    results = []
    total = len(translations)
    
    # 如果提供了写入器，先加载已有结果（用于断点恢复）
    existing_results_map = {}
    if eval_writer:
        existing_evaluations = eval_writer.get_all_evaluations()
        # 构建已有结果的映射（按index索引）
        for existing in existing_evaluations:
            existing_results_map[existing["index"]] = {
                "index": existing["index"],
                "evaluation": existing.get("evaluation"),
                "error": existing.get("error"),
                "evaluation_time": existing.get("evaluation_time", 0)
            }
        logger.info(f"[评估阶段] 已加载 {len(existing_evaluations)} 条已有评估结果，将从中断点继续")
    
    logger.info("=" * 80)
    logger.info(f"[评估阶段] 开始批量评估: 总样本数={total}")
    logger.info("=" * 80)
    print(f"\n{'='*80}")
    print(f"开始评估 {total} 个样本...")
    if eval_writer and eval_writer.evaluated_indices:
        print(f"[恢复] 已评估: {len(eval_writer.evaluated_indices)} 条，待评估: {total - len(eval_writer.evaluated_indices)} 条")
    print(f"{'='*80}")
    
    for i, trans in enumerate(translations):
        sample_num = trans["index"] + 1
        
        # 检查是否已评估（断点恢复）
        if trans["index"] in existing_results_map:
            existing_result = existing_results_map[trans["index"]]
            results.append(existing_result)
            logger.info(f"[评估阶段] 样本 {sample_num}/{total} 已评估，跳过（恢复模式）")
            print(f"[跳过] 样本 {sample_num} 已评估（恢复模式）")
            continue
        
        if trans.get("error") or not trans.get("translation"):
            error_reason = trans.get("error", "翻译失败，跳过评估")
            logger.warning(f"[评估阶段] 样本 {sample_num} 跳过评估: {error_reason}")
            
            result_dict = {
                "index": trans["index"],
                "evaluation": None,
                "error": error_reason,
                "evaluation_time": 0
            }
            results.append(result_dict)
            
            # 实时写入跳过结果
            if eval_writer:
                eval_writer.write_evaluation(result_dict)
            
            continue
        
        logger.info(f"[评估阶段] 样本 {sample_num}/{total}")
        logger.debug(f"[评估阶段] 样本 {sample_num} 翻译文本: {trans['translation']}")
        
        # 检查索引是否在有效范围内，并获取参考文本
        trans_index = trans["index"]
        if trans_index >= len(references) or references[trans_index] is None:
            error_msg = f"缺少参考文本: trans['index']={trans_index}, references长度={len(references)}"
            logger.warning(f"[评估阶段] 样本 {sample_num} {error_msg}")
            # 如果没有参考文本，使用空字符串（某些评估指标可能仍能工作）
            reference_text = ""
            if trans_index >= len(references):
                logger.error(f"[评估阶段] 样本 {sample_num} 索引越界，跳过评估")
                result_dict = {
                    "index": trans_index,
                    "evaluation": None,
                    "error": error_msg,
                    "evaluation_time": 0
                }
                results.append(result_dict)
                
                # 实时写入错误结果
                if eval_writer:
                    eval_writer.write_evaluation(result_dict)
                
                print(f"[ERROR] {error_msg}")
                continue
        else:
            reference_text = references[trans_index]
        logger.debug(f"[评估阶段] 样本 {sample_num} 参考文本: {reference_text}")
        print(f"\n[评估 {i+1}/{total}]")
        print(f"翻译: {trans['translation'][:100]}{'...' if len(trans['translation']) > 100 else ''}")
        
        start_time = datetime.now()
        try:
            logger.debug(f"[评估阶段] 样本 {sample_num} 开始调用eval_service.evaluate()")
            eval_result = eval_service.evaluate(
                translation=trans["translation"],
                reference=reference_text,
                source=trans["source"],
                mqm_score=trans.get("mqm_score")
            )
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            if eval_result:
                logger.info(f"[评估阶段] 样本 {sample_num} 评估完成，耗时 {elapsed_time:.2f} 秒")
                logger.info(f"[评估阶段] 样本 {sample_num} 综合评分: {eval_result.get('final_score', 0):.4f}")
                logger.debug(f"[评估阶段] 样本 {sample_num} 详细评分: BLEU={eval_result.get('bleu', 0):.4f}, "
                           f"COMET={eval_result.get('comet', 0):.4f}, "
                           f"BLEURT={eval_result.get('bleurt', 0):.4f}, "
                           f"BERTScore={eval_result.get('bertscore_f1', 0):.4f}, "
                           f"ChrF={eval_result.get('chrf', 0):.4f}")
                
                result_dict = {
                    "index": trans["index"],
                    "evaluation": eval_result,
                    "error": None,
                    "evaluation_time": elapsed_time
                }
                results.append(result_dict)
                
                # 实时写入评估结果
                if eval_writer:
                    eval_writer.write_evaluation(result_dict)
                
                print(f"综合评分: {eval_result['final_score']:.4f}")
            else:
                logger.error(f"[评估阶段] 样本 {sample_num} 评估失败: 返回结果为空")
                result_dict = {
                    "index": trans["index"],
                    "evaluation": None,
                    "error": "评估失败",
                    "evaluation_time": elapsed_time
                }
                results.append(result_dict)
                
                # 实时写入失败结果
                if eval_writer:
                    eval_writer.write_evaluation(result_dict)
                
                print("[ERROR] 评估失败")
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            logger.error(f"[评估阶段] 样本 {sample_num} 评估异常，耗时 {elapsed_time:.2f} 秒: {error_msg}")
            logger.exception(f"[评估阶段] 样本 {sample_num} 异常详情:")
            print(f"[ERROR] 评估异常: {e}")
            
            result_dict = {
                "index": trans["index"],
                "evaluation": None,
                "error": error_msg,
                "evaluation_time": elapsed_time
            }
            results.append(result_dict)
            
            # 实时写入异常结果
            if eval_writer:
                eval_writer.write_evaluation(result_dict)
    
    # 统计评估结果
    successful = sum(1 for r in results if r.get("evaluation") is not None)
    failed = total - successful
    logger.info(f"[评估阶段] 批量评估完成: 成功={successful}, 失败={failed}, 总计={total}")
    print(f"\n[评估阶段] 批量评估完成: 成功={successful}, 失败={failed}, 总计={total}")
    
    return results


class EvaluationTempWriter:
    """实时写入评估结果到临时文件（每句评估完成立即写入）"""
    
    def __init__(self, lang_code: str, output_dir: Path, translation_temp_file: Path, run_timestamp: str):
        """
        初始化评估临时文件写入器
        
        Args:
            lang_code: 语言代码
            output_dir: 输出目录
            translation_temp_file: 对应的翻译临时文件路径
            run_timestamp: 本次运行的时间戳（格式：temp_YYYYMMDDHHMMSS）
        """
        self.lang_code = lang_code
        self.lang_name = LANG_NAMES.get(lang_code, lang_code)
        self.translation_temp_file = translation_temp_file
        self.run_timestamp = run_timestamp
        
        # 创建临时保存目录（使用统一的时间戳子目录，避免覆盖）
        temp_dir = output_dir / "evaluations_temp" / run_timestamp
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建临时文件（JSON Lines格式，每行一个JSON对象）
        # 文件名格式：evaluations_{lang_code}.jsonl（不再包含时间戳，因为已经在目录名中）
        self.temp_file = temp_dir / f"evaluations_{lang_code}.jsonl"
        self.metadata_file = temp_dir / f"evaluations_{lang_code}.meta.json"
        
        # 检查是否已有评估文件（用于恢复）
        self.existing_evaluations = self._load_existing_evaluations()
        self.evaluated_indices = set(eval_data["index"] for eval_data in self.existing_evaluations)
        
        # 写入元数据文件
        metadata = {
            "language": self.lang_name,
            "lang_code": lang_code,
            "run_timestamp": run_timestamp,
            "translation_temp_file": str(translation_temp_file),
            "status": "evaluating",
            "evaluated_count": len(self.evaluated_indices)
        }
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 打开临时文件（追加模式）
        self.file_handle = open(self.temp_file, 'a', encoding='utf-8')
        self.written_count = len(self.existing_evaluations)
        
        if self.existing_evaluations:
            logger.info(f"[实时保存] 检测到已有评估结果: {len(self.existing_evaluations)} 条，将从中断点继续")
            print(f"[恢复] 检测到已有评估结果: {len(self.existing_evaluations)} 条，将从中断点继续")
        
        logger.info(f"[实时保存] 初始化评估临时文件写入器: {self.temp_file}")
        logger.info(f"[实时保存] 元数据文件: {self.metadata_file}")
    
    def _load_existing_evaluations(self) -> List[Dict]:
        """加载已有的评估结果（用于恢复）"""
        existing = []
        
        # 首先尝试加载新格式文件（evaluations_{lang_code}.jsonl）
        if self.temp_file.exists():
            try:
                with open(self.temp_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            eval_data = json.loads(line)
                            existing.append(eval_data)
                        except json.JSONDecodeError:
                            continue
                logger.info(f"[恢复] 从新格式文件加载了 {len(existing)} 条评估结果")
                return existing
            except Exception as e:
                logger.warning(f"[恢复] 加载新格式文件失败: {e}")
        
        # 如果新格式文件不存在，尝试查找旧格式文件（evaluations_{lang_code}_{timestamp}.jsonl）
        import re
        temp_dir = self.temp_file.parent
        if temp_dir.exists():
            # 查找所有匹配的旧格式文件
            pattern = re.compile(rf'evaluations_{re.escape(self.lang_code)}_\d{{8}}_\d{{6}}\.jsonl')
            for file in temp_dir.glob(f"evaluations_{self.lang_code}_*.jsonl"):
                if pattern.match(file.name):
                    logger.info(f"[恢复] 发现旧格式评估文件: {file.name}")
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    eval_data = json.loads(line)
                                    existing.append(eval_data)
                                except json.JSONDecodeError:
                                    continue
                        logger.info(f"[恢复] 从旧格式文件加载了 {len(existing)} 条评估结果")
                        # 如果找到旧格式文件，将其重命名为新格式（避免下次再查找）
                        if existing:
                            try:
                                file.rename(self.temp_file)
                                logger.info(f"[恢复] 已将旧格式文件重命名为新格式: {self.temp_file.name}")
                            except Exception as e:
                                logger.warning(f"[恢复] 重命名文件失败: {e}")
                        return existing
                    except Exception as e:
                        logger.warning(f"[恢复] 加载旧格式文件失败: {e}")
        
        return existing
    
    def is_evaluated(self, index: int) -> bool:
        """检查指定索引的样本是否已评估"""
        return index in self.evaluated_indices
    
    def get_existing_evaluation(self, index: int) -> Optional[Dict]:
        """获取已有的评估结果"""
        for eval_data in self.existing_evaluations:
            if eval_data.get("index") == index:
                return eval_data
        return None
    
    def write_evaluation(self, evaluation_result: Dict):
        """
        实时写入一条评估结果
        
        Args:
            evaluation_result: 评估结果字典
        """
        try:
            # 构建要保存的数据
            eval_data = {
                "index": evaluation_result["index"],
                "evaluation": evaluation_result.get("evaluation"),
                "error": evaluation_result.get("error"),
                "evaluation_time": evaluation_result.get("evaluation_time"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 写入JSON Lines格式（每行一个JSON对象）
            json_line = json.dumps(eval_data, ensure_ascii=False)
            self.file_handle.write(json_line + '\n')
            self.file_handle.flush()  # 立即刷新到磁盘
            
            self.written_count += 1
            self.evaluated_indices.add(evaluation_result["index"])
            
            sample_num = evaluation_result["index"] + 1
            logger.debug(f"[实时保存] 样本 {sample_num} 评估结果已写入临时文件")
            
        except Exception as e:
            logger.error(f"[实时保存] 写入评估结果失败: {e}")
            logger.exception(f"[实时保存] 异常详情:")
    
    def finalize(self):
        """
        完成写入，关闭文件并更新元数据
        """
        try:
            # 关闭文件
            if self.file_handle:
                self.file_handle.close()
            
            # 更新元数据
            metadata = {
                "language": self.lang_name,
                "lang_code": self.lang_code,
                "run_timestamp": self.run_timestamp,
                "translation_temp_file": str(self.translation_temp_file),
                "written_samples": self.written_count,
                "status": "completed",
                "temp_file": str(self.temp_file)
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[实时保存] {self.lang_name} 评估结果写入完成: {self.written_count} 条, 文件={self.temp_file}")
            print(f"[实时保存] 评估结果已保存: {self.written_count} 条")
            
        except Exception as e:
            logger.error(f"[实时保存] 完成写入时出错: {e}")
            logger.exception(f"[实时保存] 异常详情:")
    
    def get_temp_file(self) -> Path:
        """获取临时文件路径"""
        return self.temp_file
    
    def get_all_evaluations(self) -> List[Dict]:
        """获取所有已评估的结果（包括已有的和新增的）"""
        return self.existing_evaluations


class TranslationTempWriter:
    """实时写入翻译结果到临时文件（每句翻译完成立即写入）"""
    
    def __init__(self, lang_code: str, output_dir: Path, references: List[str], run_timestamp: str):
        """
        初始化临时文件写入器
        
        Args:
            lang_code: 语言代码
            output_dir: 输出目录
            references: 参考翻译列表
            run_timestamp: 本次运行的时间戳（格式：temp_YYYYMMDDHHMMSS）
        """
        self.lang_code = lang_code
        self.lang_name = LANG_NAMES.get(lang_code, lang_code)
        self.references = references
        self.total_samples = len(references)
        self.run_timestamp = run_timestamp
        
        # 创建临时保存目录（使用统一的时间戳子目录，避免覆盖）
        temp_dir = output_dir / "translations_temp" / run_timestamp
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建临时文件（JSON Lines格式，每行一个JSON对象）
        # 文件名格式：translations_{lang_code}.jsonl（不再包含时间戳，因为已经在目录名中）
        self.temp_file = temp_dir / f"translations_{lang_code}.jsonl"
        self.metadata_file = temp_dir / f"translations_{lang_code}.meta.json"
        
        # 写入元数据文件
        metadata = {
            "language": self.lang_name,
            "lang_code": lang_code,
            "run_timestamp": run_timestamp,
            "total_samples": self.total_samples,
            "status": "translating"
        }
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 打开临时文件（追加模式）
        self.file_handle = open(self.temp_file, 'a', encoding='utf-8')
        self.written_count = 0
        
        logger.info(f"[实时保存] 初始化临时文件写入器: {self.temp_file}")
        logger.info(f"[实时保存] 元数据文件: {self.metadata_file}")
    
    def write_translation(self, translation_result: Dict):
        """
        实时写入一条翻译结果
        
        Args:
            translation_result: 翻译结果字典
        """
        try:
            # 构建要保存的数据
            trans_data = {
                "index": translation_result["index"],
                "source": translation_result["source"],
                "translation": translation_result.get("translation"),
                "reference": self.references[translation_result["index"]] if translation_result["index"] < len(self.references) else None,
                "mqm_score": translation_result.get("mqm_score"),
                "error": translation_result.get("error"),
                "translation_time": translation_result.get("translation_time"),
                "timestamp": datetime.now().isoformat()
            }
            
            # 写入JSON Lines格式（每行一个JSON对象）
            json_line = json.dumps(trans_data, ensure_ascii=False)
            self.file_handle.write(json_line + '\n')
            self.file_handle.flush()  # 立即刷新到磁盘
            
            self.written_count += 1
            
            sample_num = translation_result["index"] + 1
            logger.debug(f"[实时保存] 样本 {sample_num}/{self.total_samples} 已写入临时文件")
            
        except Exception as e:
            logger.error(f"[实时保存] 写入翻译结果失败: {e}")
            logger.exception(f"[实时保存] 异常详情:")
    
    def finalize(self):
        """
        完成写入，关闭文件并更新元数据
        """
        try:
            # 关闭文件
            if self.file_handle:
                self.file_handle.close()
            
            # 更新元数据
            metadata = {
                "language": self.lang_name,
                "lang_code": self.lang_code,
                "run_timestamp": self.run_timestamp,
                "total_samples": self.total_samples,
                "written_samples": self.written_count,
                "status": "completed",
                "temp_file": str(self.temp_file)
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[实时保存] {self.lang_name} 翻译结果写入完成: {self.written_count}/{self.total_samples}, 文件={self.temp_file}")
            print(f"[实时保存] 翻译结果已保存: {self.written_count}/{self.total_samples} 条")
            
        except Exception as e:
            logger.error(f"[实时保存] 完成写入时出错: {e}")
            logger.exception(f"[实时保存] 异常详情:")
    
    def get_temp_file(self) -> Path:
        """获取临时文件路径"""
        return self.temp_file


def load_evaluations_temp(temp_file: Path) -> List[Dict]:
    """
    从临时文件加载评估结果（支持JSON Lines格式）
    
    Args:
        temp_file: 临时文件路径（.jsonl格式）
        
    Returns:
        List[Dict]: 评估结果列表
    """
    logger.info(f"[加载评估结果] 从临时文件加载: {temp_file}")
    
    if not temp_file.exists():
        return []
    
    evaluations = []
    
    # 读取JSON Lines格式文件
    with open(temp_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                eval_data = json.loads(line)
                evaluations.append(eval_data)
            except json.JSONDecodeError as e:
                logger.warning(f"[加载评估结果] 解析JSON行失败: {e}, 行内容: {line[:100]}")
                continue
    
    logger.info(f"[加载评估结果] 已加载 {len(evaluations)} 条评估结果")
    
    return evaluations


def load_translations_temp(temp_file: Path) -> tuple:
    """
    从临时文件加载翻译结果（支持JSON Lines格式）
    
    Args:
        temp_file: 临时文件路径（.jsonl格式）
        
    Returns:
        tuple: (translations, references, metadata)
    """
    logger.info(f"[加载翻译结果] 从临时文件加载: {temp_file}")
    
    if not temp_file.exists():
        raise FileNotFoundError(f"临时文件不存在: {temp_file}")
    
    translations = []
    references = []
    
    # 读取JSON Lines格式文件
    with open(temp_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                trans_data = json.loads(line)
                translations.append({
                    "index": trans_data["index"],
                    "source": trans_data["source"],
                    "translation": trans_data.get("translation"),
                    "mqm_score": trans_data.get("mqm_score"),
                    "error": trans_data.get("error"),
                    "translation_time": trans_data.get("translation_time")
                })
                if trans_data.get("reference"):
                    references.append(trans_data["reference"])
            except json.JSONDecodeError as e:
                logger.warning(f"[加载翻译结果] 解析JSON行失败: {e}, 行内容: {line[:100]}")
                continue
    
    # 尝试读取元数据文件
    metadata_file = temp_file.parent / f"{temp_file.stem}.meta.json"
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(f"[加载翻译结果] 读取元数据文件失败: {e}")
    
    # 如果没有元数据，从文件名推断
    if not metadata:
        import re
        # 支持两种文件名格式：
        # 1. 新格式：translations_{lang_code}.jsonl（在时间戳子目录中）
        # 2. 旧格式：translations_{lang_code}_{timestamp}.jsonl（兼容旧文件）
        match = re.search(r'translations_(\w+)(?:_(\d{8}_\d{6}))?\.jsonl', temp_file.name)
        if match:
            lang_code = match.group(1)
            timestamp = match.group(2) if match.group(2) else None
            metadata = {
                "lang_code": lang_code,
                "language": LANG_NAMES.get(lang_code, lang_code),
                "total_samples": len(translations)
            }
            if timestamp:
                metadata["timestamp"] = timestamp
            # 尝试从父目录名提取时间戳
            parent_name = temp_file.parent.name
            if parent_name.startswith("temp_"):
                metadata["run_timestamp"] = parent_name
    
    logger.info(f"[加载翻译结果] 已加载 {len(translations)} 条翻译结果")
    
    return translations, references, metadata


def generate_summary_report(
    all_results: Dict[str, Dict],
    output_dir: Path,
    eval_result_dir: Optional[Path] = None
):
    """
    生成汇总分析报告（包含所有语言对的对比分析）
    
    Args:
        all_results: 所有语言的结果字典，格式：
            {
                "lang_code": {
                    "lang_name": "语言名称",
                    "translations": [...],
                    "evaluations": [...],
                    "metadata": {...}
                }
            }
        output_dir: 输出目录（基础目录）
        eval_result_dir: 评估结果子目录（如果为None，则保存到output_dir）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 确定保存目录
    if eval_result_dir:
        save_dir = eval_result_dir
        save_dir.mkdir(parents=True, exist_ok=True)
    else:
        save_dir = output_dir
    
    summary_path = save_dir / f"flores_summary_{timestamp}.md"
    
    logger.info(f"[汇总报告] 开始生成汇总分析报告...")
    print(f"\n[汇总报告] 生成汇总分析报告...")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# FLORES数据集批量评估汇总报告\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**评估语言对**: {len(all_results)} 个\n\n")
        
        # 统计所有语言的数据
        lang_stats = []
        for lang_code, lang_data in all_results.items():
            lang_name = lang_data["lang_name"]
            translations = lang_data["translations"]
            evaluations = lang_data["evaluations"]
            
            # 计算统计信息
            successful = sum(1 for e in evaluations if e.get("evaluation") is not None)
            total = len(evaluations)
            
            if successful > 0:
                # 提取所有评分
                eval_scores = [e["evaluation"] for e in evaluations if e.get("evaluation")]
                
                # 计算各指标平均值
                metrics_data = {}
                metric_names = ["bleu", "comet", "bleurt", "bertscore_f1", "chrf", "final_score"]
                mqm_metrics = ["adequacy", "fluency", "overall", "terminology"]
                
                for metric in metric_names:
                    scores = [e.get(metric, 0) for e in eval_scores if e.get(metric, 0) > 0]
                    if scores:
                        metrics_data[metric] = {
                            "avg": sum(scores) / len(scores),
                            "count": len(scores)
                        }
                    else:
                        metrics_data[metric] = {"avg": 0.0, "count": 0}
                
                # MQM评分（从translations中提取）
                mqm_data = {}
                for mqm_metric in mqm_metrics:
                    mqm_scores = []
                    for trans in translations:
                        if trans.get("mqm_score") and trans["mqm_score"].get(mqm_metric):
                            mqm_scores.append(trans["mqm_score"][mqm_metric])
                    if mqm_scores:
                        mqm_data[mqm_metric] = sum(mqm_scores) / len(mqm_scores)
                    else:
                        mqm_data[mqm_metric] = 0.0
                
                lang_stats.append({
                    "lang_code": lang_code,
                    "lang_name": lang_name,
                    "total": total,
                    "successful": successful,
                    "metrics": metrics_data,
                    "mqm": mqm_data
                })
        
        # 评分汇总表
        f.write("## 评分汇总表\n\n")
        f.write("| 源语言 | 目标语言 | BLEU | COMET | BERTScore F1 | BLEURT | ChrF | 综合评分 | ")
        f.write("MQM_ADEQUACY | MQM_FLUENCY | MQM_OVERALL | MQM_TERMINOLOGY |\n")
        f.write("|---------|----------|------|-------|--------------|--------|------|----------|")
        f.write("-------------|-------------|-------------|----------------|\n")
        
        for stat in lang_stats:
            metrics = stat["metrics"]
            mqm = stat["mqm"]
            f.write(f"| {stat['lang_name']} | 中文 | ")
            f.write(f"{metrics['bleu']['avg']:.4f} | ")
            f.write(f"{metrics['comet']['avg']:.4f} | " if metrics['comet']['count'] > 0 else "0.0000 | ")
            f.write(f"{metrics['bertscore_f1']['avg']:.4f} | ")
            f.write(f"{metrics['bleurt']['avg']:.4f} | " if metrics['bleurt']['count'] > 0 else "0.0000 | ")
            f.write(f"{metrics['chrf']['avg']:.4f} | ")
            f.write(f"{metrics['final_score']['avg']:.4f} | ")
            f.write(f"{mqm['adequacy']:.4f} | ")
            f.write(f"{mqm['fluency']:.4f} | ")
            f.write(f"{mqm['overall']:.4f} | ")
            f.write(f"{mqm['terminology']:.4f} |\n")
        
        # 计算总体平均值（使用加权平均，按各语言的样本数加权）
        if lang_stats:
            # 计算加权平均值：sum(平均值 * 样本数) / sum(样本数)
            total_bleu_weighted = sum(s["metrics"]["bleu"]["avg"] * s["metrics"]["bleu"]["count"] for s in lang_stats)
            total_bleu_count = sum(s["metrics"]["bleu"]["count"] for s in lang_stats)
            total_bleu = total_bleu_weighted / total_bleu_count if total_bleu_count > 0 else 0.0
            
            total_comet_weighted = sum(s["metrics"]["comet"]["avg"] * s["metrics"]["comet"]["count"] for s in lang_stats if s["metrics"]["comet"]["count"] > 0)
            total_comet_count = sum(s["metrics"]["comet"]["count"] for s in lang_stats if s["metrics"]["comet"]["count"] > 0)
            total_comet_avg = total_comet_weighted / total_comet_count if total_comet_count > 0 else 0.0
            
            total_bertscore_weighted = sum(s["metrics"]["bertscore_f1"]["avg"] * s["metrics"]["bertscore_f1"]["count"] for s in lang_stats)
            total_bertscore_count = sum(s["metrics"]["bertscore_f1"]["count"] for s in lang_stats)
            total_bertscore = total_bertscore_weighted / total_bertscore_count if total_bertscore_count > 0 else 0.0
            
            total_bleurt_weighted = sum(s["metrics"]["bleurt"]["avg"] * s["metrics"]["bleurt"]["count"] for s in lang_stats if s["metrics"]["bleurt"]["count"] > 0)
            total_bleurt_count = sum(s["metrics"]["bleurt"]["count"] for s in lang_stats if s["metrics"]["bleurt"]["count"] > 0)
            total_bleurt_avg = total_bleurt_weighted / total_bleurt_count if total_bleurt_count > 0 else 0.0
            
            total_chrf_weighted = sum(s["metrics"]["chrf"]["avg"] * s["metrics"]["chrf"]["count"] for s in lang_stats)
            total_chrf_count = sum(s["metrics"]["chrf"]["count"] for s in lang_stats)
            total_chrf = total_chrf_weighted / total_chrf_count if total_chrf_count > 0 else 0.0
            
            total_final_weighted = sum(s["metrics"]["final_score"]["avg"] * s["metrics"]["final_score"]["count"] for s in lang_stats)
            total_final_count = sum(s["metrics"]["final_score"]["count"] for s in lang_stats)
            total_final = total_final_weighted / total_final_count if total_final_count > 0 else 0.0
            
            # MQM评分使用简单平均（因为各语言的MQM评分可能相同）
            total_mqm_adeq = sum(s["mqm"]["adequacy"] for s in lang_stats) / len(lang_stats)
            total_mqm_flue = sum(s["mqm"]["fluency"] for s in lang_stats) / len(lang_stats)
            total_mqm_over = sum(s["mqm"]["overall"] for s in lang_stats) / len(lang_stats)
            total_mqm_term = sum(s["mqm"]["terminology"] for s in lang_stats) / len(lang_stats)
            
            f.write("| **总计平均** | 中文 | ")
            f.write(f"**{total_bleu:.4f}** | ")
            f.write(f"**{total_comet_avg:.4f}** | " if total_comet_count > 0 else "**0.0000** | ")
            f.write(f"**{total_bertscore:.4f}** | ")
            f.write(f"**{total_bleurt_avg:.4f}** | " if total_bleurt_count > 0 else "**0.0000** | ")
            f.write(f"**{total_chrf:.4f}** | ")
            f.write(f"**{total_final:.4f}** | ")
            f.write(f"**{total_mqm_adeq:.4f}** | ")
            f.write(f"**{total_mqm_flue:.4f}** | ")
            f.write(f"**{total_mqm_over:.4f}** | ")
            f.write(f"**{total_mqm_term:.4f}** |\n")
        
        f.write("\n")
        
        # 各语言详细统计
        f.write("## 各语言详细统计\n\n")
        for stat in lang_stats:
            f.write(f"### {stat['lang_name']} → 中文\n\n")
            f.write(f"- **总样本数**: {stat['total']}\n")
            f.write(f"- **成功评估**: {stat['successful']}/{stat['total']}\n")
            f.write(f"- **成功率**: {stat['successful']/stat['total']*100:.2f}%\n\n")
            
            f.write("**各指标详情**:\n\n")
            metrics = stat["metrics"]
            f.write(f"- BLEU: {metrics['bleu']['avg']:.4f} (有效样本: {metrics['bleu']['count']})\n")
            if metrics['comet']['count'] > 0:
                f.write(f"- COMET: {metrics['comet']['avg']:.4f} (有效样本: {metrics['comet']['count']})\n")
            f.write(f"- BERTScore F1: {metrics['bertscore_f1']['avg']:.4f} (有效样本: {metrics['bertscore_f1']['count']})\n")
            if metrics['bleurt']['count'] > 0:
                f.write(f"- BLEURT: {metrics['bleurt']['avg']:.4f} (有效样本: {metrics['bleurt']['count']})\n")
            f.write(f"- ChrF: {metrics['chrf']['avg']:.4f} (有效样本: {metrics['chrf']['count']})\n")
            f.write(f"- 综合评分: {metrics['final_score']['avg']:.4f}\n\n")
            
            f.write("**MQM评分**:\n\n")
            mqm = stat["mqm"]
            f.write(f"- 充分性 (Adequacy): {mqm['adequacy']:.4f}\n")
            f.write(f"- 流畅性 (Fluency): {mqm['fluency']:.4f}\n")
            f.write(f"- 总体 (Overall): {mqm['overall']:.4f}\n")
            f.write(f"- 术语 (Terminology): {mqm['terminology']:.4f}\n\n")
            f.write("---\n\n")
        
        # 总体统计
        f.write("## 总体统计\n\n")
        total_samples = sum(s["total"] for s in lang_stats)
        total_successful = sum(s["successful"] for s in lang_stats)
        f.write(f"- **总样本数**: {total_samples}\n")
        f.write(f"- **成功评估**: {total_successful}/{total_samples}\n")
        f.write(f"- **总体成功率**: {total_successful/total_samples*100:.2f}%\n")
        f.write(f"- **评估语言对数**: {len(lang_stats)}\n\n")
    
    logger.info(f"[汇总报告] 汇总分析报告已保存: {summary_path}")
    print(f"[OK] 汇总分析报告已保存: {summary_path}")
    return summary_path


def save_results(
    lang_code: str,
    translations: List[Dict],
    evaluations: List[Dict],
    output_dir: Path,
    metadata: Optional[Dict] = None,
    eval_result_dir: Optional[Path] = None
):
    """
    保存最终结果（阶段2：评估完成后保存）
    
    Args:
        lang_code: 语言代码
        translations: 翻译结果列表
        evaluations: 评估结果列表
        output_dir: 输出目录（基础目录）
        metadata: 元数据
        eval_result_dir: 评估结果子目录（如果为None，则保存到output_dir）
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lang_name = LANG_NAMES.get(lang_code, lang_code)
    
    # 确定保存目录
    if eval_result_dir:
        save_dir = eval_result_dir
        save_dir.mkdir(parents=True, exist_ok=True)
    else:
        save_dir = output_dir
    
    logger.info(f"[保存最终结果] 开始保存 {lang_name} 的最终结果...")
    logger.info(f"[保存最终结果] 保存目录: {save_dir}")
    
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
    json_path = save_dir / f"flores_{lang_code}_{timestamp}.json"
    logger.debug(f"[保存结果] 保存JSON文件: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "language": lang_name,
            "lang_code": lang_code,
            "timestamp": timestamp,
            "total_samples": len(combined_results),
            "results": combined_results
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"[保存结果] JSON文件已保存: {json_path}")
    
    # 保存Markdown报告
    md_path = save_dir / f"flores_{lang_code}_{timestamp}.md"
    logger.debug(f"[保存结果] 保存Markdown报告: {md_path}")
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
    
    logger.info(f"[保存结果] Markdown报告已保存: {md_path}")
    logger.info(f"[保存结果] {lang_name} 结果保存完成: 成功评估={successful}/{len(combined_results)}")
    print(f"\n[OK] 结果已保存:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="FLORES数据集批量翻译和评估脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 完整流程（翻译+评估）
  python evaluate_flores_batch.py
  
  # 仅评估已有翻译结果（指定单个文件）
  python evaluate_flores_batch.py --eval-only results/flores_evaluation/translations_temp/translations_en_20251212_102241.jsonl
  
  # 仅评估已有翻译结果（指定目录，自动查找所有.jsonl文件）
  python evaluate_flores_batch.py --eval-only results/flores_evaluation/translations_temp/
  
  # 仅评估已有翻译结果（指定多个文件）
  python evaluate_flores_batch.py --eval-only file1.jsonl file2.jsonl file3.jsonl
        """
    )
    
    parser.add_argument(
        '--eval-only',
        nargs='+',
        type=str,
        help='仅评估模式：指定要评估的翻译结果文件路径（.jsonl格式）或目录。可以指定多个文件或一个目录（会自动查找所有.jsonl文件）'
    )
    
    parser.add_argument(
        '--languages',
        nargs='+',
        type=str,
        default=["en", "de", "vi", "km", "ms"],
        help='要测试的语言代码列表（默认: en de vi km ms）'
    )
    
    parser.add_argument(
        '--dataset-type',
        type=str,
        default="dev",
        choices=["dev", "devtest"],
        help='数据集类型（默认: dev）'
    )
    
    parser.add_argument(
        '--max-samples',
        type=int,
        default=50,
        help='每种语言最多测试的样本数（默认: 50）'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='每批翻译的样本数（默认: 10）'
    )
    
    return parser.parse_args()


def find_translation_files(paths: List[str]) -> Dict[str, Path]:
    """
    查找翻译结果文件
    
    Args:
        paths: 文件路径或目录路径列表
        
    Returns:
        Dict[str, Path]: 语言代码到文件路径的映射
    """
    translation_files = {}
    
    for path_str in paths:
        # 处理相对路径，转换为绝对路径
        path = Path(path_str)
        if not path.is_absolute():
            # 如果是相对路径，相对于脚本所在目录
            path = Path(__file__).parent / path
        
        if not path.exists():
            logger.warning(f"路径不存在，跳过: {path}")
            continue
        
        if path.is_file():
            # 单个文件
            if path.suffix == '.jsonl':
                # 从文件名提取语言代码
                # 支持两种格式:
                # 1. 新格式: translations_{lang_code}.jsonl（在时间戳子目录中）
                # 2. 旧格式: translations_{lang_code}_{timestamp}.jsonl（兼容旧文件）
                import re
                match = re.search(r'translations_(\w+)(?:_\d{8}_\d{6})?\.jsonl', path.name)
                if match:
                    lang_code = match.group(1)
                    translation_files[lang_code] = path
                    logger.info(f"找到翻译文件: {lang_code} -> {path}")
                else:
                    logger.warning(f"无法从文件名提取语言代码: {path.name}")
            else:
                logger.warning(f"不是.jsonl文件，跳过: {path}")
        
        elif path.is_dir():
            # 目录，递归查找所有.jsonl文件（支持时间戳子目录）
            # 使用 ** 进行递归查找
            jsonl_files = list(path.rglob("translations_*.jsonl"))
            
            if not jsonl_files:
                logger.warning(f"目录中没有找到翻译文件: {path}")
                logger.debug(f"搜索路径: {path.absolute()}")
                # 列出目录内容以便调试
                try:
                    dir_contents = list(path.iterdir())
                    logger.debug(f"目录内容: {[str(p.name) for p in dir_contents]}")
                except Exception as e:
                    logger.debug(f"无法列出目录内容: {e}")
                continue
            
            logger.info(f"在目录 {path} 中找到 {len(jsonl_files)} 个翻译文件")
            
            for jsonl_file in jsonl_files:
                import re
                # 支持两种文件名格式：
                # 1. 新格式：translations_{lang_code}.jsonl（在时间戳子目录中）
                # 2. 旧格式：translations_{lang_code}_{timestamp}.jsonl（兼容旧文件）
                match = re.search(r'translations_(\w+)(?:_\d{8}_\d{6})?\.jsonl', jsonl_file.name)
                if match:
                    lang_code = match.group(1)
                    if lang_code in translation_files:
                        # 如果同一语言有多个文件，选择最新的（时间戳最大的）
                        existing_file = translation_files[lang_code]
                        logger.warning(f"语言 {lang_code} 有多个文件:")
                        logger.warning(f"  - 已有: {existing_file}")
                        logger.warning(f"  - 新发现: {jsonl_file}")
                        # 比较文件修改时间，选择最新的
                        if jsonl_file.stat().st_mtime > existing_file.stat().st_mtime:
                            translation_files[lang_code] = jsonl_file
                            logger.info(f"使用更新的文件: {lang_code} -> {jsonl_file}")
                        else:
                            logger.info(f"保留已有文件: {lang_code} -> {existing_file}")
                    else:
                        translation_files[lang_code] = jsonl_file
                        logger.info(f"找到翻译文件: {lang_code} -> {jsonl_file}")
    
    return translation_files


async def main():
    """主函数"""
    global logger
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 初始化日志系统（必须在最开始）
    logger = setup_logging()
    
    # 配置参数
    LANGUAGES = args.languages
    DATASET_TYPE = args.dataset_type
    MAX_SAMPLES = args.max_samples
    BATCH_SIZE = args.batch_size
    EVAL_ONLY = args.eval_only
    
    logger.info("=" * 80)
    logger.info("FLORES数据集批量翻译和评估")
    logger.info("=" * 80)
    logger.info(f"测试语言: {[LANG_NAMES.get(l, l) for l in LANGUAGES]}")
    logger.info(f"数据集类型: {DATASET_TYPE}")
    logger.info(f"每种语言样本数: {MAX_SAMPLES}")
    logger.info(f"批次大小: {BATCH_SIZE}")
    logger.info("=" * 80)
    
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
    logger.info(f"输出目录: {output_dir}")
    
    # 生成本次运行的统一时间戳（格式：temp_YYYYMMDDHHMMSS）
    run_timestamp = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"本次运行时间戳: {run_timestamp}")
    
    # 如果指定了 --eval-only，跳过翻译阶段
    temp_files = {}  # 保存临时文件路径
    
    if EVAL_ONLY:
        # 仅评估模式：从指定文件加载翻译结果
        logger.info("=" * 80)
        logger.info("仅评估模式：跳过翻译阶段")
        logger.info("=" * 80)
        print("\n" + "=" * 80)
        print("仅评估模式：跳过翻译阶段")
        print("=" * 80)
        
        # 查找翻译文件
        logger.info(f"[仅评估模式] 查找翻译结果文件...")
        print(f"\n[仅评估模式] 查找翻译结果文件...")
        temp_files = find_translation_files(EVAL_ONLY)
        
        if not temp_files:
            logger.error("[仅评估模式] 未找到任何翻译结果文件！")
            print("[ERROR] 未找到任何翻译结果文件！")
            print(f"请检查文件路径是否正确，或文件是否存在")
            return
        
        logger.info(f"[仅评估模式] 找到 {len(temp_files)} 个翻译结果文件:")
        print(f"[OK] 找到 {len(temp_files)} 个翻译结果文件:")
        for lang_code, file_path in temp_files.items():
            lang_name = LANG_NAMES.get(lang_code, lang_code)
            print(f"  - {lang_name} ({lang_code}): {file_path}")
        
        # 设置翻译开始时间为当前时间（用于计算总耗时）
        translation_start_time = datetime.now()
    
    else:
        # ========== 阶段1: 批量翻译 ==========
        logger.info("=" * 80)
        logger.info("阶段1: 批量翻译")
        logger.info("=" * 80)
        print("\n" + "=" * 80)
        print("阶段1: 批量翻译")
        print("=" * 80)
        
        # 创建翻译Pipeline
        logger.info("[阶段1] 初始化翻译Pipeline...")
        print("\n[阶段1] 初始化翻译Pipeline...")
        try:
            pipeline = create_pipeline()
            logger.info("翻译Pipeline已就绪")
            print("[OK] 翻译Pipeline已就绪")
        except Exception as e:
            logger.exception("翻译Pipeline初始化失败:")
            print(f"[ERROR] 翻译Pipeline初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 处理每种语言的翻译
        translation_start_time = datetime.now()
        
        for lang_idx, lang_code in enumerate(LANGUAGES, 1):
            lang_name = LANG_NAMES.get(lang_code, lang_code)
            lang_start_time = datetime.now()
            
            logger.info("=" * 80)
            logger.info(f"[阶段1] [语言 {lang_idx}/{len(LANGUAGES)}] 处理语言: {lang_name} ({lang_code})")
            logger.info("=" * 80)
            print(f"\n{'='*80}")
            print(f"[阶段1] 处理语言: {lang_name} ({lang_code})")
            print(f"{'='*80}")
            
            try:
                # 加载数据
                logger.info(f"[{lang_name}] 加载数据...")
                print(f"\n加载 {lang_name} 数据...")
                sources = load_flores_data(lang_code, DATASET_TYPE, MAX_SAMPLES)
                references = load_reference_translations(lang_code, DATASET_TYPE, MAX_SAMPLES)
                
                if len(sources) != len(references):
                    logger.warning(f"[{lang_name}] 源文本和参考翻译数量不匹配: {len(sources)} vs {len(references)}")
                    print(f"[WARN] 源文本和参考翻译数量不匹配: {len(sources)} vs {len(references)}")
                    min_len = min(len(sources), len(references))
                    sources = sources[:min_len]
                    references = references[:min_len]
                
                logger.info(f"[{lang_name}] 已加载 {len(sources)} 条样本")
                print(f"[OK] 已加载 {len(sources)} 条样本")
                
                # 创建实时写入器（传入统一的时间戳）
                temp_writer = TranslationTempWriter(lang_code, output_dir, references, run_timestamp)
                temp_files[lang_code] = temp_writer.get_temp_file()
                
                # 批量翻译（实时写入）
                logger.info(f"[{lang_name}] 开始批量翻译（批次大小: {BATCH_SIZE}，实时保存）...")
                print(f"\n开始批量翻译（批次大小: {BATCH_SIZE}，实时保存）...")
                translations = await translate_batch(
                    pipeline,
                    sources,
                    source_lang=lang_code,
                    target_lang="zh",
                    batch_size=BATCH_SIZE,
                    temp_writer=temp_writer  # 传入实时写入器
                )
                
                # 完成写入
                temp_writer.finalize()
                
                lang_elapsed = (datetime.now() - lang_start_time).total_seconds()
                logger.info(f"[{lang_name}] 翻译阶段完成，耗时 {lang_elapsed:.2f} 秒 ({lang_elapsed/60:.2f} 分钟)")
                print(f"[OK] {lang_name} 翻译完成，耗时 {lang_elapsed:.2f} 秒")
                
            except Exception as e:
                logger.exception(f"[{lang_name}] 翻译阶段出错:")
                print(f"[ERROR] 处理 {lang_name} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        translation_elapsed = (datetime.now() - translation_start_time).total_seconds()
        logger.info("=" * 80)
        logger.info(f"[阶段1] 所有语言翻译完成！总耗时: {translation_elapsed:.2f} 秒 ({translation_elapsed/60:.2f} 分钟)")
        logger.info("=" * 80)
        print(f"\n{'='*80}")
        print(f"[阶段1] 所有语言翻译完成！总耗时: {translation_elapsed:.2f} 秒 ({translation_elapsed/60:.2f} 分钟)")
        print(f"{'='*80}")
    
    # ========== 阶段2: 批量评估 ==========
    logger.info("=" * 80)
    logger.info("阶段2: 批量评估")
    logger.info("=" * 80)
    print("\n" + "=" * 80)
    print("阶段2: 批量评估")
    print("=" * 80)
    
    # 初始化评估服务
    logger.info("[阶段2] 初始化评估服务...")
    print("\n[阶段2] 初始化评估服务...")
    eval_service = None
    try:
        eval_service = create_evaluation_service()
        if not eval_service or not eval_service.is_available():
            logger.warning("评估服务不可用，将跳过评估阶段")
            print("[WARN] 评估服务不可用，将跳过评估阶段")
            print("[INFO] 翻译结果已保存在临时文件中，可以稍后手动评估")
        else:
            logger.info("评估服务已就绪")
            print("[OK] 评估服务已就绪")
    except Exception as e:
        logger.warning(f"评估服务初始化失败: {e}，将跳过评估阶段")
        print(f"[WARN] 评估服务初始化失败: {e}")
        print("[INFO] 翻译结果已保存在临时文件中，可以稍后手动评估")
    
    # 如果评估服务可用，进行批量评估
    if eval_service and eval_service.is_available():
        evaluation_start_time = datetime.now()
        all_evaluation_results = {}  # 保存所有语言的结果，用于生成汇总报告
        
        # 创建评估结果子目录（格式：eval_result_YYYYMMDDHHMMSS）
        eval_result_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        eval_result_dir = output_dir / "evaluation_results" / f"eval_result_{eval_result_timestamp}"
        eval_result_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[评估结果] 创建评估结果目录: {eval_result_dir}")
        print(f"[评估结果] 评估结果将保存到: {eval_result_dir}")
        
        # 确定要评估的语言列表
        if EVAL_ONLY:
            # 仅评估模式：使用找到的文件对应的语言
            eval_languages = list(temp_files.keys())
        else:
            # 完整流程：使用配置的语言列表
            eval_languages = LANGUAGES
        
        for lang_idx, lang_code in enumerate(eval_languages, 1):
            lang_name = LANG_NAMES.get(lang_code, lang_code)
            
            if lang_code not in temp_files:
                logger.warning(f"[{lang_name}] 未找到翻译结果临时文件，跳过评估")
                continue
            
            temp_file = temp_files[lang_code]
            lang_start_time = datetime.now()
            
            logger.info("=" * 80)
            logger.info(f"[阶段2] [语言 {lang_idx}/{len(eval_languages)}] 评估语言: {lang_name} ({lang_code})")
            logger.info("=" * 80)
            print(f"\n{'='*80}")
            print(f"[阶段2] 评估语言: {lang_name} ({lang_code})")
            print(f"{'='*80}")
            
            try:
                # 从临时文件加载翻译结果
                logger.info(f"[{lang_name}] 从临时文件加载翻译结果...")
                print(f"\n从临时文件加载翻译结果...")
                translations, references, metadata = load_translations_temp(temp_file)
                
                # 创建评估实时写入器（支持断点恢复，使用统一的时间戳）
                # 如果是从旧文件加载，尝试从文件路径提取时间戳
                eval_run_timestamp = run_timestamp
                if EVAL_ONLY:
                    # 尝试从翻译文件的父目录提取时间戳
                    parent_name = temp_file.parent.name
                    if parent_name.startswith("temp_"):
                        eval_run_timestamp = parent_name
                    else:
                        # 如果父目录不是时间戳格式，使用当前时间戳（新运行）
                        eval_run_timestamp = run_timestamp
                eval_writer = EvaluationTempWriter(lang_code, output_dir, temp_file, eval_run_timestamp)
                
                # 批量评估（实时写入，支持断点恢复）
                logger.info(f"[{lang_name}] 开始批量评估（实时保存，支持断点恢复）...")
                print(f"\n开始批量评估（实时保存，支持断点恢复）...")
                evaluations = await evaluate_batch(
                    eval_service,
                    translations,
                    references,
                    eval_writer=eval_writer  # 传入实时写入器
                )
                
                # 完成写入
                eval_writer.finalize()
                
                # 合并评估结果（确保顺序正确）
                # evaluations可能不包含已评估的结果，需要按index排序并填充
                evaluations_dict = {e["index"]: e for e in evaluations}
                sorted_evaluations = []
                for trans in translations:
                    idx = trans["index"]
                    if idx in evaluations_dict:
                        sorted_evaluations.append(evaluations_dict[idx])
                    else:
                        # 如果某个翻译没有对应的评估结果，创建一个空结果
                        sorted_evaluations.append({
                            "index": idx,
                            "evaluation": None,
                            "error": "未评估",
                            "evaluation_time": 0
                        })
                
                # 保存最终结果
                logger.info(f"[{lang_name}] 保存最终结果...")
                print(f"\n保存最终结果...")
                save_results(lang_code, translations, sorted_evaluations, output_dir, metadata, eval_result_dir)
                
                # 保存到汇总结果中
                all_evaluation_results[lang_code] = {
                    "lang_name": lang_name,
                    "translations": translations,
                    "evaluations": sorted_evaluations,
                    "metadata": metadata
                }
                
                lang_elapsed = (datetime.now() - lang_start_time).total_seconds()
                logger.info(f"[{lang_name}] 评估阶段完成，耗时 {lang_elapsed:.2f} 秒 ({lang_elapsed/60:.2f} 分钟)")
                print(f"[OK] {lang_name} 评估完成，耗时 {lang_elapsed:.2f} 秒")
                
            except Exception as e:
                logger.exception(f"[{lang_name}] 评估阶段出错:")
                print(f"[ERROR] 评估 {lang_name} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        evaluation_elapsed = (datetime.now() - evaluation_start_time).total_seconds()
        logger.info("=" * 80)
        logger.info(f"[阶段2] 所有语言评估完成！总耗时: {evaluation_elapsed:.2f} 秒 ({evaluation_elapsed/60:.2f} 分钟)")
        logger.info("=" * 80)
        print(f"\n{'='*80}")
        print(f"[阶段2] 所有语言评估完成！总耗时: {evaluation_elapsed:.2f} 秒 ({evaluation_elapsed/60:.2f} 分钟)")
        print(f"{'='*80}")
        
        # 生成汇总分析报告
        if all_evaluation_results:
            logger.info("=" * 80)
            logger.info("[汇总报告] 开始生成汇总分析报告...")
            logger.info("=" * 80)
            print(f"\n{'='*80}")
            print("[汇总报告] 生成汇总分析报告...")
            print(f"{'='*80}")
            try:
                summary_path = generate_summary_report(all_evaluation_results, output_dir, eval_result_dir)
                logger.info(f"[汇总报告] 汇总分析报告生成完成: {summary_path}")
                print(f"[OK] 汇总分析报告已生成: {summary_path}")
            except Exception as e:
                logger.exception(f"[汇总报告] 生成汇总报告时出错: {e}")
                print(f"[ERROR] 生成汇总报告时出错: {e}")
    else:
        logger.info("[阶段2] 评估服务不可用，跳过评估阶段")
        print("\n[阶段2] 评估服务不可用，跳过评估阶段")
        print("[INFO] 翻译结果已保存在以下临时文件中:")
        for lang_code, temp_file in temp_files.items():
            lang_name = LANG_NAMES.get(lang_code, lang_code)
            print(f"  - {lang_name}: {temp_file}")
    
    # 计算总耗时
    total_elapsed = (datetime.now() - translation_start_time).total_seconds()
    logger.info("=" * 80)
    logger.info(f"所有处理完成！总耗时: {total_elapsed:.2f} 秒 ({total_elapsed/60:.2f} 分钟)")
    logger.info("=" * 80)
    print(f"\n{'='*80}")
    print("所有处理完成！")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(main())

