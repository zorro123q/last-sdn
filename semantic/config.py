# -*- coding: utf-8 -*-
"""
semantic/config.py - 语义聚类模块配置

从项目根目录 .env 读取配置，包括 MySQL 连接参数和语义聚类参数。
支持 sentence-transformers 句向量聚类，也支持 TF-IDF fallback。
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


def get_semantic_config():
    """
    获取语义聚类模块配置参数。

    Returns:
        dict: 语义聚类配置字典
    """
    return {
        # 嵌入方法：sentence_transformers 或 tfidf
        "embedding_method": os.getenv("SEMANTIC_EMBEDDING_METHOD", "sentence_transformers"),
        # sentence-transformers 模型名称（多语言支持）
        "model_name": os.getenv("SEMANTIC_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"),
        # 本地模型路径，如果不为空则优先从本地加载
        "local_model_path": os.getenv("SEMANTIC_LOCAL_MODEL_PATH", "").strip(),
        # 聚类数量
        "cluster_count": int(os.getenv("SEMANTIC_CLUSTER_COUNT", "6")),
        # 最多分析条数限制
        "top_limit": int(os.getenv("SEMANTIC_TOP_LIMIT", "500")),
        # 是否允许 fallback 到 TF-IDF
        "fallback_to_tfidf": os.getenv("SEMANTIC_FALLBACK_TO_TFIDF", "true").lower() in ("true", "1", "yes"),
    }


# 导出配置对象供模块内部使用
mysql_config = get_mysql_config()
semantic_config = get_semantic_config()
