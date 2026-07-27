#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_senso_incomum.py — busca full-text no corpus da coluna "Senso Incomum"
(Lenio Streck, ConJur) em C:\\Users\\alden\\.notebooklm\\senso_incomum\\fontes\\*.md (744 artigos, 2012–2026).
Busca acento-insensível; retorna trechos com título/data/URL da fonte.

Uso:
    python consultar_senso_incomum.py "hermenêutica"
    python consultar_senso_incomum.py "ativismo judicial" --ano 2023 --limite 8
    python consultar_senso_incomum.py "discricionariedade" --de 2015 --ate 2018
Opções:
    --ano N        só artigos do ano N
    --de N --ate N faixa de anos
    --limite N     máx. de trechos (padrão 12)
    --contexto N   caracteres em torno do match (padrão 260)
    --titulos      lista só títulos das fontes que casam (sem trechos)
"""
import sys, os, re, argparse, unicodedata, glob
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
DIR = r"C:\Users\alden\.notebooklm\senso_incomum\fontes"
MES = {"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}
def norm(s): return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
def ano(fn):
    m=re.match(r'(\d{4})-', os.path.basename(fn));  return int(m.group(1)) if m else 0
def meta(txt):
    t=re.search(r'titulo:\s*(.+)', txt); u=re.search(r'url:\s*(\S+)', txt); d=re.search(r'data:\s*(\S+)', txt)
    return (t.group(1).strip() if t else "?"), (d.group(1) if d else "?"), (u.group(1) if u else "")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("termo"); ap.add_argument("--ano",type=int)
    ap.add_argument("--de",type=int); ap.add_argument("--ate",type=int)
    ap.add_argument("--limite",type=int,default=12); ap.add_argument("--contexto",type=int,default=260)
    ap.add_argument("--titulos",action="store_true")
    a=ap.parse_args(); q=norm(a.termo)
    files=sorted(glob.glob(os.path.join(DIR,"*.md")))
    def keep(f):
        y=ano(f)
        if a.ano and y!=a.ano: return False
        if a.de and y<a.de: return False
        if a.ate and y>a.ate: return False
        return True
    files=[f for f in files if keep(f)]
    hits=[]; titulos=[]
    for f in files:
        try: txt=open(f,encoding="utf-8").read()
        except Exception: continue
        nt=norm(txt)
        if q not in nt: continue
        ti,da,ur=meta(txt)
        if a.titulos: titulos.append((da,ti,ur)); continue
        start=0; got=0
        while got<2 and len(hits)<a.limite:
            i=nt.find(q,start)
            if i<0: break
            ini=max(0,i-a.contexto//2); fim=min(len(txt),i+len(a.termo)+a.contexto//2)
            hits.append((ti,da,ur,re.sub(r'\s+',' ',txt[ini:fim]).strip())); start=i+len(q); got+=1
        if len(hits)>=a.limite: break
    if a.titulos:
        print(f'Senso Incomum · "{a.termo}" · {len(titulos)} artigo(s)\n')
        for da,ti,ur in titulos[:50]: print(f"  [{da}] {ti}\n    {ur}")
        return
    if not hits: print(f'Nada encontrado para "{a.termo}" no corpus Senso Incomum (744 artigos).'); return
    nf=len(set(h[0] for h in hits))
    print(f'Senso Incomum (Lenio Streck) · "{a.termo}" · {len(hits)} trecho(s) em {nf} artigo(s)\n')
    for ti,da,ur,sn in hits:
        print(f"■ {ti} ({da})"); print(f"  …{sn}…"); print(f"  {ur}\n")
    print("Corpus local (ConJur). Confirme o teor/contexto no artigo original.")
if __name__=="__main__": main()
