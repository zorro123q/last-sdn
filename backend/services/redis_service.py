"""Redis 查询服务。"""

from typing import Dict, List

from config import BackendConfig
from database import get_redis_client


def get_current_ranking(config: BackendConfig, limit: int = 20) -> Dict[str, object]:
    """从 Redis Sorted Set 读取当前热搜榜。"""

    client = get_redis_client(config)

    try:
        ranking_rows = client.zrevrange(config.redis_ranking_key, 0, limit - 1, withscores=True)
        latest_fetch_time = client.get(f"{config.redis_ranking_key}:fetch_time")
        data: List[Dict[str, object]] = [
            {
                "rank": index + 1,
                "title": title,
                "hot_value": int(score),
            }
            for index, (title, score) in enumerate(ranking_rows)
        ]
        return {
            "data": data,
            "count": len(data),
            "latest_fetch_time": latest_fetch_time,
        }
    finally:
        client.close()
