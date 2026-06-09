from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.schemas import AgentType, AgentStatus, AgentMessage, MessageType
from app.core.message_bus import message_bus


class ResearcherAgent(BaseAgent):
    """研究员智能体 - 负责信息收集与知识检索（ReAct模式）"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCHER,
            name="研究员",
            description="负责信息收集、知识检索与资料整理"
        )

    def _build_system_prompt(self) -> str:
        return """你是一位资深研究员，擅长信息收集与知识整理。你的职责是：
1. 围绕给定主题进行全面的信息收集
2. 整理关键概念、发展历程和重要节点
3. 识别核心问题和争议点
4. 收集相关数据和事实支撑

请按照以下结构输出研究结果：

## 研究主题概述
[主题的核心定义与背景]

## 关键概念与术语
[列出3-5个核心概念及其解释]

## 发展历程与重要节点
[梳理主题的发展脉络]

## 核心问题与争议
[识别2-3个关键问题]

## 相关数据与事实
[提供支撑性的事实和数据]

## 信息来源评估
[对信息可靠性进行简要评估]

要求：内容详实、逻辑清晰、信息准确，总字数800-1200字。"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行研究任务"""
        await self._update_status(AgentStatus.THINKING, "正在规划研究方案...")
        self.progress = 0.1

        research_focus = context.get("research_focus", task) if context else task
        dimensions = context.get("analysis_dimensions", []) if context else []

        prompt = f"""请对以下主题进行深入研究：

研究主题：{research_focus}

{"重点关注以下维度：" + "、".join(dimensions) if dimensions else ""}

请提供全面、深入的研究结果。"""

        self.progress = 0.3
        await self._update_status(AgentStatus.WORKING, "正在收集和整理信息...")

        result = await self._think(prompt, temperature=0.5)

        self.progress = 0.8
        await self._update_status(AgentStatus.WORKING, "正在整理研究结果...")

        self.progress = 1.0
        await self._update_status(AgentStatus.COMPLETED, "研究阶段完成")

        await self._publish_result(f"研究完成：已收集关于「{research_focus}」的详细信息")

        return result
