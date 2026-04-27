"""
SparkSession 创建工具。
"""

import os
from pathlib import Path

from pyspark.sql import SparkSession

from analysis.config import settings


def create_spark_session() -> SparkSession:
    """
    创建本地 PySpark 批处理使用的 SparkSession。

    Windows 下不要优先使用 spark.jars 加载本地 Jar，
    否则容易触发 HADOOP_HOME / winutils.exe 问题。
    """
    print(f"[analysis] Spark appName：{settings.spark_app_name}")
    print(f"[analysis] Spark master：{settings.spark_master}")

    builder = (
        SparkSession.builder
        .appName(settings.spark_app_name)
        .master(settings.spark_master)
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
        .config("spark.ui.showConsoleProgress", "false")
    )

    if settings.spark_mysql_jar:
        jar_path = Path(settings.spark_mysql_jar).resolve()

        if jar_path.exists():
            jar_str = str(jar_path)
            print(f"[analysis] 加载 MySQL JDBC Jar：{jar_str}")

            # Windows 本地运行时，用 extraClassPath 加载 JDBC 驱动
            # 避免 spark.jars 触发 Hadoop 的 winutils.exe 权限处理
            builder = (
                builder
                .config("spark.driver.extraClassPath", jar_str)
                .config("spark.executor.extraClassPath", jar_str)
            )

            # 非 Windows 环境才使用 spark.jars
            if os.name != "nt":
                builder = builder.config("spark.jars", jar_str)
        else:
            print(f"[analysis] SPARK_MYSQL_JAR 文件不存在：{jar_str}")
    else:
        print("[analysis] 未配置 SPARK_MYSQL_JAR，请确认 MySQL Connector/J 可被 Spark 找到")

    spark = builder.getOrCreate()

    timezone = spark.conf.get("spark.sql.session.timeZone")
    print(f"[analysis] Spark session timeZone：{timezone}")

    return spark