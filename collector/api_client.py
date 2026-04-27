"""微博热搜接口请求与结果解析。"""

import re
import time
from datetime import datetime
from typing import Any

import requests

from config import settings


class WeiboApiClient:
    """微博热搜接口客户端。"""

    def __init__(self) -> None:
        # 统一维护请求头，尽量降低因缺少头部导致的请求失败。
        self.headers = {
            "User-Agent": settings.collect_user_agent,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://weibo.com/hot/search",
        }
        if settings.weibo_cookie:
            self.headers["Cookie"] = settings.weibo_cookie

    def fetch_hot_search(self) -> list[dict[str, Any]]:
        """拉取热搜接口并转换为统一字段。"""
        payload = self._request_payload()
        fetch_time = datetime.now()
        items = self._normalize_records(payload, fetch_time)

        if not items:
            print("[weibo] 接口请求成功，但未解析到热搜数据，请检查接口返回结构或 Cookie。")
            raise ValueError("当前未解析到微博热搜数据，请稍后重试或配置 WEIBO_COOKIE。")

        return items

    def _request_payload(self) -> Any:
        """请求微博接口；网络不稳定时按配置重试，最终仍失败则抛出最后一次异常。"""
        last_error: Exception | None = None
        retry_times = settings.weibo_api_retry_times

        for attempt in range(1, retry_times + 2):
            try:
                response = requests.get(
                    settings.weibo_api_url,
                    headers=self.headers,
                    timeout=settings.weibo_api_timeout,
                )
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as exc:
                    print("[weibo] 微博接口返回异常 JSON，请检查接口访问状态或 Cookie。")
                    raise ValueError("微博接口返回异常 JSON，暂时无法解析热搜数据。") from exc
            except (
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError,
            ) as exc:
                last_error = exc
                if attempt <= retry_times:
                    print(
                        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                        f"微博接口请求失败，第 {attempt}/{retry_times} 次重试，原因：{exc}"
                    )
                    time.sleep(settings.weibo_api_retry_delay_seconds)
                else:
                    print(
                        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                        f"微博接口请求失败，{retry_times} 次重试均失败，原因：{exc}"
                    )

        if last_error is not None:
            raise last_error

        raise RuntimeError("微博接口请求失败，请检查网络和接口配置。")

    def _normalize_records(
        self, payload: dict[str, Any], fetch_time: datetime
    ) -> list[dict[str, Any]]:
        """兼容不同返回结构，统一输出数据库需要的字段。"""
        records: list[dict[str, Any]] = []
        candidates = self._extract_candidate_list(payload)

        for index, item in enumerate(candidates, start=1):
            if not isinstance(item, dict):
                continue
            if item.get("is_ad") or item.get("ad_info"):
                continue

            title = self._pick_first_text(
                item, ["title", "word", "note", "desc", "label_name"]
            )
            if not title:
                continue

            rank_num = self._parse_rank_num(item, index)
            hot_value = self._parse_hot_value(item)
            source = self._pick_first_text(item, ["source"]) or settings.weibo_api_source

            records.append(
                {
                    "title": title.strip(),
                    "rank_num": rank_num,
                    "hot_value": hot_value,
                    "source": source,
                    "fetch_time": fetch_time,
                }
            )

        return records

    def _extract_candidate_list(self, payload: Any) -> list[dict[str, Any]]:
        """优先匹配常见字段结构，找不到时再递归寻找候选列表。"""
        if not isinstance(payload, dict):
            return []

        data = payload.get("data")
        candidate_lists = [
            payload.get("list"),
            data if isinstance(data, list) else None,
            data.get("list") if isinstance(data, dict) else None,
            data.get("realtime") if isinstance(data, dict) else None,
            data.get("band_list") if isinstance(data, dict) else None,
            data.get("cards") if isinstance(data, dict) else None,
        ]

        for candidate in candidate_lists:
            if self._is_hot_list(candidate):
                return candidate

        return self._find_hot_list(payload)

    def _find_hot_list(self, node: Any) -> list[dict[str, Any]]:
        """在未知结构中递归寻找最像热搜列表的节点。"""
        if self._is_hot_list(node):
            return node

        if isinstance(node, dict):
            for value in node.values():
                result = self._find_hot_list(value)
                if result:
                    return result

        if isinstance(node, list):
            for value in node:
                result = self._find_hot_list(value)
                if result:
                    return result

        return []

    def _is_hot_list(self, value: Any) -> bool:
        """判断一个节点是否像热搜列表。"""
        if not isinstance(value, list) or not value:
            return False
        if not all(isinstance(item, dict) for item in value):
            return False

        for item in value:
            if self._pick_first_text(item, ["title", "word", "note", "desc"]):
                return True
        return False

    def _pick_first_text(self, item: dict[str, Any], keys: list[str]) -> str:
        """按顺序取第一个非空文本字段。"""
        for key in keys:
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    def _parse_rank_num(self, item: dict[str, Any], fallback_rank: int) -> int:
        """解析榜单排名，不存在时使用当前顺序作为默认值。"""
        for key in ["rank_num", "rank", "realpos", "position", "display_rank"]:
            value = self._to_int(item.get(key))
            if value is not None:
                return value

        num_value = self._to_int(item.get("num"))
        if num_value is not None and 1 <= num_value <= 200:
            return num_value

        return fallback_rank

    def _parse_hot_value(self, item: dict[str, Any]) -> int:
        """解析热度值，兼容 hot、hot_value、raw_hot 等字段。"""
        for key in ["hot_value", "hot", "raw_hot", "score", "num", "number"]:
            value = self._to_int(item.get(key))
            if value is not None:
                return value
        return 0

    def _to_int(self, value: Any) -> int | None:
        """将可能带中文或符号的值转换为整数。"""
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)

        digits = re.sub(r"[^\d]", "", str(value))
        if not digits:
            return None
        return int(digits)
