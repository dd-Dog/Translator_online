"""
翻译API
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.models.request import TranslateRequest
from app.models.response import TranslateResponse, TaskStatus, TranslationResult
from app.services.task_manager import task_manager
from app.services.history_service import history_service
from app.config import security_config

router = APIRouter(prefix="/api/v1", tags=["translate"])

# 速率限制
limiter = Limiter(key_func=get_remote_address)


@router.post("/translate", response_model=TranslateResponse)
@limiter.limit(security_config.RATE_LIMIT_TRANSLATE)
async def translate(request: Request, translate_request: TranslateRequest):
    """
    创建翻译任务
    """
    try:
        # 调试：打印接收到的请求数据
        import json
        print(f"[API调试] 接收到的model_configs: {translate_request.model_configs}")
        if translate_request.model_configs:
            for stage, config in translate_request.model_configs.items():
                print(f"[API调试] {stage}: model_type={config.model_type if hasattr(config, 'model_type') else 'N/A'}, api_key长度={len(config.api_key) if hasattr(config, 'api_key') else 0}")
        
        # 创建任务
        task_id = task_manager.create_task(translate_request)
        
        # 延迟启动任务，给WebSocket连接建立的时间
        # 增加等待时间，确保WebSocket连接已建立
        import asyncio
        from app.utils.websocket_manager import ws_manager
        
        async def delayed_start():
            # 等待WebSocket连接建立，最多等待3秒
            max_wait = 3.0  # 最大等待时间（秒）
            check_interval = 0.1  # 检查间隔（秒）
            waited = 0.0
            
            while waited < max_wait:
                # 检查是否有WebSocket连接
                if task_id in ws_manager.connections and len(ws_manager.connections[task_id]) > 0:
                    print(f"[API] WebSocket连接已建立，等待时间: {waited:.2f}秒")
                    break
                await asyncio.sleep(check_interval)
                waited += check_interval
            
            if waited >= max_wait:
                print(f"[API] 警告: 等待WebSocket连接超时（{max_wait}秒），但任务将继续执行")
            
            # 启动任务
            await task_manager.start_task(task_id)
        
        # 异步执行任务（延迟启动）
        asyncio.create_task(delayed_start())
        
        return TranslateResponse(
            task_id=task_id,
            status="processing",
            message="翻译任务已创建"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translate/{task_id}", response_model=TranslateResponse)
async def get_translation(task_id: str):
    """
    获取翻译结果
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 历史记录已在任务完成时保存，这里不再重复保存
    
    return TranslateResponse(
        task_id=task_id,
        status=task.status,
        message=task.current_stage or "等待中",
        result=task.result,
        error=task.error
    )


@router.get("/translate/{task_id}/status", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    status = task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="任务不存在")
    return status

