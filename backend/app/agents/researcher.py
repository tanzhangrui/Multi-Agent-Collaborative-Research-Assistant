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
        return """你是一位学术研究员，专注于客观的信息收集与知识整理。

【核心原则】
- 只输出客观、中立、基于事实的学术性内容
- 所有分析必须保持专业和严谨
- 避免任何主观判断或争议性表述

【工作职责】
1. 围绕给定主题进行客观的信息收集与整理
2. 梳理相关领域的关键概念和发展脉络
3. 归纳学术界公认的研究观点和数据

【输出格式】请按以下结构输出：

## 研究主题概述
[客观描述主题的核心定义与研究背景]

## 关键概念与术语
[列出3-5个核心概念及其学术定义]

## 发展历程与重要节点
[梳理该领域的学术发展脉络]

## 主要研究方向
[归纳2-3个当前主要的研究方向]

## 相关数据与事实
[提供已知的、可验证的事实和数据]

要求：内容客观中立、逻辑清晰、信息准确，总字数800-1200字。"""

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
