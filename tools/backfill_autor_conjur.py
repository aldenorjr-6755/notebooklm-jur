#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Corrige/preenche o campo `autor:` dos .md dos acervos ConJur, lendo o byline
real da página (bloco `conjur-post-autores` → links /assinaturas/<slug>/).

Só toca em arquivo sem `autor:` ou com autor ausente/suspeito. Retomável.
"""
from __future__ import annotations
import os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from conjur_api import ApiConjur
from atualizar_conjur import autor_do_html, RAIZ

DIRS = ["senso_incomum", "criminal_player", "justo_processo",
        "direitos_fundamentais", "direito_de_defesa", "critica_penal"]
SUSPEITO = re.compile(r"^\s*$|VERIFICAR|disse:|reda[çc][ãa]o", re.I)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    horas = 0.0
    for a in sys.argv[1:]:
        if a.startswith("--horas="):
            horas = float(a.split("=", 1)[1])
    limite = time.time() - horas * 3600 if horas else None
    alvos = argv or DIRS
    pend = []
    for d in alvos:
        base = os.path.join(RAIZ, d, "fontes")
        if not os.path.isdir(base):
            continue
        for fn in sorted(os.listdir(base)):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(base, fn)
            if limite and os.path.getmtime(p) < limite:
                continue
            cab = open(p, encoding="utf-8", errors="replace").read(900)
            au = re.search(r"^autor:\s*(.*)$", cab, re.M)
            url = re.search(r"^url:\s*(\S+)", cab, re.M)
            if not url:
                continue
            if au and not SUSPEITO.search(au.group(1)):
                continue
            # o fetch roda DENTRO da página de conjur.com.br: URL com `www.`
            # é outra origem e o navegador barra por CORS.
            pend.append((p, url.group(1).strip().replace("://www.conjur", "://conjur")))
    print(f"arquivos a corrigir: {len(pend)}")
    if not pend:
        return
    ok = 0
    with ApiConjur(visivel=True) as api:
        for p, url in pend:
            try:
                autor = autor_do_html(api.html(url))
            except Exception as e:
                print(f"  ERRO {url} -> {e}")
                continue
            txt = open(p, encoding="utf-8").read()
            if re.search(r"^autor:.*$", txt, re.M):
                txt = re.sub(r"^autor:.*$", f"autor: {autor}", txt, count=1, flags=re.M)
            else:
                txt = re.sub(r"^(fonte:.*)$", r"\1\n" + f"autor: {autor}", txt, count=1, flags=re.M)
            open(p, "w", encoding="utf-8").write(txt)
            ok += 1
            print(f"  {os.path.basename(p)[:60]:60s} -> {autor}")
            time.sleep(0.3)
    print(f"FIM: {ok}/{len(pend)}")


if __name__ == "__main__":
    main()
