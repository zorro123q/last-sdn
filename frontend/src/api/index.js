const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    throw new Error("接口请求失败，请检查后端服务是否启动");
  }

  if (!response.ok) {
    let message = "接口请求失败，请稍后重试";
    try {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        message = data.detail || data.message || message;
      } else {
        message = (await response.text()) || message;
      }
    } catch (error) {
      message = "接口返回异常，请稍后重试";
    }
    throw new Error(message || "接口请求失败");
  }
  return response.json();
}

async function downloadFile(path) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch (error) {
    throw new Error("报告下载失败，请检查后端服务是否启动");
  }

  if (!response.ok) {
    let message = "报告下载失败，请稍后重试";
    try {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        message = data.detail || data.message || message;
      } else {
        message = (await response.text()) || message;
      }
    } catch (error) {
      message = "报告下载返回异常，请稍后重试";
    }
    throw new Error(message);
  }

  const disposition = response.headers.get("content-disposition") || "";
  const filenameMatch = disposition.match(/filename\*=UTF-8''([^;]+)/);
  const filename = filenameMatch ? decodeURIComponent(filenameMatch[1]) : "";

  return {
    blob: await response.blob(),
    filename
  };
}

export function getSummary() {
  return request("/api/summary");
}

export function getCurrentRanking() {
  return request("/api/ranking/current");
}

export function getTrend(keyword) {
  return request(`/api/trend?keyword=${encodeURIComponent(keyword)}`);
}

export function getTopKeywords(limit = 20) {
  return request(`/api/analysis/keywords/top?limit=${encodeURIComponent(limit)}`);
}

export function getDailyStats() {
  return request("/api/analysis/daily");
}

export function runAnalysisJob() {
  return request("/api/analysis/run", { method: "POST" });
}

export function runCollectorJob() {
  return request("/api/collector/run", { method: "POST" });
}

export function getBurstTop(limit = 20) {
  return request(`/api/ml/burst/top?limit=${encodeURIComponent(limit)}`);
}

export function searchBurstKeyword(keyword) {
  return request(`/api/ml/burst/search?keyword=${encodeURIComponent(keyword)}`);
}

export function getTopicClusters() {
  return request("/api/ml/topics");
}

export function getClusterSummary() {
  return request("/api/ml/topics/summary");
}

export function runBurstPredictionJob() {
  return request("/api/ml/burst/run", { method: "POST" });
}

export function runTopicClusterJob() {
  return request("/api/ml/topics/run", { method: "POST" });
}

export function exportMlReportCsv() {
  return downloadFile("/api/export/ml_report.csv");
}

export function exportMlReportExcel() {
  return downloadFile("/api/export/ml_report.xlsx");
}

/* ===== 第五期情感分析与语义聚类 API ===== */

/**
 * 获取情感分析总体概览
 */
export function getSentimentSummary() {
  return request("/api/sentiment/summary");
}

/**
 * 获取每日情感统计数据
 */
export function getSentimentDaily() {
  return request("/api/sentiment/daily");
}

/**
 * 获取情感分析 Top 数据
 * @param {number} limit - 返回条数限制，默认 20
 * @param {string|null} label - 可选，按情感标签过滤
 */
export function getSentimentTop(limit = 20, label = null) {
  let path = `/api/sentiment/top?limit=${encodeURIComponent(limit)}`;
  if (label) {
    path += `&label=${encodeURIComponent(label)}`;
  }
  return request(path);
}

/**
 * 根据关键词搜索情感分析结果
 * @param {string} keyword - 搜索关键词
 */
export function searchSentiment(keyword) {
  return request(`/api/sentiment/search?keyword=${encodeURIComponent(keyword)}`);
}

/**
 * 手动触发情感分析任务
 */
export function runSentimentJob() {
  return request("/api/sentiment/run", { method: "POST" });
}

/**
 * 获取语义聚类结果
 */
export function getSemanticClusters() {
  return request("/api/semantic/clusters");
}

/**
 * 获取语义聚类主题分布统计
 */
export function getSemanticClusterSummary() {
  return request("/api/semantic/clusters/summary");
}

