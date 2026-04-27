# -*- coding: utf-8 -*-
"""
semantic/embedding_cluster.py - 语义嵌入与聚类模块

支持两种嵌入方法：
1. sentence-transformers：使用预训练多语言模型生成句向量（优先）
2. TF-IDF fallback：当 sentence-transformers 不可用时使用

使用 KMeans 进行聚类，为每个聚类生成主题名称。
"""

import sys
from pathlib import Path
from collections import Counter

import pandas as pd

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from semantic.config import semantic_config

# 尝试导入必要的库
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[semantic] 警告：scikit-learn 未安装")

try:
    import jieba

    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("[semantic] 警告：jieba 未安装，中文分词将不可用")

# sentence-transformers 相关变量
SENTENCE_TRANSFORMERS_AVAILABLE = False
sentence_transformer_model = None

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("[semantic] sentence-transformers 已安装，可使用语义向量聚类")
except ImportError:
    print("[semantic] 警告：sentence-transformers 未安装，将使用 TF-IDF fallback")


def load_sentence_transformer_model():
    """
    加载 sentence-transformers 模型。

    优先使用本地模型路径，如果为空则下载模型。

    Returns:
        SentenceTransformer or None: 模型实例，加载失败返回 None
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None

    try:
        config = semantic_config
        model_name = config["model_name"]
        local_path = config.get("local_model_path", "")

        if local_path and Path(local_path).exists():
            print(f"[semantic] 从本地路径加载模型：{local_path}")
            model = SentenceTransformer(local_path)
        else:
            print(f"[semantic] 加载预训练模型：{model_name}")
            model = SentenceTransformer(model_name)

        return model
    except Exception as e:
        print(f"[semantic] 模型加载失败：{e}")
        return None


def get_cluster_name(title):
    """
    根据标题关键词确定聚类主题名称。

    规则：
    - 包含"明星、演唱会、电影、综艺、演员、导演、票房"等 -> 娱乐热点
    - 包含"高考、大学、学校、考试、考研、教育、学生"等 -> 教育考试
    - 包含"股票、公司、发布、科技、AI、手机、汽车、芯片"等 -> 科技财经
    - 包含"比赛、冠军、足球、篮球、奥运、运动员"等 -> 体育赛事
    - 包含"警方、事故、回应、通报、医院、法院、火灾"等 -> 社会事件
    - 包含"降雨、台风、地震、天气、暴雨"等 -> 自然天气
    - 否则 -> 综合热点

    Args:
        title: 热搜标题

    Returns:
        str: 主题名称
    """
    if not title:
        return "综合热点"

    # 娱乐热点
    entertainment_keywords = ["明星", "演唱会", "电影", "综艺", "演员", "导演", "票房",
                               "歌", "曲", "剧", "偶像", "粉丝", "CP"]
    if any(kw in title for kw in entertainment_keywords):
        return "娱乐热点"

    # 教育考试
    education_keywords = ["高考", "大学", "学校", "考试", "考研", "教育", "学生",
                           "录取", "分数线", "毕业", "教师", "作业", "培训班"]
    if any(kw in title for kw in education_keywords):
        return "教育考试"

    # 科技财经
    tech_keywords = ["股票", "公司", "发布", "科技", "AI", "手机", "汽车", "芯片",
                      "投资", "经济", "市场", "新品", "产品", "融资", "市值", "互联网"]
    if any(kw in title for kw in tech_keywords):
        return "科技财经"

    # 体育赛事
    sports_keywords = ["比赛", "冠军", "足球", "篮球", "奥运", "运动员", "球", "赛",
                       "队", "世界杯", "金牌", "亚军", "季军", "决赛", "英超", "NBA"]
    if any(kw in title for kw in sports_keywords):
        return "体育赛事"

    # 社会事件
    social_keywords = ["警方", "事故", "回应", "通报", "医院", "法院", "火灾",
                        "死亡", "受伤", "救援", "调查", "嫌疑", "嫌疑人"]
    if any(kw in title for kw in social_keywords):
        return "社会事件"

    # 自然天气
    weather_keywords = ["降雨", "台风", "地震", "天气", "暴雨", "高温", "低温",
                          "雪", "寒潮", "预警", "洪水", "灾害", "气象"]
    if any(kw in title for kw in weather_keywords):
        return "自然天气"

    # 默认综合热点
    return "综合热点"


def extract_keywords_from_titles(titles, top_n=10):
    """
    从标题列表中提取高频关键词。

    使用 jieba 分词后统计词频。

    Args:
        titles: 标题列表
        top_n: 返回前 N 个高频词

    Returns:
        str: 关键词字符串，用顿号分隔
    """
    if not JIEBA_AVAILABLE:
        return "综合热点"

    # 停用词
    stopwords = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
        "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
        "自己", "这", "那", "他", "她", "它", "们", "这个", "那个", "什么", "怎么",
        "为什么", "如何", "一下", "一些", "一点", "可以", "可能", "应该", "还有",
        "但是", "所以", "因为", "如果", "虽然", "只是", "不过", "然后", "还是",
        "已经", "正在", "将会", "或者", "以及", "关于", "对于", "通过", "根据",
    }

    all_words = []
    for title in titles:
        if not title or not isinstance(title, str):
            continue
        words = jieba.cut(title)
        # 过滤停用词和单字
        words = [w.strip() for w in words if w.strip() and len(w) > 1 and w not in stopwords]
        all_words.extend(words)

    # 统计词频
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(top_n)

    return "、".join([w[0] for w in top_words]) if top_words else "综合热点"


def run_tfidf_clustering(titles, n_clusters):
    """
    使用 TF-IDF + KMeans 进行聚类（fallback 方法）。

    Args:
        titles: 标题列表
        n_clusters: 聚类数量

    Returns:
        tuple: (聚类标签列表, TF-IDF 特征矩阵, TfidfVectorizer 实例)
    """
    if not SKLEARN_AVAILABLE:
        raise RuntimeError("scikit-learn 未安装，无法使用 TF-IDF 聚类")

    # 分词
    if JIEBA_AVAILABLE:
        segmented_titles = [" ".join(jieba.cut(title)) for title in titles]
    else:
        # 不使用分词，直接使用原始文本
        segmented_titles = titles

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=1,
        max_df=0.95,
    )
    tfidf_matrix = vectorizer.fit_transform(segmented_titles)

    # KMeans 聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(tfidf_matrix)

    return labels, tfidf_matrix, vectorizer


def run_embedding_clustering(raw_df):
    """
    执行语义嵌入聚类。

    优先使用 sentence-transformers 生成句向量。
    如果模型不可用或加载失败，根据配置决定是否回退到 TF-IDF。

    Args:
        raw_df: pandas.DataFrame，包含 title, rank_num, hot_value, fetch_time 字段

    Returns:
        pandas.DataFrame: 聚类结果，包含以下字段：
            - keyword: 热搜关键词（标题）
            - cluster_id: 聚类 ID
            - cluster_name: 聚类主题名称
            - semantic_keywords: 聚类关键词
            - embedding_method: 嵌入方法
            - hot_value: 热度值
            - rank_num: 排名
            - cluster_date: 聚类日期
    """
    if raw_df.empty:
        print("[semantic] 语义聚类完成，结果数量：0")
        return pd.DataFrame()

    # 获取配置
    config = semantic_config
    n_clusters = config["cluster_count"]
    embedding_method = config["embedding_method"]
    fallback_to_tfidf = config.get("fallback_to_tfidf", True)

    # 获取标题列表
    titles = raw_df["title"].tolist()
    sample_count = len(titles)

    # 检查样本数量
    if sample_count < 2:
        print("[semantic] 聚类样本数量不足（少于2条），跳过聚类")
        return pd.DataFrame()

    # 动态调整聚类数量
    if sample_count < n_clusters:
        n_clusters = max(2, sample_count)
        print(f"[semantic] 样本数量少于聚类数量，自动调整为 {n_clusters}")

    print("[semantic] 语义向量聚类开始")

    # 尝试使用 sentence-transformers
    embeddings = None
    actual_method = "sentence_transformers"

    if embedding_method == "sentence_transformers" or embedding_method == "sentence-transformers":
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            global sentence_transformer_model
            if sentence_transformer_model is None:
                sentence_transformer_model = load_sentence_transformer_model()

            if sentence_transformer_model is not None:
                try:
                    print(f"[semantic] 使用模型：{config['model_name']}")
                    embeddings = sentence_transformer_model.encode(titles, show_progress_bar=True)
                except Exception as e:
                    print(f"[semantic] 句向量生成失败：{e}")
                    embeddings = None
            else:
                print("[semantic] 模型加载失败")
        else:
            print("[semantic] sentence-transformers 未安装")

    # 如果没有句向量，检查是否回退到 TF-IDF
    if embeddings is None:
        if fallback_to_tfidf:
            print("[semantic] 使用 TF-IDF fallback")
            actual_method = "tfidf"
        else:
            print("[semantic] 错误：不允许 TF-IDF fallback，请检查 sentence-transformers 安装")
            raise RuntimeError("sentence-transformers 不可用且不允许 fallback")

    # 执行聚类
    if embeddings is not None:
        # 使用 sentence-transformers 句向量聚类
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn 未安装，无法进行聚类")

        print(f"[semantic] 聚类样本数量：{sample_count}")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        print(f"[semantic] 聚类完成，结果数量：{len(cluster_labels)}")
    else:
        # 使用 TF-IDF fallback
        cluster_labels, _, _ = run_tfidf_clustering(titles, n_clusters)
        print(f"[semantic] TF-IDF fallback 聚类完成，结果数量：{len(cluster_labels)}")

    # 生成结果
    results = []
    cluster_keyword_map = {}  # 用于存储每个聚类的关键词

    # 第一遍：提取每个聚类的关键词
    for i in range(n_clusters):
        cluster_indices = [idx for idx, label in enumerate(cluster_labels) if label == i]
        cluster_titles = [titles[idx] for idx in cluster_indices]
        keywords = extract_keywords_from_titles(cluster_titles, top_n=8)
        cluster_keyword_map[i] = keywords

    # 第二遍：生成完整结果
    for idx, (_, row) in enumerate(raw_df.iterrows()):
        title = row.get("title", "")
        cluster_id = int(cluster_labels[idx])
        cluster_name = get_cluster_name(title)
        keywords = cluster_keyword_map.get(cluster_id, "综合热点")
        hot_value = row.get("hot_value", 0)
        rank_num = row.get("rank_num", None)
        fetch_time = row.get("fetch_time", None)
        cluster_date = fetch_time.date() if fetch_time else None

        results.append({
            "keyword": title,
            "cluster_id": cluster_id,
            "cluster_name": cluster_name,
            "semantic_keywords": keywords,
            "embedding_method": actual_method,
            "hot_value": int(hot_value) if pd.notna(hot_value) else 0,
            "rank_num": int(rank_num) if pd.notna(rank_num) else None,
            "cluster_date": cluster_date,
        })

    result_df = pd.DataFrame(results)
    print(f"[semantic] 语义向量聚类完成，结果数量：{len(result_df)}")

    return result_df


if __name__ == "__main__":
    # 测试聚类
    test_data = pd.DataFrame({
        "title": [
            "某明星演唱会门票秒空",
            "电影票房突破10亿",
            "高考成绩今日公布",
            "大学录取通知书发放",
            "某公司发布新品手机",
            "AI技术再次突破",
            "世界杯足球赛开幕",
            "中国女排夺冠",
            "某地发生火灾事故",
            "警方破获重大案件",
            "明起暴雨来袭",
            "台风即将来临",
            "天气晴朗适合出行",
            "某明星新剧开播",
            "某学校发生事故",
        ],
        "rank_num": list(range(1, 16)),
        "hot_value": [1000000 - i * 50000 for i in range(15)],
        "fetch_time": pd.date_range("2024-01-01", periods=15, freq="h"),
    })

    results = run_embedding_clustering(test_data)
    print(results)
