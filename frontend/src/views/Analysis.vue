<template>
  <div class="page-shell">
    <main class="analysis-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">⚡ 离线批处理</p>
          <h1>PySpark 数据分析</h1>
          <p class="hero-text">
            基于 MySQL 原始采集表，通过 PySpark 批量生成关键词统计与每日采集统计，展示离线分析结果。
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadAnalysisData" :disabled="loadingPage">
            <span class="btn-icon">↻</span>
            {{ loadingPage ? "刷新中..." : "刷新数据" }}
          </button>
          <button class="btn btn--primary" @click="handleRunAnalysis" :disabled="runningJob">
            <span class="btn-icon">▶</span>
            {{ runningJob ? "任务启动中..." : "运行分析任务" }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">⚠️ {{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">✅ {{ runMessage }}</div>

      <!-- 空状态 -->
      <section v-if="!hasAnalysisData && !loadingPage" class="empty-panel">
        <span class="empty-icon">📊</span>
        <p>暂无分析数据，请先运行 PySpark 分析任务</p>
      </section>

      <!-- 关键词 Top20 统计 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>关键词 Top20 统计</h2>
            <p>按出现次数和最高热度值排序，展示高频热搜关键词分布。</p>
          </div>
          <div class="stat-badge">
            <span>共 {{ topKeywords.length }} 个关键词</span>
          </div>
        </div>
        <div class="chart-box">
          <div ref="keywordChartRef" class="chart"></div>
        </div>
      </section>

      <!-- 每日采集统计 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>每日采集统计</h2>
            <p>展示每日总记录数、平均热度和最大热度变化趋势。</p>
          </div>
          <div class="stat-badge">
            <span>共 {{ dailyStats.length }} 天</span>
          </div>
        </div>
        <div class="chart-box">
          <div ref="dailyChartRef" class="chart"></div>
        </div>

        <!-- 数据表格 -->
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>统计日期</th>
                <th>总记录数</th>
                <th>关键词数</th>
                <th>平均热度</th>
                <th>最大热度</th>
                <th>最高排名</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in dailyStats" :key="item.stat_date">
                <td class="date-cell">{{ item.stat_date }}</td>
                <td><span class="num-badge">{{ formatNumber(item.total_records) }}</span></td>
                <td>{{ formatNumber(item.total_keywords) }}</td>
                <td class="heat-cell">{{ formatNumber(item.avg_hot_value) }}</td>
                <td class="heat-cell heat-cell--max">{{ formatNumber(item.max_hot_value) }}</td>
                <td>
                  <span class="rank-badge">{{ item.min_rank || "—" }}</span>
                </td>
              </tr>
              <tr v-if="!dailyStats.length">
                <td colspan="6" class="table-empty">暂无每日统计数据</td>
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
import { getDailyStats, getTopKeywords, runAnalysisJob } from "../api/index.js";

const topKeywords = ref([]);
const dailyStats = ref([]);
const pageError = ref("");
const runMessage = ref("");
const loadingPage = ref(false);
const runningJob = ref(false);
const keywordChartRef = ref(null);
const dailyChartRef = ref(null);

let keywordChart = null;
let dailyChart = null;

const hasAnalysisData = computed(
  () => topKeywords.value.length > 0 || dailyStats.value.length > 0
);

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function buildKeywordChart() {
  if (!keywordChartRef.value) return;
  if (!keywordChart) keywordChart = echarts.init(keywordChartRef.value);

  const data = topKeywords.value;
  const colors = ["#e4572e", "#f4723e", "#f98b56", "#faa575", "#fbbf9e"];

  keywordChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(params) {
        const item = data[params[0]?.dataIndex];
        if (!item) return "";
        return `
          <div style="font-weight:700;margin-bottom:6px;">${item.keyword}</div>
          <div>出现次数：${formatNumber(item.appear_count)}</div>
          <div>最高热度：${formatNumber(item.max_hot_value)}</div>
        `;
      }
    },
    grid: { left: 48, right: 20, top: 36, bottom: 90 },
    xAxis: {
      type: "category",
      data: data.map((item) => item.keyword),
      axisLabel: {
        color: "#5b6475",
        rotate: 35,
        interval: 0,
        fontSize: 11,
        formatter: (v) => (v.length > 6 ? v.slice(0, 6) + "…" : v),
      },
      axisLine: { lineStyle: { color: "rgba(157,176,208,0.4)" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#5b6475", fontSize: 11 },
      splitLine: { lineStyle: { color: "rgba(157,176,208,0.15)", type: "dashed" } },
    },
    series: [
      {
        name: "出现次数",
        type: "bar",
        barMaxWidth: 36,
        data: data.map((item, i) => ({
          value: Number(item.appear_count || 0),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: colors[i % colors.length] },
              { offset: 1, color: colors[i % colors.length] + "55" },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
        })),
      },
    ],
  });
}

