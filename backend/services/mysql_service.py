"""MySQL 查询服务。"""

from typing import Dict, List

from config import BackendConfig
from database import get_mysql_connection


def get_keyword_trend(keyword: str, config: BackendConfig) -> Dict[str, object]:
    """查询关键词热度趋势，第一版按采集时间聚合最大热度值。"""

    connection = get_mysql_connection(config)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    DATE_FORMAT(fetch_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS fetch_time,
                    MAX(hot_value) AS hot_value,
                    MIN(rank_no) AS best_rank
                FROM {config.mysql_table_raw}
                WHERE title LIKE %s
                GROUP BY DATE_FORMAT(fetch_time, '%%Y-%%m-%%d %%H:%%i:%%s')
                ORDER BY fetch_time ASC
                LIMIT 200
                """,
                (f"%{keyword.strip()}%",),
            )
            rows: List[Dict[str, object]] = cursor.fetchall()

        return {
            "keyword": keyword,
            "data": rows,
        }
    finally:
        connection.close()


def get_summary(config: BackendConfig) -> Dict[str, object]:
    """查询总记录数、关键词数和最新采集时间。"""

    connection = get_mysql_connection(config)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT title) AS unique_keywords,
                    MAX(fetch_time) AS latest_fetch_time
                FROM {config.mysql_table_raw}
                """
            )
            row = cursor.fetchone() or {}

        latest_fetch_time = row.get("latest_fetch_time")
        latest_fetch_time_text = latest_fetch_time.strftime("%Y-%m-%d %H:%M:%S") if latest_fetch_time else None

        return {
            "total_records": int(row.get("total_records", 0) or 0),
            "unique_keywords": int(row.get("unique_keywords", 0) or 0),
            "latest_fetch_time": latest_fetch_time_text,
        }
    finally:
        connection.close()
