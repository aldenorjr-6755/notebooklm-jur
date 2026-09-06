#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_acervo.py — busca full-text GENÉRICA nos corpora locais das colunas ConJur
(.md em C:\\Users\\alden\\.notebooklm\\<acervo>\\fontes\\). Acento-insensível; retorna trechos com título/data/URL.

Acervos (registry): senso_incomum · criminal_player · justo_processo · direitos_fundamentais · direito_de_defesa
(senso_incomum e criminal_player também têm helper dedicado próprio.)

Uso:
    python consultar_acervo.py --acervo direito_de_defesa "lavagem de dinheiro"
    python consultar_acervo.py --acervo justo_processo "cadeia de custódia" --titulos
    python consultar_acervo.py --acervo direitos_fundamentais "controle de convencionalidade" --ano 2023
"""
import sys, os, re, argparse, unicodedata, glob
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = r"C:\Users\alden\.notebooklm"
ACERVOS = {
    "senso_incomum": "Senso Incomum (Lenio Streck)",
    "criminal_player": "Criminal Player / Limite Penal",
    "justo_processo": "Justo Processo",
    "direitos_fundamentais": "Direitos Fundamentais",
    "direito_de_defesa": "Direito de Defesa",
    # registrados em 2026-08-30 (antes eram corpora orfaos, sem consumidor)
    "critica_penal": "Critica Penal (ConJur)",
    "nova_limite_penal": "Nova Limite Penal (Migalhas, 2023) - complementa criminal_player",
    "migalhas_criminais": "Migalhas Criminais",
    "migalhas_direitos_fundamentais": "Migalhas - Direitos Fundamentais",
    "perspectivas_direito_penal": "Perspectivas do Direito Penal",
}
def norm(s): return unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
def ano(fn):
    m=re.match(r'(\d{4})-', os.path.basename(fn)); return int(m.group(1)) if m else 0
def meta(txt):
    t=re.search(r'titulo:\s*(.+)', txt); u=re.search(r'url:\s*(\S+)', txt); d=re.search(r'data:\s*(\S+)', txt)
    return (t.group(1).strip() if t else "?"), (d.group(1) if d else "?"), (u.group(1) if u else "")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acervo", required=True, choices=list(ACERVOS))
    ap.add_argument("termo")
    ap.add_argument("--ano", type=int); ap.add_argument("--de", type=int); ap.add_argument("--ate", type=int)
    ap.add_argument("--limite", type=int, default=12); ap.add_argument("--contexto", type=int, default=260)
    ap.add_argument("--titulos", action="store_true")
    a=ap.parse_args(); q=norm(a.termo)
    files=sorted(glob.glob(os.path.join(ROOT, a.acervo, "fontes", "*.md")))
    if not files: print(f"Corpus vazio/ausente: {a.acervo}"); return
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
        if q not in norm(txt): continue
        ti,da,ur=meta(txt)
        if a.titulos: titulos.append((da,ti,ur)); continue
        nt=norm(txt); start=0; got=0
        while got<2 and len(hits)<a.limite:
            i=nt.find(q,start)
            if i<0: break
            ini=max(0,i-a.contexto//2); fim=min(len(txt),i+len(a.termo)+a.contexto//2)
            hits.append((ti,da,ur,re.sub(r'\s+',' ',txt[ini:fim]).strip())); start=i+len(q); got+=1
        if len(hits)>=a.limite: break
    lbl=ACERVOS[a.acervo]
    if a.titulos:
        print(f'{lbl} · "{a.termo}" · {len(titulos)} artigo(s)\n')
        for da,ti,ur in titulos[:60]: print(f"  [{da}] {ti}\n    {ur}")
        return
    if not hits: print(f'Nada encontrado para "{a.termo}" no acervo {lbl}.'); return
    nf=len(set(h[0] for h in hits))
    print(f'{lbl} (ConJur) · "{a.termo}" · {len(hits)} trecho(s) em {nf} artigo(s)\n')
    for ti,da,ur,sn in hits:
        print(f"■ {ti} ({da})"); print(f"  …{sn}…"); print(f"  {ur}\n")
    print("Corpus local (ConJur). Doutrina — confirmar o teor no artigo original.")
if __name__=="__main__": main()
