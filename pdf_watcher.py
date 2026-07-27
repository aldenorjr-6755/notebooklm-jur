#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pdf_watcher.py — Vigia uma pasta e converte automaticamente cada PDF que
cair nela em Markdown, aplicando OCR (OCRmyPDF + Tesseract) e extraindo o
texto estruturado com PyMuPDF4LLM.

Autossuficiente: faz a deteccao da camada de texto, escolhe o modo de OCR,
trata arquivos ainda em download e evita reprocessar o que ja foi convertido.

Uso manual:
    python pdf_watcher.py
    python pdf_watcher.py --watch "C:\\caminho" --out "C:\\saida" --lang por
    python pdf_watcher.py --sweep        # converte tambem os PDFs ja existentes
    python pdf_watcher.py --once "arquivo.pdf"   # converte 1 PDF e sai
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuracao do ambiente (Tesseract / Ghostscript / idioma) ANTES de
# importar ocrmypdf — ele localiza os binarios pelo PATH no momento do uso.
# ---------------------------------------------------------------------------
TESSERACT_DIR = r"C:\Program Files\Tesseract-OCR"
GHOSTSCRIPT_DIR = r"C:\Program Files\PDF24\gs\bin"
TESSDATA_DIR = r"C:\Users\alden\.notebooklm\tessdata"

for _d in (TESSERACT_DIR, GHOSTSCRIPT_DIR):
    if _d and os.path.isdir(_d) and _d not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
if os.path.isdir(TESSDATA_DIR):
    os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

import fitz  # PyMuPDF
import ocrmypdf
import pymupdf4llm

# ---------------------------------------------------------------------------
# Padroes (sobrescreviveis por linha de comando)
# ---------------------------------------------------------------------------
DEFAULT_WATCH = r"C:\Users\alden\Downloads"
DEFAULT_OUT = r"C:\Users\alden\Downloads\saida_md"
DEFAULT_LANG = "por"
LOG_FILE = r"C:\Users\alden\.notebooklm\pdf_watcher.log"

# Extensoes de arquivos parciais/temporarios que NAO devem ser processados.
IGNORE_SUFFIXES = (".crdownload", ".part", ".tmp", ".partial", ".opdownload")

STABLE_CHECKS = 3       # leituras de tamanho iguais para considerar "pronto"
STABLE_INTERVAL = 1.5   # segundos entre as leituras

log = logging.getLogger("pdf_watcher")


def setup_logging() -> None:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    # Console so quando ha terminal (no autostart com pythonw nao ha).
    if sys.stderr is not None:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(sh)


def wait_until_stable(path: Path) -> bool:
    """Espera o arquivo parar de crescer (download/copia concluida)."""
    last = -1
    stable = 0
    for _ in range(120):  # ~3 min de teto
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size == last and size > 0:
            stable += 1
            if stable >= STABLE_CHECKS:
                return True
        else:
            stable = 0
            last = size
        time.sleep(STABLE_INTERVAL)
    return False


def pick_ocr_mode(pdf: Path) -> str:
    """Decide entre 'skip' (so paginas sem texto) e 'force' (refaz tudo).

    Se a maioria das paginas vem quase sem texto extraivel, o PDF e' um
    digitalizado/imagem (tipico do PJe) -> force. Caso contrario, skip.
    """
    try:
        doc = fitz.open(pdf)
    except Exception:
        return "force"
    try:
        pages = doc.page_count or 1
        empty = sum(1 for p in doc if len(p.get_text("text").strip()) < 20)
    finally:
        doc.close()
    return "force" if empty / pages > 0.5 else "skip"


def convert(pdf: Path, out_dir: Path, lang: str) -> bool:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / (pdf.stem + ".md")

    if md_path.exists() and md_path.stat().st_mtime >= pdf.stat().st_mtime:
        log.info("Ja convertido (md atual), pulando: %s", pdf.name)
        return True

    mode = pick_ocr_mode(pdf)
    log.info("Convertendo %s  (modo OCR: %s, lang: %s)", pdf.name, mode, lang)

    searchable = out_dir / (pdf.stem + "_ocr.pdf")
    ocr_kwargs = dict(
        language=lang,
        output_type="pdf",
        optimize=1,
        progress_bar=False,
        deskew=(mode == "force"),
        rotate_pages=(mode == "force"),
    )
    if mode == "force":
        ocr_kwargs["force_ocr"] = True
    else:
        ocr_kwargs["skip_text"] = True

    try:
        ocrmypdf.ocr(str(pdf), str(searchable), **ocr_kwargs)
    except ocrmypdf.exceptions.PriorOcrFoundError:
        # Ja tinha OCR e pedimos skip — usa o proprio PDF.
        searchable = pdf
    except Exception as exc:
        log.error("Falha no OCR de %s: %s", pdf.name, exc)
        return False

    try:
        md = pymupdf4llm.to_markdown(str(searchable))
        md_path.write_text(md, encoding="utf-8")
    except Exception as exc:
        log.error("Falha ao gerar Markdown de %s: %s", pdf.name, exc)
        return False
    finally:
        if searchable != pdf and searchable.exists():
            try:
                searchable.unlink()  # remove o PDF pesquisavel intermediario
            except OSError:
                pass

    log.info("OK -> %s", md_path)
    return True


def is_target(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(IGNORE_SUFFIXES):
        return False
    return path.suffix.lower() == ".pdf"


def process(path: Path, out_dir: Path, lang: str) -> None:
    if not is_target(path):
        return
    if not wait_until_stable(path):
        log.warning("Arquivo nao estabilizou, ignorando: %s", path.name)
        return
    try:
        convert(path, out_dir, lang)
    except Exception:
        log.exception("Erro inesperado processando %s", path.name)


def run_watch(watch: Path, out_dir: Path, lang: str, sweep: bool) -> None:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    if sweep:
        log.info("Varredura inicial dos PDFs existentes em %s", watch)
        for pdf in sorted(watch.glob("*.pdf")):
            process(pdf, out_dir, lang)

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                process(Path(event.src_path), out_dir, lang)

        def on_moved(self, event):
            # downloads concluem renomeando .crdownload -> .pdf
            if not event.is_directory:
                process(Path(event.dest_path), out_dir, lang)

    obs = Observer()
    obs.schedule(Handler(), str(watch), recursive=False)
    obs.start()
    log.info("Vigiando %s  ->  %s", watch, out_dir)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Encerrando por Ctrl+C")
    finally:
        obs.stop()
        obs.join()


def main() -> None:
    ap = argparse.ArgumentParser(description="Watcher PDF->Markdown com OCR")
    ap.add_argument("--watch", default=DEFAULT_WATCH, help="Pasta vigiada")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Pasta de saida dos .md")
    ap.add_argument("--lang", default=DEFAULT_LANG, help="Idioma(s) Tesseract")
    ap.add_argument("--sweep", action="store_true",
                    help="Converter tambem os PDFs ja existentes na pasta")
    ap.add_argument("--once", metavar="PDF",
                    help="Converter um unico PDF e sair")
    args = ap.parse_args()

    setup_logging()
    out_dir = Path(args.out)

    if args.once:
        ok = convert(Path(args.once), out_dir, args.lang)
        sys.exit(0 if ok else 1)

    watch = Path(args.watch)
    if not watch.is_dir():
        log.error("Pasta vigiada nao existe: %s", watch)
        sys.exit(1)
    run_watch(watch, out_dir, args.lang, args.sweep)


if __name__ == "__main__":
    main()
