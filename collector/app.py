"""采集入口脚本。"""

import logging
import time

from api_client import fetch_hot_searches
from config import CollectorConfig
from kafka_producer import HotSearchProducer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def run_collector() -> None:
    """循环拉取微博热搜并写入 Kafka。"""

    config = CollectorConfig()
    producer = HotSearchProducer(
        bootstrap_servers=config.kafka_bootstrap_servers,
        topic=config.kafka_topic,
        client_id=config.kafka_client_id,
        retries=config.kafka_retries,
    )

    logging.info("采集器启动，目标 Kafka Topic: %s", config.kafka_topic)

    try:
        while True:
            try:
                payload = fetch_hot_searches(config)
                metadata = producer.send(payload)
                logging.info(
                    "采集成功，条目数=%s，Kafka partition=%s，offset=%s",
                    len(payload["items"]),
                    metadata.partition,
                    metadata.offset,
                )
            except Exception as exc:  # noqa: BLE001
                logging.exception("采集或发送失败: %s", exc)

            if config.run_once:
                break

            time.sleep(config.collect_interval)
    except KeyboardInterrupt:
        logging.info("收到中断信号，准备退出采集器。")
    finally:
        producer.close()


if __name__ == "__main__":
    run_collector()
