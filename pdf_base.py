# -*- coding: utf-8 -*-
"""Base de estilo (paleta Claude) e builder de PDF com sumário."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ---- Paleta Claude ----
CORAL   = colors.HexColor("#D97757")
CORAL_D = colors.HexColor("#B14F30")
TINTA   = colors.HexColor("#2B2A27")
CINZA   = colors.HexColor("#6B655C")
CREME   = colors.HexColor("#F5F2EB")
CREME_D = colors.HexColor("#EDE8DD")
LINHA   = colors.HexColor("#D8CFBE")

_S = getSampleStyleSheet()


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("TituloPrincipal", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=17, textColor=CORAL_D, spaceAfter=6,
        leading=21, alignment=TA_CENTER))
    s.add(ParagraphStyle("Subtitulo", parent=s["Normal"], fontName="Helvetica",
        fontSize=11, textColor=TINTA, alignment=TA_CENTER, spaceAfter=4, leading=15))
    s.add(ParagraphStyle("MetaInfo", parent=s["Normal"], fontName="Helvetica",
        fontSize=9.5, textColor=CINZA, alignment=TA_CENTER, spaceAfter=2, leading=13))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], fontName="Helvetica-Bold",
        fontSize=12.5, textColor=CORAL_D, spaceBefore=16, spaceAfter=6, leading=16))
    s.add(ParagraphStyle("H3", parent=s["Heading3"], fontName="Helvetica-Bold",
        fontSize=10.8, textColor=TINTA, spaceBefore=10, spaceAfter=4, leading=14))
    s.add(ParagraphStyle("Corpo", parent=s["Normal"], fontName="Helvetica",
        fontSize=10.5, alignment=TA_JUSTIFY, spaceAfter=8, leading=15, textColor=TINTA))
    s.add(ParagraphStyle("Citacao", parent=s["Normal"], fontName="Helvetica-Oblique",
        fontSize=10, alignment=TA_JUSTIFY, leading=14.5, leftIndent=18, rightIndent=10,
        spaceBefore=2, spaceAfter=8, textColor=TINTA))
    s.add(ParagraphStyle("RotuloFonte", parent=s["Normal"], fontName="Helvetica-Bold",
        fontSize=9.5, textColor=CORAL_D, spaceBefore=4, spaceAfter=1, leading=13))
    s.add(ParagraphStyle("Rodape", parent=s["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.5, textColor=CINZA, alignment=TA_JUSTIFY, leading=12))
    s.add(ParagraphStyle("TOCTitulo", parent=s["Heading1"], fontName="Helvetica-Bold",
        fontSize=14, textColor=CORAL_D, spaceAfter=10))
    s.add(ParagraphStyle("Item", parent=s["Normal"], fontName="Helvetica",
        fontSize=10.5, alignment=TA_JUSTIFY, spaceAfter=5, leading=14.5, textColor=TINTA,
        leftIndent=14, bulletIndent=2))
    s.add(ParagraphStyle("Quesito", parent=s["Normal"], fontName="Helvetica",
        fontSize=10.5, alignment=TA_JUSTIFY, spaceAfter=9, leading=15, textColor=TINTA,
        leftIndent=12))
    return s


class _Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "H2":
            txt = flowable.getPlainText()
            key = "h2-" + "".join(c for c in txt if c.isalnum())[:26]
            self.canv.bookmarkPage(key)
            self.notify("TOCEntry", (0, txt, self.page, key))


def _rodape_factory(legenda):
    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(CREME)
        canvas.rect(0, A4[1] - 0.5 * cm, A4[0], 0.5 * cm, stroke=0, fill=1)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(CINZA)
        canvas.drawString(2 * cm, 1.2 * cm, legenda)
        canvas.drawRightString(19 * cm, 1.2 * cm, "Pág. %d" % doc.page)
        canvas.setStrokeColor(CORAL)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, 1.5 * cm, 19 * cm, 1.5 * cm)
        canvas.restoreState()
    return rodape


def cit(texto, s):
    p = Paragraph(texto, s["Citacao"])
    t = Table([[p]], colWidths=[16.0 * cm])
    t.setStyle(TableStyle([
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, CORAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, -1), CREME),
    ]))
    return t


def make_table(data, colwidths, s):
    cell = ParagraphStyle("cell", parent=s["Normal"], fontName="Helvetica",
                          fontSize=8.6, leading=11.5, textColor=TINTA)
    cellb = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold",
                           textColor=colors.white, fontSize=8.8)
    rows = []
    for i, row in enumerate(data):
        st = cellb if i == 0 else cell
        rows.append([Paragraph(str(c).replace("\n", "<br/>"), st) for c in row])
    t = Table(rows, colWidths=colwidths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CORAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREME_D]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINHA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build(out, titulo, subtitulo, meta_lines, content, legenda, sumario=True):
    """content: lista de tuplas (tipo, *args).
    tipos: H, H3, P, R, Q, ITEM, TBL(data,colw), HR, SP(n), PB"""
    s = styles()
    story = []
    story.append(Spacer(1, 6))
    story.append(Paragraph(titulo, s["TituloPrincipal"]))
    if subtitulo:
        story.append(Paragraph(subtitulo, s["Subtitulo"]))
    story.append(Spacer(1, 8))
    for m in meta_lines:
        story.append(Paragraph(m, s["MetaInfo"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.4, color=CORAL, spaceAfter=12))

    if sumario:
        story.append(Paragraph("Sumário", s["TOCTitulo"]))
        toc = TableOfContents()
        toc.levelStyles = [ParagraphStyle("TOC0", parent=s["Normal"],
            fontName="Helvetica", fontSize=10.5, textColor=TINTA, leading=20, leftIndent=6)]
        toc.dotsMinLevel = 0
        story.append(toc)
        story.append(PageBreak())

    for item in content:
        kind = item[0]
        if kind == "H":
            story.append(Paragraph(item[1], s["H2"]))
        elif kind == "H3":
            story.append(Paragraph(item[1], s["H3"]))
        elif kind == "P":
            story.append(Paragraph(item[1], s["Corpo"]))
        elif kind == "R":
            story.append(Paragraph(item[1], s["RotuloFonte"]))
        elif kind == "Q":
            story.append(cit(item[1], s)); story.append(Spacer(1, 2))
        elif kind == "ITEM":
            story.append(Paragraph("•&nbsp;&nbsp;" + item[1], s["Item"]))
        elif kind == "QUES":
            story.append(Paragraph(item[1], s["Quesito"]))
        elif kind == "TBL":
            story.append(make_table(item[1], item[2], s))
        elif kind == "HR":
            story.append(HRFlowable(width="100%", thickness=0.8, color=CORAL,
                                    spaceBefore=6, spaceAfter=8))
        elif kind == "SP":
            story.append(Spacer(1, item[1]))
        elif kind == "PB":
            story.append(PageBreak())
        elif kind == "RODAPE_NOTE":
            story.append(Paragraph(item[1], s["Rodape"]))

    frame = Frame(2 * cm, 1.8 * cm, A4[0] - 4 * cm, A4[1] - 3.6 * cm, id="main")
    doc = _Doc(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
               topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=titulo, author="NotebookLM")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                       onPage=_rodape_factory(legenda))])
    doc.multiBuild(story)
    return out
