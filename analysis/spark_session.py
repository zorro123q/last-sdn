"""SparkSession 创建工具。"""

from pyspark.sql import SparkSession

from analysis.config import settings


def create_spark_session() -> SparkSession:
    """创建本地 PySpark 批处理使用的 SparkSession。"""
    print(f"[analysis] Spark appName：{settings.spark_app_name}")
    print(f"[analysis] Spark master：{settings.spark_master}")

    builder = (
        SparkSession.builder.appName(settings.spark_app_name)
        .master(settings.spark_master)
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
    )

    if settings.spark_mysql_jar:
        print(f"[analysis] 加载 MySQL JDBC Jar：{settings.spark_mysql_jar}")
        builder = builder.config("spark.jars", settings.spark_mysql_jar)
    else:
        print("[analysis] 未配置 SPARK_MYSQL_JAR，请确认 MySQL Connector/J 可被 Spark 找到")

    spark = builder.getOrCreate()
    timezone = spark.conf.get("spark.sql.session.timeZone")
    print(f"[analysis] Spark session timeZone：{timezone}")
    return spark
