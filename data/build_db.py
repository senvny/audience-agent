# -*- coding: utf-8 -*-
"""
数据层：生成电商用户标签宽表 user_tags（3000 用户），写入 SQLite。
标签与行为口径自洽（如 order_30d=1 则 last_order_date 必在近 30 天内），
保证测试用例的参考 SQL（标准答案）与数据一致。
输出：data/audience.db（表 user_tags）
"""
import os, random, sqlite3
from datetime import date, timedelta

random.seed(42)
BASE = os.path.join(os.path.dirname(__file__), "..")
DB = os.path.join(BASE, "data", "audience.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)

REF = date(2026, 10, 10)          # 基准日（所有"近N天"以此为锚）
N = 3000

SCHEMA = """
CREATE TABLE user_tags (
    user_id INTEGER PRIMARY KEY,
    gender TEXT,            -- 男/女
    age INTEGER,
    city_tier TEXT,         -- 一线/新一线/二线/三线及以下
    category_pref TEXT,     -- 美妆/服饰/食品/数码/母婴/家居
    member_level TEXT,      -- 普通/银卡/金卡/钻石
    is_high_value INTEGER,  -- 1=高价值用户
    register_date TEXT,     -- 注册日
    last_active_date TEXT,  -- 最近活跃日
    last_order_date TEXT,   -- 最近下单日（可为 NULL=从未下单）
    add_cart_30d INTEGER,   -- 近30天是否加购
    order_30d INTEGER,      -- 近30天是否下单
    order_cnt_30d INTEGER,  -- 近30天下单次数
    purchase_90d_cnt INTEGER, -- 近90天购买次数
    churn_risk INTEGER,     -- 1=流失预警
    coupon_user INTEGER,    -- 是否使用过优惠券
    push_enabled INTEGER    -- 是否开启推送
)"""

def d(days_ago):
    return (REF - timedelta(days=days_ago)).isoformat()

rows = []
for uid in range(1, N + 1):
    gender = random.choices(["男", "女"], weights=[45, 55])[0]
    age = max(16, min(70, int(random.gauss(30, 9))))
    city = random.choices(["一线", "新一线", "二线", "三线及以下"], weights=[15, 25, 30, 30])[0]
    cat = random.choices(["美妆", "服饰", "食品", "数码", "母婴", "家居"],
                         weights=[25, 20, 20, 15, 10, 10])[0]
    member = random.choices(["普通", "银卡", "金卡", "钻石"], weights=[55, 25, 15, 5])[0]
    hv = 1 if random.random() < (0.8 if member in ("金卡", "钻石") else 0.2) else 0

    reg_days = random.randint(0, 720)                     # 注册天数
    act_days = min(reg_days, int(random.expovariate(1 / 25)))  # 最近活跃距今天数
    order_30d = 1 if random.random() < (0.45 if hv else 0.15) else 0
    if order_30d:
        last_order_days = random.randint(0, 29)
        order_cnt = max(1, int(random.gauss(3, 2)))
    else:
        # 70% 历史下过单（31~180 天前），30% 从未下单
        last_order_days = random.choice([random.randint(31, 180), None]) if random.random() < 0.7 else None
        order_cnt = 0
    p90 = order_cnt + (random.randint(0, 6) if last_order_days is not None else 0)
    churn = 1 if act_days > 45 and random.random() < 0.8 else 0

    rows.append((uid, gender, age, city, cat, member, hv,
                 d(reg_days), d(act_days),
                 d(last_order_days) if last_order_days is not None else None,
                 1 if random.random() < 0.35 else 0,       # add_cart_30d
                 order_30d, order_cnt, p90, churn,
                 1 if random.random() < 0.4 else 0,
                 1 if random.random() < 0.55 else 0))

if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.execute("DROP TABLE IF EXISTS user_tags")
con.execute(SCHEMA)
con.executemany("INSERT INTO user_tags VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
con.commit()

# 数据健康检查：打印几个关键口径的人数，便于核对
checks = {
    "总用户数": "SELECT COUNT(*) FROM user_tags",
    "近30天加购未下单": "SELECT COUNT(*) FROM user_tags WHERE add_cart_30d=1 AND order_30d=0",
    "流失预警": "SELECT COUNT(*) FROM user_tags WHERE churn_risk=1",
    "金卡/钻石会员": "SELECT COUNT(*) FROM user_tags WHERE member_level IN ('金卡','钻石')",
    "矛盾用例X02(应为0)": "SELECT COUNT(*) FROM user_tags WHERE order_cnt_30d>5 AND purchase_90d_cnt=0",
}
for k, sql in checks.items():
    print(f"{k}: {con.execute(sql).fetchone()[0]}")
con.close()
print(f"\n数据库已生成: {DB}（{N} 用户）")
