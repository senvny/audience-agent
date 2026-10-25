# -*- coding: utf-8 -*-
"""
评测主程序：3 版 Prompt × 32 条用例全量跑测，输出：
  output/eval_results.csv   逐条明细
  output/eval_summary.csv   按版本汇总
  output/eval_by_level.csv  按版本×难度层的通过率
  charts/eval_*.png         三张图
运行：python -m eval.run_eval   （在项目根目录下执行）
"""
import os, sqlite3, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent import llm_client, sql_agent
from agent.prompts import VERSIONS, VERSION_CN
from eval.test_cases import CASES
from eval.metrics import set_metrics, is_pass, attribute_bad_case

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "output"); os.makedirs(OUT, exist_ok=True)
CHARTS = os.path.join(BASE, "charts"); os.makedirs(CHARTS, exist_ok=True)
DB = os.path.join(BASE, "data", "audience.db")

# ---------- 预跑标准答案（Ground Truth） ----------
con = sqlite3.connect(DB)
GOLD = {}
for c in CASES:
    if c["type"] == "select":
        GOLD[c["id"]] = {r[0] for r in con.execute(c["gold_sql"]).fetchall()}
con.close()
print(f"标准人群包已计算：{len(GOLD)} 条圈选用例（含 3 条空集矛盾用例）")

# ---------- 全量评测 ----------
rows = []
router_total = router_hit = 0
for ver in VERSIONS:
    for c in CASES:
        res = sql_agent.answer(c["question"], ver, case=c)
        if c["type"] == "chitchat":
            # 兜底用例：期望路由器拒绝（不生成 SQL）
            router_total += 1
            ok = res["intent"] == "chitchat"
            router_hit += ok
            rows.append({"case_id": c["id"], "level": c["level"], "version": ver,
                         "question": c["question"], "gen_sql": "", "exec_ok": True,
                         "retries": 0, "n_pred": 0, "n_gold": 0, "tp": 0,
                         "precision": 1.0 if ok else 0.0, "recall": 1.0 if ok else 0.0,
                         "f1": 1.0 if ok else 0.0, "passed": ok, "bad_type": "" if ok else "路由误判"})
            continue
        gold = GOLD[c["id"]]
        pred = res["user_ids"] or set()
        m = set_metrics(pred, gold)
        row = {"case_id": c["id"], "level": c["level"], "version": ver,
               "question": c["question"], "gen_sql": res["sql"], "exec_ok": res["exec_ok"],
               "retries": res["retries"], "n_pred": len(pred), "n_gold": len(gold), **m}
        row["passed"] = is_pass(m, res["exec_ok"])
        row["bad_type"] = "" if row["passed"] else attribute_bad_case(row, c)
        rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(OUT, "eval_results.csv"), index=False, encoding="utf-8-sig")

# ---------- 汇总 ----------
sel = df[df.level != "兜底"]
summary = sel.groupby("version").agg(
    用例数=("case_id", "size"),
    任务完成率=("exec_ok", "mean"),
    平均F1=("f1", "mean"),
    通过率=("passed", "mean"),
    平均重试次数=("retries", "mean")).reindex(VERSIONS).round(3)
summary.index = [VERSION_CN[v] for v in summary.index]
for col in ["任务完成率", "平均F1", "通过率"]:
    summary[col] = (summary[col] * 100).round(1)
summary.to_csv(os.path.join(OUT, "eval_summary.csv"), encoding="utf-8-sig")

by_level = (sel.groupby(["version", "level"]).passed.mean().unstack("level")
            .reindex(VERSIONS)[["简单", "组合", "时间", "歧义", "矛盾"]] * 100).round(1)
by_level.index = [VERSION_CN[v] for v in by_level.index]
by_level.to_csv(os.path.join(OUT, "eval_by_level.csv"), encoding="utf-8-sig")

# ---------- 图1：三版 Prompt 核心指标对比 ----------
fig, ax = plt.subplots(figsize=(9, 5))
x = range(len(summary))
w = 0.25
for i, col in enumerate(["任务完成率", "平均F1", "通过率"]):
    ax.bar([xi + (i - 1) * w for xi in x], summary[col], width=w, label=col)
ax.set_xticks(list(x)); ax.set_xticklabels(summary.index)
ax.set_ylabel("%"); ax.set_ylim(0, 108)
ax.set_title(f"3 版 Prompt 核心指标对比（{'离线演示模式' if llm_client.MODE=='mock' else '真实 LLM'}）")
ax.legend(); ax.grid(axis="y", alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(CHARTS, "eval_versions.png"), dpi=150); plt.close(fig)

# ---------- 图2：分难度层通过率 ----------
fig, ax = plt.subplots(figsize=(9, 5))
by_level.T.plot(kind="bar", ax=ax, rot=0)
ax.set_ylabel("通过率 %"); ax.set_ylim(0, 108)
ax.set_title("分难度层通过率（定位 Prompt 短板在哪类需求）")
ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(CHARTS, "eval_by_level.png"), dpi=150); plt.close(fig)

# ---------- 图3：Bad case 归因分布 ----------
bad = sel[~sel.passed]
fig, ax = plt.subplots(figsize=(9, 5))
if len(bad):
    bc = bad.groupby(["bad_type", "version"]).size().unstack(fill_value=0)
    bc.columns = [VERSION_CN[c] for c in bc.columns]
    bc.plot(kind="barh", stacked=True, ax=ax)
    ax.set_title(f"Bad case 归因分布（共 {len(bad)} 条失败样本）")
    ax.set_xlabel("失败条数")
else:
    ax.text(0.5, 0.5, "全部通过，无 Bad case", ha="center", va="center", fontsize=14)
fig.tight_layout(); fig.savefig(os.path.join(CHARTS, "eval_badcases.png"), dpi=150); plt.close(fig)
bad.to_csv(os.path.join(OUT, "bad_cases.csv"), index=False, encoding="utf-8-sig")

# ---------- 终端输出 ----------
print("\n===== 核心指标汇总 =====")
print(summary.to_string())
print(f"\n兜底闲聊路由准确率: {router_hit}/{router_total}")
print("\n===== 分难度层通过率(%) =====")
print(by_level.to_string())
if len(bad):
    print("\n===== Bad case 归因 =====")
    print(bad.groupby("bad_type").size().sort_values(ascending=False).to_string())
print(f"\n模式: {'真实 LLM (' + llm_client.MODEL + ')' if llm_client.MODE=='real' else '离线演示模式（未配置 LLM_API_KEY）'}")
print(f"明细: {os.path.join(OUT, 'eval_results.csv')}")
