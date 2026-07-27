# -*- coding: utf-8 -*-
"""Converte o recurso (Markdown) em .docx no padrão Legal Design (peca-legal-design.md):
Sitka Text 12 / entrelinha 1,16 / 6 pt entre parágrafos / margens 2 cm /
títulos principais em VERSALETE / subtítulos em negrito / citações longas em Segoe UI 1,08."""
import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = r"C:\Users\alden\.notebooklm\prazos\RECURSO_PLENARIO_0000303-28.2026.2.00.0810.md"
OUT = r"C:\Users\alden\.notebooklm\prazos\RECURSO_PLENARIO_0000303-28.2026.2.00.0810.docx"

BODY_FONT = "Sitka Text"
QUOTE_FONT = "Segoe UI"
SIZE = Pt(12)

doc = Document()

# ---- margens 2 cm ----
for s in doc.sections:
    s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Cm(2.0)

# ---- estilo Normal: Sitka Text 12, 1,16, 6pt depois, justificado ----
normal = doc.styles["Normal"]
normal.font.name = BODY_FONT
normal.font.size = SIZE
# garante o nome da fonte também para east-asia/complex
rpr = normal.element.get_or_add_rPr()
rfonts = rpr.find(qn('w:rFonts'))
if rfonts is None:
    rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
    rfonts.set(qn(a), BODY_FONT)
pf = normal.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
pf.line_spacing = 1.16
pf.space_after = Pt(6)
pf.space_before = Pt(0)
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def set_font(run, name=BODY_FONT, size=SIZE):
    run.font.name = name
    run.font.size = size
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rfonts.set(qn(a), name)

TOKEN = re.compile(r'(\*\*\*|\*\*|\*)')

def add_runs(p, text, font=BODY_FONT, small_caps=False, force_bold=False):
    text = text.replace('&nbsp;', ' ').replace('\xa0', ' ')
    bold = ital = False
    for part in TOKEN.split(text):
        if part == '***':
            bold = not bold; ital = not ital; continue
        if part == '**':
            bold = not bold; continue
        if part == '*':
            ital = not ital; continue
        if part == '':
            continue
        r = p.add_run(part)
        r.bold = bold or force_bold
        r.italic = ital
        r.font.small_caps = small_caps
        set_font(r, font)

def new_par(align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, space_before=0,
            line=1.16, left_indent=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    if left_indent is not None:
        pf.left_indent = left_indent
    return p

raw = open(SRC, encoding='utf-8').read()
lines = raw.split('\n')

for ln in lines:
    s = ln.rstrip()
    stripped = s.strip()

    if stripped == '' :
        continue
    if stripped == '---':
        continue

    # ---- títulos ----
    if s.startswith('### '):  # subtítulo: negrito, 1ª maiúscula
        p = new_par(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=10, space_after=6)
        add_runs(p, s[4:].strip(), force_bold=True)
        continue
    if s.startswith('## '):   # título principal: VERSALETE + negrito
        p = new_par(align=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=8)
        add_runs(p, s[3:].strip(), small_caps=True, force_bold=True)
        continue
    if s.startswith('# '):    # título da peça: centralizado, versalete, negrito
        p = new_par(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=12)
        add_runs(p, s[2:].strip(), small_caps=True, force_bold=True)
        continue

    # ---- citação longa em bloco (> ...) : Segoe UI 12, recuo 2cm, 1,08 ----
    if s.startswith('> '):
        p = new_par(line=1.08, left_indent=Cm(2.0), space_after=6)
        add_runs(p, s[2:].strip(), font=QUOTE_FONT)
        continue

    # ---- sub-itens dos pedidos (recuo via &nbsp;) ----
    if ln.startswith('&nbsp;') or ln.startswith('\xa0') or ln.startswith('    '):
        p = new_par(left_indent=Cm(1.25))
        add_runs(p, stripped)
        continue

    # ---- linhas centralizadas: título de peça em negrito isolado, assinatura, local/data ----
    center_triggers = (
        stripped.startswith('**RECURSO AO TRIBUNAL PLENO**'),
        stripped.startswith('Aldenor Cunha Rebouças'),
        stripped.startswith('OAB/MA 6.755'),
        stripped.startswith('[Local]'),
        stripped == 'Pede deferimento.',
    )
    if any(center_triggers):
        p = new_par(align=WD_ALIGN_PARAGRAPH.CENTER if (center_triggers[0] or
                    stripped.startswith('Aldenor') or stripped.startswith('OAB/MA'))
                    else WD_ALIGN_PARAGRAPH.JUSTIFY)
        add_runs(p, stripped)
        continue

    # ---- endereçamento (1ª linha em maiúsculas) ----
    if stripped.startswith('EXCELENTÍSSIMO'):
        p = new_par(align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        add_runs(p, stripped, force_bold=True)
        continue

    # ---- parágrafo de corpo (inclui itens numerados "N. ...") ----
    p = new_par()
    add_runs(p, stripped)

doc.save(OUT)
print("OK ->", OUT)
print("Parágrafos:", len(doc.paragraphs))
