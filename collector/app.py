"""微博热搜定时采集入口。"""

import time
from datetime import datetime

from api_client import WeiboApiClient
from config import settings
from db_writer import MySQLWriter


def collect_once() -> int:
    """执行一次采集和入库。"""
    client = WeiboApiClient()
    writer = MySQLWriter()

    records = client.fetch_hot_search()
    saved_count = writer.save_records(records)
    print(
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 本次采集完成，"
        f"获取 {len(records)} 条，写入 {saved_count} 条。"
    )
    return saved_count


def main() -> None:
    """按配置执行单次或循环采集。"""
    print("微博热搜采集程序启动。")
    print(f"采集间隔：{settings.collect_interval_seconds} 秒。")
    print(f"请求地址：{settings.weibo_api_url}")

    while True:
        try:
            collect_once()
        except Exception as exc:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 采集失败：{exc}")

        if settings.collect_run_once:
            print("当前为单次执行模式，程序结束。")
            break

        time.sleep(settings.collect_interval_seconds)


if __name__ == "__main__":
    main()
