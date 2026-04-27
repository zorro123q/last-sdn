<template>
  <div class="bigscreen">
    <!-- 背景装饰 -->
    <div class="bg-grid"></div>
    <div class="bg-glow bg-glow--left"></div>
    <div class="bg-glow bg-glow--right"></div>

    <!-- 顶部标题栏 -->
    <header class="bs-header">
      <div class="bs-header-left">
        <div class="status-badge">
          <span class="status-dot"></span>
          <span class="status-text">系统运行中</span>
        </div>
        <div class="fetch-info">
          <span>最新采集：{{ summary.latest_fetch_time || "—" }}</span>
        </div>
      </div>
      <div class="bs-header-center">
        <h1 class="bs-title">微博热搜舆情监测中心</h1>
        <p class="bs-subtitle">实时采集 · 趋势分析 · 爆发识别 · 情感洞察 · 语义聚类</p>
      </div>
      <div class="bs-header-right">
        <div class="time-box">
          <span class="time-value">{{ currentTime }}</span>
          <span class="time-label">实时时钟</span>
        </div>
      </div>
    </header>

    <!-- 顶部指标卡片 -->
    <section class="metrics-bar">
      <div class="metric-card">
        <div class="metric-glow"></div>
        <span class="metric-label">累计采集记录</span>
        <span class="metric-value">{{ formatNumber(summary.total_records) }}</span>
      </div>
      <div class="metric-card">
        <div class="metric-glow"></div>
        <span class="metric-label">采集批次</span>
        <span class="metric-value">{{ formatNumber(summary.total_batches) }}</span>
      </div>
      <div class="metric-card">
        <div class="metric-glow"></div>
        <span class="metric-label">关键词总数</span>
        <span class="metric-value">{{ formatNumber(summary.total_keywords) }}</span>
      </div>
      <div class="metric-card">
        <div class="metric-glow"></div>
        <span class="metric-label">当前榜单数量</span>
        <span class="metric-value">{{ formatNumber(summary.latest_batch_count) }}</span>
      </div>
      <div class="metric-card metric-card--alert">
        <div class="metric-glow"></div>
        <span class="metric-label">高爆发话题数</span>
        <span class="metric-value" style="color: #f87171">{{ highBurstCount }}</span>
      </div>
    </section>

    <!-- 主体三栏 -->
    <section class="bs-main">
      <!-- 左栏：实时热搜排行 -->
      <div class="bs-col bs-col--left">
        <div class="bs-panel">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            实时热搜排行
            <span class="panel-live-tag">LIVE</span>
          </div>
          <div class="ranking-scroll">
            <div
              v-for="(item, index) in rankingList.slice(0, 15)"
              :key="`${item.title}-${index}`"
              class="rank-row"
              :class="{ 'rank-row--active': selectedKeyword === item.title, 'rank-row--top3': index < 3 }"
              @click="queryTrend(item.title)"
            >
              <span class="rank-num" :class="getRankNumClass(index + 1)">{{ index + 1 }}</span>
              <span class="rank-text" :title="item.title">{{ item.title }}</span>
              <span class="rank-heat">{{ shortHeat(item.hot_value) }}</span>
              <div class="rank-bar-wrap">
                <span class="rank-bar" :style="{ width: getHeatPercent(item.hot_value) + '%' }"></span>
              </div>
            </div>
            <div v-if="!rankingList.length" class="empty-tip">暂无热搜数据</div>
          </div>
        </div>
      </div>

      <!-- 中栏：地图 + 趋势 -->
      <div class="bs-col bs-col--mid">
        <div class="bs-panel bs-panel--map">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            全国评论热力分布
            <span v-if="selectedKeyword" class="panel-keyword-badge">{{ selectedKeyword }}</span>
          </div>
          <div ref="mapRef2" class="chart-map"></div>
        </div>
        <div class="bs-panel bs-panel--trend">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            话题热度趋势
            <span v-if="selectedKeyword" class="panel-keyword-badge">{{ selectedKeyword }}</span>
          </div>
          <div ref="trendChartRef" class="chart-trend"></div>
        </div>
      </div>

      <!-- 右栏：情绪 + 爆发 -->
      <div class="bs-col bs-col--right">
        <!-- 情绪仪表盘 -->
        <div class="bs-panel bs-panel--gauge">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            公众情绪指数
          </div>
          <div ref="gaugeRef" class="chart-gauge"></div>
        </div>

        <!-- 情感分布 -->
        <div class="bs-panel bs-panel--ring">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            情感分布
          </div>
          <div ref="sentPieRef2" class="chart-ring"></div>
        </div>

        <!-- 爆发趋势分布 -->
        <div class="bs-panel bs-panel--ring">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            爆发趋势分布
          </div>
          <div ref="burstPieRef" class="chart-ring"></div>
        </div>

        <!-- 爆发型热搜 Top5 -->
        <div class="bs-panel bs-panel--burst">
          <div class="panel-title">
            <span class="panel-title-bar"></span>
            爆发型热搜 Top5
          </div>
          <div class="burst-list">
            <div v-for="(item, i) in burstTop5" :key="item.keyword" class="burst-item">
              <span class="burst-rank">{{ i + 1 }}</span>
              <span class="burst-keyword" :title="item.keyword">{{ item.keyword }}</span>
              <span class="burst-prob">{{ formatPercent(item.burst_probability) }}</span>
              <span class="burst-level" :class="getLevelClass(item.burst_level)">{{ burstLevelText(item.burst_level) }}</span>
            </div>
            <div v-if="!burstTop5.length" class="empty-tip">暂无爆发趋势数据</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部三栏 -->
    <section class="bs-bottom">
      <!-- 热词词云 -->
      <div class="bs-panel bs-panel--bottom">
        <div class="panel-title">
          <span class="panel-title-bar"></span>
          热词词云
          <span v-if="selectedKeyword" class="panel-keyword-badge">{{ selectedKeyword }}</span>
        </div>
        <div ref="wordCloudRef2" class="chart-bottom"></div>
      </div>

      <!-- 爆发趋势气泡图 -->
      <div class="bs-panel bs-panel--bottom">
        <div class="panel-title">
          <span class="panel-title-bar"></span>
          爆发趋势气泡图
        </div>
        <div ref="scatterBsRef" class="chart-bottom"></div>
      </div>

      <!-- 自动洞察 -->
      <div class="bs-panel bs-panel--bottom bs-panel--insights">
        <div class="panel-title">
          <span class="panel-title-bar"></span>
          智能洞察
        </div>
        <div class="insights-list">
          <div v-for="(text, i) in insights" :key="i" class="insight-item">
            <span class="insight-dot" :class="`insight-dot--${i}`"></span>
            <span class="insight-text">{{ text }}</span>
          </div>
          <div v-if="!insights.length" class="empty-tip">暂无洞察数据</div>
        </div>
      </div>
    </section>

    <!-- 底部状态栏 -->
    <footer class="bs-footer">
      <span>系统状态：{{ statusText }}</span>
      <span>技术栈：Python · FastAPI · PySpark · KMeans · Vue3 · ECharts</span>
      <span>刷新间隔：60s</span>
      <span>上次刷新：{{ lastRefreshTime }}</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import "echarts-wordcloud";
