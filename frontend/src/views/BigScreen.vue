<template>
  <div class="bigscreen">
    <!-- 背景装饰 -->
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow--left"></div>
    <div class="bg-glow bg-glow--right"></div>

    <!-- 顶部标题栏 -->
    <header class="bs-header">
      <div class="bs-header-side">
        <div class="stat-mini">
          <span class="stat-mini-label">累计记录</span>
          <span class="stat-mini-value">{{ formatNumber(summary.total_records) }}</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-label">采集批次</span>
          <span class="stat-mini-value">{{ formatNumber(summary.total_batches) }}</span>
        </div>
      </div>
      <div class="bs-header-center">
        <div class="title-glow-wrap">
          <h1 class="bs-title">
            <span class="title-fire">🔥</span>
            微博热搜实时监控大屏
            <span class="title-fire">🔥</span>
          </h1>
        </div>
        <p class="bs-subtitle">基于 Python + FastAPI + PySpark + ML 的全链路热搜数据分析系统</p>
      </div>
      <div class="bs-header-side bs-header-side--right">
        <div class="stat-mini">
          <span class="stat-mini-label">关键词总数</span>
          <span class="stat-mini-value">{{ formatNumber(summary.total_keywords) }}</span>
        </div>
        <div class="stat-mini">
          <span class="stat-mini-label">最新批次</span>
          <span class="stat-mini-value">{{ formatNumber(summary.latest_batch_count) }}</span>
        </div>
      </div>
    </header>

    <!-- 主体三栏布局 -->
    <div class="bs-body">
      <!-- 左列：当前热搜榜 -->
      <div class="bs-col bs-col--left">
        <div class="bs-panel">
          <div class="panel-title">
            <span class="panel-title-icon">📋</span>
            当前热搜榜 TOP {{ rankingList.length }}
            <span class="panel-live-tag">LIVE</span>
          </div>
          <div class="ranking-scroll">
            <div
              v-for="(item, index) in rankingList.slice(0, 25)"
              :key="`${item.title}-${index}`"
              class="rank-row"
              :class="getRankClass(index + 1)"
              @click="queryTrend(item.title)"
            >
              <span class="rank-num" :class="getRankNumClass(index + 1)">{{ index + 1 }}</span>
              <span class="rank-text">{{ item.title }}</span>
              <span class="rank-heat">{{ shortHeat(item.hot_value) }}</span>
              <span class="rank-bar-wrap">
                <span
                  class="rank-bar"
                  :style="{ width: getHeatPercent(item.hot_value) + '%' }"
                ></span>
              </span>
            </div>
            <div v-if="!rankingList.length" class="empty-tip">暂无热搜数据</div>
          </div>
        </div>
      </div>

      <!-- 中列：主图表区 -->
      <div class="bs-col bs-col--mid">
        <!-- 趋势折线图 -->
        <div class="bs-panel bs-panel--chart">
          <div class="panel-title">
            <span class="panel-title-icon">📈</span>
            热搜热度趋势
            <span v-if="selectedKeyword" class="panel-keyword-badge">{{ selectedKeyword }}</span>
          </div>
          <div ref="trendChartRef" class="bs-chart"></div>
          <p v-if="!selectedKeyword" class="chart-hint">← 点击左侧热搜条目查看趋势</p>
        </div>

        <!-- 关键词 Top10 热度柱状图 -->
        <div class="bs-panel bs-panel--chart">
          <div class="panel-title">
            <span class="panel-title-icon">🏆</span>
            关键词 Top10 热度排行
          </div>
          <div ref="keywordChartRef" class="bs-chart"></div>
        </div>
      </div>

      <!-- 右列：ML 分析 + 每日趋势 -->
      <div class="bs-col bs-col--right">
        <!-- 爆发趋势饼图 -->
        <div class="bs-panel bs-panel--sm">
          <div class="panel-title">
            <span class="panel-title-icon">🚀</span>
            ML 爆发趋势分布
          </div>
          <div ref="burstPieRef" class="bs-chart-sm"></div>
        </div>

        <!-- 每日统计折线 -->
        <div class="bs-panel bs-panel--chart">
          <div class="panel-title">
            <span class="panel-title-icon">📅</span>
            每日采集趋势
          </div>
          <div ref="dailyChartRef" class="bs-chart"></div>
        </div>

        <!-- 爆发型热搜列表 -->
        <div class="bs-panel bs-panel--burst">
          <div class="panel-title">
            <span class="panel-title-icon">⚡</span>
            爆发型热搜 Top5
          </div>
          <div class="burst-list">
            <div
              v-for="(item, i) in burstTop5"
              :key="item.keyword"
              class="burst-item"
            >
              <span class="burst-rank">{{ i + 1 }}</span>
              <span class="burst-keyword">{{ item.keyword }}</span>
              <span class="burst-prob">{{ formatPercent(item.burst_probability) }}</span>
              <span class="burst-level" :class="getLevelClass(item.burst_level)">
                {{ burstLevelText(item.burst_level) }}
              </span>
            </div>
            <div v-if="!burstTop5.length" class="empty-tip">暂无爆发趋势数据</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第二行：词云 + 情感分析 + 地图 -->
    <div class="bs-row2">
      <!-- 热词词云 -->
      <div class="bs-panel bs-panel--chart bs-panel--wc">
        <div class="panel-title">
          <span class="panel-title-icon">☁️</span>
          热词词云
          <span v-if="selectedKeyword" class="panel-keyword-badge">{{ selectedKeyword }}</span>
        </div>
        <div ref="wordCloudRef2" class="bs-chart bs-chart--wc"></div>
      </div>

      <!-- 情感统计环形图 -->
      <div class="bs-panel bs-panel--sm bs-panel--sent">
        <div class="panel-title">
          <span class="panel-title-icon">😊</span>
          评论情感分布
        </div>
        <div class="sentiment-cards">
          <div class="sent-card sent-card--pos">
            <span class="sent-icon">😊</span>
            <span class="sent-num">{{ shortHeat(sentimentData.positive) }}</span>
            <span class="sent-label">正面</span>
          </div>
          <div class="sent-card sent-card--neg">
            <span class="sent-icon">😡</span>
            <span class="sent-num">{{ shortHeat(sentimentData.negative) }}</span>
            <span class="sent-label">负面</span>
          </div>
          <div class="sent-card sent-card--neu">
            <span class="sent-icon">😐</span>
            <span class="sent-num">{{ shortHeat(sentimentData.neutral) }}</span>
            <span class="sent-label">中性</span>
          </div>
        </div>
        <div ref="sentPieRef2" class="bs-chart-sm"></div>
      </div>

      <!-- 省份评论分布地图 -->
      <div class="bs-panel bs-panel--chart bs-panel--map2">
        <div class="panel-title">
          <span class="panel-title-icon">🗺️</span>
          全国评论热力分布
        </div>
        <div ref="mapRef2" class="bs-chart bs-chart--map"></div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <footer class="bs-footer">
      <span>系统状态：{{ statusText }}</span>
      <span>最新采集：{{ summary.latest_fetch_time || "—" }}</span>
      <span>技术栈：Python · FastAPI · PySpark · KMeans · Vue3 · ECharts</span>
      <span>刷新间隔：60s</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import "echarts-wordcloud";
