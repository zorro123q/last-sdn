"""采集模块配置。"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# 加载项目根目录下的 .env 文件，方便在不同目录启动脚本。
ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_PATH)


def _get_int(name: str, default: int) -> int:
    """读取整数环境变量，读取失败时返回默认值。"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_bool(name: str, default: bool) -> bool:
    """读取布尔环境变量。"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class CollectorSettings:
    """采集模块运行配置。"""

    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    weibo_api_url: str
    weibo_api_timeout: int
    weibo_api_source: str
    weibo_cookie: str
    collect_user_agent: str
    collect_interval_seconds: int
    collect_run_once: bool


settings = CollectorSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    weibo_api_url=os.getenv("WEIBO_API_URL", "https://weibo.com/ajax/side/hotSearch"),
    weibo_api_timeout=_get_int("WEIBO_API_TIMEOUT", 10),
    weibo_api_source=os.getenv("WEIBO_API_SOURCE", "weibo"),
    weibo_cookie=os.getenv("WEIBO_COOKIE", ""),
    collect_user_agent=os.getenv(
        "COLLECT_USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
    ),
    collect_interval_seconds=max(_get_int("COLLECT_INTERVAL_SECONDS", 300), 1),
    collect_run_once=_get_bool("COLLECT_RUN_ONCE", False),
)
