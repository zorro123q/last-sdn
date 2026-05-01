"""第三期分析结果查询服务。"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pymysql

from database import DatabaseConnectionError, DatabaseQueryError, get_connection


class AnalysisService:
    """封装 PySpark 统计结果表的查询逻辑。"""

    def get_top_keywords(self, limit: int = 20) -> list[dict[str, Any]]:
        """查询关键词 TopN 统计，最多返回 100 条。"""
        safe_limit = min(max(int(limit), 1), 100)
        sql = """
        SELECT
            keyword,
            appear_count,
            max_hot_value,
            avg_hot_value,
            best_rank,
            latest_fetch_time,
            stat_date,
            created_at
        FROM hot_search_keyword_stats
        ORDER BY max_hot_value DESC, appear_count DESC
        LIMIT %s
        """
        return self._fetch_all(sql, (safe_limit,))

    def get_daily_stats(self) -> list[dict[str, Any]]:
        """查询每日统计结果。"""
        sql = """
        SELECT
            stat_date,
            total_records,
            total_keywords,
            avg_hot_value,
            max_hot_value,
            min_rank,
            created_at
        FROM hot_search_daily_stats
        ORDER BY stat_date ASC
        """
        return self._fetch_all(sql)

    def _fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """执行分析表查询，并把日期时间字段转换为字符串。"""
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                rows = list(cursor.fetchall())
            return [self._serialize_row(row) for row in rows]
        except DatabaseConnectionError:
            raise
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                raise DatabaseQueryError("统计表不存在，请先执行 sql/v3_stats.sql") from exc
            print(f"[backend] 分析数据查询失败：{exc}")
            raise DatabaseQueryError("分析数据查询失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            print(f"[backend] 分析数据查询失败：{exc}")
            raise DatabaseQueryError("分析数据查询失败，请稍后重试") from exc
        finally:
            if connection is not None:
                connection.close()

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """序列化 MySQL 返回的日期、时间和小数字段。"""
        result: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, date):
                result[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        return result


analysis_service = AnalysisService()
