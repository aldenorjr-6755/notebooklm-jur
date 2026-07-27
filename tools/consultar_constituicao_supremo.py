#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_constituicao_supremo.py — dado um artigo da CF, retorna a PÁGINA do PDF
'A Constituição e o Supremo' (STF, 6ª ed., 1895 p.) e, com --texto, o TEXTO das
páginas correspondentes (anotações do STF sobre o artigo).

Fontes:
  - Índice artigo→página: tools/constituicao_supremo.json (extrair_constituicao_supremo.py)
  - Texto integral: ~/.notebooklm/constituicao_supremo/fontes/ (8 volumes .md com
    marcadores '===== PAGINA N =====', páginas físicas do PDF, 250 págs/volume)
  - PDF original: ~/.notebooklm/biblioteca/pdf/A_Constituicao_e_o_Supremo_6ed_STF.pdf
    (mesmo conteúdo em Markdown paginado: ~/.notebooklm/biblioteca/md/, marcador "## [p. N]")

Uso:
    python consultar_constituicao_supremo.py 5
    python consultar_consituicao_supremo.py 103-A --texto
    python consultar_constituicao_supremo.py 37 --texto --paginas 5
    python consultar_constituicao_supremo.py --pagina 1200 --texto
    python consultar_constituicao_supremo.py 37 --json
"""
import sys, os, json, re, glob, argparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TOOLS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(TOOLS, "constituicao_supremo.json")
PDF = r"C:\Users\alden\.notebooklm\biblioteca\pdf\A_Constituicao_e_o_Supremo_6ed_STF.pdf"
MD  = r"C:\Users\alden\.notebooklm\biblioteca\md\A_Constituicao_e_o_Supremo_6ed_STF.md"  # mesmo texto em Markdown, marcador "## [p. N]"
FONTES = os.path.join(os.path.expanduser("~"), ".notebooklm", "constituicao_supremo", "fontes")
PAGS_POR_VOLUME = 250
PAG_MAX = 1895
MARCA = re.compile(r"^=====\s*PAGINA\s+(\d+)\s*=====\s*$", re.MULTILINE)


def norm_art(s):
    s = s.strip().upper().replace("º", "").replace("°", "")
    m = re.match(r'(\d+)\s*-?\s*([A-Z])?', s)
    if not m:
        return None
    return m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")


def volume_path(pagina):
    """Localiza o .md do volume que contém a página física dada."""
    inicio = ((pagina - 1) // PAGS_POR_VOLUME) * PAGS_POR_VOLUME + 1
    hits = glob.glob(os.path.join(FONTES, f"*VOLUME-* (pg-{inicio}).md"))
    return hits[0] if hits else None


def extrair_paginas(pag_ini, n_pags):
    """Extrai o texto de n_pags páginas a partir de pag_ini (cruza volumes se preciso)."""
    partes, pag = [], pag_ini
    fim = min(pag_ini + n_pags - 1, PAG_MAX)
    while pag <= fim:
        vol = volume_path(pag)
        if not vol:
            partes.append(f"[volume da página {pag} não encontrado em {FONTES}]")
            break
        with open(vol, encoding="utf-8") as f:
            texto = f.read()
        marcas = [(int(m.group(1)), m.start(), m.end()) for m in MARCA.finditer(texto)]
        idx = {num: (ini, end) for num, ini, end in marcas}
        ult_do_volume = max(idx) if idx else pag
        while pag <= fim and pag <= ult_do_volume:
            if pag in idx:
                _, end = idx[pag]
                prox = [n for n in idx if n > pag]
                corte = idx[min(prox)][0] if prox else len(texto)
                corpo = texto[end:corte].strip()
                partes.append(f"----- página {pag} -----\n{corpo if corpo else '[página sem texto extraído — OCR pendente no PDF]'}")
            else:
                partes.append(f"----- página {pag} -----\n[marcador não encontrado no volume]")
            pag += 1
    return "\n\n".join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artigo", nargs="?", help="artigo da CF (ex.: 5, 103-A)")
    ap.add_argument("--pagina", type=int, help="acesso direto por página física do PDF")
    ap.add_argument("--texto", action="store_true", help="imprime o texto das páginas")
    ap.add_argument("--paginas", type=int, default=3, help="nº de páginas a extrair (padrão 3)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.pagina:
        if a.texto:
            print(f"A Constituição e o Supremo (STF, 6ª ed.) — páginas {a.pagina}+")
            print(extrair_paginas(a.pagina, a.paginas))
        else:
            print(f"Página {a.pagina} — use --texto para extrair o conteúdo.")
        return

    if not a.artigo:
        ap.error("informe o artigo da CF ou --pagina N")

    base = json.load(open(DATA, encoding="utf-8"))
    idx = {r["artigo"]: r for r in base["artigos"]}
    key = norm_art(a.artigo)
    r = idx.get(key)

    if not r:
        msg = f"Artigo {a.artigo} não encontrado no índice (CF arts. 1º a 250 + variantes -A)."
        print(json.dumps({"erro": msg}, ensure_ascii=False) if a.json else msg)
        return

    if a.json:
        out = {"fonte": base["fonte"], "pdf": PDF, **r}
        if a.texto:
            out["texto"] = extrair_paginas(r["pagina_pdf"], a.paginas)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return

    print(f"CF Art. {r['artigo']} → A Constituição e o Supremo (STF)")
    print(f"  Página do PDF (física): {r['pagina_pdf']}")
    if r.get("caput"):
        print(f"  Caput: {r['caput'][:160]}")
    if a.texto:
        print()
        print(extrair_paginas(r["pagina_pdf"], a.paginas))
        print()
        print("⚠️ 6ª ed. (2018, até EC 99/2017) — confirmar entendimentos posteriores no STF / pesquisa-precedentes-web.")
    else:
        print(f"  Texto local: adicione --texto (corpus em {FONTES})")
        print(f"  Abra: {PDF}  (vá à página {r['pagina_pdf']})")
        print(f"  ⚠️ Confirme entendimentos posteriores à 6ª ed. no STF / pesquisa-precedentes-web.")


if __name__ == "__main__":
    main()
