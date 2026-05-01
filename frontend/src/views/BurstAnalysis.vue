<template>
  <div class="page-shell">
    <main class="burst-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">机器学习分析</p>
          <h1>热搜爆发趋势识别</h1>
          <p class="hero-text">
            基于历史排名、热度变化和标题文本特征识别潜在爆发型热搜，并使用 TF-IDF + KMeans 输出主题聚类结果。
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadPageData" :disabled="loadingPage">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            {{ loadingPage ? "刷新中..." : "刷新数据" }}
          </button>
          <button class="btn btn--primary" @click="handleRunBurst" :disabled="runningBurst">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            {{ runningBurst ? "启动中..." : "运行爆发识别" }}
          </button>
          <button class="btn btn--accent" @click="handleRunTopics" :disabled="runningTopics">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            {{ runningTopics ? "启动中..." : "运行主题聚类" }}
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
      <div v-if="runMessage" class="alert alert--info">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        {{ runMessage }}
      </div>
      <div v-if="showSampleWarning" class="alert alert--warning">
        当前仅采集 {{ appSummary.total_batches }} 个批次，趋势分析样本较少，爆发预测结果仅供参考。建议采集 30 个批次以上后重新分析。
      </div>

      <!-- 空状态 -->
      <section v-if="!hasMLData && !loadingPage" class="empty-panel">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        <p>暂无机器学习分析数据，请先运行分析任务。</p>
      </section>

      <!-- 机器学习解释卡片 -->
      <section v-if="mlExplanations.length" class="insight-panel">
        <div class="insight-header">
          <svg class="insight-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          <span>机器学习洞察</span>
        </div>
        <div class="insight-list">
          <div v-for="(text, i) in mlExplanations" :key="i" class="insight-item">
            <span class="insight-num">{{ i + 1 }}</span>
            <span class="insight-text">{{ text }}</span>
          </div>
        </div>
      </section>

      <!-- 爆发趋势图表区：气泡散点图 + 等级环形图 -->
      <section class="panel" v-if="hasMLData">
        <div class="panel-header">
          <div>
            <h2>爆发趋势多维分析</h2>
            <p>气泡散点图展示热度变化率与排名变化的关系，环形图展示爆发等级分布。</p>
          </div>
        </div>
        <div class="chart-grid">
          <div class="chart-panel">
            <div class="chart-label">爆发趋势气泡图</div>
            <div ref="scatterChartRef" class="chart"></div>
          </div>
          <div class="chart-panel">
            <div class="chart-label">爆发等级分布</div>
            <div ref="levelPieRef" class="chart"></div>
          </div>
        </div>
      </section>

      <!-- 爆发趋势 Top20 -->
      <section class="panel" v-if="hasMLData">
        <div class="panel-header">
          <div>
            <h2>爆发趋势 Top20</h2>
            <p>按爆发概率和当前热度排序，展示最可能继续升温的热搜话题。当前数据批次较少时，爆发概率可能偏极端，建议采集更多批次后重新分析。</p>
          </div>
          <div class="export-group">
            <button class="btn btn--sm btn--outline" @click="handleExportCsv" :disabled="exporting">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              CSV
            </button>
            <button class="btn btn--sm btn--outline" @click="handleExportExcel" :disabled="exporting">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
              </svg>
              Excel
            </button>
          </div>
        </div>

        <!-- 双图表区 -->
        <div class="chart-grid chart-grid--sm">
          <div class="chart-panel">
            <div class="chart-label">爆发概率分布</div>
            <div ref="probabilityChartRef" class="chart"></div>
          </div>
          <div class="chart-panel">
            <div class="chart-label">趋势方向占比</div>
            <div ref="trendChartRef" class="chart"></div>
          </div>
        </div>

        <!-- 数据表格 -->
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>关键词</th><th>爆发等级</th><th>爆发概率</th><th>趋势方向</th><th>当前排名</th><th>当前热度</th><th>热度变化率</th><th>排名变化</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in burstTop" :key="`${item.keyword}-${item.predict_date}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td><span class="level-tag" :class="getLevelClass(item.burst_level)">{{ burstLevelText(item.burst_level) }}</span></td>
                <td class="prob-cell">{{ formatPercent(item.burst_probability) }}</td>
                <td><span class="trend-tag" :class="getTrendClass(item.trend_direction)">{{ trendText(item.trend_direction) }}</span></td>
                <td>{{ item.current_rank || "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.current_hot_value) }}</td>
                <td :class="item.hot_value_change_rate >= 0 ? 'change-up' : 'change-down'">{{ formatPercent(item.hot_value_change_rate) }}</td>
                <td :class="item.rank_change > 0 ? 'change-up' : (item.rank_change < 0 ? 'change-down' : '')">{{ item.rank_change > 0 ? '+' : '' }}{{ formatNumber(item.rank_change) }}</td>
              </tr>
              <tr v-if="!burstTop.length"><td colspan="8" class="table-empty">暂无爆发趋势识别结果</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 关键词搜索 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>关键词搜索</h2>
            <p>查询指定关键词的爆发趋势识别结果。</p>
          </div>
          <form class="search-box" @submit.prevent="handleSearch">
            <input
              v-model="searchKeyword"
              type="text"
              placeholder="输入关键词，例如：高考"
              @keydown.enter.prevent="handleSearch"
            />
            <button type="submit" :disabled="searching">{{ searching ? "查询中..." : "查询" }}</button>
          </form>
        </div>
        <!-- 搜索结果提示 -->
        <div v-if="searched && searchResults.length" class="search-tip">
          共找到 <strong>{{ searchResults.length }}</strong> 条结果，关键词：<strong>{{ searchKeyword }}</strong>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>关键词</th>
                <th>爆发等级</th>
                <th>爆发概率</th>
                <th>趋势方向</th>
                <th>当前排名</th>
                <th>当前热度</th>
                <th>热度变化率</th>
                <th>排名变化</th>
                <th>出现次数</th>
                <th>预测日期</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in searchResults" :key="`${item.keyword}-${item.created_at || item.predict_date}`">
                <td class="keyword-cell">{{ item.keyword || "—" }}</td>
                <td><span class="level-tag" :class="getLevelClass(item.burst_level)">{{ burstLevelText(item.burst_level) }}</span></td>
                <td class="prob-cell">{{ formatPercent(item.burst_probability) }}</td>
                <td><span class="trend-tag" :class="getTrendClass(item.trend_direction)">{{ trendText(item.trend_direction) }}</span></td>
                <td>{{ item.current_rank != null ? item.current_rank : "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.current_hot_value) }}</td>
                <td :class="(item.hot_value_change_rate || 0) >= 0 ? 'change-up' : 'change-down'">{{ formatPercent(item.hot_value_change_rate) }}</td>
                <td :class="(item.rank_change || 0) > 0 ? 'change-up' : ((item.rank_change || 0) < 0 ? 'change-down' : '')">
                  {{ (item.rank_change || 0) > 0 ? '+' : '' }}{{ formatNumber(item.rank_change) }}
                </td>
                <td>{{ item.appear_count != null ? item.appear_count : "—" }}</td>
                <td class="date-cell">{{ item.predict_date || item.feature_date || "—" }}</td>
              </tr>
              <tr v-if="searched && !searchResults.length && !searching">
                <td colspan="10" class="table-empty">
                  未查询到关键词「{{ searchKeyword }}」的爆发趋势结果，请先运行爆发识别任务或更换关键词。
                </td>
              </tr>
              <tr v-if="!searched">
                <td colspan="10" class="table-empty table-empty--hint">请输入关键词后点击查询</td>
              </tr>
              <tr v-if="searching">
                <td colspan="10" class="table-empty">查询中，请稍候...</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 主题聚类分析 -->
      <section class="panel" v-if="hasMLData">
        <div class="panel-header">
          <div>
            <h2>主题聚类分析</h2>
            <p>展示 TF-IDF + KMeans 聚类后的主题分布和热搜标题归类结果。</p>
          </div>
          <div class="stat-badge"><span>共 {{ topicClusters.length }} 条数据</span></div>
        </div>
        <div class="chart-box">
          <div ref="topicChartRef" class="chart"></div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>关键词</th><th>主题类别</th><th>TF-IDF 关键词</th><th>热度值</th><th>排名</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in topicClusters" :key="`${item.keyword}-${item.cluster_id}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td><span class="cluster-badge">{{ item.cluster_name }}</span></td>
                <td class="tfidf-cell">{{ item.tfidf_keywords || "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.hot_value) }}</td>
                <td>{{ item.rank_num || "—" }}</td>
              </tr>
              <tr v-if="!topicClusters.length"><td colspan="5" class="table-empty">暂无主题聚类结果</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import {
  exportMlReportCsv, exportMlReportExcel, getBurstTop, getClusterSummary,
  getSummary, getTopicClusters, runBurstPredictionJob, runTopicClusterJob, searchBurstKeyword,
} from "../api/index.js";

const appSummary = ref({ total_batches: 0 });
const burstTop = ref([]);
const topicClusters = ref([]);
const clusterSummary = ref([]);
const searchKeyword = ref("");
const searchResults = ref([]);
const pageError = ref("");
const runMessage = ref("");
const loadingPage = ref(false);
const runningBurst = ref(false);
const runningTopics = ref(false);
const searching = ref(false);
const searched = ref(false);
const exporting = ref(false);

const probabilityChartRef = ref(null);
const trendChartRef = ref(null);
const topicChartRef = ref(null);
const scatterChartRef = ref(null);
const levelPieRef = ref(null);

let probabilityChart = null;
let trendChart = null;
let topicChart = null;
let scatterChart = null;
let levelPieChart = null;

const hasMLData = computed(() => burstTop.value.length > 0 || topicClusters.value.length > 0);
const showSampleWarning = computed(() => {
  const batches = Number(appSummary.value.total_batches || 0);
  return batches > 0 && batches < 30;
});

// ML 洞察
const mlExplanations = computed(() => {
  const items = [];
  const top3 = burstTop.value.slice(0, 3);
  for (const item of top3) {
    const level = burstLevelText(item.burst_level);
    items.push(
      `「${item.keyword}」热度变化率为 ${formatPercent(item.hot_value_change_rate)}，` +
      `当前排名为第 ${item.current_rank} 位，爆发概率为 ${formatPercent(item.burst_probability)}，` +
      `因此被识别为${level}话题。`
    );
  }
  return items;
});

function toNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number : 0;
}

function formatNumber(value) {
  const number = toNumber(value);
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function formatPercent(value) {
  const n = Number(value || 0) * 100;
  if (!Number.isFinite(n)) return "0.0%";
  if (n > 99.9 && n < 100) return "99.9%";
  return `${n.toFixed(1)}%`;
}

function rawPercent(value) {
  const n = Number(value || 0) * 100;
  if (!Number.isFinite(n)) return "0.0000%";
  return `${n.toFixed(4)}%`;
}

function chartPercentValue(value) {
  const n = Number(value || 0) * 100;
  if (!Number.isFinite(n)) return 0;
  if (n > 99.9 && n < 100) return 99.9;
  return Number(n.toFixed(1));
}

function shortLabel(value, maxLength = 8) {
  const text = String(value || "");
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}

function burstLevelText(level) {
  const n = Number(level);
  // 兼容两套映射：0/1/2 和 1/2/3
  if (n === 3 || n === 2) return "高爆发";
  if (n === 2 || n === 1) return "中爆发";
  if (n === 1 || n === 0) return "低爆发";
  return "低爆发";
}

function trendText(direction) {
  // 兼容英文（后端存储值）和中文（部分历史数据）
  const map = { rising: "上升", stable: "平稳", falling: "下降", 上升: "上升", 平稳: "平稳", 下降: "下降" };
  return map[direction] || direction || "平稳";
}

function getLevelClass(level) {
  const n = Number(level);
  if (n >= 2) return "level--burst";
  if (n === 1) return "level--stable";
  return "level--cool";
}

function getTrendClass(direction) {
  // 兼容英文和中文两套 trend_direction 值
  const map = { rising: "trend--up", stable: "trend--flat", falling: "trend--down", 上升: "trend--up", 平稳: "trend--flat", 下降: "trend--down" };
  return map[direction] || "trend--flat";
}

const CLUSTER_COLORS = ["#2563eb", "#06b6d4", "#8b5cf6", "#f59e0b", "#ec4899", "#14b8a6", "#22c55e", "#ef4444"];
const LEVEL_COLORS = { 3: "#ef4444", 2: "#f59e0b", 1: "#3b82f6", 0: "#94a3b8" };

function buildProbabilityChart() {
  if (!probabilityChartRef.value) return;
  if (!probabilityChart) probabilityChart = echarts.init(probabilityChartRef.value);
  const data = burstTop.value.slice(0, 20);
  probabilityChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(params) {
        const item = data[params?.[0]?.dataIndex || 0];
        if (!item) return "";
        return `<div style="font-weight:700;margin-bottom:6px;">${item.keyword}</div>` +
          `<div>爆发概率：${formatPercent(item.burst_probability)}</div>` +
          `<div>原始概率：${rawPercent(item.burst_probability)}</div>` +
          `<div>当前热度：${formatNumber(item.current_hot_value)}</div>` +
          `<div>趋势方向：${trendText(item.trend_direction)}</div>`;
      },
    },
    grid: { left: 52, right: 16, top: 20, bottom: 80 },
    xAxis: {
      type: "category",
      data: data.map((item) => item.keyword),
      axisLabel: { color: "#64748b", rotate: 35, interval: 0, fontSize: 11, formatter: (v) => shortLabel(v) },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
      axisTick: { show: false },
    },
    yAxis: { type: "value", name: "概率", max: 100, axisLabel: { color: "#64748b", fontSize: 11, formatter: "{value}%" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } } },
    series: [{
      name: "爆发概率",
      type: "bar",
      barMaxWidth: 32,
      data: data.map((item) => ({
        value: chartPercentValue(item.burst_probability),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "#2563eb" }, { offset: 1, color: "rgba(37,99,235,0.25)" }]),
          borderRadius: [6, 6, 0, 0],
        },
      })),
    }],
  }, true);
}

