"""数据库和缓存连接工具。"""

import pymysql
import redis

from config import BackendConfig


def get_mysql_connection(config: BackendConfig):
    """创建 MySQL 连接，查询类场景直接使用 DictCursor。"""

    return pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_redis_client(config: BackendConfig):
    """创建 Redis 连接。"""

    return redis.Redis(
        host=config.redis_host,
        port=config.redis_port,
        db=config.redis_db,
        password=config.redis_password or None,
        decode_responses=True,
    )
