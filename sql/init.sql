-- 微博热搜准实时分析系统初始化脚本
-- 第一版先建立原始明细表和预留统计表，方便后续做趋势分析扩展。

CREATE DATABASE IF NOT EXISTS weibo_hot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE weibo_hot;

CREATE TABLE IF NOT EXISTS hot_search_raw (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '自增主键',
    rank_no INT NOT NULL COMMENT '热搜排名',
    title VARCHAR(255) NOT NULL COMMENT '热搜标题',
    hot_value BIGINT DEFAULT 0 COMMENT '热度值',
    source VARCHAR(64) NOT NULL DEFAULT 'weibo_api' COMMENT '数据来源',
    fetch_time DATETIME NOT NULL COMMENT '采集时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '写入时间',
    KEY idx_title (title),
    KEY idx_fetch_time (fetch_time),
    KEY idx_title_fetch_time (title, fetch_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜原始流水表';

CREATE TABLE IF NOT EXISTS hot_search_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '自增主键',
    keyword VARCHAR(255) NOT NULL COMMENT '统计关键词',
    stat_time DATETIME NOT NULL COMMENT '统计时间窗口',
    record_count INT NOT NULL DEFAULT 0 COMMENT '该窗口内记录数',
    max_hot_value BIGINT NOT NULL DEFAULT 0 COMMENT '最大热度值',
    avg_hot_value BIGINT NOT NULL DEFAULT 0 COMMENT '平均热度值',
    best_rank INT NOT NULL DEFAULT 0 COMMENT '最佳排名',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '写入时间',
    UNIQUE KEY uk_keyword_stat_time (keyword, stat_time),
    KEY idx_stat_time (stat_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜统计预留表';
