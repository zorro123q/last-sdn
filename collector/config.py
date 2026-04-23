"""采集模块配置。"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class CollectorConfig:
    """集中维护采集模块所需配置。"""

    api_url: str = os.getenv("WEIBO_API_URL", "https://weibo.com/ajax/side/hotSearch")
    request_timeout: int = int(os.getenv("WEIBO_REQUEST_TIMEOUT", "15"))
    collect_interval: int = int(os.getenv("COLLECT_INTERVAL_SECONDS", "300"))
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC_RAW", "weibo_hot_raw")
    kafka_client_id: str = os.getenv("KAFKA_CLIENT_ID", "weibo-hot-collector")
    kafka_retries: int = int(os.getenv("KAFKA_RETRIES", "3"))
    user_agent: str = os.getenv(
        "WEIBO_USER_AGENT",
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    run_once: bool = os.getenv("COLLECTOR_RUN_ONCE", "false").lower() == "true"
    source_name: str = os.getenv("COLLECTOR_SOURCE_NAME", "weibo_api")
