<template>
  <div class="page-shell">
    <main class="sentiment-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">第五期 · SnowNLP 情感分析 · Sentence-Transformers 语义聚类</p>
          <h1>微博热搜情感分析与语义聚类增强</h1>
          <p class="hero-text">
            基于中文情感分析与语义向量表示的微博热搜深度文本分析模块。
            使用 SnowNLP 计算情感分数，Sentence-Transformers 生成语义向量，KMeans 进行主题聚类。
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--primary" @click="runSentiment" :disabled="running">
            <span class="btn-icon" :class="{ spin: running }">↻</span>
            {{ running === 'sentiment' ? '运行中...' : '运行情感分析' }}
          </button>
          <button class="btn btn--secondary" @click="runSemantic" :disabled="running">
            <span class="btn-icon" :class="{ spin: running }">↻</span>
            {{ running === 'semantic' ? '运行中...' : '运行语义聚类' }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">⚠️ {{ pageError }}</div>
      <div v-if="pageSuccess" class="alert alert--success">✅ {{ pageSuccess }}</div>

      <!-- 无数据提示 -->
      <div v-if="hasNoData" class="empty-hint">
        <p>暂无情感或语义分析数据，请先运行第五期分析任务。</p>
        <p>运行命令：<code>python sentiment/sentiment_job.py</code> 和 <code>python semantic/semantic_cluster_job.py</code></p>
      </div>

      <!-- 情感概览卡片 -->
      <section class="cards" v-if="!hasNoData">
        <article class="card card--pos">
          <div class="card-left">
            <div class="card-icon">😊</div>
          </div>
          <div class="card-body">
            <span class="card-label">平均情绪分</span>
            <strong class="card-value">{{ summary.avg_sentiment_score?.toFixed(3) || '0.500' }}</strong>
            <span class="card-rate">情感倾向：{{ sentimentTrendLabel }}</span>
          </div>
          <div class="card-bar" :style="{ '--fill': (summary.avg_sentiment_score * 100) + '%', '--color': sentimentColor }"></div>
        </article>
        <article class="card card--pos2">
          <div class="card-left">
            <div class="card-icon">👍</div>
          </div>
          <div class="card-body">
            <span class="card-label">正向数量</span>
            <strong class="card-value card-value--pos">{{ formatNumber(summary.positive_count || 0) }}</strong>
            <span class="card-rate">占比 {{ positiveRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': positiveRatio + '%', '--color': '#22c55e' }"></div>
        </article>
        <article class="card card--neu">
          <div class="card-left">
            <div class="card-icon">😐</div>
          </div>
          <div class="card-body">
            <span class="card-label">中性数量</span>
            <strong class="card-value card-value--neu">{{ formatNumber(summary.neutral_count || 0) }}</strong>
            <span class="card-rate">占比 {{ neutralRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': neutralRatio + '%', '--color': '#94a3b8' }"></div>
        </article>
        <article class="card card--neg">
          <div class="card-left">
            <div class="card-icon">👎</div>
          </div>
          <div class="card-body">
            <span class="card-label">负向数量</span>
            <strong class="card-value card-value--neg">{{ formatNumber(summary.negative_count || 0) }}</strong>
            <span class="card-rate">占比 {{ negativeRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': negativeRatio + '%', '--color': '#ef4444' }"></div>
        </article>
      </section>

      <!-- 情感图表区域 -->
      <section class="charts-row" v-if="!hasNoData">
        <!-- 情感分布饼图 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>🥧 情感分布</h2>
              <p>正向、中性、负向情感的整体占比</p>
            </div>
          </div>
          <div ref="pieChartRef" class="chart"></div>
        </section>

        <!-- 公众情绪指数折线图 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>📈 公众情绪指数</h2>
              <p>每日平均情感分数变化趋势</p>
            </div>
          </div>
          <div ref="lineChartRef" class="chart"></div>
        </section>
      </section>

      <!-- 情感 Top20 表格 -->
      <section class="panel" v-if="!hasNoData">
        <div class="panel-header">
          <div>
            <h2>🔥 情绪 Top20 热搜</h2>
            <p>情感分数最高的热搜话题</p>
          </div>
          <div class="panel-actions">
            <div class="search-box">
              <input
                v-model="searchKeyword"
                placeholder="搜索关键词..."
                class="search-input"
                @keyup.enter="doSearch"
              />
              <button class="btn-search" @click="doSearch">搜索</button>
            </div>
            <select v-model="filterLabel" class="filter-select" @change="loadSentimentTop">
              <option value="">全部</option>
              <option value="positive">正向</option>
              <option value="neutral">中性</option>
              <option value="negative">负向</option>
            </select>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>关键词</th>
                <th>情绪分</th>
                <th>情绪标签</th>
                <th>热度值</th>
                <th>采集时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in sentimentTop" :key="index">
                <td>{{ index + 1 }}</td>
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td>
                  <span class="score-badge" :class="getScoreClass(item.sentiment_label)">
                    {{ Number(item.sentiment_score).toFixed(3) }}
                  </span>
                </td>
                <td>
                  <span class="label-tag" :class="'label-' + item.sentiment_label">
                    {{ item.sentiment_label_cn }}
                  </span>
                </td>
                <td>{{ formatNumber(item.hot_value) }}</td>
                <td>{{ formatTime(item.fetch_time) }}</td>
              </tr>
              <tr v-if="sentimentTop.length === 0">
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 语义聚类图表 -->
      <section class="charts-row" v-if="!hasNoData">
        <!-- 语义聚类分布 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>📊 语义聚类分布</h2>
              <p>热搜话题按语义主题分类统计</p>
            </div>
          </div>
          <div ref="clusterChartRef" class="chart"></div>
        </section>

        <!-- 语义主题分布 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>📋 主题分布统计</h2>
              <p>各语义主题的数量和热度</p>
            </div>
          </div>
          <div class="cluster-summary">
            <div v-for="item in clusterSummary" :key="item.cluster_name" class="cluster-item">
              <div class="cluster-name">{{ item.cluster_name }}</div>
              <div class="cluster-bar-wrap">
                <div class="cluster-bar" :style="{ width: getClusterPercent(item.count) + '%' }"></div>
              </div>
              <div class="cluster-info">
                <span class="cluster-count">{{ item.count }}条</span>
                <span class="cluster-avg">均热{{ formatNumber(item.avg_hot_value) }}</span>
              </div>
            </div>
          </div>
        </section>
      </section>

      <!-- 语义聚类结果表格 -->
      <section class="panel" v-if="!hasNoData">
        <div class="panel-header">
          <div>
            <h2>🔍 语义聚类明细</h2>
            <p>基于 Sentence-Transformers 句向量的语义聚类结果</p>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>主题</th>
                <th>关键词</th>
                <th>语义关键词</th>
                <th>嵌入方法</th>
                <th>热度值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in semanticClusters.slice(0, 30)" :key="index">
                <td>
                  <span class="cluster-tag">{{ item.cluster_name }}</span>
                </td>
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td class="keywords-cell">{{ item.semantic_keywords }}</td>
                <td>
                  <span class="method-tag" :class="item.embedding_method === 'sentence_transformers' ? 'method-st' : 'method-tfidf'">
                    {{ item.embedding_method === 'sentence_transformers' ? 'ST' : 'TF-IDF' }}
                  </span>
                </td>
                <td>{{ formatNumber(item.hot_value) }}</td>
              </tr>
              <tr v-if="semanticClusters.length === 0">
                <td colspan="5" class="empty-cell">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 导出报告按钮 -->
      <section class="export-section" v-if="!hasNoData">
        <button class="btn btn--export" @click="exportCsv">
          <span>📥</span> 导出 CSV 综合报告
        </button>
        <button class="btn btn--export btn--excel" @click="exportExcel">
          <span>📊</span> 导出 Excel 综合报告
        </button>
      </section>

    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import {
  getSentimentSummary,
  getSentimentDaily,
  getSentimentTop,
  searchSentiment,
  runSentimentJob,
  getSemanticClusters,
  getSemanticClusterSummary,
  runSemanticClusterJob,
  exportEnhancedReportCsv,
  exportEnhancedReportExcel,
} from "../api/index.js";

/* ===== 状态 ===== */
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const pageSuccess = ref("");

// 数据
const summary = ref({});
const sentimentDaily = ref([]);
const sentimentTop = ref([]);
const semanticClusters = ref([]);
const clusterSummary = ref([]);

// 筛选
const searchKeyword = ref("");
const filterLabel = ref("");

// 图表 DOM
const pieChartRef = ref(null);
const lineChartRef = ref(null);
const clusterChartRef = ref(null);

let pieChart = null;
let lineChart = null;
let clusterChart = null;

/* ===== 计算属性 ===== */
const hasNoData = computed(() => {
  return !summary.value.total_count && sentimentTop.value.length === 0 && semanticClusters.value.length === 0;
});

const sentimentTrendLabel = computed(() => {
  const score = summary.value.avg_sentiment_score || 0.5;
  if (score >= 0.6) return "偏正向";
  if (score <= 0.4) return "偏负向";
  return "偏中性";
});

const sentimentColor = computed(() => {
  const score = summary.value.avg_sentiment_score || 0.5;
  if (score >= 0.6) return "#22c55e";
  if (score <= 0.4) return "#ef4444";
  return "#94a3b8";
});

const totalCount = computed(() => {
  return (summary.value.positive_count || 0) + (summary.value.neutral_count || 0) + (summary.value.negative_count || 0) || 1;
});

const positiveRatio = computed(() => {
  return ((summary.value.positive_count || 0) / totalCount.value * 100).toFixed(1);
});

const neutralRatio = computed(() => {
  return ((summary.value.neutral_count || 0) / totalCount.value * 100).toFixed(1);
});

const negativeRatio = computed(() => {
  return ((summary.value.negative_count || 0) / totalCount.value * 100).toFixed(1);
});

const maxClusterCount = computed(() => {
  if (!clusterSummary.value.length) return 1;
  return Math.max(...clusterSummary.value.map(c => c.count));
});

/* ===== 工具函数 ===== */
function formatNumber(value) {
  const n = Number(value || 0);
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return n.toLocaleString("zh-CN");
}

function formatTime(time) {
  if (!time) return "-";
  const d = new Date(time);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function getScoreClass(label) {
  if (label === "positive") return "score-pos";
  if (label === "negative") return "score-neg";
  return "score-neu";
}

function getClusterPercent(count) {
  return (count / maxClusterCount.value * 100).toFixed(1);
}

/* ===== 数据加载 ===== */
async function loadSentimentSummary() {
  try {
    const res = await getSentimentSummary();
    if (res.error) {
      pageError.value = res.error;
      return;
    }
    summary.value = res || {};
  } catch (e) {
    pageError.value = "加载情感概览失败";
  }
}

async function loadSentimentDaily() {
  try {
    const res = await getSentimentDaily();
    if (res.error) return;
    sentimentDaily.value = res || [];
    await nextTick();
    buildLineChart();
  } catch (e) {
    console.error("加载每日情绪失败", e);
  }
}

async function loadSentimentTop() {
  try {
    const res = await getSentimentTop(20, filterLabel.value || null);
    if (res.error) {
      sentimentTop.value = [];
      return;
    }
    sentimentTop.value = res || [];
  } catch (e) {
    sentimentTop.value = [];
  }
}

async function doSearch() {
  if (!searchKeyword.value.trim()) {
    loadSentimentTop();
    return;
  }
  try {
    const res = await searchSentiment(searchKeyword.value.trim());
    if (res.error) {
      sentimentTop.value = [];
      return;
    }
    sentimentTop.value = res || [];
  } catch (e) {
    sentimentTop.value = [];
  }
}

async function loadSemanticClusters() {
  try {
    const res = await getSemanticClusters();
    if (res.error) {
      semanticClusters.value = [];
      return;
    }
    semanticClusters.value = res || [];
  } catch (e) {
    semanticClusters.value = [];
  }
}

async function loadClusterSummary() {
  try {
    const res = await getSemanticClusterSummary();
    if (res.error) {
      clusterSummary.value = [];
      return;
    }
    clusterSummary.value = res || [];
    await nextTick();
    buildClusterChart();
  } catch (e) {
    clusterSummary.value = [];
  }
}

async function loadAllData() {
  loading.value = true;
  pageError.value = "";
  try {
    await Promise.all([
      loadSentimentSummary(),
      loadSentimentDaily(),
      loadSentimentTop(),
      loadSemanticClusters(),
      loadClusterSummary(),
    ]);
    await nextTick();
    buildPieChart();
  } catch (e) {
    pageError.value = "部分数据加载失败";
  }
  loading.value = false;
}

/* ===== 图表构建 ===== */
function buildPieChart() {
  if (!pieChartRef.value) return;
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value);
  }

  pieChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      bottom: 20,
      textStyle: { color: "#5b6475", fontSize: 12 },
    },
    series: [
      {
        name: "情感分布",
        type: "pie",
        radius: ["42%", "68%"],
        center: ["50%", "45%"],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: "{b}\n{d}%",
          color: "#374151",
          fontSize: 12,
          fontWeight: 600,
        },
        labelLine: { lineStyle: { color: "#c4d0e5" } },
        data: [
          {
            name: "正向",
            value: summary.value.positive_count || 0,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "#4ade80" },
              { offset: 1, color: "#22c55e" },
            ]) },
          },
          {
            name: "中性",
            value: summary.value.neutral_count || 0,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "#cbd5e1" },
              { offset: 1, color: "#94a3b8" },
            ]) },
          },
          {
            name: "负向",
            value: summary.value.negative_count || 0,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "#f87171" },
              { offset: 1, color: "#ef4444" },
            ]) },
          },
        ],
      },
    ],
  }, true);
}

