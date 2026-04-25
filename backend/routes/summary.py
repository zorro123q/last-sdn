"""统计概览接口。"""

from fastapi import APIRouter

from services.mysql_service import mysql_service


router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/summary")
def get_summary() -> dict:
    """返回系统概览统计信息。"""
    return mysql_service.get_summary()
