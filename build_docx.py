# -*- coding: utf-8 -*-
"""生成可编辑的 Word 版作品集（内容与口语化 PDF 版一致）。"""
import os, re
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = r"D:\Software\WkbRecord\2026-10-10-20-44-03\audience-agent-eval"
ASSETS = os.path.join(BASE, "_assets")
CHARTS = os.path.join(BASE, "charts")
OUT = os.path.join(BASE, "人群圈选Agent作品集.docx")

INK = RGBColor(0x22, 0x30, 0x3D)
DARK = RGBColor(0x12, 0x39, 0x5F)
BLUE = RGBColor(0x1F, 0x6F, 0xEB)
RED = RGBColor(0xC0, 0x39, 0x2B)
MUTED = RGBColor(0x7B, 0x8B, 0x9C)
GREEN = RGBColor(0x16, 0xA0, 0x85)
AMBER = RGBColor(0x5D, 0x4A, 0x2C)

FONT = "Microsoft YaHei"
EAST = "微软雅黑"

def _set_run(run, size=10.5, bold=False, color=INK, mono=False):
    run.font.name = "Consolas" if mono else FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.get_or_add_rFonts()
    rf.set(qn('w:eastAsia'), EAST)

TOKEN = re.compile(r'(@@.*?@@|\*\*.*?\*\*)')

def _fill_runs(p, text, size, color):
    for tok in TOKEN.split(text):
        if not tok:
            continue
        red = tok.startswith('@@') and tok.endswith('@@')
        bold = tok.startswith('**') and tok.endswith('**')
        if red:
            tok = tok[2:-2]
        if bold:
            tok = tok[2:-2]
        run = p.add_run(tok)
        _set_run(run, size=size, bold=(bold or red), color=(RED if red else color))

def para(doc, text="", size=10.5, color=INK, align=None, before=0, after=6, line=1.6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if align is not None:
        p.alignment = align
    if text:
        _fill_runs(p, text, size, color)
    return p

def h1(doc, text, before=16):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    _set_run(run, size=15, bold=True, color=DARK)
    # 底部边框
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single'); bottom.set(qn('w:sz'), '8')
    bottom.set(qn('w:space'), '4'); bottom.set(qn('w:color'), '1F6FEB')
    pbdr.append(bottom); pPr.append(pbdr)
    return p

def h2(doc, text, before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    _set_run(run, size=11.5, bold=True, color=BLUE)
    return p

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), fill)
    tcPr.append(shd)

def table(doc, headers, rows, widths=None, size=9.5, header_fill="F2F6FB"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        p = hdr[i].paragraphs[0]
        run = p.add_run(h)
        _set_run(run, size=size, bold=True, color=DARK)
        shade(hdr[i], header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            _fill_runs(p, str(v), size, INK)
    if widths:
        for i, w in enumerate(widths):
            for r in t.rows:
                r.cells[i].width = Cm(w)
    para(doc, "", size=4, after=4)
    return t

def picture(doc, path, width_in=6.4, after=4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(after)
    run = p.add_run()
    run.add_picture(path, width=Inches(width_in))
    return p

def caption(doc, text):
    para(doc, text, size=9, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER, after=10, line=1.5)

def callout(doc, text, kind="blue"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.6
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '18')
    left.set(qn('w:space'), '8')
    left.set(qn('w:color'), {'blue': '1F6FEB', 'amber': 'D68910', 'green': '16A085'}[kind])
    pbdr.append(left); pPr.append(pbdr)
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), {'blue': 'EEF4FF', 'amber': 'FFFAF0', 'green': 'ECFAF5'}[kind])
    pPr.append(shd)
    _fill_runs(p, text, 10.5, {'blue': INK, 'amber': AMBER, 'green': RGBColor(0x14, 0x50, 0x3F)}[kind])
    return p

def code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.5
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:fill'), 'F6F8FA')
    pPr.append(shd)
    run = p.add_run(text)
    _set_run(run, size=9, mono=True, color=RGBColor(0x1F, 0x3B, 0x57))
    return p

# ============ 文档初始化 ============
doc = Document()
for s in doc.sections:
    s.top_margin = Cm(2); s.bottom_margin = Cm(2)
    s.left_margin = Cm(2); s.right_margin = Cm(2)

# Normal 样式兜底
normal = doc.styles['Normal']
normal.font.name = FONT
normal.font.size = Pt(10.5)
normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), EAST)

