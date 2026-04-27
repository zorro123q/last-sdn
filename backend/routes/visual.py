"""可视化增强接口。"""

from fastapi import APIRouter

from services.visual_service import visual_service


router = APIRouter(prefix="/api/visual", tags=["visual"])


@router.get("/hourly-heatmap")
def get_hourly_heatmap() -> dict:
    """返回按日期和小时分组的热搜采集热力图数据。"""
    items = visual_service.get_hourly_heatmap()
    return {"count": len(items), "items": items}


@router.get("/rank-movers")
def get_rank_movers() -> dict:
    """返回最新两批热搜之间的排名变化榜。"""
    result = visual_service.get_rank_movers()
    return {
        "up_count": len(result["up"]),
        "down_count": len(result["down"]),
        **result,
    }


@router.get("/insights")
def get_insights() -> dict:
    """返回系统自动生成的数据洞察。"""
    return visual_service.get_insights()
