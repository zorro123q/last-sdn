<template>
  <div class="page-shell">
    <main class="dashboard">

      <!-- Hero 标题区 -->
      <section class="hero">
        <div class="hero-content">
          <p class="eyebrow">实时总览</p>
          <h1>微博热搜数据分析系统</h1>
          <p class="hero-text">
            Python 定时采集微博热搜，写入 MySQL 后由 FastAPI 提供接口，通过 Vue3 + ECharts 实现全链路可视化展示。
          </p>
        </div>
        <div class="hero-badge">
          <span class="badge-label">最新采集时间</span>
          <strong class="badge-value">{{ summary.latest_fetch_time || "暂无数据" }}</strong>
          <!-- 自动刷新状态提示 -->
          <div class="auto-refresh-tip">
            <span :class="['auto-dot', autoRefreshEnabled ? 'auto-dot--active' : 'auto-dot--paused']"></span>
            <span>{{ autoRefreshEnabled ? `自动刷新中，每 ${AUTO_REFRESH_SECONDS} 秒更新` : "自动刷新已暂停" }}</span>
            <span v-if="lastRefreshTime" class="last-refresh">（{{ lastRefreshTime }} 已更新）</span>
          </div>
          <div class="badge-actions">
            <button class="refresh-btn" @click="loadPageData" :disabled="loadingPage">
              <svg class="refresh-icon" :class="{ 'spin': loadingPage }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10"></polyline>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
              </svg>
              {{ loadingPage ? "刷新中" : "刷新" }}
            </button>
            <button class="refresh-btn collect-btn" @click="handleCollectNow" :disabled="collecting || loadingPage">
              <span class="refresh-icon" :class="{ 'spin': collecting }">↻</span>
              {{ collecting ? "采集中..." : "立即采集" }}
            </button>
          </div>
        </div>
      </section>

      <!-- 错误提示 -->
      <p v-if="pageError" class="error-bar">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        {{ pageError }}
      </p>
      <!-- 数据库暂无数据时的友好提示 -->
      <p v-if="noDataTip" class="error-bar warning-bar">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
        当前暂无数据，请先在新终端运行采集程序：<code style="background:rgba(0,0,0,0.06);padding:1px 6px;border-radius:5px;font-size:13px">python collector\app.py</code>
      </p>
      <p v-if="showSampleWarning" class="error-bar warning-bar">
        当前仅采集 {{ summary.total_batches }} 个批次，趋势分析样本较少，爆发预测结果仅供参考。建议采集 30 个批次以上后重新分析。
      </p>

      <!-- 数据统计卡片 -->
      <section class="cards">
        <article class="card card--1">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">累计采集记录</span>
            <strong class="card-value">{{ formatNumber(summary.total_records) }}</strong>
          </div>
        </article>
        <article class="card card--2">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">采集批次数</span>
            <strong class="card-value">{{ formatNumber(summary.total_batches) }}</strong>
          </div>
        </article>
        <article class="card card--3">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
              <line x1="7" y1="7" x2="7.01" y2="7"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">关键词总数</span>
            <strong class="card-value">{{ formatNumber(summary.total_keywords) }}</strong>
          </div>
        </article>
        <article class="card card--4">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">当前榜单数量</span>
            <strong class="card-value">{{ formatNumber(summary.latest_batch_count) }}</strong>
          </div>
        </article>
      </section>

      <!-- 自动洞察卡片 -->
      <section v-if="insights.length" class="insight-panel">
        <div class="insight-header">
          <svg class="insight-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
          <span>数据洞察</span>
        </div>
        <div class="insight-list">
          <div v-for="(text, i) in insights.slice(0, 4)" :key="i" class="insight-item">
            <span class="insight-dot"></span>
            <span class="insight-text">{{ text }}</span>
          </div>
        </div>
      </section>

      <!-- 双栏：趋势图 + 热力图 -->
      <section class="content-grid content-grid--2">
        <!-- 关键词趋势分析 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>热度趋势分析</h2>
              <p>默认展示全库每日最高热度；输入关键词可查看该词历史热度变化。</p>
            </div>
            <form class="search-box" @submit.prevent="handleSearch">
              <input v-model="keyword" type="text" placeholder="输入关键词过滤，留空显示全部" />
              <button type="submit" :disabled="loadingTrend">{{ loadingTrend ? "加载中..." : "查询" }}</button>
              <button v-if="keyword" type="button" class="clear-btn" @click="() => { keyword = ''; queryTrend(''); }" title="清空，回到全库视图">✕</button>
            </form>
          </div>
          <div class="chart-wrap">
            <div ref="chartRef" class="chart"></div>
          </div>
          <p v-if="trendMessage" class="helper-text">{{ trendMessage }}</p>
        </section>

        <!-- 热搜活跃时段分析 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>热搜活跃时段分析</h2>
              <p>柱状图：24小时活跃趋势 | 玫瑰图：活跃时段结构占比</p>
            </div>
            <div class="view-toggle">
              <button :class="['toggle-btn', hourlyView === 'rose' ? 'active' : '']" @click="switchHourlyView('rose')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;margin-right:3px"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
                玫瑰图
              </button>
              <button :class="['toggle-btn', hourlyView === 'bar' ? 'active' : '']" @click="switchHourlyView('bar')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:13px;height:13px;margin-right:3px"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                柱状图
              </button>
            </div>
          </div>
          <div v-if="heatmapLoading" class="chart-loading">加载中...</div>
          <div v-else-if="!heatmapData.length" class="chart-empty">
            <EmptyState title="暂无数据" description="需要包含小时信息的采集记录才能生成活跃时段分析。" />
          </div>
          <div v-else class="chart-wrap">
            <div ref="heatmapRef" class="chart"></div>
          </div>
        </section>
      </section>

      <!-- 排名变化榜 -->
      <section class="panel" v-if="rankMovers.up.length || rankMovers.down.length">
        <div class="panel-header">
          <div>
            <h2>排名变化榜</h2>
            <p>对比最新两批热搜数据，展示上升最快和下降最快的话题。</p>
          </div>
        </div>
        <div class="movers-grid">
          <div class="movers-col">
            <div class="movers-title movers-title--up">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
              上升最快 Top10
            </div>
            <div class="movers-list">
              <div v-for="item in rankMovers.up" :key="item.title" class="movers-item">
                <span class="movers-rank">{{ item.current_rank }}</span>
                <span class="movers-name" :title="item.title">{{ item.title }}</span>
                <span class="movers-delta movers-delta--up">+{{ item.rank_delta }}</span>
                <span class="movers-hot">{{ formatHot(item.current_hot_value) }}</span>
              </div>
            </div>
          </div>
          <div class="movers-col">
            <div class="movers-title movers-title--down">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
              下降最快 Top10
            </div>
            <div class="movers-list">
              <div v-for="item in rankMovers.down" :key="item.title" class="movers-item">
                <span class="movers-rank">{{ item.current_rank }}</span>
                <span class="movers-name" :title="item.title">{{ item.title }}</span>
                <span class="movers-delta movers-delta--down">{{ item.rank_delta }}</span>
                <span class="movers-hot">{{ formatHot(item.current_hot_value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 双栏：热搜榜 + 趋势明细 -->
      <section class="content-grid">
        <section class="panel ranking-panel">
          <div class="panel-header">
            <div>
              <h2>当前热搜榜</h2>
              <p>数据库中最新一批微博热搜采集结果。</p>
            </div>
          </div>
          <div v-if="rankingList.length" class="ranking-list">
            <button v-for="item in rankingList" :key="`${item.fetch_time}-${item.rank_num}-${item.title}`" class="ranking-item" :class="getRankClass(item.rank_num)" @click="queryTrend(item.title)">
              <span class="rank-no" :class="getRankBadgeClass(item.rank_num)">{{ item.rank_num }}</span>
              <span class="rank-title">{{ item.title }}</span>
              <span class="rank-hot">{{ formatHot(item.hot_value) }}</span>
            </button>
          </div>
          <div v-else class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            <p>当前暂无热搜榜数据，请先运行采集程序</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>热度数据明细</h2>
              <p v-if="keyword">过滤关键词：<strong style="color: var(--primary)">{{ keyword }}</strong></p>
              <p v-else>全库数据 · 每行为当日所有热搜中的最高热度</p>
            </div>
          </div>
          <div class="table-wrap">
            <table class="data-table trend-table">
              <thead><tr><th>日期</th><th>当日最高热度</th></tr></thead>
              <tbody>
                <tr v-for="point in trendPoints" :key="point.stat_date || point.fetch_time">
                  <td>{{ String(point.stat_date || point.fetch_time || "").slice(0, 10) }}</td>
                  <td class="hot-cell">{{ formatNumber(point.hot_value) }}</td>
                </tr>
                <tr v-if="!trendPoints.length"><td colspan="2" class="table-empty">暂无数据，请先运行采集器</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { getCurrentRanking, getSummary, getTrend, getHourlyHeatmap, getRankMovers, getVisualInsights, runCollectorJob } from "../api/index.js";
import EmptyState from "../components/EmptyState.vue";

// ─── 自动轮询配置 ───────────────────────────────────────────
/** 自动刷新间隔（秒）—— 改这里即可调整轮询频率 */
const AUTO_REFRESH_SECONDS = 30;

let autoRefreshTimer = null;            // setInterval 句柄
const autoRefreshEnabled = ref(true);   // 是否已启动轮询（用于 UI 状态展示）
const lastRefreshTime = ref("");        // 最近一次自动刷新的时间字符串

/** 启动自动轮询，每隔 AUTO_REFRESH_SECONDS 秒刷新一次页面数据 */
function startAutoRefresh() {
  stopAutoRefresh(); // 先清除已有定时器，防止重复注册
  autoRefreshEnabled.value = true;
  autoRefreshTimer = setInterval(async () => {
    // 静默刷新：不改变 loadingPage，避免 UI 抖动
    try {
      await Promise.all([loadSummaryData(), loadRankingData(), loadHeatmap(), loadMovers(), loadInsightsData()]);
      // 自动刷新趋势图（有关键词时按关键词，无关键词时刷全库）
      await queryTrend(keyword.value);
      const now = new Date();
      lastRefreshTime.value = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
    } catch (err) {
      // 自动刷新静默失败，不弹出错误栏，只在控制台打印
      console.warn("[auto-refresh] 本次自动刷新失败：", err?.message || err);
    }
  }, AUTO_REFRESH_SECONDS * 1000);
}

/** 停止自动轮询，释放定时器 */
function stopAutoRefresh() {
  if (autoRefreshTimer !== null) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
  autoRefreshEnabled.value = false;
}
// ────────────────────────────────────────────────────────────

const summary = ref({ total_records: 0, total_batches: 0, total_keywords: 0, latest_batch_count: 0, latest_fetch_time: "" });
const rankingList = ref([]);
const keyword = ref("");
const trendPoints = ref([]);
const trendMessage = ref("正在加载全库热度趋势...");
const pageError = ref("");
const noDataTip = ref(false);   // 数据库暂无数据时显示友好提示
const loadingPage = ref(false);
const loadingTrend = ref(false);
const collecting = ref(false);
const chartRef = ref(null);
let chartInstance = null;

const showSampleWarning = computed(() => {
  const batches = Number(summary.value.total_batches || 0);
  return batches > 0 && batches < 30;
});

// 热力图
const heatmapRef = ref(null);
let heatmapChart = null;
const heatmapData = ref([]);
const heatmapLoading = ref(false);
const hourlyView = ref("rose"); // "rose" | "bar"

// 排名变化
const rankMovers = ref({ up: [], down: [] });

// 洞察
const insights = ref([]);

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

  if (!trendPoints.value.length) {
    chartInstance.setOption({
      backgroundColor: "transparent",
      tooltip: { show: false },
      grid: { left: 0, right: 0, top: 0, bottom: 0 },
      xAxis: { show: false, type: "category", data: [] },
      yAxis: { show: false, type: "value" },
      dataZoom: [],
      series: [],
      graphic: [
        { type: "circle", left: "center", top: "38%", silent: true, shape: { cx: 0, cy: 0, r: 38 }, style: { fill: "rgba(37,99,235,0.07)" } },
        { type: "text", left: "center", top: "45%", silent: true, style: { text: "暂无趋势数据", fill: "#0f172a", fontSize: 17, fontWeight: 800, textAlign: "center" } },
        { type: "text", left: "center", top: "54%", silent: true, style: { text: "请点击右侧热搜榜或更换关键词后查询", fill: "#64748b", fontSize: 13, fontWeight: 600, textAlign: "center" } },
      ],
    }, true);
    return;
  }

  const times = trendPoints.value.map((p) => String(p.stat_date || p.fetch_time || "").slice(0, 10));
  const hotValues = trendPoints.value.map((p) => Number(p.hot_value || 0));
  const zoomStart = times.length > 30 ? Math.max(0, 100 - (30 / times.length) * 100) : 0;
  const seriesLabel = keyword.value ? `「${keyword.value}」每日最高热度` : "全库每日最高热度";

  // ── 高级统计计算 ───────────────────────────────────────────
  const avgVal = hotValues.length ? hotValues.reduce((a, b) => a + b, 0) / hotValues.length : 0;
  const maxVal = Math.max(...hotValues);
  const maxIdx = hotValues.indexOf(maxVal);
  const minVal = Math.min(...hotValues);
  const minIdx = hotValues.indexOf(minVal);
  const stdDev = hotValues.length > 1
    ? Math.sqrt(hotValues.reduce((s, v) => s + Math.pow(v - avgVal, 2), 0) / hotValues.length)
    : 0;
  const upperBand = avgVal + stdDev;
  const lowerBand = Math.max(0, avgVal - stdDev);

  // 动态颜色：根据热度归一化值分配渐变色（冷→暖）
  const colorStops = [
    { offset: 0.0, color: "#60a5fa" },  // 浅蓝（低）
    { offset: 0.4, color: "#2563eb" },  // 蓝（中）
    { offset: 0.7, color: "#8b5cf6" },  // 紫（中高）
    { offset: 1.0, color: "#ef4444" },  // 红（高）
  ];

  // 生成平滑趋势线（移动平均，窗口=5）
  const smoothWindow = Math.min(5, Math.max(3, Math.floor(times.length / 4)));
  const trendLine = hotValues.map((_, i) => {
    const start = Math.max(0, i - smoothWindow + 1);
    const slice = hotValues.slice(start, i + 1);
    return Math.round(slice.reduce((a, b) => a + b, 0) / slice.length);
  });

  // 一阶差分（变化率）
  const diffLine = hotValues.map((v, i) =>
    i === 0 ? 0 : Math.round(((v - hotValues[i - 1]) / hotValues[i - 1]) * 100)
  );

  // 峰值/谷值标记
  const markPoints = [];
  // 标注最高点
  if (maxIdx >= 0) {
    markPoints.push({
      coord: [maxIdx, maxVal],
      value: maxVal,
      name: "最高",
      itemStyle: { color: "#ef4444", borderColor: "#fff", borderWidth: 2, shadowBlur: 10, shadowColor: "rgba(239,68,68,0.5)" },
    });
  }
  // 标注最低点（仅在数据跨度足够时显示）
  if (times.length > 7 && minIdx !== maxIdx) {
    markPoints.push({
      coord: [minIdx, minVal],
      value: minVal,
      name: "最低",
      itemStyle: { color: "#38bdf8", borderColor: "#fff", borderWidth: 2, shadowBlur: 10, shadowColor: "rgba(56,189,248,0.5)" },
    });
  }

  chartInstance.setOption({
    backgroundColor: "transparent",
    graphic: [],
    color: ["#2563eb"],
    // ── 动画配置 ──────────────────────────────────────────────
    animation: true,
    animationDuration: 1400,
    animationEasing: "cubicOut",
    animationDurationUpdate: 600,
    animationEasingUpdate: "cubicInOut",

    // ── 增强 Tooltip ──────────────────────────────────────────
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.88)",
      borderColor: "rgba(148,163,184,0.28)",
      borderWidth: 1,
      padding: 0,
      textStyle: { color: "#e8f0ff" },
      extraCssText: "backdrop-filter: blur(16px); border-radius: 16px; box-shadow: 0 20px 48px rgba(15,23,42,0.32); overflow: hidden;",
      axisPointer: { type: "shadow", shadowStyle: { color: "rgba(37,99,235,0.10)" } },
      formatter(params) {
        const bar = params.find((p) => p.seriesType === "bar" && p.seriesName !== "均值线");
        if (!bar) return "";
        const dataIndex = bar.dataIndex;
        const point = trendPoints.value[dataIndex] || {};
        const val = Number(point.hot_value || 0);
        const delta = dataIndex > 0 ? val - Number(trendPoints.value[dataIndex - 1]?.hot_value || 0) : 0;
        const pct = dataIndex > 0 && Number(trendPoints.value[dataIndex - 1]?.hot_value || 0) > 0
          ? (((val - Number(trendPoints.value[dataIndex - 1]?.hot_value || 0)) / Number(trendPoints.value[dataIndex - 1]?.hot_value || 0)) * 100).toFixed(1)
          : null;
        const diff = avgVal > 0 ? val - avgVal : 0;
        const diffPct = avgVal > 0 ? ((diff / avgVal) * 100).toFixed(1) : null;
        const deltaStr = delta > 0 ? `<span style="color:#4ade80">▲ +${formatNumber(delta)}</span>` : delta < 0 ? `<span style="color:#f87171">▼ ${formatNumber(delta)}</span>` : `<span style="color:#94a3b8">— 持平</span>`;
        const pctStr = pct !== null ? (Number(pct) > 0 ? `<span style="color:#4ade80">+${pct}%</span>` : `<span style="color:#f87171">${pct}%</span>`) : "";
        const avgDiffStr = diffPct !== null
          ? (diff > 0 ? `<span style="color:#fbbf24">高于均值 ${diffPct}%</span>` : `<span style="color:#60a5fa">低于均值 ${Math.abs(diffPct)}%</span>`)
          : "";
        const diffRate = diffLine[dataIndex] || 0;
        const diffRateStr = diffRate > 0 ? `<span style="color:#c084fc">+${diffRate}%</span>` : diffRate < 0 ? `<span style="color:#94a3b8">${diffRate}%</span>` : `<span style="color:#94a3b8">—</span>`;
        return (
          `<div style="min-width:240px;padding:14px 16px;">` +
          `<div style="font-size:12px;color:#94a3b8;margin-bottom:10px;font-weight:600;">📅 ${times[dataIndex] || ""}</div>` +
          `<div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:8px;"><span style="color:#67e8f9;">热度值</span><strong style="color:#fff;font-size:18px;">${formatNumber(val)}</strong></div>` +
          `<div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:6px;"><span style="color:#94a3b8;font-size:12px;">日涨跌</span><span style="font-size:13px;">${deltaStr} ${pctStr}</span></div>` +
          (avgDiffStr ? `<div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:6px;"><span style="color:#94a3b8;font-size:12px;">偏离均值</span><span style="font-size:13px;">${avgDiffStr}</span></div>` : "") +
          `<div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:4px;"><span style="color:#94a3b8;font-size:12px;">变化率</span><span style="font-size:13px;">${diffRateStr}</span></div>` +
          `<div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;gap:12px;font-size:10px;color:#64748b;">` +
          `<span>均值 ${formatNumber(Math.round(avgVal))}</span>` +
          `<span>σ ${formatNumber(Math.round(stdDev))}</span>` +
          `<span>极差 ${formatNumber(maxVal - minVal)}</span>` +
          `</div>` +
          `</div>`
        );
      },
    },

    // ── 图例（四系列） ─────────────────────────────────────────
    legend: {
      top: 0,
      right: 8,
      itemWidth: 18,
      itemHeight: 10,
      textStyle: { color: "#64748b", fontSize: 11 },
      data: [seriesLabel, "趋势线", "日变化率"],
    },

    grid: { left: 62, right: 32, top: 52, bottom: 96 },

    // ── 缩放控制器 ────────────────────────────────────────────
    dataZoom: [
      {
        type: "inside",
        start: zoomStart,
        end: 100,
        minValueSpan: Math.min(7, Math.max(3, Math.floor(times.length / 8))),
      },
      {
        type: "slider",
        start: zoomStart,
        end: 100,
        height: 28,
        bottom: 24,
        borderColor: "rgba(148,163,184,0.22)",
        fillerColor: "rgba(37,99,235,0.12)",
        handleStyle: { color: "#2563eb", borderColor: "#2563eb" },
        textStyle: { color: "#64748b", fontSize: 11 },
        moveHandleStyle: { color: "#2563eb", opacity: 0.6 },
        emphasis: { handleStyle: { color: "#1d4ed8" } },
      },
    ],

    // ── X 轴 ─────────────────────────────────────────────────
    xAxis: {
      type: "category",
      data: times,
      boundaryGap: true,
      axisLabel: { color: "#64748b", rotate: 30, fontSize: 11, margin: 8 },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
      axisTick: { show: false },
    },

    // ── Y 轴（双轴）────────────────────────────────────────────
    yAxis: [
      {
        type: "value",
        name: "热度值",
        nameTextStyle: { color: "#64748b", fontSize: 11, padding: [0, 0, 0, -8] },
        axisLabel: { color: "#64748b", formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v) },
        splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } },
      },
      {
        type: "value",
        name: "变化率%",
        nameTextStyle: { color: "#a78bfa", fontSize: 10, padding: [0, 0, 0, 0] },
        axisLabel: { color: "#a78bfa", formatter: (v) => `${v > 0 ? "+" : ""}${v}%`, fontSize: 10 },
        splitLine: { show: false },
        min: (val) => Math.min(-10, Math.floor(val.min / 5) * 5),
        max: (val) => Math.max(10, Math.ceil(val.max / 5) * 5),
      },
    ],

    // ── 波动通道（均值 ± 标准差）──────────────────────────────────
    markLine: {
      silent: true,
      symbol: "none",
      lineStyle: { type: "dashed", width: 1.5, color: "rgba(139,92,246,0.35)", opacity: 0.7 },
      label: {
        formatter: (p) => p.seriesIndex === 0 ? `均值±σ\n${Math.round(avgVal)}±${Math.round(stdDev)}` : "",
        position: "insideEndTop",
        color: "#94a3b8",
        fontSize: 10,
        fontWeight: 600,
        backgroundColor: "rgba(255,255,255,0.88)",
        padding: [3, 8, 3, 8],
        borderRadius: 6,
      },
      data: [
        { yAxis: upperBand, name: "上轨" },
        { yAxis: lowerBand, name: "下轨" },
        { type: "average", name: "均值" },
      ],
    },

    // ── 峰值标注 ───────────────────────────────────────────────
    markPoint: {
      symbol: "circle",
      symbolSize: 14,
      label: {
        formatter: "{b}\n{c}",
        position: "top",
        distance: 6,
        color: "#fff",
        fontSize: 11,
        fontWeight: 700,
        backgroundColor: "rgba(15,23,42,0.72)",
        padding: [4, 8, 4, 8],
        borderRadius: 8,
      },
      data: markPoints,
    },

    // ── 四系列：波动带 + 柱状图 + 平滑趋势线 + 变化率 ─────────────
    series: [
      // ── 波动通道面积（均值 ± σ）───────────────────────────────
      {
        name: "波动带",
        type: "custom",
        renderItem(params, api) {
          const upper = api.coord([0, upperBand])[1];
          const lower = api.coord([0, lowerBand])[1];
          const width = Math.abs(api.coord([1, 0])[0] - api.coord([0, 0])[0]);
          return {
            type: "rect",
            shape: {
              x: api.coord([params.dataIndex, 0])[0] - width / 2,
              y: upper,
              width,
              height: lower - upper,
            },
            style: {
              fill: "rgba(139,92,246,0.07)",
              stroke: "rgba(139,92,246,0.18)",
              lineWidth: 1,
            },
          };
        },
        data: hotValues.map((v) => v),
        z: 1,
      },
      {
        name: seriesLabel,
        type: "bar",
        barMaxWidth: 32,
        barGap: "10%",
        data: hotValues.map((value, i) => ({
          value,
          itemStyle: {
            // 动态颜色：归一化到 [0,1] 区间后查表
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: getColorForValue(value, minVal, maxVal, 0.0, 0.4) },
              { offset: 0.5, color: getColorForValue(value, minVal, maxVal, 0.4, 0.7) },
              { offset: 1, color: getColorForValue(value, minVal, maxVal, 0.7, 1.0) },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
          // 峰值高亮
          emphasis: {
            itemStyle: {
              shadowBlur: 18,
              shadowColor: `rgba(${hexToRgb(getColorForValue(value, minVal, maxVal, 0.7, 1.0))}, 0.35)`,
              borderColor: "#fff",
              borderWidth: 1.5,
            },
          },
        })),
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { type: "dashed", width: 2, color: "#94a3b8", opacity: 0.7 },
          label: {
            formatter: "均值 {c}",
            position: "insideEndTop",
            color: "#64748b",
            fontSize: 11,
            fontWeight: 600,
            backgroundColor: "rgba(255,255,255,0.88)",
            padding: [3, 8, 3, 8],
            borderRadius: 6,
          },
          data: [{ type: "average" }],
        },
        markPoint: {
          symbol: "circle",
          symbolSize: 14,
          label: {
            formatter: "{b}\n{c}",
            position: "top",
            distance: 6,
            color: "#fff",
            fontSize: 11,
            fontWeight: 700,
            backgroundColor: "rgba(15,23,42,0.72)",
            padding: [4, 8, 4, 8],
            borderRadius: 8,
          },
          data: markPoints,
        },
      },
      // ── 平滑趋势线（叠加在柱状图上方）─────────────────────────
      {
        name: "趋势线",
        type: "line",
        smooth: 0.5,
        symbol: "circle",
        symbolSize: 5,
        showSymbol: false,
        lineStyle: { width: 3, color: "#06b6d4", type: "solid", opacity: 0.85 },
        itemStyle: { color: "#06b6d4", borderColor: "#fff", borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(6,182,212,0.22)" },
            { offset: 1, color: "rgba(6,182,212,0.02)" },
          ]),
        },
        emphasis: { focus: "series", itemStyle: { symbolSize: 8, shadowBlur: 10, shadowColor: "rgba(6,182,212,0.6)" } },
        data: trendLine,
        z: 2,
      },
      // ── 变化率指标（右 Y 轴）───────────────────────────────────
      {
        name: "日变化率",
        type: "line",
        smooth: 0.3,
        symbol: "circle",
        symbolSize: 4,
        showSymbol: false,
        yAxisIndex: 1,
        lineStyle: { width: 1.8, color: "#8b5cf6", type: "solid", opacity: 0.7 },
        itemStyle: { color: "#8b5cf6", borderColor: "#fff", borderWidth: 1.5 },
        emphasis: { focus: "series", itemStyle: { symbolSize: 7, shadowBlur: 10, shadowColor: "rgba(139,92,246,0.5)" } },
        data: diffLine,
        z: 3,
      },
    ],
  }, true);
}

