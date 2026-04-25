<template>
  <div class="page-shell">
    <main class="dashboard">

      <!-- Hero 标题区 -->
      <section class="hero">
        <div class="hero-content">
          <p class="eyebrow">🔥 实时总览</p>
          <h1>微博热搜数据分析系统</h1>
          <p class="hero-text">
            Python 定时采集微博热搜，写入 MySQL 后由 FastAPI 提供接口，通过 Vue3 + ECharts 实现全链路可视化展示。
          </p>
        </div>
        <div class="hero-badge">
          <span class="badge-label">📡 最新采集时间</span>
          <strong class="badge-value">{{ summary.latest_fetch_time || "暂无数据" }}</strong>
          <button class="refresh-btn" @click="loadPageData" :disabled="loadingPage">
            <span class="refresh-icon" :class="{ 'spin': loadingPage }">↻</span>
            {{ loadingPage ? "刷新中" : "刷新" }}
          </button>
        </div>
      </section>

      <!-- 数据统计卡片 -->
      <section class="cards">
        <article class="card card--1">
          <div class="card-icon">📦</div>
          <div class="card-body">
            <span class="card-label">累计采集记录</span>
            <strong class="card-value">{{ formatNumber(summary.total_records) }}</strong>
          </div>
          <div class="card-bg-text">TOTAL</div>
        </article>
        <article class="card card--2">
          <div class="card-icon">🗂️</div>
          <div class="card-body">
            <span class="card-label">采集批次数</span>
            <strong class="card-value">{{ formatNumber(summary.total_batches) }}</strong>
          </div>
          <div class="card-bg-text">BATCH</div>
        </article>
        <article class="card card--3">
          <div class="card-icon">🏷️</div>
          <div class="card-body">
            <span class="card-label">关键词总数</span>
            <strong class="card-value">{{ formatNumber(summary.total_keywords) }}</strong>
          </div>
          <div class="card-bg-text">KEYS</div>
        </article>
        <article class="card card--4">
          <div class="card-icon">📊</div>
          <div class="card-body">
            <span class="card-label">当前榜单数量</span>
            <strong class="card-value">{{ formatNumber(summary.latest_batch_count) }}</strong>
          </div>
          <div class="card-bg-text">NOW</div>
        </article>
      </section>

      <!-- 错误提示 -->
      <p v-if="pageError" class="error-bar">⚠️ {{ pageError }}</p>

      <!-- 趋势分析面板 -->
      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>📈 关键词趋势分析</h2>
            <p>点击右侧热搜榜条目，或手动输入关键词查看历史热度变化。</p>
          </div>
          <form class="search-box" @submit.prevent="handleSearch">
            <input
              v-model="keyword"
              type="text"
              placeholder="输入关键词，例如：高考"
            />
            <button type="submit" :disabled="loadingTrend">
              {{ loadingTrend ? "加载中..." : "查询趋势" }}
            </button>
          </form>
        </div>

        <div class="chart-wrap">
          <div ref="chartRef" class="chart"></div>
        </div>
        <p v-if="trendMessage" class="helper-text">{{ trendMessage }}</p>
      </section>

      <!-- 双栏：热搜榜 + 趋势明细 -->
      <section class="content-grid">
        <!-- 热搜榜 -->
        <section class="panel ranking-panel">
          <div class="panel-header">
            <div>
              <h2>🏆 当前热搜榜</h2>
              <p>数据库中最新一批微博热搜采集结果。</p>
            </div>
          </div>

          <div v-if="rankingList.length" class="ranking-list">
            <button
              v-for="(item, index) in rankingList"
              :key="`${item.fetch_time}-${item.rank_num}-${item.title}`"
              class="ranking-item"
              :class="getRankClass(item.rank_num)"
              @click="queryTrend(item.title)"
            >
              <span class="rank-no" :class="getRankBadgeClass(item.rank_num)">
                {{ item.rank_num }}
              </span>
              <span class="rank-title">{{ item.title }}</span>
              <span class="rank-hot">{{ formatHot(item.hot_value) }}</span>
            </button>
          </div>
          <div v-else class="empty-state">
            <span>📭</span>
            <p>当前暂无热搜榜数据，请先运行采集程序</p>
          </div>
        </section>

        <!-- 趋势明细 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>📋 趋势数据明细</h2>
              <p v-if="keyword">当前关键词：<strong style="color: var(--primary)">{{ keyword }}</strong></p>
              <p v-else>当前关键词对应的历史采集点。</p>
            </div>
          </div>

          <div class="table-wrap">
            <table class="trend-table">
              <thead>
                <tr>
                  <th>采集时间</th>
                  <th>热度值</th>
                  <th>最佳排名</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="point in trendPoints" :key="point.fetch_time">
                  <td>{{ point.fetch_time }}</td>
                  <td class="hot-cell">{{ formatNumber(point.hot_value) }}</td>
                  <td>
                    <span class="rank-badge">{{ point.best_rank }}</span>
                  </td>
                </tr>
                <tr v-if="!trendPoints.length">
                  <td colspan="3" class="table-empty">
                    暂无趋势数据，请更换关键词或先采集更多数据
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
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
  latest_fetch_time: "",
});
const rankingList = ref([]);
const keyword = ref("");
const trendPoints = ref([]);
const trendMessage = ref("请输入关键词后查询趋势。");
const pageError = ref("");
const loadingPage = ref(false);
const loadingTrend = ref(false);
const chartRef = ref(null);

