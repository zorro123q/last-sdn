<template>
  <div class="page-shell">
    <main class="v6-page">
      <section class="hero hero--report">
        <div>
          <p class="eyebrow">AI Daily Report</p>
          <h1>AI 舆情日报</h1>
          <p class="hero-text">将热搜榜单、爆发趋势、生命周期、情感倾向、语义主题和预警结果自动汇总为中文 Markdown 日报。</p>
        </div>
        <div class="hero-actions">
          <button class="btn btn--outline" @click="loadData" :disabled="loading">{{ loading ? "刷新中..." : "刷新数据" }}</button>
          <button class="btn btn--primary" @click="handleRun" :disabled="running">{{ running ? "启动中..." : "生成新日报" }}</button>
          <button class="btn btn--outline" @click="copyMarkdown" :disabled="!latestReport.markdown_content">复制 Markdown</button>
        </div>
      </section>

      <div v-if="pageError" class="alert alert--error">{{ pageError }}</div>
      <div v-if="runMessage" class="alert alert--info">{{ runMessage }}</div>

      <section class="layout-grid">
        <article class="panel latest-card">
          <div class="panel-header">
            <div>
              <h2>最新日报</h2>
              <p>最近一次自动生成的舆情研判报告。</p>
            </div>
          </div>
          <div v-if="latestReport.id" class="report-meta">
            <strong>{{ latestReport.report_title }}</strong>
            <span>报告日期：{{ latestReport.report_date }}</span>
            <span>生成时间：{{ latestReport.created_at }}</span>
          </div>
          <div v-else class="empty-box">暂无 AI 舆情日报，请点击生成新日报。</div>
        </article>

        <article class="panel">
          <div class="panel-header">
            <div>
              <h2>历史日报</h2>
              <p>保留历次生成记录，便于答辩展示分析链路可追踪性。</p>
            </div>
          </div>
          <div class="history-list">
            <button
              v-for="item in reportList"
              :key="item.id"
              class="history-item"
              :class="{ 'history-item--active': item.id === latestReport.id }"
              @click="loadDetail(item.id)"
            >
              <strong>{{ item.report_title }}</strong>
              <span>{{ item.report_date }} · {{ item.created_at }}</span>
            </button>
            <div v-if="!reportList.length" class="empty-box">暂无历史日报</div>
          </div>
        </article>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h2>Markdown 日报正文</h2>
            <p>规则模板生成，后续可接入 OPENAI_API_KEY、OPENAI_MODEL 或 DASHSCOPE_API_KEY。</p>
          </div>
        </div>
        <pre class="markdown-body">{{ latestReport.markdown_content || "暂无日报正文。" }}</pre>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { getAiReportDetail, getAiReportList, getLatestAiReport, runAiReportJob } from "../api/index.js";

const latestReport = ref({});
const reportList = ref([]);
const loading = ref(false);
const running = ref(false);
const pageError = ref("");
const runMessage = ref("");

async function loadData() {
  loading.value = true;
  pageError.value = "";
  try {
    const [latestResponse, listResponse] = await Promise.all([
      getLatestAiReport(),
      getAiReportList(),
    ]);
    latestReport.value = latestResponse || {};
    reportList.value = listResponse.items || [];
  } catch (error) {
    latestReport.value = {};
    reportList.value = [];
    pageError.value = error.message || "AI 舆情日报加载失败";
  } finally {
    loading.value = false;
  }
}

async function loadDetail(reportId) {
  try {
    latestReport.value = await getAiReportDetail(reportId);
  } catch (error) {
    pageError.value = error.message || "日报详情加载失败";
  }
}

async function handleRun() {
  running.value = true;
  try {
    const response = await runAiReportJob();
    runMessage.value = response.message || "AI 舆情日报任务已启动";
    setTimeout(loadData, 1800);
  } catch (error) {
    runMessage.value = error.message || "AI 舆情日报任务启动失败";
  } finally {
    running.value = false;
  }
}

async function copyMarkdown() {
  const text = latestReport.value.markdown_content || "";
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    runMessage.value = "Markdown 内容已复制";
  } catch {
    pageError.value = "复制失败，请检查浏览器剪贴板权限";
  }
}

onMounted(loadData);
</script>

<style scoped>
.page-shell { min-height: calc(100vh - 64px); padding: 24px; }
.v6-page { max-width: 1440px; margin: 0 auto; display: grid; gap: 24px; }
.hero { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 32px; border-radius: var(--radius-card); color: #fff; box-shadow: var(--shadow-hero); }
.hero--report { background: linear-gradient(135deg, #4338ca, #0891b2); }
.eyebrow { margin: 0 0 8px; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.74); }
h1 { margin: 0; font-size: 34px; line-height: 1.15; }
h2 { margin: 0 0 6px; font-size: 20px; color: var(--navy); }
p { margin: 0; color: var(--text-muted); font-size: 14px; }
.hero-text { margin-top: 10px; max-width: 740px; color: rgba(255,255,255,0.8); line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { border: none; border-radius: var(--radius-btn); padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn:disabled { opacity: 0.65; cursor: not-allowed; }
.btn--primary { background: #fff; color: #4338ca; }
.btn--outline { background: rgba(255,255,255,0.14); color: #fff; border: 1px solid rgba(255,255,255,0.3); }
.alert { padding: 12px 16px; border-radius: 12px; font-size: 14px; }
.alert--error { background: rgba(239,68,68,0.08); color: #dc2626; border: 1px solid rgba(239,68,68,0.18); }
.alert--info { background: rgba(34,197,94,0.08); color: #15803d; border: 1px solid rgba(34,197,94,0.18); }
.layout-grid { display: grid; grid-template-columns: 1fr 1.35fr; gap: 24px; align-items: stretch; }
.panel { padding: 24px; border-radius: var(--radius-card); background: var(--bg-glass); border: 1px solid var(--border-light); box-shadow: var(--shadow-card); }
.panel-header { margin-bottom: 18px; }
.latest-card { min-height: 210px; }
.report-meta { display: grid; gap: 10px; }
.report-meta strong { font-size: 19px; color: var(--navy); }
.report-meta span { color: #64748b; font-size: 14px; }
.history-list { display: grid; gap: 10px; max-height: 280px; overflow: auto; padding-right: 4px; }
.history-item { text-align: left; border: 1px solid #e2e8f0; background: #fff; border-radius: 12px; padding: 12px 14px; cursor: pointer; }
.history-item strong { display: block; color: var(--navy); margin-bottom: 5px; }
.history-item span { color: #64748b; font-size: 12px; }
.history-item--active { border-color: rgba(67,56,202,0.45); background: rgba(67,56,202,0.06); }
.empty-box { padding: 28px; color: var(--text-light); text-align: center; border: 1.5px dashed rgba(148,163,184,0.4); border-radius: 14px; background: rgba(255,255,255,0.64); }
.markdown-body { white-space: pre-wrap; word-break: break-word; min-height: 520px; max-height: 760px; overflow: auto; padding: 22px; border-radius: 14px; border: 1px solid #e2e8f0; background: #0f172a; color: #e5edf8; line-height: 1.75; font-size: 14px; font-family: "Consolas", "Microsoft YaHei", monospace; }
@media (max-width: 1000px) { .layout-grid { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .page-shell { padding: 16px 12px 36px; } .hero { flex-direction: column; align-items: flex-start; } h1 { font-size: 27px; } }
</style>
