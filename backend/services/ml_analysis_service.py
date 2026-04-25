"""第四期机器学习分析查询、任务触发和报告导出服务。"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql

from database import DatabaseConnectionError, DatabaseQueryError, get_connection


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.report_exporter import export_ml_report_csv as build_ml_report_csv
from ml.report_exporter import export_ml_report_excel as build_ml_report_excel


class MLAnalysisService:
    """封装第四期机器学习结果表的查询逻辑。"""

    def get_burst_top(self, limit: int = 20) -> list[dict[str, Any]]:
        """查询爆发趋势 TopN，按爆发概率和当前热度排序。"""
        safe_limit = min(max(int(limit), 1), 100)
        sql = """
        SELECT
            keyword,
            burst_level,
            burst_probability,
            trend_direction,
            current_rank,
            current_hot_value,
            hot_value_change_rate,
            rank_change,
            appear_count,
            model_name,
            predict_date,
            created_at
        FROM hot_search_burst_predictions
        ORDER BY burst_probability DESC, current_hot_value DESC
        LIMIT %s
        """
        return self._fetch_all(sql, (safe_limit,))

    def get_burst_by_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """根据关键词模糊查询爆发趋势识别结果。"""
        cleaned_keyword = keyword.strip()
        if not cleaned_keyword:
            return []

        sql = """
        SELECT
            keyword,
            burst_level,
            burst_probability,
            trend_direction,
            current_rank,
            current_hot_value,
            hot_value_change_rate,
            rank_change,
            appear_count,
            model_name,
            predict_date,
            created_at
        FROM hot_search_burst_predictions
        WHERE keyword LIKE %s
        ORDER BY burst_probability DESC, current_hot_value DESC
        LIMIT 100
        """
        return self._fetch_all(sql, (f"%{cleaned_keyword}%",))

    def get_topic_clusters(self) -> list[dict[str, Any]]:
        """查询主题聚类明细。"""
        sql = """
        SELECT
            keyword,
            cluster_id,
            cluster_name,
            tfidf_keywords,
            hot_value,
            rank_num,
            cluster_date,
            created_at
        FROM hot_search_topic_clusters
        ORDER BY cluster_id ASC, hot_value DESC
        """
        return self._fetch_all(sql)

    def get_cluster_summary(self) -> list[dict[str, Any]]:
        """按主题类别统计数量和平均热度。"""
        sql = """
        SELECT
            cluster_name,
            COUNT(*) AS keyword_count,
            AVG(hot_value) AS avg_hot_value,
            MAX(hot_value) AS max_hot_value
        FROM hot_search_topic_clusters
        GROUP BY cluster_name
        ORDER BY keyword_count DESC, avg_hot_value DESC
        """
        return self._fetch_all(sql)

    def run_burst_prediction_job(self) -> dict[str, str]:
        """后台触发第四期爆发趋势识别任务。"""
        job_path = ROOT_DIR / "ml" / "predict_job.py"
        subprocess.Popen([sys.executable, str(job_path)], cwd=ROOT_DIR)
        return {
            "message": "机器学习爆发趋势识别任务已启动，请查看后端控制台日志",
            "command": "python ml/predict_job.py",
        }

    def run_topic_cluster_job(self) -> dict[str, str]:
        """后台触发第四期主题聚类任务。"""
        job_path = ROOT_DIR / "ml" / "topic_cluster.py"
        subprocess.Popen([sys.executable, str(job_path)], cwd=ROOT_DIR)
        return {
            "message": "主题聚类分析任务已启动，请查看后端控制台日志",
            "command": "python ml/topic_cluster.py",
        }

    def export_ml_report_csv(self) -> bytes:
        """导出机器学习分析 CSV 报告。"""
        try:
            return build_ml_report_csv()
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                raise DatabaseQueryError("第四期报告相关表不存在，请先执行 sql/v4_ml_analysis.sql") from exc
            raise DatabaseQueryError("机器学习分析 CSV 报告导出失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            raise DatabaseQueryError("机器学习分析 CSV 报告导出失败，请检查数据库连接") from exc

    def export_ml_report_excel(self) -> bytes:
        """导出机器学习分析 Excel 报告。"""
        try:
            return build_ml_report_excel()
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                raise DatabaseQueryError("第四期报告相关表不存在，请先执行 sql/v4_ml_analysis.sql") from exc
            raise DatabaseQueryError("机器学习分析 Excel 报告导出失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            raise DatabaseQueryError("机器学习分析 Excel 报告导出失败，请检查数据库连接") from exc

    def _fetch_all(
        self, sql: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """执行查询，并统一处理缺表与日期序列化。"""
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
                raise DatabaseQueryError(
                    "第四期机器学习结果表不存在，请先执行 sql/v4_ml_analysis.sql"
                ) from exc
            print(f"[backend] 机器学习分析数据查询失败：{exc}")
            raise DatabaseQueryError("机器学习分析数据查询失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            print(f"[backend] 机器学习分析数据查询失败：{exc}")
            raise DatabaseQueryError("机器学习分析数据查询失败，请稍后重试") from exc
        finally:
            if connection is not None:
                connection.close()

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """把 MySQL 日期、时间和 Decimal 类型转换为 JSON 可序列化格式。"""
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


ml_analysis_service = MLAnalysisService()
