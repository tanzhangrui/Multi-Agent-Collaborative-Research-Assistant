import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api.routes import router
from app.api.websocket import websocket_endpoint
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 多智能体协作研究助手启动中...")
    print(f"📡 API地址: http://{settings.HOST}:{settings.PORT}")
    print(f"🌐 前端地址: http://localhost:8000")
    yield
    # Shutdown
    from app.core.llm_client import llm_client
    await llm_client.close()
    print("👋 系统已关闭")


app = FastAPI(
    title="多智能体协作研究助手",
    description="基于多智能体协作的智能研究助手系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

# WebSocket路由
app.add_api_websocket_route("/ws", websocket_endpoint)

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Multi-Agent Research Assistant"}


# 静态文件服务
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
