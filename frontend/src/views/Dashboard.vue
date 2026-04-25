<template>
  <div class="page-shell">
    <main class="dashboard">
      <section class="hero">
        <div>
          <p class="eyebrow">Graduation Demo</p>
          <h1>Weibo Hot Search Dashboard</h1>
          <p class="hero-text">
            Python collector, MySQL storage, FastAPI APIs, and a Vue3 + ECharts dashboard.
          </p>
        </div>
        <div class="hero-badge">
          <span>Latest Fetch Time</span>
          <strong>{{ summary.latest_fetch_time || "No data yet" }}</strong>
        </div>
      </section>

      <section class="cards">
        <article class="card">
          <span>Total Records</span>
          <strong>{{ formatNumber(summary.total_records) }}</strong>
        </article>
        <article class="card">
          <span>Total Batches</span>
          <strong>{{ formatNumber(summary.total_batches) }}</strong>
        </article>
        <article class="card">
          <span>Total Keywords</span>
          <strong>{{ formatNumber(summary.total_keywords) }}</strong>
        </article>
        <article class="card">
          <span>Current List Size</span>
          <strong>{{ formatNumber(summary.latest_batch_count) }}</strong>
        </article>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>Keyword Trend</h2>
            <p>Search a keyword to view historical hot value changes. You can also click a ranking item.</p>
          </div>
          <form class="search-box" @submit.prevent="handleSearch">
            <input
              v-model="keyword"
              type="text"
              placeholder="Enter keyword, e.g. gaokao"
            />
            <button type="submit" :disabled="loadingTrend">
              {{ loadingTrend ? "Loading..." : "Search Trend" }}
            </button>
          </form>
        </div>

        <div class="chart-panel">
          <div ref="chartRef" class="chart"></div>
        </div>
        <p v-if="trendMessage" class="helper-text">{{ trendMessage }}</p>
      </section>

      <section class="content-grid">
        <section class="panel ranking-panel">
          <div class="panel-header">
            <div>
              <h2>Current Ranking</h2>
              <p>The latest hot search list fetched from the database.</p>
            </div>
            <button class="ghost-button" @click="loadPageData" :disabled="loadingPage">
              {{ loadingPage ? "Refreshing..." : "Refresh Data" }}
            </button>
          </div>

          <p v-if="pageError" class="helper-text danger-text">{{ pageError }}</p>

          <div v-if="rankingList.length" class="ranking-list">
            <button
              v-for="item in rankingList"
              :key="`${item.fetch_time}-${item.rank_num}-${item.title}`"
              class="ranking-item"
              @click="queryTrend(item.title)"
            >
              <span class="rank-no">{{ item.rank_num }}</span>
              <span class="rank-title">{{ item.title }}</span>
              <span class="rank-hot">{{ formatNumber(item.hot_value) }}</span>
            </button>
          </div>
          <div v-else class="empty-state">No ranking data. Run the collector first.</div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>Trend Points</h2>
              <p>Historical trend points for the current keyword.</p>
            </div>
          </div>

          <table class="trend-table">
            <thead>
              <tr>
                <th>Fetch Time</th>
                <th>Hot Value</th>
                <th>Best Rank</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="point in trendPoints" :key="point.fetch_time">
                <td>{{ point.fetch_time }}</td>
                <td>{{ formatNumber(point.hot_value) }}</td>
                <td>{{ point.best_rank }}</td>
              </tr>
              <tr v-if="!trendPoints.length">
                <td colspan="3" class="table-empty">No trend data</td>
              </tr>
            </tbody>
          </table>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";

import { getCurrentRanking, getSummary, getTrend } from "../api/index.js";

const summary = ref({
  total_records: 0,
  total_batches: 0,
  total_keywords: 0,
  latest_batch_count: 0,
  latest_fetch_time: ""
});
const rankingList = ref([]);
const keyword = ref("");
const trendPoints = ref([]);
const trendMessage = ref("Enter a keyword to start the trend query.");
const pageError = ref("");
const loadingPage = ref(false);
const loadingTrend = ref(false);
const chartRef = ref(null);

let chartInstance = null;

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function buildChart() {
  if (!chartRef.value) {
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  chartInstance.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis"
    },
    grid: {
      left: 40,
      right: 20,
      top: 40,
      bottom: 40
    },
    xAxis: {
      type: "category",
      data: trendPoints.value.map((item) => item.fetch_time),
      axisLabel: {
        color: "#5b6475",
        rotate: 30
      },
      axisLine: {
        lineStyle: {
          color: "#9db0d0"
        }
      }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#5b6475"
      },
      splitLine: {
        lineStyle: {
          color: "rgba(104, 128, 170, 0.18)"
        }
      }
    },
    series: [
      {
        name: "Hot Value",
        type: "line",
        smooth: true,
        symbolSize: 8,
        data: trendPoints.value.map((item) => item.hot_value),
        lineStyle: {
          width: 3,
          color: "#e4572e"
        },
        itemStyle: {
          color: "#e4572e"
        },
        areaStyle: {
          color: "rgba(228, 87, 46, 0.12)"
        }
      }
    ]
  });
}

async function loadSummaryData() {
  summary.value = await getSummary();
}

