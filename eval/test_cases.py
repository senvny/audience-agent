# -*- coding: utf-8 -*-
"""
测试集：32 条用例 = 30 条圈选（5 个难度层）+ 2 条兜底闲聊。
每条圈选用例带 gold_sql（参考 SQL）作为客观标准答案：
  用 gold_sql 跑出标准人群包，与 Agent 生成 SQL 的结果做集合比对，
  计算 Precision / Recall / F1 —— 全程无人工打分，可复现。
歧义类用例附 wrong_sql（"不查口径词典时的典型错误答案"），供离线演示模式使用。
矛盾类用例的 gold_sql 语义上必返回空集（返回空 = 正确行为）。
"""

def C(cid, level, q, gold, wrong=None):
    return {"id": cid, "type": "select", "level": level,
            "question": q, "gold_sql": gold, "wrong_sql": wrong}

def X(cid, q):
    return {"id": cid, "type": "chitchat", "level": "兜底", "question": q, "gold_sql": None}

W = "SELECT user_id FROM user_tags WHERE "

CASES = [
    # ---------- 简单（单条件，10 条） ----------
    C("S01", "简单", "圈出所有钻石会员", W + "member_level = '钻石'"),
    C("S02", "简单", "圈出高价值用户", W + "is_high_value = 1"),
    C("S03", "简单", "圈出偏好美妆的用户", W + "category_pref = '美妆'"),
    C("S04", "简单", "圈出女性用户", W + "gender = '女'"),
    C("S05", "简单", "圈出一线城市用户", W + "city_tier = '一线'"),
    C("S06", "简单", "圈出开启了推送的用户", W + "push_enabled = 1"),
    C("S07", "简单", "圈出流失预警用户", W + "churn_risk = 1"),
    C("S08", "简单", "圈出近30天有加购行为的用户", W + "add_cart_30d = 1"),
    C("S09", "简单", "圈出银卡会员", W + "member_level = '银卡'"),
    C("S10", "简单", "圈出18到25岁的用户", W + "age BETWEEN 18 AND 25"),

    # ---------- 组合（多条件，8 条） ----------
    C("C01", "组合", "圈出近30天加购但未下单的高价值用户",
      W + "add_cart_30d = 1 AND order_30d = 0 AND is_high_value = 1"),
    C("C02", "组合", "圈出流失预警的美妆用户",
      W + "churn_risk = 1 AND category_pref = '美妆'"),
    C("C03", "组合", "圈出一线和新一线城市的女性金卡会员",
      W + "city_tier IN ('一线', '新一线') AND gender = '女' AND member_level = '金卡'"),
    C("C04", "组合", "圈出近30天有下单但没开推送的用户",
      W + "order_30d = 1 AND push_enabled = 0"),
    C("C05", "组合", "圈出三线及以下城市的母婴偏好用户",
      W + "city_tier = '三线及以下' AND category_pref = '母婴'"),
    C("C06", "组合", "圈出近90天购买3次及以上的数码用户",
      W + "purchase_90d_cnt >= 3 AND category_pref = '数码'"),
    C("C07", "组合", "圈出用过优惠券的服饰偏好女性用户",
      W + "coupon_user = 1 AND category_pref = '服饰' AND gender = '女'"),
    C("C08", "组合", "圈出26到40岁的食品偏好用户",
      W + "age BETWEEN 26 AND 40 AND category_pref = '食品'"),

    # ---------- 时间窗口（6 条） ----------
    C("T01", "时间", "圈出近7天活跃的用户",
      W + "last_active_date >= date('2026-10-10', '-7 day')"),
    C("T02", "时间", "圈出近30天有下单的用户",
      W + "last_order_date >= date('2026-10-10', '-30 day')"),
    C("T03", "时间", "圈出超过60天没活跃的沉默用户",
      W + "last_active_date <= date('2026-10-10', '-60 day')"),
    C("T04", "时间", "圈出近90天购买2次及以上的用户",
      W + "purchase_90d_cnt >= 2"),
    C("T05", "时间", "圈出近30天注册的新用户",
      W + "register_date >= date('2026-10-10', '-30 day')"),
    C("T06", "时间", "圈出近14天活跃但近30天没下单的用户",
      W + "last_active_date >= date('2026-10-10', '-14 day') AND "
        "(last_order_date < date('2026-10-10', '-30 day') OR last_order_date IS NULL)"),

    # ---------- 歧义口径（业务黑话，3 条；附典型错误答案） ----------
    C("A01", "歧义", "圈出活跃用户",
      W + "last_active_date >= date('2026-10-10', '-7 day')",
      wrong=W + "is_high_value = 1"),  # 错把"活跃"理解成"高价值"
    C("A02", "歧义", "圈出老客",
      W + "register_date <= date('2026-10-10', '-180 day')",
      wrong=W + "purchase_90d_cnt >= 3"),  # 错把"老客"理解成"购买次数多"
    C("A03", "歧义", "圈出高潜用户",
      W + "add_cart_30d = 1 AND order_30d = 0",
      wrong=W + "is_high_value = 1"),  # 错把"高潜"理解成"高价值"

    # ---------- 矛盾需求（正确行为 = 返回空集，3 条） ----------
    C("X01", "矛盾", "圈出金卡会员且从未注册的用户",
      W + "member_level = '金卡' AND register_date IS NULL"),
    C("X02", "矛盾", "圈出近30天下单超过5次且近90天购买次数为0的用户",
      W + "order_cnt_30d > 5 AND purchase_90d_cnt = 0"),
    C("X03", "矛盾", "圈出年龄小于18岁且大于60岁的用户",
      W + "age < 18 AND age > 60"),

    # ---------- 兜底闲聊（考察路由器，2 条） ----------
    X("B01", "你们这个产品是干嘛的？"),
    X("B02", "今天天气怎么样"),
]