// ── 辅助函数：热度值 → 颜色映射 ──────────────────────────────
function getColorForValue(value, minVal, maxVal, stopMin, stopMax) {
  const range = maxVal - minVal || 1;
  const ratio = (value - minVal) / range;
  const t = Math.max(0, Math.min(1, stopMin + ratio * (stopMax - stopMin)));
  const colors = [
    { stop: 0.0, r: 96, g: 165, b: 250 },   // #60a5fa 浅蓝
    { stop: 0.4, r: 37, g: 99, b: 235 },   // #2563eb 蓝
    { stop: 0.7, r: 139, g: 92, b: 246 },  // #8b5cf6 紫
    { stop: 1.0, r: 239, g: 68, b: 68 },   // #ef4444 红
  ];
  let c1 = colors[0], c2 = colors[1];
  for (let i = 1; i < colors.length; i++) {
    if (t >= colors[i - 1].stop && t <= colors[i].stop) {
      c1 = colors[i - 1]; c2 = colors[i]; break;
    }
  }
  const seg = c2.stop - c1.stop || 1;
  const f = (t - c1.stop) / seg;
  const r = Math.round(c1.r + (c2.r - c1.r) * f);
  const g = Math.round(c1.g + (c2.g - c1.g) * f);
  const b = Math.round(c1.b + (c2.b - c1.b) * f);
  return `rgb(${r},${g},${b})`;
}

