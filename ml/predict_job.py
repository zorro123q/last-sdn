"""第四期机器学习爆发趋势识别主入口。"""

from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql


# 支持 python ml/predict_job.py 直接运行，避免子目录导入失败。
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.config import get_mysql_connection_params, settings
from ml.data_loader import load_hot_search_raw
from ml.feature_builder import build_features
from ml.label_builder import build_labels
from ml.train_model import train_burst_model


FEATURE_TABLE_COLUMNS = [
    "keyword",
    "current_rank",
    "current_hot_value",
    "appear_count",
    "max_hot_value",
    "avg_hot_value",
    "min_rank",
    "best_rank",
    "recent_avg_hot_value",
    "recent_max_hot_value",
    "hot_value_change",
    "hot_value_change_rate",
    "rank_change",
    "duration_minutes",
    "title_length",
    "has_number",
    "has_hashtag",
    "fetch_hour",
    "feature_date",
]

PREDICTION_COLUMNS = [
    "keyword",
    "burst_level",
    "burst_probability",
    "trend_direction",
    "current_rank",
    "current_hot_value",
    "hot_value_change_rate",
    "rank_change",
    "appear_count",
    "model_name",
    "predict_date",
]


def main() -> None:
    """执行完整爆发趋势识别任务。"""
    print("[ml] 机器学习爆发趋势识别任务开始")

    raw_df = load_hot_search_raw()
    print("[ml] 原始数据读取完成")
    total_batches = int(raw_df["fetch_time"].nunique()) if not raw_df.empty and "fetch_time" in raw_df.columns else 0
    if total_batches < 30:
        print(f"[ml] 当前仅 {total_batches} 个采集批次，样本较少，将使用平滑规则概率")

    feature_df = build_features(raw_df)
    print("[ml] 特征工程完成")

    labeled_df = build_labels(feature_df)
    print("[ml] 标签构造完成")

    if labeled_df.empty:
        _write_feature_stats(feature_df)
        _write_burst_predictions(pd.DataFrame(columns=PREDICTION_COLUMNS))
        print("[ml] 模型训练完成")
        print("[ml] 预测结果写入完成")
        print("[ml] 机器学习爆发趋势识别任务结束")
        return

    train_result = train_burst_model(labeled_df)
    print("[ml] 模型训练完成")

    prediction_df = _build_prediction_df(labeled_df, train_result)
    _write_feature_stats(feature_df)
    _write_burst_predictions(prediction_df)

    print("[ml] 预测结果写入完成")
    print("[ml] 机器学习爆发趋势识别任务结束")


def _build_prediction_df(labeled_df: pd.DataFrame, train_result) -> pd.DataFrame:
    """模型可用时用模型预测，样本不足时用规则概率兜底。"""
    result_df = labeled_df.copy()

    if train_result is not None:
        model, feature_columns, _metrics = train_result
        X = result_df[feature_columns].fillna(0)
        result_df["burst_level"] = model.predict(X).astype(int)
        result_df["burst_probability"] = _predict_burst_probability(model, X)
    else:
        print("[ml] 使用规则分数生成平滑爆发概率")
        result_df["burst_probability"] = _build_rule_based_probability(result_df)

    result_df["model_name"] = settings.ml_model_name
    result_df["predict_date"] = date.today()

    result_df = result_df[PREDICTION_COLUMNS]
    result_df = result_df.sort_values(
        ["burst_probability", "current_hot_value"],
        ascending=[False, False],
    )
    # 不要只保存 head(settings.ml_top_limit)，否则关键词搜索只能搜索到 TopN 数据
    return result_df.reset_index(drop=True)


def _predict_burst_probability(model, X: pd.DataFrame) -> list[float]:
    """
    混合模型置信度与多维特征分数，解决模型输出两极分化问题。

    模型 predict_proba 对 burst_level=2 输出全部 >0.92，对 level=1/0 全部 <0.05，
    单独使用会导致柱状图没有区分度。

    解决方案：将模型置信度与 _build_rule_based_probability 的多特征分数按比例混合，
    model_confidence_weight=0.6 作为主信号，feature_score=0.4 作为调节信号，
    让同一等级内也能产生有意义的差异化。
    """
    if not hasattr(model, "predict_proba"):
        return _build_rule_based_probability(X)

    probabilities = model.predict_proba(X)
    class_list = list(getattr(model, "classes_", []))
    if 2 in class_list:
        burst_index = class_list.index(2)
        model_confidences = [float(row[burst_index]) for row in probabilities]
    else:
        model_confidences = [float(max(row)) for row in probabilities]

    # 获取多特征规则分数（内部已按 burst_level 设定范围）
    feature_scores = _build_rule_based_probability(X)

    # 混合：model_confidence_weight=0.6，feature_score=0.4
    # 置信度高时（>0.8）混合后主要由模型决定，置信度低时由特征分数调节
    MODEL_WEIGHT = 0.60
    mixed = [
        MODEL_WEIGHT * mc + (1.0 - MODEL_WEIGHT) * fs
        for mc, fs in zip(model_confidences, feature_scores)
    ]
    return [_clip_probability(p, 0.05, 0.95) for p in mixed]