import {
  getCurrentRanking, getDailyStats, getBurstTop, getSummary, getTrend,
  getTopKeywords, getCommentGeoData, getSentimentData, getWordCloudData,
  getSentimentSummary,
} from "../api/index.js";

/* ===== 状态 ===== */
const summary = ref({
  total_records: 0, total_batches: 0, total_keywords: 0,
  latest_batch_count: 0, latest_fetch_time: "",
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
const lastRefreshTime = ref("—");
const currentTime = ref("");

/* ===== 图表 DOM 引用 ===== */
const trendChartRef = ref(null);
const burstPieRef = ref(null);
const wordCloudRef2 = ref(null);
const sentPieRef2 = ref(null);
const mapRef2 = ref(null);
const scatterBsRef = ref(null);
const gaugeRef = ref(null);

let trendChart = null;
let burstPieChart = null;
let wordCloudChart2 = null;
let sentPieChart2 = null;
let mapChart2 = null;
let scatterBsChart = null;
let gaugeChart = null;
let refreshTimer = null;
let clockTimer = null;

/* ===== 计算属性 ===== */
const highBurstCount = computed(() => burstData.value.filter(i => Number(i.burst_level) >= 3).length);

const burstTop5 = computed(() => {
  const sorted = [...burstData.value].sort((a, b) => Number(b.burst_probability) - Number(a.burst_probability));
  return sorted.slice(0, 5);
});

const sentimentTotal = computed(() =>
  sentimentData.value.positive + sentimentData.value.negative + sentimentData.value.neutral
);

const maxHeat = computed(() => {
  if (!rankingList.value.length) return 1;
  return Math.max(...rankingList.value.map((item) => Number(item.hot_value || 0)));
});

const insights = computed(() => {
  const items = [];
  items.push(`当前共采集 ${formatNumber(summary.value.total_records)} 条热搜记录，最新采集时间为 ${summary.value.latest_fetch_time || "—"}。`);

  const top = rankingList.value[0];
  items.push(top ? `当前榜首话题为「${top.title}」，热度值为 ${shortHeat(top.hot_value)}。` : "暂无榜首话题数据。");

  const high = burstData.value.filter(i => Number(i.burst_level) >= 3);
  if (high.length > 0) {
    const topBurst = [...high].sort((a, b) => Number(b.burst_probability) - Number(a.burst_probability))[0];
    items.push(`当前高爆发话题共有 ${high.length} 个，其中「${topBurst.keyword}」爆发概率最高，达 ${formatPercent(topBurst.burst_probability)}。`);
  } else {
    const mid = burstData.value.filter(i => Number(i.burst_level) === 2);
    items.push(`当前高爆发话题共有 0 个，中爆发话题 ${mid.length} 个。`);
  }

  const total = sentimentTotal.value || 1;
  const posRate = ((sentimentData.value.positive / total) * 100).toFixed(1);
  const negRate = ((sentimentData.value.negative / total) * 100).toFixed(1);
  let dominant = "中性";
  if (sentimentData.value.positive > sentimentData.value.negative && sentimentData.value.positive > sentimentData.value.neutral) dominant = "正向";
  else if (sentimentData.value.negative > sentimentData.value.positive && sentimentData.value.negative > sentimentData.value.neutral) dominant = "负向";
  items.push(`当前评论情绪以${dominant}为主，正向占比 ${posRate}%，负向占比 ${negRate}%。`);

  return items;
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
  const n = Number(level);
  if (n >= 3) return "高爆发";
  if (n === 2) return "中爆发";
  return "低爆发";
}

function getLevelClass(level) {
  const n = Number(level);
  if (n >= 3) return "level--high";
  if (n === 2) return "level--mid";
  return "level--low";
}

function getRankNumClass(rank) {
  if (rank === 1) return "rank-num--gold";
  if (rank === 2) return "rank-num--silver";
  if (rank === 3) return "rank-num--bronze";
  return "";
}

function updateClock() {
  currentTime.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

/* ===== 省份名称映射 ===== */
const provinceNameMap = {
  北京: "北京市", 天津: "天津市", 上海: "上海市", 重庆: "重庆市",
  广东: "广东省", 江苏: "江苏省", 浙江: "浙江省", 山东: "山东省",
  四川: "四川省", 湖北: "湖北省", 湖南: "湖南省", 河南: "河南省",
  河北: "河北省", 山西: "山西省", 辽宁: "辽宁省", 吉林: "吉林省",
  黑龙江: "黑龙江省", 安徽: "安徽省", 福建: "福建省", 江西: "江西省",
  海南: "海南省", 贵州: "贵州省", 云南: "云南省", 陕西: "陕西省",
  甘肃: "甘肃省", 青海: "青海省", 台湾: "台湾省",
  内蒙古: "内蒙古自治区", 广西: "广西壮族自治区", 西藏: "西藏自治区",
  宁夏: "宁夏回族自治区", 新疆: "新疆维吾尔自治区",
  香港: "香港特别行政区", 澳门: "澳门特别行政区",
};

function normalizeProvinceName(name) {
  if (!name) return "";
  if (/[省市自治区特别行政区]$/.test(name)) return name;
  return provinceNameMap[name] || name;
}

function normalizeMapData(data) {
  return (data || []).map((item) => ({
    name: normalizeProvinceName(item.name),
    value: Number(item.value || 0),
    rawName: item.name,
  }));
}

/* ===== 暗色 ECharts 主题辅助 ===== */
const darkAxisStyle = {
  axisLabel: { color: "rgba(200,220,255,0.7)", fontSize: 11 },
  axisLine: { lineStyle: { color: "rgba(100,150,220,0.3)" } },
  splitLine: { lineStyle: { color: "rgba(100,150,220,0.12)" } },
};

/* ===== 图表构建 ===== */
function buildTrendChart() {
  if (!trendChartRef.value) return;
  if (!trendChart) trendChart = echarts.init(trendChartRef.value, null, { renderer: "canvas" });

  const times = trendPoints.value.map((p) => p.fetch_time?.slice(-8) || "");
  const values = trendPoints.value.map((p) => Number(p.hot_value || 0));

  trendChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" } },
    grid: { left: 50, right: 20, top: 14, bottom: 28 },
    xAxis: { type: "category", data: times, boundaryGap: false, ...darkAxisStyle, axisLabel: { ...darkAxisStyle.axisLabel, fontSize: 10 } },
    yAxis: {
      type: "value", ...darkAxisStyle,
      axisLabel: { ...darkAxisStyle.axisLabel, fontSize: 10, formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v) },
    },
    series: [{
      name: "热度值", type: "line", smooth: true, symbolSize: 5, data: values,
      lineStyle: { width: 2.5, color: "#38bdf8" }, itemStyle: { color: "#38bdf8" },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(56,189,248,0.35)" },
          { offset: 1, color: "rgba(56,189,248,0.02)" },
        ]),
      },
    }],
  }, true);
}

