"""
Domain Stylist Agent
术语统一和风格统一
"""

from typing import Optional, Dict, List
from src.models.base import BaseModel, TranslationRequest
from src.agents.workflow import StylistResult


class Stylist:
    """风格化Agent"""
    
    def __init__(self, model: BaseModel, glossary: Optional[Dict[str, str]] = None, style: str = "general"):
        """
        初始化风格化Agent
        
        Args:
            model: 用于风格化的模型（通常是Qwen或DeepSeek）
            glossary: 术语表（可选），格式：{原文: 统一术语}
            style: 风格类型（"academic", "official", "colloquial", "general"）
        """
        self.model = model
        self.glossary = glossary or {}
        self.style_type = style  # 重命名为style_type避免与方法名冲突
    
    async def style(
        self,
        text: str,
        source_text: Optional[str] = None
    ) -> StylistResult:
        """
        对翻译文本进行风格化和术语统一
        
        Args:
            text: 待风格化的翻译文本
            source_text: 源文本（可选，用于上下文）
            
        Returns:
            StylistResult: 风格化结果
        """
        # 构建风格化提示词
        prompt = self._build_styling_prompt(text, source_text)
        
        request = TranslationRequest(
            text=prompt,
            source_lang="auto",
            target_lang="zh",
            temperature=0.3
        )
        
        response = await self.model.translate(request)
        
        # 解析风格化结果
        result = self._parse_styling_response(response.translated_text, text)
        
        return result
    
    def _build_styling_prompt(self, text: str, source_text: Optional[str]) -> str:
        """构建风格化提示词"""
        # 加载风格配置
        style_config = self._load_style_config()
        
        if self.style_type in style_config:
            style_info = style_config[self.style_type]
            style_name = style_info.get('name', self.style_type)
            guidelines = style_info.get('guidelines', [])
            terminology = style_info.get('terminology', {})
        else:
            # 兼容旧格式
            style_map = {
                "academic": "学术论文风格",
                "official": "正式公文风格",
                "colloquial": "口语化风格",
                "general": "通用风格",
                "native": "地道风格",
                "business": "商务风格",
                "technical": "技术文档风格",
                "literary": "文学风格",
                "news": "新闻风格",
                "legal": "法律风格"
            }
            style_name = style_map.get(self.style_type, "通用风格")
            guidelines = []
            terminology = {}
        
        prompt = f"""你是一个专业的文本风格化专家。请对以下翻译文本进行术语统一和风格调整。

待处理的翻译文本：
{text}
"""
        if source_text:
            prompt += f"\n原文（供参考）：\n{source_text}\n"
        
        prompt += f"\n要求：\n1. 统一术语：根据提供的术语表统一专业术语\n"
        
        if self.glossary:
            prompt += "术语表：\n"
            for original, unified in self.glossary.items():
                prompt += f"  {original} -> {unified}\n"
        
        prompt += f"\n2. 统一风格：调整为{style_name}\n"
        
        # 添加风格指导原则
        if guidelines:
            prompt += f"\n风格指导原则：\n"
            for guideline in guidelines:
                prompt += f"  - {guideline}\n"
        
        # 添加风格特定术语
        if terminology:
            prompt += f"\n风格特定术语：\n"
            for term, trans in terminology.items():
                prompt += f"  {term} -> {trans}\n"
        
        prompt += "\n3. 保持翻译的准确性和流畅性\n"
        prompt += "4. 记录所有修改（术语变更和风格变更）\n\n"
        prompt += """请按以下格式返回：
风格化文本：[处理后的文本]

术语变更：
- [原文] -> [统一术语] (原因：[原因])

风格变更：
- [原文本] -> [修改后文本] (原因：[原因])
"""
        return prompt
    
    def _parse_styling_response(self, response_text: str, original_text: str) -> StylistResult:
        """解析风格化响应"""
        import re
        
        # 提取风格化文本
        styled_match = re.search(r'风格化文本[：:]\s*(.+?)(?=术语变更|风格变更|$)', response_text, re.DOTALL)
        styled_text = styled_match.group(1).strip() if styled_match else original_text
        
        # 提取术语变更
        terminology_changes = []
        term_section = re.search(r'术语变更[：:]\s*(.+?)(?=风格变更|$)', response_text, re.DOTALL)
        if term_section:
            term_text = term_section.group(1)
            term_matches = re.finditer(r'-\s*\[(.+?)\]\s*->\s*\[(.+?)\]\s*\(原因[：:]\s*(.+?)\)', term_text)
            for match in term_matches:
                terminology_changes.append({
                    'original': match.group(1),
                    'unified': match.group(2),
                    'reason': match.group(3)
                })
        
        # 提取风格变更
        style_changes = []
        style_section = re.search(r'风格变更[：:]\s*(.+?)$', response_text, re.DOTALL)
        if style_section:
            style_text = style_section.group(1)
            style_matches = re.finditer(r'-\s*\[(.+?)\]\s*->\s*\[(.+?)\]\s*\(原因[：:]\s*(.+?)\)', style_text)
            for match in style_matches:
                style_changes.append({
                    'original': match.group(1),
                    'modified': match.group(2),
                    'reason': match.group(3)
                })
        
        return StylistResult(
            styled_text=styled_text,
            terminology_changes=terminology_changes,
            style_changes=style_changes
        )
    
    def _load_style_config(self) -> dict:
        """加载风格配置"""
        try:
            import yaml
            from pathlib import Path
            
            config_path = Path("config/styles.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('styles', {})
        except:
            pass
        return {}

