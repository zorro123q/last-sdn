# 微博热搜分析系统

这是一个适合毕业设计演示的微博热搜采集、存储、分析与可视化项目。

第一期主链路：

`Python 定时采集 -> MySQL 原始表 hot_search_raw -> FastAPI -> Vue3 + ECharts`

第二期已完成采集重试、`.env.example` 配置补齐、README 使用说明、前端中文化和基础异常提示。默认采集间隔为 `120` 秒。

第三期新增 PySpark 离线批处理分析：

`hot_search_raw -> analysis/batch_job.py -> hot_search_keyword_stats / hot_search_daily_stats -> FastAPI 分析接口 -> Vue Analysis 页面`

第四期新增机器学习数据挖掘增强：

`hot_search_raw -> ml 特征工程 -> 爆发趋势识别 -> TF-IDF + KMeans 主题聚类 -> MySQL 结果表 -> FastAPI 机器学习接口 -> Vue BurstAnalysis 页面 -> CSV / Excel 报告导出`

项目不引入 Redis、Kafka、Spark Streaming、Structured Streaming、登录鉴权或 WebSocket。

## 1. 项目结构

```text
weibo-hot-project/
├─ .env.example
├─ README.md
├─ collector/
│  ├─ app.py
│  ├─ api_client.py
│  ├─ db_writer.py
│  ├─ config.py
│  └─ requirements.txt
├─ analysis/
│  ├─ batch_job.py
│  ├─ spark_session.py
│  ├─ config.py
│  ├─ readers/mysql_reader.py
│  ├─ processors/keyword_stats.py
│  ├─ processors/daily_stats.py
│  ├─ writers/mysql_writer.py
│  └─ requirements.txt
├─ ml/
│  ├─ config.py
│  ├─ data_loader.py
│  ├─ feature_builder.py
│  ├─ label_builder.py
│  ├─ train_model.py
│  ├─ predict_job.py
│  ├─ topic_cluster.py
│  ├─ report_exporter.py
│  ├─ model_store/.gitkeep
│  └─ requirements.txt
├─ backend/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ routes/
│  │  ├─ analysis.py
│  │  ├─ ml_analysis.py
│  │  ├─ ranking.py
│  │  ├─ trend.py
│  │  └─ summary.py
│  └─ services/
│     ├─ analysis_service.py
│     ├─ ml_analysis_service.py
│     └─ mysql_service.py
├─ frontend/
│  └─ src/views/
│     ├─ Dashboard.vue
│     ├─ Analysis.vue
│     └─ BurstAnalysis.vue
└─ sql/
   ├─ init.sql
   ├─ v3_stats.sql
   └─ v4_ml_analysis.sql
```

## 2. 环境要求

- Python 3.10+
- conda
- MySQL 8.0+
- Node.js 18+
- npm 9+
- JDK 8、11 或 17
- 已配置 `JAVA_HOME`
- PySpark
- MySQL Connector/J Jar

`analysis/requirements.txt` 只安装 Python 包，不包含 JDBC Jar。MySQL Connector/J 需要单独下载，例如放到：

```text
C:/drivers/mysql-connector-j-8.4.0.jar
```

并在 `.env` 中配置：

```env
SPARK_MYSQL_JAR=C:/drivers/mysql-connector-j-8.4.0.jar
```

## 3. 配置说明

首次运行前，在项目根目录复制示例配置：

```powershell
Copy-Item .env.example .env
```

然后按需修改 `.env`：

1. 修改 `MYSQL_PASSWORD` 为本机 MySQL 密码。
2. 如果微博接口访问受限，可以填写 `WEIBO_COOKIE`，不要把真实 Cookie 写入代码。
3. 如果采集过快或不稳定，可以调大 `COLLECT_INTERVAL_SECONDS`。
4. 如果网络较慢，可以适当调大 `WEIBO_API_TIMEOUT`。
5. 第三期运行 PySpark 前，配置 `SPARK_MYSQL_JAR`。
6. 第四期机器学习配置可以不填，系统会使用 `.env.example` 中的默认值。

