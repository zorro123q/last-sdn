# -*- coding: utf-8 -*-
"""
backend/routes/sentiment_semantic.py - 第五期情感与语义分析 API 路由

提供情感分析和语义聚类的 RESTful API 接口。
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, FileResponse

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.sentiment_semantic_service import (
    get_sentiment_summary,
    get_sentiment_daily,
    get_sentiment_top,
    search_sentiment,
    run_sentiment_job,
    get_semantic_clusters,
    get_semantic_cluster_summary,
    run_semantic_cluster_job,
    export_enhanced_report_csv,
    export_enhanced_report_excel,
    get_report_debug_counts,
)

# 创建路由
router = APIRouter()


# ============================================================
# 情感分析接口
# ============================================================

@router.get("/api/sentiment/summary")
async def api_get_sentiment_summary():
    """
    获取情感分析总体概览。

    Returns:
        dict: 情感概览数据，包含平均情感分数、正向/中性/负向数量、总数量
    """
    try:
        result = get_sentiment_summary()
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/sentiment/daily")
async def api_get_sentiment_daily():
    """
    获取每日情感统计数据。

    Returns:
        list: 每日情感统计数据列表，按日期升序排序
    """
    try:
        result = get_sentiment_daily()
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/sentiment/top")
async def api_get_sentiment_top(
    limit: int = Query(20, ge=1, le=100, description="返回条数限制"),
    label: Optional[str] = Query(None, description="情感标签过滤：positive/neutral/negative")
):
    """
    获取情感分析 Top 数据。

    Args:
        limit: 返回条数，范围 1-100，默认 20
        label: 可选，按情感标签过滤

    Returns:
        list: 情感分析结果列表
    """
    try:
        result = get_sentiment_top(limit=limit, label=label)
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/sentiment/search")
async def api_search_sentiment(
    keyword: str = Query(..., description="搜索关键词")
):
    """
    根据关键词模糊查询情感分析结果。

    Args:
        keyword: 搜索关键词

    Returns:
        list: 匹配的情感分析结果列表
    """
    try:
        result = search_sentiment(keyword=keyword)
        return result
    except Exception as e:
        return {"error": str(e)}


@router.post("/api/sentiment/run")
async def api_run_sentiment_job():
    """
    手动触发情感分析任务。

    在后端后台运行 python sentiment/sentiment_job.py

    Returns:
        dict: 执行结果
    """
    try:
        result = run_sentiment_job()
        return result
    except Exception as e:
        return {"success": False, "message": str(e), "returncode": -1}


# ============================================================
# 语义聚类接口
# ============================================================

@router.get("/api/semantic/clusters")
async def api_get_semantic_clusters():
    """
    获取语义聚类结果。

    Returns:
        list: 语义聚类结果列表，按聚类ID和热度降序排序
    """
    try:
        result = get_semantic_clusters()
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/semantic/clusters/summary")
async def api_get_semantic_cluster_summary():
    """
    获取语义聚类主题分布统计。

    Returns:
        list: 按主题类别分组的统计数据
    """
    try:
        result = get_semantic_cluster_summary()
        return result
    except Exception as e:
        return {"error": str(e)}


@router.post("/api/semantic/run")
async def api_run_semantic_cluster_job():
    """
    手动触发语义聚类任务。

    在后端后台运行 python semantic/semantic_cluster_job.py

    Returns:
        dict: 执行结果
    """
    try:
        result = run_semantic_cluster_job()
        return result
    except Exception as e:
        return {"success": False, "message": str(e), "returncode": -1}


# ============================================================
# 报告调试接口
# ============================================================

@router.get("/api/report/debug-counts")
async def api_get_report_debug_counts():
    """获取增强报告依赖的关键数据表记录数。"""
    return get_report_debug_counts()


# ============================================================
# 报告导出接口
# ============================================================

@router.get("/api/export/enhanced_report.csv")
async def api_export_enhanced_report_csv():
    """
    导出增强版综合报告 CSV。

    包含：情感分析汇总、每日情绪统计、语义聚类结果、
    第四期爆发趋势识别结果、第三期关键词统计结果、当前热搜榜

    Returns:
        StreamingResponse: CSV 文件流
    """
    try:
        csv_content, filename = export_enhanced_report_csv()

        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
            }
        )
    except Exception as e:
        return {"error": str(e)}


@router.get("/api/export/enhanced_report.xlsx")
async def api_export_enhanced_report_excel():
    """
    导出增强版综合报告 Excel（多 Sheet）。

    Sheet：情感汇总、每日情绪、情感明细、语义聚类、
           语义主题分布、爆发趋势、关键词统计、当前热搜

    Returns:
        FileResponse: Excel 文件
    """
    try:
        file_path, filename = export_enhanced_report_excel()

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return {"error": str(e)}
