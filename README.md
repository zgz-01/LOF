# LOF Premium Monitor — LOF 基金实时溢价率监控

基于 palmmicro.com（无敌哥）核心算法的 QDII/LOF 基金实时溢价率监控工具。

## 架构

```
┌─ 用户浏览器 ──────────────────────┐
│  Flask 网页 (Railway)              │
│  → 展示溢价排行 + 基金详情          │
└──────────────┬────────────────────┘
               │ HTTP API
┌──────────────▼────────────────────┐
│  数据API服务 (server.py)           │
│  → 定时抓数据 → 缓存 → 提供API     │
│  运行在本机 (OpenClaw 服务器)       │
└──────┬──────────────────┬─────────┘
       │                  │
       ▼                  ▼
┌──────────┐      ┌──────────────┐
│ 无敌哥网站 │      │ Yahoo Finance│
│ 抓净值/价格│      │ 抓指数/期货   │
└──────────┘      └──────────────┘
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Flask 网页应用 → 部署到 Railway |
| `server.py` | API 服务 → 运行在本机，定时刷数据 |
| `fetcher.py` | 数据抓取层（无敌哥网站 + Yahoo Finance）|
| `engine.py` | 核心计算引擎（移植自无敌哥PHP源码）|
| `config.py` | 基金配置（指数映射、仓位等）|
| `requirements.txt` | Python 依赖 |
| `Procfile` | Railway 启动配置 |
| `templates/` | 网页模板 |

## 部署

### 本机 API 服务
```bash
python3 server.py
# 启动在 http://0.0.0.0:8080
```

### Railway 网页
1. 把此目录推送到 GitHub
2. 在 Railway 中连接该仓库
3. 设置环境变量 `API_BASE_URL` = 本机API地址
4. Railway 自动部署

## 接口

| 路径 | 说明 |
|------|------|
| `GET /api/premium` | 溢价排行数据 |
| `GET /api/fund/<code>` | 单只基金详情 |
| `GET /api/status` | 服务状态 |
| `GET /api/refresh` | 手动刷新缓存 |

## 数据源

- 国内基金数据: palmmicro.com（无敌哥）
- 美股指数/期货: Yahoo Finance
- 汇率: 中国货币网（通过无敌哥中转）

## 免责声明

数据仅供参考，不构成投资建议。