/**
 * 获取增强报告关键表数据量
 */
export function getReportDebugCounts() {
  return request("/api/report/debug-counts");
}

/* ===== 可视化增强 API ===== */

export function getHourlyHeatmap() {
  return request("/api/visual/hourly-heatmap");
}

/**
 * 热搜活跃时间热力图（/api/analysis/ 路径别名，与 getHourlyHeatmap 等价）
 */
export function getAnalysisHourlyHeatmap() {
  return request("/api/analysis/hourly-heatmap");
}

export function getRankMovers() {
  return request("/api/visual/rank-movers");
}

export function getVisualInsights() {
  return request("/api/visual/insights");
}

/**
 * 根据关键词查询爆发趋势识别结果（/api/analysis/ 路径版本）
 * @param {string} keyword - 搜索关键词
 */
export function getBurstByKeyword(keyword) {
  return request(`/api/analysis/burst/keyword?keyword=${encodeURIComponent(keyword)}`);
}

/**
 * 手动触发语义聚类任务
 */
export function runSemanticClusterJob() {
  return request("/api/semantic/run", { method: "POST" });
}

/**
 * 导出增强版综合报告 CSV
 */
export function exportEnhancedReportCsv() {
  return downloadFile("/api/export/enhanced_report.csv");
}

/**
 * 导出增强版综合报告 Excel
 */
export function exportEnhancedReportExcel() {
  return downloadFile("/api/export/enhanced_report.xlsx");
}

/* ===== 第六期智能分析与预警增强 API ===== */

export function getLifecycleSummary() {
  return request("/api/v6/lifecycle/summary");
}

export function getLifecycleList(stage = "", limit = 100) {
  const params = new URLSearchParams();
  if (stage) params.set("stage", stage);
  params.set("limit", String(limit));
  return request(`/api/v6/lifecycle/list?${params.toString()}`);
}

export function runLifecycleJob() {
  return request("/api/v6/lifecycle/run", { method: "POST" });
}

export function getAlertSummary() {
  return request("/api/v6/alerts/summary");
}

export function getAlertList(level = "", type = "", limit = 100) {
  const params = new URLSearchParams();
  if (level) params.set("level", level);
  if (type) params.set("type", type);
  params.set("limit", String(limit));
  return request(`/api/v6/alerts/list?${params.toString()}`);
}

export function runAlertJob() {
  return request("/api/v6/alerts/run", { method: "POST" });
}

export function markAlertRead(alertId) {
  return request(`/api/v6/alerts/${encodeURIComponent(alertId)}/read`, { method: "POST" });
}

export function getLatestAiReport() {
  return request("/api/v6/reports/latest");
}

export function getAiReportList() {
  return request("/api/v6/reports/list");
}

export function getAiReportDetail(reportId) {
  return request(`/api/v6/reports/${encodeURIComponent(reportId)}`);
}

export function runAiReportJob() {
  return request("/api/v6/reports/run", { method: "POST" });
}

export function getJobList() {
  return request("/api/v6/jobs");
}

export function getJobDetail(jobId) {
  return request(`/api/v6/jobs/${encodeURIComponent(jobId)}`);
}

export function runAllJobs() {
  return request("/api/v6/jobs/run-all", { method: "POST" });
}

export function getSystemHealthSummary() {
  return request("/api/v6/health/summary");
}

export function runSystemHealthCheck() {
  return request("/api/v6/health/run", { method: "POST" });
}

/* ===== 评论地理分布（省份热力数据） ===== */
export async function getCommentGeoData(keyword = "") {
  try {
    return await request(`/api/analysis/geo?keyword=${encodeURIComponent(keyword)}`);
  } catch {
    // 后端未实现时使用模拟演示数据
    return generateMockGeoData();
  }
}

/* ===== 情感分析数据 ===== */
export async function getSentimentData(keyword = "", withTrend = false) {
  try {
    const path = `/api/analysis/sentiment?keyword=${encodeURIComponent(keyword)}&trend=${withTrend}`;
    return await request(path);
  } catch {
    return generateMockSentimentData(withTrend);
  }
}