let chartInstance = null;

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function formatHot(value) {
  const n = Number(value || 0);
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`;
  if (n >= 10000) return `${Math.round(n / 10000)}万`;
  return n.toLocaleString("zh-CN");
}

function getRankClass(rank) {
  const n = Number(rank || 0);
  if (n <= 3) return "ranking-item--top3";
  if (n <= 10) return "ranking-item--top10";
  return "";
}

function getRankBadgeClass(rank) {
  const n = Number(rank || 0);
  if (n === 1) return "rank-no--gold";
  if (n === 2) return "rank-no--silver";
  if (n === 3) return "rank-no--bronze";
  return "";
}

function buildChart() {
  if (!chartRef.value) return;
  if (!chartInstance) chartInstance = echarts.init(chartRef.value);

  const times = trendPoints.value.map((p) => p.fetch_time);
  const values = trendPoints.value.map((p) => Number(p.hot_value || 0));

  chartInstance.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.9)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    grid: { left: 50, right: 20, top: 36, bottom: 46 },
    xAxis: {
      type: "category",
      data: times,
      boundaryGap: false,
      axisLabel: { color: "#5b6475", rotate: 30, fontSize: 11 },
      axisLine: { lineStyle: { color: "#c4d0e5" } },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#5b6475",
        formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v),
      },
      splitLine: { lineStyle: { color: "rgba(157,176,208,0.2)" } },
    },
    series: [
      {
        name: "热度值",
        type: "line",
        smooth: true,
        symbolSize: 8,
        symbol: "circle",
        data: values,
        lineStyle: { width: 3, color: "#e4572e" },
        itemStyle: { color: "#e4572e", borderWidth: 2, borderColor: "#fff" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(228,87,46,0.25)" },
            { offset: 1, color: "rgba(228,87,46,0.02)" },
          ]),
        },
      },
    ],
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
    pageError.value = error.message || "数据加载失败，请检查后端接口和数据库连接";
  } finally {
    loadingPage.value = false;
  }
}

async function queryTrend(targetKeyword = keyword.value) {
  const cleanedKeyword = String(targetKeyword || "").trim();
  keyword.value = cleanedKeyword;

  if (!cleanedKeyword) {
    trendPoints.value = [];
    trendMessage.value = "请输入关键词后再查询。";
    buildChart();
    return;
  }

  loadingTrend.value = true;
  try {
    const response = await getTrend(cleanedKeyword);
    trendPoints.value = response.points || [];
    trendMessage.value = trendPoints.value.length
      ? `当前关键词：${response.keyword}，共 ${trendPoints.value.length} 条数据`
      : `暂无"${response.keyword}"的趋势数据，请更换关键词或先采集更多数据。`;
    buildChart();
  } catch (error) {
    trendPoints.value = [];
    trendMessage.value = error.message || "查询失败，请检查后端服务是否启动";
    buildChart();
  } finally {
    loadingTrend.value = false;
  }
}

function handleSearch() {
  queryTrend(keyword.value);
}

function handleResize() {
  if (chartInstance) chartInstance.resize();
}

onMounted(async () => {
  await loadPageData();
  await nextTick();
  buildChart();
  if (keyword.value) await queryTrend(keyword.value);
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
.page-shell {
  min-height: calc(100vh - 64px);
  padding: 28px 20px 48px;
}

.dashboard {
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
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #e4572e, #f4723e, #2a9d8f, #3f72af);
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
  max-width: 640px;
  line-height: 1.7;
  font-size: 14px;
}

.hero-badge {
  flex-shrink: 0;
  min-width: 230px;
  padding: 20px 22px;
  border-radius: 18px;
  background: linear-gradient(135deg, #16324f 0%, #274c77 50%, #3f72af 100%);
  color: #fff;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 28px rgba(22,50,79,0.35);
}

.hero-badge::after {
  content: "📡";
  position: absolute;
  bottom: -10px;
  right: 10px;
  font-size: 52px;
  opacity: 0.12;
}

.badge-label {
  display: block;
  font-size: 12px;
  opacity: 0.75;
  margin-bottom: 6px;
  letter-spacing: 0.04em;
}

.badge-value {
  display: block;
  font-size: 16px;
  line-height: 1.5;
  font-weight: 600;
  margin-bottom: 14px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 10px;
  background: rgba(255,255,255,0.12);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(4px);
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.22);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-icon {
  font-size: 16px;
  display: inline-block;
  transition: transform 0.3s ease;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===================== 统计卡片 ===================== */
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.card {
  padding: 22px 20px;
  border-radius: 20px;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(157,176,208,0.25);
  box-shadow: 0 8px 24px rgba(82,100,128,0.08);
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(82,100,128,0.14);
}

.card-icon {
  font-size: 28px;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.12));
}

.card-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
  font-weight: 500;
}

.card-value {
  font-size: 26px;
  font-weight: 800;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.card-bg-text {
  position: absolute;
  right: 14px;
  bottom: -6px;
  font-size: 38px;
  font-weight: 900;
  letter-spacing: -0.02em;
  opacity: 0.04;
  color: #0f172a;
  pointer-events: none;
  user-select: none;
}

/* 卡片配色 */
.card--1 { border-top: 3px solid #e4572e; }
.card--2 { border-top: 3px solid #2a9d8f; }
.card--3 { border-top: 3px solid #3f72af; }
.card--4 { border-top: 3px solid #f2a541; }

/* ===================== 错误提示 ===================== */
.error-bar {
  padding: 12px 18px;
  border-radius: 12px;
  background: rgba(180,35,24,0.08);
  border: 1px solid rgba(180,35,24,0.2);
  color: #b42318;
  font-size: 14px;
  font-weight: 500;
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

/* ===================== 搜索框 ===================== */
.search-box {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.search-box input {
  width: 260px;
  padding: 11px 16px;
  border-radius: 12px;
  border: 1.5px solid #cdd7ea;
  background: #fff;
  font-size: 14px;
  color: #1f2937;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  outline: none;
}

.search-box input:focus {
  border-color: #e4572e;
  box-shadow: 0 0 0 3px rgba(228,87,46,0.12);
}

.search-box button {
  padding: 11px 20px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #e4572e, #f4723e);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(228,87,46,0.35);
}

.search-box button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(228,87,46,0.4);
}

.search-box button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

/* ===================== 图表 ===================== */
.chart-wrap {
  min-height: 360px;
}

.chart {
  width: 100%;
  height: 360px;
}

.helper-text {
  margin-top: 10px;
  font-size: 13px;
  color: #5b6475;
  padding: 0 4px;
}

/* ===================== 双栏布局 ===================== */
.content-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 22px;
}

/* ===================== 热搜榜 ===================== */
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 680px;
  overflow-y: auto;
  padding-right: 4px;
}

.ranking-item {
  display: grid;
  grid-template-columns: 52px 1fr 88px;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1.5px solid #edf3fc;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff, #f7fbff);
  cursor: pointer;
  text-align: left;
  transition: all 0.18s ease;
  font-size: 14px;
}

.ranking-item:hover {
  border-color: #aec4e8;
  background: linear-gradient(135deg, #f0f8ff, #eef4ff);
  transform: translateX(2px);
  box-shadow: 0 4px 14px rgba(82,100,128,0.1);
}

.ranking-item--top3 {
  border-color: rgba(255,210,60,0.45);
  background: linear-gradient(135deg, #fffdf0, #fff8e0);
}

.rank-no {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  background: rgba(22,50,79,0.08);
  color: #44556b;
  font-weight: 700;
  font-size: 14px;
}

.rank-no--gold {
  background: linear-gradient(135deg, #f7b731, #f9ca24);
  color: #5c3900;
  box-shadow: 0 3px 10px rgba(249,202,36,0.45);
}
.rank-no--silver {
  background: linear-gradient(135deg, #9e9e9e, #c8c8c8);
  color: #2a2a2a;
  box-shadow: 0 3px 10px rgba(160,160,160,0.35);
}
.rank-no--bronze {
  background: linear-gradient(135deg, #cd7f32, #e09060);
  color: #3a1500;
  box-shadow: 0 3px 10px rgba(205,127,50,0.4);
}

.rank-title {
  font-weight: 600;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-hot {
  text-align: right;
  color: #e4572e;
  font-weight: 700;
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 12px;
  color: #6b7280;
  font-size: 14px;
}

.empty-state span {
  font-size: 36px;
  opacity: 0.6;
}

/* ===================== 数据明细表 ===================== */
.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.trend-table {
  width: 100%;
  border-collapse: collapse;
}

.trend-table th,
.trend-table td {
  padding: 11px 12px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  font-size: 14px;
}

.trend-table th {
  color: #475569;
  font-weight: 700;
  background: rgba(241,245,249,0.8);
  font-size: 13px;
}

.trend-table tbody tr:hover {
  background: rgba(239,246,255,0.7);
}

.hot-cell {
  color: #e4572e;
  font-weight: 600;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
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
@media (max-width: 1100px) {
  .cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-badge {
    width: 100%;
  }

  .content-grid {
    grid-template-columns: 1fr;
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

  h1 {
    font-size: 26px;
  }

  .cards {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .card-value {
    font-size: 22px;
  }

  .chart {
    height: 300px;
  }

  .ranking-item {
    grid-template-columns: 42px 1fr;
  }

  .rank-hot {
    grid-column: 2;
    text-align: left;
  }
}
</style>
