<template>
  <div class="app-shell" :class="{ 'bigscreen-mode': isBigScreen }">
    <!-- 顶部导航栏（大屏模式下隐藏） -->
    <header v-if="!isBigScreen" class="top-nav">
      <div class="nav-inner">
        <!-- Logo 区域 -->
        <div class="nav-brand">
          <span class="brand-icon">🔥</span>
          <span class="brand-name">微博热搜分析系统</span>
          <span class="brand-tag">毕业设计</span>
        </div>

        <!-- 导航菜单 -->
        <nav class="nav-menu">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            active-class="nav-item--active"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </nav>

        <!-- 右侧操作区 -->
        <div class="nav-right">
          <router-link to="/bigscreen" class="bigscreen-btn" title="进入可视化大屏">
            <span>📺</span>
            <span>大屏模式</span>
          </router-link>
          <div class="live-dot">
            <span class="dot-pulse"></span>
            <span class="dot-label">实时数据</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 大屏模式返回按钮 -->
    <div v-if="isBigScreen" class="bigscreen-back">
      <router-link to="/dashboard" class="back-btn">← 返回普通模式</router-link>
      <span class="bigscreen-time">{{ currentTime }}</span>
    </div>

    <!-- 页面内容 -->
    <main class="page-content" :class="{ 'page-content--padded': !isBigScreen }">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const currentTime = ref("");

const isBigScreen = computed(() => route.path === "/bigscreen");

const navItems = [
  { path: "/dashboard", label: "实时总览", icon: "📊" },
  { path: "/analysis", label: "PySpark 分析", icon: "⚡" },
  { path: "/burst", label: "ML 爆发趋势", icon: "🚀" },
  { path: "/sentiment", label: "评论情感分析", icon: "🌍" },
  { path: "/sentiment-analysis", label: "情感语义分析", icon: "💡" },
];

let timer = null;

function updateTime() {
  const now = new Date();
  currentTime.value = now.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

onMounted(() => {
  updateTime();
  timer = setInterval(updateTime, 1000);
});

onBeforeUnmount(() => {
  clearInterval(timer);
});
</script>

<style>
/* ===================== 全局重置与基础变量 ===================== */
:root {
  --primary: #e4572e;
  --primary-dark: #c23d1a;
  --accent: #2a9d8f;
  --navy: #16324f;
  --navy-mid: #274c77;
  --text-base: #1f2937;
  --text-muted: #5b6475;
  --text-light: #94a3b8;
  --bg-glass: rgba(255, 255, 255, 0.88);
  --border-light: rgba(157, 176, 208, 0.32);
  --shadow-card: 0 16px 38px rgba(82, 100, 128, 0.1);
  --shadow-hero: 0 18px 48px rgba(82, 100, 128, 0.12);
  --radius-card: 20px;
  --radius-btn: 12px;
  --nav-height: 64px;
  --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: radial-gradient(circle at 15% 5%, rgba(69, 123, 157, 0.22), transparent 30%),
    radial-gradient(circle at 85% 90%, rgba(228, 87, 46, 0.1), transparent 30%),
    linear-gradient(145deg, #eef4ff 0%, #f5f8fc 50%, #fff8f5 100%);
  min-height: 100vh;
  color: var(--text-base);
  overflow-x: hidden;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(157, 176, 208, 0.5);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(87, 117, 144, 0.6);
}
</style>

<style scoped>
/* ===================== 应用容器 ===================== */
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ===================== 顶部导航栏 ===================== */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-height);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-light);
  box-shadow: 0 2px 20px rgba(82, 100, 128, 0.08);
}

.nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  height: 100%;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 32px;
}

/* Brand */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}

.brand-icon {
  font-size: 22px;
  filter: drop-shadow(0 2px 4px rgba(228, 87, 46, 0.35));
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--navy);
  letter-spacing: 0.02em;
}

.brand-tag {
  padding: 2px 8px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--primary), #f4723e);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

/* 导航菜单 */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-btn);
  text-decoration: none;
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition);
  position: relative;
}

.nav-item:hover {
  background: rgba(228, 87, 46, 0.06);
  color: var(--primary);
}

.nav-item--active {
  background: rgba(228, 87, 46, 0.1);
  color: var(--primary);
  font-weight: 600;
}

.nav-item--active::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 16px;
  right: 16px;
  height: 2px;
  background: var(--primary);
  border-radius: 2px 2px 0 0;
  transform: translateY(1px);
}

.nav-icon {
  font-size: 16px;
}

/* 右侧 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
  flex-shrink: 0;
}

.bigscreen-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-btn);
  background: linear-gradient(135deg, var(--navy-mid), var(--navy));
  color: #fff;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all var(--transition);
  box-shadow: 0 4px 12px rgba(22, 50, 79, 0.3);
}

.bigscreen-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(22, 50, 79, 0.36);
}

.live-dot {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  animation: pulse-ring 1.8s ease-out infinite;
}

@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(34, 197, 94, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
  }
}

.dot-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

/* ===================== 大屏模式 ===================== */
.bigscreen-mode {
  background: none;
}

.bigscreen-back {
  position: fixed;
  top: 14px;
  left: 20px;
  z-index: 200;
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  padding: 7px 14px;
  border-radius: 10px;
  background: rgba(22, 50, 79, 0.75);
  backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all var(--transition);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.back-btn:hover {
  background: rgba(22, 50, 79, 0.9);
}

.bigscreen-time {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.03em;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

/* ===================== 页面内容 ===================== */
.page-content {
  flex: 1;
}

.page-content--padded {
  padding-top: 0;
}

/* ===================== 页面切换过渡动画 ===================== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ===================== 响应式 ===================== */
@media (max-width: 768px) {
  .nav-inner {
    padding: 0 16px;
    gap: 16px;
  }

  .brand-name {
    display: none;
  }

  .bigscreen-btn span:last-child {
    display: none;
  }

  .dot-label {
    display: none;
  }

  .nav-item {
    padding: 8px 12px;
  }

  .nav-label {
    display: none;
  }
}
</style>
