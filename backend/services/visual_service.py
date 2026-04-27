"""可视化增强查询服务。"""

from datetime import datetime
from typing import Any

import pymysql

from database import DatabaseConnectionError, DatabaseQueryError, get_connection


class VisualService:
    """封装 Dashboard 和其他页面所需的增强可视化查询。"""

    def get_hourly_heatmap(self) -> list[dict[str, Any]]:
        """返回按日期和小时分组的热搜采集热力图数据。"""
        sql = """
        SELECT
            DATE(fetch_time) AS stat_date,
            HOUR(fetch_time) AS stat_hour,
            COUNT(*) AS count,
            ROUND(AVG(hot_value), 0) AS avg_hot_value
        FROM hot_search_raw
        GROUP BY DATE(fetch_time), HOUR(fetch_time)
        ORDER BY stat_date ASC, stat_hour ASC
        """
        rows = self._fetch_all(sql)
        return [
            {
                "date": str(row["stat_date"]),
                "hour": int(row["stat_hour"]),
                "count": int(row["count"]),
                # Decimal → float，确保 JSON 可序列化且前端 Number() 正常
                "avg_hot_value": float(row["avg_hot_value"]) if row["avg_hot_value"] is not None else 0,
            }
            for row in rows
        ]

    def get_rank_movers(self) -> dict[str, list[dict[str, Any]]]:
        """返回最新两批热搜之间的排名变化榜（上升最快 / 下降最快）。"""
        conn = None
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                # 获取最新的两个 fetch_time
                cursor.execute(
                    """
                    SELECT DISTINCT fetch_time
                    FROM hot_search_raw
                    ORDER BY fetch_time DESC
                    LIMIT 2
                    """
                )
                times = [row["fetch_time"] for row in cursor.fetchall()]
                if len(times) < 2:
                    return {"up": [], "down": []}

                latest_time, prev_time = times[0], times[1]

                # 最新一批
                cursor.execute(
                    """
                    SELECT title, rank_num, hot_value
                    FROM hot_search_raw
                    WHERE fetch_time = %s
                    """,
                    (latest_time,),
                )
                latest_rows = {row["title"]: row for row in cursor.fetchall()}

                # 上一批
                cursor.execute(
                    """
                    SELECT title, rank_num, hot_value
                    FROM hot_search_raw
                    WHERE fetch_time = %s
                    """,
                    (prev_time,),
                )
                prev_rows = {row["title"]: row for row in cursor.fetchall()}

        except DatabaseConnectionError:
            raise
        except pymysql.MySQLError as exc:
            print(f"[backend] 排名变化查询失败：{exc}")
            raise DatabaseQueryError("排名变化查询失败，请稍后重试") from exc
        finally:
            if conn is not None:
                conn.close()

        movers = []
        for title, cur in latest_rows.items():
            prev = prev_rows.get(title)
            if prev is None:
                continue
            rank_delta = prev["rank_num"] - cur["rank_num"]
            hot_delta = cur["hot_value"] - prev["hot_value"]
            if rank_delta == 0 and hot_delta == 0:
                continue
            movers.append(
                {
                    "title": title,
                    "current_rank": cur["rank_num"],
                    "previous_rank": prev["rank_num"],
                    "rank_delta": rank_delta,
                    "current_hot_value": cur["hot_value"],
                    "previous_hot_value": prev["hot_value"],
                    "hot_delta": hot_delta,
                }
            )

        # 上升最快：rank_delta 最大（排名数字变小）
        up = sorted(movers, key=lambda x: (-x["rank_delta"], -x["hot_delta"]))[:10]
        # 下降最快：rank_delta 最小（排名数字变大）
        down = sorted(movers, key=lambda x: (x["rank_delta"], x["hot_delta"]))[:10]

        return {"up": up, "down": down}

    def get_insights(self) -> dict[str, Any]:
        """根据 summary、ranking、trend 数据生成自动洞察。"""
        conn = None
        items = []
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                # 总记录数、最新采集时间
                cursor.execute(
                    """
                    SELECT COUNT(*) AS total_records, MAX(fetch_time) AS latest_fetch_time
                    FROM hot_search_raw
                    """
                )
                row = cursor.fetchone()
                total_records = row["total_records"] if row else 0
                latest_fetch_time = row["latest_fetch_time"] if row else None

                items.append(
                    f"当前共采集 {total_records:,} 条热搜记录，"
                    f"最新采集时间为 {self._fmt(latest_fetch_time)}。"
                )

                # 当前榜首
                if latest_fetch_time:
                    cursor.execute(
                        """
                        SELECT title, hot_value
                        FROM hot_search_raw
                        WHERE fetch_time = %s
                        ORDER BY rank_num ASC, hot_value DESC
                        LIMIT 1
                        """,
                        (latest_fetch_time,),
                    )
                    top = cursor.fetchone()
                    if top:
                        items.append(
                            f"当前榜首话题为「{top['title']}」，热度值为 {top['hot_value']:,}。"
                        )

                # 高爆发话题数
                cursor.execute(
                    """
                    SELECT COUNT(*) AS high_burst_count
                    FROM hot_search_burst_predictions
                    WHERE burst_level = 3
                    """
                )
                burst_row = cursor.fetchone()
                high_burst = burst_row["high_burst_count"] if burst_row else 0
                items.append(f"当前高爆发话题共有 {high_burst} 个。")

                # 平均情感分
                cursor.execute(
                    """
                    SELECT AVG(sentiment_score) AS avg_sentiment
                    FROM hot_search_sentiment_stats
                    """
                )
                sentiment_row = cursor.fetchone()
                avg_sentiment = sentiment_row["avg_sentiment"] if sentiment_row else None
                if avg_sentiment is not None:
                    label = "正向" if avg_sentiment > 0.6 else ("负向" if avg_sentiment < 0.4 else "中性")
                    items.append(
                        f"当前微博热搜整体情绪偏{label}，平均情感分数为 {avg_sentiment:.3f}。"
                    )

                # 热度变化最明显
                cursor.execute(
                    """
                    SELECT keyword, hot_value_change_rate
                    FROM hot_search_burst_predictions
                    ORDER BY ABS(hot_value_change_rate) DESC
                    LIMIT 1
                    """
                )
                change_row = cursor.fetchone()
                if change_row:
                    items.append(
                        f"关键词「{change_row['keyword']}」在最近采集周期中热度变化最明显"
                        f"（变化率 {change_row['hot_value_change_rate']:.1%}）。"
                    )

        except DatabaseConnectionError:
            raise
        except pymysql.MySQLError:
            # 洞察生成失败时返回基础信息，不抛异常
            pass
        finally:
            if conn is not None:
                conn.close()

        return {"items": items}

    def _fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                return list(cursor.fetchall())
        except DatabaseConnectionError:
            raise
        except pymysql.MySQLError as exc:
            print(f"[backend] 可视化数据查询失败：{exc}")
            raise DatabaseQueryError("可视化数据查询失败，请稍后重试") from exc
        finally:
            if connection is not None:
                connection.close()

    def _fmt(self, value: datetime | None) -> str:
        if value is None:
            return "暂无"
        return value.strftime("%Y-%m-%d %H:%M")


visual_service = VisualService()
