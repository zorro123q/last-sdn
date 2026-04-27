<template>
  <div class="page-shell">
    <main class="sentiment-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">评论地理分布 · 热词词云 · 情感分析</p>
          <h1>大数据评论可视化分析</h1>
          <p class="hero-text">
            基于微博热搜评论数据，展示全国评论地理分布热力图、高频热词词云，以及正面/负面/中性情感统计分析。
          </p>
        </div>
        <div class="hero-actions">
          <div class="keyword-selector">
            <span class="selector-label">当前热搜</span>
            <select v-model="selectedKeyword" class="kw-select" @change="onKeywordChange">
              <option v-for="item in hotKeywords" :key="item" :value="item">{{ item }}</option>
            </select>
          </div>
          <button class="btn btn--outline" @click="loadAllData" :disabled="loading">
            <svg class="btn-icon" :class="{ spin: loading }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            {{ loading ? "加载中..." : "刷新" }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        {{ pageError }}
      </div>

      <!-- 情感统计卡片 -->
      <section class="cards">
        <article class="card card--pos">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">正面评论</span>
            <strong class="card-value card-value--pos">{{ formatNumber(sentiment.positive) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.positive }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.positive + '%', '--color': '#22c55e' }"></div>
        </article>
        <article class="card card--neg">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">负面评论</span>
            <strong class="card-value card-value--neg">{{ formatNumber(sentiment.negative) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.negative }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.negative + '%', '--color': '#ef4444' }"></div>
        </article>
        <article class="card card--neu">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">中性评论</span>
            <strong class="card-value card-value--neu">{{ formatNumber(sentiment.neutral) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.neutral }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.neutral + '%', '--color': '#94a3b8' }"></div>
        </article>
        <article class="card card--total">
          <div class="card-icon-wrap">
            <svg class="card-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
            </svg>
          </div>
          <div class="card-body">
            <span class="card-label">总评论数</span>
            <strong class="card-value">{{ formatNumber(sentimentTotal) }}</strong>
            <span class="card-rate">情感覆盖率 100%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': '100%', '--color': '#2563eb' }"></div>
        </article>
      </section>

      <!-- 主体双栏 -->
      <section class="main-grid">
        <!-- 左：中国地图 -->
        <section class="panel panel--map">
          <div class="panel-header">
            <div>
              <h2>全国评论地理分布</h2>
              <p>热搜话题评论用户的省份分布热力图（颜色越深代表讨论越热烈）</p>
            </div>
            <div class="panel-tag">{{ selectedKeyword || "热搜话题" }}</div>
          </div>
          <div ref="mapRef" class="chart-map"></div>
        </section>

        <!-- 右：词云 -->
        <section class="panel panel--wordcloud">
          <div class="panel-header">
            <div>
              <h2>热词词云</h2>
              <p>评论与标题中高频词汇可视化，字号越大代表出现频率越高</p>
            </div>
            <div class="panel-tag">Top {{ wordCloudData.length }} 词</div>
          </div>
          <div ref="wordCloudRef" class="chart-wordcloud"></div>
        </section>
      </section>

      <!-- 情感趋势 + 省份 Top10 -->
      <section class="bottom-grid">
        <!-- 情感趋势折线图 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>情感趋势变化</h2>
              <p>随时间推移正面/负面/中性评论数量变化趋势</p>
            </div>
          </div>
          <div ref="sentimentTrendRef" class="chart"></div>
        </section>

        <!-- 省份 Top10 评论榜 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>省份评论 Top10</h2>
              <p>讨论最活跃的省份排行榜</p>
            </div>
          </div>
          <div class="province-list">
            <div
              v-for="(item, index) in provinceTop10"
              :key="item.name"
              class="province-item"
            >
              <span class="prov-rank" :class="getProvRankClass(index + 1)">{{ index + 1 }}</span>
              <span class="prov-name">{{ item.name }}</span>
              <div class="prov-bar-wrap">
                <div
                  class="prov-bar"
                  :style="{ width: getProvPercent(item.value) + '%', background: getProvColor(index) }"
                ></div>
              </div>
              <span class="prov-value">{{ formatNumber(item.value) }}</span>
            </div>
          </div>
        </section>
      </section>

      <!-- 情感饼图 + 情感关键词 -->
      <section class="bottom-grid">
        <!-- 情感占比饼图 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>情感占比分布</h2>
              <p>正面、负面、中性评论的整体占比环形图</p>
            </div>
          </div>
          <div ref="sentimentPieRef" class="chart"></div>
        </section>

        <!-- 情感关键词列表 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>情感关键词分析</h2>
              <p>正面与负面情感中最具代表性的高频词汇</p>
            </div>
          </div>
          <div class="sentiment-keywords">
            <div class="sk-group">
              <div class="sk-group-title sk-pos">正面关键词</div>
              <div class="sk-tags">
                <span v-for="kw in posKeywords" :key="kw.word" class="sk-tag sk-tag--pos">
                  {{ kw.word }}
                  <em>{{ kw.count }}</em>
                </span>
              </div>
            </div>
            <div class="sk-group">
              <div class="sk-group-title sk-neg">负面关键词</div>
              <div class="sk-tags">
                <span v-for="kw in negKeywords" :key="kw.word" class="sk-tag sk-tag--neg">
                  {{ kw.word }}
                  <em>{{ kw.count }}</em>
                </span>
              </div>
            </div>
          </div>
        </section>
      </section>

    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import "echarts-wordcloud";
