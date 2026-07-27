#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_glossario.py — Glossário Jurídico do STF (definições de termos).
Fonte: tools/glossario_stf.json (atualizar com extrair_glossario.py).
Uso: python consultar_glossario.py "habeas corpus" | "a quo" [--json] [--limite N]"""
import sys,os,json,re,argparse,unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),"glossario_stf.json")
def norm(s): return unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
ap=argparse.ArgumentParser(); ap.add_argument("termo")
ap.add_argument("--json",action="store_true"); ap.add_argument("--limite",type=int,default=5)
a=ap.parse_args(); base=json.load(open(DATA,encoding="utf-8")); vs=base["verbetes"]
q=norm(a.termo)
exatos=[v for v in vs if norm(v["verbete"])==q]
no_verbete=[v for v in vs if q in norm(v["verbete"]) and v not in exatos]
na_desc=[v for v in vs if q in norm(v["descricao"]) and v not in exatos and v not in no_verbete]
res=(exatos+no_verbete+na_desc)[:a.limite]
if a.json:
    print(json.dumps({"fonte":base["fonte"],"resultados":len(res),"verbetes":res},ensure_ascii=False,indent=1)); sys.exit()
if not res: print("Nenhum verbete encontrado no Glossário do STF para:",a.termo); sys.exit()
print(f"Glossário Jurídico do STF · {len(res)} resultado(s)\n")
for v in res:
    print(f"■ {v['verbete']}"); print(f"  {v['descricao']}"); print()
print("Fonte: portal.stf.jus.br/jurisprudencia/glossario.asp · termo controlado: ver Tesauro do STF.")
