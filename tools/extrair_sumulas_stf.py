#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extrair_sumulas_stf.py — extrai Súmulas do STF (comuns e vinculantes) do PDF oficial
'Súmula do STF' para dataset JSON canônico. Uso: python extrair_sumulas_stf.py <pdf> <saida.json>"""
import sys, re, json, unicodedata
import fitz

LABELS = ["Data de Aprovação", "Data de Aprovacao", "Fonte de Publicação", "Fonte de Publicacao",
          "Referência Legislativa", "Referencia Legislativa", "Precedentes", "Observação", "Observacao"]

def asc(s): return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode()

def main():
    pdf, out = sys.argv[1], sys.argv[2]
    doc = fitz.open(pdf)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    # cabeçalho: SÚMULA [VINCULANTE] N  no início de linha
    heads = list(re.finditer(r'\nS[UÚ]MULA(\s+VINCULANTE)?\s+(\d+)\s*\n', text))
    out_map = {}  # (tipo,num) -> registro
    for k, m in enumerate(heads):
        vinc = bool(m.group(1))
        num = int(m.group(2))
        start = m.end()
        end = heads[k+1].start() if k+1 < len(heads) else len(text)
        block = text[start:end]
        # corta no primeiro rótulo de metadado
        cut = len(block)
        for lab in LABELS:
            j = block.find(lab)
            if j != -1 and j < cut: cut = j
        enun = re.sub(r'\s+', ' ', block[:cut]).strip()
        # entrada de sumário: bloco curtíssimo só com número (página)
        if not enun or enun.isdigit() or len(enun) < 12:
            continue
        data = ""
        md = re.search(r'Sess[aã]o\s+Plen[aá]ria\s+de\s+([\d/]+)', block)
        if md: data = md.group(1)
        canc = "CANCELAD" in asc(block[:cut+40]).upper() or "CANCELAD" in asc(enun).upper()
        tipo = "vinculante" if vinc else "sumula"
        key = (tipo, num)
        if key not in out_map or len(enun) > len(out_map[key]["enunciado"]):
            out_map[key] = {"numero": num, "tipo": tipo, "enunciado": enun,
                            "data_aprovacao": data,
                            "situacao": "CANCELADA" if canc else "vigente"}
    regs = [out_map[k] for k in sorted(out_map, key=lambda x:(x[0], x[1]))]
    comuns = [r for r in regs if r["tipo"]=="sumula"]
    vincs  = [r for r in regs if r["tipo"]=="vinculante"]
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fonte":"STF — Súmula do STF (Secretaria de Documentação, atualizado 01/12/2017)",
                   "total": len(regs), "total_comuns": len(comuns), "total_vinculantes": len(vincs),
                   "sumulas": regs}, f, ensure_ascii=False, indent=1)
    print("Total verbetes:", len(regs), "| comuns:", len(comuns), "| vinculantes:", len(vincs))
    if comuns: print("Comuns faixa:", comuns[0]["numero"], "a", comuns[-1]["numero"])
    if vincs:  print("Vinculantes faixa:", vincs[0]["numero"], "a", vincs[-1]["numero"])
    print("Canceladas:", sum(1 for r in regs if r["situacao"]=="CANCELADA"))
    print("\n--- Amostras ---")
    for r in regs[:1]+[x for x in comuns if x["numero"] in (346,473,636)]:
        print(f"[{r['tipo']} {r['numero']}] {r['enunciado'][:150]}")
if __name__=="__main__": main()
