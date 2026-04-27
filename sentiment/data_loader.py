# -*- coding: utf-8 -*-
"""
sentiment/data_loader.py - 情感分析数据加载器

从 MySQL hot_search_raw 表读取微博热搜原始数据。
返回 pandas DataFrame，包含 id, title, rank_num, hot_value, source, fetch_time, created_at 字段。
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from sentiment.config import mysql_config


def load_hot_search_raw(limit=None):
    """
    从 MySQL hot_search_raw 表读取热搜原始数据。

    过滤条件：
    - title 不能为空
    - fetch_time 不能为空

    Args:
        limit: 可选，限制读取条数

    Returns:
        pandas.DataFrame: 包含热搜数据的 DataFrame
            字段：id, title, rank_num, hot_value, source, fetch_time, created_at
    """
    conn = None
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 构建查询语句
        sql = """
            SELECT
                id,
                title,
                rank_num,
                hot_value,
                source,
                fetch_time,
                created_at
            FROM hot_search_raw
            WHERE title IS NOT NULL
              AND title != ''
              AND fetch_time IS NOT NULL
            ORDER BY fetch_time ASC
        """

        # 如果有 limit 限制
        if limit is not None and limit > 0:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            print("[sentiment] 原始数据为空，请先运行 collector 采集数据")
            return pd.DataFrame()

        # 转换为 DataFrame
        df = pd.DataFrame(rows)

        # 数据类型转换
        # 将 fetch_time 转换为 datetime
        if "fetch_time" in df.columns:
            df["fetch_time"] = pd.to_datetime(df["fetch_time"], errors="coerce")

        # 将 hot_value 转换为数值类型
        if "hot_value" in df.columns:
            df["hot_value"] = pd.to_numeric(df["hot_value"], errors="coerce").fillna(0)

        # 将 rank_num 转换为数值类型
        if "rank_num" in df.columns:
            df["rank_num"] = pd.to_numeric(df["rank_num"], errors="coerce").fillna(0).astype(int)

        # 按 fetch_time 升序排序
        if "fetch_time" in df.columns:
            df = df.sort_values("fetch_time", ascending=True)

        print(f"[sentiment] 已读取原始数据 {len(df)} 条")
        return df

    except pymysql.MySQLError as e:
        print(f"[sentiment] 数据库读取失败：{e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 测试数据加载
    df = load_hot_search_raw()
    print(f"加载数据量: {len(df)}")
    if not df.empty:
        print(df.head())
