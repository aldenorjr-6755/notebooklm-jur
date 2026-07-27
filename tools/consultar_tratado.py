#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_tratado.py — texto por artigo de tratados de DH (registry por --fonte).
Fontes: pidcp (Pacto Internacional DCP, Dec.592/92). [cadh tem helper próprio consultar_cadh.py]
Uso: python consultar_tratado.py --fonte pidcp <artigo|palavra> [--json]"""
import sys,os,json,re,argparse,unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
BASE=os.path.dirname(os.path.abspath(__file__))
REG={"pidcp":"pidcp_artigos.json","cadh":"cadh_artigos.json","tpi":"estatuto_roma_artigos.json"}
def norm(s): return unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
ap=argparse.ArgumentParser(); ap.add_argument("--fonte",required=True,choices=list(REG))
ap.add_argument("consulta"); ap.add_argument("--json",action="store_true"); ap.add_argument("--limite",type=int,default=10)
a=ap.parse_args(); base=json.load(open(os.path.join(BASE,REG[a.fonte]),encoding="utf-8")); arts=base["artigos"]
if re.fullmatch(r'\d+',a.consulta.strip()): res=[r for r in arts if r["artigo"]==int(a.consulta)]
else:
    q=norm(a.consulta); res=[r for r in arts if q in norm(r["texto"])][:a.limite]
if a.json: print(json.dumps({"fonte":base["fonte"],"url":base.get("url"),"resultados":len(res),"artigos":res},ensure_ascii=False,indent=1)); sys.exit()
if not res: print("Nenhum artigo encontrado. Fonte:",base["fonte"]); sys.exit()
print(base["fonte"],"\n")
for r in res: print(f"=== Artigo {r['artigo']} ===\n{r['texto'][:1500]}\n")
