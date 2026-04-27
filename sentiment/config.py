# -*- coding: utf-8 -*-
"""
sentiment/config.py - 情感分析模块配置

从项目根目录 .env 读取配置，包括 MySQL 连接参数和情感分析参数。
提供 MySQL 连接参数方法供 data_loader、mysql_writer 复用。
路径兼容 Windows，不写死绝对路径。
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 将项目根目录加入 sys.path，兼容本地运行
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# 加载 .env 配置
load_dotenv(PROJECT_ROOT / ".env")


def get_mysql_config():
    """
    获取 MySQL 数据库连接配置。
    从 .env 中读取，如果未配置则使用默认值。

    Returns:
        dict: MySQL 连接参数字典
    """
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "database": os.getenv("MYSQL_DATABASE", "weibo_hot"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    }


def get_sentiment_config():
    """
    获取情感分析模块配置参数。

    Returns:
        dict: 情感分析配置字典
    """
    return {
        # 情感分析方法：默认使用 snownlp
        "method": os.getenv("SENTIMENT_METHOD", "snownlp"),
        # 正向情感阈值：分数 >= 此值视为正向
        "positive_threshold": float(os.getenv("SENTIMENT_POSITIVE_THRESHOLD", "0.6")),
        # 负向情感阈值：分数 <= 此值视为负向
        "negative_threshold": float(os.getenv("SENTIMENT_NEGATIVE_THRESHOLD", "0.4")),
        # 最多分析条数限制
        "top_limit": int(os.getenv("SENTIMENT_TOP_LIMIT", "100")),
    }


# 导出配置对象供模块内部使用
mysql_config = get_mysql_config()
sentiment_config = get_sentiment_config()
