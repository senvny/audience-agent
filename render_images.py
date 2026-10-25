# -*- coding: utf-8 -*-
"""把作品集中的手绘 SVG 图与原型 mockup 渲染成 PNG（供 Word 嵌入）。"""
import os, subprocess

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE = r"D:\Software\WkbRecord\2026-10-10-20-44-03\audience-agent-eval"
OUT = os.path.join(BASE, "_assets")
os.makedirs(OUT, exist_ok=True)

SVG_ARCH = '''<svg viewBox="0 0 780 350" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei,sans-serif">
<defs><marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#1f6feb"/></marker></defs>
<rect x="20" y="14" width="600" height="88" rx="12" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/>
<text x="38" y="42" font-size="14" font-weight="700" fill="#12395f">产品层 · app/</text>
<text x="38" y="62" font-size="11" fill="#7b8b9c">FastAPI 接口 + 单页前端，只做 HTTP 协议层</text>
<g font-size="11" fill="#1f6feb">
<rect x="38" y="72" width="86" height="21" rx="6" fill="#fff" stroke="#1f6feb"/><text x="54" y="86">圈选接口</text>
<rect x="132" y="72" width="86" height="21" rx="6" fill="#fff" stroke="#1f6feb"/><text x="148" y="86">画像统计</text>
<rect x="226" y="72" width="86" height="21" rx="6" fill="#fff" stroke="#1f6feb"/><text x="242" y="86">历史记录</text>
<rect x="320" y="72" width="86" height="21" rx="6" fill="#fff" stroke="#1f6feb"/><text x="336" y="86">CSV 导出</text>
<rect x="414" y="72" width="86" height="21" rx="6" fill="#fff" stroke="#1f6feb"/><text x="430" y="86">单页前端</text>
</g>
<line x1="320" y1="102" x2="320" y2="124" stroke="#1f6feb" stroke-width="2" marker-end="url(#a1)"/>
<text x="332" y="118" font-size="10" fill="#7b8b9c">单向依赖</text>
<rect x="20" y="126" width="600" height="108" rx="12" fill="#f2f6fb" stroke="#3b82f6" stroke-width="1.5"/>
<text x="38" y="154" font-size="14" font-weight="700" fill="#12395f">引擎层 · langgraph_version/ + agent/</text>
<text x="38" y="174" font-size="11" fill="#7b8b9c">核心编排：LangGraph 四节点图 + 3 版 Prompt + 路由 + LLM 客户端</text>
<g font-size="11" fill="#12395f">
<rect x="38" y="186" width="96" height="21" rx="6" fill="#fff" stroke="#3b82f6"/><text x="52" y="200">意图路由</text>
<rect x="142" y="186" width="96" height="21" rx="6" fill="#fff" stroke="#3b82f6"/><text x="156" y="200">Prompt 三版</text>
<rect x="246" y="186" width="96" height="21" rx="6" fill="#fff" stroke="#3b82f6"/><text x="260" y="200">SQL 生成</text>
<rect x="350" y="186" width="96" height="21" rx="6" fill="#fff" stroke="#3b82f6"/><text x="364" y="200">SQL 执行</text>
<rect x="454" y="186" width="110" height="21" rx="6" fill="#fff" stroke="#3b82f6"/><text x="470" y="200">自愈重试 ≤2</text>
</g>
<line x1="320" y1="234" x2="320" y2="256" stroke="#1f6feb" stroke-width="2" marker-end="url(#a1)"/>
<rect x="20" y="258" width="600" height="72" rx="12" fill="#fafbfd" stroke="#8fa6bd" stroke-width="1.5"/>
<text x="38" y="286" font-size="14" font-weight="700" fill="#12395f">数据层 · data/</text>
<text x="38" y="310" font-size="11" fill="#5a6b7d">业务库：user_tags · 3000 用户 × 17 字段</text>
<text x="410" y="310" font-size="11" fill="#5a6b7d">历史库：history.db · 圈选历史</text>
<text x="650" y="62" font-size="11" fill="#1f6feb" font-weight="600">用户可感知</text>
<text x="650" y="184" font-size="11" fill="#3b82f6" font-weight="600">核心编排</text>
<text x="650" y="296" font-size="11" fill="#5a6b7d" font-weight="600">数据底座</text>
</svg>'''

