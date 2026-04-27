# 微博热搜舆情智能分析平台 - 长期记忆

## 项目设计规范（2026-04-25 确立）

### CSS 变量系统
```css
:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --primary-light: #3b82f6;
  --accent: #06b6d4;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --navy: #0f172a;
  --navy-mid: #1e293b;
  --text-base: #1e293b;
  --text-muted: #64748b;
  --text-light: #94a3b8;
  --bg-glass: rgba(255, 255, 255, 0.92);
  --border-light: rgba(148, 163, 184, 0.25);
  --shadow-card: 0 8px 32px rgba(15, 23, 42, 0.08);
  --shadow-hero: 0 12px 40px rgba(15, 23, 42, 0.1);
  --radius-card: 20px;
  --radius-btn: 12px;
  --nav-height: 64px;
}
```

### 页面布局规范
- 所有页面容器：`max-width: 1440px; margin: 0 auto;`
- 页面内边距：`padding: 24px`
- 卡片间距：`gap: 24px`
- 移动端 padding：`16px 12px 36px`

### Hero 区规范
- 背景：`linear-gradient(135deg, #2563eb 0%, #1d4ed8 50%, #1e40af 100%)`
- 文字颜色：白色，副标题使用 `rgba(255,255,255,0.75)`
- 装饰：`radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08), transparent 50%)`

### 统计卡片规范
- 4 列 grid（桌面端），2 列（平板），2 列（手机）
- 顶部 3px 颜色条区分类型
- Icon wrap：48px 圆角方块，背景色 10% 透明度
- 悬停：`transform: translateY(-2px)` + 加深阴影

### 图表颜色规范
- 主色：`#2563eb`（蓝）
- 辅助：`#06b6d4`（青）、`#8b5cf6`（紫）
- 情感：正 `#22c55e`、负 `#ef4444`、中 `#94a3b8`
- 禁止使用橙红色系作为图表主色

### 图标规范
- 不使用 emoji 作为 UI 图标
- 统一使用 Lucide 风格 SVG（stroke-width="2"）
- 默认尺寸：16px（按钮内）、18px（提示）、24px（卡片）

## 技术栈
- 前端：Vue3 + Vite + ECharts + echarts-wordcloud
- 后端：Python + FastAPI + MySQL
- 分析：PySpark + SnowNLP + Sentence-Transformers + KMeans
- 采集：Python 定时爬虫

## 数据同步链路修复记录（2026-04-26）

### 问题根因
1. 项目根目录缺少 `.env` 文件，collector 和 backend 都使用硬编码默认值（相同），实际连接同一个库，但建议总是用 `.env` 管理
2. `Dashboard.vue` 只在 `onMounted` 时加载一次数据，没有自动轮询，collector 写入新数据后前端无法感知

### 修复内容
- 创建了 `.env`（从 `.env.example` 复制）
- `collector/db_writer.py`：增加写入成功/失败的详细日志（含 host、db 信息）
- `backend/routes/debug.py`（新增）：`GET /api/debug/db-status` 调试接口
- `backend/main.py`：注册 debug_router
- `backend/routes/summary.py`：数据为空时返回中文 tip 提示
- `backend/routes/ranking.py`：数据为空时返回中文 tip 提示
- `frontend/src/views/Dashboard.vue`：
  - 新增 `startAutoRefresh()`/`stopAutoRefresh()` 函数，`setInterval` 每 30 秒触发一次静默刷新
  - `onBeforeUnmount` 时清除定时器防内存泄漏
  - 有关键词时自动轮询同步刷新趋势图
  - Hero 区增加"自动刷新中，每 30 秒更新"状态指示器（绿色脉冲点 + 上次刷新时间）
  - 增加 `noDataTip` 变量，数据库为空时显示友好提示，告知用户运行 collector
- `README.md`：顶部新增"🚀 快速启动"章节（含四步启动顺序、常见问题诊断表格）

### 关键接口
- `GET /api/debug/db-status` 用于排查 collector/backend 是否连同一个库