function buildTrendChart() {
  if (!trendChartRef.value) return;
  if (!trendChart) trendChart = echarts.init(trendChartRef.value);
  const summary = { rising: 0, stable: 0, falling: 0 };
  burstTop.value.forEach((item) => { summary[item.trend_direction || "stable"] = (summary[item.trend_direction || "stable"] || 0) + 1; });
  trendChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    legend: { bottom: 0, textStyle: { color: "#64748b", fontSize: 12 }, icon: "roundRect" },
    series: [{
      name: "趋势方向",
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "44%"],
      label: { show: false },
      data: [
        { name: "上升", value: summary.rising, itemStyle: { color: "#22c55e" } },
        { name: "平稳", value: summary.stable, itemStyle: { color: "#3b82f6" } },
        { name: "下降", value: summary.falling, itemStyle: { color: "#94a3b8" } },
      ],
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" } },
    }],
  }, true);
}

function buildTopicChart() {
  if (!topicChartRef.value) return;
  if (!topicChart) topicChart = echarts.init(topicChartRef.value);
  topicChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    legend: { top: 0, textStyle: { color: "#64748b", fontSize: 12 }, icon: "roundRect" },
    series: [{
      name: "主题分布",
      type: "pie",
      radius: "62%",
      center: ["50%", "55%"],
      data: clusterSummary.value.map((item, i) => ({ name: item.cluster_name, value: toNumber(item.keyword_count), itemStyle: { color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] } })),
      label: { color: "#374151", fontSize: 12 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" } },
    }],
  }, true);
}

