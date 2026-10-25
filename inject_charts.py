# -*- coding: utf-8 -*-
"""把 charts/ 下三张评测图 base64 内嵌进 pm_portfolio.html 占位符。"""
import base64, os

BASE = r"D:\Software\WkbRecord\2026-10-10-20-44-03\audience-agent-eval"
HTML = os.path.join(BASE, "pm_portfolio.html")
CHARTS = os.path.join(BASE, "charts")

def b64(name):
    with open(os.path.join(CHARTS, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace("__CHART_VERSIONS__", b64("eval_versions.png"))
html = html.replace("__CHART_LEVEL__", b64("eval_by_level.png"))
html = html.replace("__CHART_BAD__", b64("eval_badcases.png"))

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)

print("charts embedded:", os.path.getsize(HTML), "bytes")
for name in ["eval_versions.png", "eval_by_level.png", "eval_badcases.png"]:
    print(" -", name, os.path.getsize(os.path.join(CHARTS, name)), "bytes")
