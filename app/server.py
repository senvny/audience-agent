# -*- coding: utf-8 -*-
"""
人群圈选 Agent — Web 服务入口（FastAPI）。

职责边界：本文件只做「HTTP 协议层」——接收请求、调引擎/模块、组装 JSON 返回。
业务逻辑分布（高内聚低耦合，依赖单向：server → 模块 → 引擎）：
  - 圈选链路   → langgraph_version/graph_flow.py（LangGraph 图，32 条用例验证过的核心引擎）
  - 历史存取   → app/history.py（独立 data/history.db，防数据重建时被清）
  - 画像统计   → app/profile.py（读 data/audience.db）
  - 名单导出   → app/export.py（内存生成 CSV，不落盘）

启动方式（在 langgraph_version/ 目录下，复用已装依赖的 .venv）：
  .venv/Scripts/python.exe ../app/server.py
  浏览器打开 http://127.0.0.1:8000

完整交互流程（一次圈选的数据流转）：
  浏览器 → POST /api/select
        → history.save() 占位拿 record_id
        → graph_flow.answer() 跑 LangGraph（路由→DeepSeek生成SQL→执行→自愈重试≤2）
        → profile.stats() 出画像 → history.update() 回填结果
        → JSON 返回前端渲染
"""
import os
import sqlite3
import sys
import time

# 把项目根（audience-agent-eval/）加入 import 路径，
# 使本文件无论从哪里启动都能 import 到 agent / langgraph_version 包
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, APP_DIR)   # 让 import history/profile/export 命中 app/ 目录

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from langgraph_version.graph_flow import answer     # 核心引擎（LangGraph 图）
from agent import llm_client, router                # 读 MODE/MODEL；演示模式预路由
import history, profile, export as export_mod       # 产品三模块（互不引用）

app = FastAPI(title="人群圈选 Agent", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
BUSINESS_DB = os.path.join(ROOT, "data", "audience.db")


# ---------------- 请求模型 ----------------
class SelectReq(BaseModel):
    """POST /api/select 的请求体：一条自然语言圈选需求。"""
    question: str


# ---------------- 状态接口：前端顶部状态栏 ----------------
@app.get("/api/status")
def status():
    """返回运行模式（real=真实DeepSeek / mock=离线演示）、模型名、库规模。"""
    con = sqlite3.connect(BUSINESS_DB)
    total = con.execute("SELECT COUNT(*) FROM user_tags").fetchone()[0]
    con.close()
    return {"mode": llm_client.MODE, "model": llm_client.MODEL,
            "users": total, "base_url": llm_client.BASE_URL}


# ---------------- 演示模式保护 ----------------
def _match_case(question: str):
    """
    演示模式（未配 Key）下，mock 引擎需要一条评测用例的 gold_sql 作为模拟依据。
    产品场景用户自由输入没有现成 case，这里按文本相似度匹配 32 条评测用例：
    匹配得上就回放该用例（页面上仍能看懂整条链路），匹配不上就明确提示需要真实 Key。
    该逻辑只在 mock 模式生效，真实模式完全不受影响。
    """
    import difflib
    from eval.test_cases import CASES
    best, best_ratio = None, 0.0
    for c in CASES:
        ratio = difflib.SequenceMatcher(None, question, c["question"]).ratio()
        if ratio > best_ratio:
            best, best_ratio = c, ratio
    return best if best_ratio >= 0.55 else None


# ---------------- 核心闭环：自然语言圈选 ----------------
@app.post("/api/select")
def select(req: SelectReq):
    """
    完整跑一遍「需求 → SQL → 人群」并落历史。
    引擎层报错不抛 500，而是包装进正常 JSON 返回——
    产品化处理：失败原因（SQL 报错/重试耗尽）也是要展示给用户的结果。
    """
    q = req.question.strip()
    if not q:
        raise HTTPException(400, "需求不能为空")

    rid = history.save(q)                          # 1. 先落占位记录
    t0 = time.time()

    # 演示模式（未配 Key）特殊处理：router 是纯规则实现，不依赖 LLM，
    # 所以闲聊类先放行（answer 内部会返回兜底话术，不需要 case）；
    # 只有真实要生成 SQL 的圈选请求才需要匹配评测用例作为 mock 依据
    case = None
    if llm_client.MODE != "real" and router.classify(q) == "select":
        case = _match_case(q)
        if case is None:
            history.update(rid, "select", None, [], 0, 0)
            return {"record_id": rid, "intent": "select", "mode": "mock",
                    "reply": "当前为离线演示模式（未配置 LLM_API_KEY），自由圈选需真实模型支持。"
                             "请在启动前配置 DeepSeek Key，或在输入框使用评测用例原文回放。"}

    r = answer(q, version="v3_rule", case=case)    # 2. 引擎（评测最优 Prompt 版）
    elapsed = int((time.time() - t0) * 1000)

    intent = r.get("intent")
    user_ids = r.get("user_ids") or []
    history.update(rid, intent, r.get("sql"), user_ids,   # 3. 回填历史（兜底场景也留痕）
                   r.get("retries", 0), elapsed)

    # 4. 组装响应：兜底返回话术；圈选返回人数+SQL+画像+名单预览
    if intent != "select":
        return {"record_id": rid, "intent": intent,
                "reply": r.get("reply"), "mode": llm_client.MODE}

    return {
        "record_id": rid,
        "intent": intent,
        "sql": r.get("sql"),
        "count": len(user_ids),
        "sample": profile.sample(user_ids),        # 名单预览前 50 条
        "profile": profile.stats(user_ids),        # 四组分布统计
        "retries": r.get("retries", 0),
        "exec_ok": r.get("exec_ok", False),
        "error": r.get("error"),
        "elapsed_ms": elapsed,
        "mode": llm_client.MODE,
    }


# ---------------- 历史 ----------------
@app.get("/api/history")
def history_list():
    """历史列表（侧栏）：最近 50 条摘要，按时间倒序。"""
    return history.list_recent(50)


@app.get("/api/history/{rid}")
def history_detail(rid: int):
    """单条历史详情（回看完整结果，含全部名单与画像）。"""
    rec = history.get(rid)
    if rec is None:
        raise HTTPException(404, "记录不存在")
    rec["profile"] = profile.stats(rec["user_ids"])   # 回看与实时圈选展示口径一致
    return rec


# ---------------- 导出 ----------------
@app.get("/api/export/{rid}")
def export_csv(rid: int):
    """导出某次圈选的完整名单 CSV（带 BOM，Excel 直开中文不乱码）。"""
    rec = history.get(rid)
    if rec is None:
        raise HTTPException(404, "记录不存在")
    data = export_mod.export_csv(rec["user_ids"])
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="audience_{rid}.csv"'},
    )


# ---------------- 前端页面 ----------------
@app.get("/")
def index():
    """托管单页前端（app/static/index.html），无构建步骤直接返回。"""
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html; charset=utf-8")


if __name__ == "__main__":
    # 编程式启动：只监听本机，交付即用，无需额外命令行参数
    import uvicorn
    print(f"启动服务: http://127.0.0.1:8000  （模式: {llm_client.MODE}）")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
