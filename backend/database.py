"""数据库连接管理。"""

import pymysql
from pymysql.cursors import DictCursor

from config import settings


def get_connection() -> pymysql.connections.Connection:
    """创建一个用于查询的 MySQL 连接。"""
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
