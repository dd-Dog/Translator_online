"""
Task Planner Agent - 全局调度Agent
负责任务规划、语言检测、任务拆分
"""

from typing import Dict, Optional
from src.models.base import BaseModel, TranslationRequest, TranslationResponse
from src.agents.workflow import TaskPlan, TaskType


class TaskPlanner:
    """任务规划Agent"""
    
    def __init__(self, model: BaseModel):
        """
        初始化任务规划Agent
        
        Args:
            model: 用于规划的模型（通常是ChatGPT）
        """
        self.model = model
    
    async def plan(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "zh"
    ) -> TaskPlan:
        """
        制定翻译任务计划
        
        Args:
            text: 待翻译文本
            source_lang: 源语言（None表示自动检测）
            target_lang: 目标语言
            
        Returns:
            TaskPlan: 任务计划
        """
        # 构建规划提示词
        prompt = self._build_planning_prompt(text, source_lang, target_lang)
        
        # 调用模型进行规划
        request = TranslationRequest(
            text=prompt,
            source_lang="auto",
            target_lang="zh",
            temperature=0.3
        )
        
        response = await self.model.translate(request)
        
        # 解析规划结果（这里简化处理，实际应该解析JSON）
        plan = self._parse_plan_response(response.translated_text, text, source_lang, target_lang)
        
        return plan
    
    def _build_planning_prompt(self, text: str, source_lang: Optional[str], target_lang: str) -> str:
        """构建规划提示词"""
        prompt = f"""你是一个专业的翻译任务规划器。请分析以下文本并制定翻译计划。

待翻译文本：
{text}

目标语言：{target_lang}
"""
        if source_lang:
            prompt += f"源语言：{source_lang}\n"
        else:
            prompt += "源语言：自动检测\n"
        
        prompt += """
请完成以下任务：
1. 检测源语言（如果未指定）
2. 将文本拆分为合适的翻译单元（句子级或段落级）
3. 识别哪些段落需要双重翻译（复杂、专业术语多、歧义等）
4. 识别哪些段落需要多重审核（重要内容、关键信息等）

请以JSON格式返回结果，格式如下：
{
    "source_lang": "检测到的源语言",
    "target_lang": "目标语言",
    "segments": [
        {
            "id": "seg_1",
            "text": "段落文本",
            "type": "sentence" 或 "paragraph",
            "needs_double_translation": true/false,
            "needs_multi_review": true/false
        }
    ]
}
"""
        return prompt
    
    def _parse_plan_response(self, response_text: str, original_text: str, 
                            source_lang: Optional[str], target_lang: str) -> TaskPlan:
        """解析规划响应（简化版，实际应使用JSON解析）"""
        import json
        import re
        
        # 尝试提取JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                plan_data = json.loads(json_match.group())
                segments = plan_data.get('segments', [])
                tasks = []
                
                for seg in segments:
                    tasks.append({
                        'segment_id': seg.get('id', f"seg_{len(tasks)+1}"),
                        'text': seg.get('text', ''),
                        'type': seg.get('type', 'sentence'),
                        'needs_double_translation': seg.get('needs_double_translation', False),
                        'needs_multi_review': seg.get('needs_multi_review', False)
                    })
                
                return TaskPlan(
                    source_lang=plan_data.get('source_lang', source_lang or 'auto'),
                    target_lang=plan_data.get('target_lang', target_lang),
                    tasks=tasks,
                    segments=segments
                )
            except:
                pass
        
        # 如果解析失败，使用默认拆分
        return self._default_plan(original_text, source_lang, target_lang)
    
    def _default_plan(self, text: str, source_lang: Optional[str], target_lang: str) -> TaskPlan:
        """默认任务计划（简单按句子拆分）"""
        import re
        
        # 简单按句号、问号、感叹号拆分
        sentences = re.split(r'[.!?]\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        tasks = []
        segments = []
        
        for i, sentence in enumerate(sentences):
            seg_id = f"seg_{i+1}"
            task = {
                'segment_id': seg_id,
                'text': sentence,
                'type': 'sentence',
                'needs_double_translation': len(sentence) > 100,  # 长句子需要双重翻译
                'needs_multi_review': False
            }
            tasks.append(task)
            segments.append({
                'id': seg_id,
                'text': sentence,
                'type': 'sentence'
            })
        
        return TaskPlan(
            source_lang=source_lang or 'auto',
            target_lang=target_lang,
            tasks=tasks,
            segments=segments
        )

