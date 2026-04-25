"""FastAPI 应用入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes.ranking import router as ranking_router
from routes.summary import router as summary_router
from routes.trend import router as trend_router


app = FastAPI(title="微博热搜分析系统", version="1.0.0")

# 开启跨域，方便本地前端直接请求后端接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ranking_router)
app.include_router(trend_router)
app.include_router(summary_router)


@app.get("/")
def index() -> dict:
    """基础健康检查接口。"""
    return {"message": "weibo hot backend is running"}
