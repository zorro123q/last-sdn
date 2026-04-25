# -*- coding: utf-8 -*-
"""
semantic/mysql_writer.py - 语义聚类结果写入 MySQL

将语义聚类结果写入 hot_search_semantic_clusters 表。
写入前先清空表（TRUNCATE），不要删除其他表。
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from semantic.config import mysql_config


def write_semantic_clusters(results_df):
    """
    将语义聚类结果写入 hot_search_semantic_clusters 表。

    Args:
        results_df: pandas.DataFrame，包含以下字段：
            - keyword: 热搜关键词（标题）
            - cluster_id: 聚类 ID
            - cluster_name: 聚类主题名称
            - semantic_keywords: 聚类关键词
            - embedding_method: 嵌入方法
            - hot_value: 热度值
            - rank_num: 排名
            - cluster_date: 聚类日期
    """
    if results_df.empty:
        print("[semantic] 语义聚类结果为空，跳过写入 hot_search_semantic_clusters")
        return

    conn = None
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()

        # 先清空表
        try:
            cursor.execute("TRUNCATE TABLE hot_search_semantic_clusters")
            print("[semantic] 已清空 hot_search_semantic_clusters 表")
        except pymysql.MySQLError as e:
            print(f"[semantic] 清空表失败，可能表不存在：{e}")
            print("[semantic] 请先执行 sql/v5_sentiment_semantic.sql 创建表")
            return

        # 插入数据
        insert_sql = """
            INSERT INTO hot_search_semantic_clusters
            (keyword, cluster_id, cluster_name, semantic_keywords, embedding_method,
             hot_value, rank_num, cluster_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        for _, row in results_df.iterrows():
            cursor.execute(insert_sql, (
                row.get("keyword", ""),
                int(row.get("cluster_id", 0)),
                row.get("cluster_name", "综合热点"),
                row.get("semantic_keywords", ""),
                row.get("embedding_method", "sentence_transformers"),
                int(row.get("hot_value", 0)),
                row.get("rank_num"),
                row.get("cluster_date"),
            ))

        conn.commit()
        print(f"[semantic] 已写入 {len(results_df)} 条语义聚类结果到 hot_search_semantic_clusters")

    except pymysql.MySQLError as e:
        print(f"[semantic] 写入 hot_search_semantic_clusters 失败：{e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 测试写入功能
    import pandas as pd

    test_results = pd.DataFrame({
        "keyword": ["测试标题1", "测试标题2", "测试标题3"],
        "cluster_id": [0, 1, 2],
        "cluster_name": ["娱乐热点", "科技财经", "综合热点"],
        "semantic_keywords": ["明星、演唱会", "股票、科技", "其他"],
        "embedding_method": ["sentence_transformers", "sentence_transformers", "tfidf"],
        "hot_value": [100000, 80000, 60000],
        "rank_num": [1, 2, 3],
        "cluster_date": [pd.Timestamp("2024-01-01").date()] * 3,
    })

    print("测试写入功能...")
    # write_semantic_clusters(test_results)
    print("测试完成")