/* ===== 热词词云数据 ===== */
export async function getWordCloudData(keyword = "") {
  try {
    return await request(`/api/analysis/wordcloud?keyword=${encodeURIComponent(keyword)}`);
  } catch {
    return generateMockWordCloud(keyword);
  }
}

/* ===== 模拟数据生成器（当后端接口未实现时使用） ===== */
function generateMockGeoData() {
  const provinces = [
    { name: "广东", value: 45823 }, { name: "北京", value: 38921 }, { name: "上海", value: 36540 },
    { name: "江苏", value: 28934 }, { name: "浙江", value: 26712 }, { name: "山东", value: 21456 },
    { name: "四川", value: 19834 }, { name: "湖北", value: 17623 }, { name: "河南", value: 16784 },
    { name: "湖南", value: 15432 }, { name: "陕西", value: 13456 }, { name: "福建", value: 12987 },
    { name: "辽宁", value: 11234 }, { name: "安徽", value: 10876 }, { name: "河北", value: 9876 },
    { name: "天津", value: 9234 }, { name: "重庆", value: 8976 }, { name: "黑龙江", value: 7654 },
    { name: "吉林", value: 6543 }, { name: "江西", value: 6234 }, { name: "云南", value: 5876 },
    { name: "广西", value: 5432 }, { name: "贵州", value: 4987 }, { name: "山西", value: 4765 },
    { name: "内蒙古", value: 3987 }, { name: "新疆", value: 3456 }, { name: "甘肃", value: 2987 },
    { name: "海南", value: 2765 }, { name: "宁夏", value: 2156 }, { name: "青海", value: 1654 },
    { name: "西藏", value: 987 },
  ];
  // 加入轻微随机波动使演示更真实
  return provinces.map((p) => ({
    name: p.name,
    value: p.value + Math.floor(Math.random() * 2000 - 1000),
  }));
}

function generateMockSentimentData(withTrend = false) {
  const positive = 24680 + Math.floor(Math.random() * 5000);
  const negative = 8920 + Math.floor(Math.random() * 2000);
  const neutral = 15430 + Math.floor(Math.random() * 3000);

  if (!withTrend) {
    return { positive, negative, neutral };
  }

  // 生成最近 7 天趋势数据
  const trend = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = `${d.getMonth() + 1}/${d.getDate()}`;
    trend.push({
      date: dateStr,
      positive: Math.floor(positive * (0.8 + Math.random() * 0.4) / 7),
      negative: Math.floor(negative * (0.8 + Math.random() * 0.4) / 7),
      neutral: Math.floor(neutral * (0.8 + Math.random() * 0.4) / 7),
    });
  }
  return { positive, negative, neutral, trend };
}

function generateMockWordCloud(keyword = "") {
  const baseWords = [
    { name: "热搜", value: 3200 }, { name: "微博", value: 2890 }, { name: "关注", value: 2456 },
    { name: "评论", value: 2134 }, { name: "转发", value: 1987 }, { name: "点赞", value: 1876 },
    { name: "社会", value: 1654 }, { name: "新闻", value: 1543 }, { name: "网友", value: 1432 },
    { name: "视频", value: 1321 }, { name: "直播", value: 1234 }, { name: "明星", value: 1123 },
    { name: "话题", value: 987 }, { name: "爆料", value: 876 }, { name: "官方", value: 765 },
    { name: "回应", value: 698 }, { name: "热议", value: 654 }, { name: "网络", value: 612 },
    { name: "群众", value: 587 }, { name: "事件", value: 543 }, { name: "舆论", value: 512 },
    { name: "讨论", value: 487 }, { name: "声音", value: 456 }, { name: "关心", value: 432 },
    { name: "传播", value: 412 }, { name: "影响", value: 389 }, { name: "引发", value: 367 },
    { name: "公众", value: 345 }, { name: "媒体", value: 323 }, { name: "呼吁", value: 301 },
  ];
  if (keyword) {
    baseWords.unshift({ name: keyword.slice(0, 6), value: 4500 });
  }
  return baseWords.map((w) => ({
    name: w.name,
    value: w.value + Math.floor(Math.random() * 200 - 100),
  }));
}
