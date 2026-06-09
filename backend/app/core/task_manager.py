import uuid
from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import TaskStep, AgentType


class Task:
    """任务实体"""
    def __init__(self, topic: str, session_id: str):
        self.task_id = str(uuid.uuid4())[:8]
        self.topic = topic
        self.session_id = session_id
        self.steps: List[TaskStep] = []
        self.status = "pending"
        self.created_at = datetime.now()
        self.result: Optional[str] = None

    def add_step(self, step: TaskStep):
        self.steps.append(step)

    def update_step(self, step_id: int, **kwargs):
        for step in self.steps:
            if step.step_id == step_id:
                for key, value in kwargs.items():
                    setattr(step, key, value)
                break


class TaskManager:
    """任务管理器 - 管理研究任务的生命周期"""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(self, topic: str, session_id: str) -> Task:
        task = Task(topic=topic, session_id=session_id)
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_session_tasks(self, session_id: str) -> List[Task]:
        return [t for t in self._tasks.values() if t.session_id == session_id]


# 全局任务管理器
task_manager = TaskManager()
