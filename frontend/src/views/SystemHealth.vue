<template>
  <div class="page-shell">
    <main class="v6-page">
      <section class="hero hero--health">
        <div>
          <p class="eyebrow">System Observability</p>
          <h1>系统运行监控</h1>
          <p class="hero-text">监控采集批次、数据完整性、重复标题、分析任务状态和模型结果状态，支撑可观测的数据分析平台。</p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadData" :disabled="loading">{{ loading ? "刷新中..." : "刷新数据" }}</button>
          <button class="btn btn--primary" @click="handleRun" :disabled="running">{{ running ? "检查中..." : "运行健康检查" }}</button>
        </div>
      </section>

      <div v-if="pageError" class="alert alert--error">{{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">{{ runMessage }}</div>

      <section class="stat-grid">
        <article v-for="item in statCards" :key="item.key" class="stat-card">
          <span class="stat-label">{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </section>

      <section class="content-grid">
        <article class="panel">
          <div class="panel-header">
            <div>
              <h2>健康分数</h2>
              <p>综合采集时效、空热度、重复标题、分析状态和模型状态计算。</p>
            </div>
          </div>
          <div class="score-block">
            <div class="score-ring" :style="{ '--score': `${healthScore}%` }">
              <strong>{{ healthScore }}</strong>
              <span>分</span>
            </div>
            <div class="progress-track">
              <div class="progress-bar" :style="{ width: `${healthScore}%` }"></div>
            </div>
          </div>
          <div class="issue-grid">
            <div class="issue-item">
              <span>空热度记录数</span>
              <strong>{{ formatNumber(health.null_hot_value_count) }}</strong>
            </div>
            <div class="issue-item">
              <span>重复标题数量</span>
              <strong>{{ formatNumber(health.duplicate_title_count) }}</strong>
            </div>
            <div class="issue-item">
              <span>采集状态</span>
              <strong :class="statusClass(health.collector_status)">{{ statusText(health.collector_status) }}</strong>
            </div>
            <div class="issue-item">
              <span>分析状态</span>
              <strong :class="statusClass(health.analysis_status)">{{ statusText(health.analysis_status) }}</strong>
            </div>
            <div class="issue-item">
              <span>模型状态</span>
              <strong :class="statusClass(health.ml_status)">{{ statusText(health.ml_status) }}</strong>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="panel-header">
            <div>
              <h2>最近采集趋势</h2>
              <p>复用每日统计结果展示记录量和关键词数量变化。</p>
            </div>
          </div>
          <div ref="trendChartRef" class="chart"></div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { getDailyStats, getSystemHealthSummary, runSystemHealthCheck } from "../api/index.js";

const health = ref({});
const dailyStats = ref([]);
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const runMessage = ref("");
const trendChartRef = ref(null);

let trendChart = null;

const healthScore = computed(() => {
  const score = Number(health.value.health_score || 0);
  if (!Number.isFinite(score)) return 0;
  return Math.max(0, Math.min(100, Math.round(score)));
});

const statCards = computed(() => [
  { key: "total_raw_records", label: "原始记录数", value: formatNumber(health.value.total_raw_records) },
  { key: "total_batches", label: "采集批次数", value: formatNumber(health.value.total_batches) },
  { key: "total_keywords", label: "关键词数量", value: formatNumber(health.value.total_keywords) },
  { key: "latest_fetch_time", label: "最新采集时间", value: health.value.latest_fetch_time || "-" },
  { key: "latest_batch_count", label: "最新批次数量", value: formatNumber(health.value.latest_batch_count) },
  { key: "health_score", label: "健康分数", value: `${healthScore.value} 分` },
]);

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function statusText(status) {
  const map = {
    healthy: "正常",
    stale: "滞后",
    empty: "无数据",
    unknown: "未知",
  };
  return map[status] || status || "未知";
}

function statusClass(status) {
  if (status === "healthy") return "status-ok";
  if (status === "stale") return "status-warn";
  if (status === "empty") return "status-bad";
  return "status-muted";
}

function buildTrendChart() {
  if (!trendChartRef.value) return;
  if (!trendChart) trendChart = echarts.init(trendChartRef.value);
  const data = dailyStats.value.slice(-14);
  trendChart.setOption({
    tooltip: { trigger: "axis", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "transparent", textStyle: { color: "#fff" } },
    legend: { top: 0, textStyle: { color: "#64748b" } },
    grid: { left: 54, right: 52, top: 46, bottom: 40 },
    xAxis: { type: "category", data: data.map((item) => item.stat_date?.slice(5) || item.stat_date), axisLabel: { color: "#64748b" } },
    yAxis: [
      { type: "value", name: "记录数", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.18)", type: "dashed" } } },
      { type: "value", name: "关键词", axisLabel: { color: "#64748b" }, splitLine: { show: false } },
    ],
    series: [
      {
        name: "原始记录数",
        type: "bar",
        data: data.map((item) => Number(item.total_records || 0)),
        barMaxWidth: 30,
        itemStyle: { color: "#2563eb", borderRadius: [6, 6, 0, 0] },
      },
      {
        name: "关键词数量",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        data: data.map((item) => Number(item.total_keywords || 0)),
        lineStyle: { width: 3, color: "#14b8a6" },
        itemStyle: { color: "#14b8a6" },
      },
    ],
  }, true);
}

async function loadData() {
  loading.value = true;
  pageError.value = "";
  try {
    const [healthResponse, dailyResponse] = await Promise.all([
      getSystemHealthSummary(),
      getDailyStats(),
    ]);
    health.value = healthResponse || {};
    dailyStats.value = dailyResponse.items || [];
    await nextTick();
    buildTrendChart();
  } catch (error) {
    health.value = {};
    dailyStats.value = [];
    pageError.value = error.message || "系统监控数据加载失败";
    await nextTick();
    buildTrendChart();
  } finally {
    loading.value = false;
  }
}

async function handleRun() {
  running.value = true;
  try {
    const response = await runSystemHealthCheck();
    runMessage.value = response.message || "数据质量检查已完成";
    await loadData();
  } catch (error) {
    pageError.value = error.message || "数据质量检查失败";
  } finally {
    running.value = false;
  }
}

function handleResize() {
  trendChart?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  trendChart?.dispose();
  trendChart = null;
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.v6-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); color: #fff; box-shadow: var(--shadow-hero); }
.hero--health { background: linear-gradient(135deg, #0f766e, #1e40af); }
.eyebrow { margin: 0 0 8px; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.74); }
h1 { margin: 0; font-size: 34px; line-height: 1.15; }
h2 { margin: 0 0 6px; font-size: 20px; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 740px; color: rgba(255,255,255,0.8); line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { border: none; border-radius: var(--radius-btn); padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--primary { background: #fff; color: #0f766e; }
.btn--outline { background: rgba(255,255,255,0.14); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.alert { padding: 12px 16px; border-radius: 12px; font-size: 14px; }
.alert--error { background: rgba(239,68,68,0.08); color: #dc2626; border: 1px solid rgba(239,68,68,0.18); }
.alert--info { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.18); }
.stat-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; }
.stat-card { padding: 18px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.stat-label { display: block; color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }
.stat-card strong { display: block; font-size: 22px; color: var(--navy); word-break: break-all; }
.content-grid { display: grid; grid-template-columns: 0.82fr 1.18fr; gap: 24px; align-items: stretch; }
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { margin-bottom: 18px; }
.score-block { display: grid; gap: 18px; justify-items: center; margin: 10px 0 22px; }
.score-ring { --score: 0%; width: 150px; height: 150px; border-radius: 50%; display: grid; place-items: center; background: conic-gradient(#14b8a6 var(--score), #e2e8f0 0); position: relative; }
.score-ring::after { content: ""; position: absolute; inset: 14px; border-radius: 50%; background: #fff; }
.score-ring strong, .score-ring span { position: relative; z-index: 1; }
.score-ring strong { font-size: 38px; color: var(--navy); }
.score-ring span { margin-top: 42px; color: #64748b; font-size: 13px; }
.progress-track { width: 100%; height: 10px; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
.progress-bar { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #14b8a6, #2563eb); transition: width 0.3s ease; }
.issue-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.issue-item { padding: 13px; border-radius: 12px; background: #fff; border: 1px solid #e2e8f0; }
.issue-item span { display: block; color: #64748b; font-size: 12px; margin-bottom: 6px; }
.issue-item strong { color: var(--navy); }
.status-ok { color: #15803d !important; }
.status-warn { color: #b45309 !important; }
.status-bad { color: #dc2626 !important; }
.status-muted { color: #64748b !important; }
.chart { height: 430px; width: 100%; }
@media (max-width: 1120px) { .stat-grid { grid-template-columns: repeat(3, 1fr); } .content-grid { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .page-shell { padding: 16px 12px 36px; } .hero { flex-direction: column; align-items: flex-start; } .stat-grid, .issue-grid { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 27px; } }
</style>
