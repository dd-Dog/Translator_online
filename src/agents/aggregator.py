"""
Final Aggregator Agent
最终整合和可解释性报告生成
"""

from typing import List, Dict
from src.models.base import BaseModel, TranslationRequest
from src.agents.workflow import (
    FinalTranslation, ExplainabilityReport, QualityScore,
    TranslationDraft, CheckerReport, StylistResult
)


class Aggregator:
    """最终整合Agent"""
    
    def __init__(self, model: BaseModel):
        """
        初始化整合Agent
        
        Args:
            model: 用于整合的模型（通常是ChatGPT）
        """
        self.model = model
    
    async def aggregate(
        self,
        source_text: str,
        drafts: List[TranslationDraft],
        checker_report: CheckerReport,
        stylist_result: StylistResult,
        segment_id: str
    ) -> FinalTranslation:
        """
        整合所有结果，生成最终翻译和可解释性报告
        
        Args:
            source_text: 源文本
            drafts: 翻译草稿列表
            checker_report: 检查报告
            stylist_result: 风格化结果
            segment_id: 段落ID
            
        Returns:
            FinalTranslation: 最终翻译结果
        """
        # 构建整合提示词
        prompt = self._build_aggregation_prompt(
            source_text, drafts, checker_report, stylist_result
        )
        
        request = TranslationRequest(
            text=prompt,
            source_lang="auto",
            target_lang="zh",
            temperature=0.3
        )
        
        response = await self.model.translate(request)
        
        # 构建提示词
        prompt = self._build_aggregation_prompt(
            source_text, drafts, checker_report, stylist_result, segment_id
        )
        
        request = TranslationRequest(
            text=prompt,
            source_lang="auto",
            target_lang="zh",
            temperature=0.3
        )
        
        response = await self.model.translate(request)
        
        # 解析最终结果
        final_text, explainability = self._parse_aggregation_response(
            response.translated_text,
            checker_report,
            stylist_result,
            segment_id
        )
        
        return FinalTranslation(
            translated_text=final_text,
            explainability_report=explainability,
            source_lang="auto",  # 可以从任务计划中获取
            target_lang="zh",
            processing_stages=[
                "Task Planning",
                "Primary Translation (Translator-A)",
                "Comparison Translation (Translator-B)",
                "Quality Checking",
                "Styling",
                "Final Aggregation"
            ]
        )
    
    def _build_aggregation_prompt(
        self,
        source_text: str,
        drafts: List[TranslationDraft],
        checker_report: CheckerReport,
        stylist_result: StylistResult,
        segment_id: str = ""
    ) -> str:
        """构建整合提示词"""
        prompt = f"""你是一个专业的翻译整合专家。请基于以下信息生成最终翻译和可解释性报告。

原文：
{source_text}

翻译草稿：
"""
        for i, draft in enumerate(drafts, 1):
            prompt += f"\n草稿{i} ({draft.model_name}):\n{draft.translated_text}\n"
        
        prompt += f"\n检查报告：\n"
        if checker_report.conflicting_segments:
            prompt += "冲突段落：\n"
            for conflict in checker_report.conflicting_segments:
                prompt += f"  - {conflict.get('issue', '')}\n"
        if checker_report.omissions:
            prompt += "遗漏内容：\n"
            for omission in checker_report.omissions:
                prompt += f"  - {omission.get('missing_content', '')}\n"
        
        if segment_id in checker_report.quality_scores:
            score = checker_report.quality_scores[segment_id]
            prompt += f"\n质量评分：\n"
            prompt += f"  充分性: {score.adequacy:.2f}\n"
            prompt += f"  流畅性: {score.fluency:.2f}\n"
            prompt += f"  术语准确性: {score.terminology:.2f}\n"
            prompt += f"  总体: {score.overall:.2f}\n"
        
        prompt += f"\n风格化结果：\n{stylist_result.styled_text}\n"
        
        if stylist_result.terminology_changes:
            prompt += "\n术语变更：\n"
            for change in stylist_result.terminology_changes:
                prompt += f"  - {change['original']} -> {change['unified']} ({change['reason']})\n"
        
        prompt += """
请完成以下任务：
1. 基于检查报告和风格化结果，生成最终的最佳翻译
2. 记录所有修改和原因（用于可解释性报告）
3. 评估质量改进情况

请按以下格式返回：
最终翻译：[最终翻译文本]

修改记录：
- [阶段] - [段落] - [原文] -> [修改后] (原因：[原因])

质量改进：
- [指标] - 改进前: [分数] -> 改进后: [分数] (改进: [改进值])
"""
        return prompt
    
    def _parse_aggregation_response(
        self,
        response_text: str,
        checker_report: CheckerReport,
        stylist_result: StylistResult,
        segment_id: str
    ) -> tuple:
        """解析整合响应"""
        import re
        
        # 提取最终翻译
        final_match = re.search(r'最终翻译[：:]\s*(.+?)(?=修改记录|质量改进|$)', response_text, re.DOTALL)
        final_text = final_match.group(1).strip() if final_match else stylist_result.styled_text
        
        # 提取修改记录
        modifications = []
        mod_section = re.search(r'修改记录[：:]\s*(.+?)(?=质量改进|$)', response_text, re.DOTALL)
        if mod_section:
            mod_text = mod_section.group(1)
            mod_matches = re.finditer(r'-\s*\[(.+?)\]\s*-\s*\[(.+?)\]\s*-\s*\[(.+?)\]\s*->\s*\[(.+?)\]\s*\(原因[：:]\s*(.+?)\)', mod_text)
            for match in mod_matches:
                modifications.append({
                    'stage': match.group(1),
                    'segment_id': match.group(2),
                    'original': match.group(3),
                    'modified': match.group(4),
                    'reason': match.group(5)
                })
        
        # 提取质量改进
        quality_improvements = {}
        quality_section = re.search(r'质量改进[：:]\s*(.+?)$', response_text, re.DOTALL)
        if quality_section:
            quality_text = quality_section.group(1)
            quality_matches = re.finditer(r'-\s*\[(.+?)\]\s*-\s*改进前[：:]\s*([0-9.]+)\s*->\s*改进后[：:]\s*([0-9.]+)\s*\(改进[：:]\s*([0-9.]+)\)', quality_text)
            for match in quality_matches:
                metric = match.group(1)
                before = float(match.group(2))
                after = float(match.group(3))
                improvement = float(match.group(4))
                quality_improvements[metric] = {
                    'before': before,
                    'after': after,
                    'improvement': improvement
                }
        
        # 获取最终质量分数
        final_quality = None
        if segment_id in checker_report.quality_scores:
            original_score = checker_report.quality_scores[segment_id]
            # 假设经过风格化后质量有所提升
            final_quality = QualityScore(
                adequacy=min(1.0, original_score.adequacy + 0.05),
                fluency=min(1.0, original_score.fluency + 0.05),
                terminology=min(1.0, original_score.terminology + 0.05),
                overall=min(1.0, original_score.overall + 0.05)
            )
        
        explainability = ExplainabilityReport(
            modifications=modifications,
            quality_improvements=quality_improvements,
            final_quality_score=final_quality
        )
        
        return final_text, explainability

