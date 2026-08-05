#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_jurisprudencia.py — busca full-text no corpus oficial de jurisprudência
(clone STF·STJ·TRF1) em C:\\Users\\alden\\.notebooklm\\clone_jurisprudencia\\fontes\\*.md.
Cobre: Informativos STJ/STF, Jurisprudência em Teses, Repetitivos/IAC, Súmulas anotadas,
TRF1 BIJ, enunciados. Busca acento-insensível; retorna trechos com a fonte.

Uso:
    python consultar_jurisprudencia.py "prescrição intercorrente"
    python consultar_jurisprudencia.py "dano moral" --tribunal stj --limite 8
    python consultar_jurisprudencia.py "improbidade" --fonte "Teses" --contexto 280
Opções:
    --tribunal stj|stf|trf1   filtra pelos arquivos do tribunal
    --fonte "<substr>"        filtra arquivos cujo nome contém a substring (ex.: "Repetitivos", "2023")
    --limite N                máx. de trechos (padrão 12)
    --contexto N              caracteres em torno do match (padrão 240)
"""
import sys, os, re, argparse, unicodedata, glob
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
DIR = r"C:\Users\alden\.notebooklm\clone_jurisprudencia\fontes"
def norm(s): return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
TRIB = {"stj":["sumulasstj","informativos stj","jurisprudencia em teses","jurisprudência em teses","repetitivos"],
        "stf":["sumulas stf","sumulas_vinculantes","sumulas vinculantes stf","informativo_tematico","informativos20"],
        "trf1":["trf1"]}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("termo")
    ap.add_argument("--tribunal",choices=["stj","stf","trf1"])
    ap.add_argument("--fonte",default="")
    ap.add_argument("--limite",type=int,default=12)
    ap.add_argument("--contexto",type=int,default=240)
    a=ap.parse_args()
    q=norm(a.termo)
    files=sorted(glob.glob(os.path.join(DIR,"*.md")))
    if a.fonte: files=[f for f in files if norm(a.fonte) in norm(os.path.basename(f))]
    if a.tribunal:
        pats=[norm(p) for p in TRIB[a.tribunal]]
        files=[f for f in files if any(p in norm(os.path.basename(f)) for p in pats)]
    hits=[]; nfiles=0
    for f in files:
        try: txt=open(f,encoding="utf-8").read()
        except Exception: continue
        nt=norm(txt); start=0; got=0
        while True:
            i=nt.find(q,start)
            if i<0 or len(hits)>=a.limite: break
            ini=max(0,i-a.contexto//2); fim=min(len(txt),i+len(a.termo)+a.contexto//2)
            snip=re.sub(r'\s+',' ',txt[ini:fim]).strip()
            hits.append((os.path.basename(f)[:-3],snip)); start=i+len(q); got+=1
            if got>=3: break  # no máx 3 por fonte para diversificar
        if len(hits)>=a.limite: break
    nfiles=len(set(h[0] for h in hits))
    if not hits:
        print(f'Nada encontrado para "{a.termo}" no corpus (70 fontes STF/STJ/TRF1).'); return
    print(f'Corpus de jurisprudência (STF·STJ·TRF1) · "{a.termo}" · {len(hits)} trecho(s) em {nfiles} fonte(s)\n')
    for src,snip in hits:
        print(f"■ [{src}]"); print(f"  …{snip}…\n")
    print("Fonte: clone_jurisprudencia (notebook cb154c24). Confirme inteiro teor/atualidade na fonte oficial.")
if __name__=="__main__": main()