function buildBurstPieChart() {
  if (!burstPieRef.value) return;
  if (!burstPieChart) burstPieChart = echarts.init(burstPieRef.value, null, { renderer: "canvas" });

  const counts = { high: 0, mid: 0, low: 0 };
  burstData.value.forEach((item) => {
    const k = Number(item.burst_level);
    if (k >= 3) counts.high++;
    else if (k === 2) counts.mid++;
    else counts.low++;
  });

  burstPieChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" }, formatter: "{b}: {c} ({d}%)" },
    legend: { bottom: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 10 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      name: "爆发趋势", type: "pie", radius: ["38%", "68%"], center: ["50%", "44%"],
      label: { show: false },
      data: [
        { name: "高爆发", value: counts.high, itemStyle: { color: "#ef4444" } },
        { name: "中爆发", value: counts.mid, itemStyle: { color: "#f97316" } },
        { name: "低爆发", value: counts.low, itemStyle: { color: "#22c55e" } },
      ],
    }],
  }, true);
}

function buildSentPieChart2() {
  if (!sentPieRef2.value) return;
  if (!sentPieChart2) sentPieChart2 = echarts.init(sentPieRef2.value, null, { renderer: "canvas" });

  sentPieChart2.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item", backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" }, formatter: "{b}: {c} ({d}%)" },
    legend: { bottom: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 10 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: "pie", radius: ["38%", "68%"], center: ["50%", "44%"],
      label: { show: false },
      data: [
        { name: "正面", value: sentimentData.value.positive, itemStyle: { color: "#22c55e" } },
        { name: "负面", value: sentimentData.value.negative, itemStyle: { color: "#ef4444" } },
        { name: "中性", value: sentimentData.value.neutral, itemStyle: { color: "#64748b" } },
      ],
    }],
  }, true);
}

