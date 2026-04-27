<template>
  <div class="page-shell">
    <main class="analysis-page">

      <!-- Hero 区域 -->
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">离线批处理</p>
          <h1>PySpark 数据分析</h1>
          <p class="hero-text">
            基于 MySQL 原始采集表，通过 PySpark 批量生成关键词统计与每日采集统计，展示离线分析结果。
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadAnalysisData" :disabled="loadingPage">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
            {{ loadingPage ? "刷新中..." : "刷新数据" }}
          </button>
          <button class="btn btn--primary" @click="handleRunAnalysis" :disabled="runningJob">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            {{ runningJob ? "任务启动中..." : "运行分析任务" }}
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
      <div v-if="runMessage" class="alert alert--info">
        <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        {{ runMessage }}
      </div>
      <div v-if="showSampleWarning" class="alert alert--warning">
        当前仅采集 {{ appSummary.total_batches }} 个批次，趋势分析样本较少，爆发预测结果仅供参考。建议采集 30 个批次以上后重新分析。
      </div>

      <!-- 空状态 -->
      <section v-if="!hasAnalysisData && !loadingPage" class="empty-panel">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="3" y1="9" x2="21" y2="9"></line>
          <line x1="9" y1="21" x2="9" y2="9"></line>
        </svg>
        <p>暂无分析数据，请先运行 PySpark 分析任务</p>
      </section>

      <!-- 数据分析说明卡片 -->
      <section v-if="analysisInsights.length" class="insight-panel">
        <div class="insight-header">
          <svg class="insight-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
          <span>分析结论</span>
        </div>
        <div class="insight-list">
          <div v-for="(text, i) in analysisInsights" :key="i" class="insight-item">
            <span class="insight-dot"></span>
            <span class="insight-text">{{ text }}</span>
          </div>
        </div>
      </section>

      <!-- 双栏：关键词柱状图 + 词云 -->
      <section class="content-grid content-grid--2" v-if="hasAnalysisData">
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>高热关键词 Top20</h2>
              <p>按最高热度值排序，辅助展示出现次数，反映当前高影响力热搜话题。</p>
            </div>
            <div class="stat-badge"><span>共 {{ topKeywords.length }} 个关键词</span></div>
          </div>
          <div class="chart-box">
            <div ref="keywordChartRef" class="chart"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2>高频关键词词云</h2>
              <p>字号越大代表出现频率越高，颜色区分不同热度区间。</p>
            </div>
            <div class="stat-badge"><span>Top {{ wordCloudData.length }} 词</span></div>
          </div>
          <div v-if="!wordCloudData.length" class="chart-empty">
            <EmptyState title="暂无词云数据" description="请先运行 PySpark 分析任务生成关键词统计数据。" />
          </div>
          <div v-else class="chart-box">
            <div ref="wordCloudRef" class="chart"></div>
          </div>
        </section>
      </section>

      <!-- 每日采集统计 -->
      <section class="panel" v-if="hasAnalysisData">
        <div class="panel-header">
          <div>
            <h2>每日采集统计</h2>
            <p>展示每日总记录数与关键词数量变化趋势。</p>
          </div>
          <div class="stat-badge"><span>共 {{ dailyStats.length }} 天</span></div>
        </div>
        <div class="chart-box">
          <div ref="dailyChartRef" class="chart"></div>
        </div>

        <!-- 数据表格 -->
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr><th>统计日期</th><th>总记录数</th><th>关键词数</th><th>平均热度</th><th>最大热度</th><th>最高排名</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in dailyStats" :key="item.stat_date">
                <td class="date-cell">{{ item.stat_date }}</td>
                <td><span class="num-badge">{{ formatNumber(item.total_records) }}</span></td>
                <td>{{ formatNumber(item.total_keywords) }}</td>
                <td class="heat-cell">{{ formatNumber(item.avg_hot_value) }}</td>
                <td class="heat-cell heat-cell--max">{{ formatNumber(item.max_hot_value) }}</td>
                <td><span class="rank-badge">{{ item.min_rank || "—" }}</span></td>
              </tr>
              <tr v-if="!dailyStats.length"><td colspan="6" class="table-empty">暂无每日统计数据</td></tr>
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
import "echarts-wordcloud";
import { getDailyStats, getSummary, getTopKeywords, runAnalysisJob } from "../api/index.js";
import EmptyState from "../components/EmptyState.vue";

