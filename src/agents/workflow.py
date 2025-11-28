"""
工作流数据结构和中间结果
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class TaskType(Enum):
    """任务类型"""
    SENTENCE = "sentence"  # 句子级翻译
    PARAGRAPH = "paragraph"  # 段落级翻译
    DOUBLE_TRANSLATION = "double_translation"  # 需要双重翻译
    MULTI_REVIEW = "multi_review"  # 需要多重审核


@dataclass
class TaskPlan:
    """任务计划"""
    source_lang: str
    target_lang: str
    tasks: List[Dict[str, Any]]  # 任务列表，每个任务包含text, type, needs_double_translation, needs_multi_review等
    segments: List[Dict[str, Any]]  # 文本分段信息


@dataclass
class SelfCheckReport:
    """自检报告"""
    uncertain_segments: List[Dict[str, Any]]  # 不确定的段落，格式：{segment_id, text, reason}
    confidence_scores: Dict[str, float]  # 各段落的置信度分数
    suggestions: List[str]  # 建议


@dataclass
class TranslationDraft:
    """翻译草稿"""
    translated_text: str
    self_check_report: Optional[SelfCheckReport] = None
    model_name: str = ""
    segment_id: Optional[str] = None


@dataclass
class QualityScore:
    """质量评分（MQM简化版）"""
    adequacy: float  # 充分性 (0-1)
    fluency: float  # 流畅性 (0-1)
    terminology: float  # 术语准确性 (0-1)
    overall: float  # 总体评分


@dataclass
class CheckerReport:
    """检查报告"""
    consistent_segments: List[str]  # 一致的句子ID
    conflicting_segments: List[Dict[str, Any]]  # 冲突的句子，格式：{segment_id, translator_a_text, translator_b_text, issue}
    omissions: List[Dict[str, Any]]  # 遗漏，格式：{segment_id, missing_content}
    misinterpretations: List[Dict[str, Any]]  # 误解，格式：{segment_id, original_meaning, translated_meaning}
    quality_scores: Dict[str, QualityScore]  # 各段落的评分，key为segment_id


@dataclass
class StylistResult:
    """风格化结果"""
    styled_text: str
    terminology_changes: List[Dict[str, Any]]  # 术语变更，格式：{original, unified, reason}
    style_changes: List[Dict[str, Any]]  # 风格变更，格式：{segment_id, original, modified, reason}


@dataclass
class ExplainabilityReport:
    """可解释性报告"""
    modifications: List[Dict[str, Any]]  # 修改记录，格式：{stage, segment_id, original, modified, reason}
    quality_improvements: Dict[str, float]  # 质量改进，格式：{metric, before, after, improvement}
    final_quality_score: Optional[QualityScore] = None


@dataclass
class FinalTranslation:
    """最终翻译结果"""
    translated_text: str
    explainability_report: ExplainabilityReport
    source_lang: str
    target_lang: str
    processing_stages: List[str]  # 处理阶段列表