def _build_rule_based_probability(df: pd.DataFrame) -> list[float]:
    """
    样本不足时的规则概率兜底。
    使用连续分数，避免同一爆发等级全部显示相同概率。
    """
    if df.empty:
        return []

    max_hot_value = pd.to_numeric(
        df.get("current_hot_value", pd.Series([], dtype=float)), errors="coerce"
    ).fillna(0).max()
    max_hot_log = math.log1p(max(float(max_hot_value), 1.0))

    probabilities: list[float] = []

    for _, row in df.iterrows():
        burst_level = int(row.get("burst_level", 1) or 1)

        hot_value_change_rate = float(row.get("hot_value_change_rate", 0) or 0)
        rank_change = float(row.get("rank_change", 0) or 0)
        current_hot_value = float(row.get("current_hot_value", 0) or 0)

        current_rank_value = row.get("current_rank")
        try:
            current_rank = float(current_rank_value)
        except (TypeError, ValueError):
            current_rank = 50.0

        # 各维度分数计算（系数调小避免所有数据饱和到 1.0）
        # sigmoid(x*3.0) 在 x>0.5 时就≈1.0，太容易饱和 → 改为 *0.2
        # sigmoid(x*0.35) 在 x=5 时≈0.85，改为 *0.08 以获得更宽的区分度
        growth_score = _sigmoid(hot_value_change_rate * 0.2)
        rank_change_score = _sigmoid(rank_change * 0.08)
        rank_score = max(0.0, min(1.0, (51.0 - current_rank) / 50.0))
        heat_score = math.log1p(max(current_hot_value, 0.0)) / max_hot_log

        raw_score = (
            growth_score * 0.35
            + rank_change_score * 0.25
            + rank_score * 0.20
            + heat_score * 0.20
        )

        # 按爆发等级设定概率范围（统一设上限为 0.90，避免任何情况达到 1.0）
        if burst_level == 2:
            probability = min(max(raw_score, 0.60), 0.90)
        elif burst_level == 1:
            probability = min(max(raw_score, 0.35), 0.60)
        else:
            probability = min(max(raw_score, 0.0), 0.35)

        probabilities.append(round(float(probability), 4))

    return probabilities


def _sigmoid(value: float) -> float:
    """安全 sigmoid，避免指数溢出。"""
    value = max(min(value, 50.0), -50.0)
    return 1.0 / (1.0 + math.exp(-value))


def _clip_probability(value: float, min_value: float, max_value: float) -> float:
    if not math.isfinite(value):
        return min_value
    return min(max(value, min_value), max_value)


def _write_feature_stats(feature_df: pd.DataFrame) -> None:
    """写入第四期特征表，只处理第四期结果表。"""
    _replace_table_data("hot_search_feature_stats", feature_df, FEATURE_TABLE_COLUMNS)


def _write_burst_predictions(prediction_df: pd.DataFrame) -> None:
    """写入第四期爆发趋势预测表，只保留本次任务最新结果。"""
    _replace_table_data(
        "hot_search_burst_predictions",
        prediction_df,
        PREDICTION_COLUMNS,
    )


def _replace_table_data(table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
    """清空并写入第四期结果表，避免保留过期预测。"""
    allowed_tables = {"hot_search_feature_stats", "hot_search_burst_predictions"}
    if table_name not in allowed_tables:
        raise ValueError(f"不允许写入非第四期结果表：{table_name}")

    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
            if df.empty:
                return
            placeholders = ", ".join(["%s"] * len(columns))
            column_sql = ", ".join(columns)
            sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"
            values = [
                tuple(_clean_value(row.get(column)) for column in columns)
                for row in df.to_dict("records")
            ]
            cursor.executemany(sql, values)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError("第四期结果表不存在，请先执行 sql/v4_ml_analysis.sql") from exc
        raise
    finally:
        if connection is not None:
            connection.close()


def _clean_value(value: Any):
    """把 pandas 空值和时间类型转换成 pymysql 可写入的普通类型。"""
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
