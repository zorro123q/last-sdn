<template>
  <div class="page-shell">
    <main class="v6-page">
      <section class="hero hero--risk">
        <div>
          <p class="eyebrow">Risk Warning Center</p>
          <h1>舆情风险预警中心</h1>
          <p class="hero-text">融合热度突增、排名跃升、负面情绪、爆发概率和生命周期阶段，形成主动风险预警。</p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadData" :disabled="loading">{{ loading ? "刷新中..." : "刷新数据" }}</button>
          <button class="btn btn--primary" @click="handleRun" :disabled="running">{{ running ? "启动中..." : "运行预警分析" }}</button>
        </div>
      </section>

      <div v-if="pageError" class="alert alert--error">{{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">{{ runMessage }}</div>

      <section class="stat-grid">
        <article v-for="item in statCards" :key="item.key" class="stat-card" :class="item.className">
          <span class="stat-label">{{ item.label }}</span>
          <strong>{{ formatNumber(item.value) }}</strong>
        </article>
      </section>

      <section class="chart-grid">
        <div class="panel">
          <div class="panel-header">
            <div>
              <h2>预警等级分布</h2>
              <p>按 low、medium、high、critical 分布展示当前风险态势。</p>
            </div>
          </div>
          <div ref="levelPieRef" class="chart"></div>
        </div>
        <div class="panel">
          <div class="panel-header">
            <div>
              <h2>预警类型分布</h2>
              <p>定位热度、情绪、爆发趋势和生命周期中的主要风险来源。</p>
            </div>
          </div>
          <div ref="typeBarRef" class="chart"></div>
        </div>
      </section>

      <section class="panel" v-if="highRiskAlerts.length">
        <div class="panel-header">
          <div>
            <h2>高风险预警列表</h2>
            <p>优先展示 high 与 critical 等级预警，适合答辩时展示主动监测能力。</p>
          </div>
        </div>
        <div class="risk-list">
          <article v-for="item in highRiskAlerts" :key="`risk-${item.id}`" class="risk-item" :class="`risk--${item.alert_level}`">
            <div class="risk-meta">
              <span class="level-tag" :class="`level--${item.alert_level}`">{{ item.alert_level_cn }}</span>
              <span>{{ item.alert_type_cn }}</span>
              <span>{{ item.created_at }}</span>
            </div>
            <strong>【{{ item.keyword }}】</strong>
            <p>{{ item.alert_message }}</p>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>全部预警</h2>
            <p>支持按风险等级筛选，并可将单条预警标记为已读。</p>
          </div>
          <div class="filter-bar">
            <select v-model="levelFilter" @change="loadAlerts">
              <option value="">全部等级</option>
              <option value="low">低风险</option>
              <option value="medium">中风险</option>
              <option value="high">高风险</option>
              <option value="critical">严重风险</option>
            </select>
          </div>
        </div>
        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>关键词</th>
                <th>等级</th>
                <th>类型</th>
                <th>触发值</th>
                <th>阈值</th>
                <th>消息</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in alertList" :key="item.id">
                <td class="keyword-cell">{{ item.keyword }}</td>
                <td><span class="level-tag" :class="`level--${item.alert_level}`">{{ item.alert_level_cn }}</span></td>
                <td>{{ item.alert_type_cn }}</td>
                <td>{{ formatMetric(item.trigger_value) }}</td>
                <td>{{ formatMetric(item.threshold_value) }}</td>
                <td class="message-cell">{{ item.alert_message }}</td>
                <td>{{ item.is_read ? "已读" : "未读" }}</td>
                <td>
                  <button class="table-btn" @click="handleRead(item)" :disabled="item.is_read">标记已读</button>
                </td>
              </tr>
              <tr v-if="!alertList.length">
                <td colspan="8" class="table-empty">暂无预警记录，请先运行预警分析</td>
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
import { getAlertList, getAlertSummary, markAlertRead, runAlertJob } from "../api/index.js";

const summary = ref({});
const alertList = ref([]);
const levelFilter = ref("");
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const runMessage = ref("");
const levelPieRef = ref(null);
const typeBarRef = ref(null);

let levelPie = null;
let typeBar = null;

const levelLabels = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  critical: "严重风险",
};

const levelColors = {
  low: "#3b82f6",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};

const statCards = computed(() => [
  { key: "total_alerts", label: "总预警数", value: summary.value.total_alerts },
  { key: "low_count", label: "低风险", value: summary.value.low_count, className: "stat--low" },
  { key: "medium_count", label: "中风险", value: summary.value.medium_count, className: "stat--medium" },
  { key: "high_count", label: "高风险", value: summary.value.high_count, className: "stat--high" },
  { key: "critical_count", label: "严重风险", value: summary.value.critical_count, className: "stat--critical" },
  { key: "unread_count", label: "未读预警", value: summary.value.unread_count },
]);

const highRiskAlerts = computed(() => alertList.value
  .filter((item) => item.alert_level === "high" || item.alert_level === "critical")
  .slice(0, 8));

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function formatMetric(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) return "0";
  if (Math.abs(number) <= 1) return `${(number * 100).toFixed(1)}%`;
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function buildCharts() {
  buildLevelPie();
  buildTypeBar();
}

function buildLevelPie() {
  if (!levelPieRef.value) return;
  if (!levelPie) levelPie = echarts.init(levelPieRef.value);
  const data = Object.keys(levelLabels).map((level) => ({
    name: levelLabels[level],
    value: alertList.value.filter((item) => item.alert_level === level).length,
    itemStyle: { color: levelColors[level] },
  })).filter((item) => item.value > 0);
  levelPie.setOption({
    tooltip: { trigger: "item", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "transparent", textStyle: { color: "#fff" } },
    legend: { bottom: 0, textStyle: { color: "#64748b" } },
    series: [{ name: "风险等级", type: "pie", radius: ["42%", "68%"], center: ["50%", "44%"], label: { color: "#334155" }, data }],
  }, true);
}

function buildTypeBar() {
  if (!typeBarRef.value) return;
  if (!typeBar) typeBar = echarts.init(typeBarRef.value);
  const counts = {};
  alertList.value.forEach((item) => {
    const name = item.alert_type_cn || item.alert_type || "未知";
    counts[name] = (counts[name] || 0) + 1;
  });
  const data = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  typeBar.setOption({
    tooltip: { trigger: "axis", backgroundColor: "rgba(15,23,42,0.92)", borderColor: "transparent", textStyle: { color: "#fff" } },
    grid: { left: 42, right: 22, top: 28, bottom: 72 },
    xAxis: { type: "category", data: data.map((item) => item[0]), axisLabel: { color: "#64748b", rotate: 26 } },
    yAxis: { type: "value", axisLabel: { color: "#64748b" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.18)", type: "dashed" } } },
    series: [{ type: "bar", data: data.map((item) => item[1]), barMaxWidth: 28, itemStyle: { color: "#f97316", borderRadius: [6, 6, 0, 0] } }],
  }, true);
}

async function loadAlerts() {
  const listResponse = await getAlertList(levelFilter.value, "", 300);
  alertList.value = listResponse.items || [];
  await nextTick();
  buildCharts();
}

async function loadData() {
  loading.value = true;
  pageError.value = "";
  try {
    const summaryResponse = await getAlertSummary();
    summary.value = summaryResponse || {};
    await loadAlerts();
  } catch (error) {
    pageError.value = error.message || "预警数据加载失败";
    summary.value = {};
    alertList.value = [];
    await nextTick();
    buildCharts();
  } finally {
    loading.value = false;
  }
}

async function handleRun() {
  running.value = true;
  try {
    const response = await runAlertJob();
    runMessage.value = response.message || "舆情预警任务已启动";
    setTimeout(loadData, 1800);
  } catch (error) {
    runMessage.value = error.message || "舆情预警任务启动失败";
  } finally {
    running.value = false;
  }
}

async function handleRead(item) {
  try {
    await markAlertRead(item.id);
    item.is_read = 1;
    await loadData();
  } catch (error) {
    pageError.value = error.message || "标记已读失败";
  }
}

function handleResize() {
  levelPie?.resize();
  typeBar?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  levelPie?.dispose();
  typeBar?.dispose();
  levelPie = null;
  typeBar = null;
});
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.v6-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); color: #fff; box-shadow: var(--shadow-hero); }
.hero--risk { background: linear-gradient(135deg, #991b1b, #f97316); }
.eyebrow { margin: 0 0 8px; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.75); }
h1 { margin: 0; font-size: 34px; line-height: 1.15; }
h2 { margin: 0 0 6px; font-size: 20px; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 700px; color: rgba(255,255,255,0.8); line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { border: none; border-radius: var(--radius-btn); padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--primary { background: #fff; color: #b91c1c; }
.btn--outline { background: rgba(255,255,255,0.14); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.alert { padding: 12px 16px; border-radius: 12px; font-size: 14px; }
.alert--error { background: rgba(239,68,68,0.08); color: #dc2626; border: 1px solid rgba(239,68,68,0.18); }
.alert--info { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.18); }
.stat-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; }
.stat-card { padding: 18px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.stat-label { display: block; color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }
.stat-card strong { font-size: 28px; color: var(--navy); }
.stat--low strong { color: #2563eb; }
.stat--medium strong { color: #d97706; }
.stat--high strong { color: #f97316; }
.stat--critical strong { color: #dc2626; }
.chart-grid { display: grid; grid-template-columns: 1fr 1.35fr; gap: 24px; }
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 18px; }
.chart { height: 340px; width: 100%; }
.filter-bar select { padding: 9px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; color: #334155; }
.risk-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
.risk-item { padding: 16px; border-radius: 14px; border: 1px solid rgba(148,163,184,0.25); background: #fff; }
.risk-item strong { display: block; margin: 8px 0 6px; color: var(--navy); }
.risk-item p { line-height: 1.7; }
.risk-meta { display: flex; flex-wrap: wrap; gap: 8px; color: #64748b; font-size: 12px; }
.risk--critical { border-color: rgba(239,68,68,0.35); background: rgba(239,68,68,0.04); }
.risk--high { border-color: rgba(249,115,22,0.35); background: rgba(249,115,22,0.04); }
.table-wrap { width: 100%; overflow-x: auto; }
.data-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.data-table th, .data-table td { padding: 11px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.data-table th { background: rgba(241,245,249,0.8); color: #475569; font-weight: 700; }
.data-table tbody tr:hover { background: rgba(255,247,237,0.6); }
.keyword-cell { max-width: 220px; font-weight: 700; color: var(--navy); word-break: break-all; }
.message-cell { min-width: 360px; line-height: 1.6; color: #475569; }
.table-empty { text-align: center; color: var(--text-light); padding: 28px; }
.level-tag { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.level--low { background: rgba(59,130,246,0.12); color: #2563eb; }
.level--medium { background: rgba(245,158,11,0.16); color: #b45309; }
.level--high { background: rgba(249,115,22,0.16); color: #c2410c; }
.level--critical { background: rgba(239,68,68,0.14); color: #dc2626; }
.table-btn { border: 1px solid #cbd5e1; background: #fff; color: #334155; border-radius: 8px; padding: 6px 10px; cursor: pointer; }
.table-btn:disabled { color: #94a3b8; cursor: not-allowed; }
@media (max-width: 1100px) { .stat-grid { grid-template-columns: repeat(3, 1fr); } .chart-grid { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .page-shell { padding: 16px 12px 36px; } .hero { flex-direction: column; align-items: flex-start; } .stat-grid { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 27px; } }
</style>
