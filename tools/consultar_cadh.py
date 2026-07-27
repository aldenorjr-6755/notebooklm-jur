#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_cadh.py — Convenção Americana sobre Direitos Humanos (Pacto de São José / CADH),
promulgada pelo Decreto 678/1992. Texto literal por artigo + busca por palavra.

Fonte: tools/cadh_artigos.json (extraído de planalto.gov.br/ccivil_03/decreto/d0678.htm).

Uso:
    python consultar_cadh.py 8                 # artigo 8 (Garantias Judiciais)
    python consultar_cadh.py "prazo razoável"  # busca por palavra
    python consultar_cadh.py 25 --json
"""
import sys, os, json, re, argparse, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cadh_artigos.json")
def norm(s): return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("consulta"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--limite", type=int, default=10); a = ap.parse_args()
    base = json.load(open(DATA, encoding="utf-8")); arts = base["artigos"]
    res = []
    if re.fullmatch(r'\d+', a.consulta.strip()):
        res = [r for r in arts if r["artigo"] == int(a.consulta)]
    else:
        q = norm(a.consulta); res = [r for r in arts if q in norm(r["texto"])][: a.limite]
    if a.json:
        print(json.dumps({"fonte": base["fonte"], "url": base["url"], "resultados": len(res), "artigos": res}, ensure_ascii=False, indent=1)); return
    if not res: print("Nenhum artigo encontrado. Fonte:", base["fonte"]); return
    print(f"{base['fonte']}\n")
    for r in res:
        print(f"=== Artigo {r['artigo']} da CADH ===")
        print(r["texto"][:1500])
        print()
    print("⚠️ Norma supralegal (STF, RE 466.343); aplicada pela Corte IDH — ver agente corte-idh-brasil.")

if __name__ == "__main__":
    main()