const appSummary = ref({ total_batches: 0 });
const topKeywords = ref([]);
const dailyStats = ref([]);
const pageError = ref("");
const runMessage = ref("");
const loadingPage = ref(false);
const runningJob = ref(false);
const keywordChartRef = ref(null);
const dailyChartRef = ref(null);
const wordCloudRef = ref(null);

let keywordChart = null;
let dailyChart = null;
let wordCloudChart = null;

const hasAnalysisData = computed(() => topKeywords.value.length > 0 || dailyStats.value.length > 0);
const showSampleWarning = computed(() => {
  const batches = Number(appSummary.value.total_batches || 0);
  return batches > 0 && batches < 30;
});

// 词云数据
const wordCloudData = computed(() => {
  return topKeywords.value.slice(0, 100).map((item) => ({
    name: item.keyword,
    value: Number(item.appear_count || 0),
  }));
});

// 分析洞察
const analysisInsights = computed(() => {
  const items = [];
  if (topKeywords.value.length) {
    const top3 = topKeywords.value.slice(0, 3).map((k) => k.keyword).join("、");
    items.push(`高频关键词主要集中在「${top3}」等话题。`);
  }
  if (dailyStats.value.length) {
    const maxDay = dailyStats.value.reduce((a, b) => (a.total_records > b.total_records ? a : b), dailyStats.value[0]);
    items.push(`采集量最高日期为 ${maxDay?.stat_date}，当日共采集 ${formatNumber(maxDay?.total_records)} 条记录。`);
    const maxHot = dailyStats.value.reduce((a, b) => (a.max_hot_value > b.max_hot_value ? a : b), dailyStats.value[0]);
    items.push(`最高热度值出现在 ${maxHot?.stat_date}，当日最高热度达 ${formatNumber(maxHot?.max_hot_value)}。`);
  }
  return items;
});

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function buildKeywordChart() {
  if (!keywordChartRef.value) return;
  if (!keywordChart) keywordChart = echarts.init(keywordChartRef.value);
  const data = [...topKeywords.value]
    .sort((a, b) => Number(b.max_hot_value || 0) - Number(a.max_hot_value || 0))
    .slice(0, 20);
  const colors = ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"];
  keywordChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter(params) {
        const item = data[params[0]?.dataIndex];
        if (!item) return "";
        return `<div style="font-weight:700;margin-bottom:6px;">${item.keyword}</div>` +
          `<div>出现次数：${formatNumber(item.appear_count)}</div>` +
          `<div>最高热度：${formatNumber(item.max_hot_value)}</div>` +
          `<div>平均热度：${formatNumber(item.avg_hot_value)}</div>` +
          `<div>最佳排名：${item.best_rank || "-"}</div>`;
      },
    },
    grid: { left: 112, right: 28, top: 24, bottom: 38 },
    xAxis: {
      type: "value",
      name: "最高热度",
      axisLabel: { color: "#64748b", fontSize: 11, formatter: (v) => (v >= 10000 ? `${Math.round(v / 10000)}万` : v) },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: data.map((item) => item.keyword),
      axisLabel: { color: "#64748b", fontSize: 11, formatter: (v) => (v.length > 8 ? v.slice(0, 8) + "…" : v) },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
      axisTick: { show: false },
    },
    series: [{
      name: "最高热度",
      type: "bar",
      barMaxWidth: 16,
      data: data.map((item, i) => ({
        value: Number(item.max_hot_value || 0),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: colors[i % colors.length] + "55" }, { offset: 1, color: colors[i % colors.length] }]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      label: { show: true, position: "right", color: "#475569", fontSize: 11, formatter: (p) => formatNumber(p.value) },
    }],
  });
}

