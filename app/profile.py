# -*- coding: utf-8 -*-
"""
人群画像模块：对圈出的一批 user_ids 读取 user_tags 表，输出各维度的分布统计。

业务价值：运营圈人后第一反应是"这群人长什么样"——画像分布能立刻验证圈选
是否符合直觉（比如圈"高价值用户"结果里普通会员占大头，就说明圈错了）。

实现说明：
- 只读业务库 data/audience.db（与引擎共用同一份数据源，口径天然一致）；
- 用「SELECT 维度, COUNT(*) ... WHERE user_id IN (...) GROUP BY 维度」统计；
- user_ids 数量可能很大，IN 子句按 SQLite 变量上限（999）分批查询后合并。
"""
import os
import sqlite3

# 与 agent/sql_agent.py 保持同一业务库（单一数据源，避免两处路径漂移）
from agent.sql_agent import DB

# 画像维度：只挑"类目型"字段做分布（数值型如 age 不适合条形图展示）
DIMENSIONS = ["gender", "city_tier", "member_level", "category_pref"]

# 每个维度的中文名（前端直接展示用）
DIM_CN = {"gender": "性别", "city_tier": "城市等级",
          "member_level": "会员等级", "category_pref": "品类偏好"}

# SQLite 默认变量上限 999，留余量按 900 分批
_BATCH = 900


def stats(user_ids) -> dict:
    """
    对给定人群做画像统计。
    返回: {维度: [{label, count, pct}, ...], ...}，pct 为占该人群的百分比（1位小数）。
    空人群返回空 dict（前端渲染"暂无数据"）。
    """
    ids = list(set(user_ids or []))
    if not ids:
        return {}

    con = sqlite3.connect(DB)
    result = {}
    for dim in DIMENSIONS:
        counter = {}
        # 分批 IN 查询：避免一次传几千个参数触发 SQLite 变量上限
        for i in range(0, len(ids), _BATCH):
            batch = ids[i:i + _BATCH]
            ph = ",".join("?" * len(batch))
            rows = con.execute(
                f"SELECT {dim}, COUNT(*) FROM user_tags WHERE user_id IN ({ph}) "
                f"GROUP BY {dim}", batch).fetchall()
            for label, cnt in rows:
                counter[label] = counter.get(label, 0) + cnt
        total = sum(counter.values())
        # 按人数降序输出，附占比（占比分母=该维度有值的人数）
        result[dim] = [
            {"label": k, "count": v, "pct": round(v * 100.0 / total, 1) if total else 0}
            for k, v in sorted(counter.items(), key=lambda x: -x[1])
        ]
    con.close()
    return result


def sample(user_ids, limit: int = 50) -> list:
    """
    名单预览：取前 limit 个用户的 id + 关键标签（与画像字段对齐），
    完整名单通过导出 CSV 获取，页面只展示预览防止一次渲染几千行卡死。
    """
    ids = sorted(set(user_ids or []))[:limit]
    if not ids:
        return []
    con = sqlite3.connect(DB)
    ph = ",".join("?" * len(ids))
    rows = con.execute(
        f"SELECT user_id, gender, age, city_tier, member_level, category_pref "
        f"FROM user_tags WHERE user_id IN ({ph}) ORDER BY user_id", ids).fetchall()
    con.close()
    return [dict(zip(["user_id", "gender", "age", "city_tier",
                      "member_level", "category_pref"], r)) for r in rows]