import { getCurrentRanking, getCommentGeoData, getSentimentData, getWordCloudData } from "../api/index.js";

/* ===== 状态 ===== */
const loading = ref(false);
const pageError = ref("");
const hotKeywords = ref([]);
const selectedKeyword = ref("");
const sentiment = ref({ positive: 0, negative: 0, neutral: 0 });
const geoData = ref([]);
const wordCloudData = ref([]);
const sentimentTrend = ref([]);

/* ===== 图表 DOM ===== */
const mapRef = ref(null);
const wordCloudRef = ref(null);
const sentimentTrendRef = ref(null);
const sentimentPieRef = ref(null);

let mapChart = null;
let wordCloudChart = null;
let trendChart = null;
let pieChart = null;

/* ===== 计算属性 ===== */
const sentimentTotal = computed(() =>
  sentiment.value.positive + sentiment.value.negative + sentiment.value.neutral
);

const sentimentRate = computed(() => {
  const total = sentimentTotal.value || 1;
  return {
    positive: ((sentiment.value.positive / total) * 100).toFixed(1),
    negative: ((sentiment.value.negative / total) * 100).toFixed(1),
    neutral: ((sentiment.value.neutral / total) * 100).toFixed(1),
  };
});

const provinceTop10 = computed(() =>
  [...geoData.value]
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)
);

const maxProvinceVal = computed(() =>
  provinceTop10.value.length ? provinceTop10.value[0].value : 1
);

// 模拟正/负面情感关键词
const posKeywords = ref([
  { word: "支持", count: 2341 }, { word: "点赞", count: 1982 }, { word: "感动", count: 1756 },
  { word: "棒棒的", count: 1421 }, { word: "厉害", count: 1204 }, { word: "太好了", count: 987 },
  { word: "加油", count: 876 }, { word: "开心", count: 754 }, { word: "佩服", count: 632 },
]);

const negKeywords = ref([
  { word: "心疼", count: 1876 }, { word: "无语", count: 1654 }, { word: "失望", count: 1432 },
  { word: "愤怒", count: 1123 }, { word: "难受", count: 987 }, { word: "不行", count: 765 },
  { word: "可怕", count: 654 }, { word: "糟糕", count: 543 }, { word: "反对", count: 432 },
]);

