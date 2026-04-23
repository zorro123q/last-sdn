"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes.ranking import router as ranking_router
from routes.summary import router as summary_router
from routes.trend import router as trend_router


settings = get_settings()

app = FastAPI(
    title="微博热搜准实时分析系统",
    version="0.1.0",
    description="第一版最小可运行后端接口服务。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ranking_router, prefix="/api")
app.include_router(trend_router, prefix="/api")
app.include_router(summary_router, prefix="/api")


@app.get("/health")
def health_check():
    """基础健康检查。"""

    return {"status": "ok"}