第四期机器学习配置含义：

- `ML_MIN_HISTORY_COUNT`：单个热搜标题至少出现多少次才构造特征，默认 `3`。
- `ML_RECENT_WINDOW`：计算最近热度变化和排名变化的窗口大小，默认 `5`。
- `ML_BURST_HOT_GROWTH_THRESHOLD`：判定爆发型热搜的热度增长率阈值，默认 `0.3`。
- `ML_BURST_TOP_RANK_THRESHOLD`：进入前多少名可视为潜在爆发，默认 `10`。
- `ML_MODEL_NAME`：爆发趋势识别模型名，默认 `sklearn_gradient_boosting`，也支持代码中预留的 `sklearn_random_forest`。
- `ML_CLUSTER_COUNT`：KMeans 主题聚类数量，默认 `6`。
- `ML_TOP_LIMIT`：爆发趋势识别结果最多写入条数，默认 `100`。
- `ML_MODEL_DIR`：模型文件保存目录，默认 `ml/model_store`。

## 4. 初始化步骤

### 4.1 创建原始表

PowerShell 不能直接使用 `<` 输入重定向，推荐使用：

```powershell
cmd /c "mysql -u root -p < sql\init.sql"
```

如果需要指定数据库，也可以使用：

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\init.sql"
```

### 4.2 创建第三期统计表

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\v3_stats.sql"
```

等价的 MySQL 命令是：

```powershell
mysql -u root -p weibo_hot < sql/v3_stats.sql
```

如果 PowerShell 不支持 `<` 重定向，请使用上面的 `cmd /c` 写法。

### 4.3 创建第四期机器学习结果表

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\v4_ml_analysis.sql"
```

等价的 MySQL 命令是：

```powershell
mysql -u root -p weibo_hot < sql/v4_ml_analysis.sql
```

如果 PowerShell 不支持 `<` 重定向，请使用上面的 `cmd /c` 写法。

### 4.4 创建 conda 环境并安装依赖

```powershell
conda create -n sdn python=3.11
conda activate sdn
pip install -r collector\requirements.txt
pip install -r backend\requirements.txt
```

安装 PySpark 分析依赖：

```powershell
cd analysis
pip install -r requirements.txt
cd ..
```

安装第四期机器学习依赖：

```powershell
cd ml
pip install -r requirements.txt
cd ..
```

安装前端依赖：

```powershell
cd frontend
npm install
cd ..
```

## 5. 启动方式

### 5.1 单次采集测试

在 Windows PowerShell 中可以使用：

```powershell
cd collector
$env:COLLECT_RUN_ONCE="true"
python app.py
```

### 5.2 恢复循环采集

```powershell
cd collector
$env:COLLECT_RUN_ONCE="false"
python app.py
```

循环采集默认每 `120` 秒执行一次，可通过 `.env` 中的 `COLLECT_INTERVAL_SECONDS` 修改。

### 5.3 运行 PySpark 分析任务

确认已经采集到 `hot_search_raw` 数据，并已经执行 `sql/v3_stats.sql` 后，在项目根目录运行：

```powershell
python analysis/batch_job.py
```

任务会读取 `hot_search_raw`，生成：

- `hot_search_keyword_stats`
- `hot_search_daily_stats`

### 5.4 运行机器学习爆发趋势识别

确认已经采集到足够的 `hot_search_raw` 历史数据，并已经执行 `sql/v4_ml_analysis.sql` 后，在项目根目录运行：

```powershell
python ml/predict_job.py
```

任务会读取原始表、构造特征、生成弱监督标签、训练 scikit-learn 三分类模型，并写入：

- `hot_search_feature_stats`
- `hot_search_burst_predictions`

如果历史样本不足或类别不足，任务不会崩溃，会使用弱监督规则结果作为预测结果。

### 5.5 运行主题聚类分析

```powershell
python ml/topic_cluster.py
```

任务会使用 `jieba` 分词、`TF-IDF` 提取文本特征、`KMeans` 聚类，并写入：

- `hot_search_topic_clusters`

### 5.6 启动后端服务

新开一个终端，在项目根目录执行：

```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后可访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

