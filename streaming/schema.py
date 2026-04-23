"""Kafka 消息结构定义。"""

from pyspark.sql.types import ArrayType, IntegerType, LongType, StringType, StructField, StructType


ITEM_SCHEMA = StructType(
    [
        StructField("rank", IntegerType(), True),
        StructField("title", StringType(), True),
        StructField("hot_value", LongType(), True),
        StructField("source", StringType(), True),
        StructField("fetch_time", StringType(), True),
    ]
)

PAYLOAD_SCHEMA = StructType(
    [
        StructField("fetch_time", StringType(), True),
        StructField("items", ArrayType(ITEM_SCHEMA), True),
    ]
)
