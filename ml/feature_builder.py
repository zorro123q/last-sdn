"""微博热搜爆发趋势识别的特征工程。"""

import re

import pandas as pd

from ml.config import settings


def build_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """按热搜标题聚合历史记录，构造模型可用的数值特征。"""
    if raw_df.empty:
        print("[ml] 特征构造完成，样本数量：0")
        return pd.DataFrame()

    rows: list[dict] = []
    recent_window = settings.ml_recent_window
    min_history_count = settings.ml_min_history_count

    for title, group in raw_df.groupby("title"):
        group = group.sort_values("fetch_time")
        if len(group) < min_history_count:
            continue

        recent = group.tail(recent_window)
        first_record = group.iloc[0]
        latest_record = group.iloc[-1]
        recent_first = recent.iloc[0]

        current_hot_value = float(latest_record["hot_value"])
        base_hot_value = float(recent_first["hot_value"])
        hot_value_change = current_hot_value - base_hot_value
        hot_value_change_rate = hot_value_change / max(base_hot_value, 1.0)

        latest_rank = _safe_float(latest_record.get("rank_num"))
        recent_first_rank = _safe_float(recent_first.get("rank_num"))
        rank_change = 0.0
        if latest_rank is not None and recent_first_rank is not None:
            rank_change = recent_first_rank - latest_rank

        latest_fetch_time = latest_record["fetch_time"]
        first_fetch_time = first_record["fetch_time"]
        duration_minutes = max(
            (latest_fetch_time - first_fetch_time).total_seconds() / 60.0,
            0.0,
        )

        ranks = pd.to_numeric(group["rank_num"], errors="coerce").dropna()
        best_rank = int(ranks.min()) if not ranks.empty else None

        rows.append(
            {
                "keyword": str(title),
                "current_rank": int(latest_rank) if latest_rank is not None else None,
                "current_hot_value": int(current_hot_value),
                "appear_count": int(len(group)),
                "max_hot_value": int(group["hot_value"].max()),
                "avg_hot_value": float(group["hot_value"].mean()),
                "min_rank": best_rank,
                "best_rank": best_rank,
                "latest_fetch_time": latest_fetch_time,
                "first_fetch_time": first_fetch_time,
                "recent_avg_hot_value": float(recent["hot_value"].mean()),
                "recent_max_hot_value": int(recent["hot_value"].max()),
                "hot_value_change": float(hot_value_change),
                "hot_value_change_rate": float(hot_value_change_rate),
                "rank_change": float(rank_change),
                "duration_minutes": float(duration_minutes),
                "title_length": len(str(title)),
                "has_number": int(bool(re.search(r"\d", str(title)))),
                "has_hashtag": int("#" in str(title)),
                "fetch_hour": int(latest_fetch_time.hour),
                "feature_date": latest_fetch_time.date(),
            }
        )

    feature_df = pd.DataFrame(rows)
    print(f"[ml] 特征构造完成，样本数量：{len(feature_df)}")
    return feature_df


def _safe_float(value) -> float | None:
    """把 pandas / MySQL 数值安全转换为 float，空值返回 None。"""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