function buildSentimentGauge() {
  if (!gaugeRef.value) return;
  if (!gaugeChart) gaugeChart = echarts.init(gaugeRef.value, null, { renderer: "canvas" });

  const total = sentimentTotal.value || 1;
  const score = Math.round((sentimentData.value.positive / total) * 100);

  gaugeChart.setOption({
    backgroundColor: "transparent",
    series: [{
      type: "gauge",
      startAngle: 200, endAngle: -20,
      min: 0, max: 100,
      radius: "92%", center: ["50%", "55%"],
      axisLine: {
        lineStyle: {
          width: 8,
          color: [[0.4, "#ef4444"], [0.6, "#fbbf24"], [1, "#22c55e"]],
        },
      },
      pointer: { itemStyle: { color: "#38bdf8" }, width: 4, length: "60%" },
      axisTick: { distance: -8, length: 4, lineStyle: { color: "rgba(200,220,255,0.25)" } },
      splitLine: { distance: -8, length: 8, lineStyle: { color: "rgba(200,220,255,0.25)" } },
      axisLabel: { color: "rgba(200,220,255,0.45)", fontSize: 9, distance: 12 },
      detail: {
        valueAnimation: true,
        formatter: "{value}",
        color: "#e8f0ff",
        fontSize: 20,
        fontWeight: 700,
        offsetCenter: [0, "55%"],
      },
      data: [{ value: score, name: "正向指数" }],
      title: { offsetCenter: [0, "78%"], fontSize: 10, color: "rgba(200,220,255,0.55)" },
    }],
  }, true);
}

async function buildMapChart2() {
  if (!mapRef2.value) return;
  if (!mapChart2) mapChart2 = echarts.init(mapRef2.value, null, { renderer: "canvas" });

  let chinaGeoJson = null;
  try {
    const res = await fetch("https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json");
    chinaGeoJson = await res.json();
  } catch { chinaGeoJson = null; }

  if (chinaGeoJson) {
    echarts.registerMap("china_dark", chinaGeoJson);
  }

  const mapName = chinaGeoJson ? "china_dark" : "china";
  const mapData = normalizeMapData(geoDataBs.value);
  const maxValue = Math.max(...mapData.map((d) => d.value), 1);

  mapChart2.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(10,20,40,0.9)",
      borderColor: "rgba(100,160,255,0.4)",
      textStyle: { color: "#e8f0ff" },
      formatter: (p) => `<b>${p.name}</b><br/>评论数：${(p.value || 0).toLocaleString("zh-CN")}`,
    },
    visualMap: {
      min: 0, max: maxValue,
      left: 8, bottom: 20,
      text: ["多", "少"],
      inRange: { color: ["#0a1628", "#1a3a6e", "#2a6db5", "#3f9cf5", "#7dd3fc"] },
      textStyle: { color: "rgba(200,220,255,0.55)", fontSize: 10 },
      calculable: false,
      itemWidth: 10,
      itemHeight: 60,
    },
    series: [{
      name: "评论数", type: "map", map: mapName,
      roam: false, zoom: 1.15,
      label: { show: false },
      emphasis: {
        label: { show: true, color: "#fbbf24", fontSize: 11, fontWeight: 700 },
        itemStyle: { areaColor: "#fb923c" },
      },
      data: mapData,
      itemStyle: {
        borderColor: "rgba(77,150,255,0.3)",
        borderWidth: 0.8,
      },
    }],
  }, true);
}

