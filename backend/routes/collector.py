"""Collector task trigger routes."""

from pathlib import Path
import os
import subprocess
import sys

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/api/collector", tags=["collector"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@router.post("/run")
def run_collector_once():
    """Start collector/app.py once in the background."""
    try:
        script_path = PROJECT_ROOT / "collector" / "app.py"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="采集脚本 collector/app.py 不存在")

        env = os.environ.copy()
        env["COLLECT_RUN_ONCE"] = "true"

        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            env=env,
        )

        return {
            "success": True,
            "message": "微博热搜采集任务已启动，请稍后刷新数据",
            "command": "python collector/app.py",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动采集任务失败：{e}") from e
