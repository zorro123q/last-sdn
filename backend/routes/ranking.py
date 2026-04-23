"""当前排行榜接口。"""

from fastapi import APIRouter, Depends

from config import BackendConfig, get_settings
from services.redis_service import get_current_ranking


router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("/current")
def current_ranking(config: BackendConfig = Depends(get_settings)):
    """返回 Redis 中的当前热搜榜。"""

    return get_current_ranking(config)