function buildDailyChart() {
  if (!dailyChartRef.value) return;
  if (!dailyChart) dailyChart = echarts.init(dailyChartRef.value);

  dailyChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: {
      top: 0,
      textStyle: { color: "#5b6475", fontSize: 12 },
      icon: "roundRect",
    },
    grid: { left: 54, right: 54, top: 46, bottom: 44 },
    xAxis: {
      type: "category",
      data: dailyStats.value.map((item) => item.stat_date?.slice(5) || item.stat_date),
      axisLabel: { color: "#5b6475", fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(157,176,208,0.4)" } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: "value",
        name: "记录数",
        nameTextStyle: { color: "#5b6475", fontSize: 10 },
        axisLabel: { color: "#5b6475", fontSize: 11 },
        splitLine: { lineStyle: { color: "rgba(157,176,208,0.15)", type: "dashed" } },
      },
      {
        type: "value",
        name: "热度",
        nameTextStyle: { color: "#5b6475", fontSize: 10 },
        axisLabel: {
          color: "#5b6475",
          fontSize: 11,
          formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v),
        },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "总记录数",
        type: "bar",
        barMaxWidth: 32,
        data: dailyStats.value.map((item) => Number(item.total_records || 0)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(63,114,175,0.9)" },
            { offset: 1, color: "rgba(63,114,175,0.2)" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: "平均热度",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 6,
        data: dailyStats.value.map((item) => Number(item.avg_hot_value || 0)),
        lineStyle: { width: 2.5, color: "#2a9d8f" },
        itemStyle: { color: "#2a9d8f", borderWidth: 2, borderColor: "#fff" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(42,157,143,0.18)" },
            { offset: 1, color: "rgba(42,157,143,0.02)" },
          ]),
        },
      },
      {
        name: "最大热度",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 6,
        data: dailyStats.value.map((item) => Number(item.max_hot_value || 0)),
        lineStyle: { width: 2.5, color: "#e4572e" },
        itemStyle: { color: "#e4572e", borderWidth: 2, borderColor: "#fff" },
      },
    ],
  });
}

async function loadAnalysisData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    const [keywordResponse, dailyResponse] = await Promise.all([
      getTopKeywords(20),
      getDailyStats(),
    ]);
    topKeywords.value = keywordResponse.items || [];
    dailyStats.value = dailyResponse.items || [];
    await nextTick();
    buildKeywordChart();
    buildDailyChart();
  } catch (error) {
    topKeywords.value = [];
    dailyStats.value = [];
    pageError.value = error.message || "分析数据加载失败，请检查后端服务和统计表";
    buildKeywordChart();
    buildDailyChart();
  } finally {
    loadingPage.value = false;
  }
}

async function handleRunAnalysis() {
  runningJob.value = true;
  try {
    const response = await runAnalysisJob();
    runMessage.value = response.message || "PySpark 分析任务已启动";
  } catch (error) {
    runMessage.value = error.message || "分析任务启动失败，请在命令行运行 python analysis/batch_job.py";
  } finally {
    runningJob.value = false;
  }
}

function handleResize() {
  if (keywordChart) keywordChart.resize();
  if (dailyChart) dailyChart.resize();
}

onMounted(async () => {
  await loadAnalysisData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  if (keywordChart) { keywordChart.dispose(); keywordChart = null; }
  if (dailyChart) { dailyChart.dispose(); dailyChart = null; }
});
</script>

<style scoped>
.page-shell {
  min-height: calc(100vh - 64px);
  padding: 28px 20px 48px;
}

.analysis-page {
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
  background: linear-gradient(90deg, #3f72af, #2a9d8f, #e4572e);
  border-radius: 24px 24px 0 0;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.16em;
  font-weight: 600;
  color: #3f72af;
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

.btn-icon {
  font-size: 15px;
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
  background: rgba(63,114,175,0.08);
  border: 1px solid rgba(63,114,175,0.2);
  color: #3f72af;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

/* ===================== 图表 ===================== */
.chart-box {
  min-height: 360px;
  margin-bottom: 8px;
}

.chart {
  width: 100%;
  height: 360px;
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

/* ===================== 表格 ===================== */
.table-wrap {
  width: 100%;
  overflow-x: auto;
  margin-top: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 680px;
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

.date-cell {
  font-variant-numeric: tabular-nums;
  color: #374151;
  font-weight: 600;
}

.num-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(63,114,175,0.08);
  color: #274c77;
  font-weight: 600;
}

.heat-cell {
  color: #2a9d8f;
  font-weight: 600;
}

.heat-cell--max {
  color: #e4572e;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(22,50,79,0.08);
  color: #16324f;
  font-size: 12px;
  font-weight: 600;
}

.table-empty {
  text-align: center;
  color: #9ca3af;
  padding: 32px;
}

/* ===================== 响应式 ===================== */
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
}

@media (max-width: 640px) {
  .page-shell {
    padding: 18px 12px 36px;
  }

  h1 { font-size: 26px; }

  .chart { height: 300px; }
  .chart-box { min-height: 300px; }
}
</style>
