<template>
  <Dashboard />
</template>

<script setup>
// 根组件只挂载主看板页面，避免第一版结构过重。
import Dashboard from "./views/Dashboard.vue";
</script>

<style>
:root {
  color: #1f2937;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top right, rgba(248, 113, 113, 0.18), transparent 28%),
    linear-gradient(180deg, #fff8f4 0%, #f4f7fb 100%);
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  margin: 0;
}
</style>
