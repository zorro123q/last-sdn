# 微博热搜准实时分析系统

这是一个面向毕业设计讲解场景的第一版可运行项目，目标是先跑通最小主链路：

`数据采集 -> Kafka -> Spark Structured Streaming -> MySQL/Redis -> FastAPI -> Vue3 + ECharts`

## 1. 项目结构

```text
weibo-hot-project/
├─ .env.example
├─ docker-compose.yml
├─ README.md
├─ collector/
├─ streaming/
├─ backend/
├─ frontend/
└─ sql/
```

其中：

- `collector/` 负责采集微博热搜并发送到 Kafka。
- `streaming/` 负责消费 Kafka，写入 MySQL 和 Redis。
- `backend/` 负责对外提供查询接口。
- `frontend/` 负责展示排行榜和趋势图。
- `sql/` 负责初始化数据库结构。

## 2. 环境准备

建议本地准备以下环境：

- Docker Desktop
- Python 3.10+
- Node.js 18+
- Java 8/11
- Spark 3.5.x

先复制环境变量模板：

```powershell
cd weibo-hot-project
Copy-Item .env.example .env
```

Linux / macOS：

```bash
cd weibo-hot-project
cp .env.example .env
```

## 3. 启动顺序

### 第一步：启动基础依赖

```powershell
docker compose up -d
```

### 第二步：初始化数据库

PowerShell：

```powershell
Get-Content .\sql\init.sql | docker compose exec -T mysql mysql -uroot -proot
```

Bash：

```bash
docker compose exec -T mysql mysql -uroot -proot < sql/init.sql
```

### 第三步：启动 collector

```powershell
pip install -r .\collector\requirements.txt
python .\collector\app.py
```

说明：

- 默认每 300 秒采集一次。
- 如果只想试跑一次，可在 `.env` 中设置 `COLLECTOR_RUN_ONCE=true`。
- 采集接口默认使用 `https://weibo.com/ajax/side/hotSearch`，如果微博接口返回结构变化，代码会尝试做常见字段兼容解析。

### 第四步：启动 streaming

```powershell
pip install -r .\streaming\requirements.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.mysql:mysql-connector-j:8.3.0 .\streaming\spark_job.py
```

说明：

- 第一版会把展开后的热搜数据写入 MySQL 表 `hot_search_raw`。
- 同时会把当前批次按 `hot_value` 排序后的前 20 条写入 Redis Sorted Set `weibo:ranking:current`。

### 第五步：启动 backend

```powershell
pip install -r .\backend\requirements.txt
cd .\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 第六步：启动 frontend

新开一个终端：

```powershell
cd .\frontend
npm install
npm run dev
```

浏览器访问：

- 前端页面：`http://localhost:5173`
- 后端接口文档：`http://localhost:8000/docs`

## 4. 接口说明

### `GET /api/ranking/current`

返回 Redis 中当前热搜榜。

### `GET /api/trend?keyword=xxx`

返回 MySQL 中某关键词的趋势数据，第一版按采集时间聚合最大热度值。

### `GET /api/summary`

返回总记录数、关键词数量、最新采集时间等概览信息。

## 5. 验证步骤

### 验证 Kafka 是否收到消息

如果 collector 日志里出现“采集成功，条目数=xx”，通常说明已成功发送 Kafka。

### 验证 MySQL 是否有数据

```powershell
docker compose exec mysql mysql -uroot -proot -D weibo_hot -e "SELECT id, rank_no, title, hot_value, fetch_time FROM hot_search_raw ORDER BY id DESC LIMIT 10;"
```

### 验证 Redis 是否有排行榜

```powershell
docker compose exec redis redis-cli ZREVRANGE weibo:ranking:current 0 19 WITHSCORES
```

### 验证后端接口

```powershell
Invoke-RestMethod http://localhost:8000/api/summary
Invoke-RestMethod http://localhost:8000/api/ranking/current
Invoke-RestMethod "http://localhost:8000/api/trend?keyword=电影"
```

### 验证前端页面

确认页面能看到：

- 标题区
- 概览卡片
- 当前热搜榜
- 关键词趋势查询和折线图

## 6. 当前版本说明

当前版本刻意只做最小可运行主链路，没有加入以下能力：

- 情感分析
- LSTM / 预测模型
- 登录鉴权
- 多数据源切换
- 复杂统计任务编排

## 7. 后续可扩展点

- 在 `streaming/` 中把聚合结果写入 `hot_search_stats`
- 增加关键词分类、话题标签和分桶统计
- 对接 Airflow 或 Windows 计划任务做采集调度
- 增加历史排行榜分页查询
- 增加异常告警和任务状态监控

## 8. 运行注意事项

- 微博公开接口有可能出现限流、字段变化或临时不可用，这种情况下需要在 `.env` 中更换 `WEIBO_API_URL` 或增加请求头。
- Spark 首次启动 `--packages` 时会下载依赖 JAR，如果网络受限，需要提前准备对应 JAR。
- 当前版本优先保证链路可讲解、模块职责清晰，暂未做生产级容错和性能调优。
# last-sdn
