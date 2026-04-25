"""关键词统计处理逻辑。"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, current_date, max, min, trim
from pyspark.sql.types import DateType, DoubleType, IntegerType, LongType, StringType, StructField, StructType, TimestampType


KEYWORD_STATS_SCHEMA = StructType(
    [
        StructField("keyword", StringType(), False),
        StructField("appear_count", IntegerType(), False),
        StructField("max_hot_value", LongType(), True),
        StructField("avg_hot_value", DoubleType(), True),
        StructField("best_rank", IntegerType(), True),
        StructField("latest_fetch_time", TimestampType(), True),
        StructField("stat_date", DateType(), False),
    ]
)


def build_keyword_stats(raw_df: DataFrame) -> DataFrame:
    """按热搜标题生成关键词出现次数、热度和最佳排名统计。"""
    spark: SparkSession = raw_df.sparkSession
    if raw_df.limit(1).count() == 0:
        print("[analysis] 原始数据为空，关键词统计返回空结果")
        return spark.createDataFrame([], KEYWORD_STATS_SCHEMA)

    cleaned_df = raw_df.withColumn("keyword", trim(col("title"))).filter(
        col("keyword").isNotNull() & (col("keyword") != "")
    )

    if cleaned_df.limit(1).count() == 0:
        print("[analysis] 原始数据中没有有效 title，关键词统计返回空结果")
        return spark.createDataFrame([], KEYWORD_STATS_SCHEMA)

    # 保留平均热度为 DOUBLE，方便后续图表展示小数。
    return (
        cleaned_df.groupBy("keyword")
        .agg(
            count("*").cast("int").alias("appear_count"),
            max(col("hot_value").cast("long")).alias("max_hot_value"),
            avg(col("hot_value").cast("double")).alias("avg_hot_value"),
            min(col("rank_num").cast("int")).alias("best_rank"),
            max("fetch_time").alias("latest_fetch_time"),
        )
        .withColumn("stat_date", current_date())
        .select(
            "keyword",
            "appear_count",
            "max_hot_value",
            "avg_hot_value",
            "best_rank",
            "latest_fetch_time",
            "stat_date",
        )
        .orderBy(col("appear_count").desc(), col("max_hot_value").desc())
    )
