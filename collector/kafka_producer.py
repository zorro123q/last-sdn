"""Kafka 生产者封装。"""

import json
from typing import Any, Dict

from kafka import KafkaProducer


class HotSearchProducer:
    """负责把标准化后的热搜数据发送到 Kafka。"""

    def __init__(self, bootstrap_servers: str, topic: str, client_id: str, retries: int = 3) -> None:
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            retries=retries,
            linger_ms=100,
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        )

    def send(self, payload: Dict[str, Any]):
        """发送单条消息，并等待 Kafka 返回元数据。"""

        future = self.producer.send(self.topic, payload)
        return future.get(timeout=10)

    def close(self) -> None:
        """优雅关闭生产者，避免数据未刷盘。"""

        try:
            self.producer.flush()
        finally:
            self.producer.close()
