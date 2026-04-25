import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import Dashboard from "./views/Dashboard.vue";
import Analysis from "./views/Analysis.vue";
import BurstAnalysis from "./views/BurstAnalysis.vue";
import BigScreen from "./views/BigScreen.vue";
import SentimentMap from "./views/SentimentMap.vue";
import SentimentAnalysis from "./views/SentimentAnalysis.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard", component: Dashboard, meta: { title: "实时总览" } },
  { path: "/analysis", component: Analysis, meta: { title: "PySpark 分析" } },
  { path: "/burst", component: BurstAnalysis, meta: { title: "ML 爆发趋势" } },
  { path: "/sentiment", component: SentimentMap, meta: { title: "评论情感分析" } },
  { path: "/sentiment-analysis", component: SentimentAnalysis, meta: { title: "情感语义分析" } },
  { path: "/bigscreen", component: BigScreen, meta: { title: "可视化大屏" } },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

const app = createApp(App);
app.use(router);
app.mount("#app");
