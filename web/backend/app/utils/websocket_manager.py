"""
WebSocket管理器
"""
from typing import Dict, List
from fastapi import WebSocket
import json
from app.models.response import WebSocketMessage


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """建立连接"""
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)
    
    async def disconnect(self, websocket: WebSocket, task_id: str):
        """断开连接"""
        if task_id in self.connections:
            if websocket in self.connections[task_id]:
                self.connections[task_id].remove(websocket)
            if not self.connections[task_id]:
                del self.connections[task_id]
    
    async def send_progress(self, task_id: str, message: WebSocketMessage):
        """发送进度消息"""
        if task_id in self.connections:
            disconnected = []
            connections_count = len(self.connections[task_id])
            print(f"[WebSocket] 发送消息到 {connections_count} 个连接: task_id={task_id}, type={message.type}")
            for ws in self.connections[task_id]:
                try:
                    message_dict = message.dict()
                    await ws.send_json(message_dict)
                    print(f"[WebSocket] 消息已发送: {message_dict}")
                except Exception as e:
                    print(f"[WebSocket] 发送消息失败: {e}")
                    disconnected.append(ws)
            
            # 清理断开的连接
            for ws in disconnected:
                await self.disconnect(ws, task_id)
        else:
            print(f"[WebSocket] 警告: task_id={task_id} 没有活跃的连接")
    
    async def send_to_all(self, task_id: str, msg_type: str, data: dict):
        """发送消息到所有连接的客户端"""
        message = WebSocketMessage(
            type=msg_type,
            task_id=task_id,
            data=data
        )
        await self.send_progress(task_id, message)


# 全局WebSocket管理器实例
ws_manager = WebSocketManager()

