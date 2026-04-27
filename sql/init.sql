CREATE DATABASE IF NOT EXISTS weibo_hot
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

USE weibo_hot;

CREATE TABLE IF NOT EXISTS hot_search_raw (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL COMMENT '热搜标题',
    rank_num INT DEFAULT NULL COMMENT '榜单排名',
    hot_value BIGINT DEFAULT NULL COMMENT '热度值',
    source VARCHAR(100) NOT NULL DEFAULT 'weibo' COMMENT '数据来源',
    fetch_time DATETIME NOT NULL COMMENT '本次采集时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入库时间',
    INDEX idx_fetch_time (fetch_time),
    INDEX idx_title (title),
    INDEX idx_fetch_title (fetch_time, title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜原始采集表';
