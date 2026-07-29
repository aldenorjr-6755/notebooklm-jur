#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Atualização INCREMENTAL dos acervos de colunas (ConJur e Migalhas).

Para cada coluna: (1) rastreia as primeiras páginas do índice, (2) diffa contra
o corpus local (campo `url:` do frontmatter), (3) baixa só o que é novo em .md.

Uso:
  python atualizar_colunas.py --check              # só diagnostica (não baixa)
  python atualizar_colunas.py --baixar [coluna...] # baixa os novos
"""
import re, os, sys, time, html, argparse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
RAIZ = r"C:\Users\alden\.notebooklm"

# chave: (portal, slug da coluna, diretório do corpus, rótulo `fonte:`)
COLUNAS = {
    "senso-incomum":         ("conjur", "senso-incomum",         "senso_incomum",         "Senso Incomum (ConJur)"),
    "criminal-player":       ("conjur", "criminal-player",       "criminal_player",       "Criminal Player (ConJur)"),
    "justo-processo":        ("conjur", "justo-processo",        "justo_processo",        "Justo Processo (ConJur)"),
    "direitos-fundamentais": ("conjur", "direitos-fundamentais", "direitos_fundamentais", "Direitos Fundamentais (ConJur)"),
    "direito-de-defesa":     ("conjur", "direito-de-defesa",     "direito_de_defesa",     "Direito de Defesa (ConJur)"),
    "critica-penal":         ("conjur", "critica-penal",         "critica_penal",         "Crítica Penal (ConJur)"),
    "migalhas-criminais":    ("migalhas", "migalhas-criminais",  "migalhas_criminais",    "Migalhas Criminais"),
    "migalhas-df":           ("migalhas", "direitos-fundamentais", "migalhas_direitos_fundamentais", "Migalhas — Direitos Fundamentais"),
    "nova-limite-penal":     ("migalhas", "nova-limite-penal",   "nova_limite_penal",     "Nova Limite Penal (Migalhas)"),
    "perspectivas-penal":    ("migalhas", "perspectivas-do-direito-penal", "perspectivas_direito_penal", "Perspectivas do Direito Penal (Migalhas)"),
}

MESES = {"janeiro":"01","fevereiro":"02","março":"03","marco":"03","abril":"04","maio":"05",
         "junho":"06","julho":"07","agosto":"08","setembro":"09","outubro":"10",
         "novembro":"11","dezembro":"12"}


def fetch(u, timeout=40):
    req = urllib.request.Request(u, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", errors="replace")


def limpar(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def chave_migalhas(u):
    """No Migalhas o ID numérico é a única parte estável da URL — o slug varia
    (`...cibercrimes--uma-visao` × `...cibercrimes-uma-visao`) e diff por URL
    inteira acusa artigo repetido como novo."""
    m = re.search(r"/coluna/[^/]+/(\d+)/", u + "/")
    return m.group(1) if m else u.rstrip("/")


def urls_locais(dirc, portal="conjur"):
    """Chaves já presentes no corpus local (frontmatter `url:`)."""
    base = os.path.join(RAIZ, dirc, "fontes")
    vistas = set()
    if not os.path.isdir(base):
        return vistas
    for fn in os.listdir(base):
        if not fn.endswith(".md"):
            continue
        try:
            cab = open(os.path.join(base, fn), encoding="utf-8", errors="replace").read(900)
        except OSError:
            continue
        m = re.search(r"^url:\s*(\S+)", cab, re.M)
        if m:
            u = m.group(1).strip().rstrip("/").replace("\r", "")
            vistas.add(chave_migalhas(u) if portal == "migalhas" else u)
    return vistas


# ─────────────────────────── ConJur ───────────────────────────

def crawl_conjur(slug, max_pag=3):
    """Links de artigo das primeiras páginas da coluna (só de dentro do <article>,
    antes do <aside> — o <aside> traz OUTRAS colunas e contamina)."""
    base = f"https://www.conjur.com.br/colunistas/{slug}/"
    achados = []
    for p in range(1, max_pag + 1):
        u = base if p == 1 else f"{base}page/{p}/"
        try:
            h = fetch(u)
        except Exception as e:
            print(f"    ! p{p}: {e}")
            break
        main = h.split("<aside")[0]
        for l in re.findall(r'href="(https://www\.conjur\.com\.br/\d{4}-[a-z]{3}-\d{2}/[^"]+)"', main):
            l = l.rstrip("/")
            if l not in achados:
                achados.append(l)
        time.sleep(0.3)
    return achados


def baixar_conjur(u, dirc, rotulo):
    m = re.search(r"/(\d{4}-[a-z]{3}-\d{2})/([^/?#]+)", u)
    data, sg = (m.group(1), m.group(2)) if m else ("0000-jan-01", re.sub(r"\W+", "-", u)[-40:])
    destino = os.path.join(RAIZ, dirc, "fontes", f"{data}_{sg}.md")
    h = fetch(u + "/")
    main = h.split("<aside")[0]
    corpo_m = re.search(r'<div[^>]+class="[^"]*the_content[^"]*"[^>]*>(.*)', main, re.S)
    main = corpo_m.group(1) if corpo_m else main
    main = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", main, flags=re.S | re.I)

    tt = re.search(r'property="og:title" content="([^"]+)"', h) or re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    titulo = re.sub(r"\s*[-–|]\s*Conjur.*$", "", limpar(tt.group(1)) if tt else sg)
    au = re.search(r'rel="author"[^>]*>(.*?)</a>', h, re.S) or re.search(r'href="/autor/[^"]*"[^>]*>(.*?)</a>', h, re.S)
    autor = limpar(au.group(1)) if au else ""
    if re.match(r"reda[çc][ãa]o", autor, re.I) or not autor:
        autor = "[VERIFICAR]"

    partes = [limpar(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", main, re.S)]
    corpo = "\n\n".join(p for p in partes if len(p) > 30)
    if len(corpo) < 300:
        raise ValueError(f"corpo curto ({len(corpo)} chars)")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8").write(
        f"---\ntitulo: {titulo}\nfonte: {rotulo}\nautor: {autor}\ndata: {data}\nurl: {u}/\n---\n\n# {titulo}\n\n{corpo}\n")
    return destino, titulo, data


# ─────────────────────────── Migalhas ───────────────────────────

def crawl_migalhas(slug, max_pag=3):
    base = f"https://www.migalhas.com.br/coluna/{slug}"
    achados = []
    for p in range(1, max_pag + 1):
        # a paginação é `?pagina=N`; `?p=` e `?page=` são IGNORADOS e devolvem
        # sempre a página 1 — o que faz o acervo parecer completo com 30 itens.
        u = base if p == 1 else f"{base}?pagina={p}"
        try:
            h = fetch(u)
        except Exception as e:
            print(f"    ! p{p}: {e}")
            break
        pat = rf'href="(https://www\.migalhas\.com\.br/coluna/{re.escape(slug)}/\d+/[^"]+)"'
        links = re.findall(pat, h) or re.findall(rf'href="(/coluna/{re.escape(slug)}/\d+/[^"]+)"', h)
        for l in links:
            if l.startswith("/"):
                l = "https://www.migalhas.com.br" + l
            l = l.rstrip("/")
            if l not in achados:
                achados.append(l)
        time.sleep(0.4)
    return achados


def baixar_migalhas(u, dirc, rotulo):
    m = re.search(r"/(\d+)/([^/?#]+)", u)
    aid, sg = (m.group(1), m.group(2)) if m else ("0", re.sub(r"\W+", "-", u)[-40:])
    h = fetch(u)
    main = h.split("<aside")[0] if "<aside" in h else h
    main = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", main, flags=re.S | re.I)

    dm = re.search(r'article:published_time"\s+content="([^"]+)"', h)
    if dm:
        data = dm.group(1)[:10]
    else:
        dm = re.search(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", h, re.I)
        data = f"{dm.group(3)}-{MESES.get(dm.group(2).lower(),'01')}-{dm.group(1).zfill(2)}" if dm else "0000-00-00"

    tt = re.search(r'property="og:title"\s+content="([^"]+)"', h) or re.search(r"<title[^>]*>(.*?)</title>", h, re.S)
    titulo = re.sub(r"\s*[-–|]\s*Migalhas.*$", "", limpar(tt.group(1)) if tt else sg).strip()
    au = re.search(r'<a[^>]+/autor/[^"]*"[^>]*>(.*?)</a>', main, re.S)
    autor = limpar(au.group(1)) if au else "[VERIFICAR]"

    partes = [limpar(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", main, re.S)]
    corpo = "\n\n".join(p for p in partes if len(p) > 30)
    if len(corpo) < 300:
        raise ValueError(f"corpo curto ({len(corpo)} chars)")

    destino = os.path.join(RAIZ, dirc, "fontes", f"{data}_{aid}_{sg[:50]}.md")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    open(destino, "w", encoding="utf-8").write(
        f"---\ntitulo: {titulo}\nautor: {autor}\nfonte: {rotulo}\ncoluna: {rotulo}\ndata: {data}\nid: {aid}\nurl: {u}\n---\n\n"
        f"# {titulo}\n\n**Autor(es):** {autor}  \n**Data:** {data}  \n**URL:** {u}\n\n---\n\n{corpo}\n")
    return destino, titulo, data


# ─────────────────────────── driver ───────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("colunas", nargs="*", default=[])
    ap.add_argument("--baixar", action="store_true")
    ap.add_argument("--paginas", type=int, default=3)
    args = ap.parse_args()

    alvos = args.colunas or list(COLUNAS)
    total_novos = 0
    for chave in alvos:
        portal, slug, dirc, rotulo = COLUNAS[chave]
        locais = urls_locais(dirc, portal)
        crawl = crawl_conjur if portal == "conjur" else crawl_migalhas
        remotos = crawl(slug, args.paginas)
        ident = chave_migalhas if portal == "migalhas" else (lambda u: u.rstrip("/"))
        novos = [u for u in remotos if ident(u) not in locais]
        print(f"\n### {chave}  [{portal}]  local={len(locais)}  índice={len(remotos)}  NOVOS={len(novos)}")
        for u in novos:
            print("   +", u)
        total_novos += len(novos)

        if args.baixar and novos:
            baixar = baixar_conjur if portal == "conjur" else baixar_migalhas
            for u in novos:
                try:
                    d, t, dt = baixar(u, dirc, rotulo)
                    print(f"   OK {dt} | {t[:70]}")
                except Exception as e:
                    print(f"   ERRO {u} -> {e}")
                time.sleep(0.6)

    print(f"\n== TOTAL de artigos novos: {total_novos}")


if __name__ == "__main__":
    main()
