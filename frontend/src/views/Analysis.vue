<template>
  <div class="page-shell">
    <main class="analysis-page">
      <section class="hero">
        <div>
          <p class="eyebrow">离线批处理</p>
          <h1>PySpark 数据分析</h1>
          <p class="hero-text">
            基于 MySQL 原始采集表生成关键词统计和每日采集统计，展示离线分析结果。
          </p>
        </div>
        <div class="hero-actions">
          <button class="ghost-button" @click="loadAnalysisData" :disabled="loadingPage">
            {{ loadingPage ? "刷新中..." : "刷新分析数据" }}
          </button>
          <button class="primary-button" @click="handleRunAnalysis" :disabled="runningJob">
            {{ runningJob ? "任务启动中..." : "运行分析任务" }}
          </button>
        </div>
      </section>

      <p v-if="pageError" class="helper-text danger-text">{{ pageError }}</p>
      <p v-if="runMessage" class="helper-text">{{ runMessage }}</p>

      <section v-if="!hasAnalysisData" class="panel empty-panel">
        暂无分析数据，请先运行 PySpark 分析任务
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>关键词 Top20 统计</h2>
            <p>按出现次数和最高热度值排序，展示高频热搜关键词。</p>
          </div>
        </div>
        <div class="chart-panel">
          <div ref="keywordChartRef" class="chart"></div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>每日采集统计</h2>
            <p>展示每日总记录数、平均热度和最大热度变化。</p>
          </div>
        </div>
        <div class="chart-panel">
          <div ref="dailyChartRef" class="chart"></div>
        </div>

        <table class="daily-table">
          <thead>
            <tr>
              <th>统计日期</th>
              <th>总记录数</th>
              <th>关键词数</th>
              <th>平均热度</th>
              <th>最大热度</th>
              <th>最高排名</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in dailyStats" :key="item.stat_date">
              <td>{{ item.stat_date }}</td>
              <td>{{ formatNumber(item.total_records) }}</td>
              <td>{{ formatNumber(item.total_keywords) }}</td>
              <td>{{ formatNumber(item.avg_hot_value) }}</td>
              <td>{{ formatNumber(item.max_hot_value) }}</td>
              <td>{{ item.min_rank || "-" }}</td>
            </tr>
            <tr v-if="!dailyStats.length">
              <td colspan="6" class="table-empty">暂无每日统计数据</td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";

import { getDailyStats, getTopKeywords, runAnalysisJob } from "../api/index.js";

const topKeywords = ref([]);
const dailyStats = ref([]);
const pageError = ref("");
const runMessage = ref("");
const loadingPage = ref(false);
const runningJob = ref(false);
const keywordChartRef = ref(null);
const dailyChartRef = ref(null);

let keywordChart = null;
let dailyChart = null;

const hasAnalysisData = computed(
  () => topKeywords.value.length > 0 || dailyStats.value.length > 0
);

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function buildKeywordChart() {
  if (!keywordChartRef.value) {
    return;
  }
  if (!keywordChart) {
    keywordChart = echarts.init(keywordChartRef.value);
  }

  keywordChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis"
    },
    grid: {
      left: 48,
      right: 20,
      top: 36,
      bottom: 86
    },
    xAxis: {
      type: "category",
      data: topKeywords.value.map((item) => item.keyword),
      axisLabel: {
        color: "#5b6475",
        rotate: 35,
        interval: 0
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
        name: "出现次数",
        type: "bar",
        barMaxWidth: 34,
        data: topKeywords.value.map((item) => item.appear_count),
        itemStyle: {
          color: "#e4572e"
        }
      }
    ]
  });
}

function buildDailyChart() {
  if (!dailyChartRef.value) {
    return;
  }
  if (!dailyChart) {
    dailyChart = echarts.init(dailyChartRef.value);
  }

  dailyChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis"
    },
    legend: {
      top: 0,
      textStyle: {
        color: "#475569"
      }
    },
    grid: {
      left: 48,
      right: 28,
      top: 52,
      bottom: 44
    },
    xAxis: {
      type: "category",
      data: dailyStats.value.map((item) => item.stat_date),
      axisLabel: {
        color: "#5b6475"
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
        name: "总记录数",
        type: "line",
        smooth: true,
        data: dailyStats.value.map((item) => item.total_records),
        lineStyle: {
          width: 3,
          color: "#16324f"
        },
        itemStyle: {
          color: "#16324f"
        }
      },
      {
        name: "平均热度",
        type: "line",
        smooth: true,
        data: dailyStats.value.map((item) => item.avg_hot_value),
        lineStyle: {
          width: 3,
          color: "#2a9d8f"
        },
        itemStyle: {
          color: "#2a9d8f"
        }
      },
      {
        name: "最大热度",
        type: "line",
        smooth: true,
        data: dailyStats.value.map((item) => item.max_hot_value),
        lineStyle: {
          width: 3,
          color: "#e4572e"
        },
        itemStyle: {
          color: "#e4572e"
        }
      }
    ]
  });
}

async function loadAnalysisData() {
  loadingPage.value = true;
  try {
    pageError.value = "";
    const [keywordResponse, dailyResponse] = await Promise.all([
      getTopKeywords(20),
      getDailyStats()
    ]);
    topKeywords.value = keywordResponse.items || [];
    dailyStats.value = dailyResponse.items || [];
    await nextTick();
    buildKeywordChart();
    buildDailyChart();
  } catch (error) {
    topKeywords.value = [];
    dailyStats.value = [];
    pageError.value = error.message || "分析数据加载失败，请检查后端服务和统计表";
    buildKeywordChart();
    buildDailyChart();
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
  if (keywordChart) {
    keywordChart.resize();
  }
  if (dailyChart) {
    dailyChart.resize();
  }
}

onMounted(async () => {
  await loadAnalysisData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  if (keywordChart) {
    keywordChart.dispose();
    keywordChart = null;
  }
  if (dailyChart) {
    dailyChart.dispose();
    dailyChart = null;
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

.analysis-page {
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

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.panel {
  padding: 22px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(157, 176, 208, 0.32);
  box-shadow: 0 16px 38px rgba(82, 100, 128, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.primary-button,
.ghost-button {
  padding: 12px 16px;
  border: none;
  border-radius: 12px;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
}

.primary-button {
  background: #e4572e;
}

.ghost-button {
  background: #16324f;
}

.primary-button:disabled,
.ghost-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.chart-panel {
  min-height: 360px;
}

.chart {
  width: 100%;
  height: 360px;
}

.helper-text {
  color: #4b5563;
}

.danger-text {
  color: #b42318;
}

.empty-panel {
  text-align: center;
  color: #6b7280;
}

.daily-table {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
}

.daily-table th,
.daily-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #edf2f7;
  text-align: left;
  font-size: 14px;
}

.daily-table th {
  color: #475569;
  font-weight: 600;
}

.table-empty {
  text-align: center;
  color: #6b7280;
}

@media (max-width: 960px) {
  .hero,
  .panel-header {
    grid-template-columns: 1fr;
    display: grid;
  }

  .hero-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .page-shell {
    padding: 20px 12px 28px;
  }

  h1 {
    font-size: 30px;
  }

  .chart {
    height: 300px;
  }

  .daily-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