### 5.7 启动前端页面

新开一个终端，在项目根目录执行：

```powershell
cd frontend
npm install
npm run dev
```

默认访问地址：

- `http://127.0.0.1:5173`

页面顶部可以切换：

- 首页大屏
- PySpark 分析
- 机器学习分析

## 6. 接口说明

第一期接口：

```http
GET /api/summary
GET /api/ranking/current
GET /api/trend?keyword=高考
```

第三期分析接口：

```http
GET /api/analysis/keywords/top?limit=20
GET /api/analysis/daily
POST /api/analysis/run
```

`POST /api/analysis/run` 会尝试在后端后台进程中触发 `python analysis/batch_job.py`，更推荐在命令行手动运行分析任务，方便查看 PySpark 日志。

第四期机器学习接口：

```http
GET /api/ml/burst/top?limit=20
GET /api/ml/burst/search?keyword=高考
GET /api/ml/topics
GET /api/ml/topics/summary
POST /api/ml/burst/run
POST /api/ml/topics/run
GET /api/export/ml_report.csv
GET /api/export/ml_report.xlsx
```

`POST /api/ml/burst/run` 会在后端后台触发 `python ml/predict_job.py`；`POST /api/ml/topics/run` 会触发 `python ml/topic_cluster.py`。命令行手动运行更适合查看完整日志。

## 7. 验证方式

### 7.1 验证采集是否成功

执行一次采集后，在 MySQL 中运行：

```sql
USE weibo_hot;
SELECT COUNT(*) AS total_records FROM hot_search_raw;
SELECT * FROM hot_search_raw ORDER BY id DESC LIMIT 10;
```

### 7.2 验证 PySpark 分析是否成功

运行分析任务后，在 MySQL 中执行：

```sql
SELECT * FROM hot_search_keyword_stats ORDER BY appear_count DESC LIMIT 10;
SELECT * FROM hot_search_daily_stats ORDER BY stat_date ASC;
```

### 7.3 验证机器学习分析是否成功

运行第四期任务后，在 MySQL 中执行：

```sql
SELECT * FROM hot_search_feature_stats ORDER BY current_hot_value DESC LIMIT 10;
SELECT * FROM hot_search_burst_predictions ORDER BY burst_probability DESC LIMIT 10;
SELECT * FROM hot_search_topic_clusters ORDER BY cluster_id ASC, hot_value DESC LIMIT 10;
```

### 7.4 验证后端接口

在 PowerShell 中执行：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/summary
Invoke-RestMethod http://127.0.0.1:8000/api/ranking/current
Invoke-RestMethod "http://127.0.0.1:8000/api/trend?keyword=高考"
Invoke-RestMethod "http://127.0.0.1:8000/api/analysis/keywords/top?limit=20"
Invoke-RestMethod http://127.0.0.1:8000/api/analysis/daily
Invoke-RestMethod "http://127.0.0.1:8000/api/ml/burst/top?limit=20"
Invoke-RestMethod "http://127.0.0.1:8000/api/ml/burst/search?keyword=高考"
Invoke-RestMethod http://127.0.0.1:8000/api/ml/topics
Invoke-RestMethod http://127.0.0.1:8000/api/ml/topics/summary
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/ml/burst/run
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/ml/topics/run
```

浏览器也可以直接访问：

- `http://127.0.0.1:8000/api/summary`
- `http://127.0.0.1:8000/api/ranking/current`
- `http://127.0.0.1:8000/api/analysis/keywords/top?limit=20`
- `http://127.0.0.1:8000/api/analysis/daily`
- `http://127.0.0.1:8000/api/ml/burst/top?limit=20`
- `http://127.0.0.1:8000/api/ml/topics`
- `http://127.0.0.1:8000/api/export/ml_report.csv`