function buildLineChart() {
  if (!lineChartRef.value) return;
  if (!lineChart) {
    lineChart = echarts.init(lineChartRef.value);
  }

  const dates = sentimentDaily.value.map(d => {
    const dt = new Date(d.stat_date);
    return `${dt.getMonth() + 1}/${dt.getDate()}`;
  });
  const scores = sentimentDaily.value.map(d => Number(d.avg_sentiment_score).toFixed(3));

  lineChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLabel: { color: "#5b6475", fontSize: 11 },
      axisLine: { lineStyle: { color: "#c4d0e5" } },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 1,
      axisLabel: { color: "#5b6475", fontSize: 11, formatter: v => v.toFixed(1) },
      splitLine: { lineStyle: { color: "rgba(157,176,208,0.2)" } },
    },
    series: [
      {
        name: "情绪指数",
        type: "line",
        smooth: true,
        symbolSize: 8,
        data: scores,
        lineStyle: { width: 3, color: "#3f72af" },
        itemStyle: { color: "#3f72af" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(63,114,175,0.3)" },
            { offset: 1, color: "rgba(63,114,175,0.02)" },
          ]),
        },
      },
    ],
  }, true);
}

function buildClusterChart() {
  if (!clusterChartRef.value) return;
  if (!clusterChart) {
    clusterChart = echarts.init(clusterChartRef.value);
  }

  const data = clusterSummary.value.map(c => ({
    name: c.cluster_name,
    value: c.count,
  }));

  const colors = ["#e4572e", "#f4723e", "#2a9d8f", "#3f72af", "#60a5fa", "#a78bfa", "#22c55e"];

  clusterChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: "{b}: {c}条",
    },
    series: [
      {
        type: "pie",
        radius: ["35%", "65%"],
        center: ["50%", "50%"],
        roseType: "area",
        itemStyle: {
          borderRadius: 8,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: true,
          color: "#374151",
          fontSize: 12,
          fontWeight: 600,
        },
        data: data.map((d, i) => ({
          ...d,
          itemStyle: { color: colors[i % colors.length] },
        })),
      },
    ],
  }, true);
}