# ============ 标题 ============
t = doc.add_paragraph()
t.paragraph_format.space_after = Pt(4)
run = t.add_run("人群圈选 Agent：让运营用一句话圈人，再证明它圈得准")
_set_run(run, size=20, bold=True, color=DARK)

para(doc, "个人项目 · 2026.09 – 2026.10 · 独立完成 · Python / LangGraph / SQLite / LLM API",
     size=10, color=MUTED, after=2)
para(doc, "对标岗位：AI 产品运营 / 数据产品经理 / 增长产品经理", size=10, color=MUTED, after=10)

# 核心数据卡
m = doc.add_table(rows=2, cols=4)
m.style = 'Table Grid'
vals = ["56.7% → 96.7%", "74.5% → 99.8%", "6 / 6", "32 条"]
labs = ["圈选通过率", "平均 F1", "兜底路由准确率", "分层评测用例"]
for i in range(4):
    c0 = m.rows[0].cells[i]; c0.text = ''
    r0 = c0.paragraphs[0]; r0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run(r0.add_run(vals[i]), size=12.5, bold=True, color=RED)
    shade(c0, "FAFBFD")
    c1 = m.rows[1].cells[i]; c1.text = ''
    r1 = c1.paragraphs[0]; r1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_run(r1.add_run(labs[i]), size=8.5, color=MUTED)
    shade(c1, "FAFBFD")
para(doc, "", size=4, after=6)

# ============ 一、整体思路 ============
h1(doc, "一、这项目到底在做什么")
para(doc, "一句话：**先立起“圈得对不对”的尺子，再谈怎么优化。**")
para(doc, "市面上「用自然语言查数据」的工具不少，但大多数只解决“能不能跑起来”，没几个认真回答“到底准不准”。我一开始也是自己看着结果打分，写了个“准确率 88%”。后来一想，这数字站不住：**裁判是我自己，别人凭什么信？**")
para(doc, "所以我干脆把整个项目的重心，从“做个 Agent”换成了“@@搭一套能复现的评测@@”。做法是：给每条测试需求提前写好标准答案 SQL，让 Agent 跑出来的结果去和标准答案比，用集合重合度算分。这样谁都能重跑一遍验证，分数是算出来的，不是拍脑袋拍出来的。")
callout(doc, "我在这项目里最看重的一次判断：自评准确率没说服力，能被人复现的评测才有。为此我宁可把 Agent 功能做得简单一点。")

h2(doc, "五步走下来")
table(doc, ["步骤", "做了什么"],
      [["**1 先定尺子**", "参考 SQL 跑出的标准人群包当答案，集合比对算 P / R / F1"],
       ["**2 搭评测**", "32 条分层用例，指标全自动，零人工打分"],
       ["**3 拆开看**", "按难度层拆通过率，直接看出短板在哪类需求"],
       ["**4 改 Prompt**", "3 版对照实验，每版只补上一版的洞"],
       ["**5 包成产品**", "把最优引擎封成一个能用的圈选工具"]],
      widths=[3.2, 13.4])

# ============ 二、背景 ============
h1(doc, "二、为什么做它")
para(doc, "电商运营每天都在“圈人”：短信召回、优惠券定向、个性化推送，都得先从几千万用户里把目标人群挑出来，比如“近 30 天加购没下单的高价值用户”“流失预警的美妆用户”。")
para(doc, "但圈人一直有两道坎：")
table(doc, ["痛点", "具体表现", "结果"],
      [["**门槛高**", "要么自己会写 SQL，要么排队等 BI 出数", "需求响应慢，运营卡在“提数”上"],
       ["**口径乱**", "“活跃”“老客”“高潜”这些黑话，各人理解不一样", "圈出来的不是同一批人，投放没法比"]],
      widths=[2.6, 9.0, 5.0])
