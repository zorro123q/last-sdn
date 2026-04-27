SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS hot_search_feature_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    current_rank INT DEFAULT NULL,
    current_hot_value BIGINT DEFAULT 0,
    appear_count INT DEFAULT 0,
    max_hot_value BIGINT DEFAULT 0,
    avg_hot_value DOUBLE DEFAULT 0,
    min_rank INT DEFAULT NULL,
    best_rank INT DEFAULT NULL,
    recent_avg_hot_value DOUBLE DEFAULT 0,
    recent_max_hot_value BIGINT DEFAULT 0,
    hot_value_change DOUBLE DEFAULT 0,
    hot_value_change_rate DOUBLE DEFAULT 0,
    rank_change DOUBLE DEFAULT 0,
    duration_minutes DOUBLE DEFAULT 0,
    title_length INT DEFAULT 0,
    has_number TINYINT DEFAULT 0,
    has_hashtag TINYINT DEFAULT 0,
    fetch_hour INT DEFAULT NULL,
    feature_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_keyword(keyword),
    INDEX idx_feature_date(feature_date),
    INDEX idx_current_hot_value(current_hot_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜机器学习特征表';


CREATE TABLE IF NOT EXISTS hot_search_burst_predictions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    burst_level INT NOT NULL DEFAULT 1,
    burst_probability DOUBLE DEFAULT 0,
    trend_direction VARCHAR(20) NOT NULL DEFAULT 'stable',
    current_rank INT DEFAULT NULL,
    current_hot_value BIGINT DEFAULT 0,
    hot_value_change_rate DOUBLE DEFAULT 0,
    rank_change DOUBLE DEFAULT 0,
    appear_count INT DEFAULT 0,
    model_name VARCHAR(80) NOT NULL DEFAULT 'sklearn_gradient_boosting',
    predict_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_keyword(keyword),
    INDEX idx_burst_level(burst_level),
    INDEX idx_burst_probability(burst_probability),
    INDEX idx_predict_date(predict_date),
    INDEX idx_trend_direction(trend_direction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜爆发趋势识别结果表';


CREATE TABLE IF NOT EXISTS hot_search_topic_clusters (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    cluster_id INT NOT NULL,

    -- 注意：这里不要使用 TEXT DEFAULT，也不要直接使用中文默认值，避免 MySQL 兼容性问题
    cluster_name VARCHAR(100) NOT NULL DEFAULT '',

    tfidf_keywords TEXT,
    hot_value BIGINT DEFAULT 0,
    rank_num INT DEFAULT NULL,
    cluster_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_keyword(keyword),
    INDEX idx_cluster_id(cluster_id),
    INDEX idx_cluster_name(cluster_name),
    INDEX idx_cluster_date(cluster_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜主题聚类结果表';