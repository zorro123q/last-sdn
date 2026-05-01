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
              <h2>关键词趋势分析</h2>
              <p>点击右侧热搜榜条目，或手动输入关键词查看历史热度变化。</p>
            </div>
            <form class="search-box" @submit.prevent="handleSearch">
              <input v-model="keyword" type="text" placeholder="输入关键词，例如：高考" />
              <button type="submit" :disabled="loadingTrend">{{ loadingTrend ? "加载中..." : "查询趋势" }}</button>
            </form>
          </div>
          <div class="chart-wrap">
            <div ref="chartRef" class="chart"></div>
          </div>
          <p v-if="trendMessage" class="helper-text">{{ trendMessage }}</p>
        </section>

        <!-- 热搜活跃时间热力图 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>热搜活跃时间热力图</h2>
              <p>展示各日期不同小时段的热搜采集密度。</p>
            </div>
          </div>
          <div v-if="heatmapLoading" class="chart-loading">加载中...</div>
          <div v-else-if="!heatmapData.length" class="chart-empty">
            <EmptyState title="暂无热力图数据" description="需要至少包含小时信息的采集记录才能生成热力图。" />
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
              <h2>趋势数据明细</h2>
              <p v-if="keyword">当前关键词：<strong style="color: var(--primary)">{{ keyword }}</strong></p>
              <p v-else>当前关键词对应的历史采集点。</p>
            </div>
          </div>
          <div class="table-wrap">
            <table class="trend-table">
              <thead><tr><th>采集时间</th><th>热度值</th><th>最佳排名</th></tr></thead>
              <tbody>
                <tr v-for="point in trendPoints" :key="point.fetch_time">
                  <td>{{ point.fetch_time }}</td>
                  <td class="hot-cell">{{ formatNumber(point.hot_value) }}</td>
                  <td><span class="rank-badge">{{ point.best_rank }}</span></td>
                </tr>
                <tr v-if="!trendPoints.length"><td colspan="3" class="table-empty">暂无趋势数据，请更换关键词或先采集更多数据</td></tr>
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
      // 如果当前有关键词，同步刷新趋势数据
      if (keyword.value) {
        await queryTrend(keyword.value);
      }
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
const trendMessage = ref("请输入关键词后查询趋势。");
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
  const times = trendPoints.value.map((p) => p.fetch_time);
  const values = trendPoints.value.map((p) => Number(p.hot_value || 0));
  chartInstance.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(15,23,42,0.9)", borderColor: "rgba(148,163,184,0.3)", textStyle: { color: "#e8f0ff" } },
    grid: { left: 50, right: 20, top: 36, bottom: 46 },
    xAxis: { type: "category", data: times, boundaryGap: false, axisLabel: { color: "#64748b", rotate: 30, fontSize: 11 }, axisLine: { lineStyle: { color: "#cbd5e1" } } },
    yAxis: { type: "value", axisLabel: { color: "#64748b", formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v) }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.2)" } } },
    series: [{
      name: "热度值", type: "line", smooth: true, symbolSize: 8, symbol: "circle", data: values,
      lineStyle: { width: 3, color: "#2563eb" },
      itemStyle: { color: "#2563eb", borderWidth: 2, borderColor: "#fff" },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(37,99,235,0.25)" }, { offset: 1, color: "rgba(37,99,235,0.02)" }]) },
    }],
  });
}