function buildScatterChart() {
  if (!scatterChartRef.value) return;
  if (!scatterChart) scatterChart = echarts.init(scatterChartRef.value);
  const data = burstTop.value.slice(0, 50).map((item) => ({
    name: item.keyword,
    value: [
      toNumber(item.hot_value_change_rate),
      toNumber(item.rank_change),
      toNumber(item.current_hot_value),
    ],
    itemStyle: { color: LEVEL_COLORS[item.burst_level] || "#94a3b8" },
    burst_probability: item.burst_probability,
    trend_direction: item.trend_direction,
    current_rank: item.current_rank,
  }));
  scatterChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(params) {
        const d = params.data;
        return `<div style="font-weight:700;margin-bottom:6px">${d.name}</div>` +
          `<div>热度变化率：${formatPercent(d.value[0])}</div>` +
          `<div>排名变化：${d.value[1] > 0 ? '+' : ''}${d.value[1]}</div>` +
          `<div>当前热度：${formatNumber(d.value[2])}</div>` +
          `<div>爆发概率：${formatPercent(d.burst_probability)}</div>` +
          `<div>原始概率：${rawPercent(d.burst_probability)}</div>` +
          `<div>趋势方向：${trendText(d.trend_direction)}</div>`;
      },
    },
    legend: {
      top: 0,
      data: [{ name: "高爆发", icon: "circle" }, { name: "中爆发", icon: "circle" }, { name: "低爆发", icon: "circle" }],
      textStyle: { color: "#64748b", fontSize: 12 },
    },
    grid: { left: 60, right: 30, top: 40, bottom: 50 },
    xAxis: {
      type: "value",
      name: "热度变化率",
      nameTextStyle: { color: "#64748b", fontSize: 11 },
      axisLabel: { color: "#64748b", fontSize: 11, formatter: (v) => `${(v * 100).toFixed(0)}%` },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
    },
    yAxis: {
      type: "value",
      name: "排名变化",
      nameTextStyle: { color: "#64748b", fontSize: 11 },
      axisLabel: { color: "#64748b", fontSize: 11 },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
    },
    series: [
      {
        name: "高爆发",
        type: "scatter",
        symbolSize: (d) => Math.min(Math.max(Math.sqrt(d[2]) / 30, 8), 40),
        data: data.filter((d) => Number(d.itemStyle.color === LEVEL_COLORS[3] || d.itemStyle.color === LEVEL_COLORS[2])),
        itemStyle: { color: "#ef4444", opacity: 0.85 },
      },
      {
        name: "中爆发",
        type: "scatter",
        symbolSize: (d) => Math.min(Math.max(Math.sqrt(d[2]) / 30, 8), 40),
        data: data.filter((d) => d.itemStyle.color === LEVEL_COLORS[1]),
        itemStyle: { color: "#f59e0b", opacity: 0.85 },
      },
      {
        name: "低爆发",
        type: "scatter",
        symbolSize: (d) => Math.min(Math.max(Math.sqrt(d[2]) / 30, 8), 40),
        data: data.filter((d) => d.itemStyle.color === LEVEL_COLORS[0]),
        itemStyle: { color: "#3b82f6", opacity: 0.85 },
      },
    ],
  }, true);
}