function buildWordCloudChart() {
  if (!wordCloudRef.value) return;
  if (!wordCloudChart) wordCloudChart = echarts.init(wordCloudRef.value);
  if (!wordCloudData.value.length) return;
  wordCloudChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      show: true,
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
      formatter: (params) => `${params.name}：出现 ${formatNumber(params.value)} 次`,
    },
    series: [{
      type: "wordCloud",
      shape: "circle",
      left: "center",
      top: "center",
      width: "92%",
      height: "92%",
      sizeRange: [12, 52],
      rotationRange: [-45, 45],
      rotationStep: 15,
      gridSize: 10,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: "system-ui, sans-serif",
        color: () => {
          const palette = ["#2563eb", "#3b82f6", "#06b6d4", "#0ea5e9", "#6366f1", "#8b5cf6", "#1d4ed8", "#0284c7"];
          return palette[Math.floor(Math.random() * palette.length)];
        },
      },
      emphasis: { focus: "self", textStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.2)" } },
      data: wordCloudData.value,
    }],
  }, true);
}

function buildDailyChart() {
  if (!dailyChartRef.value) return;
  if (!dailyChart) dailyChart = echarts.init(dailyChartRef.value);
  dailyChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(15,23,42,0.92)",
      borderColor: "rgba(148,163,184,0.3)",
      textStyle: { color: "#e8f0ff" },
    },
    legend: { top: 0, textStyle: { color: "#64748b", fontSize: 12 }, icon: "roundRect" },
    grid: { left: 54, right: 54, top: 46, bottom: 44 },
    xAxis: {
      type: "category",
      data: dailyStats.value.map((item) => item.stat_date?.slice(5) || item.stat_date),
      axisLabel: { color: "#64748b", fontSize: 11 },
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.4)" } },
      axisTick: { show: false },
    },
    yAxis: [
      { type: "value", name: "记录数", nameTextStyle: { color: "#64748b", fontSize: 10 }, axisLabel: { color: "#64748b", fontSize: 11 }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.15)", type: "dashed" } } },
      { type: "value", name: "关键词数", nameTextStyle: { color: "#64748b", fontSize: 10 }, axisLabel: { color: "#64748b", fontSize: 11 }, splitLine: { show: false } },
    ],
    series: [
      {
        name: "总记录数",
        type: "bar",
        barMaxWidth: 32,
        data: dailyStats.value.map((item) => Number(item.total_records || 0)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(37,99,235,0.9)" }, { offset: 1, color: "rgba(37,99,235,0.2)" }]),
          borderRadius: [4, 4, 0, 0],
        },
      },
      {
        name: "关键词数",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbolSize: 6,
        data: dailyStats.value.map((item) => Number(item.total_keywords || 0)),
        lineStyle: { width: 2.5, color: "#06b6d4" },
        itemStyle: { color: "#06b6d4", borderWidth: 2, borderColor: "#fff" },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(6,182,212,0.18)" }, { offset: 1, color: "rgba(6,182,212,0.02)" }]) },
      },
    ],
  });
}

async function loadAnalysisData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    const [keywordResponse, dailyResponse, summaryResponse] = await Promise.all([getTopKeywords(20), getDailyStats(), getSummary()]);
    topKeywords.value = keywordResponse.items || [];
    dailyStats.value = dailyResponse.items || [];
    appSummary.value = summaryResponse || { total_batches: 0 };
    await nextTick();
    buildKeywordChart();
    buildDailyChart();
    buildWordCloudChart();
  } catch (error) {
    topKeywords.value = [];
    dailyStats.value = [];
    pageError.value = error.message || "分析数据加载失败，请检查后端服务和统计表";
    buildKeywordChart();
    buildDailyChart();
    buildWordCloudChart();
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
  if (wordCloudChart) wordCloudChart.resize();
}

onMounted(async () => {
  await loadAnalysisData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  if (keywordChart) { keywordChart.dispose(); keywordChart = null; }
  if (dailyChart) { dailyChart.dispose(); dailyChart = null; }
  if (wordCloudChart) { wordCloudChart.dispose(); wordCloudChart = null; }
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.analysis-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }

/* Hero */
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%); border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 20px 52px rgba(37,99,235,0.2), 0 1px 0 rgba(255,255,255,0.1) inset; position: relative; overflow: hidden; }
.hero::before { content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08), transparent 50%); pointer-events: none; }
.eyebrow { margin: 0 0 8px; font-size: 13px; letter-spacing: 0.16em; font-weight: 600; color: rgba(255,255,255,0.7); text-transform: uppercase; }
h1 { margin: 0; font-size: 36px; font-weight: 800; line-height: 1.15; color: #fff; letter-spacing: -0.02em; }
h2 { margin: 0 0 5px; font-size: 20px; font-weight: 700; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 680px; line-height: 1.7; color: rgba(255,255,255,0.75); }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; flex-shrink: 0; }