function buildWordCloudChart2() {
  if (!wordCloudRef2.value) return;
  if (!wordCloudChart2) wordCloudChart2 = echarts.init(wordCloudRef2.value, null, { renderer: "canvas" });

  wordCloudChart2.setOption({
    backgroundColor: "transparent",
    series: [{
      type: "wordCloud",
      shape: "circle",
      left: "center", top: "center",
      width: "90%", height: "90%",
      sizeRange: [12, 52],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 6,
      drawOutOfBound: false,
      layoutAnimation: true,
      textStyle: {
        fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
        fontWeight: "bold",
        color: () => {
          const colors = ["#60a5fa", "#fbbf24", "#34d399", "#f87171", "#a78bfa", "#fb923c", "#22d3ee"];
          return colors[Math.floor(Math.random() * colors.length)];
        },
      },
      emphasis: {
        focus: "self",
        textStyle: { shadowBlur: 10, shadowColor: "rgba(255,255,255,0.3)" },
      },
      data: wordCloudDataBs.value,
    }],
  }, true);
}

function buildScatterChartBs() {
  if (!scatterBsRef.value) return;
  if (!scatterBsChart) scatterBsChart = echarts.init(scatterBsRef.value, null, { renderer: "canvas" });

  const data = burstData.value.slice(0, 40).map(item => ({
    name: item.keyword,
    value: [Number(item.hot_value_change_rate || 0), Number(item.rank_change || 0), Number(item.current_hot_value || 0)],
    level: Number(item.burst_level),
  }));

  scatterBsChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "rgba(10,20,40,0.9)", borderColor: "rgba(100,160,255,0.4)", textStyle: { color: "#e8f0ff" },
      formatter(p) {
        return `<div style="font-weight:700;margin-bottom:4px">${p.data.name}</div>` +
          `<div>热度变化率：${(p.data.value[0] * 100).toFixed(1)}%</div>` +
          `<div>排名变化：${p.data.value[1] > 0 ? '+' : ''}${p.data.value[1]}</div>` +
          `<div>当前热度：${shortHeat(p.data.value[2])}</div>` +
          `<div>趋势方向：${p.data.level >= 3 ? '高爆发' : p.data.level === 2 ? '中爆发' : '低爆发'}</div>`;
      },
    },
    legend: { top: 0, textStyle: { color: "rgba(200,220,255,0.7)", fontSize: 10 }, itemWidth: 10, itemHeight: 10, data: ["高爆发", "中爆发", "低爆发"] },
    grid: { left: 46, right: 16, top: 24, bottom: 36 },
    xAxis: {
      type: "value", name: "热度变化率", nameTextStyle: { color: "rgba(200,220,255,0.5)", fontSize: 10 },
      axisLabel: { color: "rgba(200,220,255,0.7)", fontSize: 10, formatter: v => `${(v * 100).toFixed(0)}%` },
      splitLine: { lineStyle: { color: "rgba(100,150,220,0.12)" } },
      axisLine: { lineStyle: { color: "rgba(100,150,220,0.3)" } },
    },
    yAxis: {
      type: "value", name: "排名变化", nameTextStyle: { color: "rgba(200,220,255,0.5)", fontSize: 10 },
      axisLabel: { color: "rgba(200,220,255,0.7)", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(100,150,220,0.12)" } },
      axisLine: { lineStyle: { color: "rgba(100,150,220,0.3)" } },
    },
    series: [
      { name: "高爆发", type: "scatter", symbolSize: d => Math.min(Math.max(Math.sqrt(d[2]) / 30, 5), 28), data: data.filter(d => d.level >= 3), itemStyle: { color: "#ef4444", opacity: 0.85 } },
      { name: "中爆发", type: "scatter", symbolSize: d => Math.min(Math.max(Math.sqrt(d[2]) / 30, 5), 28), data: data.filter(d => d.level === 2), itemStyle: { color: "#f97316", opacity: 0.85 } },
      { name: "低爆发", type: "scatter", symbolSize: d => Math.min(Math.max(Math.sqrt(d[2]) / 30, 5), 28), data: data.filter(d => d.level <= 1), itemStyle: { color: "#22c55e", opacity: 0.85 } },
    ],
  }, true);
}

