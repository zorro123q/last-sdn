-- ============================================================
-- 第五期情感分析与语义聚类 SQL 脚本
-- 文件名: v5_sentiment_semantic.sql
-- 说明: 创建情感分析结果表和语义聚类结果表
-- ============================================================

-- 设置连接字符集，避免中文注释和中文内容乱码
SET NAMES utf8mb4;
SET character_set_client = utf8mb4;
SET character_set_connection = utf8mb4;
SET character_set_results = utf8mb4;

-- ============================================================
-- 表1: hot_search_sentiment_stats
-- 微博热搜标题情感分析单条结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS hot_search_sentiment_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',

    keyword VARCHAR(255) NOT NULL COMMENT '热搜关键词（标题）',

    sentiment_score DOUBLE DEFAULT 0.5 COMMENT '情感分数，范围0-1',

    sentiment_label VARCHAR(20) DEFAULT 'neutral' COMMENT '情感标签：positive/neutral/negative',

    -- 注意：这里不要设置 DEFAULT '中性'
    -- 某些 MySQL 版本或连接字符集下，中文默认值可能导致 ERROR 1067
    sentiment_label_cn VARCHAR(20) DEFAULT NULL COMMENT '中文情感标签：正向/中性/负向',

    rank_num INT DEFAULT NULL COMMENT '热搜排名',

    hot_value BIGINT DEFAULT 0 COMMENT '热度值',

    fetch_time DATETIME DEFAULT NULL COMMENT '采集时间',

    stat_date DATE NOT NULL COMMENT '统计日期',

    method_name VARCHAR(50) DEFAULT 'snownlp' COMMENT '分析方法',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_keyword (keyword),
    INDEX idx_sentiment_label (sentiment_label),
    INDEX idx_stat_date (stat_date),
    INDEX idx_sentiment_score (sentiment_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微博热搜情感分析结果表';

-- ============================================================
-- 表2: hot_search_sentiment_daily_stats
-- 微博热搜每日情感统计表
-- ============================================================
CREATE TABLE IF NOT EXISTS hot_search_sentiment_daily_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',

    stat_date DATE NOT NULL COMMENT '统计日期',

    avg_sentiment_score DOUBLE DEFAULT 0.5 COMMENT '平均情感分数',

    positive_count INT DEFAULT 0 COMMENT '正向情感数量',

    neutral_count INT DEFAULT 0 COMMENT '中性情感数量',

    negative_count INT DEFAULT 0 COMMENT '负向情感数量',

    total_count INT DEFAULT 0 COMMENT '总数量',

    positive_ratio DOUBLE DEFAULT 0 COMMENT '正向占比',

    neutral_ratio DOUBLE DEFAULT 0 COMMENT '中性占比',

    negative_ratio DOUBLE DEFAULT 0 COMMENT '负向占比',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微博热搜每日情感统计表';

-- ============================================================
-- 表3: hot_search_semantic_clusters
-- 微博热搜语义聚类结果表
-- ============================================================
CREATE TABLE IF NOT EXISTS hot_search_semantic_clusters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',

    keyword VARCHAR(255) NOT NULL COMMENT '热搜关键词（标题）',

    cluster_id INT NOT NULL COMMENT '聚类ID',

    cluster_name VARCHAR(100) DEFAULT 'general' COMMENT '聚类主题名称',

    cluster_name_cn VARCHAR(100) DEFAULT NULL COMMENT '中文聚类主题名称，例如：综合热点、娱乐热点、社会热点',

    semantic_keywords TEXT COMMENT '聚类关键词',

    embedding_method VARCHAR(80) DEFAULT 'sentence_transformers' COMMENT '嵌入方法',

    hot_value BIGINT DEFAULT 0 COMMENT '热度值',

    rank_num INT DEFAULT NULL COMMENT '排名',

    cluster_date DATE NOT NULL COMMENT '聚类日期',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_keyword (keyword),
    INDEX idx_cluster_id (cluster_id),
    INDEX idx_cluster_name (cluster_name),
    INDEX idx_cluster_date (cluster_date),
    INDEX idx_embedding_method (embedding_method)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微博热搜语义聚类结果表';

-- ============================================================
-- 说明
-- ============================================================
-- 本脚本创建三张新表，不修改已有表结构
-- 不要删除 hot_search_raw 表
-- 不要删除第三期统计表：hot_search_keyword_stats, hot_search_daily_stats
-- 不要删除第四期机器学习结果表：hot_search_feature_stats, hot_search_burst_predictions, hot_search_topic_clusters