function buildHeatmap() {
  // 1. DOM 检查
  if (!heatmapRef.value) {
    console.warn("[heatmap] heatmapRef 未挂载，跳过 buildHeatmap");
    return;
  }
  const data = heatmapData.value;
  if (!data.length) {
    console.warn("[heatmap] 数据为空，跳过 buildHeatmap");
    return;
  }

  // 2. 销毁旧实例再重新 init（v-else 节点重新挂载后容器句柄已变）
  if (heatmapChart) {
    heatmapChart.dispose();
    heatmapChart = null;
  }
  heatmapChart = echarts.init(heatmapRef.value);

  // 3. 收集所有日期（去重、升序）
  const dates = [...new Set(data.map((d) => d.date))].sort();
  // x 轴标签（0时 ~ 23时，共 24 个）
  const hourLabels = Array.from({ length: 24 }, (_, i) => `${i}时`);

  // 4. 构建 lookup map：{ "日期_小时" -> item }，快速查找
  const lookup = {};
  data.forEach((d) => {
    lookup[`${d.date}_${Number(d.hour)}`] = d;
  });

  // 5. 构造完整的 24×n 格子数据（缺失小时填 0，确保热力图网格完整显示）
  // ECharts heatmap series.data 格式：[xIndex, yIndex, value]
  // xAxis = 小时（category index 0-23），yAxis = 日期（category index）
  const seriesData = [];
  for (let dIdx = 0; dIdx < dates.length; dIdx++) {
    for (let hIdx = 0; hIdx < 24; hIdx++) {
      const item = lookup[`${dates[dIdx]}_${hIdx}`];
      seriesData.push([
        hIdx,                                  // x: 小时 index（0-23）
        dIdx,                                  // y: 日期 index
        item ? Number(item.count || 0) : 0,    // value
      ]);
    }
  }

  // 6. visualMap 上限取实际最大值
  const maxCount = Math.max(...data.map((d) => Number(d.count || 0)), 1);

  console.log(`[heatmap] dates=${dates.length} rows=${data.length} max=${maxCount}`);

  heatmapChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      position: "top",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(p) {
        const [hIdx, dIdx, cnt] = p.data;
        const dateLabel = dates[dIdx] || "";
        const hourStr = String(hIdx).padStart(2, "0");
        const item = lookup[`${dateLabel}_${hIdx}`];
        if (!cnt) return `<div style="color:#94a3b8">${dateLabel} ${hourStr}:00 无数据</div>`;
        return (
          `<div style="font-weight:700;margin-bottom:4px">${dateLabel} ${hourStr}:00</div>` +
          `<div>热搜数：${cnt}</div>` +
          (item && item.avg_hot_value != null
            ? `<div>平均热度：${formatNumber(Number(item.avg_hot_value))}</div>`
            : "")
        );
      },
    },
    grid: { left: 80, right: 20, top: 16, bottom: 68 },
    xAxis: {
      type: "category",
      data: hourLabels,
      splitArea: { show: true, areaStyle: { color: ["rgba(241,245,249,0.5)", "rgba(255,255,255,0.5)"] } },
      axisLabel: { color: "#64748b", fontSize: 10, interval: 1 },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.3)" } },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      data: dates,
      splitArea: { show: true, areaStyle: { color: ["rgba(241,245,249,0.5)", "rgba(255,255,255,0.5)"] } },
      axisLabel: { color: "#64748b", fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.3)" } },
      axisTick: { show: false },
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 4,
      itemHeight: 120,
      text: ["高", "低"],
      textStyle: { color: "#64748b", fontSize: 11 },
      // 0 值用近白色，有数据时从浅蓝到深蓝
      inRange: { color: ["#f0f9ff", "#bae6fd", "#7dd3fc", "#38bdf8", "#0ea5e9", "#0369a1"] },
    },
    series: [{
      name: "热搜数量",
      type: "heatmap",
      data: seriesData,
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,0.15)" } },
      itemStyle: { borderColor: "#fff", borderWidth: 0.5 },
    }],
  });
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
  if (!keyword.value && rankingList.value.length) keyword.value = rankingList.value[0].title;
}

async function loadHeatmap() {
  heatmapLoading.value = true;
  try {
    const res = await getHourlyHeatmap();
    heatmapData.value = res.items || [];
  } catch (e) {
    heatmapData.value = [];
  } finally {
    // 必须先把 loading 置为 false，Vue 才会渲染 v-else 分支并挂载 heatmapRef
    heatmapLoading.value = false;
  }
  // loading=false 之后等两轮 nextTick，让 v-else 分支的 DOM 完成挂载再 init ECharts
  if (heatmapData.value.length) {
    await nextTick();
    await nextTick();
    buildHeatmap();
  }
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
  if (!cleanedKeyword) { trendPoints.value = []; trendMessage.value = "请输入关键词后再查询。"; buildChart(); return; }
  loadingTrend.value = true;
  try {
    const response = await getTrend(cleanedKeyword);
    trendPoints.value = response.points || [];
    trendMessage.value = trendPoints.value.length ? `当前关键词：${response.keyword}，共 ${trendPoints.value.length} 条数据` : `暂无"${response.keyword}"的趋势数据，请更换关键词或先采集更多数据。`;
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
  buildChart();
  if (keyword.value) await queryTrend(keyword.value);
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
.table-wrap { width: 100%; overflow-x: auto; }
.trend-table { width: 100%; border-collapse: collapse; }
.trend-table th, .trend-table td { padding: 11px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.trend-table th { color: #475569; font-weight: 700; background: rgba(241,245,249,0.8); font-size: 13px; }
.trend-table tbody tr:hover { background: rgba(239,246,255,0.7); }
.hot-cell { color: var(--primary); font-weight: 600; }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; padding: 2px 8px; border-radius: 6px; background: rgba(15,23,42,0.06); color: var(--navy); font-size: 12px; font-weight: 600; }
.table-empty { text-align: center; color: var(--text-light); padding: 32px; }

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
