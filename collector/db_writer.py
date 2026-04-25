"""采集结果写入 MySQL。"""

from typing import Any

import pymysql

from config import settings


class MySQLWriter:
    """负责将采集结果批量写入数据库。"""

    def get_connection(self) -> pymysql.connections.Connection:
        """创建 MySQL 连接。"""
        return pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            charset=settings.mysql_charset,
            autocommit=False,
        )

    def save_records(self, records: list[dict[str, Any]]) -> int:
        """批量插入热搜记录并返回写入数量。"""
        if not records:
            return 0

        sql = """
        INSERT INTO hot_search_raw (title, rank_num, hot_value, source, fetch_time)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = [
            (
                item["title"],
                item["rank_num"],
                item["hot_value"],
                item["source"],
                item["fetch_time"],
            )
            for item in records
        ]

        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.executemany(sql, values)
            connection.commit()
            return len(values)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
