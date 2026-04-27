"""从 MySQL 读取微博热搜原始数据。"""

import pandas as pd
import pymysql

from ml.config import get_mysql_connection_params


def load_hot_search_raw() -> pd.DataFrame:
    """读取 hot_search_raw，并完成基础清洗和类型转换。"""
    query = """
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
      AND TRIM(title) <> ''
      AND hot_value IS NOT NULL
      AND fetch_time IS NOT NULL
    """

    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        raw_df = pd.read_sql(query, connection)
    finally:
        if connection is not None:
            connection.close()

    if raw_df.empty:
        print("[ml] 原始数据为空，请先运行 collector 采集数据")
        return raw_df

    raw_df["title"] = raw_df["title"].astype(str).str.strip()
    raw_df["fetch_time"] = pd.to_datetime(raw_df["fetch_time"], errors="coerce")
    raw_df["created_at"] = pd.to_datetime(raw_df["created_at"], errors="coerce")
    raw_df["hot_value"] = pd.to_numeric(raw_df["hot_value"], errors="coerce")
    raw_df["rank_num"] = pd.to_numeric(raw_df["rank_num"], errors="coerce")

    # 再过滤一次转换失败的数据，保证后续特征计算不会被空值打断。
    raw_df = raw_df.dropna(subset=["title", "hot_value", "fetch_time"])
    raw_df = raw_df[raw_df["title"].str.len() > 0]
    raw_df = raw_df.sort_values(["title", "fetch_time"], ascending=[True, True])
    raw_df = raw_df.reset_index(drop=True)

    if raw_df.empty:
        print("[ml] 原始数据为空，请先运行 collector 采集数据")

    return raw_df
