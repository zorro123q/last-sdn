"""统计概览接口。"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.mysql_service import mysql_service
from database import DatabaseConnectionError


router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/summary")
def get_summary() -> dict:
    """
    返回系统概览统计信息。
    数据库为空时返回全零数据和中文提示，不会返回 500。
    """
    try:
        data = mysql_service.get_summary()
    except DatabaseConnectionError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "detail": str(exc),
                "tip": "请确认 MySQL 已启动，并检查 .env 中的数据库配置",
            },
        )

    if not data.get("total_records"):
        data["tip"] = "当前暂无数据，请先运行 python collector\\app.py 进行采集"
    else:
        data["tip"] = ""
    return data
