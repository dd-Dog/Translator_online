"""
历史记录服务
"""
import json
import aiofiles
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from app.models.response import HistoryItem
from app.config import app_config


class HistoryService:
    """历史记录服务"""
    
    def __init__(self):
        self.history_file = app_config.HISTORY_FILE
    
    async def save(self, task_id: str, source_text: str, translated_text: str,
                   source_lang: str, target_lang: str, style: str, 
                   quality_score: Optional[float] = None,
                   processing_stages: Optional[List] = None,
                   explainability_report: Optional[dict] = None,
                   evaluation_result: Optional[dict] = None):
        """保存历史记录（如果已存在则更新，否则追加）"""
        # 检查是否已存在
        existing_item = await self.get_by_task_id(task_id)
        
        item = {
            "task_id": task_id,
            "source_text": source_text,
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "style": style,
            "quality_score": quality_score,
            "processing_stages": processing_stages or [],
            "explainability_report": explainability_report or {},
            "evaluation_result": evaluation_result or {},
            "created_at": existing_item.get('created_at', datetime.now().isoformat()) if existing_item else datetime.now().isoformat()
        }
        
        try:
            # 确保目录存在
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            if existing_item:
                # 如果已存在，更新记录（删除旧记录，添加新记录）
                await self.delete(task_id)
                async with aiofiles.open(self.history_file, 'a', encoding='utf-8') as f:
                    await f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
            else:
                # 如果不存在，追加新记录
                async with aiofiles.open(self.history_file, 'a', encoding='utf-8') as f:
                    await f.write(json.dumps(item, ensure_ascii=False, default=str) + '\n')
        except Exception as e:
            print(f"保存历史记录失败: {e}, 文件路径: {self.history_file}")
            import traceback
            print(traceback.format_exc())
            raise
    
    async def load(self, page: int = 1, page_size: int = 15,
                   source_lang: Optional[str] = None,
                   style: Optional[str] = None) -> List[dict]:
        """加载历史记录"""
        if not self.history_file.exists():
            print(f"历史记录文件不存在: {self.history_file}")
            return []
        
        items = []
        try:
            async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            # 过滤
                            if source_lang and item.get('source_lang') != source_lang:
                                continue
                            if style and item.get('style') != style:
                                continue
                            
                            # 确保created_at是datetime对象
                            if isinstance(item.get('created_at'), str):
                                try:
                                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                                except:
                                    item['created_at'] = datetime.now()
                            
                            # 去重：只保留每个task_id的最新记录
                            task_id = item.get('task_id')
                            if task_id:
                                # 检查是否已存在该task_id的记录
                                existing_index = None
                                for idx, existing_item in enumerate(items):
                                    if existing_item.get('task_id') == task_id:
                                        existing_index = idx
                                        break
                                
                                if existing_index is not None:
                                    # 如果已存在，比较时间戳，保留最新的
                                    existing_item = items[existing_index]
                                    existing_time = existing_item.get('created_at')
                                    current_time = item.get('created_at')
                                    
                                    # 比较时间，保留最新的
                                    if isinstance(existing_time, str):
                                        try:
                                            existing_time = datetime.fromisoformat(existing_time)
                                        except:
                                            existing_time = datetime.min
                                    if isinstance(current_time, str):
                                        try:
                                            current_time = datetime.fromisoformat(current_time)
                                        except:
                                            current_time = datetime.min
                                    
                                    if current_time > existing_time:
                                        items[existing_index] = item
                                else:
                                    # 如果不存在，添加新记录
                                    items.append(item)
                            else:
                                # 如果没有task_id，直接添加
                                items.append(item)
                        except json.JSONDecodeError as e:
                            print(f"JSON解析失败: {e}, line: {line[:100]}")
                            continue
                        except Exception as e:
                            print(f"解析历史记录失败: {e}, line: {line[:100]}")
                            continue
        except Exception as e:
            print(f"读取历史记录文件失败: {e}, 文件路径: {self.history_file}")
            return []
        
        # 按时间倒序排序
        try:
            def get_sort_key(x):
                created_at = x.get('created_at')
                if isinstance(created_at, datetime):
                    return created_at
                elif isinstance(created_at, str):
                    try:
                        return datetime.fromisoformat(created_at)
                    except:
                        return datetime.min
                else:
                    return datetime.min
            
            items.sort(key=get_sort_key, reverse=True)
        except Exception as e:
            print(f"排序历史记录失败: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        return items[start:end]
    
    async def get_total(self, source_lang: Optional[str] = None,
                       style: Optional[str] = None) -> int:
        """获取总数"""
        if not self.history_file.exists():
            return 0
        
        count = 0
        try:
            async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            # 过滤
                            if source_lang and item.get('source_lang') != source_lang:
                                continue
                            if style and item.get('style') != style:
                                continue
                            count += 1
                        except:
                            continue
        except:
            pass
        
        return count
    
    async def delete(self, task_id: str) -> bool:
        """删除历史记录"""
        if not self.history_file.exists():
            return False
        
        # 读取所有记录，过滤掉要删除的
        items = []
        async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
            async for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        if item['task_id'] != task_id:
                            items.append(line)
                    except:
                        continue
        
        # 写回文件
        async with aiofiles.open(self.history_file, 'w', encoding='utf-8') as f:
            for line in items:
                await f.write(line)
        
        return True
    
    async def get_by_task_id(self, task_id: str) -> Optional[dict]:
        """根据task_id获取历史记录详情"""
        if not self.history_file.exists():
            return None
        
        async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
            async for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        if item['task_id'] == task_id:
                            return item
                    except:
                        continue
        return None


# 全局历史记录服务实例
history_service = HistoryService()

