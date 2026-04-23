"""后端服务配置。"""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List

from dotenv import load_dotenv


load_dotenv()


@dataclass
class BackendConfig:
    """集中维护 FastAPI 所需配置。"""

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

    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    @property
    def cors_origins(self) -> List[str]:
        """把逗号分隔的 CORS 配置转成列表。"""

        raw_value = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173")
        return [item.strip() for item in raw_value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> BackendConfig:
    """缓存配置对象，避免每次请求重复解析环境变量。"""

    return BackendConfig()