function hexToRgb(color) {
  if (!color) return "0,0,0";
  const m = color.match(/^rgb\((\d+),(\d+),(\d+)\)$/);
  if (m) return `${m[1]},${m[2]},${m[3]}`;
  const hex = color.replace("#", "");
  const bigint = parseInt(hex, 16);
  return `${(bigint >> 16) & 255},${(bigint >> 8) & 255},${bigint & 255}`;
}

function buildHeatmap() {
  if (!heatmapRef.value) { console.warn("[hourly] heatmapRef 未挂载，跳过"); return; }
  const data = heatmapData.value;
  if (!data.length) { console.warn("[hourly] 数据为空，跳过"); return; }

  if (heatmapChart) { heatmapChart.dispose(); heatmapChart = null; }
  heatmapChart = echarts.init(heatmapRef.value);

  const { labels, counts } = buildHourlyActivityData(data);
  const maxCount = Math.max(...counts, 1);

  if (hourlyView.value === "rose") {
    buildHourlyRose(buildTimePeriodRoseData(data));
  } else {
    buildHourlyBar(labels, counts, maxCount);
  }
}

const TIME_PERIODS = [
  { name: "凌晨", start: 0, end: 5 },
  { name: "早晨", start: 6, end: 9 },
  { name: "上午", start: 10, end: 11 },
  { name: "下午", start: 12, end: 17 },
  { name: "晚间", start: 18, end: 21 },
  { name: "深夜", start: 22, end: 23 },
];

