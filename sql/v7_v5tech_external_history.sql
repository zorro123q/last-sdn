SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS hot_search_v5tech_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    title VARCHAR(255) NOT NULL COMMENT '热搜标题',
    url VARCHAR(1000) DEFAULT NULL COMMENT '热搜链接',
    rank_num INT DEFAULT NULL COMMENT '根据热度排序生成的排名',
    hot_value BIGINT DEFAULT 0 COMMENT '热搜热度值',
    dataset_date DATE NOT NULL COMMENT '数据集日期',
    fetch_time DATETIME NOT NULL COMMENT '模拟采集时间',
    source VARCHAR(100) NOT NULL DEFAULT 'v5tech_dataset' COMMENT '数据来源',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_title(title),
    INDEX idx_dataset_date(dataset_date),
    INDEX idx_fetch_time(fetch_time),
    INDEX idx_rank_num(rank_num),
    INDEX idx_hot_value(hot_value),
    INDEX idx_source(source),
    UNIQUE KEY uk_v5tech_date_title(source, dataset_date, title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='v5tech微博热搜历史数据表';