function buildLevelPieChart() {
  if (!levelPieRef.value) return;
  if (!levelPieChart) levelPieChart = echarts.init(levelPieRef.value);
  const counts = { 高爆发: 0, 中爆发: 0, 低爆发: 0 };
  burstTop.value.forEach((item) => {
    const text = burstLevelText(item.burst_level);
    counts[text] = (counts[text] || 0) + 1;
  });
  levelPieChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    legend: { bottom: 0, textStyle: { color: "#64748b", fontSize: 12 }, icon: "roundRect" },
    series: [{
      name: "爆发等级",
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "44%"],
      label: { show: true, color: "#374151", fontSize: 12, formatter: "{b}: {c}" },
      data: [
        { name: "高爆发", value: counts["高爆发"], itemStyle: { color: "#ef4444" } },
        { name: "中爆发", value: counts["中爆发"], itemStyle: { color: "#f59e0b" } },
        { name: "低爆发", value: counts["低爆发"], itemStyle: { color: "#3b82f6" } },
      ],
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" } },
    }],
  }, true);
}

async function loadPageData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    const [burstResponse, topicResponse, summaryResponse, appSummaryResponse] = await Promise.all([
      getBurstTop(50), getTopicClusters(), getClusterSummary(), getSummary(),
    ]);
    burstTop.value = burstResponse.items || [];
    topicClusters.value = topicResponse.items || [];
    clusterSummary.value = summaryResponse.items || [];
    appSummary.value = appSummaryResponse || { total_batches: 0 };
    await nextTick();
    buildProbabilityChart();
    buildTrendChart();
    buildTopicChart();
    buildScatterChart();
    buildLevelPieChart();
  } catch (error) {
    burstTop.value = [];
    topicClusters.value = [];
    clusterSummary.value = [];
    pageError.value = error.message || "机器学习分析数据加载失败，请先执行第四期 SQL 和分析任务";
    await nextTick();
    buildProbabilityChart();
    buildTrendChart();
    buildTopicChart();
    buildScatterChart();
    buildLevelPieChart();
  } finally {
    loadingPage.value = false;
  }
}

