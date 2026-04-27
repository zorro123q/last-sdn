"""微博热搜标题 TF-IDF + KMeans 主题聚类。"""

from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import jieba
import pandas as pd
import pymysql
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


# 支持 python ml/topic_cluster.py 直接运行。
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.config import get_mysql_connection_params, settings
from ml.data_loader import load_hot_search_raw


TOPIC_COLUMNS = [
    "keyword",
    "cluster_id",
    "cluster_name",
    "tfidf_keywords",
    "hot_value",
    "rank_num",
    "cluster_date",
]


def run_topic_clustering() -> None:
    """读取热搜标题，完成分词、TF-IDF 特征提取、KMeans 聚类并写库。"""
    print("[ml] 主题聚类分析任务开始")
    raw_df = load_hot_search_raw()
    if raw_df.empty:
        print("[ml] 可聚类标题数量不足，跳过主题聚类")
        _write_topic_clusters(pd.DataFrame(columns=TOPIC_COLUMNS))
        print("[ml] 主题聚类分析任务结束")
        return

    latest_df = (
        raw_df.sort_values(["title", "fetch_time"])
        .groupby("title", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    latest_df["title"] = latest_df["title"].astype(str).str.strip()
    latest_df = latest_df[latest_df["title"].str.len() > 0].reset_index(drop=True)

    if len(latest_df) < 2:
        print("[ml] 可聚类标题数量不足，跳过主题聚类")
        _write_topic_clusters(pd.DataFrame(columns=TOPIC_COLUMNS))
        print("[ml] 主题聚类分析任务结束")
        return

    cut_titles = latest_df["title"].map(_cut_title)
    cut_titles = cut_titles[cut_titles.str.len() > 0]
    latest_df = latest_df.loc[cut_titles.index].reset_index(drop=True)
    cut_titles = cut_titles.reset_index(drop=True)

    if len(cut_titles) < 2:
        print("[ml] 中文分词结果为空或数量不足，跳过主题聚类")
        _write_topic_clusters(pd.DataFrame(columns=TOPIC_COLUMNS))
        print("[ml] 主题聚类分析任务结束")
        return

    vectorizer = TfidfVectorizer(tokenizer=str.split, token_pattern=None, lowercase=False)
    tfidf_matrix = vectorizer.fit_transform(cut_titles.tolist())
    cluster_count = min(settings.ml_cluster_count, tfidf_matrix.shape[0])

    if cluster_count < 2:
        print("[ml] 可聚类标题数量不足，跳过主题聚类")
        _write_topic_clusters(pd.DataFrame(columns=TOPIC_COLUMNS))
        print("[ml] 主题聚类分析任务结束")
        return

    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf_matrix)
    cluster_keywords = _extract_cluster_keywords(kmeans, vectorizer)

    rows: list[dict[str, Any]] = []
    for index, row in latest_df.iterrows():
        cluster_id = int(labels[index])
        tfidf_keywords = cluster_keywords.get(cluster_id, [])
        rows.append(
            {
                "keyword": row["title"],
                "cluster_id": cluster_id,
                "cluster_name": _build_cluster_name(tfidf_keywords),
                "tfidf_keywords": "、".join(tfidf_keywords),
                "hot_value": int(row["hot_value"]) if not pd.isna(row["hot_value"]) else 0,
                "rank_num": int(row["rank_num"]) if not pd.isna(row["rank_num"]) else None,
                "cluster_date": date.today(),
            }
        )

    _write_topic_clusters(pd.DataFrame(rows))
    print(f"[ml] 主题聚类完成，样本数量：{len(rows)}")
    print("[ml] 主题聚类分析任务结束")


def _cut_title(title: str) -> str:
    """使用 jieba 对中文标题分词，并过滤空白和过短噪声词。"""
    tokens = []
    for token in jieba.cut(str(title)):
        token = token.strip()
        if not token:
            continue
        if len(token) == 1 and not token.isalnum():
            continue
        tokens.append(token)
    return " ".join(tokens)


def _extract_cluster_keywords(kmeans: KMeans, vectorizer: TfidfVectorizer) -> dict[int, list[str]]:
    """从每个聚类中心提取权重最高的 TF-IDF 关键词。"""
    terms = vectorizer.get_feature_names_out()
    result: dict[int, list[str]] = {}
    for cluster_id, center in enumerate(kmeans.cluster_centers_):
        top_indexes = center.argsort()[::-1][:8]
        result[cluster_id] = [
            str(terms[index])
            for index in top_indexes
            if center[index] > 0 and str(terms[index]).strip()
        ]
    return result


def _build_cluster_name(keywords: list[str]) -> str:
    """根据聚类关键词生成便于答辩展示的中文主题名称。"""
    text = " ".join(keywords)
    if any(word in text for word in ["明星", "演唱会", "电影", "综艺"]):
        return "娱乐热点"
    if any(word in text for word in ["高考", "大学", "学校", "考试"]):
        return "教育考试"
    if any(word in text for word in ["股票", "公司", "发布", "科技", "AI"]):
        return "科技财经"
    if any(word in text for word in ["比赛", "冠军", "足球", "篮球"]):
        return "体育赛事"
    if any(word in text for word in ["警方", "事故", "回应", "通报"]):
        return "社会事件"
    return "综合热点"


def _write_topic_clusters(df: pd.DataFrame) -> None:
    """清空并写入主题聚类结果表。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE hot_search_topic_clusters")
            if df.empty:
                return
            placeholders = ", ".join(["%s"] * len(TOPIC_COLUMNS))
            column_sql = ", ".join(TOPIC_COLUMNS)
            sql = f"INSERT INTO hot_search_topic_clusters ({column_sql}) VALUES ({placeholders})"
            values = [
                tuple(_clean_value(row.get(column)) for column in TOPIC_COLUMNS)
                for row in df.to_dict("records")
            ]
            cursor.executemany(sql, values)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError("第四期主题聚类表不存在，请先执行 sql/v4_ml_analysis.sql") from exc
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
    run_topic_clustering()
