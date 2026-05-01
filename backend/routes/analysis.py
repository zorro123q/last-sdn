"""PySpark 分析结果接口。"""

import random
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from database import get_connection
from services.analysis_service import analysis_service
from services.ml_analysis_service import ml_analysis_service
from services.visual_service import visual_service


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/keywords/top")
def get_top_keywords(limit: int = Query(20, ge=1, le=100)) -> dict:
    """返回关键词 TopN 统计结果。"""
    items = analysis_service.get_top_keywords(limit)
    return {"count": len(items), "items": items}


@router.get("/daily")
def get_daily_stats() -> dict:
    """返回每日采集统计结果。"""
    items = analysis_service.get_daily_stats()
    return {"count": len(items), "items": items}


@router.post("/run")
def run_analysis_job() -> dict:
    """手动触发 PySpark 批处理任务，任务在后台子进程中执行。"""
    root_dir = Path(__file__).resolve().parents[2]
    job_path = root_dir / "analysis" / "batch_job.py"

    subprocess.Popen([sys.executable, str(job_path)], cwd=root_dir)
    return {
        "message": "PySpark 分析任务已启动，请查看后端控制台日志",
        "command": "python analysis/batch_job.py",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 以下为兼容性路由别名，将 /api/analysis/* 请求转发到对应 service，
# 避免前端需要同时维护两套路由前缀。
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/hourly-heatmap")
def get_hourly_heatmap_alias() -> dict:
    """热搜活跃时间热力图（/api/analysis/ 别名，内部复用 visual_service）。"""
    items = visual_service.get_hourly_heatmap()
    return {"count": len(items), "items": items}


@router.get("/burst/top")
def get_burst_top_alias(limit: int = Query(20, ge=1, le=100)) -> dict:
    """爆发趋势 TopN（/api/analysis/ 别名，内部复用 ml_analysis_service）。"""
    items = ml_analysis_service.get_burst_top(limit)
    return {"count": len(items), "items": items}


@router.get("/burst/keyword")
def get_burst_by_keyword_alias(keyword: str = Query(..., description="查询关键词")) -> dict:
    """根据关键词查询爆发趋势（/api/analysis/ 别名，内部复用 ml_analysis_service）。

    返回格式::

        {
          "keyword": "输入关键词",
          "total": 3,
          "items": [{...}, ...]
        }
    """
    cleaned = keyword.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="关键词不能为空")
    items = ml_analysis_service.get_burst_by_keyword(cleaned)
    return {
        "keyword": cleaned,
        "total": len(items),
        "items": items,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 评论情感分析接口
# ──────────────────────────────────────────────────────────────────────────────

def _mock_sentiment(keyword: str, with_trend: bool) -> dict[str, Any]:
    """当数据库无数据时生成演示用情感数据。"""
    seed = sum(ord(c) for c in keyword) if keyword else 42
    rng = random.Random(seed)
    positive = 20000 + rng.randint(0, 10000)
    negative = 6000 + rng.randint(0, 4000)
    neutral = 12000 + rng.randint(0, 6000)
    result: dict[str, Any] = {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "source": "mock",
    }
    if with_trend:
        trend = []
        today = date.today()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            trend.append({
                "date": f"{d.month}/{d.day}",
                "positive": int(positive * rng.uniform(0.8, 1.2) / 7),
                "negative": int(negative * rng.uniform(0.8, 1.2) / 7),
                "neutral": int(neutral * rng.uniform(0.8, 1.2) / 7),
            })
        result["trend"] = trend
    return result


@router.get("/sentiment")
def get_sentiment(
    keyword: str = Query("", description="热搜关键词"),
    trend: bool = Query(False, description="是否返回趋势数据"),
) -> dict:
    """返回关键词的情感分析汇总数据。

    先尝试从 hot_search_sentiment_stats 和 hot_search_sentiment_daily_stats 表
    读取真实分析结果；若表不存在或无数据则返回演示数据，**不会返回 404**。
    """
    kw = keyword.strip()
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # ---- 情感汇总 ----
            if kw:
                cur.execute(
                    """
                    SELECT
                        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive,
                        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative,
                        SUM(CASE WHEN sentiment_label = 'neutral'  THEN 1 ELSE 0 END) AS neutral
                    FROM hot_search_sentiment_stats
                    WHERE keyword LIKE %s
                    """,
                    (f"%{kw}%",),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive,
                        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative,
                        SUM(CASE WHEN sentiment_label = 'neutral'  THEN 1 ELSE 0 END) AS neutral
                    FROM hot_search_sentiment_stats
                    """
                )
            row = cur.fetchone() or {}
            pos = int(row.get("positive") or 0)
            neg = int(row.get("negative") or 0)
            neu = int(row.get("neutral") or 0)

            # 若全为 0，说明表空或关键词无匹配，回退模拟数据
            if pos + neg + neu == 0:
                conn.close()
                return _mock_sentiment(kw, trend)

            result: dict[str, Any] = {
                "positive": pos,
                "negative": neg,
                "neutral": neu,
                "source": "db",
            }

            # ---- 趋势数据 ----
            if trend:
                cur.execute(
                    """
                    SELECT stat_date,
                           positive_count AS positive,
                           negative_count AS negative,
                           neutral_count  AS neutral
                    FROM hot_search_sentiment_daily_stats
                    ORDER BY stat_date ASC
                    LIMIT 30
                    """
                )
                rows = cur.fetchall() or []
                trend_list = []
                for r in rows:
                    d = r.get("stat_date")
                    date_str = (
                        d.strftime("%m/%d") if hasattr(d, "strftime") else str(d)[-5:].replace("-", "/")
                    )
                    trend_list.append({
                        "date": date_str,
                        "positive": int(r.get("positive") or 0),
                        "negative": int(r.get("negative") or 0),
                        "neutral": int(r.get("neutral") or 0),
                    })
                result["trend"] = trend_list

        conn.close()
        return result

    except Exception:
        # 表不存在或连接失败时静默回退，不返回 404
        return _mock_sentiment(kw, trend)


# ──────────────────────────────────────────────────────────────────────────────
# 评论地理分布接口
# ──────────────────────────────────────────────────────────────────────────────

_PROVINCE_MOCK_BASE = [
    ("广东", 45823), ("北京", 38921), ("上海", 36540), ("江苏", 28934),
    ("浙江", 26712), ("山东", 21456), ("四川", 19834), ("湖北", 17623),
    ("河南", 16784), ("湖南", 15432), ("陕西", 13456), ("福建", 12987),
    ("辽宁", 11234), ("安徽", 10876), ("河北", 9876),  ("天津", 9234),
    ("重庆", 8976),  ("黑龙江", 7654), ("吉林", 6543),  ("江西", 6234),
    ("云南", 5876),  ("广西", 5432),  ("贵州", 4987),  ("山西", 4765),
    ("内蒙古", 3987), ("新疆", 3456), ("甘肃", 2987),  ("海南", 2765),
    ("宁夏", 2156),  ("青海", 1654),  ("西藏", 987),
]


def _mock_geo(keyword: str) -> list[dict]:
    """生成演示省份分布数据。"""
    seed = sum(ord(c) for c in keyword) if keyword else 0
    rng = random.Random(seed)
    return [
        {"name": name, "value": base + rng.randint(-1000, 1000)}
        for name, base in _PROVINCE_MOCK_BASE
    ]


@router.get("/geo")
def get_geo(keyword: str = Query("", description="热搜关键词")) -> list:
    """返回关键词相关评论的省份分布数据。

    当前版本直接返回基于关键词哈希生成的演示数据（省份分布），
    格式为 ``[{"name": "广东", "value": 45823}, ...]``。
    前端地图组件可直接消费此格式，**不会返回 404**。
    """
    kw = keyword.strip()
    # 尝试从 hot_search_raw 按省份字段汇总（如有该字段）
    # 当前数据表无省份字段，直接返回演示数据
    return _mock_geo(kw)


# ──────────────────────────────────────────────────────────────────────────────
# 热词词云接口
# ──────────────────────────────────────────────────────────────────────────────

_WORDCLOUD_DEFAULTS = [
    ("热搜", 3200), ("微博", 2890), ("关注", 2456), ("评论", 2134),
    ("转发", 1987), ("点赞", 1876), ("社会", 1654), ("新闻", 1543),
    ("网友", 1432), ("视频", 1321), ("直播", 1234), ("明星", 1123),
    ("话题", 987),  ("爆料", 876),  ("官方", 765),  ("回应", 698),
    ("热议", 654),  ("网络", 612),  ("群众", 587),  ("事件", 543),
    ("舆论", 512),  ("讨论", 487),  ("声音", 456),  ("关心", 432),
    ("传播", 412),  ("影响", 389),  ("引发", 367),  ("公众", 345),
    ("媒体", 323),  ("呼吁", 301),
]


def _mock_wordcloud(keyword: str) -> list[dict]:
    seed = sum(ord(c) for c in keyword) if keyword else 0
    rng = random.Random(seed)
    words = list(_WORDCLOUD_DEFAULTS)
    if keyword:
        words.insert(0, (keyword[:6], 4500))
    return [
        {"name": name, "value": base + rng.randint(-100, 100)}
        for name, base in words
    ]


@router.get("/wordcloud")
def get_wordcloud(keyword: str = Query("", description="热搜关键词")) -> list:
    """返回关键词相关的热词词云数据。

    先尝试从 hot_search_keyword_stats 中提取关键词作为词云词条；
    若无数据则返回通用演示词云，**不会返回 404**。
    格式为 ``[{"name": "热搜", "value": 3200}, ...]``。
    """
    kw = keyword.strip()
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if kw:
                cur.execute(
                    """
                    SELECT keyword AS name, max_hot_value AS value
                    FROM hot_search_keyword_stats
                    WHERE keyword LIKE %s
                    ORDER BY max_hot_value DESC
                    LIMIT 50
                    """,
                    (f"%{kw}%",),
                )
            else:
                cur.execute(
                    """
                    SELECT keyword AS name, max_hot_value AS value
                    FROM hot_search_keyword_stats
                    ORDER BY max_hot_value DESC
                    LIMIT 50
                    """
                )
            rows = cur.fetchall() or []
        conn.close()
        if rows:
            # 把 max_hot_value 等比缩放到词云合适范围（100-5000）
            max_val = max(int(r.get("value") or 1) for r in rows) or 1
            result = []
            for r in rows:
                v = int(r.get("value") or 0)
                scaled = max(100, int(v / max_val * 5000))
                result.append({"name": r["name"], "value": scaled})
            return result
        return _mock_wordcloud(kw)
    except Exception:
        return _mock_wordcloud(kw)
