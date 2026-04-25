CREATE TABLE IF NOT EXISTS hot_search_keyword_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    keyword VARCHAR(255) NOT NULL COMMENT '热搜关键词',
    appear_count INT NOT NULL DEFAULT 0 COMMENT '出现次数',
    max_hot_value BIGINT DEFAULT 0 COMMENT '最高热度值',
    avg_hot_value DOUBLE DEFAULT 0 COMMENT '平均热度值',
    best_rank INT DEFAULT NULL COMMENT '最佳排名',
    latest_fetch_time DATETIME DEFAULT NULL COMMENT '最近采集时间',
    stat_date DATE NOT NULL COMMENT '统计日期',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_keyword (keyword),
    INDEX idx_stat_date (stat_date),
    INDEX idx_appear_count (appear_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜关键词统计表';

CREATE TABLE IF NOT EXISTS hot_search_daily_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL COMMENT '统计日期',
    total_records INT NOT NULL DEFAULT 0 COMMENT '总记录数',
    total_keywords INT NOT NULL DEFAULT 0 COMMENT '关键词总数',
    avg_hot_value DOUBLE DEFAULT 0 COMMENT '平均热度值',
    max_hot_value BIGINT DEFAULT 0 COMMENT '最高热度值',
    min_rank INT DEFAULT NULL COMMENT '最高榜单排名',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜每日统计表';
