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
    """模型可用时用模型预测，样本不足时用弱监督规则结果兜底。"""
    result_df = labeled_df.copy()

    if train_result is not None:
        model, feature_columns, _metrics = train_result
        X = result_df[feature_columns].fillna(0)
        result_df["burst_level"] = model.predict(X).astype(int)
        result_df["burst_probability"] = _predict_burst_probability(model, X)
    else:
        result_df["burst_probability"] = result_df["burst_level"].map(
            {2: 0.8, 1: 0.5, 0: 0.3}
        )

    result_df["model_name"] = settings.ml_model_name
    result_df["predict_date"] = date.today()

    result_df = result_df[PREDICTION_COLUMNS]
    result_df = result_df.sort_values(
        ["burst_probability", "current_hot_value"],
        ascending=[False, False],
    )
    return result_df.head(settings.ml_top_limit).reset_index(drop=True)


def _predict_burst_probability(model, X: pd.DataFrame) -> list[float]:
    """优先返回 burst_level=2 的概率，便于排序潜在爆发型热搜。"""
    if not hasattr(model, "predict_proba"):
        return [1.0] * len(X)

    probabilities = model.predict_proba(X)
    class_list = list(getattr(model, "classes_", []))
    if 2 in class_list:
        burst_index = class_list.index(2)
        return [float(row[burst_index]) for row in probabilities]
    return [float(max(row)) for row in probabilities]


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