/* ===== 工具函数 ===== */
function formatNumber(value) {
  const n = Number(value || 0);
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`;
  return n.toLocaleString("zh-CN");
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

function getProvPercent(value) {
  return Math.round((value / maxProvinceVal.value) * 100);
}

function getProvColor(index) {
  const colors = ["#2563eb", "#3b82f6", "#60a5fa", "#06b6d4", "#22c55e",
    "#8b5cf6", "#a78bfa", "#f59e0b", "#f97316", "#ef4444"];
  return colors[index % colors.length];
}

function getProvRankClass(rank) {
  if (rank === 1) return "prov-rank--gold";
  if (rank === 2) return "prov-rank--silver";
  if (rank === 3) return "prov-rank--bronze";
  return "";
}

/* ===== 图表构建 ===== */
// 中国地图
async function buildMapChart() {
  if (!mapRef.value) return;
  if (!mapChart) {
    mapChart = echarts.init(mapRef.value);
  }

  // 动态加载中国地图数据（从 CDN 获取）
  let chinaGeoJson = null;
  try {
    const res = await fetch("https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json");
    chinaGeoJson = await res.json();
  } catch {
    chinaGeoJson = null;
  }

  if (chinaGeoJson) {
    echarts.registerMap("china", chinaGeoJson);
  }

  const mapData = normalizeMapData(geoData.value);
  const maxValue = Math.max(...mapData.map((d) => d.value), 1);

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff", fontSize: 13 },
      formatter: (params) => {
        const val = params.value || 0;
        return `<b>${params.name}</b><br/>评论数：${val.toLocaleString("zh-CN")}`;
      },
    },
    visualMap: {
      type: "piecewise",
      left: 20,
      bottom: 40,
      pieces: [
        { min: 40000, color: "#0c4a6e", label: "4万以上" },
        { min: 30000, max: 39999, color: "#0369a1", label: "3万-4万" },
        { min: 20000, max: 29999, color: "#0ea5e9", label: "2万-3万" },
        { min: 10000, max: 19999, color: "#7dd3fc", label: "1万-2万" },
        { min: 1, max: 9999, color: "#e0f2fe", label: "1万以下" },
        { value: 0, color: "#f1f5f9", label: "无数据" },
      ],
      textStyle: { color: "#64748b", fontSize: 11 },
      itemWidth: 16,
      itemHeight: 14,
      itemGap: 6,
    },
    series: [
      {
        name: "评论数",
        type: "map",
        map: "china",
        roam: true,
        zoom: 1.1,
        label: {
          show: true,
          fontSize: 9,
          color: "#64748b",
        },
        emphasis: {
          label: { show: true, color: "#0f172a", fontWeight: 700 },
          itemStyle: { areaColor: "#f59e0b" },
        },
        data: mapData,
        itemStyle: {
          borderColor: "#94a3b8",
          borderWidth: 0.8,
        },
      },
    ],
  };

  mapChart.setOption(option, true);
}

// 词云图
function buildWordCloudChart() {
  if (!wordCloudRef.value) return;
  if (!wordCloudChart) {
    wordCloudChart = echarts.init(wordCloudRef.value);
  }

  wordCloudChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      show: true,
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: (params) => `${params.name}：${params.value}次`,
    },
    series: [
      {
        type: "wordCloud",
        shape: "circle",
        left: "center",
        top: "center",
        width: "92%",
        height: "92%",
        right: null,
        bottom: null,
        sizeRange: [14, 72],
        rotationRange: [-45, 45],
        rotationStep: 15,
        gridSize: 8,
        drawOutOfBound: false,
        layoutAnimation: true,
        textStyle: {
          fontFamily: "PingFang SC, Microsoft YaHei, sans-serif",
          fontWeight: "bold",
          color: () => {
            const colors = [
              "#2563eb", "#3b82f6", "#60a5fa", "#06b6d4", "#22c55e",
              "#8b5cf6", "#f59e0b", "#f97316", "#ec4899", "#14b8a6",
            ];
            return colors[Math.floor(Math.random() * colors.length)];
          },
        },
        emphasis: {
          focus: "self",
          textStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" },
        },
        data: wordCloudData.value,
      },
    ],
  }, true);
}

// 情感趋势折线图
function buildTrendChart() {
  if (!sentimentTrendRef.value) return;
  if (!trendChart) {
    trendChart = echarts.init(sentimentTrendRef.value);
  }

  const dates = sentimentTrend.value.map((d) => d.date);
  const posValues = sentimentTrend.value.map((d) => d.positive);
  const negValues = sentimentTrend.value.map((d) => d.negative);
  const neuValues = sentimentTrend.value.map((d) => d.neutral);

  trendChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: {
      top: 4,
      right: 20,
      textStyle: { color: "#64748b", fontSize: 12 },
    },
    grid: { left: 50, right: 20, top: 36, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLabel: { color: "#64748b", fontSize: 11, rotate: 20 },
      axisLine: { lineStyle: { color: "#cbd5e1" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#64748b", fontSize: 11 },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.2)" } },
    },
    series: [
      {
        name: "正面",
        type: "line",
        smooth: true,
        symbolSize: 6,
        data: posValues,
        lineStyle: { width: 2.5, color: "#22c55e" },
        itemStyle: { color: "#22c55e" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(34,197,94,0.2)" },
            { offset: 1, color: "rgba(34,197,94,0.02)" },
          ]),
        },
      },
      {
        name: "负面",
        type: "line",
        smooth: true,
        symbolSize: 6,
        data: negValues,
        lineStyle: { width: 2.5, color: "#ef4444" },
        itemStyle: { color: "#ef4444" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(239,68,68,0.2)" },
            { offset: 1, color: "rgba(239,68,68,0.02)" },
          ]),
        },
      },
      {
        name: "中性",
        type: "line",
        smooth: true,
        symbolSize: 6,
        data: neuValues,
        lineStyle: { width: 2, color: "#94a3b8" },
        itemStyle: { color: "#94a3b8" },
      },
    ],
  }, true);
}

// 情感饼图
function buildPieChart() {
  if (!sentimentPieRef.value) return;
  if (!pieChart) {
    pieChart = echarts.init(sentimentPieRef.value);
  }

  pieChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      bottom: 20,
      textStyle: { color: "#64748b", fontSize: 12 },
    },
    series: [
      {
        name: "情感分布",
        type: "pie",
        radius: ["42%", "68%"],
        center: ["50%", "45%"],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: "{b}\n{d}%",
          color: "#374151",
          fontSize: 12,
          fontWeight: 600,
        },
        labelLine: { lineStyle: { color: "#cbd5e1" } },
        data: [
          {
            name: "正面评论",
            value: sentiment.value.positive,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "#4ade80" },
                { offset: 1, color: "#22c55e" },
              ]),
            },
          },
          {
            name: "负面评论",
            value: sentiment.value.negative,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "#f87171" },
                { offset: 1, color: "#ef4444" },
              ]),
            },
          },
          {
            name: "中性评论",
            value: sentiment.value.neutral,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "#cbd5e1" },
                { offset: 1, color: "#94a3b8" },
              ]),
            },
          },
        ],
      },
    ],
  }, true);
}

/* ===== 数据加载 ===== */
async function loadAllData() {
  loading.value = true;
  pageError.value = "";

  try {
    // 加载热搜列表
    const rankRes = await getCurrentRanking().catch(() => ({ items: [] }));
    hotKeywords.value = (rankRes.items || []).slice(0, 20).map((i) => i.title);
    if (!selectedKeyword.value && hotKeywords.value.length) {
      selectedKeyword.value = hotKeywords.value[0];
    }

    // 并行加载地理分布、情感数据、词云
    const [geoRes, sentRes, wcRes, trendRes] = await Promise.allSettled([
      getCommentGeoData(selectedKeyword.value),
      getSentimentData(selectedKeyword.value),
      getWordCloudData(selectedKeyword.value),
      getSentimentData(selectedKeyword.value, true),
    ]);

    if (geoRes.status === "fulfilled") geoData.value = geoRes.value || [];
    if (sentRes.status === "fulfilled") {
      const s = sentRes.value || {};
      sentiment.value = {
        positive: s.positive || 0,
        negative: s.negative || 0,
        neutral: s.neutral || 0,
      };
    }
    if (wcRes.status === "fulfilled") wordCloudData.value = wcRes.value || [];
    if (trendRes.status === "fulfilled" && trendRes.value?.trend) {
      sentimentTrend.value = trendRes.value.trend || [];
    }
  } catch (e) {
    pageError.value = "部分数据加载失败，已使用演示数据展示效果";
  }

  loading.value = false;
  await nextTick();
  buildMapChart();
  buildWordCloudChart();
  buildTrendChart();
  buildPieChart();
}

async function onKeywordChange() {
  await loadAllData();
}

/* ===== 生命周期 ===== */
function handleResize() {
  [mapChart, wordCloudChart, trendChart, pieChart].forEach((c) => c?.resize());
}

onMounted(async () => {
  await loadAllData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  [mapChart, wordCloudChart, trendChart, pieChart].forEach((c) => {
    if (c) { c.dispose(); }
  });
  mapChart = null;
  wordCloudChart = null;
  trendChart = null;
  pieChart = null;
});
</script>

<style scoped>
.page-shell {
  min-height: calc(100vh - 64px);
  padding: 24px;
}

.sentiment-page {
  max-width: 1440px;
  margin: 0 auto;
  display: grid;
  gap: 24px;
}

/* ===================== Hero ===================== */
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 32px;
  border-radius: var(--radius-card);
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 52px rgba(37, 99, 235, 0.2), 0 1px 0 rgba(255, 255, 255, 0.1) inset;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.08), transparent 50%);
  pointer-events: none;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.12em;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  line-height: 1.15;
  color: #fff;
  letter-spacing: -0.02em;
}

h2 {
  margin: 0 0 5px;
  font-size: 18px;
  font-weight: 700;
  color: var(--navy);
}

p {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
}

.hero-text {
  margin-top: 10px;
  max-width: 640px;
  line-height: 1.7;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.keyword-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
}

.kw-select {
  padding: 9px 14px;
  border-radius: var(--radius-btn);
  border: 1.5px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  font-size: 13px;
  color: #fff;
  cursor: pointer;
  outline: none;
  min-width: 160px;
  max-width: 220px;
  transition: border-color 0.2s;
  backdrop-filter: blur(4px);
}

.kw-select option {
  color: var(--text-base);
}

.kw-select:focus {
  border-color: rgba(255, 255, 255, 0.6);
}

/* ===================== 按钮 ===================== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: var(--radius-btn);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn--outline {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  backdrop-filter: blur(4px);
}

.btn--outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.btn--outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
  display: inline-block;
  transition: transform 0.3s;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===================== 消息提示 ===================== */
.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.alert-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.alert--error {
  background: rgba(239, 68, 68, 0.07);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #dc2626;
}

/* ===================== 统计卡片 ===================== */
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.card {
  padding: 22px 20px 28px;
  border-radius: var(--radius-card);
  background: var(--bg-glass);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
}

.card-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon-svg {
  width: 24px;
  height: 24px;
}

.card-body {
  flex: 1;
}

.card-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
  font-weight: 500;
}

.card-value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: var(--navy);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.card-value--pos { color: #16a34a; }
.card-value--neg { color: #dc2626; }
.card-value--neu { color: #475569; }

.card-rate {
  display: block;
  font-size: 12px;
  font-weight: 500;
  margin-top: 4px;
  color: var(--text-light);
}

/* 底部进度条 */
.card-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(148, 163, 184, 0.15);
}

.card-bar::after {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: var(--fill);
  background: var(--color);
  border-radius: 0 2px 2px 0;
  transition: width 0.8s ease;
}

.card--pos { border-top: 3px solid #22c55e; }
.card--pos .card-icon-wrap { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
.card--neg { border-top: 3px solid #ef4444; }
.card--neg .card-icon-wrap { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.card--neu { border-top: 3px solid #94a3b8; }
.card--neu .card-icon-wrap { background: rgba(148, 163, 184, 0.1); color: #94a3b8; }
.card--total { border-top: 3px solid #2563eb; }
.card--total .card-icon-wrap { background: rgba(37, 99, 235, 0.1); color: #2563eb; }

/* ===================== 面板 ===================== */
.panel {
  padding: 24px;
  border-radius: var(--radius-card);
  background: var(--bg-glass);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-card);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}

.panel-tag {
  flex-shrink: 0;
  padding: 5px 14px;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.2);
  color: var(--primary);
  font-size: 12px;
  font-weight: 600;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===================== 主体双栏 ===================== */
.main-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
}

.panel--map {
  display: flex;
  flex-direction: column;
}

.panel--wordcloud {
  display: flex;
  flex-direction: column;
}

.chart-map {
  flex: 1;
  min-height: 480px;
  width: 100%;
}

.chart-wordcloud {
  flex: 1;
  min-height: 480px;
  width: 100%;
}

/* ===================== 底部双栏 ===================== */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.chart {
  width: 100%;
  height: 320px;
}

/* ===================== 省份榜 ===================== */
.province-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.province-item {
  display: grid;
  grid-template-columns: 28px 68px 1fr 56px;
  align-items: center;
  gap: 10px;
}

.prov-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 700;
  background: rgba(37, 99, 235, 0.1);
  color: var(--primary);
  flex-shrink: 0;
}

.prov-rank--gold {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: #78350f;
}

.prov-rank--silver {
  background: linear-gradient(135deg, #94a3b8, #cbd5e1);
  color: #1e293b;
}

.prov-rank--bronze {
  background: linear-gradient(135deg, #b45309, #d97706);
  color: #fff;
}

.prov-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-base);
}

.prov-bar-wrap {
  height: 8px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.prov-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s ease;
}

.prov-value {
  font-size: 12px;
  font-weight: 700;
  color: #374151;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ===================== 情感关键词 ===================== */
.sentiment-keywords {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sk-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sk-group-title {
  font-size: 13px;
  font-weight: 700;
}

.sk-pos { color: #16a34a; }
.sk-neg { color: #dc2626; }

.sk-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sk-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  transition: transform 0.15s;
  cursor: default;
}

.sk-tag:hover {
  transform: scale(1.05);
}

.sk-tag em {
  font-style: normal;
  font-size: 11px;
  opacity: 0.75;
  font-weight: 500;
}

.sk-tag--pos {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  color: #15803d;
}

.sk-tag--neg {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: #dc2626;
}

/* ===================== 响应式 ===================== */
@media (max-width: 1100px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
  .bottom-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 24px; }
  .hero { flex-direction: column; align-items: flex-start; }
  .cards { grid-template-columns: 1fr 1fr; gap: 10px; }
}
</style>
