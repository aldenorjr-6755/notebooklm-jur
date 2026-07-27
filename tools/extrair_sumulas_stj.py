#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extrair_sumulas_stj.py — extrai enunciados das Súmulas do STJ do PDF 'Inteiro Teor'
(Secretaria de Jurisprudência) para um dataset JSON canônico consultável.
Uso: python extrair_sumulas_stj.py <pdf> <saida.json>"""
import sys, re, json, unicodedata
import fitz

LABELS = ["Enunciado:", "Referências Legislativas:", "Referencias Legislativas:",
          "Órgão Julgador:", "Orgao Julgador:", "Data da decisão:", "Data da decisao:",
          "Fonte:", "Excerto dos Precedentes Originários:", "Excerto dos Precedentes Originarios:",
          "Situação:", "Situacao:", "Precedentes:"]

def field(block, label, stops):
    i = block.find(label)
    if i < 0: return ""
    start = i + len(label)
    end = len(block)
    for s in stops:
        j = block.find(s, start)
        if j != -1 and j < end:
            end = j
    return re.sub(r'\s+', ' ', block[start:end]).strip()

def main():
    pdf, out = sys.argv[1], sys.argv[2]
    doc = fitz.open(pdf)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    # cada verbete começa em "SÚMULA N" (maiúsculo) no início de linha
    heads = list(re.finditer(r'\nS[UÚ]MULA\s+(\d+)\b', text))
    sumulas = {}
    for k, m in enumerate(heads):
        num = int(m.group(1))
        start = m.end()
        end = heads[k+1].start() if k+1 < len(heads) else len(text)
        block = text[start:end]
        if "Enunciado:" not in block:
            continue  # provavelmente entrada de sumário, não verbete
        enun = field(block, "Enunciado:", ["Referências Legislativas:", "Referencias Legislativas:",
                     "Órgão Julgador:", "Orgao Julgador:", "Situação:", "Situacao:", "Fonte:"])
        if not enun:
            continue
        # ramo/tema = primeira linha não vazia do bloco antes de "Enunciado:"
        pre = block[:block.find("Enunciado:")].strip().splitlines()
        ramo = next((l.strip() for l in pre if l.strip()), "")
        orgao = field(block, "Órgão Julgador:", ["Data da decisão:", "Data da decisao:", "Fonte:"]) or \
                field(block, "Orgao Julgador:", ["Data da decisão:", "Data da decisao:", "Fonte:"])
        data = field(block, "Data da decisão:", ["Fonte:"]) or field(block, "Data da decisao:", ["Fonte:"])
        situ = field(block, "Situação:", ["Enunciado:"]) or field(block, "Situacao:", ["Enunciado:"])
        cancel = "CANCELAD" in unicodedata.normalize("NFKD", block[:400]).encode("ascii","ignore").decode().upper()
        # mantém a versão mais completa se número repetir
        if num not in sumulas or len(enun) > len(sumulas[num]["enunciado"]):
            sumulas[num] = {"numero": num, "ramo": ramo, "enunciado": enun,
                            "orgao": orgao, "data": data,
                            "situacao": "CANCELADA" if cancel else (situ or "vigente")}
    data_out = [sumulas[n] for n in sorted(sumulas)]
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"fonte": "STJ — Inteiro Teor das Súmulas (Secretaria de Jurisprudência, 16/11/2022)",
                   "total": len(data_out), "sumulas": data_out}, f, ensure_ascii=False, indent=1)
    print("Súmulas extraídas:", len(data_out))
    print("Faixa:", data_out[0]["numero"], "a", data_out[-1]["numero"])
    canc = [s["numero"] for s in data_out if s["situacao"] == "CANCELADA"]
    print("Marcadas CANCELADA:", len(canc), canc[:15])
    print("\n--- Amostras ---")
    for n in (7, 297, 568):
        s = sumulas.get(n)
        if s: print(f"[{n}] ({s['ramo']}) {s['enunciado'][:160]}")

if __name__ == "__main__":
    main()