async function loadRankingData() {
  const response = await getCurrentRanking();
  rankingList.value = response.items || [];

  if (!keyword.value && rankingList.value.length) {
    keyword.value = rankingList.value[0].title;
  }
}

async function loadPageData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    await Promise.all([loadSummaryData(), loadRankingData()]);
  } catch (error) {
    pageError.value = error.message || "Page initialization failed. Check whether the backend is running.";
  } finally {
    loadingPage.value = false;
  }
}

async function queryTrend(targetKeyword = keyword.value) {
  const cleanedKeyword = String(targetKeyword || "").trim();
  keyword.value = cleanedKeyword;

  if (!cleanedKeyword) {
    trendPoints.value = [];
    trendMessage.value = "Enter a keyword before searching.";
    buildChart();
    return;
  }

  loadingTrend.value = true;
  try {
    const response = await getTrend(cleanedKeyword);
    trendPoints.value = response.points || [];
    trendMessage.value = trendPoints.value.length
      ? `Current keyword: ${response.keyword}`
      : `No historical trend data found for "${response.keyword}".`;
    buildChart();
  } catch (error) {
    trendPoints.value = [];
    trendMessage.value = error.message || "Trend query failed.";
    buildChart();
  } finally {
    loadingTrend.value = false;
  }
}

function handleSearch() {
  queryTrend(keyword.value);
}

function handleResize() {
  if (chartInstance) {
    chartInstance.resize();
  }
}

onMounted(async () => {
  await loadPageData();
  await nextTick();
  buildChart();

  if (keyword.value) {
    await queryTrend(keyword.value);
  }

  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});
</script>

<style scoped>
:global(body) {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(69, 123, 157, 0.24), transparent 28%),
    linear-gradient(135deg, #eef4ff 0%, #f8fafc 45%, #fff7ef 100%);
  color: #1f2937;
}

:global(*) {
  box-sizing: border-box;
}

.page-shell {
  min-height: 100vh;
  padding: 32px 16px 40px;
}

.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  padding: 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(157, 176, 208, 0.32);
  box-shadow: 0 18px 48px rgba(82, 100, 128, 0.12);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #577590;
}

h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.1;
}

h2 {
  margin: 0 0 6px;
  font-size: 22px;
}

p {
  margin: 0;
  color: #5b6475;
}

.hero-text {
  margin-top: 12px;
  max-width: 720px;
  line-height: 1.7;
}

.hero-badge {
  min-width: 260px;
  padding: 18px 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, #274c77 0%, #3f72af 100%);
  color: #ffffff;
}

.hero-badge span {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  opacity: 0.85;
}

.hero-badge strong {
  font-size: 18px;
  line-height: 1.5;
}

.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.card,
.panel {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(157, 176, 208, 0.32);
  box-shadow: 0 16px 38px rgba(82, 100, 128, 0.1);
}

.card {
  padding: 20px;
  border-radius: 20px;
}

.card span {
  display: block;
  margin-bottom: 14px;
  color: #6b7280;
}

.card strong {
  font-size: 28px;
  color: #16324f;
}

.panel {
  padding: 22px;
  border-radius: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.search-box {
  display: flex;
  gap: 10px;
}

.search-box input {
  width: 260px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #cdd7ea;
  background: #ffffff;
  font-size: 14px;
}

.search-box button,
.ghost-button {
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  background: #e4572e;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
}

.search-box button:disabled,
.ghost-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.ghost-button {
  background: #16324f;
}

.chart-panel {
  min-height: 360px;
}

.chart {
  width: 100%;
  height: 360px;
}

.helper-text {
  margin-top: 12px;
  color: #4b5563;
}

.danger-text {
  color: #b42318;
}

.content-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
}

.ranking-list {
  display: grid;
  gap: 10px;
  max-height: 640px;
  overflow: auto;
}

.ranking-item {
  display: grid;
  grid-template-columns: 64px 1fr 120px;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid #e3eaf7;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  cursor: pointer;
  text-align: left;
}

.ranking-item:hover {
  border-color: #8aa4cf;
  transform: translateY(-1px);
}

.rank-no {
  width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #16324f;
  color: #ffffff;
  font-weight: 700;
}

.rank-title {
  font-weight: 600;
  color: #1f2937;
}

.rank-hot {
  text-align: right;
  color: #e4572e;
  font-weight: 700;
}

.trend-table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
}

.trend-table th,
.trend-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  font-size: 14px;
}

.trend-table th {
  color: #475569;
  font-weight: 600;
}

.table-empty,
.empty-state {
  text-align: center;
  color: #6b7280;
}

.empty-state {
  padding: 36px 12px;
}

@media (max-width: 960px) {
  .hero,
  .panel-header,
  .content-grid {
    grid-template-columns: 1fr;
    display: grid;
  }

  .cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-box {
    width: 100%;
  }

  .search-box input {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding: 20px 12px 28px;
  }

  h1 {
    font-size: 30px;
  }

  .cards {
    grid-template-columns: 1fr;
  }

  .ranking-item {
    grid-template-columns: 56px 1fr;
  }

  .rank-hot {
    grid-column: 2;
    text-align: left;
  }

  .chart {
    height: 300px;
  }
}
</style>
