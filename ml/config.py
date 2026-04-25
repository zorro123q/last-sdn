"""第四期机器学习模块配置。"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# 统一从项目根目录读取 .env，兼容在根目录或 ml 子目录启动脚本。
ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ROOT_ENV_PATH)


def _get_int(name: str, default: int) -> int:
    """读取整数配置，缺失或非法时使用默认值，避免本地演示因配置缺失中断。"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    """读取浮点数配置，缺失或非法时使用默认值。"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _resolve_model_dir(value: str) -> Path:
    """把模型目录转换为跨平台路径，支持 Windows 相对路径。"""
    path = Path(value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


@dataclass(frozen=True)
class MLSettings:
    """机器学习分析任务运行配置。"""

    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    ml_min_history_count: int
    ml_recent_window: int
    ml_burst_hot_growth_threshold: float
    ml_burst_top_rank_threshold: int
    ml_model_name: str
    ml_cluster_count: int
    ml_top_limit: int
    ml_model_dir: Path

    def mysql_connection_params(self) -> dict[str, Any]:
        """返回 pymysql / pandas 可复用的 MySQL 连接参数。"""
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
            "charset": self.mysql_charset,
            "autocommit": True,
        }


settings = MLSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    ml_min_history_count=max(_get_int("ML_MIN_HISTORY_COUNT", 3), 1),
    ml_recent_window=max(_get_int("ML_RECENT_WINDOW", 5), 2),
    ml_burst_hot_growth_threshold=_get_float("ML_BURST_HOT_GROWTH_THRESHOLD", 0.3),
    ml_burst_top_rank_threshold=max(_get_int("ML_BURST_TOP_RANK_THRESHOLD", 10), 1),
    ml_model_name=os.getenv("ML_MODEL_NAME", "sklearn_gradient_boosting"),
    ml_cluster_count=max(_get_int("ML_CLUSTER_COUNT", 6), 1),
    ml_top_limit=min(max(_get_int("ML_TOP_LIMIT", 100), 1), 1000),
    ml_model_dir=_resolve_model_dir(os.getenv("ML_MODEL_DIR", "ml/model_store")),
)


def get_mysql_connection_params() -> dict[str, Any]:
    """模块级连接参数方法，供 data_loader、写入任务和报告导出复用。"""
    return settings.mysql_connection_params()
