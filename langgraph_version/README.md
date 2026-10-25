# LangGraph + uv 版本说明

本目录是"人群圈选 Agent"的 LangGraph 图编排实现，与项目根目录的轻量版（手写 for 循环）功能等价，
用来对比"手写编排"和"框架编排"的差别。

## 一、uv 是什么，为什么要用它

uv 是 Python 的包管理器和虚拟环境工具，替代 `pip` + `venv` + `requirements.txt` 三件套：

| 传统做法 | uv 做法 | 好处 |
|---|---|---|
| `python -m venv .venv` | `uv venv` | 建环境更快 |
| 手写 requirements.txt | `uv add langgraph` | 自动写进 pyproject.toml 并解析版本 |
| `pip install -r ...` | `uv sync` | 按 uv.lock 精确复现，装出来完全一致 |
| `python xxx.py` | `uv run xxx.py` | 自动切进虚拟环境，不污染系统 Python |

### 安装 uv（Windows）

```bash
# 方式一：官方脚本（PowerShell）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# 方式二：用 pip 装
pip install uv
```

### 用 uv 初始化本项目

```bash
cd audience-agent-eval/langgraph_version

uv venv                      # 创建 .venv
uv add langgraph             # 加依赖，自动写进 pyproject.toml
uv add pandas matplotlib
uv lock                      # 生成 uv.lock，锁定精确版本
uv sync                      # 按 lock 文件同步环境

uv run graph_flow.py         # 运行，自动使用 .venv 里的解释器
```

国内网络慢的话加镜像：

```bash
uv add langgraph --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 二、LangGraph 的核心概念（对照本项目代码）

| 概念 | 在 graph_flow.py 里的位置 | 作用 |
|---|---|---|
| State（状态） | `class AgentState(TypedDict)` | 一个贯穿全图的字典，节点只读写它，不互相传参 |
| Node（节点） | `node_router` / `node_plan_sql` / `node_execute` / `node_self_heal` | 一个函数做一件事，返回要更新的字段 |
| Edge（普通边） | `g.add_edge("plan_sql", "execute")` | 固定顺序流转 |
| Conditional Edge（条件边） | `route_after_execute` | 按执行结果决定走自愈还是结束 |
| Loop（受控循环） | `self_heal → plan_sql → execute` | 自愈重试，靠 `retries < MAX_RETRY` 收口，不会死循环 |
| compile() | `build_graph()` | 编译成可调用对象，之后 `GRAPH.invoke({...})` 即一次完整运行 |

和轻量版的对照：

| 环节 | 轻量版写法 | LangGraph 写法 |
|---|---|---|
| 路由 | `router.classify()` 后写 if 分支 | 独立 node + 条件边 |
| SQL 生成 | for 循环里调函数 | node，靠状态里的 `error` 判断是首轮还是自愈轮 |
| 自愈重试 | `for attempt in range(MAX_RETRY+1)` | 条件边回到 `plan_sql`，循环次数写在状态里 |
| 可观测 | 自己 print | 接 LangSmith 后自动上报每个节点的输入输出 |

## 三、接 LangSmith 看链路轨迹（可选）

```bash
# Windows PowerShell
$env:LANGCHAIN_TRACING_V2="true"
$env:LANGCHAIN_API_KEY="你的 LangSmith key"
$env:LANGCHAIN_PROJECT="audience-agent"
uv run graph_flow.py
```

跑完去 LangSmith 后台就能看到每次调用的节点顺序、耗时、状态变化，出问题时定位到具体哪个节点。
不用 LangSmith 也不影响运行。

## 四、换成 LangChain 的 LLM 封装（可选）

当前默认用标准库 urllib 调 DeepSeek 兼容接口，零额外依赖。若想用 LangChain 生态：

```bash
uv add langchain-openai
```

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1",
                 api_key=os.environ["LLM_API_KEY"], temperature=0)
prompt = ChatPromptTemplate.from_messages([("user", "{q}")])
chain = prompt | llm          # LCEL 管道语法

# 在 node_plan_sql 里替换 llm_client.call_llm(prompt)：
sql = chain.invoke({"q": prompt_text}).content.strip()
```

## 五、什么时候该用框架，什么时候不必

- 链路只有三四个环节、分支简单：手写更轻，依赖更少，面试也更好讲清楚
- 环节多、需要人工介入（human-in-the-loop）、需要断点续跑、需要多 Agent 协作：
  LangGraph 的 checkpointer 和状态机优势才体现出来
- 建议的讲法：先讲手写版的设计取舍（Router 前置、自愈带上限），
  再说进阶版用 LangGraph 重写是为了拿到可观测性和可恢复执行
