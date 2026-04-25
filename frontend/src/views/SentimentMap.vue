<template>
  <div class="page-shell">
    <main class="sentiment-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">🌍 评论地理分布 · 热词词云 · 情感分析</p>
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
            <span class="btn-icon" :class="{ spin: loading }">↻</span>
            {{ loading ? "加载中..." : "刷新" }}
          </button>
        </div>
      </section>

      <!-- 消息提示 -->
      <div v-if="pageError" class="alert alert--error">⚠️ {{ pageError }}</div>

      <!-- 情感统计卡片 -->
      <section class="cards">
        <article class="card card--pos">
          <div class="card-left">
            <div class="card-icon">😊</div>
          </div>
          <div class="card-body">
            <span class="card-label">正面评论</span>
            <strong class="card-value card-value--pos">{{ formatNumber(sentiment.positive) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.positive }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.positive + '%', '--color': '#22c55e' }"></div>
        </article>
        <article class="card card--neg">
          <div class="card-left">
            <div class="card-icon">😡</div>
          </div>
          <div class="card-body">
            <span class="card-label">负面评论</span>
            <strong class="card-value card-value--neg">{{ formatNumber(sentiment.negative) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.negative }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.negative + '%', '--color': '#ef4444' }"></div>
        </article>
        <article class="card card--neu">
          <div class="card-left">
            <div class="card-icon">😐</div>
          </div>
          <div class="card-body">
            <span class="card-label">中性评论</span>
            <strong class="card-value card-value--neu">{{ formatNumber(sentiment.neutral) }}</strong>
            <span class="card-rate">占比 {{ sentimentRate.neutral }}%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': sentimentRate.neutral + '%', '--color': '#94a3b8' }"></div>
        </article>
        <article class="card card--total">
          <div class="card-left">
            <div class="card-icon">💬</div>
          </div>
          <div class="card-body">
            <span class="card-label">总评论数</span>
            <strong class="card-value">{{ formatNumber(sentimentTotal) }}</strong>
            <span class="card-rate">情感覆盖率 100%</span>
          </div>
          <div class="card-bar" :style="{ '--fill': '100%', '--color': '#3f72af' }"></div>
        </article>
      </section>

      <!-- 主体双栏 -->
      <section class="main-grid">
        <!-- 左：中国地图 -->
        <section class="panel panel--map">
          <div class="panel-header">
            <div>
              <h2>🗺️ 全国评论地理分布</h2>
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
              <h2>☁️ 热词词云</h2>
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
              <h2>📈 情感趋势变化</h2>
              <p>随时间推移正面/负面/中性评论数量变化趋势</p>
            </div>
          </div>
          <div ref="sentimentTrendRef" class="chart"></div>
        </section>

        <!-- 省份 Top10 评论榜 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>🏅 省份评论 Top10</h2>
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
              <h2>🥧 情感占比分布</h2>
              <p>正面、负面、中性评论的整体占比环形图</p>
            </div>
          </div>
          <div ref="sentimentPieRef" class="chart"></div>
        </section>

        <!-- 情感关键词列表 -->
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>🏷️ 情感关键词分析</h2>
              <p>正面与负面情感中最具代表性的高频词汇</p>
            </div>
          </div>
          <div class="sentiment-keywords">
            <div class="sk-group">
              <div class="sk-group-title sk-pos">😊 正面关键词</div>
              <div class="sk-tags">
                <span v-for="kw in posKeywords" :key="kw.word" class="sk-tag sk-tag--pos">
                  {{ kw.word }}
                  <em>{{ kw.count }}</em>
                </span>
              </div>
            </div>
            <div class="sk-group">
              <div class="sk-group-title sk-neg">😡 负面关键词</div>
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

function getProvPercent(value) {
  return Math.round((value / maxProvinceVal.value) * 100);
}

