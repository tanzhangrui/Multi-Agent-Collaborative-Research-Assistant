import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.agents.pipeline import agent_pipeline
from app.core.message_bus import message_bus
from app.core.task_manager import task_manager
from app.core.guardrails import validate_input

router = APIRouter()

# 研究历史存储（内存中）
research_history: list = []


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """处理用户聊天请求 - 非流式版本"""
    # 输入安全护栏
    is_valid, error_msg = await validate_input(request.message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        mode = request.mode.value if request.mode else "standard"
        result = await agent_pipeline.execute(
            topic=request.message,
            session_id=request.session_id or "default",
            mode=mode,
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))

        if result.get("status") == "cancelled":
            return {"status": "cancelled", "message": "任务已取消"}

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
        
        # 保存到历史
        research_history.append({
            "task_id": result.get("task_id"),
            "topic": result.get("topic", ""),
            "review_score": review.get("total_score", 0),
            "timestamp": result.get("task_id", ""),
        })
        
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE流式推送 - 实时展示智能体工作过程"""

    # 输入安全护栏
    is_valid, error_msg = await validate_input(request.message)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    mode = request.mode.value if request.mode else "standard"

    async def event_generator():
        queue = asyncio.Queue()
        
        async def on_event(event: Dict[str, Any]):
            await queue.put(event)
        
        # 启动pipeline
        async def run_pipeline():
            result = await agent_pipeline.execute(
                topic=request.message,
                session_id=request.session_id or "default",
                event_callback=on_event,
                mode=mode,
            )
            # 保存到历史
            if result.get("status") == "completed":
                review = result.get("review", {})
                research_history.append({
                    "task_id": result.get("task_id"),
                    "topic": result.get("topic", ""),
                    "review_score": review.get("total_score", 0),
                })
        
        pipeline_task = asyncio.create_task(run_pipeline())
        
        try:
            while not pipeline_task.done() or not queue.empty():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    event_data = json.dumps(event, ensure_ascii=False, default=str)
                    yield f"data: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield f": heartbeat\n\n"
                    continue
            
            # 确保pipeline完成
            await pipeline_task
        except asyncio.CancelledError:
            agent_pipeline.cancel()
            yield f"data: {json.dumps({'type': 'pipeline_cancelled'}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/api/agents/status")
async def get_agents_status():
    """获取所有智能体状态"""
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


@router.get("/api/history")
async def get_history():
    """获取研究历史"""
    return {"history": research_history[-20:]}


@router.post("/api/export")
async def export_report(request: ChatRequest):
    """导出报告为Markdown"""
    try:
        result = await agent_pipeline.execute(
            topic=request.message,
            session_id=request.session_id or "default",
        )
        
        if result.get("status") != "completed":
            raise HTTPException(status_code=500, detail="生成报告失败")
        
        report = result.get("report", "")
        review = result.get("review", {})
        
        markdown = f"""# {result.get('topic', '研究报告')}

## 质量评分: {review.get('total_score', 'N/A')}/100

---

{report}

---

## 审查详情

| 维度 | 得分 | 评语 |
|------|------|------|
"""
        for key, dim in review.get("dimensions", {}).items():
            dim_labels = {
                "completeness": "内容完整性",
                "coherence": "逻辑连贯性",
                "accuracy": "信息准确性",
                "depth": "分析深度",
                "clarity": "表达清晰度",
            }
            markdown += f"| {dim_labels.get(key, key)} | {dim.get('score', 'N/A')}/20 | {dim.get('comment', '')} |\n"
        
        from fastapi.responses import Response
        return Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=research_report.md"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