async function handleSearch() {
  const keyword = searchKeyword.value.trim();
  if (!keyword) {
    pageError.value = "请输入关键词后再查询";
    searchResults.value = [];
    searched.value = false;
    return;
  }
  searched.value = true;
  searching.value = true;
  pageError.value = "";
  try {
    const response = await searchBurstKeyword(keyword);
    // 兼容两种返回格式：{ items: [...] } 或 { total, items: [...] }
    searchResults.value = response.items || [];
  } catch (error) {
    searchResults.value = [];
    pageError.value = error.message || "关键词爆发趋势查询失败，请检查后端服务";
  } finally {
    searching.value = false;
  }
}

async function handleRunBurst() {
  runningBurst.value = true;
  try {
    const response = await runBurstPredictionJob();
    runMessage.value = response.message || "机器学习爆发趋势识别任务已启动";
    setTimeout(loadPageData, 1800);
  } catch (error) {
    runMessage.value = error.message || "任务启动失败，请在命令行运行 python ml/predict_job.py";
  } finally { runningBurst.value = false; }
}

async function handleRunTopics() {
  runningTopics.value = true;
  try {
    const response = await runTopicClusterJob();
    runMessage.value = response.message || "主题聚类分析任务已启动";
    setTimeout(loadPageData, 1800);
  } catch (error) {
    runMessage.value = error.message || "任务启动失败，请在命令行运行 python ml/topic_cluster.py";
  } finally { runningTopics.value = false; }
}

