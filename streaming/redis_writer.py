"""Redis 写入封装。"""

import logging

import redis
from pyspark.sql import DataFrame
from pyspark.sql.functions import col


logger = logging.getLogger(__name__)


def write_current_ranking(
    batch_df: DataFrame,
    redis_host: str,
    redis_port: int,
    redis_db: int,
    redis_password: str,
    ranking_key: str,
    top_n: int = 20,
) -> None:
    """把当前批次热度最高的前 N 条写入 Redis Sorted Set。"""

    ranking_rows = (
        batch_df.select("title", "hot_value")
        .where(col("title").isNotNull() & col("hot_value").isNotNull())
        .orderBy(col("hot_value").desc())
        .limit(top_n)
        .collect()
    )

    if not ranking_rows:
        logger.info("当前批次无可写入 Redis 的排行数据。")
        return

    latest_time_row = batch_df.selectExpr("max(fetch_time) as latest_fetch_time").collect()[0]
    latest_fetch_time = latest_time_row["latest_fetch_time"]
    latest_fetch_time_text = latest_fetch_time.strftime("%Y-%m-%d %H:%M:%S") if latest_fetch_time else ""

    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password or None,
        decode_responses=True,
    )

    ranking_mapping = {row["title"]: int(row["hot_value"]) for row in ranking_rows if row["title"]}

    try:
        pipeline = client.pipeline()
        pipeline.delete(ranking_key)
        if ranking_mapping:
            pipeline.zadd(ranking_key, ranking_mapping)
        pipeline.set(f"{ranking_key}:fetch_time", latest_fetch_time_text)
        pipeline.execute()
        logger.info("Redis 当前排行已刷新，条目数=%s", len(ranking_mapping))
    finally:
        client.close()
