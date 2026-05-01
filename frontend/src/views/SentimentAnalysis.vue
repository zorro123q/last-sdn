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
            <svg class="btn-icon" :class="{ spin: running }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            {{ running === 'sentiment' ? '运行中...' : '运行情感分析' }}
          </button>
          <button class="btn btn--secondary" @click="runSemantic" :disabled="running">
            <svg class="btn-icon" :class="{ spin: running }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            {{ running === 'semantic' ? '运行中...' : '运行语义聚类' }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        {{ pageError }}
      </div>
      <div v-if="pageSuccess" class="alert alert--success">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        {{ pageSuccess }}
      </div>

      <!-- 无数据提示 -->
      <div v-if="hasNoData" class="empty-hint">
        <p>暂无情感或语义分析数据，请先运行第五期分析任务。</p>
        <p>暂无语义聚类数据，请先运行语义聚类任务。</p>
        <p>运行命令：<code>python sentiment/sentiment_job.py</code> 和 <code>python semantic/semantic_cluster_job.py</code></p>
      </div>

      <div v-if="semanticNoData" class="empty-hint semantic-empty">
        <p>暂无语义聚类数据，请先运行语义聚类任务。</p>
        <p>运行命令：<code>python semantic/semantic_cluster_job.py</code></p>
      </div>

      <section v-if="debugCountEntries.length" class="debug-card">
        <div class="debug-card-title">数据表状态</div>
        <div class="debug-grid">
          <span v-for="item in debugCountEntries" :key="item.name" class="debug-pill" :class="{ 'debug-pill--empty': item.count === 0, 'debug-pill--error': item.count === null }" :title="item.name">
            <strong>{{ item.label }}</strong>
            <em>{{ item.status }}</em>
          </span>
        </div>
      </section>

      <!-- 情感分析洞察卡片 -->
      <section v-if="sentimentInsights.length" class="insight-panel">
        <div class="insight-header">
          <svg class="insight-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
          <span>情感分析洞察</span>
        </div>
        <div class="insight-list">
          <div v-for="(text, i) in sentimentInsights" :key="i" class="insight-item">
            <span class="insight-dot"></span>
            <span class="insight-text">{{ text }}</span>
          </div>
        </div>
      </section>

      <!-- 情感概览卡片 -->
      <section class="cards" v-if="!hasNoData">
        <article class="card card--avg">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">平均情绪分</span>
            <strong class="card-value">{{ summary.avg_sentiment_score?.toFixed(3) || '0.500' }}</strong>
            <span class="card-rate">情感倾向：{{ sentimentTrendLabel }}</span>
          </div>
          <div class="card-bar" :style="{ '--fill': (summary.avg_sentiment_score * 100) + '%', '--color': sentimentColor }"></div>
        </article>
        <article class="card card--pos">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">正向数量</span>
            <strong class="card-value card-value--pos">{{ formatNumber(summary.positive_count || 0) }}</strong>
            <span class="card-rate">占比 {{ positiveRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': positiveRatio + '%', '--color': '#22c55e' }"></div>
        </article>
        <article class="card card--neu">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">中性数量</span>
            <strong class="card-value card-value--neu">{{ formatNumber(summary.neutral_count || 0) }}</strong>
            <span class="card-rate">占比 {{ neutralRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': neutralRatio + '%', '--color': '#94a3b8' }"></div>
        </article>
        <article class="card card--neg">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">负向数量</span>
            <strong class="card-value card-value--neg">{{ formatNumber(summary.negative_count || 0) }}</strong>
            <span class="card-rate">占比 {{ negativeRatio }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': negativeRatio + '%', '--color': '#ef4444' }"></div>
        </article>
      </section>

      <!-- 新增图表区：仪表盘 + 气泡图 + 饼图 + 折线图 -->
      <section class="charts-row charts-row--4" v-if="!hasNoData && !semanticNoData">
        <section class="panel">
          <div class="panel-header"><div><h2>公众情绪指数</h2><p>整体情感倾向仪表盘</p></div></div>
          <div ref="gaugeChartRef" class="chart"></div>
        </section>
        <section class="panel">
          <div class="panel-header"><div><h2>情感分布</h2><p>正向、中性、负向情感占比</p></div></div>
          <div ref="pieChartRef" class="chart"></div>
        </section>
        <section class="panel">
          <div class="panel-header"><div><h2>公众情绪指数趋势</h2><p>每日平均情感分数变化</p></div></div>
          <div ref="lineChartRef" class="chart"></div>
        </section>
        <section class="panel">
          <div class="panel-header"><div><h2>情感-热度气泡图</h2><p>情感分数与热度值的相关性分布</p></div></div>
          <div v-if="!sentimentTopAll.length" class="chart-empty"><EmptyState title="暂无数据" description="请先运行情感分析任务。" /></div>
          <div v-else ref="scatterChartRef" class="chart"></div>
        </section>
      </section>

      <!-- 语义主题卡片墙 -->
      <section v-if="clusterSummary.length" class="topic-cards">
        <div class="topic-cards-header">
          <h2>语义主题卡片墙</h2>
          <p>各主题类别的数量、平均热度和代表关键词</p>
        </div>
        <div class="topic-cards-grid">
          <div v-for="item in clusterSummary" :key="item.cluster_name" class="topic-card">
            <div class="topic-card-name">{{ item.cluster_name }}</div>
            <div class="topic-card-stats">
              <span class="topic-stat"><strong>{{ item.count }}</strong> 话题</span>
              <span class="topic-stat"><strong>{{ formatNumber(item.avg_hot_value) }}</strong> 均热</span>
              <span class="topic-stat"><strong>{{ formatNumber(item.max_hot_value) }}</strong> 最高</span>
            </div>
            <div class="topic-card-keywords">
              <span v-for="kw in getClusterKeywords(item.cluster_name)" :key="kw" class="topic-kw">{{ kw }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 语义聚类 Treemap -->
      <section class="panel" v-if="!hasNoData">
        <div class="panel-header">
          <div>
            <h2>语义聚类 Treemap</h2>
            <p>按主题层级展示热搜话题分布，方块大小代表热度值。</p>
          </div>
        </div>
        <div v-if="!semanticClusters.length" class="chart-empty">
          <EmptyState title="暂无语义聚类数据" description="请先运行 python semantic/semantic_cluster_job.py" />
        </div>
        <div v-else ref="treemapChartRef" class="chart-treemap"></div>
      </section>

      <!-- 情感 Top20 表格 -->
      <section class="panel" v-if="!hasNoData">
        <div class="panel-header">
          <div>
            <h2>情绪 Top20 热搜</h2>
            <p>情感分数最高的热搜话题</p>
          </div>
          <div class="panel-actions">
            <div class="search-box">
              <input v-model="searchKeyword" placeholder="搜索关键词..." class="search-input" @keyup.enter="doSearch" />
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
              <tr><th>排名</th><th>关键词</th><th>情绪分</th><th>情绪标签</th><th>热度值</th><th>采集时间</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in sentimentTop" :key="index">
                <td>{{ index + 1 }}</td>
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td><span class="score-badge" :class="getScoreClass(item.sentiment_label)">{{ Number(item.sentiment_score).toFixed(3) }}</span></td>
                <td><span class="label-tag" :class="'label-' + item.sentiment_label">{{ item.sentiment_label_cn }}</span></td>
                <td>{{ formatNumber(item.hot_value) }}</td>
                <td>{{ formatTime(item.fetch_time) }}</td>
              </tr>
              <tr v-if="sentimentTop.length === 0"><td colspan="6" class="empty-cell">暂无数据</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 语义聚类图表 -->
      <section class="charts-row" v-if="!hasNoData">
        <section class="panel">
          <div class="panel-header"><div><h2>语义聚类分布</h2><p>热搜话题按语义主题分类统计</p></div></div>
          <div ref="clusterChartRef" class="chart"></div>
        </section>
        <section class="panel">
          <div class="panel-header"><div><h2>主题分布统计</h2><p>各语义主题的数量和热度</p></div></div>
          <div class="cluster-summary">
            <div v-for="item in clusterSummary" :key="item.cluster_name" class="cluster-item">
              <div class="cluster-name">{{ item.cluster_name }}</div>
              <div class="cluster-bar-wrap"><div class="cluster-bar" :style="{ width: getClusterPercent(item.count) + '%' }"></div></div>
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
            <h2>语义聚类明细</h2>
            <p>基于 Sentence-Transformers 句向量的语义聚类结果</p>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>主题</th><th>关键词</th><th>语义关键词</th><th>嵌入方法</th><th>热度值</th></tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in semanticClusters.slice(0, 30)" :key="index">
                <td><span class="cluster-tag">{{ item.cluster_name }}</span></td>
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td class="keywords-cell">{{ item.semantic_keywords }}</td>
                <td><span class="method-tag" :class="item.embedding_method === 'sentence_transformers' ? 'method-st' : 'method-tfidf'">{{ item.embedding_method === 'sentence_transformers' ? 'ST' : 'TF-IDF' }}</span></td>
                <td>{{ formatNumber(item.hot_value) }}</td>
              </tr>
              <tr v-if="semanticClusters.length === 0"><td colspan="5" class="empty-cell">暂无语义聚类数据，请先运行语义聚类任务</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 导出报告按钮 -->
      <section class="export-section" v-if="!hasNoData">
        <button class="btn btn--export" @click="exportCsv">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          导出 CSV 综合报告
        </button>
        <button class="btn btn--export btn--excel" @click="exportExcel">
          <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          导出 Excel 综合报告
        </button>
      </section>

    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";
import {
  getSentimentSummary, getSentimentDaily, getSentimentTop, searchSentiment,
  runSentimentJob, getSemanticClusters, getSemanticClusterSummary,
  getReportDebugCounts, runSemanticClusterJob, exportEnhancedReportCsv, exportEnhancedReportExcel,
} from "../api/index.js";
import EmptyState from "../components/EmptyState.vue";

/* ===== 状态 ===== */
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const pageSuccess = ref("");

const summary = ref({});
const sentimentDaily = ref([]);
const sentimentTop = ref([]);
const sentimentTopAll = ref([]);
const semanticClusters = ref([]);
const clusterSummary = ref([]);
const debugCounts = ref({});

const searchKeyword = ref("");
const filterLabel = ref("");

const pieChartRef = ref(null);
const lineChartRef = ref(null);
const clusterChartRef = ref(null);
const gaugeChartRef = ref(null);
const scatterChartRef = ref(null);
const treemapChartRef = ref(null);

let pieChart = null;
let lineChart = null;
let clusterChart = null;
let gaugeChart = null;
let scatterChart = null;
let treemapChart = null;

/* ===== 计算属性 ===== */
const hasNoData = computed(() => !summary.value.total_count && sentimentTop.value.length === 0 && semanticClusters.value.length === 0);
const semanticNoData = computed(() => !loading.value && !hasNoData.value && semanticClusters.value.length === 0);

const debugTableLabels = {
  hot_search_raw: "原始热搜", hot_search_keyword_stats: "关键词统计", hot_search_daily_stats: "每日统计",
  hot_search_feature_stats: "特征统计", hot_search_burst_predictions: "爆发趋势", hot_search_topic_clusters: "主题聚类",
  hot_search_sentiment_stats: "情感明细", hot_search_sentiment_daily_stats: "每日情绪", hot_search_semantic_clusters: "语义聚类",
};

const debugCountEntries = computed(() => Object.entries(debugCounts.value).map(([name, count]) => ({
  name, label: debugTableLabels[name] || name, count, status: count === null ? "查询失败" : `${formatNumber(count)} 条`,
})));

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

const totalCount = computed(() => (summary.value.positive_count || 0) + (summary.value.neutral_count || 0) + (summary.value.negative_count || 0) || 1);
const positiveRatio = computed(() => ((summary.value.positive_count || 0) / totalCount.value * 100).toFixed(1));
const neutralRatio = computed(() => ((summary.value.neutral_count || 0) / totalCount.value * 100).toFixed(1));
const negativeRatio = computed(() => ((summary.value.negative_count || 0) / totalCount.value * 100).toFixed(1));

const maxClusterCount = computed(() => clusterSummary.value.length ? Math.max(...clusterSummary.value.map(c => c.count)) : 1);

// 情感洞察
const sentimentInsights = computed(() => {
  const items = [];
  const score = summary.value.avg_sentiment_score || 0;
  const label = score > 0.6 ? "正向" : (score < 0.4 ? "负向" : "中性");
  items.push(`当前微博热搜整体情绪偏${label}。`);
  items.push(`正向话题占比 ${positiveRatio.value}%，负向话题占比 ${negativeRatio.value}%。`);
  const topPos = sentimentTopAll.value.find(s => s.sentiment_label === 'positive');
  if (topPos) items.push(`情绪分最高的话题为「${topPos.keyword}」，分数为 ${Number(topPos.sentiment_score).toFixed(3)}。`);
  return items;
});

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

function getClusterKeywords(clusterName) {
  return semanticClusters.value
    .filter(c => c.cluster_name === clusterName)
    .slice(0, 3)
    .map(c => c.keyword);
}

/* ===== 数据加载 ===== */
async function loadSentimentSummary() {
  try { summary.value = await getSentimentSummary() || {}; } catch { pageError.value = "加载情感概览失败"; }
}

async function loadSentimentDaily() {
  try { sentimentDaily.value = await getSentimentDaily() || []; await nextTick(); buildLineChart(); } catch {}
}

async function loadSentimentTop() {
  try { sentimentTop.value = await getSentimentTop(20, filterLabel.value || null) || []; } catch { sentimentTop.value = []; }
}

async function loadSentimentTopAll() {
  try { sentimentTopAll.value = await getSentimentTop(100, null) || []; await nextTick(); buildScatterChart(); } catch { sentimentTopAll.value = []; }
}

async function doSearch() {
  if (!searchKeyword.value.trim()) { loadSentimentTop(); return; }
  try { sentimentTop.value = await searchSentiment(searchKeyword.value.trim()) || []; } catch { sentimentTop.value = []; }
}

async function loadSemanticClustersData() {
  try { semanticClusters.value = await getSemanticClusters() || []; await nextTick(); buildTreemapChart(); } catch { semanticClusters.value = []; }
}

async function loadClusterSummaryData() {
  try { clusterSummary.value = await getSemanticClusterSummary() || []; await nextTick(); buildClusterChart(); } catch { clusterSummary.value = []; }
}

async function loadDebugCounts() {
  try { debugCounts.value = await getReportDebugCounts() || {}; } catch { debugCounts.value = {}; }
}

async function loadAllData() {
  loading.value = true; pageError.value = "";
  try {
    await Promise.all([loadSentimentSummary(), loadSentimentDaily(), loadSentimentTop(), loadSentimentTopAll(), loadSemanticClustersData(), loadClusterSummaryData(), loadDebugCounts()]);
    await nextTick();
    buildPieChart(); buildGaugeChart();
  } catch { pageError.value = "部分数据加载失败"; }
  loading.value = false;
}

/* ===== 图表构建 ===== */
function buildPieChart() {
  if (!pieChartRef.value) return;
  if (!pieChart) pieChart = echarts.init(pieChartRef.value);
  pieChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" }, formatter: "{b}: {c} ({d}%)" },
    legend: { bottom: 10, textStyle: { color: "#64748b", fontSize: 12 } },
    series: [{
      name: "情感分布", type: "pie", radius: ["42%", "68%"], center: ["50%", "45%"], avoidLabelOverlap: false,
      label: { show: true, formatter: "{b}\n{d}%", color: "#374151", fontSize: 12, fontWeight: 600 },
      labelLine: { lineStyle: { color: "#cbd5e1" } },
      data: [
        { name: "正向", value: summary.value.positive_count || 0, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "#4ade80" }, { offset: 1, color: "#22c55e" }]) } },
        { name: "中性", value: summary.value.neutral_count || 0, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "#cbd5e1" }, { offset: 1, color: "#94a3b8" }]) } },
        { name: "负向", value: summary.value.negative_count || 0, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "#f87171" }, { offset: 1, color: "#ef4444" }]) } },
      ],
    }],
  }, true);
}

