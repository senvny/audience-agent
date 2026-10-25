# 人群圈选 Agent — 产品层（app/）

基于本项目的 LangGraph 评测框架搭建的可直接使用的 AI 产品：在浏览器里输入一句
自然语言（如「圈出近30天加购但未下单的高价值用户」），Agent 自动完成
意图路由 → DeepSeek 生成圈选 SQL → SQLite 执行（失败自愈重试 ≤2 次），
返回命中人数、生成 SQL、人群画像与名单，可导出 CSV、回看历史。

核心引擎（`agent/` + `langgraph_version/graph_flow.py` + `data/audience.db`）
零改动复用；本目录是纯新增的产品层，依赖方向单向：`app → langgraph_version/agent → data`。

## 一、配置方式（共 1 项必填）

| 环境变量 | 必填 | 说明 |
|---|---|---|
| `LLM_API_KEY` | 是（真实模式） | DeepSeek 密钥，[platform.deepseek.com](https://platform.deepseek.com) 创建。不配置则进入离线演示模式（仅支持评测用例回放与兜底话术，自由圈选会提示需要 Key） |
| `LLM_MODEL` | 否 | 默认 `deepseek-chat` |
| `LLM_BASE_URL` | 否 | 默认 `https://api.deepseek.com/v1` |

配置方式（Windows PowerShell，会话级）：

```powershell
$env:LLM_API_KEY = "sk-你的密钥"
```

## 二、部署与启动（三条命令）

```powershell
cd D:\Software\WkbRecord\2026-10-10-20-44-03\audience-agent-eval\langgraph_version
$env:LLM_API_KEY = "sk-你的密钥"
.venv\Scripts\python.exe ..\app\server.py
```

启动后浏览器打开 **http://127.0.0.1:8000**（页面顶部会显示「真实模式 · deepseek-chat」与库内用户数）。

依赖已装好（fastapi + uvicorn 已在 `.venv`，并补记进 `langgraph_version/pyproject.toml`）。
若在新环境重建：`pip install fastapi uvicorn langgraph` 后先跑 `python ../data/build_db.py` 生成业务库。

## 三、接口说明

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/` | 单页前端 |
| GET | `/api/status` | 运行模式 / 模型 / 库内用户数 |
| POST | `/api/select` | 核心闭环。请求体 `{"question": "自然语言需求"}`，返回人数、SQL、画像、名单预览（前 50 条）、重试次数、耗时 |
| GET | `/api/history` | 最近 50 条圈选摘要 |
| GET | `/api/history/{id}` | 单条历史详情（含完整名单与画像） |
| GET | `/api/export/{id}` | 导出该次圈选完整名单 CSV（UTF-8 带 BOM，Excel 直开不乱码） |

交互流程：输入需求 → 结果卡（人数 / SQL 可折叠核对 / 自愈重试次数与耗时 /
四组画像条形图 / 名单预览）→ 导出 CSV；侧栏「圈选历史」点击任意记录回看完整结果。

## 四、数据流转与存储

```
POST /api/select
  → history.save() 占位                 [data/history.db，独立于业务库]
  → graph_flow.answer(question,"v3_rule")
      LangGraph: router ─ select → plan_sql(DeepSeek) → execute(SQLite user_tags)
                             ↑____ error & retries<2 ____|  （自愈循环）
                            └ chitchat → 兜底话术
  → profile.stats(user_ids)             [读 data/audience.db]
  → history.update() 回填结果
  → JSON → 前端渲染
```

- 业务库 `data/audience.db`：3000 用户标签宽表（`user_tags`，17 字段），由 `data/build_db.py` 生成，**本层只读不写**。
- 历史库 `data/history.db`：`records` 表（需求/SQL/名单 JSON/人数/重试/耗时），独立建库——
  业务库被 `build_db.py` 重建时历史不受影响。删除该文件即清空历史。
- 演示模式说明：未配 Key 时 router 仍可用（纯规则），圈选请求会先尝试匹配 32 条评测用例回放；
  匹配不上会明确提示需要真实 Key，而不是报错。

## 五、目录结构与模块职责

```
app/
├── server.py          # FastAPI 入口：只做 HTTP 协议层（路由/参数/JSON 组装）
├── history.py         # 圈选历史：独立 history.db 的存取
├── profile.py         # 人群画像：按性别/城市/会员/品类做分布统计（分批 IN 查询）
├── export.py          # CSV 导出：内存生成字节流，不落盘
└── static/index.html  # 单页前端：原生 JS fetch，无构建步骤
```

模块间互不引用，全部单向 import 引擎；引擎层（agent/、langgraph_version/）不感知本层。

## 六、常见问题

- **端口被占**：改 `server.py` 末尾 `uvicorn.run(..., port=8000)` 的端口。
- **想换模型**：设 `LLM_MODEL` 环境变量即可（任何 OpenAI 兼容接口都可，配合 `LLM_BASE_URL`）。
- **历史里有测试记录**：删除 `data/history.db` 后重启服务即自动重建空库。
- **评测回归**：产品层不影响评测——`cd langgraph_version && .venv/Scripts/python.exe graph_flow.py` 照常运行。