/* 按钮 */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 11px 20px; border: none; border-radius: var(--radius-btn); font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; white-space: nowrap; }
.btn-icon { width: 16px; height: 16px; flex-shrink: 0; }
.btn--primary { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; box-shadow: 0 4px 14px rgba(37,99,235,0.3); }
.btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(37,99,235,0.35); }
.btn--outline { background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3); backdrop-filter: blur(4px); }
.btn--outline:hover:not(:disabled) { background: rgba(255,255,255,0.25); transform: translateY(-1px); }
.btn:disabled { opacity: 0.65; cursor: not-allowed; transform: none !important; }

/* 提示栏 */
.alert { display: flex; align-items: center; gap: 8px; padding: 12px 18px; border-radius: 12px; font-size: 14px; font-weight: 500; }
.alert-icon { width: 18px; height: 18px; flex-shrink: 0; }
.alert--error { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); color: #dc2626; }
.alert--info { background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.15); color: #16a34a; }
.alert--warning { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); color: #b45309; }

/* 面板 */
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 20px; }
.stat-badge { padding: 5px 14px; border-radius: 20px; background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.2); color: var(--primary); font-size: 13px; font-weight: 600; flex-shrink: 0; }

/* 洞察面板 */
.insight-panel { padding: 20px 24px; border-radius: var(--radius-card); background: linear-gradient(135deg, rgba(37,99,235,0.04), rgba(6,182,212,0.04)); border: 1px solid rgba(37,99,235,0.12); box-shadow: var(--shadow-card); }
.insight-header { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: var(--primary); margin-bottom: 12px; }
.insight-icon { width: 18px; height: 18px; }
.insight-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px 24px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--text-base); line-height: 1.6; }
.insight-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); margin-top: 7px; flex-shrink: 0; }
.insight-text { flex: 1; }

/* 图表 */
.chart-box { min-height: 360px; margin-bottom: 8px; }
.chart { width: 100%; height: 360px; }
.chart-empty { height: 360px; display: flex; align-items: center; justify-content: center; }
.content-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px; }
.content-grid--2 { grid-template-columns: 1fr 1fr; }

/* 空状态 */
.empty-panel { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 48px 24px; border-radius: 20px; background: rgba(255,255,255,0.75); border: 1.5px dashed rgba(148,163,184,0.4); color: var(--text-muted); font-size: 14px; }
.empty-icon { width: 48px; height: 48px; color: var(--text-light); }

/* 表格 */
.table-wrap { width: 100%; overflow-x: auto; margin-top: 16px; }
.data-table { width: 100%; border-collapse: collapse; min-width: 680px; }
.data-table th, .data-table td { padding: 11px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.data-table th { color: #475569; font-weight: 700; background: rgba(241,245,249,0.8); font-size: 13px; }
.data-table tbody tr:hover { background: rgba(239,246,255,0.7); }
.date-cell { font-variant-numeric: tabular-nums; color: #374151; font-weight: 600; }
.num-badge { display: inline-block; padding: 2px 8px; border-radius: 6px; background: rgba(37,99,235,0.08); color: var(--primary); font-weight: 600; }
.heat-cell { color: #06b6d4; font-weight: 600; }
.heat-cell--max { color: #8b5cf6; }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 28px; padding: 2px 8px; border-radius: 6px; background: rgba(15,23,42,0.06); color: var(--navy); font-size: 12px; font-weight: 600; }
.table-empty { text-align: center; color: var(--text-light); padding: 32px; }

/* 响应式 */
@media (max-width: 1100px) { .content-grid, .content-grid--2 { grid-template-columns: 1fr; } }
@media (max-width: 900px) {
  .hero { flex-direction: column; align-items: flex-start; }
  .hero-actions { width: 100%; }
  .panel-header { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 640px) {
  .page-shell { padding: 16px 12px 36px; }
  h1 { font-size: 26px; }
  .chart { height: 300px; }
  .chart-box { min-height: 300px; }
}
</style>
