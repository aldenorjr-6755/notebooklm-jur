#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Converte a biblioteca de anexos (PDF/HTML) para Markdown paginado.

Origem : SegundoCerebro/Anexos/  (ou --origem)
Destino: ~/.notebooklm/biblioteca/{pdf,html,md}/ preservando a árvore relativa.

Convenção de página: `## [p. N]` (a mesma dos corpora já existentes), para que
os helpers que devolvem "página do PDF" continuem resolvendo no Markdown.

Verificações obrigatórias (perda silenciosa é o modo de falha conhecido):
  - páginas convertidas × páginas do PDF
  - caracteres por página (PDF escaneado → média baixa → marcar OCR PENDENTE)
  - bytes NUL (quebram o grep em silêncio) → saneados e reportados
"""
import argparse
import pathlib
import re
import shutil
import sys
import unicodedata

import fitz  # PyMuPDF

HOME = pathlib.Path.home()
DEST = HOME / ".notebooklm" / "biblioteca"
ORIGEM_PADRAO = HOME / "SegundoCerebro" / "Anexos"
LIMIAR_OCR = 120  # caracteres/página abaixo disso = provável PDF escaneado


def slug(nome):
    n = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9._-]+", "-", n).strip("-")


def limpa(txt):
    """Remove NUL e normaliza quebras — NUL faz o grep suprimir o arquivo inteiro."""
    nuls = txt.count("\x00")
    txt = txt.replace("\x00", "")
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{4,}", "\n\n\n", txt)
    return txt, nuls


def pdf_para_md(src, dst):
    doc = fitz.open(src)
    partes = [f"# {src.stem}", ""]
    chars = 0
    for i, pag in enumerate(doc, 1):
        t = pag.get_text("text") or ""
        chars += len(t.strip())
        partes.append(f"## [p. {i}]")
        partes.append("")
        partes.append(t.strip())
        partes.append("")
    n_pag = doc.page_count
    doc.close()
    texto, nuls = limpa("\n".join(partes))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(texto, encoding="utf-8")
    return {"paginas": n_pag, "chars": chars,
            "chars_pag": round(chars / n_pag) if n_pag else 0, "nuls": nuls}


def html_para_md(src, dst):
    from bs4 import BeautifulSoup
    bruto = src.read_bytes()
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            html = bruto.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sopa = BeautifulSoup(html, "html.parser")
    for tag in sopa(["script", "style"]):
        tag.decompose()
    linhas = [f"# {src.stem}", ""]
    for el in sopa.find_all(["h1", "h2", "h3", "p", "li", "td"]):
        t = " ".join(el.get_text(" ", strip=True).split())
        if not t:
            continue
        if el.name in ("h1", "h2", "h3"):
            linhas.append(f"\n## {t}\n")
        elif el.name == "li":
            linhas.append(f"- {t}")
        else:
            linhas.append(t)
    texto, nuls = limpa("\n".join(linhas))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(texto, encoding="utf-8")
    return {"paginas": 0, "chars": len(texto), "chars_pag": 0, "nuls": nuls}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--origem", nargs="+", default=[str(ORIGEM_PADRAO)],
                    help="uma ou mais pastas de origem; o relatório cobre todas de uma vez")
    ap.add_argument("--mover-original", action="store_true",
                    help="copia o original para biblioteca/pdf|html (padrão: sim)")
    a = ap.parse_args()

    arquivos = []          # (arquivo, caminho relativo no destino)
    for o in a.origem:
        origem = pathlib.Path(o)
        if not origem.exists():
            sys.exit(f"origem não encontrada: {origem}")
        # pasta "Anexos" fica na raiz do destino; qualquer outra vira subpasta homônima
        prefixo = pathlib.Path("") if origem.name.lower() == "anexos" else pathlib.Path(origem.name)
        for p in sorted(origem.rglob("*")):
            if p.is_file() and p.suffix.lower() in (".pdf", ".html", ".htm", ".txt"):
                arquivos.append((p, prefixo / p.relative_to(origem)))
    print(f"{len(arquivos)} arquivos a converter\n", flush=True)

    rel = []
    for i, (src, relpath) in enumerate(arquivos, 1):
        destino_md = DEST / "md" / relpath.parent / (slug(src.stem) + ".md")
        try:
            if src.suffix.lower() == ".pdf":
                info = pdf_para_md(src, destino_md)
                sub = "pdf"
            elif src.suffix.lower() == ".txt":
                texto, nuls = limpa(src.read_text(encoding="utf-8", errors="replace"))
                destino_md.parent.mkdir(parents=True, exist_ok=True)
                destino_md.write_text(f"# {src.stem}\n\n{texto}", encoding="utf-8")
                info = {"paginas": 0, "chars": len(texto), "chars_pag": 0, "nuls": nuls}
                sub = "html"
            else:
                info = html_para_md(src, destino_md)
                sub = "html"
            guardado = DEST / sub / relpath
            guardado.parent.mkdir(parents=True, exist_ok=True)
            if not guardado.exists():
                shutil.copy2(src, guardado)
            info.update(arquivo=str(relpath), md=str(destino_md.relative_to(DEST)),
                        kb_orig=round(src.stat().st_size / 1024),
                        kb_md=round(destino_md.stat().st_size / 1024), erro="")
        except Exception as e:
            info = {"arquivo": str(relpath), "md": "", "paginas": 0, "chars": 0,
                    "chars_pag": 0, "nuls": 0, "kb_orig": round(src.stat().st_size / 1024),
                    "kb_md": 0, "erro": str(e)[:120]}
        rel.append(info)
        if i % 20 == 0 or i == len(arquivos):
            print(f"  {i}/{len(arquivos)}", flush=True)

    ocr = [r for r in rel if r["paginas"] and r["chars_pag"] < LIMIAR_OCR]
    err = [r for r in rel if r["erro"]]
    nul = [r for r in rel if r["nuls"]]

    L = ["# Relatório de conversão da biblioteca (PDF/HTML → Markdown)", "",
         f"- Arquivos processados: **{len(rel)}**",
         f"- Páginas convertidas: **{sum(r['paginas'] for r in rel):,}**".replace(",", "."),
         f"- Erros: **{len(err)}** · NUL saneados: **{len(nul)}** · Suspeita de PDF escaneado: **{len(ocr)}**",
         "",
         "Convenção: cada página vira `## [p. N]` — a mesma dos corpora, para que as páginas",
         "devolvidas pelos helpers resolvam também no Markdown.", ""]
    if err:
        L += ["## Erros", "", "| Arquivo | Erro |", "|---|---|"]
        L += [f"| `{r['arquivo']}` | {r['erro']} |" for r in err] + [""]
    if ocr:
        L += ["## OCR pendente (texto/página abaixo do limiar — provável PDF escaneado)", "",
              "| Arquivo | Páginas | Chars/pág |", "|---|---:|---:|"]
        L += [f"| `{r['arquivo']}` | {r['paginas']} | {r['chars_pag']} |" for r in ocr] + [""]
    L += ["## Inventário", "", "| Arquivo | Págs | Chars/pág | KB orig | KB md |", "|---|---:|---:|---:|---:|"]
    for r in sorted(rel, key=lambda x: -x["kb_orig"]):
        L.append(f"| `{r['arquivo']}` | {r['paginas'] or '—'} | {r['chars_pag'] or '—'} | {r['kb_orig']} | {r['kb_md']} |")
    (DEST / "RELATORIO-CONVERSAO.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"\nOK — {len(rel)} arquivos, {sum(r['paginas'] for r in rel)} páginas")
    print(f"erros={len(err)} nul={len(nul)} ocr_pendente={len(ocr)}")
    print(f"relatório: {DEST/'RELATORIO-CONVERSAO.md'}")


if __name__ == "__main__":
    main()