para(doc, "大模型能把一句话准确翻译成 SQL，让不会写代码的同事也能圈人。但新问题来了：**模型生成的结果对不对？** 如果没人能证明它的准确率，上线后每一次圈错，都是真金白银的投放浪费。")
callout(doc, "所以我给项目定了两层目标：① 做一个“一句话圈人”的工具；② 更关键的，搭一套评测把准确率量化出来，优化到可信。", kind="amber")

# ============ 三、问题与优化点 ============
h1(doc, "三、问题怎么定的、优化点怎么挖的")
h2(doc, "先重新定义问题")
para(doc, "最开始我图省事，自己看着结果打分。后来发现不对，把核心问题重新定义成一句话：")
callout(doc, "怎么在不靠人工打分的前提下，客观、可复现地度量“自然语言 → 人群包”这条链路的准确率，并据此找到短板？")
para(doc, "解法就是前面说的“标准答案当裁判”：")
table(doc, ["要素", "我用的做法"],
      [["**标准答案**", "每条圈选需求预先写好参考 SQL，跑出“标准人群包”"],
       ["**怎么比**", "Agent 的结果和标准答案做集合重合度比对"],
       ["**算分指标**", "Precision（查准）、Recall（查全）、F1（综合）"],
       ["**通过线**", "F1 ≥ 0.95 算通过，全程无人工打分"]],
      widths=[3.2, 13.4])

h2(doc, "怎么找到该改的地方")
para(doc, "只看一个总通过率，等于没信息。我把它拆成三层看：")
table(doc, ["层级", "回答什么", "它帮我发现了什么"],
      [["**① 总通过率**", "整体好不好", "基础版只有 56.7%，明显不能用"],
       ["**② 分层通过率**", "短板在哪类需求", "矛盾层 0%、歧义层 33.3%，是硬伤"],
       ["**③ Bad case 归因**", "为什么会错", "锁定四类错误，直接指导改 Prompt"]],
      widths=[3.4, 4.4, 8.8])
callout(doc, "最值钱的是第 ② 层。只有把通过率按难度拆开，才发现不同版本短板完全不一样：基础版在“矛盾需求”上是 0%（它把 AND 擅自改成了 OR），加了角色和示例之后矛盾层解决了，但“歧义口径”还卡在 33.3%。不拆层，我根本不知道该往哪改。", kind="green")

h2(doc, "四类典型错误，对应四类改法")
table(doc, ["归因类型", "典型需求", "错在哪", "怎么改"],
      [["**条件遗漏**", "近30天加购未下单的**高价值**用户", "漏了 is_high_value", "用 Few-Shot 补组合场景"],
       ["**口径偏差**", "“活跃用户”", "猜成“高价值用户”", "注入业务口径词典"],
       ["**时间口径错**", "近 7 天活跃", "窗口天数 / 基准日算错", "显式规定基准日锚点"],
       ["**矛盾处理错**", "年龄<18 且>60", "AND 改成 OR，人群膨胀", "规则：矛盾按字面生成，空集即正确"]],
      widths=[3.2, 5.0, 4.6, 3.8])

# ============ 四、架构 ============
h1(doc, "四、架构长什么样")
para(doc, "整体分三层，依赖方向是单向的：产品层 → 引擎层 → 数据层。引擎层完全不感知产品层，所以评测引擎能被产品层零改动复用，也能单独跑回归。")
picture(doc, os.path.join(ASSETS, "arch.png"))
caption(doc, "图　三层架构：产品层（用户可感知）→ 引擎层（核心编排）→ 数据层（数据底座）")

h2(doc, "三个技术取舍（面试常问）")
table(doc, ["决策", "选了", "为什么"],
      [["**Router 前置，不用 ReAct**", "先路由、后生成", "圈选是模式化任务，入口先判意图（圈选还是闲聊）更可控、幻觉少"],
       ["**表结构注入，不上 RAG**", "全文塞进 Prompt", "单表 17 字段才几千 token；上千张表才需要向量检索，硬上反而多一个失败源"],
       ["**自愈重试带上限**", "最多 2 次", "报错回传给模型修正很有用，但不设上限可能“越改越错”死循环"]],
      widths=[4.6, 3.2, 8.8])

