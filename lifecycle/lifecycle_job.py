"""第六期：微博热搜生命周期分析任务。

从 hot_search_raw 读取历史采集记录，按热搜标题建模生命周期阶段，
并写入 hot_search_lifecycle_stats，供预警中心和前端页面使用。

运行方式：
    python lifecycle/lifecycle_job.py
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

from lifecycle.config import get_mysql_connection_params, settings


LIFECYCLE_COLUMNS = [
    "keyword",
    "first_seen_time",
    "last_seen_time",
    "duration_minutes",
    "peak_hot_value",
    "peak_rank",
    "rise_speed",
    "fall_speed",
    "appear_count",
    "lifecycle_stage",
    "lifecycle_stage_cn",
    "is_disappeared",
    "stat_date",
]

STAGE_CN_MAP = {
    "new": "新上榜",
    "rising": "快速上升",
    "stable_high": "高位稳定",
    "falling": "缓慢衰退",
    "cooling": "快速降温",
    "disappeared": "已消失",
    "unknown": "未知",
}


def main() -> None:
    """执行生命周期分析主流程。"""
    print("[lifecycle] 热搜生命周期分析任务开始")
    raw_df = _load_hot_search_raw()

    if raw_df.empty:
        print("[lifecycle] 原始数据为空，将清空生命周期结果表")
        _replace_lifecycle_stats(pd.DataFrame(columns=LIFECYCLE_COLUMNS))
        print("[lifecycle] 热搜生命周期分析任务结束")
        return

    lifecycle_df = _build_lifecycle_stats(raw_df)
    _replace_lifecycle_stats(lifecycle_df)
    print(f"[lifecycle] 生命周期结果写入完成，共 {len(lifecycle_df)} 条")
    print("[lifecycle] 热搜生命周期分析任务结束")


def _load_hot_search_raw() -> pd.DataFrame:
    """读取并标准化原始热搜数据。"""
    query = """
    SELECT
        title,
        rank_num,
        hot_value,
        fetch_time
    FROM hot_search_raw
    WHERE title IS NOT NULL
      AND TRIM(title) <> ''
      AND fetch_time IS NOT NULL
    ORDER BY title ASC, fetch_time ASC
    """

    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        raw_df = pd.read_sql(query, connection)
    finally:
        if connection is not None:
            connection.close()

    if raw_df.empty:
        return raw_df

    raw_df["title"] = raw_df["title"].astype(str).str.strip()
    raw_df["fetch_time"] = pd.to_datetime(raw_df["fetch_time"], errors="coerce")
    raw_df["hot_value"] = pd.to_numeric(raw_df["hot_value"], errors="coerce").fillna(0)
    raw_df["rank_num"] = pd.to_numeric(raw_df["rank_num"], errors="coerce")
    raw_df = raw_df.dropna(subset=["title", "fetch_time"])
    raw_df = raw_df[raw_df["title"].str.len() > 0]

    # 同一采集批次内重复标题只保留聚合结果，避免单批重复放大 appear_count。
    raw_df = (
        raw_df.groupby(["title", "fetch_time"], as_index=False)
        .agg({"hot_value": "max", "rank_num": "min"})
        .sort_values(["title", "fetch_time"])
        .reset_index(drop=True)
    )
    return raw_df


def _build_lifecycle_stats(raw_df: pd.DataFrame) -> pd.DataFrame:
    """按关键词计算生命周期指标与阶段。"""
    latest_fetch_time = raw_df["fetch_time"].max()
    stat_date = latest_fetch_time.date() if pd.notna(latest_fetch_time) else date.today()
    cycle_minutes = _estimate_cycle_minutes(raw_df["fetch_time"])
    disappeared_minutes = cycle_minutes * settings.lifecycle_disappeared_cycles

    rows: list[dict[str, Any]] = []
    for keyword, group in raw_df.groupby("title"):
        group = group.sort_values("fetch_time").reset_index(drop=True)
        first_seen_time = group["fetch_time"].iloc[0]
        last_seen_time = group["fetch_time"].iloc[-1]
        duration_minutes = _minutes_between(first_seen_time, last_seen_time)
        appear_count = int(len(group))

        peak_hot_value = int(group["hot_value"].max() or 0)
        rank_series = pd.to_numeric(group["rank_num"], errors="coerce").dropna()
        peak_rank = int(rank_series.min()) if not rank_series.empty else None

        recent_growth_rate, rank_up, rank_down = _recent_change(group)
        is_disappeared = int(_minutes_between(last_seen_time, latest_fetch_time) > disappeared_minutes)
        lifecycle_stage = _judge_stage(
            appear_count=appear_count,
            peak_rank=peak_rank,
            recent_growth_rate=recent_growth_rate,
            rank_up=rank_up,
            rank_down=rank_down,
            is_disappeared=bool(is_disappeared),
        )

        rise_speed = _calc_rise_speed(group)
        fall_speed = _calc_fall_speed(group)

        rows.append(
            {
                "keyword": keyword,
                "first_seen_time": first_seen_time,
                "last_seen_time": last_seen_time,
                "duration_minutes": round(duration_minutes, 2),
                "peak_hot_value": peak_hot_value,
                "peak_rank": peak_rank,
                "rise_speed": round(rise_speed, 4),
                "fall_speed": round(fall_speed, 4),
                "appear_count": appear_count,
                "lifecycle_stage": lifecycle_stage,
                "lifecycle_stage_cn": STAGE_CN_MAP.get(lifecycle_stage, "未知"),
                "is_disappeared": is_disappeared,
                "stat_date": stat_date,
            }
        )

    result_df = pd.DataFrame(rows, columns=LIFECYCLE_COLUMNS)
    if result_df.empty:
        return result_df
    return result_df.sort_values(
        ["is_disappeared", "peak_hot_value", "duration_minutes"],
        ascending=[True, False, False],
    ).reset_index(drop=True)


def _estimate_cycle_minutes(fetch_times: pd.Series) -> float:
    """用采集批次间隔估算一个采集周期，样本不足时使用 30 分钟兜底。"""
    unique_times = pd.Series(pd.to_datetime(fetch_times.dropna().unique())).sort_values()
    if len(unique_times) < 2:
        return 30.0
    diffs = unique_times.diff().dropna().dt.total_seconds() / 60.0
    diffs = diffs[diffs > 0]
    if diffs.empty:
        return 30.0
    return max(float(diffs.median()), 1.0)


def _recent_change(group: pd.DataFrame) -> tuple[float, float, float]:
    """计算最近两次采集之间的热度增长率、排名上升和排名下降幅度。"""
    if len(group) < 2:
        return 0.0, 0.0, 0.0

    prev = group.iloc[-2]
    latest = group.iloc[-1]
    prev_hot = float(prev.get("hot_value") or 0)
    latest_hot = float(latest.get("hot_value") or 0)
    if prev_hot > 0:
        growth_rate = (latest_hot - prev_hot) / prev_hot
    elif latest_hot > 0:
        growth_rate = 1.0
    else:
        growth_rate = 0.0

    prev_rank = _safe_float(prev.get("rank_num"))
    latest_rank = _safe_float(latest.get("rank_num"))
    if prev_rank is None or latest_rank is None:
        return growth_rate, 0.0, 0.0

    # 排名数值越小表示越靠前，因此 prev_rank - latest_rank 为排名上升幅度。
    rank_delta = prev_rank - latest_rank
    rank_up = max(rank_delta, 0.0)
    rank_down = max(-rank_delta, 0.0)
    return growth_rate, rank_up, rank_down


def _judge_stage(
    *,
    appear_count: int,
    peak_rank: int | None,
    recent_growth_rate: float,
    rank_up: float,
    rank_down: float,
    is_disappeared: bool,
) -> str:
    """根据生命周期规则判断阶段。"""
    rank_threshold = settings.lifecycle_rank_jump_threshold
    if is_disappeared:
        return "disappeared"
    if appear_count <= 2:
        return "new"
    if recent_growth_rate >= settings.lifecycle_rising_rate_threshold or rank_up >= rank_threshold:
        return "rising"
    if peak_rank is not None and peak_rank <= 10 and abs(recent_growth_rate) < 0.15 and rank_down < 3:
        return "stable_high"
    if recent_growth_rate <= settings.lifecycle_cooling_rate_threshold or rank_down >= rank_threshold:
        return "cooling"
    if recent_growth_rate < 0 or rank_down > 0:
        return "falling"
    return "unknown"


def _calc_rise_speed(group: pd.DataFrame) -> float:
    """计算从首次出现到峰值的平均上升速度。"""
    if group.empty:
        return 0.0
    peak_index = group["hot_value"].idxmax()
    peak_row = group.loc[peak_index]
    first_row = group.iloc[0]
    minutes = max(_minutes_between(first_row["fetch_time"], peak_row["fetch_time"]), 1.0)
    speed = (float(peak_row["hot_value"] or 0) - float(first_row["hot_value"] or 0)) / minutes
    return max(speed, 0.0)


def _calc_fall_speed(group: pd.DataFrame) -> float:
    """计算从峰值到最近一次出现的平均降温速度。"""
    if group.empty:
        return 0.0
    peak_index = group["hot_value"].idxmax()
    peak_row = group.loc[peak_index]
    latest_row = group.iloc[-1]
    minutes = max(_minutes_between(peak_row["fetch_time"], latest_row["fetch_time"]), 1.0)
    speed = (float(peak_row["hot_value"] or 0) - float(latest_row["hot_value"] or 0)) / minutes
    return max(speed, 0.0)


def _minutes_between(start, end) -> float:
    if pd.isna(start) or pd.isna(end):
        return 0.0
    return max((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds() / 60.0, 0.0)


def _safe_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _replace_lifecycle_stats(df: pd.DataFrame) -> None:
    """清空并写入生命周期分析表，只保留最新一轮分析结果。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE hot_search_lifecycle_stats")
            if df.empty:
                return
            placeholders = ", ".join(["%s"] * len(LIFECYCLE_COLUMNS))
            column_sql = ", ".join(LIFECYCLE_COLUMNS)
            sql = f"INSERT INTO hot_search_lifecycle_stats ({column_sql}) VALUES ({placeholders})"
            values = [
                tuple(_clean_value(row.get(column)) for column in LIFECYCLE_COLUMNS)
                for row in df.to_dict("records")
            ]
            cursor.executemany(sql, values)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError("第六期生命周期表不存在，请先执行 sql/v6_intelligent_alert_report.sql") from exc
        raise
    finally:
        if connection is not None:
            connection.close()


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
