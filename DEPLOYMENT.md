# 微博热搜数据分析系统 - 部署说明文档

> 本文档为微博热搜数据分析系统的完整部署指南，包含本地开发环境部署和配置说明。
> 
> **版本**：v5.0（含情感分析与语义聚类增强功能）  
> **最后更新**：2026-04-25

---

## 📋 目录

1. [系统要求](#1-系统要求)
2. [环境准备清单](#2-环境准备清单)
3. [快速部署（推荐）](#3-快速部署推荐)
4. [详细安装步骤](#4-详细安装步骤)
5. [配置说明](#5-配置说明)
6. [启动方式](#6-启动方式)
7. [验证部署](#7-验证部署)
8. [常见问题](#8-常见问题)
9. [项目架构](#9-项目架构)

---

## 1. 系统要求

### 1.1 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 双核 | 四核及以上 |
| 内存 | 4GB | 8GB 及以上 |
| 硬盘 | 10GB 可用空间 | 20GB 及以上 |
| 网络 | 正常网络访问 | 稳定的网络连接 |

### 1.2 软件要求

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.10+ | 后端分析脚本 |
| MySQL | 8.0+ | 数据存储 |
| Node.js | 18+ | 前端构建 |
| npm | 9+ | 前端依赖管理 |
| JDK | 8/11/17 任一 | PySpark 运行必需 |
| conda | 最新版 | Python 环境管理（推荐） |

### 1.3 网络要求

- 能够正常访问微博热搜 API：`https://weibo.com/ajax/side/hotSearch`
- 能够访问 PyPI 下载 Python 包
- 能够访问 HuggingFace 下载语义模型（可选）

---

## 2. 环境准备清单

部署前请确认以下软件已安装：

### 2.1 检查软件是否已安装

```powershell
# 检查 Python 版本
python --version

# 检查 Node.js 版本
node --version

# 检查 npm 版本
npm --version

# 检查 MySQL 版本
mysql --version

# 检查 Java 版本
java -version
```

### 2.2 安装清单

- [ ] **Python 3.10+**：[https://www.python.org/downloads/](https://www.python.org/downloads/)
- [ ] **MySQL 8.0+**：[https://dev.mysql.com/downloads/mysql/](https://dev.mysql.com/downloads/mysql/)
- [ ] **Node.js 18+**：[https://nodejs.org/](https://nodejs.org/)
- [ ] **JDK 11**：[https://adoptium.net/](https://adoptium.net/)（推荐 Eclipse Temurin）
- [ ] **conda**：[https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)（可选但推荐）

---

## 3. 快速部署（推荐）

如果你是首次部署，按照以下顺序执行命令即可完成全部安装。

### 3.1 第一步：克隆项目

```powershell
cd your-projects-folder
# 如果还没有项目，克隆仓库
# git clone <repository-url>
cd weibo-hot-project
```

### 3.2 第二步：创建配置文件

```powershell
# 在项目根目录执行，复制示例配置
Copy-Item .env.example .env
```

### 3.3 第三步：修改数据库配置

编辑 `.env` 文件，修改以下配置：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DATABASE=weibo_hot
```

### 3.4 第四步：创建数据库和表

```powershell
# 创建数据库和原始表
cmd /c "mysql -u root -p < sql\init.sql"

# 创建第三期统计表
cmd /c "mysql -u root -p weibo_hot < sql\v3_stats.sql"

# 创建第四期机器学习表
cmd /c "mysql -u root -p weibo_hot < sql\v4_ml_analysis.sql"

# 创建第五期情感语义表
cmd /c "mysql -u root -p weibo_hot < sql\v5_sentiment_semantic.sql"
```

### 3.5 第五步：安装 Python 依赖

```powershell
# 创建 conda 环境（推荐）
conda create -n weibo_hot python=3.11
conda activate weibo_hot

# 安装所有 Python 依赖
pip install -r collector\requirements.txt
pip install -r backend\requirements.txt
pip install -r analysis\requirements.txt
pip install -r ml\requirements.txt
pip install -r sentiment\requirements.txt
pip install -r semantic\requirements.txt
```

### 3.6 第六步：安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 3.7 第七步：启动服务

**终端 1 - 启动后端服务：**
```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**终端 2 - 启动前端开发服务器：**
```powershell
cd frontend
npm run dev
```

### 3.8 第八步：访问系统

- **前端页面**：http://127.0.0.1:5173
- **后端 API 文档**：http://127.0.0.1:8000/docs

---

## 4. 详细安装步骤

### 4.1 数据库配置

#### 4.1.1 创建数据库

```sql
-- 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE IF NOT EXISTS weibo_hot DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE weibo_hot;

-- 验证
SHOW TABLES;
```

#### 4.1.2 创建数据库表

| SQL 文件 | 说明 | 执行命令 |
|----------|------|----------|
| `sql/init.sql` | 原始数据表 | `cmd /c "mysql -u root -p weibo_hot < sql\init.sql"` |
| `sql/v3_stats.sql` | PySpark 统计表 | `cmd /c "mysql -u root -p weibo_hot < sql\v3_stats.sql"` |
| `sql/v4_ml_analysis.sql` | 机器学习结果表 | `cmd /c "mysql -u root -p weibo_hot < sql\v4_ml_analysis.sql"` |
| `sql/v5_sentiment_semantic.sql` | 情感语义表 | `cmd /c "mysql -u root -p weibo_hot < sql\v5_sentiment_semantic.sql"` |

#### 4.1.3 数据库表结构说明

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| `hot_search_raw` | 热搜原始数据 | id, keyword, hot_value, rank, fetch_time, is_hot |
| `hot_search_keyword_stats` | 关键词统计 | keyword, appear_count, max_hot, avg_hot, best_rank |
| `hot_search_daily_stats` | 每日统计 | stat_date, total_count, keyword_count, avg_hot |
| `hot_search_feature_stats` | 特征工程结果 | keyword, current_hot, appear_count, hot_growth_rate |
| `hot_search_burst_predictions` | 爆发趋势预测 | keyword, burst_probability, burst_level, trend_direction |
| `hot_search_topic_clusters` | TF-IDF 主题聚类 | keyword, cluster_id, cluster_name, hot_value |
| `hot_search_sentiment_stats` | 情感分析结果 | keyword, sentiment_score, sentiment_label, fetch_time |
| `hot_search_sentiment_daily_stats` | 每日情感统计 | stat_date, avg_score, positive_count, negative_count |
| `hot_search_semantic_clusters` | 语义聚类结果 | keyword, cluster_id, cluster_name, embedding_vector |

### 4.2 Python 环境配置

#### 4.2.1 使用 conda 管理环境（推荐）

```powershell
# 创建新环境
conda create -n weibo_hot python=3.11

# 激活环境
conda activate weibo_hot

# 安装基础依赖
pip install requests PyMySQL python-dotenv

# 安装后端依赖
pip install fastapi uvicorn pandas scikit-learn jieba joblib openpyxl snownlp sentence-transformers

# 安装 PySpark 依赖
pip install pyspark
```

#### 4.2.2 PySpark JDBC 配置（如使用第三期功能）

1. 下载 MySQL Connector/J：
   - 下载地址：https://dev.mysql.com/downloads/connector/j/
   - 选择 Platform Independent 版本

2. 放置 JAR 文件到合适位置：
   ```
   C:/drivers/mysql-connector-j-8.4.0.jar
   ```

3. 在 `.env` 中配置路径：
   ```env
   SPARK_MYSQL_JAR=C:/drivers/mysql-connector-j-8.4.0.jar
   ```

### 4.3 前端配置

#### 4.3.1 安装 Node.js 依赖

```powershell
cd frontend
npm install
```

#### 4.3.2 修改 API 地址（如需要）

如果后端不在本机运行，修改 `frontend/.env`：

```env
VITE_API_BASE_URL=http://后端服务器IP:8000
```

### 4.4 环境变量配置

完整 `.env` 配置示例：

```env
# ===========================================
# MySQL 数据库配置
# ===========================================
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=weibo_hot
MYSQL_CHARSET=utf8mb4

# ===========================================
# 微博热搜采集配置
# ===========================================
WEIBO_API_URL=https://weibo.com/ajax/side/hotSearch
WEIBO_API_TIMEOUT=10
WEIBO_API_SOURCE=weibo
WEIBO_COOKIE=
WEIBO_API_RETRY_TIMES=3
WEIBO_API_RETRY_DELAY_SECONDS=2
COLLECT_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
COLLECT_INTERVAL_SECONDS=60
COLLECT_RUN_ONCE=false

# ===========================================
# FastAPI 后端服务配置
# ===========================================
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

# ===========================================
# 前端接口配置
# ===========================================
VITE_API_BASE_URL=http://127.0.0.1:8000

# ===========================================
# PySpark 分析配置（第三期）
# ===========================================
SPARK_APP_NAME=WeiboHotAnalysisJob
SPARK_MASTER=local[*]
SPARK_MYSQL_DRIVER=com.mysql.cj.jdbc.Driver
SPARK_MYSQL_JAR=C:/drivers/mysql-connector-j-8.4.0.jar

# ===========================================
# 机器学习配置（第四期）
# ===========================================
ML_MIN_HISTORY_COUNT=3
ML_RECENT_WINDOW=5
ML_BURST_HOT_GROWTH_THRESHOLD=0.3
ML_BURST_TOP_RANK_THRESHOLD=10
ML_MODEL_NAME=sklearn_gradient_boosting
ML_CLUSTER_COUNT=6
ML_TOP_LIMIT=100
ML_MODEL_DIR=ml/model_store

# ===========================================
# 情感分析配置（第五期）
# ===========================================
SENTIMENT_METHOD=snownlp
SENTIMENT_POSITIVE_THRESHOLD=0.6
SENTIMENT_NEGATIVE_THRESHOLD=0.4
SENTIMENT_TOP_LIMIT=100

# ===========================================
# 语义聚类配置（第五期）
# ===========================================
SEMANTIC_EMBEDDING_METHOD=sentence_transformers
SEMANTIC_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
SEMANTIC_LOCAL_MODEL_PATH=
SEMANTIC_CLUSTER_COUNT=6
SEMANTIC_TOP_LIMIT=500
SEMANTIC_FALLBACK_TO_TFIDF=true
```

---

## 5. 配置说明

### 5.1 采集配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `COLLECT_INTERVAL_SECONDS` | 60 | 采集间隔（秒），建议 60-120 |
| `WEIBO_API_TIMEOUT` | 10 | API 超时时间（秒） |
| `WEIBO_API_RETRY_TIMES` | 3 | 失败重试次数 |
| `WEIBO_COOKIE` | 空 | 微博 Cookie（可选） |

### 5.2 机器学习配置（第四期）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ML_MIN_HISTORY_COUNT` | 3 | 最小历史出现次数 |
| `ML_RECENT_WINDOW` | 5 | 窗口大小 |
| `ML_BURST_HOT_GROWTH_THRESHOLD` | 0.3 | 爆发增长率阈值 |
| `ML_CLUSTER_COUNT` | 6 | 主题聚类数量 |

### 5.3 情感分析配置（第五期）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SENTIMENT_POSITIVE_THRESHOLD` | 0.6 | 正向情感阈值 |
| `SENTIMENT_NEGATIVE_THRESHOLD` | 0.4 | 负向情感阈值 |
| `SENTIMENT_TOP_LIMIT` | 100 | 最大分析条数 |

### 5.4 语义聚类配置（第五期）

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SEMANTIC_MODEL_NAME` | paraphrase-multilingual-MiniLM-L12-v2 | 语义向量模型 |
| `SEMANTIC_LOCAL_MODEL_PATH` | 空 | 本地模型路径（可选） |
| `SEMANTIC_CLUSTER_COUNT` | 6 | 聚类数量 |
| `SEMANTIC_FALLBACK_TO_TFIDF` | true | 是否允许 TF-IDF 回退 |

---

## 6. 启动方式

### 6.1 启动顺序

```
1. MySQL 服务（确保运行中）
2. 后端服务（FastAPI）
3. 前端服务（Vue 开发服务器）
4. 数据采集器（可选，常驻运行）
5. 分析任务（按需手动运行）
```

### 6.2 启动后端服务

```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问地址：
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/

### 6.3 启动前端服务

```powershell
cd frontend
npm run dev
```

访问地址：http://127.0.0.1:5173

### 6.4 启动数据采集

**单次采集测试：**
```powershell
cd collector
$env:COLLECT_RUN_ONCE="true"
python app.py
```

**循环采集（后台运行）：**
```powershell
cd collector
$env:COLLECT_RUN_ONCE="false"
python app.py
```

### 6.5 运行分析任务

**PySpark 统计分析（第三期）：**
```powershell
python analysis/batch_job.py
```

**机器学习爆发趋势识别（第四期）：**
```powershell
python ml/predict_job.py
```

**TF-IDF 主题聚类（第四期）：**
```powershell
python ml/topic_cluster.py
```

**情感分析（第五期）：**
```powershell
python sentiment/sentiment_job.py
```

**语义聚类（第五期）：**
```powershell
python semantic/semantic_cluster_job.py
```

---

## 7. 验证部署

### 7.1 验证数据库连接

```sql
USE weibo_hot;
SELECT COUNT(*) AS total FROM hot_search_raw;
SELECT COUNT(*) AS total FROM hot_search_keyword_stats;
SELECT COUNT(*) AS total FROM hot_search_sentiment_stats;
```

### 7.2 验证后端 API

```powershell
# 验证基础接口
Invoke-RestMethod http://127.0.0.1:8000/api/summary
Invoke-RestMethod http://127.0.0.1:8000/api/ranking/current

# 验证分析接口
Invoke-RestMethod "http://127.0.0.1:8000/api/analysis/keywords/top?limit=20"

# 验证情感接口
Invoke-RestMethod http://127.0.0.1:8000/api/sentiment/summary

# 验证语义接口
Invoke-RestMethod http://127.0.0.1:8000/api/semantic/clusters
```

### 7.3 验证前端页面

| 页面 | 路由 | 验证内容 |
|------|------|----------|
| 首页大屏 | `/dashboard` | 热搜榜、统计卡片、趋势图 |
| PySpark 分析 | `/analysis` | 关键词统计、每日趋势 |
| 机器学习 | `/burst` | 爆发趋势、主题聚类 |
| 情感分析 | `/sentiment` | 情感分布、情绪指数 |
| 情感语义 | `/sentiment-analysis` | 情感+语义综合分析 |
| 大屏模式 | `/bigscreen` | 全屏可视化 |

### 7.4 验证报告导出

```powershell
# 导出 CSV 报告
Invoke-WebRequest "http://127.0.0.1:8000/api/export/enhanced_report.csv" -OutFile "report.csv"

# 导出 Excel 报告
Invoke-WebRequest "http://127.0.0.1:8000/api/export/enhanced_report.xlsx" -OutFile "report.xlsx"
```

---

## 8. 常见问题

### Q1: PowerShell 无法执行 SQL 文件？

**问题**：`mysql` 命令的 `<` 重定向在 PowerShell 中不工作

**解决方案**：使用 `cmd /c` 包装命令

```powershell
cmd /c "mysql -u root -p weibo_hot < sql\init.sql"
```

### Q2: 后端提示数据库连接失败？

**检查项**：
1. MySQL 服务是否运行：`services.msc` 查看 MySQL 服务状态
2. `.env` 配置是否正确
3. 用户权限是否足够

**解决方案**：
```powershell
# 测试 MySQL 连接
mysql -u root -p -h 127.0.0.1
```

### Q3: PySpark 提示 JAVA_HOME 未设置？

**解决方案**：

1. 下载安装 JDK 11：https://adoptium.net/

2. 设置系统环境变量：
   ```
   JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-11.0.x.x
   ```

3. 将 `JAVA_HOME\bin` 添加到 PATH

4. 重启终端后验证：
   ```powershell
   java -version
   ```

### Q4: PySpark 提示 ClassNotFoundException？

**问题**：找不到 MySQL JDBC Driver

**解决方案**：
1. 下载 MySQL Connector/J
2. 在 `.env` 中配置：`SPARK_MYSQL_JAR=C:/drivers/mysql-connector-j-8.4.0.jar`

### Q5: 语义聚类任务下载模型失败？

**问题**：sentence-transformers 首次运行需要下载模型

**解决方案**（三选一）：

1. **等待自动下载**：首次运行会自动下载模型到缓存目录

2. **配置本地模型路径**：
   ```env
   SEMANTIC_LOCAL_MODEL_PATH=C:/models/paraphrase-multilingual-MiniLM-L12-v2
   ```

3. **启用 TF-IDF 回退**（推荐）：
   ```env
   SEMANTIC_FALLBACK_TO_TFIDF=true
   ```

### Q6: 分析任务提示历史数据不足？

**问题**：机器学习任务需要一定量的历史数据

**解决方案**：
1. 增加采集数据量（建议至少 50 条以上）
2. 等待更多批次数据采集完成
3. 这是正常提示，不影响其他功能

### Q7: 前端页面空白或加载失败？

**检查项**：
1. 后端服务是否运行在 8000 端口
2. 浏览器控制台是否有错误
3. CORS 配置是否正确

**解决方案**：
```powershell
# 重启后端服务
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 重启前端服务
cd frontend
npm run dev
```

### Q8: 采集出现网络错误？

**问题**：SSLEOFError、ConnectionError、Timeout

**解决方案**：
1. 检查网络是否能访问微博
2. 增加 `COLLECT_INTERVAL_SECONDS`
3. 增加 `WEIBO_API_TIMEOUT`
4. 配置 `WEIBO_COOKIE`
5. 稍后重试

---

## 9. 项目架构

### 9.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户端                                   │
│                   ┌─────────────────────┐                       │
│                   │   Vue.js 前端       │                       │
│                   │   (端口 5173)       │                       │
│                   └──────────┬──────────┘                       │
└──────────────────────────────│──────────────────────────────────┘
                               │ HTTP API
┌──────────────────────────────│──────────────────────────────────┐
│                         服务端                                   │
│                   ┌──────────┴──────────┐                       │
│                   │   FastAPI 后端       │                       │
│                   │   (端口 8000)       │                       │
│                   └──────────┬──────────┘                       │
└──────────────────────────────│──────────────────────────────────┘
                               │ SQL
┌──────────────────────────────│──────────────────────────────────┐
│                         数据层                                   │
│                   ┌──────────┴──────────┐                       │
│                   │     MySQL 8.0       │                       │
│                   │   (端口 3306)       │                       │
│                   └────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                               ▲
                               │ 定时/手动触发
┌──────────────────────────────│──────────────────────────────────┐
│                      数据处理层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  数据采集器  │ │   PySpark   │ │   机器学习   │              │
│  │  collector  │ │  analysis   │ │     ml       │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐                                │
│  │  情感分析    │ │  语义聚类    │                                │
│  │  sentiment  │ │  semantic   │                                │
│  └─────────────┘ └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 数据流程图

```
微博热搜 API
      │
      ▼
┌─────────────┐
│  collector  │ ──── 定时采集 ────► hot_search_raw
│  (数据采集)  │          │
└─────────────┘          │
                        ▼
           ┌─────────────────────────┐
           │     MySQL 数据库          │
           └─────────────────────────┘
                        │
      ┌─────────────────┼─────────────────┐
      ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  analysis   │  │     ml      │  │  sentiment  │
│ (PySpark)   │  │ (机器学习)   │  │ (情感分析)   │
└─────────────┘  └─────────────┘  └─────────────┘
      │                 │                 │
      ▼                 ▼                 ▼
关键词统计        爆发趋势预测        情感分析结果
每日统计          主题聚类            语义聚类
      │                 │                 │
      └─────────────────┼─────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  FastAPI 后端    │
              │   分析接口层     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Vue.js 前端   │
              │   可视化展示     │
              └─────────────────┘
```

### 9.3 技术栈总结

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Vue 3 + Vite | SPA 单页应用 |
| **图表** | ECharts | 数据可视化 |
| **词云** | echarts-wordcloud | 关键词词云 |
| **地图** | GeoJSON + ECharts | 中国地图热力图 |
| **后端** | FastAPI | Python REST API 框架 |
| **数据库** | MySQL 8.0 | 关系型数据存储 |
| **数据采集** | requests | HTTP 请求库 |
| **离线分析** | PySpark | 大数据批处理 |
| **机器学习** | scikit-learn | ML 特征工程与聚类 |
| **情感分析** | SnowNLP | 中文情感分析 |
| **语义向量** | sentence-transformers | 多语言语义嵌入 |

### 9.4 文件结构

```
weibo-hot-project/
│
├── .env.example              # 环境变量示例
├── README.md                 # 项目说明文档
│
├── collector/                # 数据采集模块
│   ├── app.py                # 采集主程序
│   ├── api_client.py         # API 客户端
│   ├── db_writer.py          # 数据库写入
│   ├── config.py             # 配置加载
│   └── requirements.txt      # 采集依赖
│
├── analysis/                 # PySpark 分析模块
│   ├── batch_job.py          # 分析主任务
│   ├── spark_session.py      # Spark 会话
│   ├── readers/              # 数据读取
│   ├── processors/           # 数据处理
│   ├── writers/              # 结果写入
│   └── requirements.txt      # 分析依赖
│
├── ml/                       # 机器学习模块
│   ├── predict_job.py        # 爆发趋势预测
│   ├── topic_cluster.py      # 主题聚类
│   ├── feature_builder.py    # 特征工程
│   ├── label_builder.py      # 标签构建
│   ├── train_model.py        # 模型训练
│   └── requirements.txt      # ML 依赖
│
├── sentiment/                # 情感分析模块
│   ├── sentiment_job.py      # 情感分析任务
│   ├── sentiment_analyzer.py # 分析核心
│   ├── data_loader.py        # 数据加载
│   ├── mysql_writer.py       # 结果写入
│   └── requirements.txt      # 情感依赖
│
├── semantic/                # 语义聚类模块
│   ├── semantic_cluster_job.py # 聚类任务
│   ├── embedding_cluster.py   # 嵌入聚类核心
│   ├── data_loader.py         # 数据加载
│   ├── mysql_writer.py        # 结果写入
│   ├── model_cache/           # 模型缓存
│   └── requirements.txt       # 语义依赖
│
├── backend/                  # FastAPI 后端
│   ├── main.py               # 应用入口
│   ├── config.py             # 后端配置
│   ├── database.py           # 数据库连接
│   ├── routes/               # API 路由
│   │   ├── analysis.py        # 分析接口
│   │   ├── ml_analysis.py     # ML 接口
│   │   ├── ranking.py         # 排行榜接口
│   │   ├── trend.py           # 趋势接口
│   │   ├── summary.py         # 汇总接口
│   │   └── sentiment_semantic.py # 情感语义接口
│   ├── services/             # 业务逻辑
│   │   ├── analysis_service.py
│   │   ├── ml_analysis_service.py
│   │   ├── mysql_service.py
│   │   └── sentiment_semantic_service.py
│   └── requirements.txt      # 后端依赖
│
├── frontend/                 # Vue.js 前端
│   ├── package.json          # 项目配置
│   ├── vite.config.js        # Vite 配置
│   └── src/
│       ├── main.js           # 应用入口
│       ├── App.vue           # 根组件
│       ├── api/
│       │   └── index.js      # API 调用
│       └── views/
│           ├── Dashboard.vue    # 首页
│           ├── Analysis.vue     # 分析页
│           ├── BurstAnalysis.vue # ML分析页
│           ├── SentimentMap.vue  # 情感地图
│           ├── SentimentAnalysis.vue # 情感语义页
│           └── BigScreen.vue    # 大屏模式
│
└── sql/                      # 数据库脚本
    ├── init.sql              # 初始化表
    ├── v3_stats.sql          # 第三期统计表
    ├── v4_ml_analysis.sql    # 第四期ML表
    └── v5_sentiment_semantic.sql # 第五期情感语义表
```

---

## 📞 技术支持

如遇到问题，请按以下顺序排查：

1. 查看本文档 [常见问题](#8-常见问题) 部分
2. 查看项目 [README.md](README.md) 中的 FAQ
3. 查看后端日志输出
4. 查看浏览器控制台错误信息
5. 检查数据库表是否正确创建

---

**祝部署顺利！** 🎉
