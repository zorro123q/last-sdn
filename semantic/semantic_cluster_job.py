# -*- coding: utf-8 -*-
"""
semantic/semantic_cluster_job.py - 第五期语义聚类增强主入口

执行流程：
1. 读取 hot_search_raw 标题数据
2. 执行语义嵌入聚类（sentence-transformers 或 TF-IDF fallback）
3. 写入 hot_search_semantic_clusters

使用方法：
    python semantic/semantic_cluster_job.py
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from semantic.config import semantic_config
from semantic.data_loader import load_hot_search_titles
from semantic.embedding_cluster import run_embedding_clustering
from semantic.mysql_writer import write_semantic_clusters


def run_semantic_cluster_job():
    """
    执行语义聚类任务主流程。

    输出执行日志：
    - [semantic] 语义聚类任务开始
    - [semantic] 原始标题读取完成
    - [semantic] 语义聚类完成
    - [semantic] 结果写入 MySQL 完成
    - [semantic] 语义聚类任务结束
    """
    print("=" * 50)
    print("[semantic] 语义聚类任务开始")
    print("=" * 50)

    # 1. 读取标题数据
    print("[semantic] 正在读取原始标题数据...")
    top_limit = semantic_config.get("top_limit", 500)
    raw_df = load_hot_search_titles(limit=top_limit)

    if raw_df.empty:
        print("[semantic] 可聚类标题为空，请先运行 collector 采集数据")
        print("=" * 50)
        print("[semantic] 语义聚类任务结束")
        print("=" * 50)
        return

    print(f"[semantic] 原始标题读取完成，共 {len(raw_df)} 条记录")

    # 2. 执行语义嵌入聚类
    print("[semantic] 正在执行语义嵌入聚类...")
    results_df = run_embedding_clustering(raw_df)

    if results_df.empty:
        print("[semantic] 语义聚类结果为空")
        print("=" * 50)
        print("[semantic] 语义聚类任务结束")
        print("=" * 50)
        return

    # 3. 写入 MySQL
    print("[semantic] 正在写入 MySQL...")
    write_semantic_clusters(results_df)

    print("=" * 50)
    print("[semantic] 语义聚类任务结束")
    print("=" * 50)


if __name__ == "__main__":
    run_semantic_cluster_job()
