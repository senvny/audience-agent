# -*- coding: utf-8 -*-
"""指标层：人群集合比对指标（Precision/Recall/F1）与 Bad case 归因规则。"""

def set_metrics(pred: set, gold: set) -> dict:
    """
    人群重合度指标。
    约定：gold 与 pred 均为空 → 完全正确（F1=1，矛盾用例的理想情形）；
         gold 空但 pred 非空 → F1=0（把矛盾条件放松了的典型错误）。
    """
    tp = len(pred & gold)
    if not gold and not pred:
        return {"tp": 0, "precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not gold:
        return {"tp": 0, "precision": 0.0, "recall": 1.0, "f1": 0.0}
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4)}


PASS_F1 = 0.95  # 通过线：F1 ≥ 0.95 视为该用例通过

def is_pass(m: dict, exec_ok: bool) -> bool:
    return exec_ok and m["f1"] >= PASS_F1


def attribute_bad_case(row: dict, case: dict) -> str:
    """对未通过用例做规则化归因（模拟人工 Bad case 分析的初筛）。"""
    if not row["exec_ok"]:
        return "SQL语法/字段错误"
    if case["level"] == "矛盾":
        return "矛盾条件处理错误（AND/OR混淆或擅自放松条件）"
    p, r = row["precision"], row["recall"]
    if case["level"] == "歧义":
        return "业务口径理解偏差"
    if case["level"] == "时间":
        return "时间口径错误（基准日/窗口天数/NULL处理）"
    if p >= 0.99 and r < 0.9:
        return "条件过严（多加条件）"
    if r >= 0.99 and p < 0.9:
        return "条件遗漏（漏加条件）"
    return "需求理解偏差"
