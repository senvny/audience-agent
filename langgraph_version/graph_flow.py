# -*- coding: utf-8 -*-
"""
LangGraph 版本：用图编排重写"人群圈选 Agent"链路。
对比轻量版（手写 for 循环 + if/else）的区别：
  1. 每个环节是一个 node（路由/生成/执行/自愈/收尾），职责清晰、可单独测试
  2. 自愈重试由【条件边 conditional edge】表达，而不是写在循环里
  3. 状态（state）显式声明，LangGraph 自动在节点间传递，链路可回溯
  4. 接 LangSmith 后每次运行的节点轨迹自动上报，无需自己打日志

图结构：
  START → router ──chitchat──→ fallback → END
                   └─select──→ plan_sql → execute ──ok──→ END
                                            └──error──→ self_heal ──(retry<2)──→ execute
                                                                   └─(retry=2)──→ END
运行：python langgraph_version/graph_flow.py
"""
import os, sys
from typing import TypedDict, Optional, Set

# 让脚本能 import 到项目根目录下的 agent / eval 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langgraph.graph import StateGraph, START, END

from agent import llm_client, router
from agent.prompts import build_prompt
from agent.sql_agent import DB, _run_sql

MAX_RETRY = 2


class AgentState(TypedDict, total=False):
    """图的状态：所有节点读写同一个 dict，LangGraph 负责在边上传递。"""
    question: str          # 用户输入
    version: str           # Prompt 版本（v1_basic / v2_role_fewshot / v3_rule）
    case: dict             # 测试用例（离线演示模式需要，真实模式可传 None）
    intent: str            # 路由结果
    sql: str               # 当前生成的 SQL
    user_ids: set          # 执行得到的人群包
    exec_ok: bool          # 是否执行成功
    error: str             # 执行报错信息（自愈节点要用）
    retries: int           # 已重试次数
    reply: str             # 兜底话术或最终提示


# ---------------- 节点 1：意图路由 ----------------
def node_router(state: AgentState) -> AgentState:
    intent = router.classify(state["question"])
    return {"intent": intent, "retries": 0, "exec_ok": False}


# ---------------- 节点 2：兜底话术 ----------------
def node_fallback(state: AgentState) -> AgentState:
    return {"reply": router.FALLBACK_REPLY}


# ---------------- 节点 3：生成 SQL ----------------
def node_plan_sql(state: AgentState) -> AgentState:
    """首轮与自愈轮都走这里：有报错就带着报错重生成。"""
    version, question = state["version"], state["question"]
    attempt = state.get("retries", 0)
    if llm_client.MODE == "real":
        prompt = build_prompt(version, question)
        if attempt:  # 把上一轮报错回传给模型，让它自我修正
            prompt += (f"\n\n上一次生成的 SQL 执行报错：{state['error']}\n"
                       f"请修正后重新输出一条 SQL。")
        sql = llm_client.call_llm(prompt)
    else:
        sql = llm_client.mock_generate_sql(state["case"], version, retry=attempt)
    return {"sql": sql}


# ---------------- 节点 4：执行 SQL ----------------
def node_execute(state: AgentState) -> AgentState:
    ids, err = _run_sql(state["sql"])
    return {"user_ids": ids or set(), "exec_ok": err is None, "error": err}


# ---------------- 节点 5：自愈（把重试计数加一，然后回到执行前的生成环节）----------------
def node_self_heal(state: AgentState) -> AgentState:
    return {"retries": state.get("retries", 0) + 1}


def route_after_router(state: AgentState) -> str:
    """条件边：圈选走生成，其他走兜底。"""
    return "plan_sql" if state["intent"] == "select" else "fallback"


def route_after_execute(state: AgentState) -> str:
    """条件边：成功就结束，失败且还有重试额度就自愈，超限也结束。"""
    if state["exec_ok"]:
        return END
    return "self_heal" if state.get("retries", 0) < MAX_RETRY else END


def build_graph():
    """组装并编译图。compile() 之后就是一个可调用对象。"""
    g = StateGraph(AgentState)
    g.add_node("router", node_router)
    g.add_node("fallback", node_fallback)
    g.add_node("plan_sql", node_plan_sql)
    g.add_node("execute", node_execute)
    g.add_node("self_heal", node_self_heal)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", route_after_router,
                            {"plan_sql": "plan_sql", "fallback": "fallback"})
    g.add_edge("plan_sql", "execute")
    g.add_conditional_edges("execute", route_after_execute,
                            {"self_heal": "self_heal", END: END})
    g.add_edge("self_heal", "plan_sql")   # 自愈后回到生成，形成受控循环
    g.add_edge("fallback", END)
    return g.compile()


GRAPH = build_graph()


def answer(question: str, version: str = "v3_rule", case: dict = None) -> dict:
    """对外接口，保持与轻量版 agent.sql_agent.answer 一致，方便直接替换。"""
    final = GRAPH.invoke({"question": question, "version": version, "case": case})
    return {"intent": final.get("intent"), "sql": final.get("sql"),
            "user_ids": final.get("user_ids"), "exec_ok": final.get("exec_ok", False),
            "retries": final.get("retries", 0), "error": final.get("error"),
            "reply": final.get("reply")}


if __name__ == "__main__":
    from eval.test_cases import CASES

    print(f"模式: {'真实 LLM' if llm_client.MODE == 'real' else '离线演示'}   图节点: {list(GRAPH.get_graph().nodes)}")
    for c in CASES[:3] + [c for c in CASES if c["id"] in ("A01", "X01", "B01")]:
        r = answer(c["question"], "v3_rule", case=c)
        print(f"\n[{c['id']}/{c['level']}] {c['question']}")
        print(f"  意图={r['intent']}  重试={r['retries']}  人群数={len(r['user_ids'] or [])}")
        print(f"  SQL={r['sql'] or r['reply']}")
