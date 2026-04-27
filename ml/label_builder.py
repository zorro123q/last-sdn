"""使用弱监督规则构造爆发趋势标签。"""

import pandas as pd

from ml.config import settings


def build_labels(feature_df: pd.DataFrame) -> pd.DataFrame:
    """根据排名和热度变化规则生成 burst_level 与 trend_direction。"""
    if feature_df.empty:
        print("[ml] 爆发型样本：0")
        print("[ml] 稳定型样本：0")
        print("[ml] 降温型样本：0")
        return feature_df.copy()

    labeled_df = feature_df.copy()
    labeled_df["burst_level"] = labeled_df.apply(_build_burst_level, axis=1)
    labeled_df["trend_direction"] = labeled_df.apply(_build_trend_direction, axis=1)

    print(f"[ml] 爆发型样本：{int((labeled_df['burst_level'] == 2).sum())}")
    print(f"[ml] 稳定型样本：{int((labeled_df['burst_level'] == 1).sum())}")
    print(f"[ml] 降温型样本：{int((labeled_df['burst_level'] == 0).sum())}")
    return labeled_df


def _build_burst_level(row: pd.Series) -> int:
    """爆发型优先判断，便于识别已冲到前排或快速升温的热搜。"""
    best_rank = _to_float(row.get("best_rank"), default=9999.0)
    hot_value_change_rate = _to_float(row.get("hot_value_change_rate"), default=0.0)
    rank_change = _to_float(row.get("rank_change"), default=0.0)

    if (
        best_rank <= settings.ml_burst_top_rank_threshold
        or hot_value_change_rate >= settings.ml_burst_hot_growth_threshold
        or rank_change >= 5
    ):
        return 2

    if hot_value_change_rate < -0.1 or rank_change < -3:
        return 0

    if -0.1 <= hot_value_change_rate < 0.3 and -3 <= rank_change < 5:
        return 1

    return 1


def _build_trend_direction(row: pd.Series) -> str:
    """根据热度和排名变化给出趋势方向，便于前端中文展示。"""
    hot_value_change_rate = _to_float(row.get("hot_value_change_rate"), default=0.0)
    rank_change = _to_float(row.get("rank_change"), default=0.0)

    if hot_value_change_rate > 0.15 or rank_change >= 3:
        return "rising"
    if hot_value_change_rate < -0.15 or rank_change <= -3:
        return "falling"
    return "stable"


def _to_float(value, default: float) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
