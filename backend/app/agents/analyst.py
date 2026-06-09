from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.schemas import AgentType, AgentStatus
from app.core.message_bus import message_bus


class AnalystAgent(BaseAgent):
    """分析师智能体 - 负责深度分析与洞察提取"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.ANALYST,
            name="分析师",
            description="负责深度分析、洞察提取与趋势研判"
        )

    def _build_system_prompt(self) -> str:
        return """你是一位专业分析师，擅长深度分析与洞察提取。你的职责是：
1. 基于研究资料进行深度分析
2. 发现数据背后的规律和趋势
3. 提出有见地的观点和判断
4. 评估不同因素的影响程度

请按照以下结构输出分析结果：

## 核心发现
[总结3-5个最重要的发现]

## 深度分析
### 维度一：[分析维度名称]
[详细分析内容]

### 维度二：[分析维度名称]
[详细分析内容]

### 维度三：[分析维度名称]
[详细分析内容]

## 趋势研判
[对未来发展趋势的判断]

## 风险与挑战
[识别潜在风险和挑战]

## 机遇与建议
[发现机遇并提出建议]

要求：分析深入、逻辑严谨、观点鲜明，总字数800-1200字。"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行分析任务"""
        await self._update_status(AgentStatus.THINKING, "正在制定分析框架...")
        self.progress = 0.1

        research_data = context.get("research_data", "") if context else ""
        dimensions = context.get("analysis_dimensions", []) if context else []

        prompt = f"""请基于以下研究资料进行深度分析：

研究主题：{task}

研究资料：
{research_data}

{"分析维度：" + "、".join(dimensions) if dimensions else ""}

请提供深入、专业的分析结果。"""

        self.progress = 0.3
        await self._update_status(AgentStatus.WORKING, "正在进行深度分析...")

        result = await self._think(prompt, temperature=0.5)

        self.progress = 1.0
        await self._update_status(AgentStatus.COMPLETED, "分析阶段完成")

        await self._publish_result(f"分析完成：已完成对「{task}」的深度分析")

        return result
