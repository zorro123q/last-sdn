"""关键词趋势接口。"""

from fastapi import APIRouter, Depends, Query

from config import BackendConfig, get_settings
from services.mysql_service import get_keyword_trend


router = APIRouter(prefix="/trend", tags=["trend"])


@router.get("")
def keyword_trend(
    keyword: str = Query(..., min_length=1, description="要查询趋势的关键词"),
    config: BackendConfig = Depends(get_settings),
):
    """按关键词查询趋势数据。"""

    return get_keyword_trend(keyword, config)