# ============ 五、引擎 + 功能点 ============
h1(doc, "五、引擎内部与功能点")
h2(doc, "引擎内部：四节点状态机")
para(doc, "把“需求 → 人群包”拆成四个职责单一的节点，自愈循环用条件边表达，而不是写死 if/else，链路可回溯、可观测。")
picture(doc, os.path.join(ASSETS, "langgraph.png"))
caption(doc, "图　LangGraph 图结构：路由 → 生成 SQL → 执行 → 自愈（失败且重试<2 次回到生成）")

h2(doc, "产品层提供了 7 个功能")
for f in [
    ("自然语言圈选", "一句话进去，自动走完“路由 → 生成 SQL → 执行 → 自愈”，出来一份名单"),
    ("意图路由兜底", "识别圈选和闲聊，闲聊直接给话术，不硬生成 SQL，防幻觉"),
    ("SQL 透明可核对", "默认折叠，运营不关心、分析师要看，折叠兼顾两类人"),
    ("自愈重试", "执行报错自动把错误喂给模型修正，实测能修字段拼写错误"),
    ("人群画像", "圈完立刻看到性别 / 城市 / 会员 / 品类分布，先验一下圈得对不对"),
    ("名单导出 CSV", "一键导出完整名单（带 BOM，Excel 直开不乱码）"),
    ("圈选历史", "自动留痕，点一下回看完整结果，方便复盘复跑"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.3)
    _set_run(p.add_run("• "), size=10.5, color=BLUE)
    _set_run(p.add_run(f[0] + "　——　"), size=10.5, bold=True, color=DARK)
    _set_run(p.add_run(f[1]), size=10.5, color=INK)

# ============ 六、用户流程 ============
h1(doc, "六、用户怎么走完一圈")
para(doc, "主流程六步：输入需求 → 意图路由 → 生成 SQL → 执行 → 结果卡 → 导出 / 回看。中间两个分支都做了兜底：非圈选 → 兜底话术；执行失败 → 自愈重试 ≤2 次。")
picture(doc, os.path.join(ASSETS, "flow.png"))
caption(doc, "图　主流程与两个异常分支（兜底话术 / 自愈重试）")
h2(doc, "一次圈选背后的数据流转")
code(doc, "POST /api/select\n  → history.save() 占位拿 record_id\n  → graph_flow.answer() 跑 LangGraph（路由 → 生成SQL → 执行 → 自愈≤2）\n  → profile.stats() 出人群画像   → history.update() 回填结果\n  → 组装 JSON → 前端渲染结果卡")
para(doc, "业务库和历史库分开（audience.db / history.db），业务库重建时历史不受影响；引擎报错也不抛 500，而是把失败原因当结果返回给用户——失败原因本身也是要展示的信息。", size=9.5, color=MUTED)

# ============ 七、原型 ============
h1(doc, "七、原型长啥样")
para(doc, "做了个能直接跑的 Web 原型（FastAPI + 原生 JS，没构建步骤），界面走浅色业务工具风。下面是还原实际界面的示意：")
picture(doc, os.path.join(ASSETS, "mockup.png"))
caption(doc, "图　原型界面：顶部状态栏 + 输入区 + 结果卡（人数 / SQL / 画像 / 名单）+ 侧栏圈选历史")
h2(doc, "几个设计上的小决定")
table(doc, ["设计点", "为什么这么定"],
      [["**SQL 默认折叠**", "运营不关心 SQL，分析师要核对，折叠刚好兼顾两类人"],
       ["**画像用条形图**", "圈完第一反应是“这群人长什么样”，图比数字直观"],
       ["**名单只预览前 50 条**", "避免几千行卡死页面，完整名单走导出"],
       ["**结果内联在主区**", "方便连续圈选、对比前后结果"],
       ["**侧栏历史可回看**", "复盘和复跑方便，减少重复劳动"]],
      widths=[4.6, 12.0])

# ============ 八、效果 ============
h1(doc, "八、最后效果怎么样")
para(doc, "把 Prompt 拆成三版做对照实验，每一版只加一类东西，这样收益能精确归因，而不是笼统一句“优化了”。")

para(doc, "@@56.7% → 96.7%@@ 通过率　　@@74.5% → 99.8%@@ 平均 F1　　@@6 / 6@@ 兜底路由",
     size=12, align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=8)

picture(doc, os.path.join(CHARTS, "eval_versions.png"))
caption(doc, "图 1　三版 Prompt 的任务完成率、平均 F1、通过率对比")
table(doc, ["版本", "加了什么", "通过率", "平均 F1", "主要短板"],
      [["V1 基础版", "只有表结构", "56.7%", "74.5%", "矛盾层 0%、组合层 37.5%"],
       ["V2 角色 + Few-Shot", "角色设定 + 2 个示例 + 口径词典", "86.7%", "93.8%", "歧义层仍是 33.3%"],
       ["V3 规则约束版", "再加 6 条生成规则", "**96.7%**", "**99.8%**", "仅时间层 83.3%"]],
      widths=[3.6, 5.6, 2.4, 2.4, 3.4])
para(doc, "每一版加的东西，都是上一版暴露的短板逼出来的。“角色 + Few-Shot”贡献主要提升，“规则约束”补齐了矛盾处理和口径边界。", size=9.5, color=MUTED)

h2(doc, "分层通过率：拆开看，短板才露出来")
picture(doc, os.path.join(CHARTS, "eval_by_level.png"))
caption(doc, "图 2　按难度层拆开的通过率。基础版在“矛盾”层是 0，“歧义”层 33.3%，一眼定位问题")
table(doc, ["难度层", "V1 基础版", "V2 角色+Few-Shot", "V3 规则约束版"],
      [["简单（10 条）", "100%", "100%", "100%"],
       ["组合（8 条）", "37.5%", "75%", "**100%**"],
       ["时间窗口（6 条）", "50%", "100%", "83.3%"],
       ["歧义口径（3 条）", "33.3%", "33.3%", "**100%**"],
       ["矛盾需求（3 条）", "0%", "100%", "**100%**"]],
      widths=[5.0, 3.6, 4.0, 4.0])
callout(doc, "关键洞察：“歧义口径”（业务黑话）只靠词典注入没用，得配“必须查词典、不得自己猜”这条显式规则，才从 33.3% 收敛到 100%。这说明“给模型的信息”和“给模型的约束”是两码事。", kind="amber")

h2(doc, "Bad case 归因：四类错误全沉淀进模板")
picture(doc, os.path.join(CHARTS, "eval_badcases.png"))
caption(doc, "图 3　未通过用例的归因分布。自愈也实测过：字段拼写错误被自动触发并修复，兜底路由 6/6")

h2(doc, "复盘：做完这个项目，我最想说的三句话")
para(doc, "**① 评测设计比功能实现值钱。** 写 Agent 大概花了三成时间，剩下七成都在想“怎么证明它对”。做完我更能理解为什么大模型团队都在死磕评测集——没有评测，优化全靠感觉，改十版也不知道是进步还是退步。")
para(doc, "**② “准确率”必须能拆开。** 只报一个总数字没信息量。我现在的做法是三层看：总通过率看整体、分层通过率看短板、Bad case 归因看原因。三层里，分层性价比最高——它直接把“该改什么”指出来了。")
para(doc, "**③ 模型的失败常常不是报错，是“看着合理其实错了”。** 比如把 AND 擅自改成 OR、把“活跃”猜成“高价值”，这些 SQL 都能执行成功，结果却全错。最隐蔽的错误往往最值钱。")

h2(doc, "如果继续做，下一步是什么")
table(doc, ["方向", "具体做什么"],
      [["**换真实模型重跑**", "接 DeepSeek Key 把离线演示的数字换成真实结果"],
       ["**扩评测集**", "从 32 条扩到 100+，尤其补歧义、矛盾两层，96.7% 的置信度还不够高"],
       ["**加人工复核**", "机器判错的地方人工再过一遍，确认不是标准答案本身写错了"]],
      widths=[4.0, 12.6])
callout(doc, "一句话收尾：这个项目的核心不是“做了一个圈选工具”，而是“建立了一套能证明它准不准、并且能一直把它改得更准的办法”。", kind="green")

doc.save(OUT)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
