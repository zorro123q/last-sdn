# -*- coding: utf-8 -*-
"""
sentiment/mysql_writer.py - 情感分析结果写入 MySQL

将情感分析结果写入 hot_search_sentiment_stats 和 hot_search_sentiment_daily_stats 表。
写入前先清空对应表（TRUNCATE），不要删除其他表。
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from sentiment.config import mysql_config


def write_sentiment_stats(results_df):
    """
    将单条情感分析结果写入 hot_search_sentiment_stats 表。

    Args:
        results_df: pandas.DataFrame，包含以下字段：
            - keyword: 热搜关键词（标题）
            - sentiment_score: 情感分数
            - sentiment_label: 情感标签（positive/neutral/negative）
            - sentiment_label_cn: 中文情感标签（正向/中性/负向）
            - rank_num: 排名
            - hot_value: 热度值
            - fetch_time: 采集时间
            - stat_date: 统计日期
            - method_name: 分析方法
    """
    if results_df.empty:
        print("[sentiment] 情感分析结果为空，跳过写入 hot_search_sentiment_stats")
        return

    conn = None
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()

        # 先清空表
        try:
            cursor.execute("TRUNCATE TABLE hot_search_sentiment_stats")
            print("[sentiment] 已清空 hot_search_sentiment_stats 表")
        except pymysql.MySQLError as e:
            print(f"[sentiment] 清空表失败，可能表不存在：{e}")
            print("[sentiment] 请先执行 sql/v5_sentiment_semantic.sql 创建表")
            return

        # 插入数据
        insert_sql = """
            INSERT INTO hot_search_sentiment_stats
            (keyword, sentiment_score, sentiment_label, sentiment_label_cn,
             rank_num, hot_value, fetch_time, stat_date, method_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for _, row in results_df.iterrows():
            cursor.execute(insert_sql, (
                row.get("keyword", ""),
                float(row.get("sentiment_score", 0.5)),
                row.get("sentiment_label", "neutral"),
                row.get("sentiment_label_cn", "中性"),
                row.get("rank_num"),
                int(row.get("hot_value", 0)),
                row.get("fetch_time"),
                row.get("stat_date"),
                row.get("method_name", "snownlp"),
            ))

        conn.commit()
        print(f"[sentiment] 已写入 {len(results_df)} 条情感分析结果到 hot_search_sentiment_stats")

    except pymysql.MySQLError as e:
        print(f"[sentiment] 写入 hot_search_sentiment_stats 失败：{e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def write_sentiment_daily_stats(daily_df):
    """
    将每日情感统计写入 hot_search_sentiment_daily_stats 表。

    Args:
        daily_df: pandas.DataFrame，包含以下字段：
            - stat_date: 统计日期
            - avg_sentiment_score: 平均情感分数
            - positive_count: 正向数量
            - neutral_count: 中性数量
            - negative_count: 负向数量
            - total_count: 总数量
            - positive_ratio: 正向占比
            - neutral_ratio: 中性占比
            - negative_ratio: 负向占比
    """
    if daily_df.empty:
        print("[sentiment] 每日情感统计为空，跳过写入 hot_search_sentiment_daily_stats")
        return

    conn = None
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()

        # 先清空表
        try:
            cursor.execute("TRUNCATE TABLE hot_search_sentiment_daily_stats")
            print("[sentiment] 已清空 hot_search_sentiment_daily_stats 表")
        except pymysql.MySQLError as e:
            print(f"[sentiment] 清空表失败，可能表不存在：{e}")
            print("[sentiment] 请先执行 sql/v5_sentiment_semantic.sql 创建表")
            return

        # 插入数据
        insert_sql = """
            INSERT INTO hot_search_sentiment_daily_stats
            (stat_date, avg_sentiment_score, positive_count, neutral_count,
             negative_count, total_count, positive_ratio, neutral_ratio, negative_ratio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for _, row in daily_df.iterrows():
            cursor.execute(insert_sql, (
                row.get("stat_date"),
                float(row.get("avg_sentiment_score", 0.5)),
                int(row.get("positive_count", 0)),
                int(row.get("neutral_count", 0)),
                int(row.get("negative_count", 0)),
                int(row.get("total_count", 0)),
                float(row.get("positive_ratio", 0)),
                float(row.get("neutral_ratio", 0)),
                float(row.get("negative_ratio", 0)),
            ))

        conn.commit()
        print(f"[sentiment] 已写入 {len(daily_df)} 条每日情感统计到 hot_search_sentiment_daily_stats")

    except pymysql.MySQLError as e:
        print(f"[sentiment] 写入 hot_search_sentiment_daily_stats 失败：{e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 测试写入功能
    import pandas as pd

    # 模拟情感分析结果
    test_results = pd.DataFrame({
        "keyword": ["测试标题1", "测试标题2", "测试标题3"],
        "sentiment_score": [0.8, 0.5, 0.2],
        "sentiment_label": ["positive", "neutral", "negative"],
        "sentiment_label_cn": ["正向", "中性", "负向"],
        "rank_num": [1, 2, 3],
        "hot_value": [100000, 80000, 60000],
        "fetch_time": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]),
        "stat_date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"]).date,
        "method_name": ["snownlp", "snownlp", "snownlp"],
    })

    # 模拟每日统计
    test_daily = pd.DataFrame({
        "stat_date": [pd.Timestamp("2024-01-01").date(), pd.Timestamp("2024-01-02").date()],
        "avg_sentiment_score": [0.65, 0.35],
        "positive_count": [2, 1],
        "neutral_count": [1, 1],
        "negative_count": [0, 1],
        "total_count": [3, 3],
        "positive_ratio": [0.67, 0.33],
        "neutral_ratio": [0.33, 0.33],
        "negative_ratio": [0.0, 0.34],
    })

    print("测试写入功能...")
    # write_sentiment_stats(test_results)
    # write_sentiment_daily_stats(test_daily)
    print("测试完成")
