"""PySpark 分析结果接口。"""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Query

from services.analysis_service import analysis_service


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
