# -*- coding: utf-8 -*-
"""
sentiment/sentiment_analyzer.py - 微博热搜标题情感分析器

使用 SnowNLP 对中文热搜标题进行情感分析。
计算情感分数（0-1），生成情感标签（positive/neutral/negative）。
"""

import sys
from pathlib import Path

import pandas as pd

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from sentiment.config import sentiment_config

# 尝试导入 SnowNLP
try:
    from snownlp import SnowNLP

    SNOWNLP_AVAILABLE = True
except ImportError:
    SNOWNLP_AVAILABLE = False
    print("[sentiment] 警告：SnowNLP 未安装，情感分析将使用默认中性分数")


def analyze_sentiment(raw_df):
    """
    对热搜标题进行情感分析。

    使用 SnowNLP 对每条 title 计算情感分数（0-1）。
    - score >= positive_threshold: positive（正向）
    - score <= negative_threshold: negative（负向）
    - 其他：neutral（中性）

    Args:
        raw_df: pandas.DataFrame，包含 title, rank_num, hot_value, fetch_time 等字段

    Returns:
        pandas.DataFrame: 包含情感分析结果的 DataFrame
            新增字段：keyword, sentiment_score, sentiment_label, sentiment_label_cn, stat_date, method_name
    """
    if raw_df.empty:
        print("[sentiment] 情感分析完成，结果数量：0")
        return pd.DataFrame()

    # 获取配置
    positive_threshold = sentiment_config["positive_threshold"]
    negative_threshold = sentiment_config["negative_threshold"]
    method_name = sentiment_config["method"]

    results = []

    for _, row in raw_df.iterrows():
        title = row.get("title", "")
        rank_num = row.get("rank_num", 0)
        hot_value = row.get("hot_value", 0)
        fetch_time = row.get("fetch_time", None)

        # 空标题处理
        if not title or not isinstance(title, str):
            sentiment_score = 0.5
            sentiment_label = "neutral"
            sentiment_label_cn = "中性"
        else:
            try:
                if SNOWNLP_AVAILABLE:
                    # 使用 SnowNLP 进行情感分析
                    s = SnowNLP(title)
                    sentiment_score = s.sentiments  # 0-1 之间的分数
                else:
                    # SnowNLP 不可用时，使用默认中性分数
                    sentiment_score = 0.5
            except Exception as e:
                # 分析失败时，使用默认中性分数
                sentiment_score = 0.5

            # 根据阈值确定情感标签
            if sentiment_score >= positive_threshold:
                sentiment_label = "positive"
                sentiment_label_cn = "正向"
            elif sentiment_score <= negative_threshold:
                sentiment_label = "negative"
                sentiment_label_cn = "负向"
            else:
                sentiment_label = "neutral"
                sentiment_label_cn = "中性"

        # 生成结果记录
        result = {
            "keyword": title,  # 使用标题作为关键词
            "sentiment_score": round(sentiment_score, 4),
            "sentiment_label": sentiment_label,
            "sentiment_label_cn": sentiment_label_cn,
            "rank_num": int(rank_num) if pd.notna(rank_num) else None,
            "hot_value": int(hot_value) if pd.notna(hot_value) else 0,
            "fetch_time": fetch_time,
            "stat_date": fetch_time.date() if fetch_time else None,
            "method_name": method_name,
        }
        results.append(result)

    # 转换为 DataFrame
    result_df = pd.DataFrame(results)

    print(f"[sentiment] 情感分析完成，结果数量：{len(result_df)}")
    return result_df


if __name__ == "__main__":
    # 测试情感分析
    import pandas as pd

    # 模拟数据
    test_data = pd.DataFrame({
        "title": [
            "中国成功发射火星探测器",
            "警方通报某地发生重大事故",
            "明天天气晴朗，适合出行",
            "某明星演唱会门票秒空",
            "考试不及格很伤心",
            "公司发布新产品获得好评",
        ],
        "rank_num": [1, 2, 3, 4, 5, 6],
        "hot_value": [1000000, 800000, 600000, 500000, 400000, 300000],
        "fetch_time": pd.date_range("2024-01-01", periods=6, freq="h"),
    })

    results = analyze_sentiment(test_data)
    print(results)
