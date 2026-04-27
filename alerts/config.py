"""第六期舆情预警模块配置。"""

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
class AlertSettings:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    hot_growth_threshold: float
    rank_jump_threshold: int
    burst_probability_threshold: float
    negative_ratio_threshold: float
    long_duration_minutes: int
    cooling_hot_value_threshold: int

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


settings = AlertSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=_get_int("MYSQL_PORT", 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    hot_growth_threshold=_get_float("ALERT_HOT_GROWTH_THRESHOLD", 0.5),
    rank_jump_threshold=max(_get_int("ALERT_RANK_JUMP_THRESHOLD", 8), 1),
    burst_probability_threshold=_get_float("ALERT_BURST_PROBABILITY_THRESHOLD", 0.85),
    negative_ratio_threshold=_get_float("ALERT_NEGATIVE_RATIO_THRESHOLD", 0.6),
    long_duration_minutes=max(_get_int("ALERT_LONG_DURATION_MINUTES", 360), 1),
    cooling_hot_value_threshold=max(_get_int("ALERT_COOLING_HOT_VALUE_THRESHOLD", 100000), 0),
)


def get_mysql_connection_params() -> dict[str, Any]:
    return settings.mysql_connection_params()
