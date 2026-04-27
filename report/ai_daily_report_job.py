"""第六期：AI 舆情日报生成任务。

当前版本使用规则模板生成中文 Markdown 日报，并预留大模型接口配置。

运行方式：
    python report/ai_daily_report_job.py
"""

from __future__ import annotations

import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from report.config import get_mysql_connection_params, settings


def main() -> None:
    """生成并落库 AI 舆情日报。"""
    print("[report] AI 舆情日报生成任务开始")
    data = _load_report_data()
    markdown, sections = _build_markdown_report(data)
    report_id = _write_report(markdown, sections, data["report_date"])
    output_path = _write_markdown_file(markdown, data["report_date"])

    print(f"[report] AI 舆情日报写入完成，report_id={report_id}")
    print(f"[report] Markdown 文件已导出：{output_path}")
    print("[report] AI 舆情日报生成任务结束")


def _load_report_data() -> dict[str, Any]:
    """读取日报所需的多张分析表。"""
    raw_df = _read_table(
        """
        SELECT title, rank_num, hot_value, source, fetch_time, created_at
        FROM hot_search_raw
        WHERE title IS NOT NULL AND TRIM(title) <> ''
        """
    )
    keyword_df = _read_table(
        """
        SELECT keyword, appear_count, max_hot_value, avg_hot_value, best_rank,
               latest_fetch_time, stat_date
        FROM hot_search_keyword_stats
        ORDER BY max_hot_value DESC, appear_count DESC
        LIMIT 100
        """
    )
    daily_df = _read_table(
        """
        SELECT stat_date, total_records, total_keywords, avg_hot_value,
               max_hot_value, min_rank
        FROM hot_search_daily_stats
        ORDER BY stat_date DESC
        LIMIT 30
        """
    )
    burst_df = _read_table(
        """
        SELECT keyword, burst_level, burst_probability, trend_direction,
               current_rank, current_hot_value, hot_value_change_rate,
               rank_change, appear_count, predict_date
        FROM hot_search_burst_predictions
        ORDER BY burst_probability DESC, current_hot_value DESC
        LIMIT 100
        """
    )
    sentiment_df = _read_table(
        """
        SELECT keyword, sentiment_score, sentiment_label, sentiment_label_cn,
               rank_num, hot_value, fetch_time, stat_date
        FROM hot_search_sentiment_stats
        """
    )
    semantic_df = _read_table(
        """
        SELECT keyword, cluster_id, cluster_name, cluster_name_cn,
               semantic_keywords, hot_value, rank_num, cluster_date
        FROM hot_search_semantic_clusters
        ORDER BY cluster_id ASC, hot_value DESC
        LIMIT 200
        """
    )
    lifecycle_df = _read_table(
        """
        SELECT keyword, duration_minutes, peak_hot_value, peak_rank,
               lifecycle_stage, lifecycle_stage_cn, is_disappeared, stat_date
        FROM hot_search_lifecycle_stats
        """
    )
    alerts_df = _read_table(
        """
        SELECT keyword, alert_type, alert_type_cn, alert_level, alert_level_cn,
               alert_message, trigger_value, threshold_value, alert_date, created_at
        FROM hot_search_alerts
        ORDER BY FIELD(alert_level, 'critical', 'high', 'medium', 'low'), created_at DESC
        LIMIT 200
        """
    )

    report_date = _infer_report_date(raw_df, daily_df)
    latest_ranking_df = _filter_latest_ranking(raw_df)
    return {
        "report_date": report_date,
        "raw_df": raw_df,
        "latest_ranking_df": latest_ranking_df,
        "keyword_df": keyword_df,
        "daily_df": daily_df,
        "burst_df": burst_df,
        "sentiment_df": sentiment_df,
        "semantic_df": semantic_df,
        "lifecycle_df": lifecycle_df,
        "alerts_df": alerts_df,
    }


def _read_table(query: str) -> pd.DataFrame:
    """读取表数据，缺表时返回空表，保障日报可渐进生成。"""
    connection = None
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        return pd.read_sql(query, connection)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            print(f"[report] 依赖表不存在，已跳过：{exc}")
            return pd.DataFrame()
        raise
    finally:
        if connection is not None:
            connection.close()


