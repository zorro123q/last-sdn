<template>
  <div class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">Weibo Hot Search Streaming Analytics</p>
        <h1>微博热搜准实时分析系统</h1>
        <p class="subtitle">
          第一版聚焦最小可运行链路：采集、流处理、缓存、接口和可视化看板。
        </p>
      </div>
      <button class="refresh-btn" @click="loadDashboard" :disabled="loading">
        {{ loading ? "刷新中..." : "刷新数据" }}
      </button>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <span>总记录数</span>
        <strong>{{ summary.total_records }}</strong>
      </article>
      <article class="summary-card">
        <span>关键词数量</span>
        <strong>{{ summary.unique_keywords }}</strong>
      </article>
      <article class="summary-card">
        <span>最新采集时间</span>
        <strong>{{ summary.latest_fetch_time || "-" }}</strong>
      </article>
    </section>

    <p v-if="message" class="message">{{ message }}</p>

    <section class="content-grid">
      <article class="panel">
        <div class="panel-header">
          <h2>当前热搜榜</h2>
          <span>{{ rankingPayload.latest_fetch_time || "暂无刷新时间" }}</span>
        </div>
        <div v-if="rankingPayload.data.length === 0" class="empty-state">Redis 中还没有排行榜数据。</div>
        <ul v-else class="ranking-list">
          <li v-for="item in rankingPayload.data" :key="item.rank + item.title">
            <div class="rank-meta">
              <span class="rank-no">{{ item.rank }}</span>
              <span class="rank-title">{{ item.title }}</span>
            </div>
            <span class="hot-value">{{ item.hot_value }}</span>
          </li>
        </ul>
      </article>

      <article class="panel">
        <div class="panel-header">
          <h2>关键词趋势</h2>
          <span>按采集时间聚合最大热度值</span>
        </div>
        <form class="trend-form" @submit.prevent="handleSearch">
          <input v-model.trim="keyword" type="text" placeholder="输入关键词，例如：电影" />
          <button type="submit">查询趋势</button>
        </form>
        <div ref="chartRef" class="chart"></div>
      </article>
    </section>
  </div>
</template>

<script setup>
// 看板页面负责聚合概览、排行和趋势展示。
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";

import { fetchCurrentRanking, fetchSummary, fetchTrend } from "../api/index.js";

const loading = ref(false);
const message = ref("");
const keyword = ref("");
const chartRef = ref(null);
const rankingPayload = ref({
  data: [],
  count: 0,
  latest_fetch_time: null
});
const trendPayload = ref({
  keyword: "",
  data: []
});
const summary = ref({
  total_records: 0,
  unique_keywords: 0,
  latest_fetch_time: null
});

let chartInstance = null;

function resizeChart() {
  if (chartInstance) {
    chartInstance.resize();
  }
}

function renderChart() {
  if (!chartRef.value) {
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const xAxisData = trendPayload.value.data.map((item) => item.fetch_time);
  const seriesData = trendPayload.value.data.map((item) => item.hot_value);

  chartInstance.setOption({
    tooltip: {
      trigger: "axis"
    },
    grid: {
      left: 48,
      right: 24,
      top: 40,
      bottom: 48
    },
    xAxis: {
      type: "category",
      data: xAxisData,
      axisLabel: {
        color: "#6b7280",
        rotate: 25
      }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#6b7280"
      },
      splitLine: {
        lineStyle: {
          color: "#e5e7eb"
        }
      }
    },
    series: [
      {
        name: trendPayload.value.keyword || "热度值",
        type: "line",
        smooth: true,
        data: seriesData,
        lineStyle: {
          width: 3,
          color: "#ef4444"
        },
        itemStyle: {
          color: "#f97316"
        },
        areaStyle: {
          color: "rgba(249, 115, 22, 0.15)"
        }
      }
    ]
  });
}

async function loadSummaryData() {
  summary.value = await fetchSummary();
}

async function loadRankingData() {
  rankingPayload.value = await fetchCurrentRanking();

  if (!keyword.value && rankingPayload.value.data.length > 0) {
    keyword.value = rankingPayload.value.data[0].title;
  }
}

async function loadTrendData() {
  if (!keyword.value) {
    trendPayload.value = { keyword: "", data: [] };
    renderChart();
    return;
  }

  trendPayload.value = await fetchTrend(keyword.value);
  renderChart();
}

async function loadDashboard() {
  loading.value = true;
  message.value = "";

  try {
    await Promise.all([loadSummaryData(), loadRankingData()]);
    await nextTick();
    await loadTrendData();
  } catch (error) {
    const detail = error.response?.data?.detail;
    message.value = detail || error.message || "加载数据失败，请先确认后端服务已启动。";
  } finally {
    loading.value = false;
  }
}

async function handleSearch() {
  try {
    message.value = "";
    await loadTrendData();
  } catch (error) {
    const detail = error.response?.data?.detail;
    message.value = detail || error.message || "趋势查询失败。";
  }
}

onMounted(async () => {
  await loadDashboard();
  window.addEventListener("resize", resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart);

  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 40px 20px 48px;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(16px);
}

.eyebrow {
  margin: 0 0 10px;
  color: #ef4444;
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: 36px;
  line-height: 1.15;
  color: #111827;
}

.subtitle {
  margin: 12px 0 0;
  max-width: 720px;
  color: #4b5563;
  line-height: 1.7;
}

.refresh-btn,
.trend-form button {
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.refresh-btn {
  min-width: 120px;
  padding: 14px 18px;
}

.refresh-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.summary-card,
.panel {
  padding: 22px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.08);
}

.summary-card span {
  display: block;
  color: #6b7280;
  font-size: 14px;
}

.summary-card strong {
  display: block;
  margin-top: 10px;
  color: #111827;
  font-size: 28px;
}

.message {
  margin: 0 0 16px;
  color: #b91c1c;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(300px, 420px) 1fr;
  gap: 18px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 22px;
}

.panel-header span {
  color: #6b7280;
  font-size: 13px;
}

.empty-state {
  color: #6b7280;
  padding: 12px 0;
}

.ranking-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}

.rank-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.rank-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: #ef4444;
  color: #fff;
  font-weight: 700;
}

.rank-title {
  color: #111827;
  word-break: break-all;
}

.hot-value {
  color: #f97316;
  font-weight: 700;
}

.trend-form {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.trend-form input {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid #d1d5db;
  border-radius: 14px;
  background: #fff;
  font-size: 14px;
}

.trend-form button {
  padding: 12px 18px;
}

.chart {
  width: 100%;
  height: 420px;
}

@media (max-width: 960px) {
  .hero,
  .panel-header,
  .trend-form,
  .content-grid {
    display: block;
  }

  .hero,
  .summary-card,
  .panel {
    padding: 18px;
  }

  .refresh-btn,
  .trend-form button {
    width: 100%;
    margin-top: 14px;
  }

  .summary-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .trend-form input {
    width: 100%;
  }

  .chart {
    height: 320px;
  }
}
</style>
