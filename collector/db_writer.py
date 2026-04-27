"""采集结果写入 MySQL。"""

from typing import Any

import pymysql

from config import settings


class MySQLWriter:
    """负责将采集结果批量写入数据库。"""

    def get_connection(self) -> pymysql.connections.Connection:
        """创建 MySQL 连接，连接失败时打印详细错误信息方便排查。"""
        try:
            conn = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_database,
                charset=settings.mysql_charset,
                autocommit=False,
            )
            return conn
        except pymysql.MySQLError as exc:
            print(
                f"[db_writer] MySQL 连接失败: host={settings.mysql_host}, "
                f"port={settings.mysql_port}, user={settings.mysql_user}, "
                f"db={settings.mysql_database}, error={exc}"
            )
            raise

    def save_records(self, records: list[dict[str, Any]]) -> int:
        """批量插入热搜记录并返回写入数量。"""
        if not records:
            print("[db_writer] 没有可写入的记录，跳过。")
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
            print(
                f"[db_writer] 成功写入 {len(values)} 条到 `{settings.mysql_database}`.hot_search_raw "
                f"(host={settings.mysql_host}:{settings.mysql_port})"
            )
            return len(values)
        except Exception as exc:
            connection.rollback()
            print(f"[db_writer] 写入失败，已回滚: {exc}")
            raise
        finally:
            connection.close()