/* ===== 任务执行 ===== */
async function runSentiment() {
  running.value = "sentiment";
  pageError.value = "";
  pageSuccess.value = "";
  try {
    const res = await runSentimentJob();
    if (res.success) {
      pageSuccess.value = "情感分析任务执行成功！";
      await loadAllData();
    } else {
      pageError.value = "情感分析任务执行失败：" + res.message;
    }
  } catch (e) {
    pageError.value = "执行情感分析任务失败：" + e.message;
  }
  running.value = false;
}

async function runSemantic() {
  running.value = "semantic";
  pageError.value = "";
  pageSuccess.value = "";
  try {
    const res = await runSemanticClusterJob();
    if (res.success) {
      pageSuccess.value = "语义聚类任务执行成功！";
      await loadAllData();
    } else {
      pageError.value = "语义聚类任务执行失败：" + res.message;
    }
  } catch (e) {
    pageError.value = "执行语义聚类任务失败：" + e.message;
  }
  running.value = false;
}

/* ===== 导出报告 ===== */
async function exportCsv() {
  try {
    const { blob, filename } = await exportEnhancedReportCsv();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "weibo_hot_enhanced_report.csv";
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    pageError.value = "导出 CSV 报告失败：" + e.message;
  }
}

async function exportExcel() {
  try {
    const { blob, filename } = await exportEnhancedReportExcel();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "weibo_hot_enhanced_report.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    pageError.value = "导出 Excel 报告失败：" + e.message;
  }
}

