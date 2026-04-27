# -*- coding: utf-8 -*-
"""
sentiment/sentiment_job.py - 第五期情感分析主入口

执行流程：
1. 读取 hot_search_raw 原始数据
2. 执行情感分析
3. 生成每日情绪统计
4. 写入 hot_search_sentiment_stats
5. 写入 hot_search_sentiment_daily_stats

使用方法：
    python sentiment/sentiment_job.py
"""

import sys
from pathlib import Path

import pandas as pd

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from sentiment.config import sentiment_config
from sentiment.data_loader import load_hot_search_raw
from sentiment.sentiment_analyzer import analyze_sentiment
from sentiment.mysql_writer import write_sentiment_stats, write_sentiment_daily_stats


def compute_daily_sentiment_stats(results_df):
    """
    计算每日情感统计。

    按 DATE(fetch_time) 分组，统计：
    - avg_sentiment_score: 平均情感分数
    - positive_count: 正向数量
    - neutral_count: 中性数量
    - negative_count: 负向数量
    - total_count: 总数量
    - positive_ratio: 正向占比
    - neutral_ratio: 中性占比
    - negative_ratio: 负向占比

    Args:
        results_df: pandas.DataFrame，包含 sentiment_label 等字段

    Returns:
        pandas.DataFrame: 每日情感统计
    """
    if results_df.empty:
        return pd.DataFrame()

    # 按日期分组
    daily_stats = []

    for stat_date, group in results_df.groupby("stat_date"):
        total_count = len(group)
        avg_score = group["sentiment_score"].mean()

        positive_count = len(group[group["sentiment_label"] == "positive"])
        neutral_count = len(group[group["sentiment_label"] == "neutral"])
        negative_count = len(group[group["sentiment_label"] == "negative"])

        positive_ratio = positive_count / total_count if total_count > 0 else 0
        neutral_ratio = neutral_count / total_count if total_count > 0 else 0
        negative_ratio = negative_count / total_count if total_count > 0 else 0

        daily_stats.append({
            "stat_date": stat_date,
            "avg_sentiment_score": round(avg_score, 4),
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "total_count": total_count,
            "positive_ratio": round(positive_ratio, 4),
            "neutral_ratio": round(neutral_ratio, 4),
            "negative_ratio": round(negative_ratio, 4),
        })

    daily_df = pd.DataFrame(daily_stats)
    # 按日期升序排序
    if not daily_df.empty:
        daily_df = daily_df.sort_values("stat_date", ascending=True)

    return daily_df


def run_sentiment_job():
    """
    执行情感分析任务主流程。

    输出执行日志：
    - [sentiment] 情感分析任务开始
    - [sentiment] 原始数据读取完成
    - [sentiment] 标题情感分析完成
    - [sentiment] 每日情绪统计完成
    - [sentiment] 结果写入 MySQL 完成
    - [sentiment] 情感分析任务结束
    """
    print("=" * 50)
    print("[sentiment] 情感分析任务开始")
    print("=" * 50)

    # 1. 读取原始数据
    print("[sentiment] 正在读取原始数据...")
    top_limit = sentiment_config.get("top_limit", 100)
    raw_df = load_hot_search_raw(limit=top_limit)

    if raw_df.empty:
        print("[sentiment] 原始数据为空，请先运行 collector 采集数据")
        print("=" * 50)
        print("[sentiment] 情感分析任务结束")
        print("=" * 50)
        return

    print(f"[sentiment] 原始数据读取完成，共 {len(raw_df)} 条记录")

    # 2. 执行情感分析
    print("[sentiment] 正在执行标题情感分析...")
    results_df = analyze_sentiment(raw_df)

    if results_df.empty:
        print("[sentiment] 情感分析结果为空")
        print("=" * 50)
        print("[sentiment] 情感分析任务结束")
        print("=" * 50)
        return

    # 3. 生成每日情绪统计
    print("[sentiment] 正在生成每日情绪统计...")
    daily_df = compute_daily_sentiment_stats(results_df)
    print(f"[sentiment] 每日情绪统计完成，共 {len(daily_df)} 天")

    # 4. 写入 MySQL
    print("[sentiment] 正在写入 MySQL...")
    write_sentiment_stats(results_df)
    write_sentiment_daily_stats(daily_df)

    print("=" * 50)
    print("[sentiment] 情感分析任务结束")
    print("=" * 50)


if __name__ == "__main__":
    run_sentiment_job()
