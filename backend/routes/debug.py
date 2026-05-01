"""数据库状态调试接口，方便排查 collector 与 backend 是否连接同一个库。"""

from datetime import datetime
from typing import Any

import pymysql
from fastapi import APIRouter

from config import settings
from database import get_connection, DatabaseConnectionError, DatabaseQueryError


router = APIRouter(prefix="/api/debug", tags=["debug"])


def _fmt(value: Any) -> Any:
    """把 datetime 转成字符串，其他类型原样返回。"""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


@router.get("/db-status")
def get_db_status() -> dict:
    """
    返回当前后端所连接的数据库基础状态。
    用于核查 collector 和 backend 是否指向同一个库。
    注意：不返回数据库密码。
    """
    connection_info = {
        "mysql_host": settings.mysql_host,
        "mysql_port": settings.mysql_port,
        "mysql_user": settings.mysql_user,
        "mysql_database": settings.mysql_database,
    }

    try:
        conn = get_connection()
    except DatabaseConnectionError as exc:
        return {
            "connection_info": connection_info,
            "connected": False,
            "error": str(exc),
            "total_records": None,
            "latest_fetch_time": None,
            "latest_5_records": [],
        }

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_records FROM hot_search_raw")
            total_row = cursor.fetchone() or {}
            total_records = total_row.get("total_records", 0)

            cursor.execute("SELECT MAX(fetch_time) AS latest_fetch_time FROM hot_search_raw")
            time_row = cursor.fetchone() or {}
            latest_fetch_time = _fmt(time_row.get("latest_fetch_time"))

            cursor.execute(
                "SELECT id, title, rank_num, hot_value, source, fetch_time "
                "FROM hot_search_raw ORDER BY id DESC LIMIT 5"
            )
            latest_5 = [
                {k: _fmt(v) for k, v in row.items()}
                for row in (cursor.fetchall() or [])
            ]

        return {
            "connection_info": connection_info,
            "connected": True,
            "total_records": total_records,
            "latest_fetch_time": latest_fetch_time,
            "latest_5_records": latest_5,
            "tip": (
                "如果 total_records 为 0，说明数据库尚无数据，"
                "请先运行 python collector/app.py"
            ) if total_records == 0 else "数据库连接正常",
        }
    except pymysql.MySQLError as exc:
        return {
            "connection_info": connection_info,
            "connected": True,
            "error": f"查询失败：{exc}",
            "total_records": None,
            "latest_fetch_time": None,
            "latest_5_records": [],
        }
    finally:
        conn.close()