async function handleExportCsv() { await exportReport(exportMlReportCsv, "微博热搜机器学习分析报告.csv"); }
async function handleExportExcel() { await exportReport(exportMlReportExcel, "微博热搜机器学习分析报告.xlsx"); }

async function exportReport(exporter, defaultFilename) {
  exporting.value = true;
  try {
    const { blob, filename } = await exporter();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || defaultFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) { pageError.value = error.message || "报告导出失败"; }
  finally { exporting.value = false; }
}

function handleResize() {
  [probabilityChart, trendChart, topicChart, scatterChart, levelPieChart].forEach((c) => c?.resize());
}

onMounted(async () => {
  await loadPageData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [probabilityChart, trendChart, topicChart, scatterChart, levelPieChart].forEach((c) => { if (c) c.dispose(); });
  probabilityChart = null; trendChart = null; topicChart = null; scatterChart = null; levelPieChart = null;
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.burst-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }

/* Hero */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 52px rgba(37,99,235,0.2), 0 1px 0 rgba(255,255,255,0.1) inset; position: relative; overflow: hidden; }
.hero::before { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08), transparent 50%); pointer-events: none; }
.eyebrow { margin: 0 0 8px; font-size: 13px; letter-spacing: 0.16em; font-weight: 600; color: rgba(255,255,255,0.7); text-transform: uppercase; }
h1 { margin: 0; font-size: 36px; font-weight: 800; line-height: 1.15; color: #fff; letter-spacing: -0.02em; }
h2 { margin: 0 0 5px; font-size: 20px; font-weight: 700; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 680px; line-height: 1.7; color: rgba(255,255,255,0.75); }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; flex-shrink: 0; }

/* 按钮 */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 11px 20px; border: none; border-radius: var(--radius-btn); font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; white-space: nowrap; }
.btn--sm { padding: 7px 14px; font-size: 13px; }
.btn-icon { width: 16px; height: 16px; flex-shrink: 0; }
.btn--primary { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; box-shadow: 0 4px 14px rgba(37,99,235,0.3); }
.btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(37,99,235,0.35); }
.btn--accent { background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: #fff; box-shadow: 0 4px 14px rgba(139,92,246,0.3); }
.btn--accent:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(139,92,246,0.35); }
.btn--outline { background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(4px); }
.btn--outline:hover:not(:disabled) { background: rgba(255,255,255,0.25); transform: translateY(-1px); }
.btn:disabled { opacity: 0.65; cursor: not-allowed; transform: none !important; }

/* 提示栏 */
.alert { display: flex; align-items: center; gap: 8px; padding: 12px 18px; border-radius: 12px; font-size: 14px; font-weight: 500; }
.alert-icon { width: 18px; height: 18px; flex-shrink: 0; }
.alert--error { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); color: #dc2626; }
.alert--info { background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.15); color: #16a34a; }
.alert--warning { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); color: #b45309; }

/* 面板 */
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 20px; }
.stat-badge { padding: 5px 14px; border-radius: 20px; background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.2); color: var(--primary); font-size: 13px; font-weight: 600; flex-shrink: 0; }
.export-group { display: flex; gap: 8px; }

