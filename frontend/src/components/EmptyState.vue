<template>
  <div class="empty-state">
    <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="3" y1="9" x2="21" y2="9"></line>
      <line x1="9" y1="21" x2="9" y2="9"></line>
    </svg>
    <p class="empty-title">{{ title || "暂无数据" }}</p>
    <p v-if="description" class="empty-desc">{{ description }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: "" },
  description: { type: String, default: "" },
});
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 20px;
  color: var(--text-muted);
  text-align: center;
}
.empty-icon {
  width: 40px;
  height: 40px;
  color: var(--text-light);
}
.empty-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}
.empty-desc {
  font-size: 13px;
  color: var(--text-light);
  margin: 0;
  max-width: 360px;
  line-height: 1.5;
}
</style>
