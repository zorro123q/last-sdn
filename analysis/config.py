"""PySpark 离线分析模块配置。"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# 统一从项目根目录读取 .env，支持在根目录或 analysis 目录启动任务。
ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ROOT_ENV_PATH)


def _get_int(name: str, default: int) -> int:
    """读取整数环境变量，非法或为空时使用默认值。"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class AnalysisSettings:
    """PySpark 批处理任务运行配置。"""

    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    spark_app_name: str
    spark_master: str
    spark_mysql_driver: str
    spark_mysql_jar: str

    @property
    def jdbc_url(self) -> str:
        """Spark JDBC 读取和写入 MySQL 使用的 URL。"""
        return (
            f"jdbc:mysql://{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8"
        )

    @property
    def jdbc_properties(self) -> dict[str, str]:
        """Spark JDBC read/write 所需的连接属性。"""
        return {
            "user": self.mysql_user,
            "password": self.mysql_password,
            "driver": self.spark_mysql_driver,
        }


settings = AnalysisSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    spark_app_name=os.getenv("SPARK_APP_NAME", "WeiboHotAnalysisJob"),
    spark_master=os.getenv("SPARK_MASTER", "local[*]"),
    spark_mysql_driver=os.getenv("SPARK_MYSQL_DRIVER", "com.mysql.cj.jdbc.Driver"),
    spark_mysql_jar=os.getenv("SPARK_MYSQL_JAR", "").strip(),
)
