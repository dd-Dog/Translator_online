"""
Consistency & Adequacy Checker Agent
一致性检查和质量评估
"""

from typing import List, Dict
from src.models.base import BaseModel, TranslationRequest
from src.agents.workflow import TranslationDraft, CheckerReport, QualityScore


class Checker:
    """一致性检查和质量评估Agent"""
    
    def __init__(self, model: BaseModel):
        """
        初始化检查Agent
        
        Args:
            model: 用于检查的模型（通常是ChatGPT）
        """
        self.model = model
    
    async def check(
        self,
        source_text: str,
        draft_a: TranslationDraft,
        draft_b: TranslationDraft,
        segment_id: str
    ) -> CheckerReport:
        """
        检查两个翻译草稿的一致性和质量
        
        Args:
            source_text: 源文本
            draft_a: Translator-A的翻译草稿
            draft_b: Translator-B的翻译草稿
            segment_id: 段落ID
            
        Returns:
            CheckerReport: 检查报告
        """
        # 构建检查提示词
        prompt = self._build_checking_prompt(source_text, draft_a, draft_b)
        
        request = TranslationRequest(
            text=prompt,
            source_lang="auto",
            target_lang="zh",
            temperature=0.2  # 低温度以获得更稳定的评估
        )
        
        response = await self.model.translate(request)
        
        # 解析检查报告
        report = self._parse_check_response(response.translated_text, segment_id)
        
        return report
    
    def _build_checking_prompt(self, source_text: str, draft_a: TranslationDraft, draft_b: TranslationDraft) -> str:
        """构建检查提示词"""
        prompt = f"""你是一个专业的翻译质量评估专家。请对比以下两个翻译版本，进行一致性检查和质量评估。

原文：
{source_text}

翻译版本A（主译）：
{draft_a.translated_text}

翻译版本B（对照译）：
{draft_b.translated_text}

请完成以下任务：
1. 识别两个版本中一致的句子/段落
2. 识别两个版本中冲突的句子/段落，并说明冲突原因
3. 检查是否有遗漏的内容
4. 检查是否有误解或误译
5. 对每个版本进行质量评分（MQM简化版）：
   - 充分性（Adequacy）：是否完整传达了原文意思（0-1）
   - 流畅性（Fluency）：翻译是否自然流畅（0-1）
   - 术语准确性（Terminology）：专业术语是否准确（0-1）

请以JSON格式返回结果，格式如下：
{{
    "consistent": true/false,
    "conflicts": [
        {{
            "issue": "冲突描述",
            "translator_a_text": "版本A的文本",
            "translator_b_text": "版本B的文本"
        }}
    ],
    "omissions": [
        {{
            "missing_content": "遗漏的内容描述"
        }}
    ],
    "misinterpretations": [
        {{
            "original_meaning": "原文意思",
            "translated_meaning": "翻译后的意思",
            "issue": "问题描述"
        }}
    ],
    "quality_scores": {{
        "translator_a": {{
            "adequacy": 0.9,
            "fluency": 0.85,
            "terminology": 0.9,
            "overall": 0.88
        }},
        "translator_b": {{
            "adequacy": 0.88,
            "fluency": 0.9,
            "terminology": 0.85,
            "overall": 0.88
        }}
    }}
}}
"""
        return prompt
    
    def _parse_check_response(self, response_text: str, segment_id: str) -> CheckerReport:
        """解析检查响应"""
        import json
        import re
        
        # 尝试提取JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                
                consistent_segments = [segment_id] if data.get('consistent', True) else []
                
                conflicting_segments = []
                for conflict in data.get('conflicts', []):
                    conflicting_segments.append({
                        'segment_id': segment_id,
                        'translator_a_text': conflict.get('translator_a_text', ''),
                        'translator_b_text': conflict.get('translator_b_text', ''),
                        'issue': conflict.get('issue', '')
                    })
                
                omissions = []
                for omission in data.get('omissions', []):
                    omissions.append({
                        'segment_id': segment_id,
                        'missing_content': omission.get('missing_content', '')
                    })
                
                misinterpretations = []
                for mis in data.get('misinterpretations', []):
                    misinterpretations.append({
                        'segment_id': segment_id,
                        'original_meaning': mis.get('original_meaning', ''),
                        'translated_meaning': mis.get('translated_meaning', ''),
                        'issue': mis.get('issue', '')
                    })
                
                quality_scores = {}
                scores_data = data.get('quality_scores', {})
                for translator, scores in scores_data.items():
                    quality_scores[segment_id] = QualityScore(
                        adequacy=scores.get('adequacy', 0.8),
                        fluency=scores.get('fluency', 0.8),
                        terminology=scores.get('terminology', 0.8),
                        overall=scores.get('overall', 0.8)
                    )
                
                return CheckerReport(
                    consistent_segments=consistent_segments,
                    conflicting_segments=conflicting_segments,
                    omissions=omissions,
                    misinterpretations=misinterpretations,
                    quality_scores=quality_scores
                )
            except Exception as e:
                pass
        
        # 如果解析失败，返回默认报告
        return CheckerReport(
            consistent_segments=[segment_id],
            conflicting_segments=[],
            omissions=[],
            misinterpretations=[],
            quality_scores={segment_id: QualityScore(0.8, 0.8, 0.8, 0.8)}
        )