function parseHourlyNumber(raw) {
  const value = Number(String(raw ?? 0).replace(/,/g, ""));
  return Number.isFinite(value) ? value : 0;
}

function getHourlyRecordHour(record) {
  const raw = record?.hour ?? record?.hour_of_day ?? record?.time ?? record?.label;
  if (raw === null || raw === undefined) return null;
  if (typeof raw === "number") {
    const hour = Math.floor(raw);
    return hour >= 0 && hour <= 23 ? hour : null;
  }

  const text = String(raw).trim();
  if (!text) return null;

  const timeMatch = text.match(/(?:^|[T\s])([01]?\d|2[0-3])(?::[0-5]?\d)?(?=\s*$|[^\d])/);
  const cnMatch = text.match(/([01]?\d|2[0-3])\s*(?:时|点)/);
  const hourText = timeMatch?.[1] ?? cnMatch?.[1] ?? (/^\d{1,2}$/.test(text) ? text : null);
  if (hourText === null) return null;

  const hour = Number(hourText);
  return Number.isFinite(hour) && hour >= 0 && hour <= 23 ? hour : null;
}

function getHourlyRecordValue(record) {
  return parseHourlyNumber(record?.count ?? record?.value ?? record?.total ?? record?.active_count ?? 0);
}

function buildHourlyActivityData(hourlyData = []) {
  const labels = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, "0")}:00`);
  const counts = Array.from({ length: 24 }, () => 0);

  (Array.isArray(hourlyData) ? hourlyData : []).forEach((record) => {
    const hour = getHourlyRecordHour(record);
    if (hour === null) return;
    counts[hour] += getHourlyRecordValue(record);
  });

  return { labels, counts };
}

function buildTimePeriodRoseData(hourlyData = []) {
  const periodData = TIME_PERIODS.map((period) => ({ name: period.name, value: 0 }));

  (Array.isArray(hourlyData) ? hourlyData : []).forEach((record) => {
    const hour = getHourlyRecordHour(record);
    if (hour === null) return;

    const periodIndex = TIME_PERIODS.findIndex((period) => hour >= period.start && hour <= period.end);
    if (periodIndex >= 0) {
      periodData[periodIndex].value += getHourlyRecordValue(record);
    }
  });

  return periodData;
}

function buildHourlyBar(labels, counts, maxCount) {
  const peakIdx = counts.indexOf(Math.max(...counts));

  heatmapChart.setOption({
    backgroundColor: "transparent",
    animation: true,
    animationDuration: 1000,
    animationEasing: "cubicOut",
    title: {
      text: "24小时活跃趋势",
      left: 8,
      top: 0,
      textStyle: { color: "#0f172a", fontSize: 14, fontWeight: 800 },
    },

    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow", shadowStyle: { color: "rgba(37,99,235,0.08)" } },
      backgroundColor: "rgba(255,255,255,0.98)",
      borderColor: "rgba(148,163,184,0.2)",
      borderWidth: 1,
      padding: 0,
      textStyle: { color: "#1e293b" },
      extraCssText: "border-radius:14px;box-shadow:0 12px 40px rgba(15,23,42,0.12);",
      formatter(params) {
        const bar = params.find((p) => p.seriesName === "活跃次数");
        if (!bar) return "";
        const i = bar.dataIndex;
        const ratio = maxCount > 0 ? counts[i] / maxCount : 0;
        const isPeak = i === peakIdx;
        return (
          `<div style="min-width:190px;padding:14px 16px;">` +
          `<div style="font-size:12px;color:#64748b;margin-bottom:10px;font-weight:500;">${isPeak ? '★ ' : ''}${labels[i]}${isPeak ? ' <span style="color:#f59e0b">(峰值)</span>' : ''}</div>` +
          `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">` +
          `<span style="font-size:11px;color:#64748b;">活跃次数</span>` +
          `<div style="flex:1;height:6px;background:#e2e8f0;border-radius:3px;">` +
          `<div style="height:100%;width:${Math.round(ratio * 100)}%;background:linear-gradient(90deg,#2563eb,#60a5fa);border-radius:3px;"></div>` +
          `</div>` +
          `<strong style="font-size:18px;font-weight:800;color:#1e293b;min-width:40px;text-align:right;">${counts[i]}</strong>` +
          `</div>` +
          `<div style="display:flex;justify-content:space-between;gap:16px;">` +
          `<div><div style="font-size:10px;color:#94a3b8;">小时</div><div style="font-size:15px;font-weight:700;color:#2563eb;">${labels[i]}</div></div>` +
          `<div style="text-align:right;"><div style="font-size:10px;color:#94a3b8;">占比峰值</div><div style="font-size:15px;font-weight:700;color:#64748b;">${Math.round(ratio * 100)}%</div></div>` +
          `</div>` +
          `</div>`
        );
      },
    },
    grid: { left: 56, right: 24, top: 48, bottom: 56 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: {
        color: "#64748b", fontSize: 10, interval: 2,
        formatter: (v) => { const h = parseInt(v); return [0, 6, 12, 18, 23].includes(h) ? v : ""; },
      },
      axisLine: { lineStyle: { color: "#e2e8f0" } },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      name: "活跃次数",
      minInterval: 1,
      nameTextStyle: { color: "#64748b", fontSize: 10 },
      axisLabel: { color: "#64748b", fontSize: 10 },
      splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
    },
    series: [
      {
        name: "活跃次数",
        type: "bar",
        barMaxWidth: 22,
        data: counts.map((v, i) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: i === peakIdx ? "#1d4ed8" : "#60a5fa" },
              { offset: 1, color: i === peakIdx ? "#2563eb" : "#93c5fd" },
            ]),
            borderRadius: [4, 4, 0, 0],
          },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(37,99,235,0.25)" } },
        })),
      },
    ],
  }, true);
}

