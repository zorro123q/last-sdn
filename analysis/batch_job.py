"""第三期 PySpark 离线批处理分析任务入口。"""

import sys
from pathlib import Path


# 支持 python analysis/batch_job.py 从项目根目录直接运行。
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from analysis.processors.daily_stats import build_daily_stats
from analysis.processors.keyword_stats import build_keyword_stats
from analysis.readers.mysql_reader import read_hot_search_raw
from analysis.spark_session import create_spark_session
from analysis.writers.mysql_writer import write_daily_stats, write_keyword_stats


def main() -> None:
    """执行完整离线分析流程。"""
    print("[analysis] PySpark 分析任务开始")
    spark = None
    try:
        spark = create_spark_session()

        raw_df = read_hot_search_raw(spark)
        print("[analysis] 读取原始数据完成")

        if raw_df.limit(1).count() == 0:
            print("[analysis] 原始数据为空，请先运行 collector 采集数据")
            return

        keyword_stats_df = build_keyword_stats(raw_df)
        print("[analysis] 关键词统计完成")

        daily_stats_df = build_daily_stats(raw_df)
        print("[analysis] 每日统计完成")

        write_keyword_stats(keyword_stats_df)
        write_daily_stats(daily_stats_df)
        print("[analysis] 写入 MySQL 完成")
    finally:
        if spark is not None:
            spark.stop()
        print("[analysis] PySpark 分析任务结束")


if __name__ == "__main__":
    main()