import {
  getCurrentRanking,
  getDailyStats,
  getBurstTop,
  getSummary,
  getTrend,
  getTopKeywords,
  getCommentGeoData,
  getSentimentData,
  getWordCloudData,
} from "../api/index.js";

/* ===== 状态 ===== */
const summary = ref({
  total_records: 0,
  total_batches: 0,
  total_keywords: 0,
  latest_batch_count: 0,
  latest_fetch_time: "",
});
const rankingList = ref([]);
const dailyStats = ref([]);
const topKeywords = ref([]);
const burstData = ref([]);
const trendPoints = ref([]);
const selectedKeyword = ref("");
const statusText = ref("加载中...");
const sentimentData = ref({ positive: 0, negative: 0, neutral: 0 });
const wordCloudDataBs = ref([]);
const geoDataBs = ref([]);

/* ===== 图表 DOM 引用 ===== */
const trendChartRef = ref(null);
const keywordChartRef = ref(null);
const burstPieRef = ref(null);
const dailyChartRef = ref(null);
const wordCloudRef2 = ref(null);
const sentPieRef2 = ref(null);
const mapRef2 = ref(null);

let trendChart = null;
let keywordChart = null;
let burstPieChart = null;
let dailyChart = null;
let wordCloudChart2 = null;
let sentPieChart2 = null;
let mapChart2 = null;
let refreshTimer = null;