function buildGaugeChart() {
  if (!gaugeChartRef.value) return;
  if (!gaugeChart) gaugeChart = echarts.init(gaugeChartRef.value);
  const score = (summary.value.avg_sentiment_score || 0.5) * 100;
  let color = "#3b82f6";
  if (score >= 60) color = "#22c55e";
  else if (score <= 40) color = "#ef4444";
  gaugeChart.setOption({
    backgroundColor: "transparent",
    series: [{
      type: "gauge",
      startAngle: 200,
      endAngle: -20,
      min: 0,
      max: 100,
      splitNumber: 10,
      itemStyle: { color },
      progress: { show: true, width: 18 },
      pointer: { show: true, length: "60%", width: 5 },
      axisLine: { lineStyle: { width: 18, color: [[1, "rgba(148,163,184,0.2)"]] } },
      axisTick: { distance: -25, splitNumber: 5, lineStyle: { width: 1, color: "#999" } },
      splitLine: { distance: -30, length: 10, lineStyle: { width: 2, color: "#999" } },
      axisLabel: { distance: -15, color: "#64748b", fontSize: 10 },
      anchor: { show: true, size: 15, itemStyle: { borderColor: color, borderWidth: 2 } },
      title: { show: true, offsetCenter: [0, "30%"], fontSize: 13, color: "#64748b" },
      detail: { valueAnimation: true, fontSize: 28, offsetCenter: [0, "-10%"], formatter: "{value}", color: "var(--navy)", fontWeight: 700 },
      data: [{ value: score.toFixed(1), name: score >= 60 ? "偏正向" : (score <= 40 ? "偏负向" : "偏中性") }],
    }],
  }, true);
}