SVG_LG = '''<svg viewBox="0 0 780 290" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei,sans-serif">
<defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#5a6b7d"/></marker></defs>
<ellipse cx="58" cy="115" rx="38" ry="19" fill="#22303d"/><text x="58" y="120" font-size="11" fill="#fff" text-anchor="middle" font-weight="600">START</text>
<line x1="96" y1="115" x2="148" y2="115" stroke="#5a6b7d" stroke-width="2" marker-end="url(#a2)"/>
<rect x="148" y="92" width="128" height="46" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/>
<text x="212" y="111" font-size="13" fill="#12395f" text-anchor="middle" font-weight="600">意图路由</text><text x="212" y="128" font-size="10" fill="#7b8b9c" text-anchor="middle">router</text>
<line x1="212" y1="92" x2="212" y2="38" stroke="#5a6b7d" stroke-width="2"/><line x1="212" y1="38" x2="374" y2="38" stroke="#5a6b7d" stroke-width="2" marker-end="url(#a2)"/>
<text x="292" y="32" font-size="10" fill="#d68910" font-weight="600">非圈选 / 闲聊</text>
<rect x="374" y="14" width="126" height="46" rx="10" fill="#fffaf0" stroke="#d68910" stroke-width="1.5"/>
<text x="437" y="33" font-size="13" fill="#5d4a2c" text-anchor="middle" font-weight="600">兜底话术</text><text x="437" y="50" font-size="10" fill="#7b8b9c" text-anchor="middle">fallback</text>
<line x1="500" y1="37" x2="574" y2="37" stroke="#5a6b7d" stroke-width="2"/><line x1="574" y1="37" x2="574" y2="96" stroke="#5a6b7d" stroke-width="2" marker-end="url(#a2)"/>
<ellipse cx="574" cy="115" rx="38" ry="19" fill="#16a085"/><text x="574" y="120" font-size="11" fill="#fff" text-anchor="middle" font-weight="600">END</text>
<line x1="276" y1="115" x2="354" y2="115" stroke="#5a6b7d" stroke-width="2" marker-end="url(#a2)"/>
<text x="314" y="108" font-size="10" fill="#1f6feb" font-weight="600">圈选</text>
<rect x="354" y="92" width="136" height="46" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/>
<text x="422" y="111" font-size="13" fill="#12395f" text-anchor="middle" font-weight="600">生成 SQL</text><text x="422" y="128" font-size="10" fill="#7b8b9c" text-anchor="middle">plan_sql</text>
<line x1="490" y1="115" x2="558" y2="115" stroke="#5a6b7d" stroke-width="2" marker-end="url(#a2)"/>
<rect x="558" y="92" width="126" height="46" rx="10" fill="#eaf1ff" stroke="#3b82f6" stroke-width="1.5"/>
<text x="621" y="111" font-size="13" fill="#12395f" text-anchor="middle" font-weight="600">执行 SQL</text><text x="621" y="128" font-size="10" fill="#7b8b9c" text-anchor="middle">execute</text>
<line x1="621" y1="92" x2="621" y2="70" stroke="#16a085" stroke-width="2"/><line x1="621" y1="70" x2="574" y2="70" stroke="#16a085" stroke-width="2"/><line x1="574" y1="70" x2="574" y2="96" stroke="#16a085" stroke-width="2"/>
<text x="596" y="64" font-size="10" fill="#16a085" font-weight="600">执行成功</text>
<line x1="621" y1="138" x2="621" y2="234" stroke="#c0392b" stroke-width="2"/>
<text x="632" y="190" font-size="10" fill="#c0392b" font-weight="600">执行失败</text>
<rect x="526" y="234" width="136" height="46" rx="10" fill="#fff0f0" stroke="#c0392b" stroke-width="1.5"/>
<text x="594" y="253" font-size="13" fill="#7a2020" text-anchor="middle" font-weight="600">自愈重试</text><text x="594" y="270" font-size="10" fill="#7b8b9c" text-anchor="middle">self_heal</text>
<line x1="526" y1="234" x2="526" y2="115" stroke="#c0392b" stroke-width="2"/><line x1="526" y1="115" x2="490" y2="115" stroke="#c0392b" stroke-width="2" marker-end="url(#a2)"/>
<text x="512" y="176" font-size="9.5" fill="#c0392b" font-weight="600">重试 &lt; 2 次</text><text x="510" y="192" font-size="9.5" fill="#7b8b9c">回到生成</text>
</svg>'''

