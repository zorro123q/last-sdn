"""第六期 AI 舆情日报模块配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


@dataclass(frozen=True)
class ReportSettings:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str
    report_output_dir: Path
    openai_api_key: str
    openai_model: str
    dashscope_api_key: str

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


settings = ReportSettings(
    mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    mysql_port=int(os.getenv("MYSQL_PORT", "3306") or 3306),
    mysql_user=os.getenv("MYSQL_USER", "root"),
    mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
    mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
    mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    report_output_dir=_resolve_path(os.getenv("AI_REPORT_OUTPUT_DIR", "storage/reports")),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
)


def get_mysql_connection_params() -> dict[str, Any]:
    return settings.mysql_connection_params()
