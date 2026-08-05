#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_regimento.py — texto literal de artigo de Regimento Interno (STF, STJ, TJMA ou TSE).

Fontes (datasets gerados por extrair_regimento.py):
    --fonte stf   -> regimento_stf.json   (RISTF, até Emenda Regimental 59/2023)
    --fonte stj   -> regimento_stj.json    (RISTJ, consolidado até a Emenda Regimental n. 53, de 30/06/2026)
    --fonte tjma  -> regimento_tjma.json   (RITJMA, consolidado até Resolução-GP 13, 26/02/2026)
    --fonte tse   -> regimento_tse.json    (RITSE, Resolução n. 4.510, de 29/09/1952, anotado)

Uso:
    python consultar_regimento.py --fonte stf 21
    python consultar_regimento.py --fonte stj 158
    python consultar_regimento.py --fonte tjma 96 --json
    python consultar_regimento.py --fonte tse 35
"""
import sys, os, json, re, argparse
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

BASE = os.path.dirname(os.path.abspath(__file__))
MAP = {"stf": "regimento_stf.json", "stj": "regimento_stj.json",
       "tjma": "regimento_tjma.json", "tse": "regimento_tse.json"}

def norm(s):
    s = s.strip().upper().replace("º","").replace("°","")
    m = re.match(r'(\d+)\s*-?\s*([A-Z])?', s)
    return None if not m else m.group(1)+(f"-{m.group(2)}" if m.group(2) else "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonte", required=True, choices=["stf","stj","tjma","tse"])
    ap.add_argument("artigo")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    base = json.load(open(os.path.join(BASE, MAP[a.fonte]), encoding="utf-8"))
    idx = {r["artigo"]: r for r in base["artigos"]}
    r = idx.get(norm(a.artigo))
    if not r:
        m = f"Art. {a.artigo} não encontrado em {base['fonte']}."
        print(json.dumps({"erro": m}, ensure_ascii=False) if a.json else m); return
    if a.json:
        print(json.dumps({"fonte": base["fonte"], **r}, ensure_ascii=False, indent=1)); return
    print(f"=== Art. {r['artigo']} — {base['fonte']} ===\n")
    n = r.get("redacoes", 1)
    if n > 1:
        # alerta ANTES do texto: em rodape ninguem le', e o erro de citar a redacao
        # revogada ja' aconteceu (RITJMA art. 390, 05/08/2026).
        print(f"🚩 ATENÇÃO — este artigo tem {n} REDAÇÕES SUCESSIVAS abaixo, na ordem do PDF")
        print("   oficial. Só a ÚLTIMA é vigente; as anteriores estão marcadas e NÃO se citam.\n")
    print(r["texto"])
    print("\n⚠️ Confira emenda/resolução posterior à data da consolidação antes de citar.")
    if n > 1:
        print(f"⚠️ Repetindo: das {n} redações acima, cite a ÚLTIMA — a que traz a nota "
              "'(Redação dada por ...)'.")

if __name__ == "__main__":
    main()
