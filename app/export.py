# -*- coding: utf-8 -*-
"""
CSV 导出模块：把某次圈选的人群名单导出为 CSV（用户 id + 关键标签）。

业务用途：运营圈出人群后要拿去投放到 push/短信/广告系统，最常用的交付形态就是
一份名单 CSV。这里按 user_id 升序导出全部命中用户，保证可复现、可去重。

实现说明：
- 数据来源是历史记录里的 user_ids（见 history.get）+ user_tags 业务库；
- 用内存 StringIO 生成 CSV 字节流，由 server 直接作为下载响应返回，
  不落盘（每次导出即时生成，避免中间文件残留）。
"""
import csv
import io
import sqlite3

from agent.sql_agent import DB

# 导出列：id 放首位便于下游系统识别，其余为常用投放标签
COLUMNS = ["user_id", "gender", "age", "city_tier", "member_level",
           "category_pref", "last_active_date", "churn_risk"]
# 表头中文，便于运营同事直接看懂
HEADER_CN = ["用户ID", "性别", "年龄", "城市等级", "会员等级",
             "品类偏好", "最近活跃日", "是否流失预警"]


def export_csv(user_ids) -> bytes:
    """
    把人群名单转成 UTF-8 CSV（带 BOM，Excel 打开中文不乱码），返回字节流。
    """
    ids = sorted(set(user_ids or []))
    con = sqlite3.connect(DB)
    ph = ",".join("?" * len(ids)) if ids else "NULL"
    rows = con.execute(
        f"SELECT {', '.join(COLUMNS)} FROM user_tags "
        f"WHERE user_id IN ({ph}) ORDER BY user_id", ids).fetchall() if ids else []
    con.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(HEADER_CN)
    writer.writerows(rows)
    # 加 BOM 前缀，保证 Excel 用 UTF-8 正确解析中文
    return ("\ufeff" + buf.getvalue()).encode("utf-8")
