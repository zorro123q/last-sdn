"""MySQL 查询服务。"""

from datetime import datetime
from typing import Any

from database import get_connection


class MySQLService:
    """封装排行榜、趋势和统计查询逻辑。"""

    def get_current_ranking(self) -> dict[str, Any]:
        """返回最新一批热搜榜数据。"""
        latest_fetch_time = self._get_latest_fetch_time()
        if latest_fetch_time is None:
            return {"latest_fetch_time": None, "count": 0, "items": []}

        sql = """
        SELECT title, rank_num, hot_value, source, fetch_time
        FROM hot_search_raw
        WHERE fetch_time = %s
        ORDER BY rank_num ASC, hot_value DESC, id ASC
        """
        rows = self._fetch_all(sql, (latest_fetch_time,))
        return {
            "latest_fetch_time": self._format_datetime(latest_fetch_time),
            "count": len(rows),
            "items": [self._serialize_row(row) for row in rows],
        }

    def get_keyword_trend(self, keyword: str) -> dict[str, Any]:
        """返回指定关键词的历史热度趋势。"""
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            return {"keyword": "", "count": 0, "points": []}

        sql = """
        SELECT fetch_time, MAX(hot_value) AS hot_value, MIN(rank_num) AS best_rank
        FROM hot_search_raw
        WHERE title LIKE %s
        GROUP BY fetch_time
        ORDER BY fetch_time ASC
        """
        rows = self._fetch_all(sql, (f"%{cleaned_keyword}%",))
        return {
            "keyword": cleaned_keyword,
            "count": len(rows),
            "points": [self._serialize_row(row) for row in rows],
        }

    def get_summary(self) -> dict[str, Any]:
        """返回总记录数、采集批次和最近一次采集时间等统计信息。"""
        summary_sql = """
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT fetch_time) AS total_batches,
            COUNT(DISTINCT title) AS total_keywords,
            MIN(fetch_time) AS earliest_fetch_time,
            MAX(fetch_time) AS latest_fetch_time
        FROM hot_search_raw
        """
        summary = self._fetch_one(summary_sql) or {}

        latest_fetch_time = summary.get("latest_fetch_time")
        latest_batch_count = 0
        if latest_fetch_time is not None:
            latest_count_sql = """
            SELECT COUNT(*) AS latest_batch_count
            FROM hot_search_raw
            WHERE fetch_time = %s
            """
            latest_row = self._fetch_one(latest_count_sql, (latest_fetch_time,)) or {}
            latest_batch_count = latest_row.get("latest_batch_count", 0)

        return {
            "total_records": summary.get("total_records", 0),
            "total_batches": summary.get("total_batches", 0),
            "total_keywords": summary.get("total_keywords", 0),
            "earliest_fetch_time": self._format_datetime(summary.get("earliest_fetch_time")),
            "latest_fetch_time": self._format_datetime(latest_fetch_time),
            "latest_batch_count": latest_batch_count,
        }

    def _get_latest_fetch_time(self) -> datetime | None:
        """获取最新一批数据的采集时间。"""
        sql = "SELECT MAX(fetch_time) AS latest_fetch_time FROM hot_search_raw"
        row = self._fetch_one(sql)
        if not row:
            return None
        return row.get("latest_fetch_time")

    def _fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        """执行单行查询。"""
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchone()
        finally:
            connection.close()

    def _fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """执行多行查询。"""
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return list(cursor.fetchall())
        finally:
            connection.close()

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """把查询结果中的日期时间转换成字符串。"""
        result: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                result[key] = self._format_datetime(value)
            else:
                result[key] = value
        return result

    def _format_datetime(self, value: datetime | None) -> str | None:
        """统一格式化时间字段。"""
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S")


mysql_service = MySQLService()