/* ===== 数据加载 ===== */
async function loadAllData() {
  try {
    const [summaryRes, rankingRes, dailyRes, keywordsRes, burstRes] = await Promise.allSettled([
      getSummary(), getCurrentRanking(), getDailyStats(), getTopKeywords(10), getBurstTop(100),
    ]);
    if (summaryRes.status === "fulfilled") summary.value = summaryRes.value;
    if (rankingRes.status === "fulfilled") rankingList.value = rankingRes.value.items || [];
    if (dailyRes.status === "fulfilled") dailyStats.value = dailyRes.value.items || [];
    if (keywordsRes.status === "fulfilled") topKeywords.value = keywordsRes.value.items || [];
    if (burstRes.status === "fulfilled") burstData.value = burstRes.value.items || [];

    const kw = selectedKeyword.value || (rankingList.value[0]?.title || "");
    const [sentRes, wcRes, geoRes, sentSummaryRes] = await Promise.allSettled([
      getSentimentData(kw), getWordCloudData(kw), getCommentGeoData(kw), getSentimentSummary(),
    ]);
    if (sentRes.status === "fulfilled") sentimentData.value = sentRes.value;
    if (wcRes.status === "fulfilled") wordCloudDataBs.value = wcRes.value || [];
    if (geoRes.status === "fulfilled") geoDataBs.value = geoRes.value || [];

    lastRefreshTime.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    statusText.value = "数据正常";
  } catch (e) {
    statusText.value = "部分数据加载失败";
  }

  await nextTick();
  buildTrendChart(); buildBurstPieChart(); buildSentPieChart2();
  buildSentimentGauge(); buildMapChart2(); buildWordCloudChart2(); buildScatterChartBs();

  if (rankingList.value.length && !selectedKeyword.value) {
    await queryTrend(rankingList.value[0].title);
  }
}

async function queryTrend(kw) {
  selectedKeyword.value = kw;
  try {
    const [trendRes, sentRes, wcRes, geoRes] = await Promise.allSettled([
      getTrend(kw), getSentimentData(kw), getWordCloudData(kw), getCommentGeoData(kw),
    ]);
    if (trendRes.status === "fulfilled") trendPoints.value = trendRes.value.points || [];
    if (sentRes.status === "fulfilled") sentimentData.value = sentRes.value;
    if (wcRes.status === "fulfilled") wordCloudDataBs.value = wcRes.value || [];
    if (geoRes.status === "fulfilled") geoDataBs.value = geoRes.value || [];
  } catch (e) {
    trendPoints.value = [];
  }
  await nextTick();
  buildTrendChart(); buildMapChart2(); buildWordCloudChart2();
  buildSentPieChart2(); buildSentimentGauge();
}

/* ===== 生命周期 ===== */
function handleResize() {
  [trendChart, burstPieChart, sentPieChart2, mapChart2, wordCloudChart2, scatterBsChart, gaugeChart].forEach((c) => c?.resize());
}

onMounted(async () => {
  await loadAllData();
  updateClock();
  window.addEventListener("resize", handleResize);
  refreshTimer = setInterval(loadAllData, 60000);
  clockTimer = setInterval(updateClock, 1000);
});

onBeforeUnmount(() => {
  clearInterval(refreshTimer);
  clearInterval(clockTimer);
  window.removeEventListener("resize", handleResize);
  [trendChart, burstPieChart, sentPieChart2, mapChart2, wordCloudChart2, scatterBsChart, gaugeChart].forEach((c) => { if (c) c.dispose(); });
  trendChart = null; burstPieChart = null; sentPieChart2 = null; mapChart2 = null;
  wordCloudChart2 = null; scatterBsChart = null; gaugeChart = null;
});
</script>

