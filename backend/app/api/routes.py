import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest
from app.agents.pipeline import agent_pipeline
from app.core.message_bus import message_bus

router = APIRouter()


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """处理用户聊天请求 - 启动多智能体协作流程"""
    try:
        result = await agent_pipeline.execute(
            topic=request.message,
            session_id=request.session_id or "default",
        )

        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))

        if result.get("status") == "cancelled":
            return {"status": "cancelled", "message": "任务已取消"}

        # 构建响应
        review = result.get("review", {})
        research_result = result.get("research_result", "")
        analysis_result = result.get("analysis_result", "")
        response_data = {
            "status": "success",
            "task_id": result.get("task_id"),
            "topic": result.get("topic", ""),
            "task_plan": result.get("task_plan", {}),
            "report": result.get("report", ""),
            "review": review,
            "research_summary": research_result[:500] + "..." if len(research_result) > 500 else research_result,
            "analysis_summary": analysis_result[:500] + "..." if len(analysis_result) > 500 else analysis_result,
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agents/status")
async def get_agents_status():
    """获取所有智能体状态"""
    from app.agents.pipeline import agent_pipeline

    agents = [
        agent_pipeline.orchestrator,
        agent_pipeline.researcher,
        agent_pipeline.analyst,
        agent_pipeline.writer,
        agent_pipeline.reviewer,
    ]

    return {
        "agents": [agent.get_state().model_dump() for agent in agents]
    }


@router.get("/api/messages/history")
async def get_message_history(limit: int = 50):
    """获取消息历史"""
    messages = message_bus.get_history(limit)
    return {
        "messages": [msg.model_dump() for msg in messages]
    }


@router.post("/api/cancel")
async def cancel_task():
    """取消当前任务"""
    agent_pipeline.cancel()
    return {"status": "cancelled"}
