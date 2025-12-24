"""
历史记录API
"""
from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from datetime import datetime
from app.models.response import HistoryResponse, HistoryItem
from app.services.history_service import history_service
from app.config import security_config

router = APIRouter(prefix="/api/v1", tags=["history"])

# 速率限制
limiter = Limiter(key_func=get_remote_address)


@router.get("/history", response_model=HistoryResponse)
@limiter.limit(security_config.RATE_LIMIT_HISTORY)
async def get_history(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_lang: str = Query(None),
    style: str = Query(None)
):
    """
    获取翻译历史
    """
    try:
        items = await history_service.load(page=page, page_size=page_size,
                                          source_lang=source_lang, style=style)
        total = await history_service.get_total(source_lang=source_lang, style=style)
        
        # 将dict转换为HistoryItem
        history_items = []
        for item in items:
            if isinstance(item, dict):
                try:
                    # 确保created_at是datetime
                    created_at = item.get('created_at')
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    elif not isinstance(created_at, datetime):
                        created_at = datetime.now()
                    
                    # 只使用HistoryItem定义的字段
                    history_item_data = {
                        'task_id': item.get('task_id', ''),
                        'source_text': item.get('source_text', ''),
                        'translated_text': item.get('translated_text', ''),
                        'source_lang': item.get('source_lang', ''),
                        'target_lang': item.get('target_lang', ''),
                        'style': item.get('style', ''),
                        'quality_score': item.get('quality_score'),
                        'created_at': created_at,
                        'evaluation_result': item.get('evaluation_result')  # 添加评估结果
                    }
                    history_item = HistoryItem(**history_item_data)
                    history_items.append(history_item)
                except Exception as e:
                    print(f"转换HistoryItem失败: {e}")
                    import traceback
                    print(traceback.format_exc())
                    print(f"item keys: {list(item.keys()) if isinstance(item, dict) else 'not dict'}")
                    # 即使转换失败，也尝试创建一个基本的HistoryItem
                    try:
                        # 处理created_at
                        basic_created_at = item.get('created_at')
                        if isinstance(basic_created_at, str):
                            basic_created_at = datetime.fromisoformat(basic_created_at)
                        elif not isinstance(basic_created_at, datetime):
                            basic_created_at = datetime.now()
                        
                        basic_item = HistoryItem(
                            task_id=item.get('task_id', 'unknown'),
                            source_text=item.get('source_text', ''),
                            translated_text=item.get('translated_text', ''),
                            source_lang=item.get('source_lang', ''),
                            target_lang=item.get('target_lang', ''),
                            style=item.get('style', ''),
                            quality_score=item.get('quality_score'),
                            created_at=basic_created_at,
                            evaluation_result=item.get('evaluation_result')  # 添加评估结果
                        )
                        history_items.append(basic_item)
                    except:
                        continue
            else:
                history_items.append(item)
        
        print(f"返回历史记录: 总数={total}, 当前页={len(history_items)}条")
        if len(history_items) == 0 and total > 0:
            print(f"警告: 有{total}条记录但转换后为0条，可能是数据格式问题")
            print(f"原始items数量: {len(items)}")
        
        return HistoryResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=history_items
        )
    except Exception as e:
        import traceback
        print(f"获取历史记录失败: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{task_id}")
async def get_history_detail(task_id: str):
    """
    获取历史记录详情
    """
    item = await history_service.get_by_task_id(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return item


@router.put("/history/{task_id}/evaluation")
async def update_evaluation(task_id: str, evaluation_result: dict):
    """
    更新历史记录的评估结果
    """
    item = await history_service.get_by_task_id(task_id)
    if not item:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    # 更新评估结果
    item['evaluation_result'] = evaluation_result
    
    # 重新保存（删除旧记录，添加新记录）
    await history_service.delete(task_id)
    await history_service.save(
        task_id=item['task_id'],
        source_text=item['source_text'],
        translated_text=item['translated_text'],
        source_lang=item['source_lang'],
        target_lang=item['target_lang'],
        style=item['style'],
        quality_score=item.get('quality_score'),
        processing_stages=item.get('processing_stages', []),
        explainability_report=item.get('explainability_report', {}),
        evaluation_result=evaluation_result
    )
    
    return {"message": "评估结果已更新"}


@router.delete("/history/{task_id}")
async def delete_history(task_id: str):
    """
    删除历史记录
    """
    success = await history_service.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return {"message": "删除成功"}

