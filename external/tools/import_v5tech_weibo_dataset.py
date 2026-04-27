# -*- coding: utf-8 -*-
"""
导入 v5tech/weibo-trending-hot-search 微博热搜历史数据。

数据来源：
https://github.com/v5tech/weibo-trending-hot-search

数据格式：
raw/YYYYMM/YYYY-MM-DD.json

示例：
{
  "热搜标题": {
    "url": "https://s.weibo.com/weibo?q=...",
    "hot": "976671"
  }
}

导入逻辑：
1. 先写入 hot_search_v5tech_history。
2. 可选使用 --sync-raw 同步写入你项目已有的 hot_search_raw。
3. source 固定为 v5tech_dataset，方便和实时采集数据区分。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass
class Settings:
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_charset: str


def get_settings() -> Settings:
    return Settings(
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "root"),
        mysql_password=os.getenv("MYSQL_PASSWORD", "123456"),
        mysql_database=os.getenv("MYSQL_DATABASE", "weibo_hot"),
        mysql_charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
    )


def get_connection():
    settings = get_settings()
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset=settings.mysql_charset,
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入 v5tech 微博热搜历史数据")
    parser.add_argument(
        "--dataset-dir",
        required=True,
        help="v5tech/weibo-trending-hot-search 本地目录，例如 external/v5tech-weibo-trending-hot-search",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="开始日期，格式 YYYY-MM-DD，例如 2024-01-01",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="结束日期，格式 YYYY-MM-DD，例如 2024-12-31",
    )
    parser.add_argument(
        "--sync-raw",
        action="store_true",
        help="是否同步写入项目已有 hot_search_raw 表",
    )
    parser.add_argument(
        "--clear-range",
        action="store_true",
        help="导入前是否清理指定日期范围内的 v5tech_dataset 数据",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="批量写入大小，默认 1000",
    )
    return parser.parse_args()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_date_from_filename(filename: str) -> date | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2})\.json$", filename)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d").date()


def clean_title(value: Any) -> str:
    title = str(value or "").strip()
    title = re.sub(r"\s+", " ", title)
    return title[:255]


def clean_url(value: Any) -> str:
    url = str(value or "").strip()
    return url[:1000]


def parse_hot_value(value: Any) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def iter_json_files(dataset_dir: Path, start: date | None, end: date | None) -> list[Path]:
    raw_dir = dataset_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"未找到 raw 目录：{raw_dir}")

    files = sorted(raw_dir.glob("*/*.json"))
    result: list[Path] = []

    for file_path in files:
        file_date = parse_date_from_filename(file_path.name)
        if file_date is None:
            continue
        if start and file_date < start:
            continue
        if end and file_date > end:
            continue
        result.append(file_path)

    return result


def load_records_from_json(file_path: Path) -> list[dict[str, Any]]:
    dataset_date = parse_date_from_filename(file_path.name)
    if dataset_date is None:
        return []

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        data = json.loads(file_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"[import] JSON 解析失败：{file_path}，原因：{exc}")
        return []

    if not isinstance(data, dict):
        print(f"[import] 文件不是 dict 结构，跳过：{file_path}")
        return []

    rows: list[dict[str, Any]] = []

    for title, item in data.items():
        if not isinstance(item, dict):
            continue

        cleaned_title = clean_title(title)
        if not cleaned_title:
            continue

        hot_value = parse_hot_value(item.get("hot"))
        url = clean_url(item.get("url"))

        rows.append(
            {
                "title": cleaned_title,
                "url": url,
                "hot_value": hot_value,
                "dataset_date": dataset_date,
                "fetch_time": datetime.combine(dataset_date, time(hour=12, minute=0, second=0)),
                "source": "v5tech_dataset",
            }
        )

    # 按 hot_value 降序重新生成 rank_num，避免依赖 JSON 顺序
    rows.sort(key=lambda x: x["hot_value"], reverse=True)

    for index, row in enumerate(rows, start=1):
        row["rank_num"] = index

    return rows


def clear_existing_data(connection, start: date | None, end: date | None, sync_raw: bool) -> None:
    if not start or not end:
        raise ValueError("使用 --clear-range 时必须同时提供 --start-date 和 --end-date")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM hot_search_v5tech_history
            WHERE source = 'v5tech_dataset'
              AND dataset_date BETWEEN %s AND %s
            """,
            (start, end),
        )

        if sync_raw:
            cursor.execute(
                """
                DELETE FROM hot_search_raw
                WHERE source = 'v5tech_dataset'
                  AND DATE(fetch_time) BETWEEN %s AND %s
                """,
                (start, end),
            )

    connection.commit()
    print(f"[import] 已清理 {start} 至 {end} 的旧数据")


