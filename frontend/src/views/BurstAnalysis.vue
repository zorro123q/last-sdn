<template>
  <div class="page-shell">
    <main class="burst-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">🚀 机器学习分析</p>
          <h1>热搜爆发趋势识别</h1>
          <p class="hero-text">
            基于历史排名、热度变化和标题文本特征识别潜在爆发型热搜，并使用 TF-IDF + KMeans 输出主题聚类结果。
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadPageData" :disabled="loadingPage">
            <span class="btn-icon">↻</span>{{ loadingPage ? "刷新中..." : "刷新数据" }}
          </button>
          <button class="btn btn--primary" @click="handleRunBurst" :disabled="runningBurst">
            <span class="btn-icon">▶</span>{{ runningBurst ? "启动中..." : "运行爆发识别" }}
          </button>
          <button class="btn btn--accent" @click="handleRunTopics" :disabled="runningTopics">
            <span class="btn-icon">◈</span>{{ runningTopics ? "启动中..." : "运行主题聚类" }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">⚠️ {{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">✅ {{ runMessage }}</div>

      <!-- 空状态 -->
      <section v-if="!hasMLData && !loadingPage" class="empty-panel">
        <span class="empty-icon">🤖</span>
        <p>暂无机器学习分析数据，请先运行分析任务。</p>
      </section>

      <!-- 爆发趋势 Top20 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>爆发趋势 Top20</h2>
            <p>按爆发概率和当前热度排序，展示最可能继续升温的热搜话题。</p>
          </div>
          <div class="export-group">
            <button class="btn btn--sm btn--outline" @click="handleExportCsv" :disabled="exporting">
              ↓ CSV
            </button>
            <button class="btn btn--sm btn--outline" @click="handleExportExcel" :disabled="exporting">
              ↓ Excel
            </button>
          </div>
        </div>

        <!-- 双图表区 -->
        <div class="chart-grid">
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
              <tr>
                <th>关键词</th>
                <th>爆发等级</th>
                <th>爆发概率</th>
                <th>趋势方向</th>
                <th>当前排名</th>
                <th>当前热度</th>
                <th>热度变化率</th>
                <th>排名变化</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in burstTop" :key="`${item.keyword}-${item.predict_date}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td>
                  <span class="level-tag" :class="getLevelClass(item.burst_level)">
                    {{ burstLevelText(item.burst_level) }}
                  </span>
                </td>
                <td class="prob-cell">{{ formatPercent(item.burst_probability) }}</td>
                <td>
                  <span class="trend-tag" :class="getTrendClass(item.trend_direction)">
                    {{ trendText(item.trend_direction) }}
                  </span>
                </td>
                <td>{{ item.current_rank || "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.current_hot_value) }}</td>
                <td :class="item.hot_value_change_rate >= 0 ? 'change-up' : 'change-down'">
                  {{ formatPercent(item.hot_value_change_rate) }}
                </td>
                <td :class="item.rank_change > 0 ? 'change-up' : (item.rank_change < 0 ? 'change-down' : '')">
                  {{ item.rank_change > 0 ? '+' : '' }}{{ formatNumber(item.rank_change) }}
                </td>
              </tr>
              <tr v-if="!burstTop.length">
                <td colspan="8" class="table-empty">暂无爆发趋势识别结果</td>
              </tr>
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
            <input v-model="searchKeyword" type="text" placeholder="输入关键词，例如：高考" />
            <button type="submit" :disabled="searching">
              {{ searching ? "查询中..." : "查询" }}
            </button>
          </form>
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
                <th>预测日期</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in searchResults" :key="`${item.keyword}-${item.created_at}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td>
                  <span class="level-tag" :class="getLevelClass(item.burst_level)">
                    {{ burstLevelText(item.burst_level) }}
                  </span>
                </td>
                <td class="prob-cell">{{ formatPercent(item.burst_probability) }}</td>
                <td>
                  <span class="trend-tag" :class="getTrendClass(item.trend_direction)">
                    {{ trendText(item.trend_direction) }}
                  </span>
                </td>
                <td>{{ item.current_rank || "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.current_hot_value) }}</td>
                <td class="date-cell">{{ item.predict_date || "—" }}</td>
              </tr>
              <tr v-if="searched && !searchResults.length">
                <td colspan="7" class="table-empty">未查询到该关键词的爆发趋势结果</td>
              </tr>
              <tr v-if="!searched">
                <td colspan="7" class="table-empty table-empty--hint">请输入关键词后点击查询</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 主题聚类分析 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>主题聚类分析</h2>
            <p>展示 TF-IDF + KMeans 聚类后的主题分布和热搜标题归类结果。</p>
          </div>
          <div class="stat-badge">
            <span>共 {{ topicClusters.length }} 条数据</span>
          </div>
        </div>

        <div class="chart-box">
          <div ref="topicChartRef" class="chart"></div>
        </div>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>关键词</th>
                <th>主题类别</th>
                <th>TF-IDF 关键词</th>
                <th>热度值</th>
                <th>排名</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in topicClusters" :key="`${item.keyword}-${item.cluster_id}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td>
                  <span class="cluster-badge">{{ item.cluster_name }}</span>
                </td>
                <td class="tfidf-cell">{{ item.tfidf_keywords || "—" }}</td>
                <td class="heat-cell">{{ formatNumber(item.hot_value) }}</td>
                <td>{{ item.rank_num || "—" }}</td>
              </tr>
              <tr v-if="!topicClusters.length">
                <td colspan="5" class="table-empty">暂无主题聚类结果</td>
              </tr>
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
  exportMlReportCsv,
  exportMlReportExcel,
  getBurstTop,
  getClusterSummary,
  getTopicClusters,
  runBurstPredictionJob,
  runTopicClusterJob,
  searchBurstKeyword,
} from "../api/index.js";

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

let probabilityChart = null;
let trendChart = null;
let topicChart = null;

const hasMLData = computed(
  () => burstTop.value.length > 0 || topicClusters.value.length > 0
);

function toNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number : 0;
}

function formatNumber(value) {
  const number = toNumber(value);
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function formatPercent(value) {
  const number = toNumber(value);
  return `${(number * 100).toFixed(1)}%`;
}

function shortLabel(value, maxLength = 8) {
  const text = String(value || "");
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}

function burstLevelText(level) {
  return { 2: "爆发型", 1: "稳定型", 0: "降温型" }[Number(level)] || "稳定型";
}

function trendText(direction) {
  return { rising: "↑ 上升", stable: "→ 平稳", falling: "↓ 下降" }[direction] || "→ 平稳";
}

function getLevelClass(level) {
  return { 2: "level--burst", 1: "level--stable", 0: "level--cool" }[Number(level)] || "level--stable";
}

function getTrendClass(direction) {
  return { rising: "trend--up", stable: "trend--flat", falling: "trend--down" }[direction] || "trend--flat";
}

const CLUSTER_COLORS = ["#e4572e", "#2a9d8f", "#3f72af", "#f2a541", "#7c3aed", "#0891b2", "#16a34a", "#dc2626"];

function buildProbabilityChart() {
  if (!probabilityChartRef.value) return;
  if (!probabilityChart) probabilityChart = echarts.init(probabilityChartRef.value);

  const data = burstTop.value.slice(0, 20);
  probabilityChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(params) {
        const item = data[params?.[0]?.dataIndex || 0];
        if (!item) return "";
        return `<div style="font-weight:700;margin-bottom:6px;">${item.keyword}</div>
          <div>爆发概率：${formatPercent(item.burst_probability)}</div>
          <div>当前热度：${formatNumber(item.current_hot_value)}</div>
          <div>趋势方向：${trendText(item.trend_direction)}</div>`;
      },
    },
    grid: { left: 52, right: 16, top: 20, bottom: 80 },
    xAxis: {
      type: "category",
      data: data.map((item) => item.keyword),
      axisLabel: { color: "#5b6475", rotate: 35, interval: 0, fontSize: 11, formatter: (v) => shortLabel(v) },
      axisLine: { lineStyle: { color: "rgba(157,176,208,0.4)" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      name: "概率",
      max: 100,
      axisLabel: { color: "#5b6475", fontSize: 11, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "rgba(157,176,208,0.15)", type: "dashed" } },
    },
    series: [
      {
        name: "爆发概率",
        type: "bar",
        barMaxWidth: 32,
        data: data.map((item, i) => ({
          value: Number((toNumber(item.burst_probability) * 100).toFixed(1)),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "#e4572e" },
              { offset: 1, color: "rgba(228,87,46,0.25)" },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
        })),
      },
    ],
  }, true);
}

function buildTrendChart() {
  if (!trendChartRef.value) return;
  if (!trendChart) trendChart = echarts.init(trendChartRef.value);

  const summary = { rising: 0, stable: 0, falling: 0 };
  burstTop.value.forEach((item) => {
    const key = item.trend_direction || "stable";
    summary[key] = (summary[key] || 0) + 1;
  });

  trendChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: {
      bottom: 0,
      textStyle: { color: "#5b6475", fontSize: 12 },
      icon: "roundRect",
    },
    series: [
      {
        name: "趋势方向",
        type: "pie",
        radius: ["42%", "68%"],
        center: ["50%", "44%"],
        label: { show: false },
        data: [
          { name: "上升", value: summary.rising, itemStyle: { color: "#2a9d8f" } },
          { name: "平稳", value: summary.stable, itemStyle: { color: "#3f72af" } },
          { name: "下降", value: summary.falling, itemStyle: { color: "#e4572e" } },
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(0,0,0,0.2)",
          },
        },
      },
    ],
  }, true);
}

function buildTopicChart() {
  if (!topicChartRef.value) return;
  if (!topicChart) topicChart = echarts.init(topicChartRef.value);

  topicChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: {
      top: 0,
      textStyle: { color: "#5b6475", fontSize: 12 },
      icon: "roundRect",
    },
    series: [
      {
        name: "主题分布",
        type: "pie",
        radius: "62%",
        center: ["50%", "55%"],
        data: clusterSummary.value.map((item, i) => ({
          name: item.cluster_name,
          value: toNumber(item.keyword_count),
          itemStyle: { color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] },
        })),
        label: {
          color: "#374151",
          fontSize: 12,
        },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" },
        },
      },
    ],
  }, true);
}

async function loadPageData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    const [burstResponse, topicResponse, summaryResponse] = await Promise.all([
      getBurstTop(20),
      getTopicClusters(),
      getClusterSummary(),
    ]);
    burstTop.value = burstResponse.items || [];
    topicClusters.value = topicResponse.items || [];
    clusterSummary.value = summaryResponse.items || [];
    await nextTick();
    buildProbabilityChart();
    buildTrendChart();
    buildTopicChart();
  } catch (error) {
    burstTop.value = [];
    topicClusters.value = [];
    clusterSummary.value = [];
    pageError.value = error.message || "机器学习分析数据加载失败，请先执行第四期 SQL 和分析任务";
    await nextTick();
    buildProbabilityChart();
    buildTrendChart();
    buildTopicChart();
  } finally {
    loadingPage.value = false;
  }
}

async function handleSearch() {
  const keyword = searchKeyword.value.trim();
  searched.value = true;
  if (!keyword) {
    searchResults.value = [];
    pageError.value = "关键词不能为空";
    return;
  }
  searching.value = true;
  try {
    pageError.value = "";
    const response = await searchBurstKeyword(keyword);
    searchResults.value = response.items || [];
  } catch (error) {
    searchResults.value = [];
    pageError.value = error.message || "关键词爆发趋势查询失败";
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
  } finally {
    runningBurst.value = false;
  }
}

async function handleRunTopics() {
  runningTopics.value = true;
  try {
    const response = await runTopicClusterJob();
    runMessage.value = response.message || "主题聚类分析任务已启动";
    setTimeout(loadPageData, 1800);
  } catch (error) {
    runMessage.value = error.message || "任务启动失败，请在命令行运行 python ml/topic_cluster.py";
  } finally {
    runningTopics.value = false;
  }
}

async function handleExportCsv() {
  await exportReport(exportMlReportCsv, "微博热搜机器学习分析报告.csv");
}

async function handleExportExcel() {
  await exportReport(exportMlReportExcel, "微博热搜机器学习分析报告.xlsx");
}

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
  } catch (error) {
    pageError.value = error.message || "报告导出失败";
  } finally {
    exporting.value = false;
  }
}

function handleResize() {
  [probabilityChart, trendChart, topicChart].forEach((c) => c?.resize());
}

onMounted(async () => {
  await loadPageData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [probabilityChart, trendChart, topicChart].forEach((c) => {
    if (c) c.dispose();
  });
  probabilityChart = null;
  trendChart = null;
  topicChart = null;
});
</script>

<style scoped>
.page-shell {
  min-height: calc(100vh - 64px);
  padding: 28px 20px 48px;
}

.burst-page {
  max-width: 1320px;
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
  box-shadow: 0 20px 52px rgba(82,100,128,0.11), 0 1px 0 rgba(255,255,255,0.8) inset;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #e4572e, #f2a541, #7c3aed, #2a9d8f);
  border-radius: 24px 24px 0 0;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.16em;
  font-weight: 600;
  color: #e4572e;
}

h1 {
  margin: 0;
  font-size: 36px;
  font-weight: 800;
  line-height: 1.15;
  color: #0f172a;
  letter-spacing: -0.02em;
}

h2 {
  margin: 0 0 5px;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

p {
  margin: 0;
  color: #5b6475;
  font-size: 14px;
}

.hero-text {
  margin-top: 10px;
  max-width: 680px;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  flex-shrink: 0;
}

/* ===================== 按钮 ===================== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 20px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn--sm {
  padding: 7px 14px;
  font-size: 13px;
}

.btn-icon {
  font-size: 14px;
}

.btn--primary {
  background: linear-gradient(135deg, #e4572e, #f4723e);
  color: #fff;
  box-shadow: 0 4px 14px rgba(228,87,46,0.35);
}

.btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(228,87,46,0.4);
}

.btn--accent {
  background: linear-gradient(135deg, #7c3aed, #9f67fa);
  color: #fff;
  box-shadow: 0 4px 14px rgba(124,58,237,0.3);
}

.btn--accent:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(124,58,237,0.38);
}

.btn--outline {
  background: #fff;
  color: #16324f;
  border: 1.5px solid rgba(157,176,208,0.55);
  box-shadow: 0 2px 8px rgba(82,100,128,0.06);
}

.btn--outline:hover:not(:disabled) {
  border-color: #aec4e8;
  background: rgba(241,247,255,0.9);
  transform: translateY(-1px);
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none !important;
}

/* ===================== 提示栏 ===================== */
.alert {
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.alert--error {
  background: rgba(180,35,24,0.07);
  border: 1px solid rgba(180,35,24,0.2);
  color: #b42318;
}

.alert--info {
  background: rgba(42,157,143,0.08);
  border: 1px solid rgba(42,157,143,0.25);
  color: #1d6b5e;
}

/* ===================== 面板 ===================== */
.panel {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(157,176,208,0.25);
  box-shadow: 0 12px 32px rgba(82,100,128,0.08);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-badge {
  padding: 5px 14px;
  border-radius: 20px;
  background: rgba(228,87,46,0.07);
  border: 1px solid rgba(228,87,46,0.2);
  color: #c23d1a;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.export-group {
  display: flex;
  gap: 8px;
}

/* ===================== 图表 ===================== */
.chart-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 18px;
  margin-bottom: 20px;
}

.chart-panel {
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.chart-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.chart-box {
  min-height: 300px;
  margin-bottom: 8px;
}

.chart {
  width: 100%;
  flex: 1;
  height: 300px;
}

/* ===================== 空状态 ===================== */
.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  border-radius: 20px;
  background: rgba(255,255,255,0.75);
  border: 1.5px dashed rgba(157,176,208,0.4);
  color: #6b7280;
  font-size: 14px;
}

.empty-icon {
  font-size: 36px;
  opacity: 0.55;
}

/* ===================== 搜索框 ===================== */
.search-box {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.search-box input {
  width: 280px;
  padding: 10px 16px;
  border-radius: 12px;
  border: 1.5px solid #cdd7ea;
  background: #fff;
  font-size: 14px;
  color: #1f2937;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box input:focus {
  border-color: #e4572e;
  box-shadow: 0 0 0 3px rgba(228,87,46,0.1);
}

.search-box button {
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #e4572e, #f4723e);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(228,87,46,0.3);
}

.search-box button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.search-box button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* ===================== 表格 ===================== */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  margin-top: 4px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 860px;
}

.data-table th,
.data-table td {
  padding: 11px 14px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  font-size: 14px;
}

.data-table th {
  color: #475569;
  font-weight: 700;
  background: rgba(241,245,249,0.8);
  font-size: 13px;
}

.data-table tbody tr:hover {
  background: rgba(239,246,255,0.7);
}

.keyword-cell {
  max-width: 240px;
  color: #0f172a;
  font-weight: 600;
  word-break: break-all;
}

.date-cell {
  font-variant-numeric: tabular-nums;
  color: #374151;
}

.prob-cell {
  font-weight: 700;
  color: #e4572e;
  font-variant-numeric: tabular-nums;
}

.heat-cell {
  color: #2a9d8f;
  font-weight: 600;
}

.change-up {
  color: #16a34a;
  font-weight: 600;
}

.change-down {
  color: #dc2626;
  font-weight: 600;
}

.tfidf-cell {
  max-width: 200px;
  font-size: 12px;
  color: #5b6475;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-empty {
  text-align: center;
  color: #9ca3af;
  padding: 32px;
}

.table-empty--hint {
  color: #c4c9d4;
  font-size: 13px;
}

/* ===================== 标签 ===================== */
.level-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

.level--burst {
  background: rgba(228,87,46,0.1);
  color: #c23d1a;
  border: 1px solid rgba(228,87,46,0.25);
}

.level--stable {
  background: rgba(63,114,175,0.1);
  color: #274c77;
  border: 1px solid rgba(63,114,175,0.25);
}

.level--cool {
  background: rgba(42,157,143,0.1);
  color: #1d6b5e;
  border: 1px solid rgba(42,157,143,0.25);
}

.trend-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.trend--up {
  background: rgba(22,163,74,0.08);
  color: #15803d;
  border: 1px solid rgba(22,163,74,0.2);
}

.trend--flat {
  background: rgba(100,116,139,0.08);
  color: #475569;
  border: 1px solid rgba(100,116,139,0.2);
}

.trend--down {
  background: rgba(220,38,38,0.08);
  color: #b91c1c;
  border: 1px solid rgba(220,38,38,0.2);
}

.cluster-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(124,58,237,0.08);
  color: #6d28d9;
  border: 1px solid rgba(124,58,237,0.2);
}

/* ===================== 响应式 ===================== */
@media (max-width: 1100px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-actions {
    width: 100%;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-box {
    width: 100%;
  }

  .search-box input {
    flex: 1;
    width: auto;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding: 18px 12px 36px;
  }

  h1 { font-size: 26px; }

  .chart { height: 260px; }
  .chart-panel { min-height: 260px; }
  .chart-box { min-height: 260px; }
}
</style>
