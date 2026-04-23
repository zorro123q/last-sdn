"""概览接口。"""

from fastapi import APIRouter, Depends

from config import BackendConfig, get_settings
from services.mysql_service import get_summary


router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("")
def summary(config: BackendConfig = Depends(get_settings)):
    """返回概览统计信息。"""

    return get_summary(config)
