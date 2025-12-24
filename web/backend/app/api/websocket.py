"""
WebSocket API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.websocket_manager import ws_manager

router = APIRouter()


@router.websocket("/ws/translate/{task_id}")
async def websocket_translate(websocket: WebSocket, task_id: str):
    """
    WebSocket连接，用于实时推送翻译进度
    """
    print(f"[WebSocket] 新连接: task_id={task_id}")
    await ws_manager.connect(websocket, task_id)
    print(f"[WebSocket] 连接已建立: task_id={task_id}")
    
    # 发送连接确认消息
    from app.models.response import WebSocketMessage
    await ws_manager.send_progress(
        task_id,
        WebSocketMessage(
            type="connected",
            task_id=task_id,
            data={"message": "WebSocket连接已建立"}
        )
    )
    
    try:
        while True:
            # 保持连接，等待服务器推送消息
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息（如果需要）
            # 目前只用于服务器推送进度
    except WebSocketDisconnect:
        print(f"[WebSocket] 连接断开: task_id={task_id}")
        await ws_manager.disconnect(websocket, task_id)

