# -*- coding: utf-8 -*-
"""
SQL Agent 核心链路：意图路由 → Prompt 拼装 → SQL 生成 → 执行 → 失败自愈重试（上限2次）。
返回结构化结果供评测层计算指标。
"""
import os, sqlite3
from . import llm_client, prompts, router

DB = os.path.join(os.path.dirname(__file__), "..", "data", "audience.db")
MAX_RETRY = 2  # 自愈重试上限，防止死循环


def _run_sql(sql: str):
    """执行 SQL，返回 (user_id 集合, 错误信息)。"""
    try:
        con = sqlite3.connect(DB)
        ids = {r[0] for r in con.execute(sql).fetchall()}
        con.close()
        return ids, None
    except Exception as e:
        return None, str(e)


def answer(question: str, version: str, case: dict = None) -> dict:
    """
    完整跑一遍圈选链路。
    返回: dict(intent, sql, user_ids, exec_ok, retries, error)
    """
    intent = router.classify(question)
    result = {"intent": intent, "sql": None, "user_ids": None,
              "exec_ok": False, "retries": 0, "error": None}
    if intent != "select":
        return result  # 兜底闲聊：不生成 SQL，由上层返回 FALLBACK_REPLY

    prompt = prompts.build_prompt(version, question)
    for attempt in range(MAX_RETRY + 1):
        if llm_client.MODE == "real":
            # 真实模式：首轮用原始 Prompt；重试时把错误信息反馈给模型自我修正
            p = prompt if attempt == 0 else (
                prompt + f"\n\n上一次生成的 SQL 执行报错：{result['error']}\n"
                         f"请修正后重新输出一条 SQL。")
            sql = llm_client.call_llm(p)
        else:
            sql = llm_client.mock_generate_sql(case, version, retry=attempt)

        ids, err = _run_sql(sql)
        result.update(sql=sql, user_ids=ids, exec_ok=err is None,
                      retries=attempt, error=err)
        if err is None:
            break  # 执行成功，结束；否则带着报错进入下一轮自愈
    return result