SVG_FLOW = '''<svg viewBox="0 0 780 240" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei,sans-serif">
<defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#1f6feb"/></marker></defs>
<g font-size="12">
<rect x="10" y="66" width="112" height="56" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/><text x="66" y="90" text-anchor="middle" fill="#12395f" font-weight="600">① 输入需求</text><text x="66" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">一句自然语言</text>
<rect x="140" y="66" width="112" height="56" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/><text x="196" y="90" text-anchor="middle" fill="#12395f" font-weight="600">② 意图路由</text><text x="196" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">圈选 / 闲聊</text>
<rect x="270" y="66" width="112" height="56" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/><text x="326" y="90" text-anchor="middle" fill="#12395f" font-weight="600">③ 生成 SQL</text><text x="326" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">DeepSeek 翻译</text>
<rect x="400" y="66" width="112" height="56" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/><text x="456" y="90" text-anchor="middle" fill="#12395f" font-weight="600">④ 执行 SQL</text><text x="456" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">SQLite 查人群</text>
<rect x="530" y="66" width="112" height="56" rx="10" fill="#eef4ff" stroke="#1f6feb" stroke-width="1.5"/><text x="586" y="90" text-anchor="middle" fill="#12395f" font-weight="600">⑤ 结果卡</text><text x="586" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">人数/画像/名单</text>
<rect x="660" y="66" width="104" height="56" rx="10" fill="#ecfaf5" stroke="#16a085" stroke-width="1.5"/><text x="712" y="90" text-anchor="middle" fill="#14503f" font-weight="600">⑥ 导出</text><text x="712" y="108" text-anchor="middle" fill="#7b8b9c" font-size="10">CSV / 回看</text>
<line x1="122" y1="94" x2="138" y2="94" stroke="#1f6feb" stroke-width="2" marker-end="url(#a3)"/>
<line x1="252" y1="94" x2="268" y2="94" stroke="#1f6feb" stroke-width="2" marker-end="url(#a3)"/>
<line x1="382" y1="94" x2="398" y2="94" stroke="#1f6feb" stroke-width="2" marker-end="url(#a3)"/>
<line x1="512" y1="94" x2="528" y2="94" stroke="#1f6feb" stroke-width="2" marker-end="url(#a3)"/>
<line x1="642" y1="94" x2="658" y2="94" stroke="#1f6feb" stroke-width="2" marker-end="url(#a3)"/>
<line x1="196" y1="66" x2="196" y2="156" stroke="#d68910" stroke-width="2"/>
<rect x="140" y="158" width="112" height="44" rx="9" fill="#fffaf0" stroke="#d68910" stroke-width="1.5"/><text x="196" y="177" text-anchor="middle" fill="#5d4a2c" font-weight="600">兜底话术</text><text x="196" y="193" text-anchor="middle" fill="#7b8b9c" font-size="9.5">非圈选 → 拒答</text>
<line x1="456" y1="122" x2="456" y2="156" stroke="#c0392b" stroke-width="2"/><line x1="456" y1="156" x2="326" y2="156" stroke="#c0392b" stroke-width="2"/><line x1="326" y1="156" x2="326" y2="124" stroke="#c0392b" stroke-width="2" marker-end="url(#a3)"/>
<text x="390" y="149" fill="#c0392b" font-size="10" font-weight="600">失败 → 自愈重试 ≤ 2 次</text>
</g>
</svg>'''

def svg2png(svg, name, ratio, w=900):
    h = int(w * ratio)
    html = f'<html><head><meta charset="utf-8"></head><body style="margin:0">'
    html += svg.replace('<svg ', f'<svg width="{w}" height="{h}" ') + '</body></html>'
    hp = os.path.join(OUT, name + ".html")
    png = os.path.join(OUT, name + ".png")
    open(hp, "w", encoding="utf-8").write(html)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={png}", f"--window-size={w},{h}",
                    "file:///" + hp.replace("\\", "/")], capture_output=True)
    return png, os.path.exists(png) and os.path.getsize(png) > 0

results = []
results.append(("arch", svg2png(SVG_ARCH, "arch", 350/780)))
results.append(("langgraph", svg2png(SVG_LG, "langgraph", 290/780)))
results.append(("flow", svg2png(SVG_FLOW, "flow", 240/780)))
for name, (png, ok) in results:
    print(name, "->", png if ok else "FAILED", os.path.getsize(png) if ok else "")
