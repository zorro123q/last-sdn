# 微博热搜分析系统

这是一个适合毕业设计演示的最小可运行版本，完整链路为：

`Python 定时采集 -> MySQL -> FastAPI -> Vue3 + ECharts`

项目只保留最基础能力，不引入 Kafka、Redis、Spark、情感分析、LSTM、登录鉴权、WebSocket、多数据源切换等复杂功能。

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
├─ backend/
│  ├─ main.py
│  ├─ config.py
│  ├─ database.py
│  ├─ requirements.txt
│  ├─ routes/
│  │  ├─ ranking.py
│  │  ├─ trend.py
│  │  └─ summary.py
│  └─ services/
│     └─ mysql_service.py
├─ frontend/
│  ├─ index.html
│  ├─ package.json
│  ├─ vite.config.js
│  └─ src/
│     ├─ main.js
│     ├─ App.vue
│     ├─ api/
│     │  └─ index.js
│     └─ views/
│        └─ Dashboard.vue
└─ sql/
   └─ init.sql
```

## 2. 环境要求

- Python 3.10+
- MySQL 8.0+
- Node.js 18+
- npm 9+

## 3. 初始化步骤

### 3.1 创建数据库和表

在项目根目录执行：

```powershell
cmd /c "mysql -u root -p < sql\init.sql"
```
### 3.2创建conda环境然后安装相关的包
```powershell
conda create -n sdn python=3.11
conda activate sdn
pip install -r collector\requirements.txt
pip install -r backend\requirements.txt
```
### 3.3安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

## 4. 启动方式

### 4.1 启动采集程序

进入 `collector` 目录后运行：

```powershell
cd collector
修改collector\config.py文件的这个数据库密码:mysql_password=os.getenv("MYSQL_PASSWORD", "123456")
python app.py
```
默认每 `300` 秒采集一次。
如果你只想测试一次采集，可以在当前 PowerShell 会话中临时设置：
```powershell
$env:COLLECT_RUN_ONCE="true"
python app.py
```

如果接口访问受限，可在 `.env` 中补充：

- `WEIBO_COOKIE`
- 或修改 `WEIBO_API_URL`

### 4.2 启动后端服务

新开一个终端，在项目根目录执行：

```powershell
cd backend
修改backend\config.py文件的这个数据库密码:mysql_password=os.getenv("MYSQL_PASSWORD", "123456")
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动成功后可访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

### 4.3 启动前端页面

新开一个终端，在项目根目录执行：

```powershell
cd frontend
npm run dev
```

默认访问地址：

- `http://127.0.0.1:5173`

## 5. 接口说明

### 5.1 获取当前热搜榜

```http
GET /api/ranking/current
```

返回数据库中最新一次采集的榜单数据。

### 5.2 获取关键词趋势

```http
GET /api/trend?keyword=高考
```

返回关键词的历史热度趋势数据。

### 5.3 获取统计概览

```http
GET /api/summary
```

返回总记录数、总批次、关键词数量、最新采集时间等信息。

## 6. 验证方式

### 6.1 验证采集是否成功

执行一次采集后，在 MySQL 中运行：

```sql
USE weibo_hot;
SELECT COUNT(*) AS total_records FROM hot_search_raw;
SELECT * FROM hot_search_raw ORDER BY id DESC LIMIT 10;
```

如果能看到最新插入的 `title`、`rank_num`、`hot_value`、`source`、`fetch_time`，说明采集与入库正常。

### 6.2 验证后端接口

在 PowerShell 中执行：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/summary
Invoke-RestMethod http://127.0.0.1:8000/api/ranking/current
Invoke-RestMethod "http://127.0.0.1:8000/api/trend?keyword=高考"
```

如果能返回 JSON，说明后端查询接口正常。

### 6.3 验证前端页面

打开 `http://127.0.0.1:5173` 后，确认以下内容能正常显示：

- 页面标题
- 统计概览卡片
- 当前热搜榜列表
- 关键词查询框
- 折线图

## 7. 模块说明

### 7.1 collector

- 使用 `requests` 拉取微博热搜接口
- 兼容 `data/list/title/word/hot/hot_value` 等常见字段
- 将热搜记录直接写入 MySQL
- 支持按环境变量设置采集间隔

### 7.2 backend

- 使用 FastAPI 提供排行榜、趋势、概览接口
- 开启 CORS，方便前端本地联调
- 所有查询逻辑统一放在 `services/mysql_service.py`

### 7.3 frontend

- 使用 Vue3 + Vite 构建单页看板
- 使用 ECharts 展示关键词趋势折线图