def _infer_report_date(raw_df: pd.DataFrame, daily_df: pd.DataFrame) -> date:
    if not raw_df.empty and "fetch_time" in raw_df.columns:
        fetch_times = pd.to_datetime(raw_df["fetch_time"], errors="coerce").dropna()
        if not fetch_times.empty:
            return fetch_times.max().date()
    if not daily_df.empty and "stat_date" in daily_df.columns:
        stat_dates = pd.to_datetime(daily_df["stat_date"], errors="coerce").dropna()
        if not stat_dates.empty:
            return stat_dates.max().date()
    return date.today()


def _filter_latest_ranking(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty or "fetch_time" not in raw_df.columns:
        return pd.DataFrame()
    df = raw_df.copy()
    df["fetch_time"] = pd.to_datetime(df["fetch_time"], errors="coerce")
    latest_time = df["fetch_time"].max()
    if pd.isna(latest_time):
        return pd.DataFrame()
    df = df[df["fetch_time"] == latest_time].copy()
    df["rank_num"] = pd.to_numeric(df.get("rank_num"), errors="coerce")
    df["hot_value"] = pd.to_numeric(df.get("hot_value"), errors="coerce").fillna(0)
    return df.sort_values(["rank_num", "hot_value"], ascending=[True, False]).reset_index(drop=True)


def _build_markdown_report(data: dict[str, Any]) -> tuple[str, dict[str, str]]:
    """构建 Markdown 日报正文和摘要字段。"""
    report_date = data["report_date"]
    overview = _build_overview_section(data)
    hot_topics = _build_hot_topics_section(data)
    burst_topics = _build_burst_topics_section(data)
    lifecycle = _build_lifecycle_section(data)
    sentiment = _build_sentiment_section(data)
    semantic = _build_semantic_section(data)
    risk_alert = _build_risk_alert_section(data)
    suggestions = _build_suggestion_section(data)

    markdown = "\n\n".join(
        [
            "# 微博热搜舆情日报",
            f"报告日期：{report_date.strftime('%Y-%m-%d')}",
            "## 一、今日热搜概况\n" + overview,
            "## 二、热度最高话题\n" + hot_topics,
            "## 三、爆发趋势话题\n" + burst_topics,
            "## 四、生命周期分析\n" + lifecycle,
            "## 五、情感倾向分析\n" + sentiment,
            "## 六、语义主题分布\n" + semantic,
            "## 七、舆情风险预警\n" + risk_alert,
            "## 八、研判建议\n" + suggestions,
        ]
    )
    sections = {
        "summary_text": overview,
        "hot_topics_text": hot_topics,
        "burst_topics_text": burst_topics,
        "sentiment_text": sentiment,
        "risk_alert_text": risk_alert,
        "suggestion_text": suggestions,
    }
    return markdown + "\n", sections


def _build_overview_section(data: dict[str, Any]) -> str:
    raw_df = data["raw_df"]
    latest_ranking_df = data["latest_ranking_df"]
    if raw_df.empty:
        return "今日暂未读取到原始热搜采集记录，请先运行采集任务。"

    df = raw_df.copy()
    df["fetch_time"] = pd.to_datetime(df["fetch_time"], errors="coerce")
    latest_time = df["fetch_time"].max()
    total_records = len(df)
    total_keywords = int(df["title"].nunique()) if "title" in df.columns else 0
    total_batches = int(df["fetch_time"].nunique()) if "fetch_time" in df.columns else 0
    latest_batch_count = len(latest_ranking_df)
    return (
        f"今日系统累计采集热搜记录 {total_records} 条，覆盖关键词 {total_keywords} 个，"
        f"形成采集批次 {total_batches} 个。最新采集时间为 {_fmt_dt(latest_time)}，"
        f"最新批次包含 {latest_batch_count} 条热搜。整体数据已从单纯榜单展示扩展为生命周期、情绪、语义和风险联动分析。"
    )


def _build_hot_topics_section(data: dict[str, Any]) -> str:
    latest_ranking_df = data["latest_ranking_df"]
    keyword_df = data["keyword_df"]
    source_df = latest_ranking_df if not latest_ranking_df.empty else keyword_df
    if source_df.empty:
        return "暂未生成热度最高话题列表。"

    lines = []
    for idx, row in source_df.head(10).iterrows():
        keyword = row.get("title") or row.get("keyword") or "未知话题"
        hot_value = _fmt_number(row.get("hot_value") or row.get("max_hot_value"))
        rank = row.get("rank_num") or row.get("best_rank") or "-"
        lines.append(f"{idx + 1}. 【{keyword}】热度 {hot_value}，当前/最佳排名 {rank}。")
    lines.append("上述话题构成今日高热讨论核心，建议结合排名变化和生命周期阶段判断后续传播强度。")
    return "\n".join(lines)


def _build_burst_topics_section(data: dict[str, Any]) -> str:
    burst_df = data["burst_df"]
    if burst_df.empty:
        return "暂未生成爆发趋势识别结果，请先运行机器学习爆发趋势识别任务。"

    lines = []
    for idx, row in burst_df.head(10).iterrows():
        keyword = row.get("keyword") or "未知话题"
        probability = _fmt_percent(row.get("burst_probability"))
        change_rate = _fmt_percent(row.get("hot_value_change_rate"))
        rank_change = _fmt_number(row.get("rank_change"))
        lines.append(
            f"{idx + 1}. 【{keyword}】爆发概率 {probability}，热度变化率 {change_rate}，排名变化 {rank_change}。"
        )
    lines.append("爆发概率靠前的话题适合作为未来窗口重点跟踪对象。")
    return "\n".join(lines)


def _build_lifecycle_section(data: dict[str, Any]) -> str:
    lifecycle_df = data["lifecycle_df"]
    if lifecycle_df.empty:
        return "暂未生成生命周期分析结果，请先运行生命周期分析任务。"

    counts = lifecycle_df["lifecycle_stage"].value_counts().to_dict()
    stage_text = (
        f"新上榜 {counts.get('new', 0)} 个，快速上升 {counts.get('rising', 0)} 个，"
        f"高位稳定 {counts.get('stable_high', 0)} 个，缓慢衰退 {counts.get('falling', 0)} 个，"
        f"快速降温 {counts.get('cooling', 0)} 个，已消失 {counts.get('disappeared', 0)} 个。"
    )
    rising = lifecycle_df[lifecycle_df["lifecycle_stage"] == "rising"].head(5)
    cooling = lifecycle_df[lifecycle_df["lifecycle_stage"] == "cooling"].head(5)
    details = [stage_text]
    if not rising.empty:
        details.append("快速上升话题：" + "、".join(f"【{x}】" for x in rising["keyword"].tolist()))
    if not cooling.empty:
        details.append("快速降温话题：" + "、".join(f"【{x}】" for x in cooling["keyword"].tolist()))
    return "\n".join(details)


def _build_sentiment_section(data: dict[str, Any]) -> str:
    sentiment_df = data["sentiment_df"]
    if sentiment_df.empty:
        return "暂未生成情感倾向分析结果，请先运行 SnowNLP 情感分析任务。"

    total = len(sentiment_df)
    positive = int((sentiment_df["sentiment_label"] == "positive").sum())
    neutral = int((sentiment_df["sentiment_label"] == "neutral").sum())
    negative = int((sentiment_df["sentiment_label"] == "negative").sum())
    avg_score = pd.to_numeric(sentiment_df["sentiment_score"], errors="coerce").mean()
    avg_text = "0.5000" if pd.isna(avg_score) else f"{avg_score:.4f}"
    return (
        f"情感样本共 {total} 条，其中正向 {positive} 条、中性 {neutral} 条、负向 {negative} 条，"
        f"平均情绪分为 {avg_text}。负向占比较高的话题需要和预警中心联动复核。"
    )


def _build_semantic_section(data: dict[str, Any]) -> str:
    semantic_df = data["semantic_df"]
    if semantic_df.empty:
        return "暂未生成语义聚类结果，请先运行语义聚类任务。"

    name_column = "cluster_name_cn" if "cluster_name_cn" in semantic_df.columns else "cluster_name"
    semantic_df[name_column] = semantic_df[name_column].fillna(semantic_df.get("cluster_name", "综合主题"))
    summary = (
        semantic_df.groupby(name_column)
        .agg(topic_count=("keyword", "count"), max_hot_value=("hot_value", "max"))
        .sort_values(["topic_count", "max_hot_value"], ascending=[False, False])
        .head(8)
    )
    lines = []
    for name, row in summary.iterrows():
        lines.append(f"- {name or '综合主题'}：{int(row['topic_count'])} 个话题，最高热度 {_fmt_number(row['max_hot_value'])}。")
    return "\n".join(lines) if lines else "语义主题分布较分散，暂无明显聚类中心。"


def _build_risk_alert_section(data: dict[str, Any]) -> str:
    alerts_df = data["alerts_df"]
    if alerts_df.empty:
        return "当前未生成舆情风险预警记录。"

    high_df = alerts_df[alerts_df["alert_level"].isin(["high", "critical"])]
    if high_df.empty:
        return "当前暂无高风险或严重风险预警，建议保持常规监测。"

    lines = []
    for _, row in high_df.head(10).iterrows():
        level = row.get("alert_level_cn") or row.get("alert_level") or "风险"
        message = row.get("alert_message") or ""
        lines.append(f"- {level}：{message}")
    return "\n".join(lines)


def _build_suggestion_section(data: dict[str, Any]) -> str:
    alerts_df = data["alerts_df"]
    burst_df = data["burst_df"]
    lifecycle_df = data["lifecycle_df"]

    suggestions = [
        "1. 对爆发概率高、排名跃升快的话题建立分钟级观察清单，优先跟踪热度拐点。",
        "2. 对负面情绪占比偏高的话题补充评论语义抽样，区分事实争议、情绪宣泄和谣言扩散。",
        "3. 对长时间高热话题进行生命周期复盘，识别持续传播的关键节点和触发因素。",
    ]
    if not alerts_df.empty and (alerts_df["alert_level"] == "critical").any():
        suggestions.append("4. 对严重风险预警话题执行人工复核，形成处置建议和后续追踪记录。")
    elif not burst_df.empty:
        suggestions.append("4. 将爆发趋势 Top10 作为下一轮未来窗口预测的重点输入。")
    if not lifecycle_df.empty and (lifecycle_df["lifecycle_stage"] == "cooling").any():
        suggestions.append("5. 对快速降温话题分析降温原因，用于优化后续预警阈值。")
    return "\n".join(suggestions[:5])


def _write_report(markdown: str, sections: dict[str, str], report_date: date) -> int:
    """将日报写入 hot_search_ai_reports。"""
    connection = None
    title = f"微博热搜舆情日报 {report_date.strftime('%Y-%m-%d')}"
    try:
        connection = pymysql.connect(**get_mysql_connection_params())
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO hot_search_ai_reports (
                report_title, report_date, report_type, summary_text, hot_topics_text,
                burst_topics_text, sentiment_text, risk_alert_text, suggestion_text,
                markdown_content
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    title,
                    report_date,
                    "daily",
                    sections.get("summary_text", ""),
                    sections.get("hot_topics_text", ""),
                    sections.get("burst_topics_text", ""),
                    sections.get("sentiment_text", ""),
                    sections.get("risk_alert_text", ""),
                    sections.get("suggestion_text", ""),
                    markdown,
                ),
            )
            return int(cursor.lastrowid)
    except pymysql.err.ProgrammingError as exc:
        if exc.args and exc.args[0] == 1146:
            raise RuntimeError("第六期日报表不存在，请先执行 sql/v6_intelligent_alert_report.sql") from exc
        raise
    finally:
        if connection is not None:
            connection.close()


def _write_markdown_file(markdown: str, report_date: date) -> Path:
    settings.report_output_dir.mkdir(parents=True, exist_ok=True)
    path = settings.report_output_dir / f"weibo_daily_report_{report_date.strftime('%Y%m%d')}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def _fmt_number(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    if not math.isfinite(number):
        number = 0.0
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if number.is_integer():
        return f"{int(number)}"
    return f"{number:.2f}"


def _fmt_percent(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    if not math.isfinite(number):
        number = 0.0
    return f"{number * 100:.1f}%"


def _fmt_dt(value) -> str:
    if pd.isna(value):
        return "未知"
    if isinstance(value, (datetime, pd.Timestamp)):
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


if __name__ == "__main__":
    main()