function buildHourlyRose(periodData) {
  const total = periodData.reduce((sum, item) => sum + Number(item.value || 0), 0);
  const colors = ["#2563eb", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"];

  heatmapChart.setOption({
    backgroundColor: "transparent",
    animation: true,
    animationDuration: 1200,
    animationEasing: "cubicOut",
    title: {
      text: "活跃时段结构占比",
      left: 8,
      top: 0,
      textStyle: { color: "#0f172a", fontSize: 14, fontWeight: 800 },
    },
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.25)",
      borderWidth: 1,
      padding: 0,
      textStyle: { color: "#e8f0ff" },
      extraCssText: "border-radius:16px;box-shadow:0 16px 48px rgba(15,23,42,0.4);backdrop-filter:blur(12px);overflow:hidden;",
      formatter(params) {
        const value = Number(params.value || 0);
        const percent = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
        return (
          `<div style="min-width:180px;padding:14px 16px;">` +
          `<div style="font-size:14px;font-weight:800;color:#fff;margin-bottom:12px;">${params.name}</div>` +
          `<div style="display:flex;justify-content:space-between;gap:18px;margin-bottom:8px;font-size:12px;color:#94a3b8;">` +
          `<span>活跃次数</span><strong style="color:#fff;font-size:17px;">${formatNumber(value)}</strong>` +
          `</div>` +
          `<div style="display:flex;justify-content:space-between;gap:18px;font-size:12px;color:#94a3b8;">` +
          `<span>占比</span><strong style="color:#38bdf8;font-size:17px;">${percent}%</strong>` +
          `</div>` +
          `</div>`
        );
      },
    },
    legend: {
      bottom: 0,
      left: "center",
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#64748b", fontSize: 11 },
    },
    graphic: total > 0 ? [] : [
      {
        type: "text",
        left: "center",
        top: "middle",
        silent: true,
        style: {
          text: "暂无活跃数据",
          fill: "#94a3b8",
          fontSize: 14,
          fontWeight: 700,
          textAlign: "center",
        },
      },
    ],
    series: [
      {
        name: "活跃时段结构占比",
        type: "pie",
        roseType: "area",
        radius: ["20%", "72%"],
        center: ["50%", "48%"],
        avoidLabelOverlap: true,
        stillShowZeroSum: false,
        label: {
          show: true,
          color: "#334155",
          fontSize: 11,
          fontWeight: 700,
          formatter(params) {
            const value = Number(params.value || 0);
            const percent = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
            return `${params.name}\n${percent}%`;
          },
        },
        labelLine: {
          show: true,
          length: 12,
          length2: 8,
          lineStyle: { color: "rgba(100,116,139,0.45)" },
        },
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 2,
          shadowBlur: 10,
          shadowColor: "rgba(15,23,42,0.08)",
        },
        emphasis: {
          scale: true,
          scaleSize: 8,
          itemStyle: { shadowBlur: 18, shadowColor: "rgba(15,23,42,0.18)" },
        },
        data: periodData.map((item, index) => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: colors[index % colors.length] },
        })),
      },
    ],
  }, true);
}

