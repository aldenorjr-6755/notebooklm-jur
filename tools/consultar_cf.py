#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_cf.py — texto literal de artigo da Constituição (Planalto, até EC 139).
Fonte: tools/cf_artigos.json. Uso: python consultar_cf.py 5 | 103-A | --json"""
import sys,os,json,re,argparse
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cf_artigos.json")
def norm(s):
    s=s.strip().upper().replace("º","").replace("°","")
    m=re.match(r'(\d+)\s*-?\s*([A-Z])?',s)
    return None if not m else m.group(1)+(f"-{m.group(2)}" if m.group(2) else "")
ap=argparse.ArgumentParser(); ap.add_argument("artigo"); ap.add_argument("--json",action="store_true")
a=ap.parse_args(); base=json.load(open(DATA,encoding="utf-8"))
idx={r["artigo"]:r for r in base["artigos"]}; r=idx.get(norm(a.artigo))
if not r:
    m=f"Art. {a.artigo} não encontrado (CF corpo permanente 1º–250; ADCT não indexado)."
    print(json.dumps({"erro":m},ensure_ascii=False) if a.json else m); sys.exit()
if a.json: print(json.dumps({"fonte":base["fonte"],**r},ensure_ascii=False,indent=1)); sys.exit()
print(f"=== CF, {r['texto'][:0]}Art. {r['artigo']} ===  (fonte: {base['fonte']})\n")
print(r["texto"])
print("\n⚠️ Confira vigência/EC posterior no Planalto. Para a leitura do STF: /constituicao "+r['artigo'])
