"""第六期智能分析、预警、日报、任务和健康监控服务。"""

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


class V6IntelligenceService:
    """封装第六期新增结果表和任务调度逻辑。"""

    def get_lifecycle_summary(self) -> dict[str, Any]:
        sql = """
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN lifecycle_stage = 'new' THEN 1 ELSE 0 END) AS new_count,
            SUM(CASE WHEN lifecycle_stage = 'rising' THEN 1 ELSE 0 END) AS rising_count,
            SUM(CASE WHEN lifecycle_stage = 'stable_high' THEN 1 ELSE 0 END) AS stable_high_count,
            SUM(CASE WHEN lifecycle_stage = 'falling' THEN 1 ELSE 0 END) AS falling_count,
            SUM(CASE WHEN lifecycle_stage = 'cooling' THEN 1 ELSE 0 END) AS cooling_count,
            SUM(CASE WHEN lifecycle_stage = 'disappeared' THEN 1 ELSE 0 END) AS disappeared_count
        FROM hot_search_lifecycle_stats
        """
        row = self._fetch_one(sql, error_hint="生命周期分析表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        return self._normalize_counts(
            row,
            [
                "total_count",
                "new_count",
                "rising_count",
                "stable_high_count",
                "falling_count",
                "cooling_count",
                "disappeared_count",
            ],
        )

    def get_lifecycle_list(self, stage: str = "", limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = min(max(int(limit), 1), 500)
        if stage:
            sql = """
            SELECT *
            FROM hot_search_lifecycle_stats
            WHERE lifecycle_stage = %s
            ORDER BY peak_hot_value DESC, duration_minutes DESC
            LIMIT %s
            """
            return self._fetch_all(sql, (stage, safe_limit), "生命周期分析表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        sql = """
        SELECT *
        FROM hot_search_lifecycle_stats
        ORDER BY FIELD(lifecycle_stage, 'rising', 'stable_high', 'new', 'cooling', 'falling', 'disappeared', 'unknown'),
                 peak_hot_value DESC,
                 duration_minutes DESC
        LIMIT %s
        """
        return self._fetch_all(sql, (safe_limit,), "生命周期分析表不存在，请先执行 sql/v6_intelligent_alert_report.sql")

    def run_lifecycle_job(self) -> dict[str, str]:
        return self._start_background_job("lifecycle/lifecycle_job.py", "生命周期分析任务已启动，请查看后端控制台日志")

    def get_alert_summary(self) -> dict[str, Any]:
        sql = """
        SELECT
            COUNT(*) AS total_alerts,
            SUM(CASE WHEN alert_level = 'low' THEN 1 ELSE 0 END) AS low_count,
            SUM(CASE WHEN alert_level = 'medium' THEN 1 ELSE 0 END) AS medium_count,
            SUM(CASE WHEN alert_level = 'high' THEN 1 ELSE 0 END) AS high_count,
            SUM(CASE WHEN alert_level = 'critical' THEN 1 ELSE 0 END) AS critical_count,
            SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) AS unread_count
        FROM hot_search_alerts
        """
        row = self._fetch_one(sql, error_hint="舆情预警表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        return self._normalize_counts(
            row,
            ["total_alerts", "low_count", "medium_count", "high_count", "critical_count", "unread_count"],
        )

    def get_alert_list(self, level: str = "", alert_type: str = "", limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = min(max(int(limit), 1), 500)
        conditions: list[str] = []
        params: list[Any] = []
        if level:
            conditions.append("alert_level = %s")
            params.append(level)
        if alert_type:
            conditions.append("alert_type = %s")
            params.append(alert_type)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
        SELECT *
        FROM hot_search_alerts
        {where_sql}
        ORDER BY is_read ASC,
                 FIELD(alert_level, 'critical', 'high', 'medium', 'low'),
                 created_at DESC
        LIMIT %s
        """
        params.append(safe_limit)
        return self._fetch_all(sql, tuple(params), "舆情预警表不存在，请先执行 sql/v6_intelligent_alert_report.sql")

    def run_alert_job(self) -> dict[str, str]:
        return self._start_background_job("alerts/alert_job.py", "舆情风险预警任务已启动，请查看后端控制台日志")

    def mark_alert_read(self, alert_id: int) -> dict[str, Any]:
        sql = "UPDATE hot_search_alerts SET is_read = 1 WHERE id = %s"
        affected = self._execute(sql, (alert_id,), "舆情预警表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        if affected == 0:
            raise DatabaseQueryError("未找到指定预警记录")
        return {"message": "预警已标记为已读", "alert_id": alert_id}

    def get_latest_report(self) -> dict[str, Any]:
        sql = """
        SELECT *
        FROM hot_search_ai_reports
        ORDER BY report_date DESC, created_at DESC, id DESC
        LIMIT 1
        """
        row = self._fetch_one(sql, error_hint="AI 舆情日报表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        return row or {}

    def get_report_list(self) -> list[dict[str, Any]]:
        sql = """
        SELECT
            id,
            report_title,
            report_date,
            report_type,
            summary_text,
            created_at
        FROM hot_search_ai_reports
        ORDER BY report_date DESC, created_at DESC, id DESC
        LIMIT 100
        """
        return self._fetch_all(sql, error_hint="AI 舆情日报表不存在，请先执行 sql/v6_intelligent_alert_report.sql")

    def get_report_detail(self, report_id: int) -> dict[str, Any]:
        sql = "SELECT * FROM hot_search_ai_reports WHERE id = %s"
        row = self._fetch_one(sql, (report_id,), "AI 舆情日报表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        if not row:
            raise DatabaseQueryError("未找到指定 AI 舆情日报")
        return row

    def run_ai_report_job(self) -> dict[str, str]:
        return self._start_background_job("report/ai_daily_report_job.py", "AI 舆情日报生成任务已启动，请查看后端控制台日志")

    def get_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = min(max(int(limit), 1), 300)
        sql = """
        SELECT
            id,
            job_type,
            job_name,
            status,
            status_cn,
            start_time,
            end_time,
            duration_seconds,
            command_text,
            error_message,
            created_at
        FROM analysis_jobs
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """
        return self._fetch_all(sql, (safe_limit,), "任务运行记录表不存在，请先执行 sql/v6_intelligent_alert_report.sql")

    def get_job_detail(self, job_id: int) -> dict[str, Any]:
        sql = "SELECT * FROM analysis_jobs WHERE id = %s"
        row = self._fetch_one(sql, (job_id,), "任务运行记录表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        if not row:
            raise DatabaseQueryError("未找到指定任务记录")
        return row

    def run_all_jobs(self) -> dict[str, Any]:
        """同步顺序执行全链路分析任务，并写入 analysis_jobs。"""
        jobs = [
            ("analysis", "PySpark 离线统计", "analysis/batch_job.py", 1800),
            ("ml_predict", "爆发趋势识别", "ml/predict_job.py", 1800),
            ("ml_topic", "TF-IDF 主题聚类", "ml/topic_cluster.py", 1800),
            ("sentiment", "情感分析", "sentiment/sentiment_job.py", 1800),
            ("semantic", "语义聚类", "semantic/semantic_cluster_job.py", 2400),
            ("lifecycle", "生命周期分析", "lifecycle/lifecycle_job.py", 1800),
            ("alerts", "舆情风险预警", "alerts/alert_job.py", 1800),
            ("report", "AI 舆情日报", "report/ai_daily_report_job.py", 1800),
        ]

        results: list[dict[str, Any]] = []
        for job_type, job_name, script, timeout in jobs:
            job_id = self._create_job_record(job_type, job_name, f"python {script}")
            result = self._run_single_job(job_id, job_type, job_name, script, timeout)
            results.append(result)

        success_count = sum(1 for item in results if item["status"] == "success")
        failed_count = sum(1 for item in results if item["status"] == "failed")
        return {
            "message": "全链路分析任务执行完成",
            "total": len(results),
            "success_count": success_count,
            "failed_count": failed_count,
            "items": results,
        }

    def get_health_summary(self) -> dict[str, Any]:
        """返回最新数据质量记录；若尚未生成，则即时计算一份不落库结果。"""
        sql = """
        SELECT *
        FROM data_quality_stats
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
        try:
            row = self._fetch_one(sql, error_hint="数据质量监控表不存在，请先执行 sql/v6_intelligent_alert_report.sql")
        except DatabaseQueryError:
            raise
        if row:
            return row
        return self._build_health_stats(write_to_db=False)

    def run_health_check(self) -> dict[str, Any]:
        data = self._build_health_stats(write_to_db=True)
        return {"message": "数据质量检查已完成", "data": data}

    def _start_background_job(self, script: str, message: str) -> dict[str, str]:
        job_path = ROOT_DIR / script
        subprocess.Popen([sys.executable, str(job_path)], cwd=ROOT_DIR)
        return {"message": message, "command": f"python {script}"}

    def _build_health_stats(self, write_to_db: bool) -> dict[str, Any]:
        raw_summary = self._fetch_one(
            """
            SELECT
                COUNT(*) AS total_raw_records,
                COUNT(DISTINCT fetch_time) AS total_batches,
                COUNT(DISTINCT title) AS total_keywords,
                MAX(fetch_time) AS latest_fetch_time,
                SUM(CASE WHEN hot_value IS NULL THEN 1 ELSE 0 END) AS null_hot_value_count
            FROM hot_search_raw
            """,
            error_hint="原始采集表不存在，请先执行 sql/init.sql",
        )
        raw_summary = raw_summary or {}
        latest_fetch_time = raw_summary.get("latest_fetch_time")
        latest_batch_count = self._count_latest_batch(latest_fetch_time)
        duplicate_title_count = self._count_duplicate_titles(latest_fetch_time)

        analysis_count = self._safe_count("hot_search_keyword_stats")
        ml_count = self._safe_count("hot_search_burst_predictions")

        collector_status = self._collector_status(raw_summary)
        analysis_status = "healthy" if analysis_count > 0 else "empty"
        ml_status = "healthy" if ml_count > 0 else "empty"
        health_score = self._calc_health_score(
            raw_summary=raw_summary,
            duplicate_title_count=duplicate_title_count,
            collector_status=collector_status,
            analysis_status=analysis_status,
            ml_status=ml_status,
        )

        stat_date_value = (
            datetime.strptime(latest_fetch_time, "%Y-%m-%d %H:%M:%S").date()
            if isinstance(latest_fetch_time, str) and latest_fetch_time
            else (latest_fetch_time.date() if hasattr(latest_fetch_time, "date") else date.today())
        )
        data = {
            "stat_date": stat_date_value.strftime("%Y-%m-%d") if hasattr(stat_date_value, "strftime") else str(stat_date_value),
            "total_raw_records": int(raw_summary.get("total_raw_records") or 0),
            "total_batches": int(raw_summary.get("total_batches") or 0),
            "total_keywords": int(raw_summary.get("total_keywords") or 0),
            "latest_fetch_time": latest_fetch_time,
            "null_hot_value_count": int(raw_summary.get("null_hot_value_count") or 0),
            "duplicate_title_count": duplicate_title_count,
            "latest_batch_count": latest_batch_count,
            "collector_status": collector_status,
            "analysis_status": analysis_status,
            "ml_status": ml_status,
            "health_score": health_score,
        }

        if write_to_db:
            self._insert_health_stats(data)
        return self._serialize_row(data)

    def _count_latest_batch(self, latest_fetch_time) -> int:
        if not latest_fetch_time:
            return 0
        row = self._fetch_one(
            "SELECT COUNT(*) AS count FROM hot_search_raw WHERE fetch_time = %s",
            (latest_fetch_time,),
            "原始采集表不存在，请先执行 sql/init.sql",
        )
        return int((row or {}).get("count") or 0)

    def _count_duplicate_titles(self, latest_fetch_time) -> int:
        if not latest_fetch_time:
            return 0
        row = self._fetch_one(
            """
            SELECT COALESCE(SUM(cnt - 1), 0) AS duplicate_count
            FROM (
                SELECT title, COUNT(*) AS cnt
                FROM hot_search_raw
                WHERE fetch_time = %s
                GROUP BY title
                HAVING COUNT(*) > 1
            ) t
            """,
            (latest_fetch_time,),
            "原始采集表不存在，请先执行 sql/init.sql",
        )
        return int((row or {}).get("duplicate_count") or 0)

    def _safe_count(self, table_name: str) -> int:
        try:
            row = self._fetch_one(f"SELECT COUNT(*) AS count FROM {table_name}")
            return int((row or {}).get("count") or 0)
        except DatabaseQueryError:
            return 0

    def _collector_status(self, raw_summary: dict[str, Any]) -> str:
        total = int(raw_summary.get("total_raw_records") or 0)
        if total <= 0:
            return "empty"
        latest = raw_summary.get("latest_fetch_time")
        if not latest:
            return "unknown"
        latest_dt = datetime.strptime(latest, "%Y-%m-%d %H:%M:%S") if isinstance(latest, str) else latest
        if not isinstance(latest_dt, datetime):
            return "unknown"
        age_minutes = (datetime.now() - latest_dt).total_seconds() / 60.0
        if age_minutes > 180:
            return "stale"
        return "healthy"

    def _calc_health_score(
        self,
        *,
        raw_summary: dict[str, Any],
        duplicate_title_count: int,
        collector_status: str,
        analysis_status: str,
        ml_status: str,
    ) -> float:
        score = 100.0
        total_raw = int(raw_summary.get("total_raw_records") or 0)
        null_hot = int(raw_summary.get("null_hot_value_count") or 0)
        if total_raw <= 0:
            return 0.0
        if collector_status == "stale":
            score -= 20
        if collector_status == "empty":
            score -= 60
        score -= min((null_hot / max(total_raw, 1)) * 100, 15)
        score -= min(duplicate_title_count * 2, 10)
        if analysis_status != "healthy":
            score -= 10
        if ml_status != "healthy":
            score -= 10
        return round(max(score, 0.0), 2)

    def _insert_health_stats(self, data: dict[str, Any]) -> None:
        sql = """
        INSERT INTO data_quality_stats (
            stat_date, total_raw_records, total_batches, total_keywords, latest_fetch_time,
            null_hot_value_count, duplicate_title_count, latest_batch_count, collector_status,
            analysis_status, ml_status, health_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute(
            sql,
            (
                data.get("stat_date"),
                data.get("total_raw_records"),
                data.get("total_batches"),
                data.get("total_keywords"),
                data.get("latest_fetch_time"),
                data.get("null_hot_value_count"),
                data.get("duplicate_title_count"),
                data.get("latest_batch_count"),
                data.get("collector_status"),
                data.get("analysis_status"),
                data.get("ml_status"),
                data.get("health_score"),
            ),
            "数据质量监控表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
        )

    def _create_job_record(self, job_type: str, job_name: str, command_text: str) -> int:
        sql = """
        INSERT INTO analysis_jobs (job_type, job_name, status, status_cn, command_text)
        VALUES (%s, %s, 'pending', '等待中', %s)
        """
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, (job_type, job_name, command_text))
                return int(cursor.lastrowid)
        except DatabaseConnectionError:
            raise
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                raise DatabaseQueryError("任务运行记录表不存在，请先执行 sql/v6_intelligent_alert_report.sql") from exc
            raise DatabaseQueryError("创建任务运行记录失败，请检查数据库") from exc
        finally:
            if connection is not None:
                connection.close()

    def _run_single_job(
        self, job_id: int, job_type: str, job_name: str, script: str, timeout: int
    ) -> dict[str, Any]:
        start_time = datetime.now()
        self._update_job_running(job_id, start_time)
        script_path = ROOT_DIR / script
        try:
            completed = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            log_text = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
            if completed.returncode == 0:
                self._finish_job(job_id, "success", "成功", end_time, duration, log_text, "")
                status = "success"
            else:
                error_message = f"任务退出码 {completed.returncode}"
                self._finish_job(job_id, "failed", "失败", end_time, duration, log_text, error_message)
                status = "failed"
        except subprocess.TimeoutExpired as exc:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            log_text = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
            self._finish_job(job_id, "failed", "失败", end_time, duration, log_text, "任务执行超时")
            status = "failed"
        return {"id": job_id, "job_type": job_type, "job_name": job_name, "status": status}

    def _update_job_running(self, job_id: int, start_time: datetime) -> None:
        self._execute(
            """
            UPDATE analysis_jobs
            SET status = 'running', status_cn = '运行中', start_time = %s
            WHERE id = %s
            """,
            (start_time, job_id),
            "任务运行记录表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
        )

    def _finish_job(
        self,
        job_id: int,
        status: str,
        status_cn: str,
        end_time: datetime,
        duration: float,
        log_text: str,
        error_message: str,
    ) -> None:
        self._execute(
            """
            UPDATE analysis_jobs
            SET status = %s,
                status_cn = %s,
                end_time = %s,
                duration_seconds = %s,
                log_text = %s,
                error_message = %s
            WHERE id = %s
            """,
            (status, status_cn, end_time, round(duration, 2), log_text[-60000:], error_message, job_id),
            "任务运行记录表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
        )

    def _fetch_all(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        error_hint: str = "第六期数据表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
    ) -> list[dict[str, Any]]:
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
                raise DatabaseQueryError(error_hint) from exc
            print(f"[backend] 第六期数据查询失败：{exc}")
            raise DatabaseQueryError("第六期数据查询失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            print(f"[backend] 第六期数据查询失败：{exc}")
            raise DatabaseQueryError("第六期数据查询失败，请检查数据库连接") from exc
        finally:
            if connection is not None:
                connection.close()

    def _fetch_one(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        error_hint: str = "第六期数据表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
    ) -> dict[str, Any] | None:
        rows = self._fetch_all(sql, params, error_hint)
        return rows[0] if rows else None

    def _execute(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None,
        error_hint: str = "第六期数据表不存在，请先执行 sql/v6_intelligent_alert_report.sql",
    ) -> int:
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return int(cursor.rowcount)
        except DatabaseConnectionError:
            raise
        except pymysql.err.ProgrammingError as exc:
            if exc.args and exc.args[0] == 1146:
                raise DatabaseQueryError(error_hint) from exc
            print(f"[backend] 第六期数据写入失败：{exc}")
            raise DatabaseQueryError("第六期数据写入失败，请稍后重试") from exc
        except pymysql.MySQLError as exc:
            print(f"[backend] 第六期数据写入失败：{exc}")
            raise DatabaseQueryError("第六期数据写入失败，请检查数据库连接") from exc
        finally:
            if connection is not None:
                connection.close()

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
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

    def _normalize_counts(self, row: dict[str, Any] | None, keys: list[str]) -> dict[str, int]:
        result: dict[str, int] = {}
        row = row or {}
        for key in keys:
            result[key] = int(row.get(key) or 0)
        return result


v6_intelligence_service = V6IntelligenceService()