### 7.5 验证前端页面

打开 `http://127.0.0.1:5173` 后，确认：

- 首页大屏展示统计概览、当前热搜榜、关键词趋势折线图。
- PySpark 分析页展示关键词 Top20 柱状图、每日采集统计折线图和明细表。
- 如果没有分析结果，页面提示“暂无分析数据，请先运行 PySpark 分析任务”。
- 机器学习分析页展示爆发趋势 Top20、爆发概率柱状图、趋势方向统计图、主题聚类分布图和主题聚类表格。
- 机器学习分析页可以点击“运行爆发趋势识别”“运行主题聚类分析”“导出 CSV 报告”“导出 Excel 报告”。

### 7.6 验证报告导出

浏览器访问：

- `http://127.0.0.1:8000/api/export/ml_report.csv`
- `http://127.0.0.1:8000/api/export/ml_report.xlsx`

CSV 报告包含多个 section；Excel 报告包含多 Sheet：

- 爆发趋势
- 主题聚类
- 关键词统计
- 每日统计
- 当前热搜榜

## 8. 常见问题

### PowerShell 执行 SQL 问题

PowerShell 不能直接使用 `<` 输入重定向，推荐使用：

```powershell
cmd /c "mysql -u root -p < sql\init.sql"
```

如果需要指定数据库，也可以使用：

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\init.sql"
cmd /c "mysql -u root -p weibo_hot < sql\v3_stats.sql"
```

### SSLEOFError 或网络异常

如果采集出现 SSLEOFError、ConnectionError、Timeout，程序会自动重试。

如果多次重试后仍然失败，可以尝试：

1. 检查网络是否能访问微博。
2. 配置 `WEIBO_COOKIE`。
3. 适当调大 `COLLECT_INTERVAL_SECONDS`。
4. 适当调大 `WEIBO_API_TIMEOUT`。
5. 稍后重新运行采集程序。

### 后端数据库连接失败

如果前端提示“数据库连接失败，请检查 MySQL 服务和 .env 配置”，请确认 MySQL 已启动，并检查 `.env` 中的 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`。

### JAVA_HOME is not set

PySpark 依赖 Java。请安装 JDK 8、11 或 17，并在系统环境变量中配置 `JAVA_HOME`，重新打开 PowerShell 后再运行：

```powershell
java -version
```

### ClassNotFoundException: com.mysql.cj.jdbc.Driver

说明 Spark 没有找到 MySQL Connector/J。请下载 Connector/J Jar，并在 `.env` 中配置：

```env
SPARK_MYSQL_JAR=C:/drivers/mysql-connector-j-8.4.0.jar
```

### Access denied for user

说明 MySQL 用户名、密码或权限不正确。请检查 `.env` 中的 `MYSQL_USER`、`MYSQL_PASSWORD`，并确认该用户可以访问 `MYSQL_DATABASE`。

### Table hot_search_keyword_stats doesn't exist

说明第三期统计表没有创建，请执行：

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\v3_stats.sql"
```

### Table hot_search_feature_stats doesn't exist

说明第四期机器学习结果表没有创建，请执行：

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\v4_ml_analysis.sql"
```

### Table hot_search_burst_predictions doesn't exist

说明第四期爆发趋势预测表没有创建，请执行 `sql/v4_ml_analysis.sql`。

### Table hot_search_topic_clusters doesn't exist

说明第四期主题聚类结果表没有创建，请执行 `sql/v4_ml_analysis.sql`。

### 历史数据不足，无法训练模型

第四期会先使用弱监督规则生成标签。如果样本量太少或类别不足，控制台会提示“样本不足或类别不足，使用规则结果作为预测结果”。这不是程序错误，可以继续采集更多批次后重新运行：

