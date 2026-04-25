<template>
  <div>
    <nav class="app-nav">
      <button
        type="button"
        :class="{ active: currentView === 'dashboard' }"
        @click="currentView = 'dashboard'"
      >
        首页大屏
      </button>
      <button
        type="button"
        :class="{ active: currentView === 'analysis' }"
        @click="currentView = 'analysis'"
      >
        PySpark 分析
      </button>
    </nav>
    <Dashboard v-if="currentView === 'dashboard'" />
    <Analysis v-else />
  </div>
</template>

<script setup>
import { ref } from "vue";

import Analysis from "./views/Analysis.vue";
import Dashboard from "./views/Dashboard.vue";

const currentView = ref("dashboard");
</script>

<style scoped>
.app-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 14px 16px 0;
}

.app-nav button {
  padding: 10px 16px;
  border: 1px solid rgba(157, 176, 208, 0.48);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  color: #16324f;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(82, 100, 128, 0.08);
}

.app-nav button.active {
  border-color: #16324f;
  background: #16324f;
  color: #ffffff;
}
</style>
