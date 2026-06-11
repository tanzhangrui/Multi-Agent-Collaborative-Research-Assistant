from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.schemas import AgentType, AgentStatus
from app.core.message_bus import message_bus


class WriterAgent(BaseAgent):
    """写作员智能体 - 负责报告撰写与内容整合"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.WRITER,
            name="写作员",
            description="负责报告撰写、内容整合与格式优化"
        )

    def _build_system_prompt(self) -> str:
        return """你是一位学术写作专家，擅长将研究成果整合为结构清晰、客观严谨的研究报告。

【核心原则】
- 只输出客观、中立、基于事实的学术性内容
- 所有论述必须有研究资料支撑
- 保持专业严谨的学术表达风格
- 不使用夸张或情绪化语言

【工作职责】
1. 整合研究和分析结果
2. 撰写结构化的学术研究报告
3. 确保内容逻辑连贯、表达清晰

【输出格式】请按以下结构撰写：

# {研究主题} - 研究报告

## 摘要
[200字以内的研究概述]

## 一、研究背景与意义
[研究主题的背景介绍与研究意义]

## 二、主要研究发现
[分点阐述核心研究发现]

## 三、深度分析讨论
[基于分析结果的深入讨论]

## 四、发展趋势展望
[对未来发展的客观展望]

## 五、结论与建议
[核心结论与建设性建议]

## 参考文献
[列出信息来源类型]

要求：结构完整、逻辑清晰、语言专业，总字数1500-2500字。使用Markdown格式。"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行写作任务"""
        await self._update_status(AgentStatus.THINKING, "正在规划报告结构...")
        self.progress = 0.1

        research_data = context.get("research_data", "") if context else ""
        analysis_data = context.get("analysis_data", "") if context else ""
        writing_req = context.get("writing_requirements", "") if context else ""

        prompt = f"""请基于以下信息撰写研究报告：

研究主题：{task}

研究资料：
{research_data}

分析结果：
{analysis_data}

{f"写作要求：{writing_req}" if writing_req else ""}

请撰写一份完整、专业的研究报告。"""

        self.progress = 0.3
        await self._update_status(AgentStatus.WORKING, "正在撰写研究报告...")

        result = await self._think(prompt, temperature=0.6)

        self.progress = 1.0
        await self._update_status(AgentStatus.COMPLETED, "报告撰写完成")

        await self._publish_result(f"写作完成：已生成「{task}」研究报告")

        return result
