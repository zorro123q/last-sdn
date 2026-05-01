"""第六期智能分析与预警增强接口。"""

from fastapi import APIRouter, Query

from services.v6_intelligence_service import v6_intelligence_service


router = APIRouter(prefix="/api/v6", tags=["v6-intelligence"])


@router.get("/lifecycle/summary")
def get_lifecycle_summary() -> dict:
    return v6_intelligence_service.get_lifecycle_summary()


@router.get("/lifecycle/list")
def get_lifecycle_list(
    stage: str = Query("", description="生命周期阶段"),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    items = v6_intelligence_service.get_lifecycle_list(stage=stage.strip(), limit=limit)
    return {"count": len(items), "items": items}


@router.post("/lifecycle/run")
def run_lifecycle_job() -> dict:
    return v6_intelligence_service.run_lifecycle_job()


@router.get("/alerts/summary")
def get_alert_summary() -> dict:
    return v6_intelligence_service.get_alert_summary()


@router.get("/alerts/list")
def get_alert_list(
    level: str = Query("", description="预警等级"),
    type: str = Query("", description="预警类型"),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    items = v6_intelligence_service.get_alert_list(
        level=level.strip(),
        alert_type=type.strip(),
        limit=limit,
    )
    return {"count": len(items), "items": items}


@router.post("/alerts/run")
def run_alert_job() -> dict:
    return v6_intelligence_service.run_alert_job()


@router.post("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int) -> dict:
    return v6_intelligence_service.mark_alert_read(alert_id)


@router.get("/reports/latest")
def get_latest_report() -> dict:
    return v6_intelligence_service.get_latest_report()


@router.get("/reports/list")
def get_report_list() -> dict:
    items = v6_intelligence_service.get_report_list()
    return {"count": len(items), "items": items}


@router.post("/reports/run")
def run_ai_report_job() -> dict:
    return v6_intelligence_service.run_ai_report_job()


@router.get("/reports/{report_id}")
def get_report_detail(report_id: int) -> dict:
    return v6_intelligence_service.get_report_detail(report_id)


@router.get("/jobs")
def get_jobs(limit: int = Query(100, ge=1, le=300)) -> dict:
    items = v6_intelligence_service.get_jobs(limit=limit)
    return {"count": len(items), "items": items}


@router.get("/jobs/{job_id}")
def get_job_detail(job_id: int) -> dict:
    return v6_intelligence_service.get_job_detail(job_id)


@router.post("/jobs/run-all")
def run_all_jobs() -> dict:
    return v6_intelligence_service.run_all_jobs()


@router.get("/health/summary")
def get_health_summary() -> dict:
    return v6_intelligence_service.get_health_summary()


@router.post("/health/run")
def run_health_check() -> dict:
    return v6_intelligence_service.run_health_check()