<style scoped>
/* ===================== 大屏容器 ===================== */
.bigscreen {
  width: 100vw;
  height: 100vh;
  background:
    radial-gradient(ellipse at 20% 10%, rgba(20, 50, 110, 0.6), transparent 50%),
    radial-gradient(ellipse at 80% 90%, rgba(80, 20, 60, 0.4), transparent 50%),
    linear-gradient(165deg, #040d1f 0%, #081426 50%, #0c1220 100%);
  color: #e8f0ff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* 背景网格 */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(80, 140, 240, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(80, 140, 240, 0.04) 1px, transparent 1px);
  background-size: 56px 56px;
  pointer-events: none;
  z-index: 0;
}

/* 光晕装饰 */
.bg-glow {
  position: absolute;
  width: 700px;
  height: 700px;
  border-radius: 50%;
  filter: blur(140px);
  pointer-events: none;
  z-index: 0;
}
.bg-glow--left {
  top: -250px;
  left: -250px;
  background: radial-gradient(circle, rgba(40, 90, 200, 0.22), transparent 70%);
}
.bg-glow--right {
  bottom: -250px;
  right: -250px;
  background: radial-gradient(circle, rgba(180, 40, 100, 0.14), transparent 70%);
}

/* ===================== 顶部标题栏 ===================== */
.bs-header {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  align-items: center;
  gap: 20px;
  padding: 10px 24px 8px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.15);
  background: rgba(4, 12, 30, 0.7);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}

.bs-header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(180, 220, 255, 0.8);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6); }
  50% { opacity: 0.6; box-shadow: 0 0 4px rgba(34, 197, 94, 0.3); }
}

.fetch-info {
  font-size: 11px;
  color: rgba(150, 190, 255, 0.55);
}

.bs-header-center {
  text-align: center;
}

.bs-title {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.08em;
  margin: 0;
  background: linear-gradient(135deg, #38bdf8, #a5f3fc, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
  text-shadow: 0 0 30px rgba(56, 189, 248, 0.3);
}

.bs-subtitle {
  font-size: 12px;
  color: rgba(150, 190, 255, 0.5);
  margin: 4px 0 0;
  letter-spacing: 0.15em;
}

.bs-header-right {
  display: flex;
  justify-content: flex-end;
}

.time-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.time-value {
  font-size: 22px;
  font-weight: 700;
  color: #38bdf8;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
  letter-spacing: 0.04em;
}

.time-label {
  font-size: 10px;
  color: rgba(150, 190, 255, 0.5);
  letter-spacing: 0.1em;
}

/* ===================== 指标卡片 ===================== */
.metrics-bar {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  padding: 10px 24px;
  flex-shrink: 0;
}

.metric-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: 12px;
  background: rgba(8, 20, 38, 0.78);
  border: 1px solid rgba(56, 189, 248, 0.25);
  box-shadow: 0 0 24px rgba(14, 165, 233, 0.12);
  overflow: hidden;
  transition: transform 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-1px);
}

.metric-glow {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 40px;
  background: radial-gradient(ellipse, rgba(56, 189, 248, 0.25), transparent 70%);
  pointer-events: none;
}

.metric-card--alert {
  border-color: rgba(248, 113, 113, 0.35);
  box-shadow: 0 0 24px rgba(248, 113, 113, 0.12);
}

.metric-card--alert .metric-glow {
  background: radial-gradient(ellipse, rgba(248, 113, 113, 0.25), transparent 70%);
}

.metric-label {
  font-size: 11px;
  color: rgba(150, 190, 255, 0.6);
  letter-spacing: 0.06em;
}

.metric-value {
  font-size: 24px;
  font-weight: 800;
  color: #38bdf8;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
  line-height: 1.1;
}

/* ===================== 主体区域 ===================== */
.bs-main {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 280px 1fr 300px;
  gap: 12px;
  padding: 0 24px;
  flex: 1;
  min-height: 0;
}

.bs-bottom {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  padding: 0 24px 10px;
  height: 220px;
  flex-shrink: 0;
}

