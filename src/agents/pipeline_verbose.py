"""
Translation Pipeline with Verbose Logging
带详细日志的翻译工作流编排器
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


class VerboseTranslationPipeline:
    """带详细日志的翻译工作流编排器"""
    
    def __init__(
        self,
        planner_model: BaseModel,
        translator_a_model: BaseModel,
        translator_b_model: BaseModel,
        checker_model: BaseModel,
        stylist_model: BaseModel,
        aggregator_model: BaseModel,
        glossary: Optional[Dict[str, str]] = None,
        style: str = "general",
        verbose: bool = True
    ):
        """初始化带详细日志的翻译工作流"""
        self.planner = TaskPlanner(planner_model)
        self.translator_a = TranslatorA(translator_a_model)
        self.translator_b = TranslatorB(translator_b_model)
        self.checker = Checker(checker_model)
        self.stylist = Stylist(stylist_model, glossary=glossary, style=style)
        self.aggregator = Aggregator(aggregator_model)
        self.verbose = verbose
    
    def log(self, stage: str, message: str, level: str = "INFO"):
        """打印日志"""
        if self.verbose:
            symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
            symbol = symbols.get(level, "•")
            print(f"{symbol} [{stage}] {message}")
    
    def print_section(self, title: str, content: str = None):
        """打印分节标题"""
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"📍 {title}")
            print(f"{'='*70}")
            if content:
                print(content)
    
    async def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "zh",
        glossary: Optional[Dict[str, str]] = None,
        style: Optional[str] = None
    ) -> FinalTranslation:
        """
        执行完整翻译流程（带详细日志）
        """
        self.print_section("🚀 开始翻译流程")
        print(f"原文: {text}")
        print(f"源语言: {source_lang or '自动检测'}")
        print(f"目标语言: {target_lang}")
        
        # 更新术语表和风格
        if glossary is not None:
            self.stylist.glossary = glossary
        if style is not None:
            self.stylist.style_type = style
        
        # ===== 阶段1: 任务规划 =====
        self.print_section("阶段1: Task Planner - 任务规划")
        self.log("Planner", f"模型: {self.planner.model.model_name}", "INFO")
        self.log("Planner", "正在分析文本并制定翻译计划...", "INFO")
        
        task_plan = await self.planner.plan(text, source_lang, target_lang)
        
        self.log("Planner", f"检测到源语言: {task_plan.source_lang}", "SUCCESS")
        self.log("Planner", f"目标语言: {task_plan.target_lang}", "SUCCESS")
        self.log("Planner", f"拆分为 {len(task_plan.tasks)} 个翻译任务", "SUCCESS")
        
        if self.verbose:
            print(f"\n任务详情:")
            for i, task in enumerate(task_plan.tasks, 1):
                print(f"  任务{i}:")
                print(f"    文本: {task['text'][:50]}...")
                print(f"    类型: {task['type']}")
                print(f"    需要双重翻译: {task.get('needs_double_translation', False)}")
        
        # 处理每个任务
        final_segments = []
        all_explainability_reports = []
        
        for task_idx, task in enumerate(task_plan.tasks, 1):
            segment_id = task['segment_id']
            segment_text = task['text']
            
            self.print_section(f"处理任务 {task_idx}/{len(task_plan.tasks)}")
            print(f"段落ID: {segment_id}")
            print(f"文本: {segment_text}")
            
            # ===== 阶段2: 主翻译 =====
            self.print_section("阶段2: Translator-A - 主翻译 (Gemini)")
            self.log("Translator-A", f"模型: {self.translator_a.model.model_name}", "INFO")
            self.log("Translator-A", "正在进行多语言通用翻译...", "INFO")
            
            draft_a = await self.translator_a.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            self.log("Translator-A", f"翻译完成", "SUCCESS")
            if self.verbose:
                print(f"  翻译结果: {draft_a.translated_text}")
                if draft_a.self_check_report:
                    print(f"  自检置信度: {draft_a.self_check_report.confidence_scores.get('overall', 'N/A')}")
                    if draft_a.self_check_report.uncertain_segments:
                        print(f"  不确定段落: {len(draft_a.self_check_report.uncertain_segments)} 处")
            
            # ===== 阶段3: 对照翻译 =====
            self.print_section("阶段3: Translator-B - 对照翻译 (Qwen)")
            self.log("Translator-B", f"模型: {self.translator_b.model.model_name}", "INFO")
            self.log("Translator-B", "正在进行对照翻译（擅长中文自然表达）...", "INFO")
            
            draft_b = await self.translator_b.translate(
                segment_text,
                task_plan.source_lang,
                task_plan.target_lang,
                segment_id
            )
            
            self.log("Translator-B", f"翻译完成", "SUCCESS")
            if self.verbose:
                print(f"  翻译结果: {draft_b.translated_text}")
                if draft_b.self_check_report:
                    print(f"  自检置信度: {draft_b.self_check_report.confidence_scores.get('overall', 'N/A')}")
            
            # 对比两个翻译
            if self.verbose:
                print(f"\n📊 两个翻译对比:")
                print(f"  翻译A (Gemini): {draft_a.translated_text}")
                print(f"  翻译B (Qwen):   {draft_b.translated_text}")
                if draft_a.translated_text == draft_b.translated_text:
                    print(f"  状态: ✅ 完全一致")
                else:
                    print(f"  状态: ⚠️  存在差异")
            
            # ===== 阶段4: 一致性检查 =====
            self.print_section("阶段4: Checker - 质量检查与MQM评分 (GPT-4)")
            self.log("Checker", f"模型: {self.checker.model.model_name}", "INFO")
            self.log("Checker", "正在对比两个翻译版本，进行质量评估...", "INFO")
            
            checker_report = await self.checker.check(
                segment_text,
                draft_a,
                draft_b,
                segment_id
            )
            
            self.log("Checker", "质量检查完成", "SUCCESS")
            if self.verbose:
                print(f"\n检查结果:")
                print(f"  一致性: {'✅ 一致' if segment_id in checker_report.consistent_segments else '⚠️ 存在冲突'}")
                print(f"  冲突数: {len(checker_report.conflicting_segments)}")
                print(f"  遗漏数: {len(checker_report.omissions)}")
                print(f"  误解数: {len(checker_report.misinterpretations)}")
                
                if checker_report.conflicting_segments:
                    print(f"\n  冲突详情:")
                    for conflict in checker_report.conflicting_segments[:2]:
                        print(f"    问题: {conflict.get('issue', 'N/A')[:100]}...")
                
                if segment_id in checker_report.quality_scores:
                    score = checker_report.quality_scores[segment_id]
                    print(f"\n  MQM质量评分:")
                    print(f"    充分性 (Adequacy): {score.adequacy:.2f}")
                    print(f"    流畅性 (Fluency): {score.fluency:.2f}")
                    print(f"    术语准确性 (Terminology): {score.terminology:.2f}")
                    print(f"    总体评分 (Overall): {score.overall:.2f}")
            
            # 选择最佳翻译
            best_draft = self._select_best_draft(draft_a, draft_b, checker_report)
            self.log("Checker", f"选择最佳翻译: {best_draft.model_name}", "INFO")
            if self.verbose:
                print(f"  选中翻译: {best_draft.translated_text}")
            
            # ===== 阶段5: 风格化 =====
            self.print_section("阶段5: Stylist - 术语统一与风格调整 (Qwen)")
            self.log("Stylist", f"模型: {self.stylist.model.model_name}", "INFO")
            self.log("Stylist", f"风格类型: {self.stylist.style_type}", "INFO")
            if self.stylist.glossary:
                self.log("Stylist", f"使用术语表: {len(self.stylist.glossary)} 条", "INFO")
            self.log("Stylist", "正在进行风格化处理...", "INFO")
            
            stylist_result = await self.stylist.style(
                best_draft.translated_text,
                segment_text
            )
            
            self.log("Stylist", "风格化完成", "SUCCESS")
            if self.verbose:
                print(f"  风格化前: {best_draft.translated_text}")
                print(f"  风格化后: {stylist_result.styled_text}")
                
                if stylist_result.terminology_changes:
                    print(f"\n  术语变更 ({len(stylist_result.terminology_changes)} 处):")
                    for change in stylist_result.terminology_changes[:3]:
                        print(f"    {change['original']} → {change['unified']} ({change['reason']})")
                
                if stylist_result.style_changes:
                    print(f"\n  风格变更 ({len(stylist_result.style_changes)} 处):")
                    for change in stylist_result.style_changes[:3]:
                        print(f"    修改原因: {change.get('reason', 'N/A')[:60]}...")
            
            # ===== 阶段6: 最终整合 =====
            self.print_section("阶段6: Aggregator - 最终整合与可解释性报告 (GPT-4)")
            self.log("Aggregator", f"模型: {self.aggregator.model.model_name}", "INFO")
            self.log("Aggregator", "正在整合所有结果，生成最终翻译...", "INFO")
            
            final_result = await self.aggregator.aggregate(
                segment_text,
                [draft_a, draft_b],
                checker_report,
                stylist_result,
                segment_id
            )
            
            self.log("Aggregator", "整合完成", "SUCCESS")
            if self.verbose:
                print(f"  最终翻译: {final_result.translated_text}")
                
                if final_result.explainability_report.final_quality_score:
                    final_score = final_result.explainability_report.final_quality_score
                    original_score = checker_report.quality_scores.get(segment_id)
                    
                    print(f"\n  质量评分变化:")
                    if original_score:
                        print(f"    Checker评分: {original_score.overall:.2f}")
                        print(f"    最终评分: {final_score.overall:.2f}")
                        print(f"    提升: {final_score.overall - original_score.overall:+.2f}")
                    else:
                        print(f"    最终评分: {final_score.overall:.2f}")
                    
                    print(f"\n  最终质量详情:")
                    print(f"    充分性: {final_score.adequacy:.2f}")
                    print(f"    流畅性: {final_score.fluency:.2f}")
                    print(f"    术语准确性: {final_score.terminology:.2f}")
                
                if final_result.explainability_report.modifications:
                    print(f"\n  修改记录: {len(final_result.explainability_report.modifications)} 处")
                    for mod in final_result.explainability_report.modifications[:3]:
                        print(f"    [{mod.get('stage', 'N/A')}] {mod.get('reason', 'N/A')[:50]}...")
            
            final_segments.append({
                'segment_id': segment_id,
                'text': final_result.translated_text
            })
            all_explainability_reports.append(final_result.explainability_report)
        
        # 合并所有段落
        final_text = ' '.join([seg['text'] for seg in final_segments])
        merged_explainability = self._merge_explainability_reports(all_explainability_reports)
        
        # 最终总结
        self.print_section("🎉 翻译流程完成")
        if self.verbose:
            print(f"\n原文 ({len(text)} 字符):")
            print(f"  {text}")
            print(f"\n最终翻译 ({len(final_text)} 字符):")
            print(f"  {final_text}")
            
            if merged_explainability.final_quality_score:
                score = merged_explainability.final_quality_score
                print(f"\n整体质量评分:")
                print(f"  充分性: {score.adequacy:.2f}")
                print(f"  流畅性: {score.fluency:.2f}")
                print(f"  术语准确性: {score.terminology:.2f}")
                print(f"  总体: {score.overall:.2f}")
                
                # 评级
                if score.overall >= 0.95:
                    level = "优秀"
                elif score.overall >= 0.85:
                    level = "良好"
                elif score.overall >= 0.70:
                    level = "中等"
                else:
                    level = "需改进"
                print(f"  评级: {level}")
        
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
        if draft_a.segment_id and draft_a.segment_id in checker_report.quality_scores:
            score_a = checker_report.quality_scores[draft_a.segment_id].overall
            score_b = checker_report.quality_scores.get(draft_b.segment_id or draft_a.segment_id, 
                                                       checker_report.quality_scores[draft_a.segment_id]).overall
            
            if self.verbose:
                print(f"\n  翻译A评分: {score_a:.2f}")
                print(f"  翻译B评分: {score_b:.2f}")
            
            if score_a >= score_b:
                return draft_a
            else:
                return draft_b
        
        if draft_a.segment_id and draft_a.segment_id in checker_report.consistent_segments:
            return draft_a
        if draft_b.segment_id and draft_b.segment_id in checker_report.consistent_segments:
            return draft_b
        
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
                all_quality_improvements[metric]['improvement'] += improvement.get('improvement', 0.0)
        
        final_quality = None
        if reports and reports[0].final_quality_score:
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

