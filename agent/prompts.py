# -*- coding: utf-8 -*-
"""
Prompt 层：人群圈选 Agent 的 3 版 Prompt（对比实验对象）。
v1 基础版：仅表结构
v2 角色版 + Few-Shot：角色设定 + 业务口径词典 + 2 个示例
v3 规则约束版：在 v2 基础上追加 6 条生成规则（即"优化后 Prompt 模板"）
"""

REF_DATE = "2026-10-10"

# 表结构描述（注入 Prompt；真实企业库上千张表时才需要向量检索，
# 本项目单表场景直接全文注入，性价比更高）
SCHEMA_DESC = f"""表名：user_tags（电商用户标签宽表，每行一个用户）
字段：
- user_id INTEGER  用户ID
- gender TEXT      性别：男/女
- age INTEGER      年龄
- city_tier TEXT   城市等级：一线/新一线/二线/三线及以下
- category_pref TEXT 品类偏好：美妆/服饰/食品/数码/母婴/家居
- member_level TEXT 会员等级：普通/银卡/金卡/钻石
- is_high_value INTEGER  是否高价值用户：1是/0否
- register_date TEXT  注册日期 YYYY-MM-DD
- last_active_date TEXT 最近活跃日期
- last_order_date TEXT  最近下单日期（从未下单为 NULL）
- add_cart_30d INTEGER  近30天是否加购：1是/0否
- order_30d INTEGER     近30天是否下单：1是/0否
- order_cnt_30d INTEGER 近30天下单次数
- purchase_90d_cnt INTEGER 近90天购买次数
- churn_risk INTEGER    是否流失预警：1是/0否
- coupon_user INTEGER   是否使用过优惠券：1是/0否
- push_enabled INTEGER  是否开启推送：1是/0否
基准日：{REF_DATE}（所有"近N天"以此为锚，用 date('{REF_DATE}', '-N day') 计算）"""

# 业务口径词典（模拟企业里的"业务黑话 -> 数据口径"映射表）
GLOSSARY = """业务口径词典：
- "活跃用户"  = 近7天有活跃：last_active_date >= date(基准日, '-7 day')
- "老客"      = 注册满180天：register_date <= date(基准日, '-180 day')
- "高潜用户"  = 近30天加购但未下单：add_cart_30d=1 AND order_30d=0
- "沉默用户"  = 超过60天未活跃：last_active_date <= date(基准日, '-60 day')"""

FEWSHOT = f"""示例1：
需求：圈出近30天加购但未下单的高价值用户
SQL：SELECT user_id FROM user_tags WHERE add_cart_30d = 1 AND order_30d = 0 AND is_high_value = 1

示例2：
需求：圈出流失预警的美妆用户
SQL：SELECT user_id FROM user_tags WHERE churn_risk = 1 AND category_pref = '美妆'"""

RULES = f"""生成规则（必须严格遵守）：
1. 只输出一条以 SELECT user_id 开头的 SQLite 查询，不要输出任何解释、注释或 Markdown 标记
2. 所有时间计算以 {REF_DATE} 为基准日，使用 date('{REF_DATE}', '-N day')
3. 多个条件默认是"且（AND）"关系，除非需求明确说"或"
4. 若需求内部条件互相矛盾，仍按字面生成 SQL（返回空结果是正确行为，不要擅自放松条件）
5. 涉及"未/没有/从未"的否定条件必须考虑 NULL 值（如"未下单"= order_30d=0，"从未下单"= last_order_date IS NULL）
6. 字段名和取值必须与上方表结构完全一致，不得臆造字段"""


def build_prompt(version: str, question: str) -> str:
    """按版本拼装完整 Prompt。"""
    if version == "v1_basic":
        return (f"你是SQL生成助手。根据下面的表结构，把业务需求转换成一条 SQLite 查询，只输出SQL。\n\n"
                f"{SCHEMA_DESC}\n\n业务需求：{question}")
    if version == "v2_role_fewshot":
        return (f"你是一名资深电商数据分析师，擅长把投放需求准确翻译成人群圈选 SQL，"
                f"尤其注意业务黑话的数据口径。\n\n{SCHEMA_DESC}\n\n{GLOSSARY}\n\n{FEWSHOT}\n\n"
                f"现在处理新需求，只输出 SQL：\n需求：{question}")
    if version == "v3_rule":
        return (f"你是一名资深电商数据分析师，擅长把投放需求准确翻译成人群圈选 SQL。\n\n"
                f"{SCHEMA_DESC}\n\n{GLOSSARY}\n\n{FEWSHOT}\n\n{RULES}\n\n"
                f"需求：{question}")
    raise ValueError(f"未知版本: {version}")

VERSIONS = ["v1_basic", "v2_role_fewshot", "v3_rule"]
VERSION_CN = {"v1_basic": "V1 基础版", "v2_role_fewshot": "V2 角色+Few-Shot", "v3_rule": "V3 规则约束版"}
