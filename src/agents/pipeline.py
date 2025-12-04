"""
Translation Pipeline Orchestrator
翻译工作流编排器
"""

import asyncio
from typing import Optional, Dict, List
from src.agents.planner import TaskPlanner
from src.agents.translator_a import TranslatorA
from src.agents.translator_b import TranslatorB
from src.agents.checker import Checker
from src.agents.stylist import Stylist
from src.agents.aggregator import Aggregator
from src.agents.workflow import (
    TaskPlan, TranslationDraft, CheckerReport, StylistResult, FinalTranslation
)
from src.models.base import BaseModel


class TranslationPipeline:
    """翻译工作流编排器"""
    
    def __init__(
        self,
        planner_model: BaseModel,  # ChatGPT
        translator_a_model: BaseModel,  # Gemini
        translator_b_model: BaseModel,  # Qwen/DeepSeek
        checker_model: BaseModel,  # ChatGPT
        stylist_model: BaseModel,  # Qwen/DeepSeek
        aggregator_model: BaseModel,  # ChatGPT
        glossary: Optional[Dict[str, str]] = None,
        style: str = "general",
        verbose: bool = False  # 是否启用详细日志
    ):
        """
        初始化翻译工作流
        
        Args:
            planner_model: 任务规划模型
            translator_a_model: 主译模型
            translator_b_model: 对照译模型
            checker_model: 检查模型
            stylist_model: 风格化模型
            aggregator_model: 整合模型
            glossary: 术语表
            style: 风格类型
        """
        self.planner = TaskPlanner(planner_model)
        self.translator_a = TranslatorA(translator_a_model)
        self.translator_b = TranslatorB(translator_b_model)
        self.checker = Checker(checker_model)
        self.stylist = Stylist(stylist_model, glossary=glossary, style=style)
        self.aggregator = Aggregator(aggregator_model)
        self.verbose = verbose
    
    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "zh",
        glossary: Optional[Dict[str, str]] = None,
        style: Optional[str] = None
    ) -> FinalTranslation:
        """
        执行完整翻译流程
        
        Args:
            text: 待翻译文本
            source_lang: 源语言（None表示自动检测）
            target_lang: 目标语言
            glossary: 术语表（可选，会覆盖初始化时的术语表）
            style: 风格类型（可选，会覆盖初始化时的风格）
            
        Returns:
            FinalTranslation: 最终翻译结果
        """
        # 更新术语表和风格（如果提供）
        if glossary is not None:
            self.stylist.glossary = glossary
        if style is not None:
            self.stylist.style_type = style
        
        # 阶段1: 任务规划
        task_plan = await self.planner.plan(text, source_lang, target_lang)
        
        # 处理每个任务
        final_segments = []
        all_explainability_reports = []
        
        for task in task_plan.tasks:
            segment_id = task['segment_id']
            segment_text = task['text']
            needs_double = task.get('needs_double_translation', False)
            
            # 阶段2: 主翻译（Translator-A）
            draft_a = await self.translator_a.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            # 阶段3: 对照翻译（Translator-B）
            draft_b = await self.translator_b.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            # 阶段4: 一致性检查
            checker_report = await self.checker.check(
                segment_text,
                draft_a,
                draft_b,
                segment_id
            )
            
            # 选择最佳翻译（基于检查报告）
            best_draft = self._select_best_draft(draft_a, draft_b, checker_report)
            
            # 阶段5: 风格化
            stylist_result = await self.stylist.style(
                best_draft.translated_text,
                segment_text
            )
            
            # 阶段6: 最终整合
            final_result = await self.aggregator.aggregate(
                segment_text,
                [draft_a, draft_b],
                checker_report,
                stylist_result,
                segment_id
            )
            
            final_segments.append({
                'segment_id': segment_id,
                'text': final_result.translated_text
            })
            all_explainability_reports.append(final_result.explainability_report)
        
        # 合并所有段落
        final_text = ' '.join([seg['text'] for seg in final_segments])
        
        # 合并可解释性报告
        merged_explainability = self._merge_explainability_reports(all_explainability_reports)
        
        return FinalTranslation(
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
    
    def _select_best_draft(
        self,
        draft_a: TranslationDraft,
        draft_b: TranslationDraft,
        checker_report: CheckerReport
    ) -> TranslationDraft:
        """基于检查报告选择最佳翻译草稿"""
        # 如果有质量评分，选择评分更高的
        if draft_a.segment_id and draft_a.segment_id in checker_report.quality_scores:
            score_a = checker_report.quality_scores[draft_a.segment_id].overall
            score_b = checker_report.quality_scores.get(draft_b.segment_id or draft_a.segment_id, 
                                                       checker_report.quality_scores[draft_a.segment_id]).overall
            
            if score_a >= score_b:
                return draft_a
            else:
                return draft_b
        
        # 如果没有评分，优先选择没有冲突的
        if draft_a.segment_id and draft_a.segment_id in checker_report.consistent_segments:
            return draft_a
        if draft_b.segment_id and draft_b.segment_id in checker_report.consistent_segments:
            return draft_b
        
        # 默认返回draft_a
        return draft_a
    
    def _merge_explainability_reports(self, reports: List) -> 'ExplainabilityReport':
        """合并多个可解释性报告"""
        from src.agents.workflow import ExplainabilityReport, QualityScore
        
        all_modifications = []
        all_quality_improvements = {}
        
        for report in reports:
            all_modifications.extend(report.modifications)
            for metric, improvement in report.quality_improvements.items():
                if metric not in all_quality_improvements:
                    all_quality_improvements[metric] = {
                        'before': 0.0,
                        'after': 0.0,
                        'improvement': 0.0
                    }
                # 累加改进值
                all_quality_improvements[metric]['improvement'] += improvement.get('improvement', 0.0)
        
        # 计算平均质量分数
        final_quality = None
        if reports and reports[0].final_quality_score:
            # 简单平均
            avg_adequacy = sum(r.final_quality_score.adequacy for r in reports if r.final_quality_score) / len(reports)
            avg_fluency = sum(r.final_quality_score.fluency for r in reports if r.final_quality_score) / len(reports)
            avg_terminology = sum(r.final_quality_score.terminology for r in reports if r.final_quality_score) / len(reports)
            avg_overall = sum(r.final_quality_score.overall for r in reports if r.final_quality_score) / len(reports)
            
            final_quality = QualityScore(
                adequacy=avg_adequacy,
                fluency=avg_fluency,
                terminology=avg_terminology,
                overall=avg_overall
            )
        
        return ExplainabilityReport(
            modifications=all_modifications,
            quality_improvements=all_quality_improvements,
            final_quality_score=final_quality
        )

