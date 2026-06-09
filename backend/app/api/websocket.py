import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.core.message_bus import message_bus, AgentMessage


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点 - 实时推送智能体状态和消息"""
    await manager.connect(websocket)

    # 注册消息总线处理器
    async def on_message(msg: AgentMessage):
        await manager.broadcast({
            "type": "agent_message",
            "data": msg.model_dump(),
        })

    message_bus.add_websocket_handler(on_message)

    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message_bus.remove_websocket_handler(on_message)