```powershell
python ml/predict_job.py
```

### scikit-learn、jieba 或 openpyxl 未安装

请安装第四期机器学习依赖：

```powershell
cd ml
pip install -r requirements.txt
cd ..
```

后端如果需要触发任务或导出 Excel，也请安装后端依赖：

```powershell
cd backend
pip install -r requirements.txt
cd ..
```

### 中文分词结果为空或聚类样本数量不足

请确认 `hot_search_raw` 中有足够多的非空中文标题。样本太少时主题聚类任务会提示“可聚类标题数量不足，跳过主题聚类”，不会中断整个项目。

### ml/predict_job.py 模块导入失败

推荐在项目根目录运行：

```powershell
python ml/predict_job.py
python ml/topic_cluster.py
```

脚本内部会把项目根目录加入 `sys.path`，用于兼容本地运行。

### fetch_time 日期格式转换失败

分析任务会过滤无法转换为日期的 `fetch_time` 数据，并在控制台打印提示。正常采集写入的 `DATETIME` 字段不会出现该问题。

### analysis/batch_job.py 模块导入失败

推荐在项目根目录运行：

```powershell
python analysis/batch_job.py
```

不要直接进入子目录后用不完整路径启动。脚本内部也会把项目根目录加入 `sys.path`，用于兼容本地运行。

## 9. 模块说明

### collector

- 使用 `requests` 拉取微博热搜接口。
- 网络异常时按 `WEIBO_API_RETRY_TIMES` 和 `WEIBO_API_RETRY_DELAY_SECONDS` 自动重试。
- 将热搜记录写入 MySQL 原始表 `hot_search_raw`。

### analysis

- 使用 PySpark JDBC 读取 `hot_search_raw`。
- 生成关键词统计：出现次数、最高热度、平均热度、最佳排名、最近采集时间。
- 生成每日统计：总记录数、关键词数、平均热度、最大热度、最高排名。
- 先 `TRUNCATE` 第三期统计表，再用 Spark JDBC `append` 写入，避免 `overwrite` 重建表。

### ml

- 使用 pandas / pymysql 读取 `hot_search_raw`。
- `feature_builder.py` 构造当前排名、当前热度、出现次数、最高热度、平均热度、热度变化率、排名变化、持续时间、标题长度、是否含数字、是否含话题标签、采集小时等特征。
- `label_builder.py` 使用弱监督规则构造 `burst_level`：`2` 为爆发型，`1` 为稳定型，`0` 为降温型；同时生成 `trend_direction`。
- `train_model.py` 使用 scikit-learn 的 GradientBoostingClassifier 训练三分类模型，样本不足时自动回退到规则结果。
- `topic_cluster.py` 使用 jieba 分词、TF-IDF 和 KMeans 对热搜标题进行主题聚类，并根据关键词规则生成娱乐热点、教育考试、科技财经、体育赛事、社会事件、综合热点等主题名。
- `report_exporter.py` 支持 CSV 和 Excel 报告导出，部分统计表不存在时会在报告中写入中文提示。

### backend

- 使用 FastAPI 提供 `/api/summary`、`/api/ranking/current`、`/api/trend`。
- 第三期新增 `/api/analysis/keywords/top`、`/api/analysis/daily`。
- 第四期新增 `/api/ml/burst/top`、`/api/ml/burst/search`、`/api/ml/topics`、`/api/ml/topics/summary` 和 `/api/export/ml_report.csv`。
- 数据库连接或查询异常时返回中文错误提示。

### frontend

- 使用 Vue3 + Vite 构建单页看板。
- 首页大屏使用 ECharts 展示关键词趋势折线图。
- PySpark 分析页展示关键词 Top20 柱状图和每日统计折线图。
- 机器学习分析页展示爆发趋势表格、爆发概率柱状图、趋势方向统计图、主题聚类分布图、主题聚类明细表和报告导出按钮。
