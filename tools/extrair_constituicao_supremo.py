#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extrair_constituicao_supremo.py — índice artigo da CF -> página do PDF
'A Constituição e o Supremo' (STF). Uso: python extrair_constituicao_supremo.py <pdf> <saida.json>"""
import sys, re, json
import fitz

pat = re.compile(r'^Art\.?\s*(\d+(?:-[A-Z])?)\s*[ºo°]?\.?$')

def main():
    pdf, out = sys.argv[1], sys.argv[2]
    doc = fitz.open(pdf)
    arts = {}  # artigo -> (pagina, header_text)
    for pno in range(doc.page_count):
        for b in doc[pno].get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    if "MdC" in s["font"]:
                        m = pat.match(s["text"].strip())
                        if m and m.group(1) not in arts:
                            arts[m.group(1)] = (pno+1,)
    # snippet do caput: texto da página inicial logo após "Art. N"
    regs = []
    def keyf(a):
        mm = re.match(r'(\d+)(?:-([A-Z]))?', a); return (int(mm.group(1)), mm.group(2) or "")
    for a in sorted(arts, key=keyf):
        pg = arts[a][0]
        txt = doc[pg-1].get_text()
        snip = ""
        mm = re.search(r'Art\.?\s*'+re.escape(a)+r'(?!\d)', txt)
        if mm:
            snip = re.sub(r'\s+', ' ', txt[mm.start():mm.start()+200]).strip()
        regs.append({"artigo": a, "pagina_pdf": pg, "caput": snip})
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fonte": "STF — A Constituição e o Supremo, 6ª ed. [VERIFICAR ano]",
                   "obs": "pagina_pdf = página FÍSICA do PDF (Anexos/A_Constituicao_e_o_Supremo_6ed_STF.pdf)",
                   "total": len(regs), "artigos": regs}, f, ensure_ascii=False, indent=1)
    print("Artigos indexados:", len(regs))
    print("Amostras:", [(r["artigo"], r["pagina_pdf"]) for r in regs if r["artigo"] in ("1","5","37","103-A","250")])

if __name__ == "__main__":
    main()
