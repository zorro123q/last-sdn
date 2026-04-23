"""微博热搜 API 客户端。"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

from config import CollectorConfig


TITLE_KEYS: Sequence[str] = ("title", "word", "note", "desc", "query", "label_name")
HOT_KEYS: Sequence[str] = ("hot_value", "hot", "raw_hot", "num", "score")
RANK_KEYS: Sequence[str] = ("rank", "realpos", "position", "note_id")
LIST_HINT_KEYS: Sequence[str] = ("data", "list", "items", "realtime", "band_list", "word_list", "hotgov")


def _pick_first_value(source: Dict[str, Any], keys: Sequence[str]) -> Any:
    """按候选字段顺序取值。"""

    for key in keys:
        value = source.get(key)
        if value not in (None, "", []):
            return value
    return None


def _parse_hot_value(raw_value: Any) -> int:
    """兼容处理整数、字符串以及带中文单位的热度值。"""

    if raw_value is None:
        return 0

    if isinstance(raw_value, (int, float)):
        return int(raw_value)

    if isinstance(raw_value, dict):
        nested_value = _pick_first_value(raw_value, HOT_KEYS)
        return _parse_hot_value(nested_value)

    text = str(raw_value).strip().replace(",", "")
    if not text:
        return 0

    multiplier = 1
    if "亿" in text:
        multiplier = 100_000_000
    elif "万" in text:
        multiplier = 10_000

    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return 0

    return int(float(match.group(1)) * multiplier)


def _looks_like_hot_item(item: Any) -> bool:
    """判断一条字典数据是否像热搜条目。"""

    return isinstance(item, dict) and any(key in item for key in TITLE_KEYS)


def _collect_candidate_lists(node: Any, candidates: List[Tuple[int, List[Dict[str, Any]]]]) -> None:
    """递归扫描响应体，找到最可能的热搜列表。"""

    if isinstance(node, list):
        dict_items = [item for item in node if isinstance(item, dict)]
        if dict_items:
            score = sum(2 for item in dict_items[:10] if _looks_like_hot_item(item))
            candidates.append((score, dict_items))
        for item in node:
            _collect_candidate_lists(item, candidates)
        return

    if isinstance(node, dict):
        for key in LIST_HINT_KEYS:
            value = node.get(key)
            if isinstance(value, list):
                dict_items = [item for item in value if isinstance(item, dict)]
                score = 5 + sum(2 for item in dict_items[:10] if _looks_like_hot_item(item))
                candidates.append((score, dict_items))

        for value in node.values():
            _collect_candidate_lists(value, candidates)


def _find_hot_list(payload: Any) -> List[Dict[str, Any]]:
    """从不稳定的响应结构中提取热搜数组。"""

    candidates: List[Tuple[int, List[Dict[str, Any]]]] = []
    _collect_candidate_lists(payload, candidates)
    candidates = [candidate for candidate in candidates if candidate[1]]

    if not candidates:
        return []

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _normalize_item(raw_item: Dict[str, Any], index: int, fetch_time: str, source_name: str) -> Optional[Dict[str, Any]]:
    """把原始条目整理成统一结构。"""

    title = _pick_first_value(raw_item, TITLE_KEYS)
    if title is None:
        return None

    rank_value = _pick_first_value(raw_item, RANK_KEYS)
    hot_value = _pick_first_value(raw_item, HOT_KEYS)

    return {
        "rank": int(rank_value) if str(rank_value).isdigit() else index,
        "title": str(title).strip(),
        "hot_value": _parse_hot_value(hot_value),
        "source": source_name,
        "fetch_time": fetch_time,
    }


def fetch_hot_searches(config: CollectorConfig) -> Dict[str, Any]:
    """请求微博热搜接口并返回标准化结果。"""

    headers = {
        "User-Agent": config.user_agent,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://s.weibo.com/top/summary",
    }

    response = requests.get(config.api_url, headers=headers, timeout=config.request_timeout)
    response.raise_for_status()

    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = json.loads(response.text)

    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_items = _find_hot_list(payload)
    items: List[Dict[str, Any]] = []

    for index, raw_item in enumerate(raw_items, start=1):
        normalized_item = _normalize_item(raw_item, index, fetch_time, config.source_name)
        if normalized_item and normalized_item["title"]:
            items.append(normalized_item)

    if not items:
        raise ValueError("未从微博接口响应中解析出热搜条目。")

    return {
        "fetch_time": fetch_time,
        "items": items,
    }
