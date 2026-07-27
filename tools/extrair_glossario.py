#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extrair_glossario.py — baixa o Glossário Jurídico do STF (endpoint JSON) e salva limpo.
Endpoint (de /scripts/glossario.js): POST portal.stf.jus.br/jurisprudencia/glossario-service.asp (body vazio) -> JSON [{seq,verbete,descricao(html)}].
Uso: python extrair_glossario.py <saida.json>"""
import sys,json,re,urllib.request
URL="https://portal.stf.jus.br/jurisprudencia/glossario-service.asp"
req=urllib.request.Request(URL,data=b"",method="POST",headers={
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
    "Referer":"https://portal.stf.jus.br/jurisprudencia/glossario.asp",
    "X-Requested-With":"XMLHttpRequest","Content-Type":"application/x-www-form-urlencoded"})
raw=urllib.request.urlopen(req,timeout=30).read().decode("utf-8-sig")
data=json.loads(raw)
def clean(h):
    h=re.sub(r'(?i)</p>|<br\s*/?>',' \n',h); h=re.sub(r'<[^>]+>',' ',h)
    h=h.replace('&nbsp;',' ').replace('&quot;','"').replace('&amp;','&').replace('&ordm;','º')
    h=re.sub(r'[ \t]+',' ',h); h=re.sub(r'\n\s*\n+','\n',h)
    return h.strip()
regs=[{"verbete":d["verbete"].strip(),"descricao":clean(d["descricao"])} for d in data if d.get("verbete")]
regs.sort(key=lambda r:r["verbete"].lower())
json.dump({"fonte":"Glossário Jurídico do STF","url":"https://portal.stf.jus.br/jurisprudencia/glossario.asp","total":len(regs),"verbetes":regs},
          open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("verbetes:",len(regs),"| ex:",[r["verbete"] for r in regs[:6]])
