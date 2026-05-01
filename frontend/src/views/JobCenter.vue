<template>
  <div class="page-shell">
    <main class="v6-page">
      <section class="hero hero--jobs">
        <div>
          <p class="eyebrow">Analysis Job Center</p>
          <h1>分析任务调度中心</h1>
          <p class="hero-text">统一触发 PySpark、机器学习、情感、语义、生命周期、预警和日报任务，并记录运行日志。</p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadJobs" :disabled="loading">{{ loading ? "刷新中..." : "刷新任务列表" }}</button>
          <button class="btn btn--primary" @click="handleRunAll" :disabled="runningAll">{{ runningAll ? "执行中..." : "一键运行全部分析" }}</button>
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

      <section class="content-grid">
        <article class="panel">
          <div class="panel-header">
            <div>
              <h2>任务列表</h2>
              <p>记录全链路分析任务的开始时间、结束时间、耗时和失败原因。</p>
            </div>
          </div>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>任务名称</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>开始时间</th>
                  <th>结束时间</th>
                  <th>耗时</th>
                  <th>错误信息</th>
                  <th>详情</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in jobList" :key="item.id">
                  <td class="keyword-cell">{{ item.job_name }}</td>
                  <td>{{ item.job_type }}</td>
                  <td><span class="status-tag" :class="`status--${item.status}`">{{ item.status_cn }}</span></td>
                  <td class="date-cell">{{ item.start_time || "-" }}</td>
                  <td class="date-cell">{{ item.end_time || "-" }}</td>
                  <td>{{ formatDuration(item.duration_seconds) }}</td>
                  <td class="error-cell">{{ item.error_message || "-" }}</td>
                  <td><button class="table-btn" @click="loadDetail(item.id)">查看日志</button></td>
                </tr>
                <tr v-if="!jobList.length">
                  <td colspan="8" class="table-empty">暂无任务记录，请先执行一键运行全部分析</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>

        <aside class="panel detail-panel">
          <div class="panel-header">
            <div>
              <h2>任务详情</h2>
              <p>展示所选任务的 command_text 与 log_text。</p>
            </div>
          </div>
          <div v-if="selectedJob.id" class="job-detail">
            <div class="detail-row"><span>任务</span><strong>{{ selectedJob.job_name }}</strong></div>
            <div class="detail-row"><span>命令</span><code>{{ selectedJob.command_text || "-" }}</code></div>
            <pre class="log-box">{{ selectedJob.log_text || "暂无日志内容。" }}</pre>
          </div>
          <div v-else class="empty-box">选择左侧任务查看运行日志。</div>
        </aside>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { getJobDetail, getJobList, runAllJobs } from "../api/index.js";

const jobList = ref([]);
const selectedJob = ref({});
const loading = ref(false);
const runningAll = ref(false);
const pageError = ref("");
const runMessage = ref("");

const statCards = computed(() => {
  const total = jobList.value.length;
  const success = jobList.value.filter((item) => item.status === "success").length;
  const failed = jobList.value.filter((item) => item.status === "failed").length;
  const running = jobList.value.filter((item) => item.status === "running").length;
  return [
    { key: "total", label: "总任务数", value: total },
    { key: "success", label: "成功任务", value: success, className: "stat--success" },
    { key: "failed", label: "失败任务", value: failed, className: "stat--failed" },
    { key: "running", label: "运行中任务", value: running, className: "stat--running" },
  ];
});

function formatNumber(value) {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString("zh-CN") : "0";
}

function formatDuration(value) {
  const seconds = Number(value || 0);
  if (!Number.isFinite(seconds) || seconds <= 0) return "-";
  if (seconds < 60) return `${seconds.toFixed(1)} 秒`;
  return `${(seconds / 60).toFixed(1)} 分钟`;
}

async function loadJobs() {
  loading.value = true;
  pageError.value = "";
  try {
    const response = await getJobList();
    jobList.value = response.items || [];
  } catch (error) {
    jobList.value = [];
    pageError.value = error.message || "任务列表加载失败";
  } finally {
    loading.value = false;
  }
}

async function loadDetail(jobId) {
  try {
    selectedJob.value = await getJobDetail(jobId);
  } catch (error) {
    pageError.value = error.message || "任务详情加载失败";
  }
}