function buildHourlyRadar(labels, counts, avgHots, maxCount, maxAvgHot) {
  // ── 填充扇形玫瑰图（南丁格尔玫瑰图）───────────────────────────
  // 核心理念：扇形面积 ∝ 热度强度（avgHots），颜色冷暖 ∝ 热搜密度（counts）
  const peakIdx = counts.indexOf(Math.max(...counts));
  const avgCount = Math.round(counts.reduce((a, b) => a + b, 0) / 24);
  const avgHot = Math.round(avgHots.filter(v => v > 0).reduce((a, b) => a + b, 0) / Math.max(1, avgHots.filter(v => v > 0).length));

  // 颜色函数：热搜密度映射（冷蓝→暖红）
  function sectorColor(value, maxVal) {
    const ratio = maxVal > 0 ? value / maxVal : 0;
    const stops = [
      { r: 96, g: 165, b: 250 },   // #60a5fa 冷蓝（低密度）
      { r: 37, g: 99, b: 235 },   // #2563eb 蓝
      { r: 139, g: 92, b: 246 },  // #8b5cf6 紫
      { r: 239, g: 68, b: 68 },   // #ef4444 红（高密度）
    ];
    const segs = [
      { min: 0, max: 0.33, c1: stops[0], c2: stops[1] },
      { min: 0.33, max: 0.66, c1: stops[1], c2: stops[2] },
      { min: 0.66, max: 1.0, c1: stops[2], c2: stops[3] },
    ];
    let c1 = stops[0], c2 = stops[1];
    for (const s of segs) { if (ratio >= s.min && ratio <= s.max) { c1 = s.c1; c2 = s.c2; break; } }
    const t = (ratio - 0) / (0.33 || 1);
    const r = Math.round(c1.r + (c2.r - c1.r) * Math.min(1, Math.max(0, t)));
    const g = Math.round(c1.g + (c2.g - c1.g) * Math.min(1, Math.max(0, t)));
    const b = Math.round(c1.b + (c2.b - c1.b) * Math.min(1, Math.max(0, t)));
    return `rgb(${r},${g},${b})`;
  }

  // 半径归一化（avgHots → 0%~90%）
  const radiusScale = (v) => maxAvgHot > 0 ? Math.round((v / maxAvgHot) * 90) + "%" : "5%";
  const avgRadius = radiusScale(avgHot);

  // 扇形角度：24等分，顶部起逆时针
  const slotAngle = (2 * Math.PI) / 24;
  const gap = 0.015; // 扇形间隙（弧度）

  // 构建 24 个扇形数据
  const sectors = labels.map((_, i) => {
    const isPeak = i === peakIdx;
    const startAngle = -Math.PI / 2 + i * slotAngle + gap;
    const endAngle = -Math.PI / 2 + (i + 1) * slotAngle - gap;
    const color = sectorColor(counts[i], maxCount);
    const alpha = isPeak ? 0.92 : 0.78;
    const innerRadius = isPeak ? "8%" : "6%"; // 峰值为圆环，其余实心
    const outerRadius = isPeak
      ? `min(${radiusScale(avgHots[i])}, 90%)`
      : radiusScale(avgHots[i]);

    return {
      value: avgHots[i],
      count: counts[i],
      isPeak,
      startAngle,
      endAngle,
      innerRadius,
      outerRadius,
      color,
      alpha,
      label: labels[i],
    };
  });

  heatmapChart.setOption({
    backgroundColor: "transparent",
    animation: true,
    animationDuration: 1800,
    animationEasing: "elasticOut",

    // ── 极坐标系统 ─────────────────────────────────────────────
    polar: { center: ["50%", "52%"], radius: "75%" },

    // ── Tooltip ──────────────────────────────────────────────────
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.25)",
      borderWidth: 1,
      padding: 0,
      textStyle: { color: "#e8f0ff" },
      extraCssText: "border-radius:16px;box-shadow:0 16px 48px rgba(15,23,42,0.4);backdrop-filter:blur(12px);overflow:hidden;",
      formatter(p) {
        if (p.seriesType !== "custom") return "";
        const s = sectors[p.dataIndex];
        if (!s) return "";
        const pct = maxCount > 0 ? (s.count / maxCount * 100).toFixed(0) : 0;
        const hotPct = maxAvgHot > 0 ? (s.value / maxAvgHot * 100).toFixed(0) : 0;
        const density = s.count > avgCount ? "🔥 高密度" : "📉 低于均值";
        return (
          `<div style="min-width:210px;padding:16px 18px;">` +
          `<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;">` +
          `<span style="font-size:14px;font-weight:700;color:#fff;">${s.label}</span>` +
          (s.isPeak ? `<span style="background:rgba(239,68,68,0.2);color:#f87171;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;border:1px solid rgba(239,68,68,0.3);">★ 峰值</span>` : "") +
          `</div>` +
          `<div style="margin-bottom:10px;">` +
          `<div style="display:flex;justify-content:space-between;font-size:10px;color:#64748b;margin-bottom:4px;"><span>热搜密度（占比）</span><span>${pct}%</span></div>` +
          `<div style="height:5px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">` +
          `<div style="height:100%;width:${pct}%;background:${sectorColor(s.count, maxCount)};border-radius:3px;box-shadow:0 0 6px ${sectorColor(s.count, maxCount)}66;"></div>` +
          `</div>` +
          `</div>` +
          `<div style="margin-bottom:12px;">` +
          `<div style="display:flex;justify-content:space-between;font-size:10px;color:#64748b;margin-bottom:4px;"><span>热度强度（半径）</span><span>${hotPct}%</span></div>` +
          `<div style="height:5px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">` +
          `<div style="height:100%;width:${hotPct}%;background:linear-gradient(90deg,#06b6d4,#22c55e);border-radius:3px;box-shadow:0 0 6px rgba(6,182,212,0.4);"></div>` +
          `</div>` +
          `</div>` +
          `<div style="display:flex;justify-content:space-between;gap:10px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);font-size:11px;color:#94a3b8;">` +
          `<span>热搜条数 <strong style="color:#fff;font-size:16px;">${s.count}</strong></span>` +
          `<span>平均热度 <strong style="color:#22c55e;font-size:16px;">${formatNumber(s.value)}</strong></span>` +
          `</div>` +
          `</div>`
        );
      },
    },

    // ── 角度轴（24 小时标签）────────────────────────────────────
    angleAxis: {
      type: "category",
      data: labels,
      startAngle: 90,
      clockwise: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: (val, i) => [0, 6, 12, 18].includes(i) ? "#1e293b" : "transparent",
        fontSize: 9,
        fontWeight: 700,
        margin: 6,
        formatter(v) {
          const h = parseInt(v);
          if (h === 0) return "00";
          if (h === 6) return "06";
          if (h === 12) return "12";
          if (h === 18) return "18";
          return "";
        },
      },
      splitLine: { show: false },
    },

    // ── 径向轴（控制圆环半径）────────────────────────────────────
    radiusAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      splitLine: {
        lineStyle: {
          color: "rgba(148,163,184,0.1)",
          type: "dashed",
          width: 1,
        },
      },
      splitArea: {
        areaStyle: {
          color: [
            "rgba(241,245,249,0.06)",
            "rgba(241,245,249,0.03)",
            "rgba(241,245,249,0)",
          ],
        },
      },
    },

    // ── 均值参考圆环（静态）──────────────────────────────────────
    graphic: [
      {
        type: "ring",
        shape: { cx: 0, cy: 0, r: parseFloat(avgRadius), r2: parseFloat(avgRadius) + 3 },
        style: {
          fill: "transparent",
          stroke: "rgba(148,163,184,0.3)",
          lineWidth: 1.5,
          lineDash: [4, 3],
        },
        left: "center",
        top: "center",
        silent: true,
      },
    ],

    // ── 三系列：填充扇形 + 热度曲线 + 均值参考环 ───────────────────
    series: [
      // ── 核心：填充扇形（自定义渲染）────────────────────────────
      {
        name: "热搜密度与热度",
        type: "custom",
        coordinateSystem: "polar",
        renderItem(params, api) {
          const idx = params.dataIndex;
          const s = sectors[idx];
          if (!s) return;
          const cx = api.coord([0, 0])[0];
          const cy = api.coord([0, 0])[1];
          // 把百分比的内外半径转换为像素
          const polar = heatmapChart.getModel().option.polar[0];
          const chartRadius = Math.min(
            (api.coord([0, 100]))[1] - cy,
            api.coord([0, 100])[0] - cx
          );
          const toPx = (pct) => (parseFloat(pct) / 100) * chartRadius;
          const innerR = toPx(s.innerRadius);
          const outerR = toPx(s.outerRadius);
          const startAngle = s.startAngle;
          const endAngle = s.endAngle;
          // 扇形路径
          const arc = (r, sa, ea) => {
            const x1 = cx + r * Math.cos(sa), y1 = cy + r * Math.sin(sa);
            const x2 = cx + r * Math.cos(ea), y2 = cy + r * Math.sin(ea);
            const large = ea - sa > Math.PI ? 1 : 0;
            return `M${x1},${y1} A${r},${r},0,${large},1,${x2},${y2}`;
          };
          const pathStr = `${arc(outerR, startAngle, endAngle)}${arc(innerR, endAngle, startAngle)}Z`;
          // 峰值：外发光效果
          const glowFilter = s.isPeak
            ? `drop-shadow(0 0 ${s.isPeak ? 12 : 4}px ${s.color}${s.isPeak ? "aa" : "44"})`
            : "";
          return {
            type: "group",
            children: [
              {
                type: "path",
                shape: { pathData: pathStr },
                style: {
                  fill: s.color,
                  opacity: s.alpha,
                  stroke: s.isPeak ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.25)",
                  lineWidth: s.isPeak ? 2 : 0.8,
                  shadowBlur: s.isPeak ? 16 : 0,
                  shadowColor: `${s.color}80`,
                },
              },
            ],
          };
        },
        data: sectors.map((s) => s.value),
        z: 2,
        encode: { tooltip: [0] },
      },
      // ── 热度强度曲线（叠加在扇形上方）─────────────────────────
      {
        name: "热度强度",
        type: "line",
        coordinateSystem: "polar",
        symbol: "circle",
        symbolSize: 5,
        showSymbol: false,
        smooth: 0.4,
        lineStyle: {
          color: "#22c55e",
          width: 2.5,
          opacity: 0.9,
          shadowBlur: 8,
          shadowColor: "rgba(34,197,94,0.5)",
        },
        itemStyle: { color: "#22c55e", borderColor: "#fff", borderWidth: 2 },
        emphasis: {
          showSymbol: true,
          symbolSize: 8,
          lineStyle: { width: 3 },
          itemStyle: { shadowBlur: 14, shadowColor: "rgba(34,197,94,0.6)" },
        },
        data: sectors.map((s) => Math.round((s.value / maxAvgHot) * 100)),
        z: 3,
      },
      // ── 均值参考弧线（虚线圆）────────────────────────────────
      {
        name: "均值参考",
        type: "line",
        coordinateSystem: "polar",
        symbol: "none",
        smooth: false,
        lineStyle: {
          color: "rgba(148,163,184,0.3)",
          width: 1.5,
          type: "dashed",
        },
        data: sectors.map(() => Math.round((avgHot / maxAvgHot) * 100)),
        z: 1,
      },
    ],
  }, true);
}

