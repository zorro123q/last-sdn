"""流处理模块配置。"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class StreamingConfig:
    """集中维护流处理所需配置。"""

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC_RAW", "weibo_hot_raw")
    kafka_starting_offsets: str = os.getenv("KAFKA_STARTING_OFFSETS", "latest")

    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "weibo_hot")
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "root")
    mysql_table_raw: str = os.getenv("MYSQL_TABLE_RAW", "hot_search_raw")

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_ranking_key: str = os.getenv("REDIS_RANKING_KEY", "weibo:ranking:current")

    spark_app_name: str = os.getenv("SPARK_APP_NAME", "weibo-hot-streaming")
    spark_checkpoint_dir: str = os.getenv("SPARK_CHECKPOINT_DIR", "./streaming/checkpoints/weibo_hot")
    spark_jars_packages: str = os.getenv(
        "SPARK_JARS_PACKAGES",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.mysql:mysql-connector-j:8.3.0",
    )

    @property
    def mysql_jdbc_url(self) -> str:
        """拼接 MySQL JDBC 连接串。"""

        return (
            f"jdbc:mysql://{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8mb4"
        )

    @property
    def mysql_connection_properties(self) -> dict:
        """Spark JDBC 写入所需属性。"""

        return {
            "user": self.mysql_user,
            "password": self.mysql_password,
            "driver": "com.mysql.cj.jdbc.Driver",
        }
