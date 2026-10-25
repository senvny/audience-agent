# -*- coding: utf-8 -*-
"""
圈选历史模块：把每次圈选的需求、SQL、结果人群落库，支持回看与导出。

设计要点（为什么独立建库）：
- 业务数据在 data/audience.db，由 data/build_db.py 维护，该脚本重建时会整库删除重建；
  若把历史表混进业务库，一次数据重建就会把历史全部清掉。
- 因此历史独立存 data/history.db，只由本模块读写，与业务库互不感知（低耦合）。

数据流转位置：POST /api/select 先 save() 占位拿 record_id → 引擎跑完 → update() 补全结果；
GET /api/history、/api/history/{id}、/api/export/{id} 均从这里读。
"""
import json
import os
import sqlite3
from datetime import datetime

# 历史库路径：固定在项目 data/ 下，与业务库 audience.db 并列
BASE = os.path.join(os.path.dirname(__file__), "..")
DB = os.path.join(BASE, "data", "history.db")

# 表结构：一次圈选一条记录。user_ids 存 JSON 数组文本（SQLite 无数组类型）。
# created_at 记录本地时间便于人读；sql 存最终执行成功（或最后一次尝试）的 SQL。
_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    question    TEXT NOT NULL,
    intent      TEXT,
    sql_text    TEXT,
    user_ids    TEXT,
    count       INTEGER,
    retries     INTEGER,
    elapsed_ms  INTEGER
)
"""


def _conn():
    """打开历史库连接，并确保表存在（首次调用时自动建表）。"""
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(_SCHEMA)
    return con


def save(question: str) -> int:
    """圈选开始时先落一条占位记录，返回 record_id 供后续 update 补全结果。"""
    con = _conn()
    cur = con.execute(
        "INSERT INTO records (created_at, question) VALUES (?, ?)",
        (datetime.now().isoformat(timespec="seconds"), question),
    )
    con.commit()
    rid = cur.lastrowid
    con.close()
    return rid


def update(rid: int, intent: str, sql: str, user_ids, retries: int, elapsed_ms: int):
    """引擎跑完后把结果回填到占位记录上（user_ids 序列化为 JSON 文本存储）。"""
    con = _conn()
    con.execute(
        "UPDATE records SET intent=?, sql_text=?, user_ids=?, count=?, retries=?, elapsed_ms=? "
        "WHERE id=?",
        (intent, sql, json.dumps(sorted(user_ids or [])),
         len(user_ids or []), retries, elapsed_ms, rid),
    )
    con.commit()
    con.close()


def list_recent(limit: int = 50) -> list:
    """历史列表（侧栏用）：不返回完整名单，只返回摘要字段，按时间倒序。"""
    con = _conn()
    rows = con.execute(
        "SELECT id, created_at, question, intent, count, retries, elapsed_ms "
        "FROM records ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(id=r[0], created_at=r[1], question=r[2], intent=r[3],
                 count=r[4], retries=r[5], elapsed_ms=r[6]) for r in rows]


def get(rid: int):
    """单条历史详情。user_ids 反序列化回 Python 集合场景需要的列表。

    返回 dict；记录不存在返回 None（由上层转 404）。
    """
    con = _conn()
    row = con.execute(
        "SELECT id, created_at, question, intent, sql_text, user_ids, count, "
        "retries, elapsed_ms FROM records WHERE id=?", (rid,)
    ).fetchone()
    con.close()
    if row is None:
        return None
    return dict(id=row[0], created_at=row[1], question=row[2], intent=row[3],
                sql=row[4], user_ids=json.loads(row[5]) if row[5] else [],
                count=row[6], retries=row[7], elapsed_ms=row[8])
