# -*- coding: utf-8 -*-
"""
semantic/data_loader.py - 语义聚类数据加载器

从 MySQL hot_search_raw 表读取热搜标题数据进行语义聚类。
对同一标题保留最高热度的一条。
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from semantic.config import mysql_config


def load_hot_search_titles(limit=None):
    """
    从 MySQL hot_search_raw 表读取热搜标题数据用于语义聚类。

    过滤条件：
    - title 不能为空
    - fetch_time 不能为空

    去重规则：
    - 同一 title 只保留 hot_value 最大的那条记录

    Args:
        limit: 可选，限制读取条数

    Returns:
        pandas.DataFrame: 包含热搜标题数据的 DataFrame
            字段：title, rank_num, hot_value, fetch_time
    """
    conn = None
    try:
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 构建查询语句
        # 子查询：对同一 title 保留 hot_value 最大的一条
        sql = """
            SELECT
                t.title,
                t.rank_num,
                t.hot_value,
                t.fetch_time
            FROM hot_search_raw t
            INNER JOIN (
                SELECT title, MAX(hot_value) as max_hot_value
                FROM hot_search_raw
                WHERE title IS NOT NULL
                  AND title != ''
                  AND fetch_time IS NOT NULL
                GROUP BY title
            ) ranked ON t.title = ranked.title AND t.hot_value = ranked.max_hot_value
            WHERE t.title IS NOT NULL
              AND t.title != ''
              AND t.fetch_time IS NOT NULL
            ORDER BY t.hot_value DESC
        """

        # 如果有 limit 限制
        if limit is not None and limit > 0:
            sql += f" LIMIT {int(limit)}"

        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            print("[semantic] 可聚类标题为空，请先运行 collector 采集数据")
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

        # 按热度降序排序
        if "hot_value" in df.columns:
            df = df.sort_values("hot_value", ascending=False)

        print(f"[semantic] 已读取可聚类标题 {len(df)} 条")
        return df

    except pymysql.MySQLError as e:
        print(f"[semantic] 数据库读取失败：{e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # 测试数据加载
    df = load_hot_search_titles(limit=100)
    print(f"加载数据量: {len(df)}")
    if not df.empty:
        print(df.head())
