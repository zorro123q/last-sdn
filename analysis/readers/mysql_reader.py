"""MySQL 原始表读取逻辑。"""

from pyspark.sql import DataFrame, SparkSession

from analysis.config import settings


def read_hot_search_raw(spark: SparkSession) -> DataFrame:
    """通过 Spark JDBC 读取 hot_search_raw 原始采集表。"""
    print("[analysis] 正在读取 MySQL 表：hot_search_raw")

    query = """
    (
        SELECT id, title, rank_num, hot_value, source, fetch_time, created_at
        FROM hot_search_raw
    ) AS hot_search_raw_src
    """

    try:
        return (
            spark.read.format("jdbc")
            .option("url", settings.jdbc_url)
            .option("dbtable", query)
            .option("user", settings.mysql_user)
            .option("password", settings.mysql_password)
            .option("driver", settings.spark_mysql_driver)
            .load()
        )
    except Exception as exc:
        print("[analysis] 读取 hot_search_raw 失败，请检查以下配置：")
        print("[analysis] 1. MySQL 服务是否启动")
        print("[analysis] 2. 数据库账号密码是否正确")
        print(f"[analysis] 3. JDBC URL 是否正确：{settings.jdbc_url}")
        print("[analysis] 4. MySQL Connector/J Jar 是否已配置到 SPARK_MYSQL_JAR")
        print("[analysis] 5. JAVA_HOME 是否已正确配置")
        raise RuntimeError("读取 hot_search_raw 失败，请检查 MySQL、JDBC Jar 和 JAVA_HOME 配置") from exc