/* ===== 生命周期 ===== */
function handleResize() {
  [pieChart, lineChart, clusterChart].forEach(c => c?.resize());
}

onMounted(async () => {
  await loadAllData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [pieChart, lineChart, clusterChart].forEach(c => {
    if (c) c.dispose();
  });
  pieChart = null;
  lineChart = null;
  clusterChart = null;
});
</script>

<style scoped>
.page-shell {
  min-height: calc(100vh - 64px);
  padding: 28px 20px 48px;
}

.sentiment-page {
  max-width: 1440px;
  margin: 0 auto;
  display: grid;
  gap: 22px;
}

/* ===================== Hero ===================== */
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 30px 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,252,255,0.9) 100%);
  border: 1px solid rgba(157,176,208,0.28);
  box-shadow: 0 20px 52px rgba(82,100,128,0.11);
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #22c55e, #3f72af, #ef4444, #e4572e);
  border-radius: 24px 24px 0 0;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.12em;
  font-weight: 600;
  color: #3f72af;
}

h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  line-height: 1.15;
  color: #0f172a;
  letter-spacing: -0.02em;
}

h2 {
  margin: 0 0 5px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

p {
  margin: 0;
  color: #5b6475;
  font-size: 13px;
}

.hero-text {
  margin-top: 10px;
  max-width: 640px;
  line-height: 1.7;
  font-size: 14px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* ===================== 按钮 ===================== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn--primary {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  box-shadow: 0 4px 12px rgba(34,197,94,0.3);
}

.btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(34,197,94,0.4);
}

.btn--secondary {
  background: linear-gradient(135deg, #3f72af, #16324f);
  color: #fff;
  box-shadow: 0 4px 12px rgba(63,114,175,0.3);
}

.btn--secondary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(63,114,175,0.4);
}

.btn--export {
  background: linear-gradient(135deg, #e4572e, #c23d1a);
  color: #fff;
  box-shadow: 0 4px 12px rgba(228,87,46,0.3);
}

.btn--export:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(228,87,46,0.4);
}

.btn--excel {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.btn--export:disabled,
.btn--primary:disabled,
.btn--secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  font-size: 16px;
  display: inline-block;
  transition: transform 0.3s;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===================== 提示 ===================== */
.alert {
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.alert--error {
  background: rgba(239,68,68,0.07);
  border: 1px solid rgba(239,68,68,0.2);
  color: #dc2626;
}

.alert--success {
  background: rgba(34,197,94,0.07);
  border: 1px solid rgba(34,197,94,0.2);
  color: #16a34a;
}

.empty-hint {
  padding: 32px;
  border-radius: 16px;
  background: rgba(63,114,175,0.05);
  border: 1px dashed rgba(63,114,175,0.3);
  text-align: center;
}

.empty-hint p {
  margin: 8px 0;
  color: #5b6475;
  font-size: 14px;
}

.empty-hint code {
  background: rgba(63,114,175,0.1);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
  color: #3f72af;
}

/* ===================== 统计卡片 ===================== */
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.card {
  padding: 22px 20px 28px;
  border-radius: 20px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(157,176,208,0.22);
  box-shadow: 0 8px 24px rgba(82,100,128,0.08);
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
}

.card-icon {
  font-size: 30px;
  flex-shrink: 0;
}

.card-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
  font-weight: 500;
}

.card-value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.card-value--pos { color: #16a34a; }
.card-value--neg { color: #dc2626; }
.card-value--neu { color: #475569; }

.card-rate {
  display: block;
  font-size: 12px;
  font-weight: 500;
  margin-top: 4px;
  color: #9ca3af;
}

.card-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(157,176,208,0.15);
}

.card-bar::after {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: var(--fill);
  background: var(--color);
  border-radius: 0 2px 2px 0;
  transition: width 0.8s ease;
}

.card--pos { border-top: 3px solid #22c55e; }
.card--pos2 { border-top: 3px solid #4ade80; }
.card--neu { border-top: 3px solid #94a3b8; }
.card--neg { border-top: 3px solid #ef4444; }

/* ===================== 面板 ===================== */
.panel {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(157,176,208,0.22);
  box-shadow: 0 12px 32px rgba(82,100,128,0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1.5px solid #cdd7ea;
  background: #fff;
  font-size: 13px;
  outline: none;
  width: 160px;
}

.search-input:focus {
  border-color: #3f72af;
}

.btn-search {
  padding: 8px 14px;
  border-radius: 10px;
  border: none;
  background: #3f72af;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.filter-select {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1.5px solid #cdd7ea;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
}

/* ===================== 图表 ===================== */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
}

.chart {
  width: 100%;
  height: 320px;
}

/* ===================== 表格 ===================== */
.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid rgba(157,176,208,0.2);
}

.data-table th {
  background: rgba(63,114,175,0.05);
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.data-table tr:hover {
  background: rgba(63,114,175,0.03);
}

.keyword-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.keywords-cell {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #6b7280;
}

.score-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.score-pos {
  background: rgba(34,197,94,0.1);
  color: #16a34a;
}

.score-neg {
  background: rgba(239,68,68,0.1);
  color: #dc2626;
}

.score-neu {
  background: rgba(148,163,184,0.2);
  color: #475569;
}

.label-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
}

.label-positive {
  background: rgba(34,197,94,0.1);
  color: #16a34a;
}

.label-neutral {
  background: rgba(148,163,184,0.2);
  color: #475569;
}

.label-negative {
  background: rgba(239,68,68,0.1);
  color: #dc2626;
}

.cluster-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(63,114,175,0.1);
  color: #3f72af;
  font-weight: 600;
}

.method-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 12px;
}

.method-st {
  background: rgba(63,114,175,0.1);
  color: #3f72af;
}

.method-tfidf {
  background: rgba(228,87,46,0.1);
  color: #c23d1a;
}

.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 32px !important;
}

/* ===================== 语义聚类统计 ===================== */
.cluster-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cluster-item {
  display: grid;
  grid-template-columns: 80px 1fr 100px;
  align-items: center;
  gap: 12px;
}

.cluster-name {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.cluster-bar-wrap {
  height: 10px;
  background: rgba(157,176,208,0.2);
  border-radius: 5px;
  overflow: hidden;
}

.cluster-bar {
  height: 100%;
  background: linear-gradient(90deg, #3f72af, #60a5fa);
  border-radius: 5px;
  transition: width 0.8s ease;
}

.cluster-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 11px;
}

.cluster-count {
  color: #374151;
  font-weight: 600;
}

.cluster-avg {
  color: #9ca3af;
}

/* ===================== 导出区域 ===================== */
.export-section {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 20px;
}

/* ===================== 响应式 ===================== */
@media (max-width: 1100px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 24px; }
  .hero { flex-direction: column; align-items: flex-start; }
  .cards { grid-template-columns: 1fr 1fr; gap: 10px; }
  .export-section { flex-direction: column; }
}
</style>
