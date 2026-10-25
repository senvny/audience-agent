# -*- coding: utf-8 -*-
"""
路由层：意图分类 —— 判断输入是"人群圈选"需求还是"兜底闲聊"。
采用 Router 前置的思路（而非 ReAct 自由决策）：人群圈选是模式化任务，
先路由再生成，链路更可控、幻觉更少。
这里用规则实现（关键词命中），真实场景可替换为 LLM 分类器。
"""

# 圈选意图的强信号词
SELECT_SIGNALS = ["圈出", "圈选", "筛选", "找出", "提取", "拉取", "人群包", "目标用户", "哪些用户"]


def classify(question: str) -> str:
    """返回 'select'（圈选）或 'chitchat'（兜底闲聊）。"""
    q = question.strip()
    if any(s in q for s in SELECT_SIGNALS):
        return "select"
    return "chitchat"


FALLBACK_REPLY = ("我目前只支持人群圈选类需求。你可以这样问我："
                  "圈出近30天加购但未下单的高价值用户。")