function buildLineChart() {
  if (!lineChartRef.value) return;
  if (!lineChart) lineChart = echarts.init(lineChartRef.value);
  const dates = sentimentDaily.value.map(d => { const dt = new Date(d.stat_date); return `${dt.getMonth() + 1}/${dt.getDate()}`; });
  const scores = sentimentDaily.value.map(d => Number(d.avg_sentiment_score).toFixed(3));
  lineChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: dates, boundaryGap: false, axisLabel: { color: "#64748b", fontSize: 11 }, axisLine: { lineStyle: { color: "#cbd5e1" } } },
    yAxis: { type: "value", min: 0, max: 1, axisLabel: { color: "#64748b", fontSize: 11, formatter: v => v.toFixed(1) }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.2)" } } },
    series: [{
      name: "情绪指数", type: "line", smooth: true, symbolSize: 8, data: scores,
      lineStyle: { width: 3, color: "#2563eb" }, itemStyle: { color: "#2563eb" },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(37,99,235,0.3)" }, { offset: 1, color: "rgba(37,99,235,0.02)" }]) },
    }],
  }, true);
}

function buildScatterChart() {
  if (!scatterChartRef.value) return;
  if (!scatterChart) scatterChart = echarts.init(scatterChartRef.value);
  const data = sentimentTopAll.value.map(item => ({
    name: item.keyword,
    value: [Number(item.sentiment_score || 0), Number(item.hot_value || 0)],
    label: item.sentiment_label_cn,
    rank: item.rank_num,
  }));
  scatterChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" },
      formatter(p) {
        return `<div style="font-weight:700;margin-bottom:4px">${p.data.name}</div>` +
          `<div>情感分数：${p.data.value[0].toFixed(3)}</div>` +
          `<div>情感标签：${p.data.label}</div>` +
          `<div>热度值：${formatNumber(p.data.value[1])}</div>` +
          `<div>排名：${p.data.rank}</div>`;
      },
    },
    grid: { left: 60, right: 30, top: 30, bottom: 50 },
    xAxis: {
      type: "value", name: "情感分数", nameTextStyle: { color: "#64748b", fontSize: 11 }, min: 0, max: 1,
      axisLabel: { color: "#64748b", fontSize: 11 }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } }, axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
    },
    yAxis: {
      type: "value", name: "热度值", nameTextStyle: { color: "#64748b", fontSize: 11 },
      axisLabel: { color: "#64748b", fontSize: 11, formatter: v => v >= 10000 ? `${Math.round(v / 10000)}万` : v },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } }, axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
    },
    series: [{
      type: "scatter", symbolSize: (d) => Math.min(Math.max(Math.sqrt(d[1]) / 25, 6), 36),
      data,
      itemStyle: { color: p => { const s = p.data.value[0]; return s >= 0.6 ? "#22c55e" : (s <= 0.4 ? "#ef4444" : "#94a3b8"); }, opacity: 0.8 },
    }],
  }, true);
}

