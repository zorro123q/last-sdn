"""第六期：微博热搜舆情风险预警任务。

综合原始热搜、爆发趋势识别、情感分析和生命周期分析结果，
生成主动预警记录并写入 hot_search_alerts。

运行方式：
    python alerts/alert_job.py
"""

from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from alerts.config import get_mysql_connection_params, settings


ALERT_COLUMNS = [
    "keyword",
    "alert_type",
    "alert_type_cn",
    "alert_level",
    "alert_level_cn",
    "alert_message",
    "trigger_value",
    "threshold_value",
    "related_metric",
    "alert_date",
]

LEVEL_CN_MAP = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "critical": "严重风险",
}


def main() -> None:
    """执行舆情风险预警主流程。"""
    print("[alerts] 舆情风险预警任务开始")

    raw_df = _read_table(
        """
        SELECT title, rank_num, hot_value, fetch_time
        FROM hot_search_raw
        WHERE title IS NOT NULL AND TRIM(title) <> '' AND fetch_time IS NOT NULL
        """
    )
    alert_date = _infer_alert_date(raw_df)

    burst_df = _read_table(
        """
        SELECT keyword, burst_probability, hot_value_change_rate, rank_change,
               current_rank, current_hot_value, appear_count, predict_date
        FROM hot_search_burst_predictions
        """
    )
    sentiment_df = _read_table(
        """
        SELECT keyword, sentiment_score, sentiment_label, hot_value, rank_num, stat_date
        FROM hot_search_sentiment_stats
        """
    )
    lifecycle_df = _read_table(
        """
        SELECT keyword, duration_minutes, peak_hot_value, peak_rank,
               lifecycle_stage, lifecycle_stage_cn, appear_count, stat_date
        FROM hot_search_lifecycle_stats
        """
    )

    alerts = _build_alerts(raw_df, burst_df, sentiment_df, lifecycle_df, alert_date)
    alert_df = pd.DataFrame(alerts, columns=ALERT_COLUMNS)
    _replace_today_alerts(alert_df, alert_date)

    print(f"[alerts] 舆情预警写入完成，共 {len(alert_df)} 条")
    print("[alerts] 舆情风险预警任务结束")


