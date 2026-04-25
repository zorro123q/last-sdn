"""后端服务配置。"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# 统一从项目根目录读取环境变量。
ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ROOT_ENV_PATH)


def _get_int(name: str, default: int) -> int:
    """读取整数环境变量，异常时回退默认值。"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_origins(name: str) -> list[str]:
    """读取逗号分隔的跨域白名单。"""
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class BackendSettings:
    """后端运行配置。"""

    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    backend_host: str
    backend_port: int
    backend_cors_origins: list[str]


settings = BackendSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    backend_host=os.getenv("BACKEND_HOST", "127.0.0.1"),
    backend_port=_get_int("BACKEND_PORT", 8000),
    backend_cors_origins=_get_origins("BACKEND_CORS_ORIGINS")
    or ["http://127.0.0.1:5173", "http://localhost:5173"],
)
