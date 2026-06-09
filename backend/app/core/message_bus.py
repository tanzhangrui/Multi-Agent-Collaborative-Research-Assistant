import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from app.models.schemas import AgentMessage, AgentType, MessageType


class MessageBus:
    """消息总线 - 实现观察者模式，支持智能体间的异步通信"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._message_history: List[AgentMessage] = []
        self._websocket_handlers: List[Callable] = []

    def subscribe(self, channel: str, handler: Callable):
        """订阅消息通道"""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(handler)

    def unsubscribe(self, channel: str, handler: Callable):
        """取消订阅"""
        if channel in self._subscribers:
            self._subscribers[channel] = [h for h in self._subscribers[channel] if h != handler]

    async def publish(self, channel: str, message: AgentMessage):
        """发布消息到指定通道"""
        self._message_history.append(message)
        # 通知订阅者
        if channel in self._subscribers:
            for handler in self._subscribers[channel]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    print(f"消息处理错误: {e}")
        # 通知WebSocket处理器
        for ws_handler in self._websocket_handlers:
            try:
                await ws_handler(message)
            except Exception as e:
                print(f"WebSocket推送错误: {e}")

    def add_websocket_handler(self, handler: Callable):
        """添加WebSocket推送处理器"""
        self._websocket_handlers.append(handler)

    def remove_websocket_handler(self, handler: Callable):
        """移除WebSocket推送处理器"""
        self._websocket_handlers = [h for h in self._websocket_handlers if h != handler]

    def get_history(self, limit: int = 50) -> List[AgentMessage]:
        """获取消息历史"""
        return self._message_history[-limit:]


# 全局消息总线实例
message_bus = MessageBus()
