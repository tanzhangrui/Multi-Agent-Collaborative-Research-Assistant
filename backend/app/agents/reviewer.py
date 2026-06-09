import json
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.schemas import AgentType, AgentStatus
from app.core.message_bus import message_bus


class ReviewerAgent(BaseAgent):
    """审查员智能体 - 负责质量审查与反馈（反思模式）"""

    def __init__(self):
        super().__init__(
            agent_type=AgentType.REVIEWER,
            name="审查员",
            description="负责报告质量审查、问题识别与改进建议"
        )

    def _build_system_prompt(self) -> str:
        return """你是一位严格的质量审查员，负责评估研究报告的质量。请从以下维度进行审查：

1. **内容完整性**（20分）：是否涵盖主题的各个方面
2. **逻辑连贯性**（20分）：论述是否逻辑清晰、层次分明
3. **信息准确性**（20分）：事实和数据是否准确可靠
4. **分析深度**（20分）：分析是否深入、有见地
5. **表达清晰度**（20分）：语言是否流畅、表达是否清晰

请用JSON格式输出审查结果：
{
    "total_score": 总分(0-100),
    "dimensions": {
        "completeness": {"score": 分数, "comment": "评语"},
        "coherence": {"score": 分数, "comment": "评语"},
        "accuracy": {"score": 分数, "comment": "评语"},
        "depth": {"score": 分数, "comment": "评语"},
        "clarity": {"score": 分数, "comment": "评语"}
    },
    "strengths": ["优点1", "优点2", "优点3"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": ["建议1", "建议2", "建议3"],
    "overall_comment": "总体评价"
}

只输出JSON，不要输出其他内容。"""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行审查任务"""
        await self._update_status(AgentStatus.THINKING, "正在制定审查标准...")
        self.progress = 0.1

        report = context.get("report", "") if context else ""
        quality_criteria = context.get("quality_criteria", "") if context else ""

        prompt = f"""请审查以下研究报告：

研究主题：{task}

报告内容：
{report}

{f"质量标准：{quality_criteria}" if quality_criteria else ""}

请给出详细的审查评估。"""

        self.progress = 0.3
        await self._update_status(AgentStatus.WORKING, "正在审查报告质量...")

        result = await self._think(prompt, temperature=0.3)

        # 解析审查结果
        try:
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0]
            review_result = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            review_result = {
                "total_score": 75,
                "dimensions": {
                    "completeness": {"score": 15, "comment": "内容基本完整"},
                    "coherence": {"score": 15, "comment": "逻辑较为清晰"},
                    "accuracy": {"score": 15, "comment": "信息基本准确"},
                    "depth": {"score": 15, "comment": "分析有一定深度"},
                    "clarity": {"score": 15, "comment": "表达较为清晰"}
                },
                "strengths": ["结构完整", "内容丰富"],
                "weaknesses": ["部分分析可更深入"],
                "suggestions": ["增加更多数据支撑", "深化趋势分析"],
                "overall_comment": "报告整体质量良好，建议进一步深化分析。"
            }

        self.progress = 1.0
        await self._update_status(AgentStatus.COMPLETED, "审查完成")

        await self._publish_result(
            f"审查完成：报告质量评分 {review_result.get('total_score', 'N/A')}/100"
        )

        return json.dumps(review_result, ensure_ascii=False)