/* 洞察面板 */
.insight-panel { padding: 20px 24px; border-radius: var(--radius-card); background: linear-gradient(135deg, rgba(37,99,235,0.04), rgba(6,182,212,0.04)); border: 1px solid rgba(37,99,235,0.12); box-shadow: var(--shadow-card); }
.insight-header { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 12px; }
.insight-icon { width: 18px; height: 18px; }
.insight-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 10px 24px; }
.insight-item { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: var(--text-base); line-height: 1.6; }
.insight-num { width: 20px; height: 20px; border-radius: 50%; background: var(--primary); color: #fff; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px; }
.insight-text { flex: 1; }

/* 图表 */
.chart-grid { display: grid; grid-template-columns: 3fr 2fr; gap: 18px; margin-bottom: 20px; }
.chart-grid--sm { grid-template-columns: 1fr 1fr; }
.chart-panel { display: flex; flex-direction: column; min-height: 320px; }
.chart-label { font-size: 12px; font-weight: 600; color: var(--text-muted); letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 8px; }
.chart-box { min-height: 300px; margin-bottom: 8px; }
.chart { width: 100%; flex: 1; height: 320px; }

/* 空状态 */
.empty-panel { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px 24px; border-radius: 20px; background: rgba(255,255,255,0.75); border: 1.5px dashed rgba(148,163,184,0.4); color: var(--text-muted); font-size: 14px; }
.empty-icon { width: 48px; height: 48px; color: var(--text-light); }

/* 搜索框 */
.search-box { display: flex; gap: 10px; flex-shrink: 0; }
.search-box input { width: 280px; padding: 10px 16px; border-radius: var(--radius-btn); border: 1.5px solid #cbd5e1; background: #fff; font-size: 14px; color: var(--text-base); outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
.search-box input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
.search-box button { padding: 10px 20px; border: none; border-radius: var(--radius-btn); background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }
.search-box button:hover:not(:disabled) { transform: translateY(-1px); }
.search-box button:disabled { opacity: 0.65; cursor: not-allowed; }
.search-tip { margin-bottom: 12px; font-size: 13px; color: var(--text-muted); padding: 8px 12px; background: rgba(37,99,235,0.04); border-radius: 8px; border: 1px solid rgba(37,99,235,0.1); }

/* 表格 */
.table-wrap { width: 100%; overflow-x: auto; margin-top: 4px; }
.data-table { width: 100%; border-collapse: collapse; min-width: 860px; }
.data-table th, .data-table td { padding: 11px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.data-table th { color: #475569; font-weight: 700; background: rgba(241,245,249,0.8); font-size: 13px; }
.data-table tbody tr:hover { background: rgba(239,246,255,0.7); }
.keyword-cell { max-width: 240px; color: var(--navy); font-weight: 600; word-break: break-all; }
.date-cell { font-variant-numeric: tabular-nums; color: #374151; }
.prob-cell { font-weight: 700; color: var(--primary); font-variant-numeric: tabular-nums; }
.heat-cell { color: #06b6d4; font-weight: 600; }
.change-up { color: #16a34a; font-weight: 600; }
.change-down { color: #dc2626; font-weight: 600; }
.tfidf-cell { max-width: 200px; font-size: 12px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-empty { text-align: center; color: var(--text-light); padding: 32px; }
.table-empty--hint { color: #c4c9d4; font-size: 13px; }

/* 标签 */
.level-tag { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; }
.level--burst { background: rgba(239,68,68,0.1); color: #dc2626; border: 1px solid rgba(239,68,68,0.25); }
.level--stable { background: rgba(245,158,11,0.1); color: #b45309; border: 1px solid rgba(245,158,11,0.25); }
.level--cool { background: rgba(37,99,235,0.1); color: var(--primary); border: 1px solid rgba(37,99,235,0.25); }
.trend-tag { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.trend--up { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.2); }
.trend--flat { background: rgba(100,116,139,0.08); color: #475569; border: 1px solid rgba(100,116,139,0.2); }
.trend--down { background: rgba(220,38,38,0.08); color: #b91c1c; border: 1px solid rgba(220,38,38,0.2); }
.cluster-badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; background: rgba(139,92,246,0.08); color: #7c3aed; border: 1px solid rgba(139,92,246,0.2); }

/* 响应式 */
@media (max-width: 1100px) {
  .chart-grid { grid-template-columns: 1fr; }
  .chart-grid--sm { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .hero { flex-direction: column; align-items: flex-start; }
  .hero-actions { width: 100%; }
  .panel-header { flex-direction: column; align-items: flex-start; }
  .search-box { width: 100%; }
  .search-box input { flex: 1; width: auto; }
}
@media (max-width: 640px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 26px; }
  .chart { height: 260px; }
  .chart-panel { min-height: 260px; }
  .chart-box { min-height: 260px; }
}
</style>