def insert_v5tech_history(connection, records: list[dict[str, Any]]) -> int:
    if not records:
        return 0

    sql = """
    INSERT IGNORE INTO hot_search_v5tech_history
    (
        title,
        url,
        rank_num,
        hot_value,
        dataset_date,
        fetch_time,
        source
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = [
        (
            row["title"],
            row["url"],
            row["rank_num"],
            row["hot_value"],
            row["dataset_date"],
            row["fetch_time"],
            row["source"],
        )
        for row in records
    ]

    with connection.cursor() as cursor:
        affected = cursor.executemany(sql, values)

    return affected


def insert_hot_search_raw(connection, records: list[dict[str, Any]]) -> int:
    """
    同步写入项目已有 hot_search_raw 表。

    注意：
    hot_search_raw 默认没有唯一约束，因此使用 NOT EXISTS 做去重。
    """
    if not records:
        return 0

    sql = """
    INSERT INTO hot_search_raw
    (
        title,
        rank_num,
        hot_value,
        source,
        fetch_time
    )
    SELECT %s, %s, %s, %s, %s
    FROM DUAL
    WHERE NOT EXISTS (
        SELECT 1
        FROM hot_search_raw
        WHERE title = %s
          AND source = %s
          AND fetch_time = %s
        LIMIT 1
    )
    """

    values = [
        (
            row["title"],
            row["rank_num"],
            row["hot_value"],
            row["source"],
            row["fetch_time"],
            row["title"],
            row["source"],
            row["fetch_time"],
        )
        for row in records
    ]

    with connection.cursor() as cursor:
        affected = cursor.executemany(sql, values)

    return affected


def import_dataset(
    dataset_dir: Path,
    start: date | None,
    end: date | None,
    sync_raw: bool,
    clear_range: bool,
    batch_size: int,
) -> None:
    files = iter_json_files(dataset_dir, start, end)

    if not files:
        print("[import] 没有找到符合日期范围的 JSON 文件")
        return

    print(f"[import] 待导入文件数：{len(files)}")
    print(f"[import] 日期范围：{start or '不限'} 至 {end or '不限'}")
    print(f"[import] 是否同步 hot_search_raw：{sync_raw}")

    connection = get_connection()

    total_parsed = 0
    total_history_inserted = 0
    total_raw_inserted = 0
    batch: list[dict[str, Any]] = []

    try:
        if clear_range:
            clear_existing_data(connection, start, end, sync_raw)

        for index, file_path in enumerate(files, start=1):
            records = load_records_from_json(file_path)
            batch.extend(records)
            total_parsed += len(records)

            print(f"[import] [{index}/{len(files)}] {file_path.name} 解析 {len(records)} 条")

            if len(batch) >= batch_size:
                history_count = insert_v5tech_history(connection, batch)
                raw_count = insert_hot_search_raw(connection, batch) if sync_raw else 0
                connection.commit()

                total_history_inserted += history_count
                total_raw_inserted += raw_count

                print(
                    f"[import] 批量写入完成：history={history_count}, "
                    f"raw={raw_count}, parsed={total_parsed}"
                )
                batch = []

        if batch:
            history_count = insert_v5tech_history(connection, batch)
            raw_count = insert_hot_search_raw(connection, batch) if sync_raw else 0
            connection.commit()

            total_history_inserted += history_count
            total_raw_inserted += raw_count

            print(
                f"[import] 最后一批写入完成：history={history_count}, "
                f"raw={raw_count}, parsed={total_parsed}"
            )

    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print("=" * 70)
    print("[import] 导入完成")
    print(f"[import] 解析总记录数：{total_parsed}")
    print(f"[import] 写入 hot_search_v5tech_history：{total_history_inserted}")
    print(f"[import] 写入 hot_search_raw：{total_raw_inserted}")
    print("=" * 70)


def main() -> None:
    args = parse_args()

    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.is_absolute():
        dataset_dir = ROOT_DIR / dataset_dir

    if not dataset_dir.exists():
        raise FileNotFoundError(f"数据集目录不存在：{dataset_dir}")

    start = parse_date(args.start_date)
    end = parse_date(args.end_date)

    if start and end and start > end:
        raise ValueError("start-date 不能晚于 end-date")

    import_dataset(
        dataset_dir=dataset_dir,
        start=start,
        end=end,
        sync_raw=args.sync_raw,
        clear_range=args.clear_range,
        batch_size=max(args.batch_size, 1),
    )


if __name__ == "__main__":
    main()