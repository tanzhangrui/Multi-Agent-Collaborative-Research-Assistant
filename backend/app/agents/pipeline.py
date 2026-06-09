import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
from app.models.schemas import AgentType, AgentStatus, AgentMessage, MessageType, TaskStep
from app.agents.orchestrator import OrchestratorAgent
from app.agents.researcher import ResearcherAgent
from app.agents.analyst import AnalystAgent
from app.agents.writer import WriterAgent
from app.agents.reviewer import ReviewerAgent
from app.core.message_bus import message_bus
from app.core.task_manager import task_manager

EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class AgentPipeline:
    """智能体协作管道 - 实现管道-过滤器风格的多智能体协作流程"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
        self._running = False
    
    async def emit_event(self, callback: Optional[EventCallback], event: Dict[str, Any]):
        """发送事件"""
        if callback:
            try:
                await callback(event)
            except Exception as e:
                print(f"Event callback error: {e}")
        # 同时通过消息总线广播
        try:
            await message_bus.publish(
                "pipeline_events",
                AgentMessage(
                    agent_type=event.get("agent_type", AgentType.ORCHESTRATOR) if isinstance(event.get("agent_type"), AgentType) else AgentType.ORCHESTRATOR,
                    agent_name=event.get("agent_name", "系统"),
                    message_type=MessageType.PROGRESS,
                    content=event.get("message", ""),
                    metadata=event,
                )
            )
        except Exception as e:
            print(f"Message bus publish error in emit_event: {e}")
    
    async def execute(self, topic: str, session_id: str, event_callback: Optional[EventCallback] = None) -> Dict[str, Any]:
        """执行完整的多智能体协作流程，通过event_callback实时推送进度"""
        self._running = True
        task = task_manager.create_task(topic=topic, session_id=session_id)
        
        try:
            # 流程开始
            await self.emit_event(event_callback, {
                "type": "pipeline_start",
                "topic": topic,
                "task_id": task.task_id,
                "message": f"开始研究：{topic}",
                "progress": 0.0,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 阶段1：编排器 - 任务分解
            await self.emit_event(event_callback, {
                "type": "agent_start",
                "agent_type": "orchestrator",
                "agent_name": "编排器",
                "step": 1,
                "description": "分析需求并分解任务",
                "message": "编排器正在分析需求...",
                "progress": 0.05,
                "timestamp": datetime.now().isoformat(),
            })
            
            orchestration_result = await self.orchestrator.execute(topic)
            task_plan = json.loads(orchestration_result)
            
            await self.emit_event(event_callback, {
                "type": "agent_output",
                "agent_type": "orchestrator",
                "agent_name": "编排器",
                "step": 1,
                "output": task_plan,
                "message": "任务分解完成",
                "progress": 0.2,
                "timestamp": datetime.now().isoformat(),
            })
            
            if not self._running:
                return {"status": "cancelled"}
            
            # 阶段2：研究员 - 信息收集
            await self.emit_event(event_callback, {
                "type": "agent_start",
                "agent_type": "researcher",
                "agent_name": "研究员",
                "step": 2,
                "description": "收集和整理研究信息",
                "message": "研究员正在收集信息...",
                "progress": 0.2,
                "timestamp": datetime.now().isoformat(),
            })
            
            research_result = await self.researcher.execute(
                topic,
                context={
                    "research_focus": task_plan.get("research_focus", topic),
                    "analysis_dimensions": task_plan.get("analysis_dimensions", []),
                }
            )
            
            await self.emit_event(event_callback, {
                "type": "agent_output",
                "agent_type": "researcher",
                "agent_name": "研究员",
                "step": 2,
                "output": research_result,
                "message": "信息收集完成",
                "progress": 0.4,
                "timestamp": datetime.now().isoformat(),
            })
            
            if not self._running:
                return {"status": "cancelled"}
            
            # 阶段3：分析师 - 深度分析
            await self.emit_event(event_callback, {
                "type": "agent_start",
                "agent_type": "analyst",
                "agent_name": "分析师",
                "step": 3,
                "description": "深度分析与洞察提取",
                "message": "分析师正在进行深度分析...",
                "progress": 0.4,
                "timestamp": datetime.now().isoformat(),
            })
            
            analysis_result = await self.analyst.execute(
                topic,
                context={
                    "research_data": research_result,
                    "analysis_dimensions": task_plan.get("analysis_dimensions", []),
                }
            )
            
            await self.emit_event(event_callback, {
                "type": "agent_output",
                "agent_type": "analyst",
                "agent_name": "分析师",
                "step": 3,
                "output": analysis_result,
                "message": "深度分析完成",
                "progress": 0.6,
                "timestamp": datetime.now().isoformat(),
            })
            
            if not self._running:
                return {"status": "cancelled"}
            
            # 阶段4：写作员 - 报告撰写
            await self.emit_event(event_callback, {
                "type": "agent_start",
                "agent_type": "writer",
                "agent_name": "写作员",
                "step": 4,
                "description": "撰写结构化研究报告",
                "message": "写作员正在撰写报告...",
                "progress": 0.6,
                "timestamp": datetime.now().isoformat(),
            })
            
            report = await self.writer.execute(
                topic,
                context={
                    "research_data": research_result,
                    "analysis_data": analysis_result,
                    "writing_requirements": task_plan.get("writing_requirements", ""),
                }
            )
            
            await self.emit_event(event_callback, {
                "type": "agent_output",
                "agent_type": "writer",
                "agent_name": "写作员",
                "step": 4,
                "output": report,
                "message": "报告撰写完成",
                "progress": 0.8,
                "timestamp": datetime.now().isoformat(),
            })
            
            if not self._running:
                return {"status": "cancelled"}
            
            # 阶段5：审查员 - 质量审查
            await self.emit_event(event_callback, {
                "type": "agent_start",
                "agent_type": "reviewer",
                "agent_name": "审查员",
                "step": 5,
                "description": "审查报告质量",
                "message": "审查员正在评估报告质量...",
                "progress": 0.8,
                "timestamp": datetime.now().isoformat(),
            })
            
            review_result = await self.reviewer.execute(
                topic,
                context={
                    "report": report,
                    "quality_criteria": task_plan.get("quality_criteria", ""),
                }
            )
            review_data = json.loads(review_result)
            
            await self.emit_event(event_callback, {
                "type": "agent_output",
                "agent_type": "reviewer",
                "agent_name": "审查员",
                "step": 5,
                "output": review_data,
                "message": f"质量审查完成，评分: {review_data.get('total_score', 'N/A')}/100",
                "progress": 1.0,
                "timestamp": datetime.now().isoformat(),
            })
            
            # 流程完成
            result = {
                "status": "completed",
                "task_id": task.task_id,
                "topic": topic,
                "task_plan": task_plan,
                "research_result": research_result,
                "analysis_result": analysis_result,
                "report": report,
                "review": review_data,
            }
            
            await self.emit_event(event_callback, {
                "type": "pipeline_complete",
                "result": result,
                "message": "多智能体协作流程完成",
                "progress": 1.0,
                "timestamp": datetime.now().isoformat(),
            })
            
            return result
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            await self.emit_event(event_callback, {
                "type": "pipeline_error",
                "error": f"{type(e).__name__}: {str(e)}",
                "message": f"流程异常: {str(e)}",
                "progress": -1,
                "timestamp": datetime.now().isoformat(),
            })
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


# 全局管道实例
agent_pipeline = AgentPipeline()
