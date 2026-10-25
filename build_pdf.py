# -*- coding: utf-8 -*-
"""把图表 base64 内嵌进打印版 HTML，再用 Edge 无头模式转成 A4 PDF。"""
import base64, os, subprocess, shutil

BASE = r"D:\Software\WkbRecord\2026-10-10-20-44-03\audience-agent-eval"
SRC = os.path.join(BASE, "pm_portfolio_print.html")
TMP = os.path.join(BASE, "_print_final.html")
PDF = os.path.join(BASE, "pm_portfolio.pdf")
CHARTS = os.path.join(BASE, "charts")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def b64(name):
    with open(os.path.join(CHARTS, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

html = open(SRC, "r", encoding="utf-8").read()
html = html.replace("__CHART_VERSIONS__", b64("eval_versions.png"))
html = html.replace("__CHART_LEVEL__", b64("eval_by_level.png"))
html = html.replace("__CHART_BAD__", b64("eval_badcases.png"))
open(TMP, "w", encoding="utf-8").write(html)

url = "file:///" + TMP.replace("\\", "/")
r = subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={PDF}", url], capture_output=True, text=True)
print("exit:", r.returncode)
print("pdf exists:", os.path.exists(PDF), os.path.getsize(PDF) if os.path.exists(PDF) else "-", "bytes")
