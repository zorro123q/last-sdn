<template>
  <div class="page-shell">
    <main class="v6-page">
      <section class="hero">
        <div>
          <p class="eyebrow">Lifecycle Intelligence</p>
          <h1>热搜生命周期分析</h1>
          <p class="hero-text">基于首次出现、持续时长、峰值热度、排名变化和消失状态，对热搜话题进行全链路生命周期建模。</p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadData" :disabled="loading">
            {{ loading ? "刷新中..." : "刷新数据" }}
          </button>
          <button class="btn btn--primary" @click="handleRun" :disabled="running">
            {{ running ? "启动中..." : "运行生命周期分析" }}
          </button>
        </div>
      </section>

      <div v-if="pageError" class="alert alert--error">{{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">{{ runMessage }}</div>

      <section class="stat-grid">
        <article v-for="item in statCards" :key="item.key" class="stat-card">
          <span class="stat-label">{{ item.label }}</span>
          <strong>{{ formatNumber(item.value) }}</strong>
        </article>
      </section>

      <section class="chart-grid">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h2>生命周期阶段分布</h2>
              <p>展示新上榜、快速上升、高位稳定、降温和消失话题占比。</p>
            </div>
          </div>
          <div ref="stagePieRef" class="chart"></div>
        </div>
        <div class="panel">
          <div class="panel-header">
            <div>
              <h2>存活时长 Top20</h2>
              <p>按 duration_minutes 排序，识别长周期高热话题。</p>
            </div>
          </div>
          <div ref="durationBarRef" class="chart"></div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>快速上升 Top20</h2>
            <p>优先展示生命周期阶段为 rising 的话题，辅助判断潜在爆发趋势。</p>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>关键词</th>
                <th>峰值热度</th>
                <th>最佳排名</th>
                <th>上升速度</th>
                <th>出现次数</th>
                <th>最后出现</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in risingTop" :key="`rising-${item.id}`">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td class="heat-cell">{{ formatNumber(item.peak_hot_value) }}</td>
                <td>{{ item.peak_rank || "-" }}</td>
                <td class="change-up">{{ formatNumber(item.rise_speed) }}</td>
                <td>{{ formatNumber(item.appear_count) }}</td>
                <td class="date-cell">{{ item.last_seen_time || "-" }}</td>
              </tr>
              <tr v-if="!risingTop.length">
                <td colspan="6" class="table-empty">暂无快速上升话题</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>生命周期明细</h2>
            <p>保留最新一轮生命周期分析结果，供预警中心和答辩展示联动使用。</p>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>关键词</th>
                <th>阶段</th>
                <th>首次出现</th>
                <th>最后出现</th>
                <th>持续分钟</th>
                <th>峰值热度</th>
                <th>最佳排名</th>
                <th>是否消失</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in lifecycleList" :key="item.id">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td><span class="stage-tag" :class="`stage--${item.lifecycle_stage}`">{{ item.lifecycle_stage_cn || stageText(item.lifecycle_stage) }}</span></td>
                <td class="date-cell">{{ item.first_seen_time || "-" }}</td>
                <td class="date-cell">{{ item.last_seen_time || "-" }}</td>
                <td>{{ formatNumber(item.duration_minutes) }}</td>
                <td class="heat-cell">{{ formatNumber(item.peak_hot_value) }}</td>
                <td>{{ item.peak_rank || "-" }}</td>
                <td>{{ item.is_disappeared ? "是" : "否" }}</td>
              </tr>
              <tr v-if="!lifecycleList.length">
                <td colspan="8" class="table-empty">暂无生命周期分析数据，请先运行任务</td>
              </tr>
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
import { getLifecycleList, getLifecycleSummary, runLifecycleJob } from "../api/index.js";

const summary = ref({});
const lifecycleList = ref([]);
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const runMessage = ref("");
const stagePieRef = ref(null);
const durationBarRef = ref(null);

let stagePie = null;
let durationBar = null;

const stageMap = {
  new: "新上榜",
  rising: "快速上升",
  stable_high: "高位稳定",
  falling: "缓慢衰退",
  cooling: "快速降温",
  disappeared: "已消失",
  unknown: "未知",
};

const stageColors = {
  new: "#3b82f6",
  rising: "#22c55e",
  stable_high: "#8b5cf6",
  falling: "#94a3b8",
  cooling: "#f59e0b",
  disappeared: "#ef4444",
  unknown: "#64748b",
};

const statCards = computed(() => [
  { key: "total_count", label: "总话题数", value: summary.value.total_count },
  { key: "new_count", label: "新上榜", value: summary.value.new_count },
  { key: "rising_count", label: "快速上升", value: summary.value.rising_count },
  { key: "stable_high_count", label: "高位稳定", value: summary.value.stable_high_count },
  { key: "cooling_count", label: "快速降温", value: summary.value.cooling_count },
  { key: "disappeared_count", label: "已消失", value: summary.value.disappeared_count },
]);

const risingTop = computed(() => lifecycleList.value
  .filter((item) => item.lifecycle_stage === "rising")
  .sort((a, b) => Number(b.rise_speed || 0) - Number(a.rise_speed || 0))
  .slice(0, 20));

const durationTop = computed(() => [...lifecycleList.value]
  .sort((a, b) => Number(b.duration_minutes || 0) - Number(a.duration_minutes || 0))
  .slice(0, 20));

function stageText(stage) {
  return stageMap[stage] || "未知";
}

function shortLabel(value, max = 8) {
  const text = String(value || "");
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function formatNumber(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) return "0";
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function buildCharts() {
  buildStagePie();
  buildDurationBar();
}

function buildStagePie() {
  if (!stagePieRef.value) return;
  if (!stagePie) stagePie = echarts.init(stagePieRef.value);
  const data = Object.keys(stageMap).map((stage) => ({
    name: stageMap[stage],
    value: lifecycleList.value.filter((item) => item.lifecycle_stage === stage).length,
    itemStyle: { color: stageColors[stage] },
  })).filter((item) => item.value > 0);
  stagePie.setOption({
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "transparent", textStyle: { color: "#fff" } },
    legend: { bottom: 0, textStyle: { color: "#64748b" } },
    series: [{
      name: "生命周期阶段",
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "44%"],
      label: { color: "#334155", formatter: "{b}: {c}" },
      data,
    }],
  }, true);
}

function buildDurationBar() {
  if (!durationBarRef.value) return;
  if (!durationBar) durationBar = echarts.init(durationBarRef.value);
  const data = durationTop.value;
  durationBar.setOption({
    tooltip: { trigger: "axis", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "transparent", textStyle: { color: "#fff" } },
    grid: { left: 92, right: 24, top: 20, bottom: 34 },
    xAxis: { type: "value", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.18)", type: "dashed" } } },
    yAxis: {
      type: "category",
      inverse: true,
      data: data.map((item) => item.keyword),
      axisLabel: { color: "#64748b", formatter: (value) => shortLabel(value) },
    },
    series: [{
      type: "bar",
      data: data.map((item) => Number(item.duration_minutes || 0)),
      barMaxWidth: 16,
      itemStyle: { color: "#2563eb", borderRadius: [0, 6, 6, 0] },
    }],
  }, true);
}

async function loadData() {
  loading.value = true;
  pageError.value = "";
  try {
    const [summaryResponse, listResponse] = await Promise.all([
      getLifecycleSummary(),
      getLifecycleList("", 300),
    ]);
    summary.value = summaryResponse || {};
    lifecycleList.value = listResponse.items || [];
    await nextTick();
    buildCharts();
  } catch (error) {
    pageError.value = error.message || "生命周期分析数据加载失败";
    lifecycleList.value = [];
    summary.value = {};
    await nextTick();
    buildCharts();
  } finally {
    loading.value = false;
  }
}

async function handleRun() {
  running.value = true;
  try {
    const response = await runLifecycleJob();
    runMessage.value = response.message || "生命周期分析任务已启动";
    setTimeout(loadData, 1800);
  } catch (error) {
    runMessage.value = error.message || "生命周期分析任务启动失败";
  } finally {
    running.value = false;
  }
}

function handleResize() {
  stagePie?.resize();
  durationBar?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  stagePie?.dispose();
  durationBar?.dispose();
  stagePie = null;
  durationBar = null;
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.v6-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); background: linear-gradient(135deg, #0f766e, #2563eb); box-shadow: var(--shadow-hero); color: #fff; }
.eyebrow { margin: 0 0 8px; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.72); }
h1 { margin: 0; font-size: 34px; line-height: 1.15; }
h2 { margin: 0 0 6px; font-size: 20px; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 700px; color: rgba(255,255,255,0.78); line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { border: none; border-radius: var(--radius-btn); padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer; transition: 0.2s ease; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--primary { background: #fff; color: #1d4ed8; }
.btn--outline { background: rgba(255,255,255,0.15); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.alert { padding: 12px 16px; border-radius: 12px; font-size: 14px; }
.alert--error { background: rgba(239,68,68,0.08); color: #dc2626; border: 1px solid rgba(239,68,68,0.18); }
.alert--info { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.18); }
.stat-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; }
.stat-card { padding: 18px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.stat-label { display: block; color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }
.stat-card strong { font-size: 28px; color: var(--navy); }
.chart-grid { display: grid; grid-template-columns: 1fr 1.35fr; gap: 24px; }
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
.chart { height: 340px; width: 100%; }
.table-wrap { width: 100%; overflow-x: auto; }
.data-table { width: 100%; min-width: 900px; border-collapse: collapse; }
.data-table th, .data-table td { padding: 11px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.data-table th { background: rgba(241,245,249,0.8); color: #475569; font-weight: 700; }
.data-table tbody tr:hover { background: rgba(239,246,255,0.72); }
.keyword-cell { max-width: 260px; font-weight: 700; color: var(--navy); word-break: break-all; }
.heat-cell { color: #0ea5e9; font-weight: 700; }
.change-up { color: #16a34a; font-weight: 700; }
.date-cell { color: #475569; font-variant-numeric: tabular-nums; }
.table-empty { text-align: center; color: var(--text-light); padding: 28px; }
.stage-tag { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: rgba(100,116,139,0.1); color: #475569; }
.stage--new { color: #1d4ed8; background: rgba(59,130,246,0.12); }
.stage--rising { color: #15803d; background: rgba(34,197,94,0.12); }
.stage--stable_high { color: #7c3aed; background: rgba(139,92,246,0.12); }
.stage--falling { color: #64748b; background: rgba(100,116,139,0.12); }
.stage--cooling { color: #b45309; background: rgba(245,158,11,0.14); }
.stage--disappeared { color: #dc2626; background: rgba(239,68,68,0.12); }
@media (max-width: 1100px) { .stat-grid { grid-template-columns: repeat(3, 1fr); } .chart-grid { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .page-shell { padding: 16px 12px 36px; } .hero { flex-direction: column; align-items: flex-start; } .stat-grid { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 27px; } }
</style>
