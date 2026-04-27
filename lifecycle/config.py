"""第六期生命周期分析模块配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class LifecycleSettings:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    lifecycle_rising_rate_threshold: float
    lifecycle_cooling_rate_threshold: float
    lifecycle_rank_jump_threshold: int
    lifecycle_disappeared_cycles: float

    def mysql_connection_params(self) -> dict[str, Any]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
            "charset": self.mysql_charset,
            "autocommit": True,
        }


settings = LifecycleSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    lifecycle_rising_rate_threshold=_get_float("LIFECYCLE_RISING_RATE_THRESHOLD", 0.3),
    lifecycle_cooling_rate_threshold=_get_float("LIFECYCLE_COOLING_RATE_THRESHOLD", -0.3),
    lifecycle_rank_jump_threshold=max(_get_int("LIFECYCLE_RANK_JUMP_THRESHOLD", 5), 1),
    lifecycle_disappeared_cycles=max(_get_float("LIFECYCLE_DISAPPEARED_CYCLES", 2.0), 1.0),
)


def get_mysql_connection_params() -> dict[str, Any]:
    return settings.mysql_connection_params()
