"""每日采集统计处理逻辑。"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, countDistinct, max, min, to_date, to_timestamp
from pyspark.sql.types import DateType, DoubleType, IntegerType, LongType, StructField, StructType


DAILY_STATS_SCHEMA = StructType(
    [
        StructField("stat_date", DateType(), False),
        StructField("total_records", IntegerType(), False),
        StructField("total_keywords", IntegerType(), False),
        StructField("avg_hot_value", DoubleType(), True),
        StructField("max_hot_value", LongType(), True),
        StructField("min_rank", IntegerType(), True),
    ]
)


def build_daily_stats(raw_df: DataFrame) -> DataFrame:
    """按采集日期生成每日记录数、关键词数和热度统计。"""
    spark: SparkSession = raw_df.sparkSession
    if raw_df.limit(1).count() == 0:
        print("[analysis] 原始数据为空，每日统计返回空结果")
        return spark.createDataFrame([], DAILY_STATS_SCHEMA)

    dated_df = raw_df.withColumn(
        "stat_date",
        to_date(to_timestamp(col("fetch_time"))),
    )

    invalid_count = dated_df.filter(
        col("fetch_time").isNotNull() & col("stat_date").isNull()
    ).count()
    if invalid_count > 0:
        print(f"[analysis] 发现 {invalid_count} 条 fetch_time 日期格式转换失败，已过滤")

    valid_df = dated_df.filter(col("stat_date").isNotNull())
    if valid_df.limit(1).count() == 0:
        print("[analysis] 没有可用的 fetch_time 日期数据，每日统计返回空结果")
        return spark.createDataFrame([], DAILY_STATS_SCHEMA)

    return (
        valid_df.groupBy("stat_date")
        .agg(
            count("*").cast("int").alias("total_records"),
            countDistinct("title").cast("int").alias("total_keywords"),
            avg(col("hot_value").cast("double")).alias("avg_hot_value"),
            max(col("hot_value").cast("long")).alias("max_hot_value"),
            min(col("rank_num").cast("int")).alias("min_rank"),
        )
        .select(
            "stat_date",
            "total_records",
            "total_keywords",
            "avg_hot_value",
            "max_hot_value",
            "min_rank",
        )
        .orderBy(col("stat_date").asc())
    )
