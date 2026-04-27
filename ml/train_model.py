"""训练微博热搜爆发趋势识别模型。"""

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from ml.config import settings


FEATURE_COLUMNS = [
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
]


def train_burst_model(labeled_df: pd.DataFrame):
    """训练 burst_level 三分类模型，样本不足时回退到规则结果。"""
    if labeled_df.empty or "burst_level" not in labeled_df.columns:
        print("[ml] 样本不足或类别不足，使用规则结果作为预测结果")
        return None

    available_columns = [col for col in FEATURE_COLUMNS if col in labeled_df.columns]
    class_counts = labeled_df["burst_level"].value_counts()
    if len(labeled_df) < 10 or class_counts.shape[0] < 2 or class_counts.min() < 2:
        print("[ml] 样本不足或类别不足，使用规则结果作为预测结果")
        return None

    X = labeled_df[available_columns].fillna(0)
    y = labeled_df["burst_level"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    if settings.ml_model_name == "sklearn_random_forest":
        model = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )
    else:
        model = GradientBoostingClassifier(random_state=42)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    print(f"[ml] 模型 accuracy：{accuracy:.4f}")
    print("[ml] classification_report：")
    print(report)

    _save_model(model, available_columns)
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy),
        "classification_report": report,
        "sample_count": int(len(labeled_df)),
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
    }
    return model, available_columns, metrics


def _save_model(model, feature_columns: list[str]) -> None:
    """保存模型和特征列，便于答辩时说明模型产物。"""
    model_dir: Path = settings.ml_model_dir
    model_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_dir / "burst_model.pkl")
    with (model_dir / "feature_columns.json").open("w", encoding="utf-8") as file:
        json.dump(feature_columns, file, ensure_ascii=False, indent=2)
