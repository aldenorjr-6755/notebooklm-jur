#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sobe para um notebook do NotebookLM apenas os .md do corpus local que ainda
NÃO estão lá.

Diff por duas chaves, porque as fontes antigas foram adicionadas por URL e as
novas entram como arquivo: (a) data+slug extraídos da URL da fonte e (b) título
normalizado. Sem isso, o mesmo artigo entra duas vezes.

Uso:
  python subir_novos.py <dir_corpus> <notebook_id> [--desde AAAA-MM-DD] [--so-listar]
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, unicodedata

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = r"C:\Users\alden\.notebooklm"
MESES = {"jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
         "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def iso(data: str) -> str:
    m = re.match(r"(\d{4})-([a-z]{3})-(\d{2})", data)
    return f"{m.group(1)}-{MESES.get(m.group(2),'00')}-{m.group(3)}" if m else data


def chave_url(u: str) -> str:
    u = u.replace("\r", "").strip()
    m = re.search(r"/(\d{4}-[a-z]{3}-\d{2})/([^/?#]+)", u)          # ConJur
    if m:
        return f"{iso(m.group(1))}/{re.sub(r'-\d+$', '', m.group(2))}"
    m = re.search(r"/coluna/[^/]+/(\d+)/", u + "/")                  # Migalhas: ID
    return m.group(1) if m else u.rstrip("/")


def cli(*args) -> str:
    nlm = shutil.which("nlm")   # o modulo do pacote e notebooklm_tools; `-m` com o nome curto nao existe
    if nlm is None:
        raise SystemExit("[ERRO] CLI `nlm` nao encontrada no PATH.")
    p = subprocess.run([nlm, *args],
                       capture_output=True, encoding="utf-8", errors="replace", cwd=RAIZ)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[-500:])
    return p.stdout


def chave_arquivo(nome: str) -> str | None:
    """As fontes antigas foram subidas como ARQUIVO — o título da fonte é o
    nome do .md, não o título do artigo. Daí extrair a mesma chave dele."""
    nome = re.sub(r"\.md$", "", nome.strip())
    m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d+)_", nome)          # Migalhas: data_id_slug
    if m:
        return m.group(2)
    m = re.match(r"(\d{4}-[a-z]{3}-\d{2})[_-](.+)$", nome)      # ConJur: data_slug
    if m:
        return f"{iso(m.group(1))}/{re.sub(r'-\d+$', '', m.group(2))}"
    return None


def data_do_titulo(nome: str) -> str | None:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", nome.strip())
    if m:
        return m.group(1)
    m = re.match(r"(\d{4}-[a-z]{3}-\d{2})", nome.strip())
    return iso(m.group(1)) if m else None


def fontes_do_notebook(nb: str):
    d = json.loads(cli("source", "list", nb, "--json"))
    s = d.get("sources", d) if isinstance(d, dict) else d
    chaves, titulos, datas = set(), set(), set()
    for x in s:
        t = x.get("title", "") or ""
        if x.get("url"):
            chaves.add(chave_url(x["url"]))
        k = chave_arquivo(t)
        if k:
            chaves.add(k)
        dt = data_do_titulo(t)
        if dt:
            datas.add(dt)
        titulos.add(norm(re.sub(r"\.md$", "", t)))
    return chaves, titulos, datas, len(s)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    dirc, nb = argv[0], argv[1]
    desde = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--desde=")), None)
    ate = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--ate=")), None)
    so_listar = "--so-listar" in sys.argv

    por_data = "--por-data" in sys.argv
    chaves, titulos, datas, n = fontes_do_notebook(nb)
    print(f"notebook {nb}: {n} fontes")

    base = os.path.join(RAIZ, dirc, "fontes")
    pendentes = []
    for fn in sorted(os.listdir(base)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(base, fn)
        cab = open(p, encoding="utf-8", errors="replace").read(900)
        u = re.search(r"^url:\s*(\S+)", cab, re.M)
        t = re.search(r"^titulo:\s*(.+)$", cab, re.M)
        d = re.search(r"^data:\s*(\S+)", cab, re.M)
        data = iso(d.group(1)) if d else "0000-00-00"
        if desde and data < desde:
            continue
        if ate and data > ate:
            continue
        if u and chave_url(u.group(1)) in chaves:
            continue
        if chave_arquivo(fn) and chave_arquivo(fn) in chaves:
            continue
        if t and norm(t.group(1)) in titulos:
            continue
        if norm(re.sub(r"\.md$", "", fn)) in titulos:
            continue
        if por_data and data in datas:      # coluna com no máx. 1 artigo por dia
            continue
        pendentes.append((p, t.group(1).strip() if t else fn, data))

    print(f"{dirc}: {len(pendentes)} a subir")
    for p, t, data in pendentes:
        print(f"   {data}  {t[:72]}")
    if so_listar or not pendentes:
        return

    ok = 0
    for p, t, data in pendentes:
        try:
            cli("source", "add", nb, "--file", p, "--title", t[:150])
            ok += 1
            print(f"   OK {data} {t[:60]}")
        except Exception as e:
            print(f"   ERRO {t[:60]} -> {e}")
    print(f"FIM: {ok}/{len(pendentes)} subidas em {nb}")


if __name__ == "__main__":
    main()
