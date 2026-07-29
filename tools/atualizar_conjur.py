#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Atualização INCREMENTAL dos acervos das colunas do ConJur.

Desde ~jul/2026 o conjur.com.br está atrás do desafio JS do Cloudflare e o
site foi reestruturado (as URLs `/colunistas/<slug>/` deixaram de ser índice
de coluna). A via que funciona: Chrome REAL (Playwright) para vencer o
Cloudflare + WP REST API para listar por coluna, usando a taxonomia própria
`nome-da-coluna`. O corpo do artigo vem em `content.rendered` (não precisa
raspar HTML); o AUTOR vem do byline da página (o `author` do Yoast é o
editor que publicou, não o colunista).

Uso:
  python atualizar_conjur.py --check
  python atualizar_conjur.py --baixar [coluna ...]
"""
from __future__ import annotations
import argparse, html, os, re, sys, time, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from conjur_api import ApiConjur

RAIZ = r"C:\Users\alden\.notebooklm"

# coluna -> (id do termo `nome-da-coluna`, diretório do corpus, rótulo `fonte:`)
COLUNAS = {
    "senso-incomum":         (22386, "senso_incomum",         "Senso Incomum (ConJur)"),
    "criminal-player":       (24406, "criminal_player",       "Criminal Player (ConJur)"),
    "justo-processo":        (24793, "justo_processo",        "Justo Processo (ConJur)"),
    "direitos-fundamentais": (24411, "direitos_fundamentais", "Direitos Fundamentais (ConJur)"),
    "direito-de-defesa":     (24384, "direito_de_defesa",     "Direito de Defesa (ConJur)"),
    "critica-penal":         (22472, "critica_penal",         "Crítica Penal (ConJur)"),
}


def limpar(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", html.unescape(s)).strip()


def texto_do_html(rendered: str) -> str:
    partes = [limpar(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", rendered, re.S)]
    corpo = "\n\n".join(p for p in partes if len(p) > 30)
    return corpo or limpar(rendered)


def _sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def chave(url: str) -> str:
    """Identidade do artigo = data + slug do path.

    Duas armadilhas da migração do site (2026): o domínio perdeu o `www.` e
    vários posts ganharam sufixo `-2` no slug canônico — sem normalizar os
    dois, o diff acusa como "novo" um artigo que já está no corpus."""
    m = re.search(r"/(\d{4}-[a-z]{3}-\d{2})/([^/?#]+)", url)
    if not m:
        return url.rstrip("/")
    return f"{m.group(1)}/{re.sub(r'-\d+$', '', m.group(2))}"


def chaves_locais(dirc: str) -> tuple[set[str], set[str]]:
    """(chaves data+slug, chaves data+título) — o título é a segunda barreira
    contra duplicata quando o slug canônico mudou."""
    base = os.path.join(RAIZ, dirc, "fontes")
    slugs, titulos = set(), set()
    if not os.path.isdir(base):
        return slugs, titulos
    for fn in os.listdir(base):
        if not fn.endswith(".md"):
            continue
        cab = open(os.path.join(base, fn), encoding="utf-8", errors="replace").read(900)
        m = re.search(r"^url:\s*(\S+)", cab, re.M)
        if m:
            slugs.add(chave(m.group(1).strip().replace("\r", "")))
        mm = re.match(r"(\d{4}-[a-z]{3}-\d{2})_(.+)\.md$", fn)
        if mm:
            slugs.add(f"{mm.group(1)}/{re.sub(r'-\d+$', '', mm.group(2))}")
        td = re.search(r"^data:\s*(\S+)", cab, re.M)
        tt = re.search(r"^titulo:\s*(.+)$", cab, re.M)
        if td and tt:
            titulos.add(f"{td.group(1)}|{_sem_acento(tt.group(1))}")
    return slugs, titulos


def chave_titulo(post: dict) -> str:
    m = re.search(r"/(\d{4}-[a-z]{3}-\d{2})/", post["link"])
    data = m.group(1) if m else post["date"][:10]
    return f"{data}|{_sem_acento(limpar(post['title']['rendered']))}"


def autor_do_html(h: str) -> str:
    """Byline REAL do colunista.

    Cuidado com dois falsos positivos: `<meta name="author">` e o `author` do
    schema Yoast trazem o EDITOR que publicou (ex.: "Emerson Voltare"), e
    `class="...author..."` casa com o nome de quem COMENTOU o artigo. O byline
    verdadeiro está no bloco `conjur-post-autores`, em links
    `/assinaturas/<slug>/` com classe `assinante-link`."""
    nomes, vistos = [], set()
    for m in re.finditer(r'href="[^"]*conjur\.com\.br/assinaturas/[^"]*"[^>]*>(.*?)</a>', h, re.S):
        n = limpar(m.group(1))
        if (n and len(n) < 80 and not re.match(r"reda[çc][ãa]o", n, re.I)
                and "assine" not in n.lower() and n.lower() not in vistos):
            vistos.add(n.lower())
            nomes.append(n)
    return "; ".join(nomes) if nomes else "[VERIFICAR]"


def autor_do_artigo(api: ApiConjur, url: str) -> str:
    try:
        return autor_do_html(api.html(url))
    except Exception:
        return "[VERIFICAR]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("colunas", nargs="*")
    ap.add_argument("--baixar", action="store_true")
    ap.add_argument("--por-pagina", type=int, default=30)
    args = ap.parse_args()

    alvos = args.colunas or list(COLUNAS)
    total = 0
    with ApiConjur(visivel=True) as api:
        for nome in alvos:
            tid, dirc, rotulo = COLUNAS[nome]
            locais, titulos = chaves_locais(dirc)
            posts = api.get(f"/wp-json/wp/v2/posts?nome-da-coluna={tid}"
                            f"&per_page={args.por_pagina}&orderby=date&order=desc")
            novos = [p for p in posts
                     if chave(p["link"]) not in locais
                     and chave_titulo(p) not in titulos]
            print(f"\n### {nome}   local={len(locais)}   últimos={len(posts)}   NOVOS={len(novos)}")
            for p in novos:
                print(f"   + {p['date'][:10]}  {limpar(p['title']['rendered'])[:78]}")
            total += len(novos)

            if args.baixar and novos:
                destino_dir = os.path.join(RAIZ, dirc, "fontes")
                os.makedirs(destino_dir, exist_ok=True)
                for p in reversed(novos):          # cronológico
                    url = p["link"]
                    m = re.search(r"/(\d{4}-[a-z]{3}-\d{2})/([^/?#]+)", url)
                    data, slug = m.group(1), m.group(2)
                    titulo = limpar(p["title"]["rendered"])
                    corpo = texto_do_html(p["content"]["rendered"])
                    if len(corpo) < 300:
                        print(f"   CURTO ({len(corpo)}) {url}")
                        continue
                    autor = autor_do_artigo(api, url)
                    fn = os.path.join(destino_dir, f"{data}_{slug}.md")
                    open(fn, "w", encoding="utf-8").write(
                        f"---\ntitulo: {titulo}\nfonte: {rotulo}\nautor: {autor}\n"
                        f"data: {data}\nurl: {url}\n---\n\n# {titulo}\n\n{corpo}\n")
                    print(f"   OK {data} | {autor[:28]:28s} | {titulo[:55]}")
                    time.sleep(0.4)

    print(f"\n== TOTAL de artigos novos: {total}")


if __name__ == "__main__":
    main()
