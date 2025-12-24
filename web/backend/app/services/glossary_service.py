"""
术语表服务
"""
import json
import aiofiles
from typing import Dict
from app.config import app_config


class GlossaryService:
    """术语表服务"""
    
    def __init__(self):
        self.glossary_file = app_config.GLOSSARY_FILE
    
    async def load(self) -> Dict[str, str]:
        """加载术语表"""
        if not self.glossary_file.exists():
            return {}
        
        try:
            async with aiofiles.open(self.glossary_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except Exception as e:
            print(f"加载术语表失败: {e}")
            return {}
    
    async def save(self, glossary: Dict[str, str]):
        """保存术语表"""
        async with aiofiles.open(self.glossary_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(glossary, ensure_ascii=False, indent=2))
    
    async def add(self, term: str, translation: str):
        """添加术语"""
        glossary = await self.load()
        glossary[term] = translation
        await self.save(glossary)
    
    async def update(self, term: str, translation: str):
        """更新术语"""
        await self.add(term, translation)  # 添加和更新逻辑相同
    
    async def delete(self, term: str):
        """删除术语"""
        glossary = await self.load()
        if term in glossary:
            del glossary[term]
            await self.save(glossary)
            return True
        return False


# 全局术语表服务实例
glossary_service = GlossaryService()

