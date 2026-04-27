"""趋势查询接口。"""

from fastapi import APIRouter, HTTPException, Query

from services.mysql_service import mysql_service


router = APIRouter(prefix="/api/trend", tags=["trend"])


@router.get("")
def get_keyword_trend(keyword: str = Query(..., description="查询关键词")) -> dict:
    """根据关键词查询历史热度趋势。"""
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    return mysql_service.get_keyword_trend(keyword)
