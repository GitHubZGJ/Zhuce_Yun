"""构建《软件工程大作业报告》Word 文档。

以 docs/ 下的 Markdown 为单一内容源，转换为带封面、摘要、目录、页码、
图表标题和规范表格的 DOCX。
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "deliverable" / "软件工程大作业报告.docx"

NAVY = RGBColor(0x12, 0x3A, 0x57)
NAVY_LIGHT = RGBColor(0x1D, 0x4A, 0x6B)
ACCENT = RGBColor(0xC0, 0x6A, 0x3C)
GOLD = RGBColor(0xD9, 0xA4, 0x41)
MUTED = RGBColor(0x6C, 0x77, 0x7E)
INK = RGBColor(0x22, 0x30, 0x3A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEADER_FILL = "123A57"
ALT_FILL = "FAF7F0"
BORDER = "D8D0C1"

BODY_SIZE = 12
CONTENT_WIDTH_CM = 16.4
FONT_CN = "宋体"
FONT_EN = "Times New Roman"
FONT_HEAD_CN = "黑体"
FONT_HEAD_EN = "Arial"
FONT_CODE = "Consolas"

CHAPTERS = [
    ("项目概述", "项目背景、范围与关键结果", "00_摘要与项目概述.md"),
    ("可行性分析", "对应作业要求 2(1) · 五维雷达图与可行性文档", "01_可行性分析报告.md"),
    ("需求分析", "对应作业要求 2(2) · 用例图、用户需求与开发需求", "02_需求规格说明书.md"),
    ("总体设计", "对应作业要求 2(3) · 系统架构图与总体设计说明", "03_总体设计说明书.md"),
    ("详细设计", "对应作业要求 2(4) · UML 类图、接口、算法与异常", "04_详细设计说明书.md"),
    ("实现与测试", "对应作业要求 2(5) · 程序流程图与测试设计", "05_实现与测试说明.md"),
    ("维护与 Agent 失效复盘", "对应作业要求 2(6) · 缺陷帕累托、失效评分与修改说明", "06_维护与Agent失效复盘.md"),
    ("AI 分级机制", "对应作业要求第 3 条 · L1/L2/L3 任务拆分", "07_AI分级机制表.md"),
    ("评级监管设计", "对应作业要求第 4 条 · Agent 失效评分与监管", "08_评级监管设计说明.md"),
]

APPENDICES = [
    ("附录 A 演示与答辩脚本", "现场演示流程、话术与故障兜底", "09_演示与答辩脚本.md"),
    ("附录 B 交付物清单", "作业要求逐条对照与证据路径", "10_交付物清单.md"),
    ("附录 C 项目实施基线", "架构基线与里程碑", "99_项目实施方案.md"),
]

FIGURE_COUNTER = 0


# ---------------------------------------------------------------------------
# 基础排版工具
# ---------------------------------------------------------------------------
PARA_AFTER_BORDER = (
    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)
TC_AFTER_SHADING = (
    "w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign",
    "w:hideMark", "w:headers", "w:cellIns", "w:cellDel", "w:cellMerge",
    "w:tcPrChange",
)
TC_AFTER_MARGINS = (
    "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark", "w:headers",
    "w:cellIns", "w:cellDel", "w:cellMerge", "w:tcPrChange",
)


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.insert_element_before(shd, *TC_AFTER_SHADING)


def set_paragraph_shading(paragraph, fill):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.insert_element_before(shd, *PARA_AFTER_BORDER[1:])


def set_paragraph_border(paragraph, color=BORDER, size=6, space=2, sides=("bottom",)):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.insert_element_before(p_bdr, *PARA_AFTER_BORDER)
    for side in sides:
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), str(space))
        element.set(qn("w:color"), color)
        p_bdr.append(element)


def set_run_font(run, size=BODY_SIZE, bold=False, color=INK, cn=FONT_CN, en=FONT_EN, italic=False):
    run.font.name = en
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), en)
    r_fonts.set(qn("w:hAnsi"), en)
    r_fonts.set(qn("w:eastAsia"), cn)


def set_style_font(style, size, bold=False, color=INK, cn=FONT_CN, en=FONT_EN):
    style.font.name = en
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = color
    r_pr = style.element.get_or_add_rPr()
    r_fonts = r_pr.find(qn("w:rFonts"))
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), en)
    r_fonts.set(qn("w:hAnsi"), en)
    r_fonts.set(qn("w:eastAsia"), cn)


def add_field(paragraph, instruction, placeholder="", size=9, color=MUTED):
    def add_char(kind):
        run = paragraph.add_run()
        char = OxmlElement("w:fldChar")
        char.set(qn("w:fldCharType"), kind)
        run._r.append(char)
        set_run_font(run, size=size, color=color)

    add_char("begin")

    run = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    run._r.append(instr)
    set_run_font(run, size=size, color=color)

    add_char("separate")

    if placeholder:
        run = paragraph.add_run(placeholder)
        set_run_font(run, size=size, color=color)

    add_char("end")


def add_inline(paragraph, text, size=BODY_SIZE, bold=False, color=INK, cn=FONT_CN, en=FONT_EN):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    pattern = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")
    for part in pattern.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            set_run_font(run, size=size, bold=True, color=color, cn=cn, en=en)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=max(size - 1, 8), color=RGBColor(0x6B, 0x4F, 0x3A), cn=cn, en=FONT_CODE)
            r_pr = run._element.get_or_add_rPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear")
            shd.set(qn("w:color"), "auto")
            shd.set(qn("w:fill"), "F4EFE4")
            r_pr.append(shd)
        else:
            run = paragraph.add_run(part)
            set_run_font(run, size=size, bold=bold, color=color, cn=cn, en=en)


def setup_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.header_distance = Cm(1.2)
    section.footer_distance = Cm(1.2)

    normal = doc.styles["Normal"]
    set_style_font(normal, BODY_SIZE, color=INK)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.first_line_indent = Pt(BODY_SIZE * 2)

    heading_specs = {
        "Heading 1": (18, NAVY, 18, 10),
        "Heading 2": (15, NAVY, 14, 6),
        "Heading 3": (13, NAVY_LIGHT, 12, 4),
        "Heading 4": (12, NAVY_LIGHT, 10, 3),
    }
    for style_name, (size, color, before, after) in heading_specs.items():
        style = doc.styles[style_name]
        set_style_font(style, size, bold=True, color=color, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.first_line_indent = Pt(0)
        style.paragraph_format.line_spacing = 1.25
        style.paragraph_format.keep_with_next = True

    doc.core_properties.title = "软件工程大作业报告 · 筑测云"
    doc.core_properties.subject = "工程检测数据管理平台"
    doc.core_properties.author = "软件工程大作业"
    doc.core_properties.comments = "由 Markdown 文档自动生成，数据截至 2026-11-06"
    return doc


# ---------------------------------------------------------------------------
# 封面、目录、页眉页脚
# ---------------------------------------------------------------------------
def add_cover(doc):
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("S O F T W A R E   E N G I N E E R I N G   ·   2 0 2 6")
    set_run_font(run, size=9, bold=True, color=ACCENT, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    set_paragraph_border(p, color="D9A441", size=13, space=1)
    run = p.add_run(" ")
    set_run_font(run, size=2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run("软件工程大作业报告")
    set_run_font(run, size=34, bold=True, color=NAVY, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("筑测云——工程检测数据管理平台")
    set_run_font(run, size=20, bold=True, color=ACCENT, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(30)
    run = p.add_run("生成式软件工程全流程实践与 AI 协作治理")
    set_run_font(run, size=12.5, color=MUTED, cn=FONT_CN, en=FONT_EN)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("项目 · 样品 · 检测 · 看板 · AI 分级 · 失效评分 · 维护复盘")
    set_run_font(run, size=10.5, color=MUTED, cn=FONT_CN, en=FONT_EN)
    p.paragraph_format.space_after = Pt(20)

    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    labels = ["姓    名", "学    号", "班    级", "指导教师", "完成日期"]
    values = ["________________", "________________", "________________", "________________", "2026 年 11 月 6 日"]
    for index, (label, value) in enumerate(zip(labels, values)):
        row = table.rows[index]
        for cell, text, bold in ((row.cells[0], label, True), (row.cells[1], value, False)):
            cell.width = Cm(5.2)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            para = cell.paragraphs[0]
            para.paragraph_format.space_after = Pt(7)
            para.paragraph_format.first_line_indent = Pt(0)
            run = para.add_run(text)
            set_run_font(run, size=12.5 if bold else 12, bold=bold, color=NAVY if bold else INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    metrics = doc.add_table(rows=1, cols=4)
    metrics.alignment = WD_TABLE_ALIGNMENT.CENTER
    metrics.autofit = False
    metric_data = [("6", "工程项目"), ("60", "检测记录"), ("24", "AI 任务"), ("85.3", "AI 可靠性")]
    for index, (number, label) in enumerate(metric_data):
        cell = metrics.rows[0].cells[index]
        cell.width = Cm(3.6)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(2)
        para.paragraph_format.first_line_indent = Pt(0)
        run = para.add_run(number)
        set_run_font(run, size=16, bold=True, color=NAVY, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)
        para2 = cell.add_paragraph()
        para2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para2.paragraph_format.space_after = Pt(0)
        para2.paragraph_format.first_line_indent = Pt(0)
        run2 = para2.add_run(label)
        set_run_font(run2, size=9, color=MUTED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    run = p.add_run("软件工程课程大作业 · 2026 年 11 月")
    set_run_font(run, size=10, color=MUTED)


def setup_body_section(doc):
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.3)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.header_distance = Cm(1.2)
    section.footer_distance = Cm(1.2)

    # 页码从正文开始
    sect_pr = section._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is None:
        pg_num = OxmlElement("w:pgNumType")
        sect_pr.insert_element_before(
            pg_num,
            "w:cols", "w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
            "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
            "w:printerSettings", "w:sectPrChange",
        )
    pg_num.set(qn("w:start"), "1")

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.text = ""
    hp.paragraph_format.space_after = Pt(2)
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(CONTENT_WIDTH_CM), WD_TAB_ALIGNMENT.RIGHT)
    run = hp.add_run("筑测云 · 工程检测数据管理平台")
    set_run_font(run, size=9, color=MUTED)
    run = hp.add_run("\t软件工程大作业报告 · 2026")
    set_run_font(run, size=9, color=MUTED)
    set_paragraph_border(hp, color="D8D0C1", size=6, space=2)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(2)
    run = fp.add_run("第 ")
    set_run_font(run, size=9, color=MUTED)
    add_field(fp, "PAGE", "1")
    run = fp.add_run(" 页 / 共 ")
    set_run_font(run, size=9, color=MUTED)
    add_field(fp, "NUMPAGES", "1")
    run = fp.add_run(" 页")
    set_run_font(run, size=9, color=MUTED)

    settings = doc.settings.element
    zoom = settings.find(qn("w:zoom"))
    if zoom is not None:
        zoom.set(qn("w:percent"), "100")
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.insert_element_before(
        update_fields,
        "w:hdrShapeDefaults", "w:footnotePr", "w:endnotePr", "w:compat",
        "w:docVars", "w:rsids", "m:mathPr", "w:attachedSchema",
        "w:themeFontLang", "w:clrSchemeMapping", "w:doNotIncludeSubdocsInStats",
        "w:doNotAutoCompressPictures", "w:shapeDefaults", "w:decimalSymbol",
        "w:listSeparator",
    )


def add_abstract(doc):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 1"]
    run = p.add_run("摘要")
    set_run_font(run, size=18, bold=True, color=NAVY, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)
    p.paragraph_format.page_break_before = False
    set_paragraph_border(p, color="D9A441", size=9, space=3)

    lines = (DOCS / "00_摘要与项目概述.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "## 摘要")
    end = next(i for i, line in enumerate(lines) if line.strip() == "## 1 项目概述")
    keywords = ""
    for line in lines[start + 1 : end]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("关键词"):
            keywords = stripped.split("：", 1)[-1]
            continue
        add_body_paragraph(doc, stripped, first_indent=True)

    if keywords:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.first_line_indent = Pt(0)
        run = p.add_run("关键词：")
        set_run_font(run, size=12, bold=True, color=NAVY, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)
        run = p.add_run(keywords)
        set_run_font(run, size=12, color=INK)


def add_toc(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(16)
    run = p.add_run("目  录")
    set_run_font(run, size=18, bold=True, color=NAVY, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)

    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-2" \\h \\z \\u', "目录将在 Word 中自动生成")
    p.paragraph_format.space_after = Pt(8)

    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.first_line_indent = Pt(0)
    run = note.add_run("（若目录未显示页码，请在 Word 中右键“更新域”或按 Ctrl+A、F9 更新）")
    set_run_font(run, size=9, color=MUTED)


# ---------------------------------------------------------------------------
# 正文渲染
# ---------------------------------------------------------------------------
def add_body_paragraph(doc, text, first_indent=True, size=BODY_SIZE, color=INK, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Pt(size * 2) if first_indent else Pt(0)
    add_inline(p, text, size=size, color=color)
    return p


def add_heading(doc, text, level):
    p = doc.add_paragraph(style=f"Heading {level}")
    run = p.add_run(text)
    size, color = {
        1: (18, NAVY),
        2: (15, NAVY),
        3: (13, NAVY_LIGHT),
        4: (12, NAVY_LIGHT),
    }[level]
    set_run_font(run, size=size, bold=True, color=color, cn=FONT_HEAD_CN, en=FONT_HEAD_EN)
    p.paragraph_format.page_break_before = level == 1
    if level == 1:
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(10)
        set_paragraph_border(p, color="D9A441", size=8, space=3)
    return p


def add_chapter(doc, title, subtitle):
    add_heading(doc, title, 1)
    if subtitle:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(subtitle)
        set_run_font(run, size=10.5, color=MUTED, italic=True)
        set_paragraph_border(p, color="EFE8DA", size=4, space=2)


def add_list_item(doc, text, numbered=False, number=None):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.45
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.4)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if numbered:
        prefix = f"{number}. " if number else ""
        add_inline(p, prefix + text, size=BODY_SIZE)
    else:
        p.style = doc.styles["List Bullet"]
        p.paragraph_format.left_indent = Cm(0.74)
        p.paragraph_format.first_line_indent = Cm(-0.4)
        add_inline(p, text, size=BODY_SIZE)


def add_quote(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.35
    add_inline(p, text, size=10.5, color=MUTED, cn=FONT_CN, en=FONT_EN)
    set_paragraph_border(p, color="D8D0C1", size=6, space=4, sides=("left",))


def add_code_block(doc, lines):
    if not lines:
        return
    for index, line in enumerate(lines):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.right_indent = Cm(0.3)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.keep_with_next = index < len(lines) - 1
        set_paragraph_shading(p, "F5F2EA")
        run = p.add_run(line if line else " ")
        set_run_font(run, size=8.8, color=RGBColor(0x3A, 0x45, 0x4D), cn=FONT_CN, en=FONT_CODE)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.first_line_indent = Pt(0)


def compute_col_widths(rows, total_cm=CONTENT_WIDTH_CM):
    cols = len(rows[0])
    lengths = []
    for col in range(cols):
        values = []
        for row in rows[:30]:
            if col < len(row):
                values.append(len(re.sub(r"[*`<br>]", "", row[col])))
        lengths.append(max(values) if values else 4)
    weights = [max(4, min(38, value)) ** 0.82 for value in lengths]
    total_weight = sum(weights)
    widths = [max(1.15, total_cm * weight / total_weight) for weight in weights]
    scale = total_cm / sum(widths)
    return [width * scale for width in widths]


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), BORDER)
        borders.append(element)
    tbl_pr.insert_element_before(
        borders,
        "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
        "w:tblCaption", "w:tblDescription", "w:tblPrChange",
    )


def set_cell_margins(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for side, value in (("top", 60), ("left", 90), ("bottom", 60), ("right", 90)):
        element = OxmlElement(f"w:{side}")
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")
        mar.append(element)
    tc_pr.insert_element_before(mar, *TC_AFTER_MARGINS)


def add_md_table(doc, rows):
    if not rows:
        return
    ncols = max(len(row) for row in rows)
    normalized = []
    for row in rows:
        normalized.append(row + [""] * (ncols - len(row)))
    rows = normalized

    font_size = 10 if ncols <= 3 else 9.2 if ncols <= 5 else 8.4 if ncols <= 7 else 7.8
    header_size = font_size + 0.4
    widths = compute_col_widths(rows)

    table = doc.add_table(rows=len(rows), cols=ncols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    for index, width in enumerate(widths):
        table.columns[index].width = Cm(width)

    for r_index, row in enumerate(rows):
        tr_pr = table.rows[r_index]._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)
        if r_index == 0:
            header = OxmlElement("w:tblHeader")
            tr_pr.append(header)
        for c_index, value in enumerate(row):
            cell = table.cell(r_index, c_index)
            cell.width = Cm(widths[c_index])
            set_cell_margins(cell)
            if r_index == 0:
                set_cell_shading(cell, HEADER_FILL)
            elif r_index % 2 == 0:
                set_cell_shading(cell, ALT_FILL)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            cell.paragraphs[0].text = ""
            segments = re.split(r"<br\s*/?>", value) if value else [""]
            for s_index, segment in enumerate(segments):
                para = cell.paragraphs[0] if s_index == 0 else cell.add_paragraph()
                para.paragraph_format.first_line_indent = Pt(0)
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = 1.15
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER if r_index == 0 else WD_ALIGN_PARAGRAPH.LEFT
                add_inline(
                    para,
                    segment,
                    size=header_size if r_index == 0 else font_size,
                    bold=r_index == 0,
                    color=WHITE if r_index == 0 else INK,
                )

    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(2)
    spacer.paragraph_format.first_line_indent = Pt(0)


def add_figure(doc, path, alt):
    global FIGURE_COUNTER
    path = (DOCS / path).resolve()
    if not path.exists():
        print("missing image:", path)
        return
    with Image.open(path) as image:
        width_px, height_px = image.size
    width_cm = 15.4 if "evidence/ui" in path.as_posix() else CONTENT_WIDTH_CM
    height_cm = width_cm * height_px / width_px
    if height_cm > 20.5:
        height_cm = 20.5
        width_cm = height_cm * width_px / height_px

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width_cm))

    FIGURE_COUNTER += 1
    caption = doc.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.first_line_indent = Pt(0)
    caption.paragraph_format.space_before = Pt(0)
    caption.paragraph_format.space_after = Pt(8)
    run = caption.add_run(f"图 {FIGURE_COUNTER}  {alt}")
    set_run_font(run, size=9, color=MUTED)


def is_table_separator(line):
    return bool(re.fullmatch(r"\|?[\s:\-|]+\|?", line.strip())) and "-" in line


def parse_table(lines, start):
    rows = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        line = lines[index].strip()
        if not is_table_separator(line):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows.append(cells)
        index += 1
    return rows, index


def render_markdown(doc, path, heading_shift=0, start_marker=None, skip_headings=()):
    lines = (DOCS / path).read_text(encoding="utf-8").splitlines()
    index = 0
    if start_marker:
        index = next(i for i, line in enumerate(lines) if line.strip() == start_marker) + 1

    first_heading_skipped = False
    in_code = False
    code_lines = []

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if in_code:
            if stripped.startswith("```"):
                add_code_block(doc, code_lines)
                code_lines = []
                in_code = False
            else:
                code_lines.append(raw.rstrip())
            index += 1
            continue

        if stripped.startswith("```"):
            in_code = True
            code_lines = []
            index += 1
            continue

        if not stripped:
            index += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            if level == 1:
                if not first_heading_skipped:
                    first_heading_skipped = True
                    index += 1
                    # 跳过文档标题后的空行与元数据引用
                    while index < len(lines) and (
                        not lines[index].strip() or lines[index].strip().startswith(">")
                    ):
                        index += 1
                    continue
                target_level = 1
            else:
                if text in skip_headings:
                    index += 1
                    continue
                target_level = max(2, min(4, level + heading_shift))
            add_heading(doc, text, target_level)
            index += 1
            continue

        if stripped == "---":
            index += 1
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if image:
            add_figure(doc, image.group(2), image.group(1) or "示意图")
            index += 1
            continue

        if stripped.startswith("|"):
            rows, index = parse_table(lines, index)
            if rows:
                add_md_table(doc, rows)
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet:
            add_list_item(doc, bullet.group(1), numbered=False)
            index += 1
            continue

        numbered = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if numbered:
            add_list_item(doc, numbered.group(2), numbered=True, number=numbered.group(1))
            index += 1
            continue

        if stripped.startswith(">"):
            add_quote(doc, stripped.lstrip(">").strip())
            index += 1
            continue

        add_body_paragraph(doc, stripped)
        index += 1

    if in_code and code_lines:
        add_code_block(doc, code_lines)


def add_summary(doc):
    add_chapter(doc, "总结与展望", "项目完成情况、经验与后续计划")
    paragraphs = [
        "本项目完成了从可行性、需求、总体设计、详细设计、实现测试到维护复盘的全流程交付。系统以工程检测业务为场景，实现了项目、样品、检测记录、自动判定、质量看板与用户权限的闭环；同时把 AI 分级、失效评分与可靠性统计做进系统，使 AI 协作过程可追溯、可量化、可复盘。",
        "交付结果包括可运行的前后端与 SQLite 数据库、Alembic 迁移、演示数据、56 个后端测试、Edge 端到端验证、8 张工程图表与全套文档。看板数据为 6 个项目、24 个样品、60 条检测记录，合格率 85.0%；AI 台账为 24 项任务，综合可靠性 85.3，4 项高失效任务完成复盘；缺陷台账累计 68 次，前四类占 76.5%。这些数字在页面、图表和文档中保持一致。",
        "项目最重要的经验是：AI 产出必须绑定验收门禁与责任边界。L1 任务可以自动执行，但人必须定义规则并抽检；L2 任务需要逐项复核；L3 任务由人决策与签字。失效评分让返工成本显性化，避免“能跑就算完成”的假象。实现与测试阶段只有 62.8 分，正好说明联调与部署环节最需要人审与契约约束。",
        "下一阶段计划包括：补齐检测记录重复提交拦截与错误码映射；引入刷新令牌、审计日志与更严格的权限矩阵；把 CI、测试、E2E 与评分证据自动关联；用 PostgreSQL 替换 SQLite；扩充 AI 评分样本并计算评分者一致性。系统将保持 Demo 可复现性，同时逐步向真实项目可用的工程质量靠拢。",
    ]
    for text in paragraphs:
        add_body_paragraph(doc, text)


def add_table_heading_note(doc):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    run = p.add_run("说明：本报告由项目文档与运行数据自动汇总生成，图表与统计数据截至 2026-11-06。")
    set_run_font(run, size=9.5, color=MUTED)


def build():
    global FIGURE_COUNTER
    FIGURE_COUNTER = 0
    doc = setup_document()
    add_cover(doc)
    setup_body_section(doc)
    add_abstract(doc)
    add_toc(doc)

    for title, subtitle, filename in CHAPTERS:
        if title == "项目概述":
            add_chapter(doc, title, subtitle)
            render_markdown(
                doc,
                filename,
                heading_shift=-1,
                start_marker="## 1 项目概述",
                skip_headings=("摘要", "1 项目概述"),
            )
        else:
            add_chapter(doc, title, subtitle)
            render_markdown(doc, filename)

    add_summary(doc)

    for title, subtitle, filename in APPENDICES:
        add_chapter(doc, title, subtitle)
        render_markdown(doc, filename)

    add_table_heading_note(doc)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print("saved", OUT)
    print("figures", FIGURE_COUNTER)
    print("paragraphs", len(doc.paragraphs), "tables", len(doc.tables))


if __name__ == "__main__":
    build()