function switchHourlyView(view) {
  hourlyView.value = view;
  buildHeatmap();
}

async function loadSummaryData() {
  const data = await getSummary();
  summary.value = data;
  // 检查后端返回的 tip 字段，决定是否显示无数据提示
  noDataTip.value = !data.total_records || data.total_records === 0;
}

async function loadRankingData() {
  const response = await getCurrentRanking();
  rankingList.value = response.items || [];
  // 不再自动把 keyword 设置为榜单第一词，保持全库默认视图
}

async function loadHeatmap() {
  heatmapLoading.value = true;
  try {
    const res = await getHourlyHeatmap();
    heatmapData.value = res.items || [];
  } catch (e) {
    console.warn("[heatmap] 热力图数据接口加载失败", e);
    heatmapData.value = [];
  } finally {
    // 必须先把 loading 置为 false，Vue 才会渲染 v-else 分支并挂载 heatmapRef
    heatmapLoading.value = false;
  }
  // loading=false 之后等两轮 nextTick，让 v-else 分支的 DOM 完成挂载再 init ECharts
  if (!heatmapData.value.length) {
    if (heatmapChart) {
      heatmapChart.dispose();
      heatmapChart = null;
    }
    return;
  }
  await nextTick();
  await nextTick();
  buildHeatmap();
}

async function loadMovers() {
  try {
    const res = await getRankMovers();
    rankMovers.value = { up: res.up || [], down: res.down || [] };
  } catch { rankMovers.value = { up: [], down: [] }; }
}

async function loadInsightsData() {
  try {
    const res = await getVisualInsights();
    insights.value = res.items || [];
  } catch { insights.value = []; }
}

async function loadPageData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    await Promise.all([loadSummaryData(), loadRankingData(), loadHeatmap(), loadMovers(), loadInsightsData()]);
  } catch (error) {
    pageError.value = error.message || "数据加载失败，请检查后端接口和数据库连接";
  } finally {
    loadingPage.value = false;
  }
}

async function handleCollectNow() {
  collecting.value = true;
  pageError.value = "";
  try {
    const res = await runCollectorJob();
    trendMessage.value = res.message || "采集任务已启动，请稍后刷新数据";
    setTimeout(async () => {
      await loadPageData();
      collecting.value = false;
    }, 3000);
  } catch (error) {
    pageError.value = error.message || "启动采集任务失败，请检查后端服务";
    collecting.value = false;
  }
}

async function queryTrend(targetKeyword = keyword.value) {
  const cleanedKeyword = String(targetKeyword || "").trim();
  keyword.value = cleanedKeyword;
  loadingTrend.value = true;
  try {
    // 关键词为空时拉取全库每日最高热度；有关键词时按关键词过滤
    const response = await getTrend(cleanedKeyword);
    trendPoints.value = response.points || [];
    if (!trendPoints.value.length) {
      trendMessage.value = cleanedKeyword
        ? `暂无「${response.keyword}」的趋势数据，请更换关键词或先采集更多数据。`
        : "数据库暂无数据，请先运行采集器。";
    } else {
      trendMessage.value = cleanedKeyword
        ? `「${response.keyword}」共覆盖 ${trendPoints.value.length} 天，每柱为当日最高热度`
        : `全库数据共覆盖 ${trendPoints.value.length} 天，每柱为当日所有热搜最高热度`;
    }
    buildChart();
  } catch (error) {
    trendPoints.value = []; trendMessage.value = error.message || "查询失败，请检查后端服务是否启动"; buildChart();
  } finally { loadingTrend.value = false; }
}

function handleSearch() { queryTrend(keyword.value); }

function handleResize() {
  if (chartInstance) chartInstance.resize();
  if (heatmapChart) heatmapChart.resize();
}

onMounted(async () => {
  await loadPageData();
  await nextTick();
  // 页面加载时自动展示全库每日最高热度（不需要关键词）
  await queryTrend("");
  window.addEventListener("resize", handleResize);
  // 页面加载完成后启动自动轮询
  startAutoRefresh();
});

