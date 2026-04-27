"""机器学习分析报告导出。"""

from __future__ import annotations

import io
from collections import OrderedDict

import pandas as pd
import pymysql

from ml.config import get_mysql_connection_params


def export_ml_report_csv() -> bytes:
    """导出 CSV 报告，多个 section 依次拼接。"""
    sections = _build_report_sections()
    output = io.StringIO()
    for section_name, df in sections.items():
        output.write(f"### {section_name}\n")
        df.to_csv(output, index=False)
        output.write("\n")
    return output.getvalue().encode("utf-8-sig")


def export_ml_report_excel() -> bytes:
    """导出 Excel 多 Sheet 报告。"""
    sections = _build_report_sections()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for section_name, df in sections.items():
            sheet_name = section_name[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.getvalue()


def _build_report_sections() -> OrderedDict[str, pd.DataFrame]:
    """按第四期要求组装报告内容，缺表时写入中文提示而不是失败。"""
    sections: OrderedDict[str, pd.DataFrame] = OrderedDict()
    sections["爆发趋势"] = _query_dataframe(
        """
        SELECT
            keyword,
            burst_level,
            burst_probability,
            trend_direction,
            current_rank,
            current_hot_value,
            hot_value_change_rate,
            rank_change,
            appear_count,
            model_name,
            predict_date
        FROM hot_search_burst_predictions
        ORDER BY burst_probability DESC, current_hot_value DESC
        LIMIT 20
        """,
        "hot_search_burst_predictions",
        "hot_search_burst_predictions 表不存在，请先执行 sql/v4_ml_analysis.sql 并运行第四期爆发趋势识别任务。",
    )
    sections["主题聚类"] = _query_dataframe(
        """
        SELECT
            keyword,
            cluster_id,
            cluster_name,
            tfidf_keywords,
            hot_value,
            rank_num,
            cluster_date
        FROM hot_search_topic_clusters
        ORDER BY cluster_id ASC, hot_value DESC
        """,
        "hot_search_topic_clusters",
        "hot_search_topic_clusters 表不存在，请先执行 sql/v4_ml_analysis.sql 并运行第四期主题聚类任务。",
    )
    sections["关键词统计"] = _query_dataframe(
        """
        SELECT
            keyword,
            appear_count,
            max_hot_value,
            avg_hot_value,
            best_rank,
            latest_fetch_time,
            stat_date
        FROM hot_search_keyword_stats
        ORDER BY appear_count DESC, max_hot_value DESC
        LIMIT 20
        """,
        "hot_search_keyword_stats",
        "hot_search_keyword_stats 统计表不存在，请先运行第三期 PySpark 分析任务。",
    )
    sections["每日统计"] = _query_dataframe(
        """
        SELECT
            stat_date,
            total_records,
            total_keywords,
            avg_hot_value,
            max_hot_value,
            min_rank
        FROM hot_search_daily_stats
        ORDER BY stat_date ASC
        """,
        "hot_search_daily_stats",
        "hot_search_daily_stats 统计表不存在，请先运行第三期 PySpark 分析任务。",
    )
    sections["当前热搜榜"] = _query_dataframe(
        """
        SELECT title, rank_num, hot_value, source, fetch_time
        FROM hot_search_raw
        WHERE fetch_time = (SELECT MAX(fetch_time) FROM hot_search_raw)
        ORDER BY rank_num ASC, hot_value DESC
        """,
        "hot_search_raw",
        "hot_search_raw 原始表不存在，请先执行 sql/init.sql 并运行采集程序。",
    )
    return sections


def _query_dataframe(sql: str, table_name: str, missing_message: str) -> pd.DataFrame:
    """执行报告查询，缺表或空数据时返回带提示的 DataFrame。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        df = pd.read_sql(sql, connection)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            return pd.DataFrame([{"提示": missing_message}])
        raise
    finally:
        if connection is not None:
            connection.close()

    if df.empty:
        return pd.DataFrame([{"提示": f"{table_name} 暂无数据，请先运行对应阶段任务。"}])
    return df
