"""第四期机器学习分析接口。"""

from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from services.ml_analysis_service import ml_analysis_service


router = APIRouter(prefix="/api/ml", tags=["ml-analysis"])
export_router = APIRouter(prefix="/api/export", tags=["ml-export"])


@router.get("/burst/top")
def get_burst_top(limit: int = Query(20, ge=1, le=100)) -> dict:
    """返回爆发趋势识别 TopN。"""
    items = ml_analysis_service.get_burst_top(limit)
    return {"count": len(items), "items": items}


@router.get("/burst/search")
def search_burst_keyword(keyword: str = Query(..., description="查询关键词")) -> dict:
    """根据关键词查询爆发趋势识别结果。"""
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="关键词不能为空")
    items = ml_analysis_service.get_burst_by_keyword(keyword)
    return {"count": len(items), "items": items}


@router.get("/topics")
def get_topic_clusters() -> dict:
    """返回主题聚类明细。"""
    items = ml_analysis_service.get_topic_clusters()
    return {"count": len(items), "items": items}


@router.get("/topics/summary")
def get_cluster_summary() -> dict:
    """返回主题聚类分布统计。"""
    items = ml_analysis_service.get_cluster_summary()
    return {"count": len(items), "items": items}


@router.post("/burst/run")
def run_burst_prediction_job() -> dict:
    """手动触发机器学习爆发趋势识别任务。"""
    return ml_analysis_service.run_burst_prediction_job()


@router.post("/topics/run")
def run_topic_cluster_job() -> dict:
    """手动触发主题聚类任务。"""
    return ml_analysis_service.run_topic_cluster_job()


@export_router.get("/ml_report.csv")
def export_ml_report_csv() -> StreamingResponse:
    """导出机器学习分析 CSV 报告。"""
    content = ml_analysis_service.export_ml_report_csv()
    filename = quote("微博热搜机器学习分析报告.csv")
    return StreamingResponse(
        BytesIO(content),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@export_router.get("/ml_report.xlsx")
def export_ml_report_excel() -> StreamingResponse:
    """导出机器学习分析 Excel 报告。"""
    content = ml_analysis_service.export_ml_report_excel()
    filename = quote("微博热搜机器学习分析报告.xlsx")
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
