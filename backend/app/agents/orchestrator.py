import json
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.schemas import AgentType, AgentStatus, AgentMessage, MessageType
from app.core.message_bus import message_bus


class OrchestratorAgent(BaseAgent):
    """编排器智能体 - 负责任务分解与智能体调度（ReAct模式）"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ORCHESTRATOR,
            name="编排器",
            description="负责任务分解、智能体调度与结果汇总"
        )

    def _build_system_prompt(self) -> str:
        return """你是一个智能任务编排器。你的职责是：
1. 分析用户的研究需求
2. 将复杂任务分解为可执行的子任务
3. 为每个子任务分配合适的智能体
4. 确保任务流程的逻辑性和完整性

你需要将研究任务分解为以下步骤：
- 研究阶段：收集和整理相关信息（分配给研究员）
- 分析阶段：深入分析研究数据（分配给分析师）
- 写作阶段：撰写结构化报告（分配给写作员）
- 审查阶段：审查报告质量（分配给审查员）

请用JSON格式输出任务分解结果，格式如下：
{
    "task_summary": "任务概述",
    "research_focus": "研究重点方向",
    "analysis_dimensions": ["分析维度1", "分析维度2", "分析维度3"],
    "writing_requirements": "写作要求",
    "quality_criteria": "质量标准"
}

只输出JSON，不要输出其他内容。"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行任务分解"""
        await self._update_status(AgentStatus.THINKING, "正在分析用户需求...")
        self.progress = 0.1

        prompt = f"请分析以下研究需求并分解任务：\n\n{task}"
        result = await self._think(prompt, temperature=0.3)

        self.progress = 0.5
        await self._update_status(AgentStatus.WORKING, "正在分解任务并分配智能体...")

        # 解析任务分解结果
        try:
            # 尝试提取JSON
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]

            task_plan = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            task_plan = {
                "task_summary": task,
                "research_focus": task,
                "analysis_dimensions": ["背景分析", "现状评估", "趋势预测"],
                "writing_requirements": "结构清晰、逻辑连贯的研究报告",
                "quality_criteria": "信息准确、分析深入、建议可行"
            }

        self.progress = 1.0
        await self._update_status(AgentStatus.COMPLETED, "任务分解完成")

        # 广播任务计划
        await message_bus.publish(
            "orchestration",
            AgentMessage(
                agent_type=self.agent_type,
                agent_name=self.name,
                message_type=MessageType.TASK_ASSIGN,
                content=f"任务计划已生成：{task_plan['task_summary']}",
                metadata=task_plan,
            )
        )

        return json.dumps(task_plan, ensure_ascii=False)
