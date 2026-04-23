"""MySQL 写入封装。"""

import logging

from pyspark.sql import DataFrame


logger = logging.getLogger(__name__)


def write_raw_batch(batch_df: DataFrame, batch_id: int, jdbc_url: str, connection_properties: dict, table_name: str) -> None:
    """把当前微批次原始热搜记录写入 MySQL。"""

    if batch_df.limit(1).count() == 0:
        logger.info("批次 %s 无数据，跳过 MySQL 写入。", batch_id)
        return

    output_df = batch_df.select("rank_no", "title", "hot_value", "source", "fetch_time")
    output_df.write.mode("append").jdbc(url=jdbc_url, table=table_name, properties=connection_properties)
    logger.info("批次 %s 已写入 MySQL，记录数=%s", batch_id, output_df.count())
