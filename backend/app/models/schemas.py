from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class MessageType(str, Enum):
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    COLLABORATION = "collaboration"
    PROGRESS = "progress"
    ERROR = "error"
    SYSTEM = "system"


class ResearchMode(str, Enum):
    QUICK = "quick"          # 快速研究：2个智能体（编排+写作）
    STANDARD = "standard"    # 标准研究：5个智能体全流程
    DEEP = "deep"            # 深度研究：5个智能体 + 反思闭环 + 并行研究


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    mode: Optional[ResearchMode] = ResearchMode.STANDARD


class AgentMessage(BaseModel):
    agent_type: AgentType
    agent_name: str
    message_type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    agent_type: AgentType
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    progress: float = 0.0
    last_activity: datetime = Field(default_factory=datetime.now)


class TaskStep(BaseModel):
    step_id: int
    agent_type: AgentType
    agent_name: str
    description: str
    status: str = "pending"
    result: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResearchReport(BaseModel):
    topic: str
    summary: str
    key_findings: List[str]
    detailed_analysis: str
    conclusions: str
    suggestions: List[str]
    quality_score: float = 0.0


class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
