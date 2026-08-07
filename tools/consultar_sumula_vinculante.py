#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_sumula_vinculante.py — Súmulas Vinculantes do STF (CF 103-A — EFEITO VINCULANTE).
Fonte: tools/sumulas_vinculantes_stf.json. Uso: ...py "<palavra>" | --numero N | --json"""
import sys,os,json,argparse,unicodedata,textwrap
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),"sumulas_vinculantes_stf.json")
def norm(s): return unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
ap=argparse.ArgumentParser(); ap.add_argument("termo",nargs="?",default="")
ap.add_argument("--numero",type=int); ap.add_argument("--json",action="store_true")
ap.add_argument("--limite",type=int,default=30); a=ap.parse_args()
base=json.load(open(DATA,encoding="utf-8")); svs=base["sumulas_vinculantes"]
if a.numero is not None: svs=[s for s in svs if s["numero"]==a.numero]
if a.termo:
    q=norm(a.termo); svs=[s for s in svs if q in norm(s["enunciado"])]
svs=svs[:a.limite]
if a.json:
    print(json.dumps({"fonte":base["fonte"],"resultados":len(svs),"sumulas_vinculantes":svs},ensure_ascii=False,indent=1)); sys.exit()
if not svs: print("Nenhuma SV encontrada. Fonte:",base["fonte"]); sys.exit()
print(f"Fonte: {base['fonte']}  ·  {len(svs)} resultado(s)  ·  EFEITO VINCULANTE (CF 103-A)\n")
for s in svs:
    flag={"PENDENTE":"  ⏳ PENDENTE DE PUBLICAÇÃO","CANCELADA":"  ⛔ CANCELADA"}.get(s["situacao"],"")
    print(f"Súmula Vinculante {s['numero']}{flag}\n  {s['enunciado']}\n")
    # a observação carrega o que muda o uso (cancelamento, ato que cancelou, pendência):
    # omiti-la fazia a SV cancelada sair sem dizer POR QUE nem POR QUAL ato.
    obs = (s.get("observacao") or "").strip()
    if obs:
        print("  » " + textwrap.fill(obs, width=104, subsequent_indent="    ") + "\n")