function buildClusterChart() {
  if (!clusterChartRef.value) return;
  if (!clusterChart) clusterChart = echarts.init(clusterChartRef.value);
  const data = clusterSummary.value.map(c => ({ name: c.cluster_name, value: c.count }));
  const colors = ["#2563eb", "#3b82f6", "#06b6d4", "#8b5cf6", "#60a5fa", "#a78bfa", "#22c55e"];
  clusterChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" }, formatter: "{b}: {c}条" },
    series: [{
      type: "pie", radius: ["35%", "65%"], center: ["50%", "50%"], roseType: "area",
      itemStyle: { borderRadius: 8, borderColor: "#fff", borderWidth: 2 },
      label: { show: true, color: "#374151", fontSize: 12, fontWeight: 600 },
      data: data.map((d, i) => ({ ...d, itemStyle: { color: colors[i % colors.length] } })),
    }],
  }, true);
}

function buildTreemapChart() {
  if (!treemapChartRef.value) return;
  if (!treemapChart) treemapChart = echarts.init(treemapChartRef.value);
  if (!semanticClusters.value.length) return;
  const groups = {};
  semanticClusters.value.forEach(item => {
    if (!groups[item.cluster_name]) groups[item.cluster_name] = [];
    groups[item.cluster_name].push({ name: item.keyword, value: item.hot_value || 1 });
  });
  const data = Object.entries(groups).map(([name, children]) => ({ name, value: children.reduce((s, c) => s + c.value, 0), children }));
  treemapChart.setOption({
    backgroundColor: "transparent",
    tooltip: { backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    series: [{
      type: "treemap", roam: false, nodeClick: false, breadcrumb: { show: false },
      label: { show: true, formatter: "{b}", fontSize: 12 },
      itemStyle: { borderColor: "#fff", borderWidth: 1, gapWidth: 1 },
      levels: [
        { itemStyle: { borderColor: "#fff", borderWidth: 2, gapWidth: 2 } },
        { colorSaturation: [0.3, 0.6], itemStyle: { borderColorSaturation: 0.5, gapWidth: 1 } },
      ],
      data,
    }],
  }, true);
}

/* ===== 任务执行 ===== */
async function runSentiment() {
  running.value = "sentiment"; pageError.value = ""; pageSuccess.value = "";
  try {
    const res = await runSentimentJob();
    if (res.success) { pageSuccess.value = "情感分析任务执行成功！"; await loadAllData(); }
    else pageError.value = "情感分析任务执行失败：" + res.message;
  } catch (e) { pageError.value = "执行情感分析任务失败：" + e.message; }
  running.value = false;
}

async function runSemantic() {
  running.value = "semantic"; pageError.value = ""; pageSuccess.value = "";
  try {
    const res = await runSemanticClusterJob();
    if (res.success) { pageSuccess.value = "语义聚类任务执行成功！"; await loadAllData(); }
    else pageError.value = "语义聚类任务执行失败：" + res.message;
  } catch (e) { pageError.value = "执行语义聚类任务失败：" + e.message; }
  running.value = false;
}

/* ===== 导出报告 ===== */
async function exportCsv() {
  try {
    const { blob, filename } = await exportEnhancedReportCsv();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = filename || "weibo_hot_enhanced_report.csv"; a.click(); URL.revokeObjectURL(url);
  } catch (e) { pageError.value = "导出 CSV 报告失败：" + e.message; }
}

async function exportExcel() {
  try {
    const { blob, filename } = await exportEnhancedReportExcel();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = filename || "weibo_hot_enhanced_report.xlsx"; a.click(); URL.revokeObjectURL(url);
  } catch (e) { pageError.value = "导出 Excel 报告失败：" + e.message; }
}

/* ===== 生命周期 ===== */
function handleResize() {
  [pieChart, lineChart, clusterChart, gaugeChart, scatterChart, treemapChart].forEach(c => c?.resize());
}

onMounted(async () => {
  await loadAllData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [pieChart, lineChart, clusterChart, gaugeChart, scatterChart, treemapChart].forEach(c => { if (c) c.dispose(); });
  pieChart = null; lineChart = null; clusterChart = null; gaugeChart = null; scatterChart = null; treemapChart = null;
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.sentiment-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }

/* Hero */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 52px rgba(37,99,235,0.2), 0 1px 0 rgba(255,255,255,0.1) inset; position: relative; overflow: hidden; }
.hero::before { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08), transparent 50%); pointer-events: none; }
.eyebrow { margin: 0 0 8px; font-size: 13px; letter-spacing: 0.12em; font-weight: 600; color: rgba(255,255,255,0.7); }
h1 { margin: 0; font-size: 32px; font-weight: 800; line-height: 1.15; color: #fff; letter-spacing: -0.02em; }
h2 { margin: 0 0 5px; font-size: 18px; font-weight: 700; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 13px; }
.hero-text { margin-top: 10px; max-width: 640px; line-height: 1.7; font-size: 14px; color: rgba(255,255,255,0.75); }
.hero-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }

