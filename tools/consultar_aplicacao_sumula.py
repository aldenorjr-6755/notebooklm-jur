#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_aplicacao_sumula.py — buscador ONLINE de Súmulas do STF + aplicação (jurisprudência).

Endpoint (de /scripts/aplicacaosumula.js):
    POST https://portal.stf.jus.br/jurisprudencia/aplicacaosumulapesquisa.asp
         body: base=<26|30>&texto=<palavra>&numero=<n>&ramo=<ramo>  -> JSON [{num,link,termo,comentario}]
    base 26 = Súmulas VINCULANTES · base 30 = Súmulas COMUNS.
    Detalhe/aplicação: https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=<b>&sumula=<link>
    (WAF exige User-Agent de navegador + Referer.)

Uso:
    python consultar_aplicacao_sumula.py --tipo sv 11
    python consultar_aplicacao_sumula.py --tipo comum --numero 1
    python consultar_aplicacao_sumula.py --tipo comum "reexame de prova"
    python consultar_aplicacao_sumula.py --tipo sv --ramo "Direito Penal" --json
"""
import sys, json, re, argparse, urllib.parse, urllib.request
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
EP="https://portal.stf.jus.br/jurisprudencia/aplicacaosumulapesquisa.asp"
DET="https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp"
BASE={"sv":"26","comum":"30"}
def clean(h):
    h=re.sub(r'<[^>]+>',' ',h or ''); h=h.replace('&nbsp;',' ').replace('&quot;','"').replace('&amp;','&')
    return re.sub(r'\s+',' ',h).strip()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tipo",required=True,choices=["sv","comum"])
    ap.add_argument("consulta",nargs="?",default="")
    ap.add_argument("--numero",default=""); ap.add_argument("--ramo",default="")
    ap.add_argument("--json",action="store_true"); ap.add_argument("--limite",type=int,default=15)
    a=ap.parse_args()
    numero=a.numero; texto=""
    if a.consulta:
        (numero:=a.consulta) if re.fullmatch(r'\d+',a.consulta.strip()) else (texto:=a.consulta)
    body=urllib.parse.urlencode({"base":BASE[a.tipo],"texto":texto,"numero":numero,"ramo":a.ramo}).encode()
    req=urllib.request.Request(EP,data=body,method="POST",headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
        "Referer":"https://portal.stf.jus.br/jurisprudencia/aplicacaosumula.asp",
        "X-Requested-With":"XMLHttpRequest","Content-Type":"application/x-www-form-urlencoded"})
    try:
        data=json.loads(urllib.request.urlopen(req,timeout=30).read().decode("utf-8-sig"))
    except Exception as e:
        print("Erro ao consultar o STF:",e); return
    regs=[{"sumula":d.get("num","").strip(),"enunciado":clean(d.get("comentario","")),
           "aplicacao_url":f"{DET}?base={BASE[a.tipo]}&sumula={d.get('link','')}"} for d in (data or [])][:a.limite]
    if a.json:
        print(json.dumps({"fonte":"STF — Aplicação de Súmula (online)","tipo":a.tipo,"resultados":len(regs),"sumulas":regs},ensure_ascii=False,indent=1)); return
    if not regs: print("Nenhuma súmula encontrada (tipo",a.tipo+")."); return
    print(f"STF — Aplicação de Súmula ({'Vinculantes' if a.tipo=='sv' else 'comuns'}) · {len(regs)} resultado(s)\n")
    for r in regs:
        print(f"■ {r['sumula']}"); print(f"  {r['enunciado']}"); print(f"  Aplicação: {r['aplicacao_url']}"); print()
    print("⚠️ Fonte online e atual; confirme a redação vigente. Texto offline: /sumula-stf, /sumula-vinculante.")
if __name__=="__main__": main()
