from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.schemas import AgentType, AgentStatus, AgentState, AgentMessage, MessageType
from app.core.llm_client import llm_client
from app.core.message_bus import message_bus


class BaseAgent(ABC):
    """智能体基类 - 定义智能体的核心接口与通用行为"""

    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.progress = 0.0
        self._system_prompt = self._build_system_prompt()

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        pass

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行任务 - 子类必须实现"""
        pass

    def get_state(self) -> AgentState:
        """获取智能体当前状态"""
        return AgentState(
            agent_type=self.agent_type,
            agent_name=self.name,
            status=self.status,
            current_task=self.current_task,
            progress=self.progress,
            last_activity=datetime.now(),
        )

    async def _update_status(self, status: AgentStatus, message: str = ""):
        """更新智能体状态并广播"""
        self.status = status
        try:
            await message_bus.publish(
                f"agent_{self.agent_type.value}",
                AgentMessage(
                    agent_type=self.agent_type,
                    agent_name=self.name,
                    message_type=MessageType.PROGRESS,
                    content=message or f"{self.name} 状态变更为 {status.value}",
                    metadata={"status": status.value, "progress": self.progress},
                )
            )
        except Exception as e:
            print(f"Message bus publish error in _update_status: {e}")

    async def _think(self, prompt: str, temperature: float = 0.7) -> str:
        """调用LLM进行思考"""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": prompt},
        ]
        result = await llm_client.chat(messages, temperature=temperature)
        return result

    async def _publish_result(self, content: str, message_type: MessageType = MessageType.TASK_RESULT):
        """发布任务结果"""
        try:
            await message_bus.publish(
                "task_results",
                AgentMessage(
                    agent_type=self.agent_type,
                    agent_name=self.name,
                    message_type=message_type,
                    content=content,
                )
            )
        except Exception as e:
            print(f"Message bus publish error in _publish_result: {e}")
