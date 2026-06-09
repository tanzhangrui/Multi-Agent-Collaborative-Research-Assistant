import json
import asyncio
from typing import Dict, Any, Optional, Callable
from app.models.schemas import AgentType, AgentStatus, AgentMessage, MessageType, TaskStep
from app.agents.orchestrator import OrchestratorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.analyst import AnalystAgent
from app.agents.writer import WriterAgent
from app.agents.reviewer import ReviewerAgent
from app.core.message_bus import message_bus
from app.core.task_manager import task_manager


class AgentPipeline:
    """智能体协作管道 - 实现管道-过滤器风格的多智能体协作流程"""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
        self._running = False

    async def execute(self, topic: str, session_id: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """执行完整的多智能体协作流程"""
        self._running = True
        task = task_manager.create_task(topic=topic, session_id=session_id)

        try:
            # 阶段1：编排器 - 任务分解
            step1 = TaskStep(step_id=1, agent_type=AgentType.ORCHESTRATOR, agent_name="编排器", description="分析需求并分解任务")
            task.add_step(step1)

            await self._notify_progress("pipeline", "开始多智能体协作流程", 0.05)

            orchestration_result = await self.orchestrator.execute(topic)
            task_plan = json.loads(orchestration_result)
            task.update_step(1, status="completed", result="任务分解完成")

            if not self._running:
                return {"status": "cancelled"}

            await self._notify_progress("pipeline", "任务分解完成，开始研究阶段", 0.2)

            # 阶段2：研究员 - 信息收集
            step2 = TaskStep(step_id=2, agent_type=AgentType.RESEARCHER, agent_name="研究员", description="收集和整理研究信息")
            task.add_step(step2)

            research_result = await self.researcher.execute(
                topic,
                context={
                    "research_focus": task_plan.get("research_focus", topic),
                    "analysis_dimensions": task_plan.get("analysis_dimensions", []),
                }
            )
            task.update_step(2, status="completed", result="研究完成")

            if not self._running:
                return {"status": "cancelled"}

            await self._notify_progress("pipeline", "研究阶段完成，开始分析阶段", 0.45)

            # 阶段3：分析师 - 深度分析
            step3 = TaskStep(step_id=3, agent_type=AgentType.ANALYST, agent_name="分析师", description="深度分析与洞察提取")
            task.add_step(step3)

            analysis_result = await self.analyst.execute(
                topic,
                context={
                    "research_data": research_result,
                    "analysis_dimensions": task_plan.get("analysis_dimensions", []),
                }
            )
            task.update_step(3, status="completed", result="分析完成")

            if not self._running:
                return {"status": "cancelled"}

            await self._notify_progress("pipeline", "分析阶段完成，开始撰写报告", 0.65)

            # 阶段4：写作员 - 报告撰写
            step4 = TaskStep(step_id=4, agent_type=AgentType.WRITER, agent_name="写作员", description="撰写结构化研究报告")
            task.add_step(step4)

            report = await self.writer.execute(
                topic,
                context={
                    "research_data": research_result,
                    "analysis_data": analysis_result,
                    "writing_requirements": task_plan.get("writing_requirements", ""),
                }
            )
            task.update_step(4, status="completed", result="报告撰写完成")

            if not self._running:
                return {"status": "cancelled"}

            await self._notify_progress("pipeline", "报告撰写完成，开始质量审查", 0.85)

            # 阶段5：审查员 - 质量审查
            step5 = TaskStep(step_id=5, agent_type=AgentType.REVIEWER, agent_name="审查员", description="审查报告质量")
            task.add_step(step5)

            review_result = await self.reviewer.execute(
                topic,
                context={
                    "report": report,
                    "quality_criteria": task_plan.get("quality_criteria", ""),
                }
            )
            review_data = json.loads(review_result)
            task.update_step(5, status="completed", result=f"审查完成，评分: {review_data.get('total_score', 'N/A')}")

            await self._notify_progress("pipeline", "多智能体协作流程完成", 1.0)

            return {
                "status": "completed",
                "task_id": task.task_id,
                "topic": topic,
                "task_plan": task_plan,
                "research_result": research_result,
                "analysis_result": analysis_result,
                "report": report,
                "review": review_data,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            await self._notify_progress("pipeline", f"流程异常: {str(e)}", -1)
            return {
                "status": "error",
                "error": f"{type(e).__name__}: {str(e)}",
                "task_id": task.task_id,
            }
        finally:
            self._running = False

    def cancel(self):
        """取消当前流程"""
        self._running = False

    async def _notify_progress(self, channel: str, message: str, progress: float):
        """通知流程进度"""
        await message_bus.publish(
            channel,
            AgentMessage(
                agent_type=AgentType.ORCHESTRATOR,
                agent_name="系统",
                message_type=MessageType.PROGRESS,
                content=message,
                metadata={"progress": progress},
            )
        )


# 全局管道实例
agent_pipeline = AgentPipeline()
