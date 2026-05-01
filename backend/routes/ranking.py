"""排行榜接口。"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.mysql_service import mysql_service
from database import DatabaseConnectionError


router = APIRouter(prefix="/api/ranking", tags=["ranking"])


@router.get("/current")
def get_current_ranking() -> dict:
    """
    返回最新一次采集的热搜榜。
    数据库为空时返回 count=0、items=[] 和中文提示，不返回 500。
    """
    try:
        data = mysql_service.get_current_ranking()
    except DatabaseConnectionError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "detail": str(exc),
                "tip": "请确认 MySQL 已启动，并检查 .env 中的数据库配置",
            },
        )

    if not data.get("count"):
        data["tip"] = "当前暂无热搜数据，请先运行 python collector\\app.py"
    else:
        data["tip"] = ""
    return data
