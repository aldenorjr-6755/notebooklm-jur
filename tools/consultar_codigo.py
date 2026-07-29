#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_codigo.py — texto literal de artigo de CÓDIGO/LEI (registry por --fonte).
Fontes: cpc (Lei 13.105/2015). Adicionar: extrair_codigo.py → json + 1 linha no REG.
Uso: python consultar_codigo.py --fonte cpc 300 | "tutela de urgência" [--json] [--limite N]"""
import sys,os,json,re,argparse,unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
BASE=os.path.dirname(os.path.abspath(__file__))
REG={"cpc":"cpc_artigos.json","cpp":"cpp_artigos.json","cp":"cp_artigos.json","eaoab":"eaoab_artigos.json","lei9868":"lei9868_artigos.json","lei9882":"lei9882_artigos.json","cc":"cc_artigos.json","codoje":"codoje_artigos.json","ctn":"ctn_artigos.json","lei12016":"lei12016_artigos.json","lindb":"lindb_artigos.json","lei6830":"lei6830_artigos.json","lei9784":"lei9784_artigos.json","lei12850":"lei12850_artigos.json","lei12830":"lei12830_artigos.json","lei12030":"lei12030_artigos.json","lei12965":"lei12965_artigos.json","lei13709":"lei13709_artigos.json","lei9613":"lei9613_artigos.json","lei9296":"lei9296_artigos.json","lei11343":"lei11343_artigos.json","lei8072":"lei8072_artigos.json","lei11340":"lei11340_artigos.json","lei13431":"lei13431_artigos.json","lei9099":"lei9099_artigos.json","lei8137":"lei8137_artigos.json","lei9873":"lei9873_artigos.json","lei8429":"lei8429_artigos.json","lei4737":"lei4737_artigos.json","lei9504":"lei9504_artigos.json","lei9096":"lei9096_artigos.json","lep":"lep_artigos.json","lc64":"lc64_artigos.json","lc105":"lc105_artigos.json","lei9605":"lei9605_artigos.json"}
def norm(s): return unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
def n_art(s):
    # aceita "3", "3º", "1.048", "3-A", "3ºA", "359-M-A" (sufixo duplo) -> "3","1048","3-A","359-M-A"
    s=s.strip().upper().replace("º","").replace("°","").replace(".","").replace(" ","")
    m=re.fullmatch(r'(\d+)((?:-?[A-Z])*)',s)
    if not m: return None
    return m.group(1)+"".join("-"+c for c in re.findall(r'[A-Z]',m.group(2)))
ap=argparse.ArgumentParser(); ap.add_argument("--fonte",required=True,choices=list(REG))
ap.add_argument("consulta"); ap.add_argument("--json",action="store_true"); ap.add_argument("--limite",type=int,default=8)
a=ap.parse_args(); base=json.load(open(os.path.join(BASE,REG[a.fonte]),encoding="utf-8")); arts=base["artigos"]
idx={r["artigo"]:r for r in arts}
if re.fullmatch(r'[\dºo°.\- A-Za-z]+',a.consulta.strip()) and re.search(r'\d',a.consulta) and len(a.consulta.strip())<=8:
    k=n_art(a.consulta); res=[idx[k]] if k in idx else []
else:
    q=norm(a.consulta); res=[r for r in arts if q in norm(r["texto"])][:a.limite]
if a.json: print(json.dumps({"fonte":base["fonte"],"resultados":len(res),"artigos":res},ensure_ascii=False,indent=1)); sys.exit()
if not res: print("Nenhum artigo encontrado. Fonte:",base["fonte"]); sys.exit()
print(base["fonte"],"\n")
for r in res:
    txt=r["texto"]
    print(txt if len(res)==1 else (txt[:300]+("…" if len(txt)>300 else "")))
    print()
print("⚠️ Versão compilada Planalto; confira lei alteradora posterior antes de citar como vigente.")