function getProvColor(index) {
  const colors = ["#e4572e", "#f4723e", "#f4923e", "#f4b23e", "#f4c84e",
    "#2a9d8f", "#3f72af", "#60a5fa", "#a78bfa", "#c084fc"];
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
    // 若 CDN 失败，使用简化占位
    chinaGeoJson = null;
  }

  if (chinaGeoJson) {
    echarts.registerMap("china", chinaGeoJson);
  }

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff", fontSize: 13 },
      formatter: (params) => {
        const val = params.value || 0;
        return `<b>${params.name}</b><br/>评论数：${val.toLocaleString("zh-CN")}`;
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(...geoData.value.map((d) => d.value), 1),
      left: 20,
      bottom: 40,
      text: ["多", "少"],
      inRange: {
        color: ["#e8f4ff", "#bdd7f5", "#7aaee8", "#3f72af", "#16324f"],
      },
      textStyle: { color: "#5b6475", fontSize: 12 },
      calculable: true,
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
          color: "#5b6475",
        },
        emphasis: {
          label: { show: true, color: "#16324f", fontWeight: 700 },
          itemStyle: { areaColor: "#f4723e" },
        },
        data: geoData.value,
        itemStyle: {
          areaColor: "#e8f4ff",
          borderColor: "#abc8e8",
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
      borderColor: "rgba(157,176,208,0.3)",
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
              "#e4572e", "#3f72af", "#2a9d8f", "#f4723e", "#60a5fa",
              "#a78bfa", "#22c55e", "#f59e0b", "#ec4899", "#14b8a6",
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
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: {
      top: 4,
      right: 20,
      textStyle: { color: "#5b6475", fontSize: 12 },
    },
    grid: { left: 50, right: 20, top: 36, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      axisLabel: { color: "#5b6475", fontSize: 11, rotate: 20 },
      axisLine: { lineStyle: { color: "#c4d0e5" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#5b6475", fontSize: 11 },
      splitLine: { lineStyle: { color: "rgba(157,176,208,0.2)" } },
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
      borderColor: "rgba(157,176,208,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: "{b}: {c} ({d}%)",
    },
    legend: {
      bottom: 20,
      textStyle: { color: "#5b6475", fontSize: 12 },
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
        labelLine: { lineStyle: { color: "#c4d0e5" } },
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
  padding: 28px 20px 48px;
}

.sentiment-page {
  max-width: 1440px;
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
  background: linear-gradient(90deg, #22c55e, #3f72af, #ef4444, #e4572e);
  border-radius: 24px 24px 0 0;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.12em;
  font-weight: 600;
  color: #3f72af;
}

h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  line-height: 1.15;
  color: #0f172a;
  letter-spacing: -0.02em;
}

h2 {
  margin: 0 0 5px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

p {
  margin: 0;
  color: #5b6475;
  font-size: 13px;
}

.hero-text {
  margin-top: 10px;
  max-width: 640px;
  line-height: 1.7;
  font-size: 14px;
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
  color: #5b6475;
  white-space: nowrap;
}

.kw-select {
  padding: 9px 14px;
  border-radius: 12px;
  border: 1.5px solid #cdd7ea;
  background: #fff;
  font-size: 13px;
  color: #1f2937;
  cursor: pointer;
  outline: none;
  min-width: 160px;
  max-width: 220px;
  transition: border-color 0.2s;
}

.kw-select:focus {
  border-color: #3f72af;
}

/* ===================== 按钮 ===================== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.btn--outline {
  background: transparent;
  border: 1.5px solid #cdd7ea;
  color: #374151;
}

.btn--outline:hover:not(:disabled) {
  border-color: #3f72af;
  color: #3f72af;
}

.btn--outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 16px;
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
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

.alert--error {
  background: rgba(239,68,68,0.07);
  border: 1px solid rgba(239,68,68,0.2);
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
  border-radius: 20px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(157,176,208,0.22);
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
  font-size: 30px;
  flex-shrink: 0;
}

.card-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
  font-weight: 500;
}

.card-value {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
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
  color: #9ca3af;
}

/* 底部进度条 */
.card-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(157,176,208,0.15);
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
.card--neg { border-top: 3px solid #ef4444; }
.card--neu { border-top: 3px solid #94a3b8; }
.card--total { border-top: 3px solid #3f72af; }

/* ===================== 面板 ===================== */
.panel {
  padding: 24px;
  border-radius: 24px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(157,176,208,0.22);
  box-shadow: 0 12px 32px rgba(82,100,128,0.08);
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
  background: rgba(63,114,175,0.08);
  border: 1px solid rgba(63,114,175,0.2);
  color: #3f72af;
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
  gap: 22px;
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
  gap: 22px;
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
  background: rgba(63,114,175,0.1);
  color: #3f72af;
  flex-shrink: 0;
}

.prov-rank--gold {
  background: linear-gradient(135deg, #f7b731, #f9ca24);
  color: #5c3900;
}

.prov-rank--silver {
  background: linear-gradient(135deg, #9e9e9e, #c8c8c8);
  color: #2a2a2a;
}

.prov-rank--bronze {
  background: linear-gradient(135deg, #cd7f32, #e09060);
  color: #3a1500;
}

.prov-name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.prov-bar-wrap {
  height: 8px;
  background: rgba(157,176,208,0.2);
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
  background: rgba(34,197,94,0.1);
  border: 1px solid rgba(34,197,94,0.25);
  color: #15803d;
}

.sk-tag--neg {
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.22);
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