onBeforeUnmount(() => {
  // 页面卸载时必须清除定时器，防止内存泄漏
  stopAutoRefresh();
  window.removeEventListener("resize", handleResize);
  if (chartInstance) { chartInstance.dispose(); chartInstance = null; }
  if (heatmapChart) { heatmapChart.dispose(); heatmapChart = null; }
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.dashboard { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }

/* Hero */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 52px rgba(37,99,235,0.2), 0 1px 0 rgba(255,255,255,0.1) inset; position: relative; overflow: hidden; }
.hero::before { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08), transparent 50%); pointer-events: none; }
.eyebrow { margin: 0 0 8px; font-size: 13px; letter-spacing: 0.16em; font-weight: 600; color: rgba(255,255,255,0.7); text-transform: uppercase; }
h1 { margin: 0; font-size: 36px; font-weight: 800; line-height: 1.15; color: #fff; letter-spacing: -0.02em; }
h2 { margin: 0 0 5px; font-size: 20px; font-weight: 700; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 640px; line-height: 1.7; font-size: 14px; color: rgba(255,255,255,0.75); }
.hero-badge { flex-shrink: 0; min-width: 230px; padding: 20px 22px; border-radius: 18px; background: rgba(255,255,255,0.12); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.15); color: #fff; position: relative; overflow: hidden; }
.badge-label { display: block; font-size: 12px; opacity: 0.7; margin-bottom: 6px; letter-spacing: 0.04em; }
.badge-value { display: block; font-size: 16px; line-height: 1.5; font-weight: 600; margin-bottom: 8px; }

/* 自动刷新状态提示 */
.auto-refresh-tip { display: flex; align-items: center; gap: 6px; font-size: 12px; color: rgba(255,255,255,0.8); margin-bottom: 10px; flex-wrap: wrap; }
.last-refresh { color: rgba(255,255,255,0.55); }
.auto-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.auto-dot--active { background: #4ade80; box-shadow: 0 0 6px rgba(74,222,128,0.7); animation: pulse-dot 2s ease-in-out infinite; }
.auto-dot--paused { background: rgba(255,255,255,0.4); }
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.badge-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.refresh-btn { display: flex; align-items: center; gap: 6px; padding: 7px 14px; border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; background: rgba(255,255,255,0.15); color: #fff; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; backdrop-filter: blur(4px); }
.refresh-btn:hover:not(:disabled) { background: rgba(255,255,255,0.25); }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.collect-btn { background: rgba(34, 197, 94, 0.18); border-color: rgba(34, 197, 94, 0.35); }
.collect-btn:hover:not(:disabled) { background: rgba(34, 197, 94, 0.28); }
.refresh-icon { width: 16px; height: 16px; display: inline-block; transition: transform 0.3s ease; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* 统计卡片 */
.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.card { padding: 22px 20px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); display: flex; align-items: center; gap: 16px; position: relative; overflow: hidden; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.card:hover { transform: translateY(-2px); box-shadow: 0 16px 36px rgba(15,23,42,0.12); }
.card-icon-wrap { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-icon-svg { width: 24px; height: 24px; }
.card-body { flex: 1; }
.card-label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 4px; font-weight: 500; }
.card-value { font-size: 26px; font-weight: 800; color: var(--navy); font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.card--1 { border-top: 3px solid #2563eb; } .card--1 .card-icon-wrap { background: rgba(37,99,235,0.1); color: #2563eb; }
.card--2 { border-top: 3px solid #06b6d4; } .card--2 .card-icon-wrap { background: rgba(6,182,212,0.1); color: #06b6d4; }
.card--3 { border-top: 3px solid #8b5cf6; } .card--3 .card-icon-wrap { background: rgba(139,92,246,0.1); color: #8b5cf6; }
.card--4 { border-top: 3px solid #f59e0b; } .card--4 .card-icon-wrap { background: rgba(245,158,11,0.1); color: #f59e0b; }

/* 洞察面板 */
.insight-panel { padding: 20px 24px; border-radius: var(--radius-card); background: linear-gradient(135deg, rgba(37,99,235,0.04), rgba(6,182,212,0.04)); border: 1px solid rgba(37,99,235,0.12); box-shadow: var(--shadow-card); }
.insight-header { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 12px; }
.insight-icon { width: 18px; height: 18px; }
.insight-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px 24px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--text-base); line-height: 1.6; }
.insight-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); margin-top: 7px; flex-shrink: 0; }
.insight-text { flex: 1; }

/* 错误提示 */
.error-bar { display: flex; align-items: center; gap: 8px; padding: 12px 18px; border-radius: 12px; background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); color: #dc2626; font-size: 14px; font-weight: 500; }
.warning-bar { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.22); color: #b45309; }
.alert-icon { width: 18px; height: 18px; flex-shrink: 0; }

/* 面板 */
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 20px; }

/* 搜索框 */
.search-box { display: flex; gap: 10px; flex-shrink: 0; }
.search-box input { width: 260px; padding: 11px 16px; border-radius: var(--radius-btn); border: 1.5px solid #cbd5e1; background: #fff; font-size: 14px; color: var(--text-base); transition: border-color 0.2s ease, box-shadow 0.2s ease; outline: none; }
.search-box input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.12); }
.search-box button { padding: 11px 20px; border: none; border-radius: var(--radius-btn); background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 14px rgba(37,99,235,0.3); }
.search-box button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(37,99,235,0.35); }
.search-box button:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
.clear-btn { padding: 11px 14px !important; background: rgba(148,163,184,0.18) !important; color: var(--text-muted) !important; box-shadow: none !important; font-size: 13px !important; }
.clear-btn:hover:not(:disabled) { background: rgba(239,68,68,0.12) !important; color: var(--danger) !important; transform: none !important; box-shadow: none !important; }

/* 视图切换按钮 */
.view-toggle { display: flex; gap: 6px; background: rgba(241,245,249,0.8); border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 3px; flex-shrink: 0; }
.toggle-btn { padding: 7px 16px; border: none; border-radius: 7px; background: transparent; color: var(--text-muted); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.toggle-btn.active { background: #fff; color: var(--primary); box-shadow: 0 2px 8px rgba(37,99,235,0.18); }
.toggle-btn:hover:not(.active) { color: var(--text-base); background: rgba(255,255,255,0.6); }

/* 图表 */
.chart-wrap { min-height: 360px; }
.chart { width: 100%; height: 360px; }
.chart-loading { height: 360px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 14px; }
.chart-empty { height: 360px; display: flex; align-items: center; justify-content: center; }
.helper-text { margin-top: 10px; font-size: 13px; color: var(--text-muted); padding: 0 4px; }

/* 双栏布局 */
.content-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; }
.content-grid--2 { grid-template-columns: 1fr 1fr; }

/* 排名变化榜 */
.movers-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.movers-col { display: flex; flex-direction: column; gap: 10px; }
.movers-title { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; padding: 10px 14px; border-radius: 12px; }
.movers-title svg { width: 18px; height: 18px; }
.movers-title--up { background: rgba(34,197,94,0.08); color: #15803d; }
.movers-title--down { background: rgba(220,38,38,0.08); color: #b91c1c; }
.movers-list { display: flex; flex-direction: column; gap: 6px; }
.movers-item { display: grid; grid-template-columns: 34px 1fr 56px 72px; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 10px; background: linear-gradient(135deg, #ffffff, #f8fafc); border: 1px solid #e2e8f0; font-size: 13px; }
.movers-rank { font-weight: 700; color: var(--navy); font-variant-numeric: tabular-nums; }
.movers-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-base); font-weight: 500; }
.movers-delta { font-weight: 700; font-variant-numeric: tabular-nums; text-align: right; }
.movers-delta--up { color: #16a34a; }
.movers-delta--down { color: #dc2626; }
.movers-hot { text-align: right; color: var(--primary); font-weight: 600; font-size: 12px; }

/* 热搜榜 */
.ranking-list { display: flex; flex-direction: column; gap: 8px; max-height: 680px; overflow-y: auto; padding-right: 4px; }
.ranking-item { display: grid; grid-template-columns: 52px 1fr 88px; align-items: center; gap: 12px; padding: 12px 14px; border: 1.5px solid #e2e8f0; border-radius: 14px; background: linear-gradient(135deg, #ffffff, #f8fafc); cursor: pointer; text-align: left; transition: all 0.18s ease; font-size: 14px; }
.ranking-item:hover { border-color: #94a3b8; background: linear-gradient(135deg, #f1f5f9, #e2e8f0); transform: translateX(2px); box-shadow: 0 4px 14px rgba(15,23,42,0.08); }
.ranking-item--top3 { border-color: rgba(245,158,11,0.35); background: linear-gradient(135deg, #fffbeb, #fef3c7); }
.rank-no { width: 40px; height: 40px; display: inline-flex; align-items: center; justify-content: center; border-radius: 11px; background: rgba(15,23,42,0.06); color: #475569; font-weight: 700; font-size: 14px; }
.rank-no--gold { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #78350f; box-shadow: 0 3px 10px rgba(245,158,11,0.4); }
.rank-no--silver { background: linear-gradient(135deg, #94a3b8, #cbd5e1); color: #1e293b; box-shadow: 0 3px 10px rgba(148,163,184,0.35); }
.rank-no--bronze { background: linear-gradient(135deg, #b45309, #d97706); color: #fff; box-shadow: 0 3px 10px rgba(180,83,9,0.4); }
.rank-title { font-weight: 600; color: var(--text-base); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rank-hot { text-align: right; color: var(--primary); font-weight: 700; font-size: 13px; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px 12px; color: var(--text-muted); font-size: 14px; }
.empty-icon { width: 48px; height: 48px; color: var(--text-light); }

/* 数据明细表 */
.table-wrap { width: 100%; overflow-x: auto; border: 1px solid rgba(203,213,225,0.8); border-radius: 16px; background: rgba(255,255,255,0.92); box-shadow: 0 14px 34px rgba(15,23,42,0.07); -webkit-overflow-scrolling: touch; }
.data-table { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 620px; }
.data-table th, .data-table td { padding: 13px 16px; border-bottom: 1px solid rgba(226,232,240,0.9); text-align: left; font-size: 14px; vertical-align: middle; }
.data-table thead th { position: sticky; top: 0; z-index: 2; color: #334155; font-weight: 800; background: linear-gradient(180deg, rgba(248,250,252,0.98), rgba(241,245,249,0.96)); font-size: 13px; white-space: nowrap; box-shadow: inset 0 -1px 0 rgba(203,213,225,0.9); }
.data-table tbody tr { transition: background 0.18s ease, box-shadow 0.18s ease; }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover td { background: rgba(239,246,255,0.78); }
.data-table tbody td:first-child { position: relative; }
.data-table tbody tr:hover td:first-child::before { content: ""; position: absolute; left: 0; top: 9px; bottom: 9px; width: 3px; border-radius: 999px; background: #2563eb; }
.hot-cell { color: #1d4ed8; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: 0.01em; }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 34px; min-height: 24px; padding: 3px 11px; border-radius: 999px; background: rgba(37,99,235,0.1); color: #1d4ed8; border: 1px solid rgba(37,99,235,0.22); font-size: 12px; font-weight: 800; line-height: 1; }
.table-empty { text-align: center; color: #94a3b8; padding: 34px 18px; background: linear-gradient(180deg, rgba(248,250,252,0.72), rgba(255,255,255,0.86)); font-weight: 600; }

/* 响应式 */
@media (max-width: 1100px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
  .content-grid, .content-grid--2 { grid-template-columns: 1fr; }
  .insight-list { grid-template-columns: 1fr; }
}
@media (max-width: 900px) {
  .hero { flex-direction: column; align-items: flex-start; }
  .hero-badge { width: 100%; }
  .panel-header { flex-direction: column; align-items: flex-start; }
  .search-box { width: 100%; }
  .search-box input { flex: 1; width: auto; }
  .movers-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 26px; }
  .cards { grid-template-columns: 1fr 1fr; gap: 10px; }
  .card-value { font-size: 22px; }
  .chart { height: 300px; }
  .ranking-item { grid-template-columns: 42px 1fr; }
  .rank-hot { grid-column: 2; text-align: left; }
  .movers-item { grid-template-columns: 30px 1fr 48px 60px; gap: 6px; padding: 8px 10px; }
}
</style>
