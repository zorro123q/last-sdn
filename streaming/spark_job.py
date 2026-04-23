"""Spark Structured Streaming 主任务。"""

import logging

from pyspark import StorageLevel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import coalesce, col, explode_outer, from_json, to_timestamp

from config import StreamingConfig
from mysql_writer import write_raw_batch
from redis_writer import write_current_ranking
from schema import PAYLOAD_SCHEMA


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def build_spark_session(config: StreamingConfig) -> SparkSession:
    """创建 SparkSession，并尽量把所需依赖配置集中在这里。"""

    builder = (
        SparkSession.builder.appName(config.spark_app_name)
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
    )

    if config.spark_jars_packages:
        builder = builder.config("spark.jars.packages", config.spark_jars_packages)

    return builder.getOrCreate()


def transform_stream(raw_stream: DataFrame) -> DataFrame:
    """把 Kafka 原始 JSON 字符串展开成结构化热搜明细。"""

    return (
        raw_stream.selectExpr("CAST(value AS STRING) AS json_text")
        .select(from_json(col("json_text"), PAYLOAD_SCHEMA).alias("payload"))
        .select(col("payload.fetch_time").alias("payload_fetch_time"), explode_outer(col("payload.items")).alias("item"))
        .select(
            col("item.rank").cast("int").alias("rank_no"),
            col("item.title").alias("title"),
            col("item.hot_value").cast("bigint").alias("hot_value"),
            col("item.source").alias("source"),
            coalesce(
                to_timestamp(col("item.fetch_time"), "yyyy-MM-dd HH:mm:ss"),
                to_timestamp(col("payload_fetch_time"), "yyyy-MM-dd HH:mm:ss"),
            ).alias("fetch_time"),
        )
        .where(col("title").isNotNull())
    )


def process_batch(batch_df: DataFrame, batch_id: int, config: StreamingConfig) -> None:
    """同一个微批次里先写 MySQL，再刷新 Redis 当前排行榜。"""

    if batch_df.limit(1).count() == 0:
        logger.info("批次 %s 无数据，跳过处理。", batch_id)
        return

    cached_df = batch_df.persist(StorageLevel.MEMORY_AND_DISK)

    try:
        write_raw_batch(
            batch_df=cached_df,
            batch_id=batch_id,
            jdbc_url=config.mysql_jdbc_url,
            connection_properties=config.mysql_connection_properties,
            table_name=config.mysql_table_raw,
        )
        write_current_ranking(
            batch_df=cached_df,
            redis_host=config.redis_host,
            redis_port=config.redis_port,
            redis_db=config.redis_db,
            redis_password=config.redis_password,
            ranking_key=config.redis_ranking_key,
            top_n=20,
        )
    finally:
        cached_df.unpersist()


def main() -> None:
    """启动流式消费任务。"""

    config = StreamingConfig()
    spark = build_spark_session(config)

    kafka_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", config.kafka_bootstrap_servers)
        .option("subscribe", config.kafka_topic)
        .option("startingOffsets", config.kafka_starting_offsets)
        .load()
    )

    parsed_stream = transform_stream(kafka_stream)

    query = (
        parsed_stream.writeStream.outputMode("append")
        .option("checkpointLocation", config.spark_checkpoint_dir)
        .foreachBatch(lambda batch_df, batch_id: process_batch(batch_df, batch_id, config))
        .start()
    )

    logger.info("Streaming 任务已启动，正在消费 Kafka Topic: %s", config.kafka_topic)
    query.awaitTermination()


if __name__ == "__main__":
    main()
