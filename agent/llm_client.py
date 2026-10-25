# -*- coding: utf-8 -*-
"""
LLM 调用层（双模式）：
- 真实模式：设置环境变量 LLM_API_KEY 后，调用 DeepSeek 兼容的 Chat Completions 接口
  （零第三方依赖，用标准库 urllib 发请求）
- 离线演示模式（mock）：无 Key 时自动启用。从测试用例的参考 SQL 出发，
  按"Prompt 版本 × 用例难度"的预设错误率注入典型错误，模拟不同 Prompt 的质量差异，
  用于在无 API 的情况下验证整条评测链路。报告中会明确标注为演示数据。

环境变量：
  LLM_API_KEY   API 密钥（必填才走真实模式）
  LLM_BASE_URL  默认 https://api.deepseek.com/v1
  LLM_MODEL     默认 deepseek-chat
"""
import json, os, random, re, urllib.request

API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

MODE = "real" if API_KEY else "mock"


def _extract_sql(text: str) -> str:
    """从 LLM 输出中提取 SQL（容忍 ```sql 代码块包裹）。"""
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    sql = (m.group(1) if m else text).strip().rstrip(";")
    return sql


def call_llm(prompt: str, temperature: float = 0.0) -> str:
    """真实模式：调用 Chat Completions，返回提取出的 SQL 文本。"""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _extract_sql(data["choices"][0]["message"]["content"])


# ---------------- 离线演示模式 ----------------
# 各版本在不同难度类别下的错误注入概率。
# 设计依据（叙事逻辑）：v1 无口径词典和规则 → 歧义/矛盾/时间类错误率高；
# v2 有了词典和示例 → 各类错误下降；v3 加了显式规则 → 最低。
ERR_P = {
    "v1_basic":        {"简单": 0.15, "组合": 0.45, "时间": 0.50, "歧义": 0.75, "矛盾": 0.50},
    "v2_role_fewshot": {"简单": 0.05, "组合": 0.20, "时间": 0.25, "歧义": 0.35, "矛盾": 0.25},
    "v3_rule":         {"简单": 0.02, "组合": 0.08, "时间": 0.10, "歧义": 0.15, "矛盾": 0.10},
}
HEAL_P = {"v1_basic": 0.70, "v2_role_fewshot": 0.85, "v3_rule": 0.95}

_FIELDS = ["member_level", "category_pref", "city_tier", "is_high_value",
           "add_cart_30d", "order_30d", "churn_risk", "purchase_90d_cnt"]


def _inject_error(sql: str, err_type: str, case: dict, rnd: random.Random) -> str:
    """对参考 SQL 注入一类典型错误，模拟 LLM 在该 Prompt 版本下的失误。"""
    if err_type == "typo":  # 字段名拼错 → 触发执行失败 → 考验自愈重试
        for f in _FIELDS:
            if f in sql:
                return sql.replace(f, f.replace("_", ""), 1)
        return sql + " AND unknown_col = 1"
    if err_type == "drop":  # 组合条件遗漏一个（AND 条件数>1 时随机删一个）
        head, _, where = sql.partition(" WHERE ")
        conds = where.split(" AND ")
        if len(conds) > 1:
            conds.pop(rnd.randrange(len(conds)))
        return head + " WHERE " + " AND ".join(conds)
    if err_type == "date":  # 时间窗口口径错（-7 day 写成 -14 day 之类）
        return re.sub(r"-(\d+) day",
                      lambda m: f"-{int(m.group(1)) + rnd.choice([-3, 3, 7])} day", sql, count=1)
    if err_type == "or":    # 矛盾需求把 AND 写成 OR → 返回非空 → 人群完全错误
        return sql.replace(" AND ", " OR ")
    if err_type == "wrong": # 歧义黑话不查口径词典，凭直觉猜错
        return case.get("wrong_sql", sql)
    return sql


def mock_generate_sql(case: dict, version: str, retry: int = 0) -> str:
    """离线演示：按版本质量画像生成 SQL（确定性随机，保证可复现）。"""
    gold = case["gold_sql"]
    rnd = random.Random(f"{case['id']}|{version}|{retry}")
    err_type = {"简单": "typo", "组合": "drop", "时间": "date", "歧义": "wrong", "矛盾": "or"}[case["level"]]
    if rnd.random() < ERR_P[version][case["level"]]:
        sql = _inject_error(gold, err_type, case, rnd)
        if retry > 0:  # 自愈重试：按概率修正（主要是 typo 类）
            if rnd.random() < HEAL_P[version]:
                return gold
        return sql
    return gold
