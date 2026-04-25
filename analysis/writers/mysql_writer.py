"""统计结果写回 MySQL。"""

import pymysql
from pyspark.sql import DataFrame

from analysis.config import settings


def write_keyword_stats(df: DataFrame) -> None:
    """清空并写入关键词统计表。"""
    _replace_table_data(df, "hot_search_keyword_stats")


def write_daily_stats(df: DataFrame) -> None:
    """清空并写入每日统计表。"""
    _replace_table_data(df, "hot_search_daily_stats")


def _replace_table_data(df: DataFrame, table_name: str) -> None:
    """先 TRUNCATE 再 append，避免 Spark overwrite 重建 MySQL 表。"""
    print(f"[analysis] 正在清空 {table_name}")
    _truncate_table(table_name)

    if df.limit(1).count() == 0:
        print(f"[analysis] {table_name} 统计结果为空，已清空表，本次不写入数据")
        return

    print(f"[analysis] 正在写入 {table_name}")
    try:
        df.write.jdbc(
            url=settings.jdbc_url,
            table=table_name,
            mode="append",
            properties=settings.jdbc_properties,
        )
    except Exception as exc:
        print(f"[analysis] 写入 {table_name} 失败，请检查 JDBC Jar、表结构和数据库权限")
        raise RuntimeError(f"写入 {table_name} 失败") from exc


def _truncate_table(table_name: str) -> None:
    """只清空第三期统计表，不触碰 hot_search_raw。"""
    allowed_tables = {"hot_search_keyword_stats", "hot_search_daily_stats"}
    if table_name not in allowed_tables:
        raise ValueError(f"不允许清空非统计表：{table_name}")

    connection = None
    try:
        connection = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            charset=settings.mysql_charset,
            autocommit=True,
        )
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError(
                f"统计表 {table_name} 不存在，请先执行 sql/v3_stats.sql"
            ) from exc
        raise
    except pymysql.MySQLError as exc:
        print(f"[analysis] 清空 {table_name} 失败，请检查 MySQL 服务和账号权限：{exc}")
        raise RuntimeError(f"清空 {table_name} 失败") from exc
    finally:
        if connection is not None:
            connection.close()
