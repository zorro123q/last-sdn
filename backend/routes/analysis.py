"""PySpark 分析结果接口。"""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

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
