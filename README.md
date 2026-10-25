# 电商人群圈选 Agent 效果评测与 Prompt 优化

模拟字节 JD 中的「人群圈选 Agent」：输入自然语言业务需求 → 自动生成 SQL → 输出目标人群包；
并建立一套**客观可复现**的评测体系（参考 SQL 作为标准答案，集合比对计算 P/R/F1），
通过 3 版 Prompt 对照实验量化 Prompt 工程的收益，完成 Bad case 归因与 Prompt 迭代闭环。

## 一、环境搭建（从零开始）

1. 安装 Python 3.10+（推荐 3.12/3.14）
2. 安装依赖（仅两个第三方库）：
   ```bash
   pip install pandas matplotlib
   ```
3. （可选，真实 LLM 模式）配置环境变量：
   ```bash
   # Windows PowerShell
   $env:LLM_API_KEY="你的DeepSeek密钥"
   $env:LLM_BASE_URL="https://api.deepseek.com/v1"   # 默认值，可省略
   $env:LLM_MODEL="deepseek-chat"                    # 默认值，可省略
   # Git Bash
   export LLM_API_KEY="你的DeepSeek密钥"
   ```
   不配置则自动进入**离线演示模式**：用内置版本质量画像模拟 Agent 输出，
   评测链路、指标口径与真实模式完全一致，适合先跑通流程。

## 二、运行步骤（按顺序执行，均在项目根目录下）

```bash
# 1. 生成数据：3000 用户的电商标签宽表 → data/audience.db
python data/build_db.py

# 2. 全量评测：3 版 Prompt × 32 条用例 → output/*.csv + charts/*.png
python eval/run_eval.py

# 3. 生成单文件 HTML 评测报告 → report.html（双击即可打开）
python analysis/make_report.py
```

## 三、项目结构

```
audience-agent-eval/
├── data/build_db.py      # 数据层：生成 user_tags 标签宽表（SQLite）
├── agent/
│   ├── router.py         # 意图路由：圈选 vs 兜底闲聊（Router 前置，防幻觉）
│   ├── prompts.py        # 3 版 Prompt + 业务口径词典（对照实验对象）
│   ├── llm_client.py     # LLM 调用：真实 API（urllib 零依赖）/ 离线演示双模式
│   └── sql_agent.py      # 核心链路：生成→执行→自愈重试（上限 2 次）
├── eval/
│   ├── test_cases.py     # 32 条分层测试用例（含参考 SQL 标准答案）
│   ├── metrics.py        # P/R/F1 集合比对 + Bad case 归因规则
│   └── run_eval.py       # 评测主程序（输出 CSV + 图表）
├── analysis/make_report.py  # 单文件离线 HTML 报告
├── output/               # eval_results / summary / by_level / bad_cases
├── charts/               # 三张评测图
├── langgraph_version/    # LangGraph 图编排版本（含 uv 用法说明，见其 README.md）
│   ├── graph_flow.py     # 路由 / 生成 / 执行 / 自愈 四个节点 + 条件边
│   ├── pyproject.toml    # uv 依赖声明
│   └── README.md         # uv 工作流 + LangGraph 概念对照表
└── report.html           # 最终评测报告
```

## 四、两套编排版本

| | 轻量版（根目录） | LangGraph 版（langgraph_version/） |
|---|---|---|
| 编排方式 | 手写 for 循环加 if 分支 | StateGraph 状态机，条件边控制自愈 |
| 依赖 | 仅 pandas、matplotlib | 加 langgraph、langchain-core |
| 适用 | 环节少、分支简单、依赖越少越好 | 环节多、需要可观测性、需要断点续跑 |

两版通过率一致（v1 基础版 17/30，v3 规则约束版 29/30），接口也保持一致，
可以互相替换。LangGraph 版的用法见 `langgraph_version/README.md`。

## 四之补充、LangGraph 版运行方式（用 uv）

```bash
cd langgraph_version
uv venv && uv add langgraph pandas matplotlib && uv lock
uv run graph_flow.py
```

没有 uv 时用普通 venv 也能跑：

```bash
cd ..
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt langgraph
.venv/Scripts/python langgraph_version/graph_flow.py
```

## 四、部署 / 分享

- **本地预览报告**：直接双击 `report.html`（单文件、图表已内嵌 base64，离线可开）
- **局域网分享**：项目根目录执行 `python -m http.server 8000`，浏览器访问 `http://localhost:8000/report.html`
- **公网分享**：把 `report.html` 传到 GitHub 仓库并开启 GitHub Pages，
  或用任意静态托管（Vercel/Netlify/Gitee Pages）—— 无需后端

## 四之二、Web 产品层（可直接用的 Agent 界面）

`app/` 是在上面这套评测引擎之上加的一层产品壳：浏览器里输入一句人话，出人群包数字、可折叠 SQL、画像分布、名单表和 CSV 导出，右侧是历史记录。

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt fastapi "uvicorn[standard]" langgraph

# 配置密钥（不配也能起，但只支持评测用例回放）
export LLM_API_KEY="你的DeepSeek密钥"

.venv/Scripts/python app/server.py
# 浏览器打开 http://127.0.0.1:8000
```

模块分工：

| 路径 | 职责 |
|---|---|
| `app/server.py` | HTTP 协议层，只做参数校验与编排，不含业务逻辑 |
| `app/profile.py` | 人群画像统计（分批 IN 查询，避免 SQLite 变量上限） |
| `app/export.py` | CSV 导出，UTF-8 BOM 保证 Excel 打开不乱码 |
| `app/history.py` | 独立的 `history.db`，与业务库分离，重建数据不丢历史 |
| `app/static/index.html` | 单页前端，原生 JS，无需 Node 构建 |

依赖方向是单向的：`app → langgraph_version / agent → data`，引擎层零改动。

## 四之三、作品与文档

| 文件 | 说明 |
|---|---|
| `pm_portfolio.html` / `pm_portfolio.pdf` | 产品经理视角作品集（背景、问题定义、架构、功能点、流程、原型、效果） |
| `人群圈选Agent作品集.docx` | 同内容的 Word 版，便于投递 |
| `report.html` | 评测报告，图表已内嵌 base64，离线可开 |
| `app/README.md` | 产品层的配置项、接口表和排查手册 |

## 五、面试要点速记

- **评测科学性**：Ground Truth 是参考 SQL 跑出的标准人群包，指标全自动、无人工打分
- **分层通过率**比总准确率更有洞察力：定位到"歧义口径"是词典注入解决不了的短板
- **Router 前置 vs ReAct**：模式化任务用路由更可控；**自愈重试**带上限防死循环
- **单表注入 Schema vs RAG**：上千张表才需要向量检索，小场景全文注入性价比更高
- 离线演示模式的数字仅验证链路；接真实 LLM 重跑后，简历数字以真实结果为准