/* ===== 计算属性 ===== */
const burstTop5 = computed(() =>
  burstData.value
    .filter((item) => Number(item.burst_level) === 2)
    .slice(0, 5)
);

const maxHeat = computed(() => {
  if (!rankingList.value.length) return 1;
  return Math.max(...rankingList.value.map((item) => Number(item.hot_value || 0)));
});

/* ===== 格式化工具 ===== */
function formatNumber(value) {
  const n = Number(value || 0);
  return Number.isFinite(n) ? n.toLocaleString("zh-CN") : "0";
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function shortHeat(value) {
  const n = Number(value || 0);
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`;
  if (n >= 10000) return `${Math.round(n / 10000)}万`;
  return String(n);
}

function getHeatPercent(value) {
  const n = Number(value || 0);
  return maxHeat.value > 0 ? Math.round((n / maxHeat.value) * 100) : 0;
}

function burstLevelText(level) {
  const map = { 2: "爆发", 1: "稳定", 0: "降温" };
  return map[Number(level)] || "稳定";
}

function getLevelClass(level) {
  const map = { 2: "level--burst", 1: "level--stable", 0: "level--cool" };
  return map[Number(level)] || "level--stable";
}

function getRankClass(rank) {
  if (rank <= 3) return "rank-row--top3";
  if (rank <= 10) return "rank-row--top10";
  return "";
}

function getRankNumClass(rank) {
  if (rank === 1) return "rank-num--gold";
  if (rank === 2) return "rank-num--silver";
  if (rank === 3) return "rank-num--bronze";
  return "";
}

/* ===== 暗色 ECharts 主题配置 ===== */
const DARK_COLORS = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#c77dff", "#ff9f43", "#2ed573", "#70a1ff"];

const darkAxisStyle = {
  axisLabel: { color: "rgba(200,220,255,0.7)", fontSize: 11 },
  axisLine: { lineStyle: { color: "rgba(100,150,220,0.3)" } },
  splitLine: { lineStyle: { color: "rgba(100,150,220,0.12)" } },
};

/* ===== 图表构建 ===== */
function buildTrendChart() {
  if (!trendChartRef.value) return;
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value, null, { renderer: "canvas" });
  }

  const times = trendPoints.value.map((p) => p.fetch_time?.slice(-8) || "");
  const values = trendPoints.value.map((p) => Number(p.hot_value || 0));

  trendChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" } },
    grid: { left: 50, right: 20, top: 20, bottom: 36 },
    xAxis: { type: "category", data: times, boundaryGap: false, ...darkAxisStyle },
    yAxis: {
      type: "value",
      ...darkAxisStyle,
      axisLabel: {
        ...darkAxisStyle.axisLabel,
        formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v),
      },
    },
    series: [
      {
        name: "热度值",
        type: "line",
        smooth: true,
        symbolSize: 6,
        data: values,
        lineStyle: { width: 2.5, color: "#ff6b6b" },
        itemStyle: { color: "#ff6b6b" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(255,107,107,0.4)" },
            { offset: 1, color: "rgba(255,107,107,0.02)" },
          ]),
        },
      },
    ],
  }, true);
}

function buildKeywordChart() {
  if (!keywordChartRef.value) return;
  if (!keywordChart) {
    keywordChart = echarts.init(keywordChartRef.value, null, { renderer: "canvas" });
  }

  const data = topKeywords.value.slice(0, 10);
  const keywords = data.map((item) => item.keyword?.slice(0, 8) || "");
  const values = data.map((item) => Number(item.max_hot_value || 0));

  keywordChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" } },
    grid: { left: 50, right: 16, top: 10, bottom: 60 },
    xAxis: {
      type: "category",
      data: keywords,
      axisLabel: { color: "rgba(200,220,255,0.7)", rotate: 30, interval: 0, fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(100,150,220,0.3)" } },
    },
    yAxis: {
      type: "value",
      ...darkAxisStyle,
      axisLabel: {
        ...darkAxisStyle.axisLabel,
        formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v),
      },
    },
    series: [
      {
        type: "bar",
        barMaxWidth: 28,
        data: values.map((v, i) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: DARK_COLORS[i % DARK_COLORS.length] },
              { offset: 1, color: DARK_COLORS[i % DARK_COLORS.length] + "55" },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
        })),
      },
    ],
  }, true);
}

function buildBurstPieChart() {
  if (!burstPieRef.value) return;
  if (!burstPieChart) {
    burstPieChart = echarts.init(burstPieRef.value, null, { renderer: "canvas" });
  }

  const summary = { 2: 0, 1: 0, 0: 0 };
  burstData.value.forEach((item) => {
    const k = Number(item.burst_level);
    summary[k] = (summary[k] || 0) + 1;
  });

  burstPieChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" } },
    legend: { bottom: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 11 } },
    series: [
      {
        name: "趋势",
        type: "pie",
        radius: ["38%", "65%"],
        center: ["50%", "44%"],
        label: { show: false },
        data: [
          { name: "爆发型", value: summary[2], itemStyle: { color: "#ff6b6b" } },
          { name: "稳定型", value: summary[1], itemStyle: { color: "#4d96ff" } },
          { name: "降温型", value: summary[0], itemStyle: { color: "#6bcb77" } },
        ],
      },
    ],
  }, true);
}

function buildDailyChart() {
  if (!dailyChartRef.value) return;
  if (!dailyChart) {
    dailyChart = echarts.init(dailyChartRef.value, null, { renderer: "canvas" });
  }

  const dates = dailyStats.value.map((item) => item.stat_date?.slice(5) || "");
  const records = dailyStats.value.map((item) => Number(item.total_records || 0));
  const maxHots = dailyStats.value.map((item) => Number(item.max_hot_value || 0));

  dailyChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" } },
    legend: { top: 0, right: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 10 } },
    grid: { left: 50, right: 50, top: 26, bottom: 36 },
    xAxis: {
      type: "category",
      data: dates,
      ...darkAxisStyle,
    },
    yAxis: [
      { type: "value", name: "记录数", ...darkAxisStyle, nameTextStyle: { color: "rgba(200,220,255,0.5)", fontSize: 10 } },
      { type: "value", name: "热度", ...darkAxisStyle, nameTextStyle: { color: "rgba(200,220,255,0.5)", fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      {
        name: "总记录数",
        type: "bar",
        barMaxWidth: 24,
        data: records,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(77,150,255,0.9)" },
            { offset: 1, color: "rgba(77,150,255,0.2)" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: "最大热度",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 5,
        data: maxHots,
        lineStyle: { width: 2, color: "#ffd93d" },
        itemStyle: { color: "#ffd93d" },
      },
    ],
  }, true);
}

/* ===== 词云图（大屏暗色风格） ===== */
function buildWordCloudChart2() {
  if (!wordCloudRef2.value) return;
  if (!wordCloudChart2) {
    wordCloudChart2 = echarts.init(wordCloudRef2.value, null, { renderer: "canvas" });
  }
  wordCloudChart2.setOption({
    backgroundColor: "transparent",
    series: [
      {
        type: "wordCloud",
        shape: "circle",
        left: "center",
        top: "center",
        width: "90%",
        height: "90%",
        sizeRange: [12, 60],
        rotationRange: [-45, 45],
        rotationStep: 15,
        gridSize: 6,
        drawOutOfBound: false,
        layoutAnimation: true,
        textStyle: {
          fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
          fontWeight: "bold",
          color: () => {
            const colors = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#c77dff",
              "#ff9f43", "#2ed573", "#70a1ff", "#ff7fc8", "#00d2d3"];
            return colors[Math.floor(Math.random() * colors.length)];
          },
        },
        emphasis: {
          focus: "self",
          textStyle: { shadowBlur: 10, shadowColor: "rgba(255,255,255,0.3)" },
        },
        data: wordCloudDataBs.value,
      },
    ],
  }, true);
}

/* ===== 情感饼图（大屏暗色） ===== */
function buildSentPieChart2() {
  if (!sentPieRef2.value) return;
  if (!sentPieChart2) {
    sentPieChart2 = echarts.init(sentPieRef2.value, null, { renderer: "canvas" });
  }
  sentPieChart2.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" }, formatter: "{b}: {d}%" },
    legend: { bottom: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 10 } },
    series: [
      {
        type: "pie",
        radius: ["35%", "62%"],
        center: ["50%", "44%"],
        label: { show: false },
        data: [
          { name: "正面", value: sentimentData.value.positive, itemStyle: { color: "#22c55e" } },
          { name: "负面", value: sentimentData.value.negative, itemStyle: { color: "#ef4444" } },
          { name: "中性", value: sentimentData.value.neutral, itemStyle: { color: "#64748b" } },
        ],
      },
    ],
  }, true);
}

/* ===== 地图（大屏暗色风格） ===== */
async function buildMapChart2() {
  if (!mapRef2.value) return;
  if (!mapChart2) {
    mapChart2 = echarts.init(mapRef2.value, null, { renderer: "canvas" });
  }

  let chinaGeoJson = null;
  try {
    const res = await fetch("https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json");
    chinaGeoJson = await res.json();
  } catch { chinaGeoJson = null; }

  if (chinaGeoJson) {
    echarts.registerMap("china_dark", chinaGeoJson);
  }

  const mapName = chinaGeoJson ? "china_dark" : "china";

  mapChart2.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(10,20,40,0.9)",
      borderColor: "rgba(100,160,255,0.4)",
      textStyle: { color: "#e8f0ff" },
      formatter: (p) => `<b>${p.name}</b><br/>评论：${(p.value || 0).toLocaleString("zh-CN")}`,
    },
    visualMap: {
      min: 0,
      max: Math.max(...geoDataBs.value.map((d) => d.value), 1),
      left: 8,
      bottom: 24,
      text: ["多", "少"],
      inRange: { color: ["#0a1628", "#1a3a6e", "#2a6db5", "#3f9cf5", "#7dd3fc"] },
      textStyle: { color: "rgba(200,220,255,0.6)", fontSize: 10 },
      calculable: false,
      itemWidth: 10,
      itemHeight: 60,
    },
    series: [
      {
        name: "评论数",
        type: "map",
        map: mapName,
        roam: false,
        zoom: 1.15,
        label: { show: false },
        emphasis: {
          label: { show: true, color: "#ffd93d", fontSize: 11, fontWeight: 700 },
          itemStyle: { areaColor: "#ff9f43" },
        },
        data: geoDataBs.value,
        itemStyle: {
          areaColor: "#0d1e3c",
          borderColor: "rgba(77,150,255,0.3)",
          borderWidth: 0.8,
        },
      },
    ],
  }, true);
}

/* ===== 数据加载 ===== */
async function loadAllData() {
  try {
    const [summaryRes, rankingRes, dailyRes, keywordsRes, burstRes] = await Promise.allSettled([
      getSummary(),
      getCurrentRanking(),
      getDailyStats(),
      getTopKeywords(10),
      getBurstTop(20),
    ]);

    if (summaryRes.status === "fulfilled") summary.value = summaryRes.value;
    if (rankingRes.status === "fulfilled") rankingList.value = rankingRes.value.items || [];
    if (dailyRes.status === "fulfilled") dailyStats.value = dailyRes.value.items || [];
    if (keywordsRes.status === "fulfilled") topKeywords.value = keywordsRes.value.items || [];
    if (burstRes.status === "fulfilled") burstData.value = burstRes.value.items || [];

    // 加载情感、词云、地图数据
    const kw = selectedKeyword.value || (rankingList.value[0]?.title || "");
    const [sentRes, wcRes, geoRes] = await Promise.allSettled([
      getSentimentData(kw),
      getWordCloudData(kw),
      getCommentGeoData(kw),
    ]);
    if (sentRes.status === "fulfilled") sentimentData.value = sentRes.value;
    if (wcRes.status === "fulfilled") wordCloudDataBs.value = wcRes.value || [];
    if (geoRes.status === "fulfilled") geoDataBs.value = geoRes.value || [];

    statusText.value = "数据正常";
  } catch (e) {
    statusText.value = "后端连接失败";
  }

  await nextTick();
  buildTrendChart();
  buildKeywordChart();
  buildBurstPieChart();
  buildDailyChart();
  buildWordCloudChart2();
  buildSentPieChart2();
  buildMapChart2();

  // 默认展示第一条热搜趋势
  if (rankingList.value.length && !selectedKeyword.value) {
    await queryTrend(rankingList.value[0].title);
  }
}

async function queryTrend(kw) {
  selectedKeyword.value = kw;
  try {
    const res = await getTrend(kw);
    trendPoints.value = res.points || [];
  } catch (e) {
    trendPoints.value = [];
  }
  await nextTick();
  buildTrendChart();
}

/* ===== 生命周期 ===== */
function handleResize() {
  [trendChart, keywordChart, burstPieChart, dailyChart, wordCloudChart2, sentPieChart2, mapChart2]
    .forEach((c) => c?.resize());
}

onMounted(async () => {
  await loadAllData();
  window.addEventListener("resize", handleResize);
  refreshTimer = setInterval(loadAllData, 60000);
});

onBeforeUnmount(() => {
  clearInterval(refreshTimer);
  window.removeEventListener("resize", handleResize);
  [trendChart, keywordChart, burstPieChart, dailyChart, wordCloudChart2, sentPieChart2, mapChart2].forEach((c) => {
    if (c) { c.dispose(); }
  });
  trendChart = null;
  keywordChart = null;
  burstPieChart = null;
  dailyChart = null;
  wordCloudChart2 = null;
  sentPieChart2 = null;
  mapChart2 = null;
});
</script>

<style scoped>
/* ===================== 大屏容器 ===================== */
.bigscreen {
  width: 100vw;
  min-height: 100vh;
  background: radial-gradient(ellipse at 20% 20%, rgba(30, 60, 120, 0.8), transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(80, 20, 60, 0.6), transparent 50%),
    linear-gradient(160deg, #030818 0%, #060d26 40%, #0a0d1f 100%);
  color: #e8f0ff;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

/* 背景网格 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(100, 150, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100, 150, 255, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 0;
}

/* 光晕装饰 */
.bg-glow {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  z-index: 0;
}

.bg-glow--left {
  top: -200px;
  left: -200px;
  background: radial-gradient(circle, rgba(60, 100, 220, 0.22), transparent 70%);
}

.bg-glow--right {
  bottom: -200px;
  right: -200px;
  background: radial-gradient(circle, rgba(180, 40, 100, 0.18), transparent 70%);
}

/* ===================== 顶部标题栏 ===================== */
.bs-header {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 20px;
  padding: 14px 28px 10px;
  border-bottom: 1px solid rgba(100, 150, 255, 0.15);
  background: rgba(5, 12, 35, 0.6);
  backdrop-filter: blur(10px);
}

.bs-header-side {
  display: flex;
  gap: 24px;
  align-items: center;
}

.bs-header-side--right {
  justify-content: flex-end;
}

.stat-mini {
  text-align: center;
}

.stat-mini-label {
  display: block;
  font-size: 11px;
  color: rgba(150, 190, 255, 0.6);
  margin-bottom: 2px;
  letter-spacing: 0.08em;
}

.stat-mini-value {
  font-size: 20px;
  font-weight: 700;
  color: #7dd3fc;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 16px rgba(125, 211, 252, 0.6);
}

.bs-header-center {
  text-align: center;
}

.bs-title {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 0.06em;
  background: linear-gradient(135deg, #60a5fa, #e0f2fe, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.3;
}

.title-fire {
  -webkit-text-fill-color: initial;
}

.bs-subtitle {
  font-size: 12px;
  color: rgba(150, 190, 255, 0.55);
  margin-top: 3px;
  letter-spacing: 0.04em;
}

/* ===================== 主体三栏 ===================== */
.bs-body {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 280px 1fr 300px;
  gap: 12px;
  padding: 12px 16px 0;
  overflow: hidden;
  flex-shrink: 0;
}

/* ===================== 第二行：词云 + 情感 + 地图 ===================== */
.bs-row2 {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr 260px 1.2fr;
  gap: 12px;
  padding: 0 16px 10px;
  flex-shrink: 0;
}

.bs-panel--wc,
.bs-panel--sent,
.bs-panel--map2 {
  min-height: 260px;
}

.bs-chart--wc,
.bs-chart--map {
  flex: 1;
  min-height: 0;
  height: 100%;
  width: 100%;
}

/* 情感统计小卡片 */
.sentiment-cards {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.sent-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  border-radius: 10px;
  gap: 2px;
}

.sent-card--pos {
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.3);
}

.sent-card--neg {
  background: rgba(239,68,68,0.12);
  border: 1px solid rgba(239,68,68,0.3);
}

.sent-card--neu {
  background: rgba(100,116,139,0.18);
  border: 1px solid rgba(100,116,139,0.3);
}

.sent-icon {
  font-size: 16px;
}

.sent-num {
  font-size: 15px;
  font-weight: 700;
  color: #e8f0ff;
  font-variant-numeric: tabular-nums;
}

.sent-label {
  font-size: 10px;
  color: rgba(180,210,255,0.6);
}

/* ===================== 面板通用 ===================== */
.bs-panel {
  background: rgba(8, 18, 50, 0.65);
  border: 1px solid rgba(80, 130, 220, 0.2);
  border-radius: 14px;
  padding: 12px 14px;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 24px rgba(0, 0, 20, 0.4), inset 0 1px 0 rgba(100, 160, 255, 0.1);
  overflow: hidden;
}

.bs-panel--chart {
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.bs-panel--sm {
  min-height: 180px;
  display: flex;
  flex-direction: column;
}

.bs-panel--burst {
  min-height: 160px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(200, 225, 255, 0.9);
  letter-spacing: 0.04em;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.panel-title-icon {
  font-size: 15px;
}

.panel-live-tag {
  margin-left: auto;
  padding: 1px 7px;
  border-radius: 4px;
  background: rgba(255, 107, 107, 0.25);
  border: 1px solid rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  animation: blink 1.8s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.panel-keyword-badge {
  margin-left: auto;
  padding: 2px 10px;
  border-radius: 6px;
  background: rgba(77, 150, 255, 0.2);
  border: 1px solid rgba(77, 150, 255, 0.4);
  color: #7dd3fc;
  font-size: 11px;
  font-weight: 600;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===================== 左列：热搜榜 ===================== */
.bs-col--left {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bs-col--left .bs-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ranking-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rank-row {
  display: grid;
  grid-template-columns: 26px 1fr 52px 60px;
  align-items: center;
  gap: 7px;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.18s ease;
  border: 1px solid transparent;
}

.rank-row:hover {
  background: rgba(77, 150, 255, 0.12);
  border-color: rgba(77, 150, 255, 0.25);
}

.rank-row--top3 {
  background: rgba(255, 215, 0, 0.05);
  border-color: rgba(255, 215, 0, 0.15);
}

.rank-num {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  background: rgba(100, 150, 255, 0.15);
  color: rgba(200, 220, 255, 0.7);
}

.rank-num--gold {
  background: linear-gradient(135deg, #f7b731, #f9ca24);
  color: #1a1000;
}
.rank-num--silver {
  background: linear-gradient(135deg, #a0a0b0, #c8c8d8);
  color: #1a1a2a;
}
.rank-num--bronze {
  background: linear-gradient(135deg, #cd7f32, #e09060);
  color: #1a0800;
}

.rank-text {
  font-size: 12px;
  color: rgba(220, 235, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-heat {
  font-size: 11px;
  color: #ff6b6b;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.rank-bar-wrap {
  height: 4px;
  background: rgba(100, 150, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.rank-bar {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd93d);
  border-radius: 2px;
  transition: width 0.6s ease;
}

/* ===================== 中列 ===================== */
.bs-col--mid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.bs-chart {
  flex: 1;
  min-height: 0;
  height: 100%;
  width: 100%;
}

.chart-hint {
  text-align: center;
  font-size: 12px;
  color: rgba(150, 190, 255, 0.45);
  padding: 20px 0;
}

/* ===================== 右列 ===================== */
.bs-col--right {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.bs-chart-sm {
  flex: 1;
  min-height: 0;
  height: 100%;
  width: 100%;
}

/* 爆发列表 */
.burst-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.burst-item {
  display: grid;
  grid-template-columns: 20px 1fr 50px 40px;
  align-items: center;
  gap: 8px;
  padding: 7px 8px;
  border-radius: 8px;
  background: rgba(255, 107, 107, 0.06);
  border: 1px solid rgba(255, 107, 107, 0.15);
}

.burst-rank {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  background: rgba(255, 107, 107, 0.25);
  color: #ff6b6b;
  font-size: 10px;
  font-weight: 700;
}

.burst-keyword {
  font-size: 12px;
  color: rgba(220, 235, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.burst-prob {
  font-size: 12px;
  color: #ffd93d;
  font-weight: 600;
  text-align: right;
}

.burst-level {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 4px;
  text-align: center;
}

.level--burst {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.4);
}

.level--stable {
  background: rgba(77, 150, 255, 0.2);
  color: #7dd3fc;
  border: 1px solid rgba(77, 150, 255, 0.4);
}

.level--cool {
  background: rgba(107, 203, 119, 0.2);
  color: #6bcb77;
  border: 1px solid rgba(107, 203, 119, 0.4);
}

/* ===================== 底部状态栏 ===================== */
.bs-footer {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 24px;
  background: rgba(5, 12, 35, 0.7);
  border-top: 1px solid rgba(80, 130, 220, 0.12);
  font-size: 11px;
  color: rgba(130, 170, 220, 0.6);
  letter-spacing: 0.04em;
}

/* 空提示 */
.empty-tip {
  text-align: center;
  font-size: 12px;
  color: rgba(150, 190, 255, 0.4);
  padding: 20px 0;
}

/* 滚动条 */
.ranking-scroll::-webkit-scrollbar {
  width: 3px;
}
.ranking-scroll::-webkit-scrollbar-thumb {
  background: rgba(100, 150, 255, 0.3);
  border-radius: 2px;
}
</style>