/* ===================== 面板通用 ===================== */
.bs-panel {
  background: rgba(8, 20, 38, 0.78);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 16px;
  padding: 10px 12px;
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 24px rgba(0, 0, 20, 0.35), inset 0 1px 0 rgba(100, 160, 255, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: rgba(220, 240, 255, 0.95);
  letter-spacing: 0.04em;
  margin-bottom: 8px;
  flex-shrink: 0;
  position: relative;
  padding-left: 10px;
}

.panel-title-bar {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 14px;
  background: linear-gradient(180deg, #38bdf8, #2563eb);
  border-radius: 2px;
}

.panel-live-tag {
  margin-left: auto;
  padding: 1px 7px;
  border-radius: 4px;
  background: rgba(248, 113, 113, 0.2);
  border: 1px solid rgba(248, 113, 113, 0.45);
  color: #f87171;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  animation: blink 1.8s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.panel-keyword-badge {
  margin-left: auto;
  padding: 2px 10px;
  border-radius: 6px;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #7dd3fc;
  font-size: 11px;
  font-weight: 600;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===================== 左栏：热搜排行 ===================== */
.bs-col--left {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.bs-col--left .bs-panel {
  flex: 1;
  overflow: hidden;
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
  grid-template-columns: 24px 1fr 50px 50px;
  align-items: center;
  gap: 6px;
  padding: 5px 7px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.rank-row:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.25);
}

.rank-row--active {
  background: rgba(56, 189, 248, 0.18);
  border-color: rgba(56, 189, 248, 0.4);
}

.rank-row--top3 {
  background: rgba(251, 191, 36, 0.06);
  border-color: rgba(251, 191, 36, 0.12);
}

.rank-num {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 700;
  background: rgba(56, 189, 248, 0.12);
  color: rgba(200, 220, 255, 0.7);
  flex-shrink: 0;
}

.rank-num--gold {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: #1a1000;
}
.rank-num--silver {
  background: linear-gradient(135deg, #94a3b8, #cbd5e1);
  color: #1a1a2a;
}
.rank-num--bronze {
  background: linear-gradient(135deg, #b45309, #d97706);
  color: #fff;
}

.rank-text {
  font-size: 12px;
  color: rgba(220, 235, 255, 0.92);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-heat {
  font-size: 10px;
  color: #f87171;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.rank-bar-wrap {
  height: 3px;
  background: rgba(56, 189, 248, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.rank-bar {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #f87171, #fbbf24);
  border-radius: 2px;
  transition: width 0.6s ease;
}

/* ===================== 中栏：地图 + 趋势 ===================== */
.bs-col--mid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.bs-panel--map {
  flex: 1.3;
  min-height: 0;
}

.bs-panel--trend {
  flex: 1;
  min-height: 0;
}

.chart-map {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.chart-trend {
  flex: 1;
  min-height: 0;
  width: 100%;
}

/* ===================== 右栏 ===================== */
.bs-col--right {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.bs-panel--gauge {
  height: 140px;
  flex-shrink: 0;
}

.chart-gauge {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.bs-panel--ring {
  height: 130px;
  flex-shrink: 0;
}

.chart-ring {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.bs-panel--burst {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 爆发列表 */
.burst-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
  overflow-y: auto;
  padding-right: 2px;
}

.burst-item {
  display: grid;
  grid-template-columns: 18px 1fr 48px 44px;
  align-items: center;
  gap: 6px;
  padding: 5px 7px;
  border-radius: 7px;
  background: rgba(248, 113, 113, 0.06);
  border: 1px solid rgba(248, 113, 113, 0.12);
}

.burst-rank {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(248, 113, 113, 0.2);
  color: #f87171;
  font-size: 9px;
  font-weight: 700;
}

.burst-keyword {
  font-size: 11px;
  color: rgba(220, 235, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.burst-prob {
  font-size: 10px;
  color: #fbbf24;
  font-weight: 600;
  text-align: right;
}

.burst-level {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  text-align: center;
}

.level--high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
}
.level--mid {
  background: rgba(249, 115, 22, 0.2);
  color: #f97316;
  border: 1px solid rgba(249, 115, 22, 0.4);
}
.level--low {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.35);
}

/* ===================== 底部三栏 ===================== */
.bs-panel--bottom {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-bottom {
  flex: 1;
  min-height: 0;
  width: 100%;
}

/* 洞察卡片 */
.bs-panel--insights {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.insights-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(56, 189, 248, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.12);
  line-height: 1.5;
}

.insight-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.insight-dot--0 { background: #38bdf8; box-shadow: 0 0 6px rgba(56,189,248,0.5); }
.insight-dot--1 { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.insight-dot--2 { background: #f97316; box-shadow: 0 0 6px rgba(249,115,22,0.5); }
.insight-dot--3 { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.5); }

.insight-text {
  font-size: 12px;
  color: rgba(200, 225, 255, 0.85);
}

/* ===================== 底部状态栏 ===================== */
.bs-footer {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 24px;
  background: rgba(4, 12, 30, 0.75);
  border-top: 1px solid rgba(56, 189, 248, 0.12);
  font-size: 11px;
  color: rgba(130, 170, 220, 0.55);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

/* 空提示 */
.empty-tip {
  text-align: center;
  font-size: 12px;
  color: rgba(150, 190, 255, 0.35);
  padding: 16px 0;
}

/* 滚动条 */
.ranking-scroll::-webkit-scrollbar,
.burst-list::-webkit-scrollbar,
.insights-list::-webkit-scrollbar {
  width: 3px;
}
.ranking-scroll::-webkit-scrollbar-thumb,
.burst-list::-webkit-scrollbar-thumb,
.insights-list::-webkit-scrollbar-thumb {
  background: rgba(56, 189, 248, 0.25);
  border-radius: 2px;
}
</style>
