"""排行榜接口。"""

from fastapi import APIRouter

from services.mysql_service import mysql_service


router = APIRouter(prefix="/api/ranking", tags=["ranking"])


@router.get("/current")
def get_current_ranking() -> dict:
    """返回最新一次采集的热搜榜。"""
    return mysql_service.get_current_ranking()