/* 按钮 */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 20px; border-radius: var(--radius-btn); font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; border: none; }
.btn--primary { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
.btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(37,99,235,0.35); }
.btn--secondary { background: linear-gradient(135deg, #06b6d4, #0891b2); color: #fff; box-shadow: 0 4px 12px rgba(6,182,212,0.3); }
.btn--secondary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(6,182,212,0.35); }
.btn--export { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
.btn--export:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(37,99,235,0.35); }
.btn--excel { background: linear-gradient(135deg, #22c55e, #16a34a); }
.btn--export:disabled, .btn--primary:disabled, .btn--secondary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-icon { width: 16px; height: 16px; display: inline-block; transition: transform 0.3s; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 提示 */
.alert { display: flex; align-items: center; gap: 8px; padding: 12px 18px; border-radius: 12px; font-size: 14px; font-weight: 500; }
.alert-icon { width: 18px; height: 18px; flex-shrink: 0; }
.alert--error { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); color: #dc2626; }
.alert--success { background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.15); color: #16a34a; }
.empty-hint { padding: 32px; border-radius: 16px; background: rgba(37,99,235,0.05); border: 1px dashed rgba(37,99,235,0.3); text-align: center; }
.empty-hint p { margin: 8px 0; color: var(--text-muted); font-size: 14px; }
.empty-hint code { background: rgba(37,99,235,0.1); padding: 2px 8px; border-radius: 4px; font-family: monospace; color: var(--primary); }
.semantic-empty { padding: 20px 24px; text-align: left; }
.debug-card { padding: 16px 18px; border-radius: 12px; background: rgba(255,255,255,0.72); border: 1px solid rgba(148,163,184,0.22); box-shadow: 0 8px 24px rgba(15,23,42,0.05); }
.debug-card-title { margin-bottom: 12px; color: #334155; font-size: 13px; font-weight: 700; }
.debug-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
.debug-pill { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 10px; border-radius: 8px; background: rgba(37,99,235,0.06); color: #334155; font-size: 12px; }
.debug-pill strong, .debug-pill em { font-style: normal; }
.debug-pill em { color: #2563eb; font-weight: 700; white-space: nowrap; }
.debug-pill--empty { background: rgba(245,158,11,0.08); }
.debug-pill--empty em { color: #b45309; }
.debug-pill--error { background: rgba(239,68,68,0.08); }
.debug-pill--error em { color: #dc2626; }

/* 洞察面板 */
.insight-panel { padding: 20px 24px; border-radius: var(--radius-card); background: linear-gradient(135deg, rgba(37,99,235,0.04), rgba(6,182,212,0.04)); border: 1px solid rgba(37,99,235,0.12); box-shadow: var(--shadow-card); }
.insight-header { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 12px; }
.insight-icon { width: 18px; height: 18px; }
.insight-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px 24px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--text-base); line-height: 1.6; }
.insight-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); margin-top: 7px; flex-shrink: 0; }
.insight-text { flex: 1; }

/* 统计卡片 */
.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.card { padding: 22px 20px 28px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); display: flex; align-items: center; gap: 16px; position: relative; overflow: hidden; transition: transform 0.2s ease; }
.card:hover { transform: translateY(-2px); }
.card-icon-wrap { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-icon-svg { width: 24px; height: 24px; }
.card-body { flex: 1; }
.card-label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 4px; font-weight: 500; }
.card-value { display: block; font-size: 28px; font-weight: 800; color: var(--navy); font-variant-numeric: tabular-nums; }
.card-value--pos { color: #16a34a; }
.card-value--neg { color: #dc2626; }
.card-value--neu { color: #475569; }
.card-rate { display: block; font-size: 12px; font-weight: 500; margin-top: 4px; color: var(--text-light); }
.card-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: rgba(148,163,184,0.15); }
.card-bar::after { content: ""; position: absolute; left: 0; top: 0; height: 100%; width: var(--fill); background: var(--color); border-radius: 0 2px 2px 0; transition: width 0.8s ease; }
.card--avg { border-top: 3px solid #2563eb; } .card--avg .card-icon-wrap { background: rgba(37,99,235,0.1); color: #2563eb; }
.card--pos { border-top: 3px solid #22c55e; } .card--pos .card-icon-wrap { background: rgba(34,197,94,0.1); color: #22c55e; }
.card--neu { border-top: 3px solid #94a3b8; } .card--neu .card-icon-wrap { background: rgba(148,163,184,0.1); color: #94a3b8; }
.card--neg { border-top: 3px solid #ef4444; } .card--neg .card-icon-wrap { background: rgba(239,68,68,0.1); color: #ef4444; }

/* 面板 */
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 20px; }
.panel-actions { display: flex; align-items: center; gap: 12px; }
.search-box { display: flex; align-items: center; gap: 8px; }
.search-input { padding: 8px 14px; border-radius: 10px; border: 1.5px solid #cbd5e1; background: #fff; font-size: 13px; outline: none; width: 160px; }
.search-input:focus { border-color: var(--primary); }
.btn-search { padding: 8px 14px; border-radius: 10px; border: none; background: var(--primary); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; }
.filter-select { padding: 8px 14px; border-radius: 10px; border: 1.5px solid #cbd5e1; background: #fff; font-size: 13px; cursor: pointer; }

/* 图表 */
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.charts-row--4 { grid-template-columns: repeat(4, 1fr); }
.chart { width: 100%; height: 320px; }
.chart-empty { height: 320px; display: flex; align-items: center; justify-content: center; }
.chart-treemap { width: 100%; height: 420px; }

/* 主题卡片墙 */
.topic-cards-header { padding: 0 4px; }
.topic-cards-header h2 { font-size: 20px; font-weight: 700; color: var(--navy); margin: 0 0 4px; }
.topic-cards-header p { color: var(--text-muted); font-size: 14px; }
.topic-cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.topic-card { padding: 20px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); transition: transform 0.2s ease; }
.topic-card:hover { transform: translateY(-2px); }
.topic-card-name { font-size: 16px; font-weight: 700; color: var(--navy); margin-bottom: 10px; }
.topic-card-stats { display: flex; gap: 12px; margin-bottom: 12px; }
.topic-stat { font-size: 12px; color: var(--text-muted); }
.topic-stat strong { color: var(--primary); font-size: 15px; font-weight: 700; }
.topic-card-keywords { display: flex; flex-wrap: wrap; gap: 6px; }
.topic-kw { padding: 3px 10px; border-radius: 20px; background: rgba(37,99,235,0.08); color: var(--primary); font-size: 12px; font-weight: 500; }

/* 表格 */
.table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid rgba(148,163,184,0.2); }
.data-table th { background: rgba(37,99,235,0.05); font-weight: 600; color: #374151; white-space: nowrap; }
.data-table tr:hover { background: rgba(37,99,235,0.03); }
.keyword-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.keywords-cell { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-muted); }
.score-badge { display: inline-block; padding: 4px 10px; border-radius: 8px; font-weight: 600; font-variant-numeric: tabular-nums; }
.score-pos { background: rgba(34,197,94,0.1); color: #16a34a; }
.score-neg { background: rgba(239,68,68,0.1); color: #dc2626; }
.score-neu { background: rgba(148,163,184,0.2); color: #475569; }
.label-tag { display: inline-block; padding: 4px 10px; border-radius: 8px; font-weight: 600; }
.label-positive { background: rgba(34,197,94,0.1); color: #16a34a; }
.label-neutral { background: rgba(148,163,184,0.2); color: #475569; }
.label-negative { background: rgba(239,68,68,0.1); color: #dc2626; }
.cluster-tag { display: inline-block; padding: 4px 10px; border-radius: 8px; background: rgba(37,99,235,0.1); color: var(--primary); font-weight: 600; }
.method-tag { display: inline-block; padding: 4px 10px; border-radius: 8px; font-weight: 600; font-size: 12px; }
.method-st { background: rgba(37,99,235,0.1); color: var(--primary); }
.method-tfidf { background: rgba(245,158,11,0.1); color: #b45309; }
.empty-cell { text-align: center; color: var(--text-light); padding: 32px !important; }

/* 语义聚类统计 */
.cluster-summary { display: flex; flex-direction: column; gap: 12px; }
.cluster-item { display: grid; grid-template-columns: 80px 1fr 100px; align-items: center; gap: 12px; }
.cluster-name { font-size: 13px; font-weight: 600; color: #374151; }
.cluster-bar-wrap { height: 10px; background: rgba(148,163,184,0.2); border-radius: 5px; overflow: hidden; }
.cluster-bar { height: 100%; background: linear-gradient(90deg, #2563eb, #60a5fa); border-radius: 5px; transition: width 0.8s ease; }
.cluster-info { display: flex; flex-direction: column; align-items: flex-end; font-size: 11px; }
.cluster-count { color: #374151; font-weight: 600; }
.cluster-avg { color: var(--text-light); }

/* 导出区域 */
.export-section { display: flex; justify-content: center; gap: 16px; padding: 20px; }

/* 响应式 */
@media (max-width: 1100px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .charts-row--4 { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 768px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 24px; }
  .hero { flex-direction: column; align-items: flex-start; }
  .cards { grid-template-columns: 1fr 1fr; gap: 10px; }
  .export-section { flex-direction: column; }
  .charts-row--4 { grid-template-columns: 1fr; }
  .topic-cards-grid { grid-template-columns: 1fr; }
}
</style>
