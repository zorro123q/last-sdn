"""数据库连接管理。"""

import pymysql
from pymysql.cursors import DictCursor

from config import settings


class DatabaseConnectionError(RuntimeError):
    """数据库连接失败时抛出，供 FastAPI 统一返回中文提示。"""


class DatabaseQueryError(RuntimeError):
    """数据库查询失败时抛出，供 FastAPI 统一返回中文提示。"""


def get_connection() -> pymysql.connections.Connection:
    """创建一个用于查询的 MySQL 连接。"""
    try:
        return pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            charset=settings.mysql_charset,
            cursorclass=DictCursor,
            autocommit=True,
        )
    except pymysql.MySQLError as exc:
        print(f"[backend] 数据库连接失败：{exc}")
        raise DatabaseConnectionError("数据库连接失败，请检查 MySQL 服务和 .env 配置") from exc