async function handleRunAll() {
  runningAll.value = true;
  pageError.value = "";
  runMessage.value = "全链路分析任务正在执行，接口会在任务结束后返回结果。";
  try {
    const response = await runAllJobs();
    runMessage.value = `${response.message || "任务执行完成"}，成功 ${response.success_count || 0} 个，失败 ${response.failed_count || 0} 个。`;
    await loadJobs();
  } catch (error) {
    pageError.value = error.message || "一键运行全部分析失败";
  } finally {
    runningAll.value = false;
  }
}

onMounted(loadJobs);
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.v6-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); color: #fff; box-shadow: var(--shadow-hero); }
.hero--jobs { background: linear-gradient(135deg, #1e293b, #2563eb); }
.eyebrow { margin: 0 0 8px; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.74); }
h1 { margin: 0; font-size: 34px; line-height: 1.15; }
h2 { margin: 0 0 6px; font-size: 20px; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 740px; color: rgba(255,255,255,0.8); line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { border: none; border-radius: var(--radius-btn); padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--primary { background: #fff; color: #1e293b; }
.btn--outline { background: rgba(255,255,255,0.14); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.alert { padding: 12px 16px; border-radius: 12px; font-size: 14px; }
.alert--error { background: rgba(239,68,68,0.08); color: #dc2626; border: 1px solid rgba(239,68,68,0.18); }
.alert--info { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.18); }
.stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.stat-card { padding: 18px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.stat-label { display: block; color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }
.stat-card strong { font-size: 28px; color: var(--navy); }
.stat--success strong { color: #16a34a; }
.stat--failed strong { color: #dc2626; }
.stat--running strong { color: #2563eb; }
.content-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr); gap: 24px; align-items: start; }
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { margin-bottom: 18px; }
.table-wrap { width: 100%; overflow-x: auto; }
.data-table { width: 100%; min-width: 980px; border-collapse: collapse; }
.data-table th, .data-table td { padding: 11px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; font-size: 14px; }
.data-table th { background: rgba(241,245,249,0.8); color: #475569; font-weight: 700; }
.data-table tbody tr:hover { background: rgba(239,246,255,0.7); }
.keyword-cell { max-width: 220px; font-weight: 700; color: var(--navy); word-break: break-all; }
.date-cell { color: #475569; font-variant-numeric: tabular-nums; }
.error-cell { max-width: 260px; color: #dc2626; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-empty { text-align: center; color: var(--text-light); padding: 28px; }
.table-btn { border: 1px solid #cbd5e1; background: #fff; color: #334155; border-radius: 8px; padding: 6px 10px; cursor: pointer; }
.status-tag { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: rgba(100,116,139,0.12); color: #475569; }
.status--success { background: rgba(34,197,94,0.12); color: #15803d; }
.status--failed { background: rgba(239,68,68,0.12); color: #dc2626; }
.status--running { background: rgba(37,99,235,0.12); color: #1d4ed8; }
.status--pending { background: rgba(245,158,11,0.14); color: #b45309; }
.detail-panel { position: sticky; top: 84px; }
.job-detail { display: grid; gap: 12px; }
.detail-row { display: grid; gap: 5px; font-size: 13px; color: #64748b; }
.detail-row strong { color: var(--navy); }
.detail-row code { padding: 9px 10px; border-radius: 8px; background: #f1f5f9; color: #334155; white-space: pre-wrap; }
.log-box { min-height: 360px; max-height: 620px; overflow: auto; white-space: pre-wrap; padding: 14px; border-radius: 12px; background: #0f172a; color: #dbeafe; line-height: 1.6; font-size: 12px; }
.empty-box { padding: 28px; color: var(--text-light); text-align: center; border: 1.5px dashed rgba(148,163,184,0.4); border-radius: 14px; background: rgba(255,255,255,0.64); }
@media (max-width: 1180px) { .content-grid { grid-template-columns: 1fr; } .detail-panel { position: static; } }
@media (max-width: 760px) { .page-shell { padding: 16px 12px 36px; } .hero { flex-direction: column; align-items: flex-start; } .stat-grid { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 27px; } }
</style>
