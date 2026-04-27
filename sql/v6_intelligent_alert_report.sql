SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS hot_search_lifecycle_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    first_seen_time DATETIME DEFAULT NULL,
    last_seen_time DATETIME DEFAULT NULL,
    duration_minutes DOUBLE DEFAULT 0,
    peak_hot_value BIGINT DEFAULT 0,
    peak_rank INT DEFAULT NULL,
    rise_speed DOUBLE DEFAULT 0,
    fall_speed DOUBLE DEFAULT 0,
    appear_count INT DEFAULT 0,
    lifecycle_stage VARCHAR(50) DEFAULT 'unknown',
    lifecycle_stage_cn VARCHAR(50) DEFAULT '未知',
    is_disappeared TINYINT DEFAULT 0,
    stat_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_keyword(keyword),
    INDEX idx_stat_date(stat_date),
    INDEX idx_lifecycle_stage(lifecycle_stage),
    INDEX idx_peak_hot_value(peak_hot_value),
    INDEX idx_duration_minutes(duration_minutes)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜生命周期分析表';

CREATE TABLE IF NOT EXISTS hot_search_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    alert_type VARCHAR(80) NOT NULL,
    alert_type_cn VARCHAR(80) NOT NULL,
    alert_level VARCHAR(30) NOT NULL DEFAULT 'low',
    alert_level_cn VARCHAR(30) NOT NULL DEFAULT '低风险',
    alert_message TEXT,
    trigger_value DOUBLE DEFAULT 0,
    threshold_value DOUBLE DEFAULT 0,
    related_metric VARCHAR(100) DEFAULT '',
    is_read TINYINT DEFAULT 0,
    alert_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_keyword(keyword),
    INDEX idx_alert_type(alert_type),
    INDEX idx_alert_level(alert_level),
    INDEX idx_alert_date(alert_date),
    INDEX idx_is_read(is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜舆情风险预警表';

CREATE TABLE IF NOT EXISTS hot_search_ai_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    report_title VARCHAR(255) NOT NULL,
    report_date DATE NOT NULL,
    report_type VARCHAR(50) DEFAULT 'daily',
    summary_text TEXT,
    hot_topics_text TEXT,
    burst_topics_text TEXT,
    sentiment_text TEXT,
    risk_alert_text TEXT,
    suggestion_text TEXT,
    markdown_content MEDIUMTEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_report_date(report_date),
    INDEX idx_report_type(report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微博热搜 AI 舆情日报表';

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_type VARCHAR(80) NOT NULL,
    job_name VARCHAR(120) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    status_cn VARCHAR(30) NOT NULL DEFAULT '等待中',
    start_time DATETIME DEFAULT NULL,
    end_time DATETIME DEFAULT NULL,
    duration_seconds DOUBLE DEFAULT 0,
    command_text VARCHAR(500) DEFAULT '',
    log_text MEDIUMTEXT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_job_type(job_type),
    INDEX idx_status(status),
    INDEX idx_start_time(start_time),
    INDEX idx_created_at(created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析任务运行记录表';

CREATE TABLE IF NOT EXISTS data_quality_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    total_raw_records INT DEFAULT 0,
    total_batches INT DEFAULT 0,
    total_keywords INT DEFAULT 0,
    latest_fetch_time DATETIME DEFAULT NULL,
    null_hot_value_count INT DEFAULT 0,
    duplicate_title_count INT DEFAULT 0,
    latest_batch_count INT DEFAULT 0,
    collector_status VARCHAR(30) DEFAULT 'unknown',
    analysis_status VARCHAR(30) DEFAULT 'unknown',
    ml_status VARCHAR(30) DEFAULT 'unknown',
    health_score DOUBLE DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_stat_date(stat_date),
    INDEX idx_health_score(health_score),
    INDEX idx_collector_status(collector_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据质量监控表';