def _read_table(query: str) -> pd.DataFrame:
    """读取单张分析表，缺表时返回空表，便于分阶段演示。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        return pd.read_sql(query, connection)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            print(f"[alerts] 依赖表不存在，已跳过：{exc}")
            return pd.DataFrame()
        raise
    finally:
        if connection is not None:
            connection.close()


def _infer_alert_date(raw_df: pd.DataFrame) -> date:
    if raw_df.empty or "fetch_time" not in raw_df.columns:
        return date.today()
    fetch_times = pd.to_datetime(raw_df["fetch_time"], errors="coerce").dropna()
    if fetch_times.empty:
        return date.today()
    return fetch_times.max().date()


def _build_alerts(
    raw_df: pd.DataFrame,
    burst_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
    lifecycle_df: pd.DataFrame,
    alert_date: date,
) -> list[dict[str, Any]]:
    """汇总多源规则预警。"""
    alerts: list[dict[str, Any]] = []
    alerts.extend(_build_growth_and_rank_alerts(raw_df, burst_df, alert_date))
    alerts.extend(_build_burst_risk_alerts(burst_df, alert_date))
    alerts.extend(_build_sentiment_alerts(sentiment_df, alert_date))
    alerts.extend(_build_lifecycle_alerts(lifecycle_df, alert_date))
    return _deduplicate_alerts(alerts)


def _build_growth_and_rank_alerts(
    raw_df: pd.DataFrame, burst_df: pd.DataFrame, alert_date: date
) -> list[dict[str, Any]]:
    """生成热度突增和排名跃升预警，优先使用 ML 特征结果。"""
    alerts: list[dict[str, Any]] = []
    feature_df = burst_df.copy()
    if feature_df.empty:
        feature_df = _build_recent_change_from_raw(raw_df)

    if feature_df.empty:
        return alerts

    for _, row in feature_df.iterrows():
        keyword = str(row.get("keyword") or row.get("title") or "").strip()
        if not keyword:
            continue

        growth_rate = _safe_float(row.get("hot_value_change_rate"), 0.0)
        rank_change = _safe_float(row.get("rank_change"), 0.0)

        if growth_rate >= settings.hot_growth_threshold:
            level = "critical" if growth_rate >= 1.0 else ("high" if growth_rate >= 0.8 else "medium")
            alerts.append(
                _alert(
                    keyword=keyword,
                    alert_type="hot_growth",
                    alert_type_cn="热度突增",
                    level=level,
                    message=f"话题【{keyword}】在短时间内热度增长明显，当前增长率为 {growth_rate * 100:.1f}%，建议重点关注。",
                    trigger_value=growth_rate,
                    threshold_value=settings.hot_growth_threshold,
                    related_metric="hot_value_change_rate",
                    alert_date=alert_date,
                )
            )

        if rank_change >= settings.rank_jump_threshold:
            level = "high" if rank_change >= settings.rank_jump_threshold * 2 else "medium"
            alerts.append(
                _alert(
                    keyword=keyword,
                    alert_type="rank_jump",
                    alert_type_cn="排名跃升",
                    level=level,
                    message=f"话题【{keyword}】排名快速跃升 {rank_change:.0f} 位，传播热度正在抬升。",
                    trigger_value=rank_change,
                    threshold_value=settings.rank_jump_threshold,
                    related_metric="rank_change",
                    alert_date=alert_date,
                )
            )
    return alerts


def _build_recent_change_from_raw(raw_df: pd.DataFrame) -> pd.DataFrame:
    """没有 ML 结果时，从原始数据兜底计算最近变化。"""
    if raw_df.empty:
        return pd.DataFrame()
    df = raw_df.copy()
    df["fetch_time"] = pd.to_datetime(df["fetch_time"], errors="coerce")
    df["hot_value"] = pd.to_numeric(df["hot_value"], errors="coerce").fillna(0)
    df["rank_num"] = pd.to_numeric(df["rank_num"], errors="coerce")
    df = df.dropna(subset=["title", "fetch_time"])
    rows: list[dict[str, Any]] = []
    for keyword, group in df.groupby("title"):
        group = group.sort_values("fetch_time")
        if len(group) < 2:
            continue
        prev = group.iloc[-2]
        latest = group.iloc[-1]
        prev_hot = float(prev.get("hot_value") or 0)
        latest_hot = float(latest.get("hot_value") or 0)
        growth_rate = (latest_hot - prev_hot) / prev_hot if prev_hot > 0 else (1.0 if latest_hot > 0 else 0.0)

        prev_rank = _nullable_float(prev.get("rank_num"))
        latest_rank = _nullable_float(latest.get("rank_num"))
        rank_change = 0.0 if prev_rank is None or latest_rank is None else max(prev_rank - latest_rank, 0.0)

        rows.append(
            {
                "keyword": keyword,
                "hot_value_change_rate": growth_rate,
                "rank_change": rank_change,
            }
        )
    return pd.DataFrame(rows)


def _build_burst_risk_alerts(burst_df: pd.DataFrame, alert_date: date) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if burst_df.empty:
        return alerts

    for _, row in burst_df.iterrows():
        keyword = str(row.get("keyword") or "").strip()
        probability = _safe_float(row.get("burst_probability"), 0.0)
        if not keyword or probability < settings.burst_probability_threshold:
            continue

        level = "critical" if probability >= 0.95 else "high"
        alerts.append(
            _alert(
                keyword=keyword,
                alert_type="burst_risk",
                alert_type_cn="爆发趋势风险",
                level=level,
                message=f"话题【{keyword}】爆发趋势概率达到 {probability * 100:.1f}%，建议纳入重点监测清单。",
                trigger_value=probability,
                threshold_value=settings.burst_probability_threshold,
                related_metric="burst_probability",
                alert_date=alert_date,
            )
        )
    return alerts


def _build_sentiment_alerts(sentiment_df: pd.DataFrame, alert_date: date) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if sentiment_df.empty:
        return alerts

    df = sentiment_df.copy()
    df["keyword"] = df["keyword"].astype(str).str.strip()
    df = df[df["keyword"] != ""]
    if "stat_date" in df.columns:
        df["stat_date"] = pd.to_datetime(df["stat_date"], errors="coerce")
        latest_date = df["stat_date"].max()
        if pd.notna(latest_date):
            df = df[df["stat_date"] == latest_date]

    grouped = df.groupby("keyword").agg(
        total_count=("sentiment_label", "count"),
        negative_count=("sentiment_label", lambda s: int((s == "negative").sum())),
        avg_sentiment_score=("sentiment_score", "mean"),
    )
    grouped["negative_ratio"] = grouped["negative_count"] / grouped["total_count"].replace(0, 1)

    for keyword, row in grouped.iterrows():
        ratio = _safe_float(row.get("negative_ratio"), 0.0)
        if ratio < settings.negative_ratio_threshold:
            continue
        level = "critical" if ratio >= 0.8 else "high"
        alerts.append(
            _alert(
                keyword=keyword,
                alert_type="negative_sentiment",
                alert_type_cn="负面情绪异常",
                level=level,
                message=f"话题【{keyword}】负面情绪占比达到 {ratio * 100:.1f}%，建议关注评论语义和事件走向。",
                trigger_value=ratio,
                threshold_value=settings.negative_ratio_threshold,
                related_metric="negative_ratio",
                alert_date=alert_date,
            )
        )
    return alerts


def _build_lifecycle_alerts(lifecycle_df: pd.DataFrame, alert_date: date) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if lifecycle_df.empty:
        return alerts

    for _, row in lifecycle_df.iterrows():
        keyword = str(row.get("keyword") or "").strip()
        if not keyword:
            continue

        duration = _safe_float(row.get("duration_minutes"), 0.0)
        peak_rank = _nullable_float(row.get("peak_rank"))
        peak_hot_value = _safe_float(row.get("peak_hot_value"), 0.0)
        stage = str(row.get("lifecycle_stage") or "")

        if duration >= settings.long_duration_minutes and peak_rank is not None and peak_rank <= 10:
            level = "high" if duration >= settings.long_duration_minutes * 2 and peak_rank <= 5 else "medium"
            alerts.append(
                _alert(
                    keyword=keyword,
                    alert_type="long_duration",
                    alert_type_cn="长时间高热",
                    level=level,
                    message=f"话题【{keyword}】已持续在榜 {duration:.0f} 分钟，且峰值排名进入前 {int(peak_rank)}，舆情影响周期较长。",
                    trigger_value=duration,
                    threshold_value=settings.long_duration_minutes,
                    related_metric="duration_minutes",
                    alert_date=alert_date,
                )
            )

        if stage == "cooling" and peak_hot_value >= settings.cooling_hot_value_threshold:
            level = "high" if peak_hot_value >= settings.cooling_hot_value_threshold * 5 else "medium"
            alerts.append(
                _alert(
                    keyword=keyword,
                    alert_type="lifecycle_cooling",
                    alert_type_cn="生命周期快速降温",
                    level=level,
                    message=f"话题【{keyword}】已进入快速降温阶段，峰值热度为 {peak_hot_value:.0f}，建议复盘降温原因和传播链路。",
                    trigger_value=peak_hot_value,
                    threshold_value=settings.cooling_hot_value_threshold,
                    related_metric="lifecycle_stage",
                    alert_date=alert_date,
                )
            )
    return alerts


def _alert(
    *,
    keyword: str,
    alert_type: str,
    alert_type_cn: str,
    level: str,
    message: str,
    trigger_value: float,
    threshold_value: float,
    related_metric: str,
    alert_date: date,
) -> dict[str, Any]:
    return {
        "keyword": keyword,
        "alert_type": alert_type,
        "alert_type_cn": alert_type_cn,
        "alert_level": level,
        "alert_level_cn": LEVEL_CN_MAP.get(level, "低风险"),
        "alert_message": message,
        "trigger_value": round(float(trigger_value or 0), 6),
        "threshold_value": round(float(threshold_value or 0), 6),
        "related_metric": related_metric,
        "alert_date": alert_date,
    }


def _deduplicate_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """同一话题同一预警类型只保留最高等级的一条。"""
    level_weight = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in alerts:
        key = (item["keyword"], item["alert_type"])
        old = result.get(key)
        if old is None or level_weight.get(item["alert_level"], 0) >= level_weight.get(old["alert_level"], 0):
            result[key] = item
    return list(result.values())


def _replace_today_alerts(alert_df: pd.DataFrame, alert_date: date) -> None:
    """删除当天旧预警后写入新预警，历史日期预警保留。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM hot_search_alerts WHERE alert_date = %s", (alert_date,))
            if alert_df.empty:
                return
            placeholders = ", ".join(["%s"] * len(ALERT_COLUMNS))
            column_sql = ", ".join(ALERT_COLUMNS)
            sql = f"INSERT INTO hot_search_alerts ({column_sql}) VALUES ({placeholders})"
            values = [
                tuple(_clean_value(row.get(column)) for column in ALERT_COLUMNS)
                for row in alert_df.to_dict("records")
            ]
            cursor.executemany(sql, values)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError("第六期预警表不存在，请先执行 sql/v6_intelligent_alert_report.sql") from exc
        raise
    finally:
        if connection is not None:
            connection.close()


def _safe_float(value, default: float = 0.0) -> float:
    number = _nullable_float(value)
    return default if number is None else number


def _nullable_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _clean_value(value: Any):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value


if __name__ == "__main__":
    main()
