"""FastAPI 应用入口。"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import DatabaseConnectionError, DatabaseQueryError
from routes.analysis import router as analysis_router
from routes.ml_analysis import export_router as ml_export_router
from routes.ml_analysis import router as ml_analysis_router
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
app.include_router(analysis_router)
app.include_router(ml_analysis_router)
app.include_router(ml_export_router)


@app.exception_handler(DatabaseConnectionError)
async def handle_database_connection_error(
    request: Request, exc: DatabaseConnectionError
) -> JSONResponse:
    """数据库连接失败时返回中文提示，详细原因已在服务端日志打印。"""
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(DatabaseQueryError)
async def handle_database_query_error(
    request: Request, exc: DatabaseQueryError
) -> JSONResponse:
    """数据库查询失败时返回中文提示，避免前端只看到默认 500。"""
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/")
def index() -> dict:
    """基础健康检查接口。"""
    return {"message": "微博热搜后端服务运行中"}
