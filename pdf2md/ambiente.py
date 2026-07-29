#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Localizacao de binarios e diagnostico de dependencias.

Duas situacoes:

* Rodando do fonte, o Tesseract e o Ghostscript costumam estar instalados
  FORA do PATH nesta maquina (ver memoria `watcher-pdf-ocr-md`).
* Rodando do executavel standalone, o Tesseract vem DENTRO do pacote e nao
  se deve depender de nada instalado na maquina.

Em ambos os casos este modulo encontra os binarios e os publica no PATH do
processo ANTES de qualquer import que dependa deles. O que esta empacotado
tem prioridade sobre o que esta instalado.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

EMPACOTADO = bool(getattr(sys, "frozen", False))


def raiz_recursos() -> Path:
    """Pasta onde vivem os recursos: o bundle, se congelado; senao o pacote."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base)
    return Path(__file__).resolve().parent


# --------------------------------------------------------------------------
# Caminhos candidatos (o primeiro que existir vence; o empacotado vem antes)
# --------------------------------------------------------------------------
def _candidatos_tesseract() -> list[str]:
    r = raiz_recursos()
    return [
        str(r / "tesseract"),                       # dentro do executavel
        str(r.parent / "tesseract"),                # ao lado do executavel
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
        r"C:\Users\alden\AppData\Local\Programs\Tesseract-OCR",
    ]


def _candidatos_tessdata() -> list[str]:
    r = raiz_recursos()
    return [
        str(r / "tesseract" / "tessdata"),
        str(r.parent / "tesseract" / "tessdata"),
        r"C:\Users\alden\.notebooklm\tessdata",
        r"C:\Program Files\Tesseract-OCR\tessdata",
    ]


CAND_GHOSTSCRIPT = [
    r"C:\Program Files\PDF24\gs\bin",
    r"C:\Program Files\gs\gs10.03.1\bin",
    r"C:\Program Files\gs\gs10.02.1\bin",
]

_preparado = False


def _primeiro_dir(candidatos: list[str]) -> str | None:
    for d in candidatos:
        if d and os.path.isdir(d):
            return d
    return None


def preparar() -> dict:
    """Publica Tesseract/Ghostscript no PATH e aponta o TESSDATA_PREFIX.

    Idempotente. Retorna o dicionario de diagnostico.
    """
    global _preparado
    diag: dict[str, object] = {}

    tess_dir = _primeiro_dir(_candidatos_tesseract())
    gs_dir = _primeiro_dir(CAND_GHOSTSCRIPT)
    tessdata = _primeiro_dir(_candidatos_tessdata())

    for d in (tess_dir, gs_dir):
        if d and d not in os.environ.get("PATH", ""):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    if tessdata:
        os.environ["TESSDATA_PREFIX"] = tessdata

    exe = shutil.which("tesseract")
    if not exe and tess_dir:
        cand = os.path.join(tess_dir, "tesseract.exe")
        exe = cand if os.path.isfile(cand) else None

    if exe:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = exe
        except ImportError:
            pass

    diag["tesseract"] = exe
    diag["ghostscript"] = shutil.which("gswin64c") or shutil.which("gs")
    diag["tessdata"] = tessdata
    diag["idiomas"] = idiomas_disponiveis(tessdata)
    diag["tesseract_embutido"] = bool(
        exe and str(raiz_recursos()).lower() in str(Path(exe).resolve()).lower())
    _preparado = True
    return diag


def idiomas_disponiveis(tessdata: str | None = None) -> list[str]:
    """Lista os idiomas de OCR instalados (pelos .traineddata)."""
    tessdata = (tessdata or os.environ.get("TESSDATA_PREFIX")
                or _primeiro_dir(_candidatos_tessdata()))
    if not tessdata or not os.path.isdir(tessdata):
        return []
    return sorted(p.stem for p in Path(tessdata).glob("*.traineddata"))


def diagnostico() -> dict:
    """Checagem completa: binarios + modulos Python. Nao levanta excecao."""
    if not _preparado:
        preparar()

    exe = shutil.which("tesseract")
    if not exe:
        cand = _primeiro_dir(_candidatos_tesseract())
        if cand and os.path.isfile(os.path.join(cand, "tesseract.exe")):
            exe = os.path.join(cand, "tesseract.exe")

    d: dict[str, object] = {
        "python": sys.version.split()[0],
        "empacotado": EMPACOTADO,
        "tesseract": exe,
        "tesseract_embutido": bool(
            exe and str(raiz_recursos()).lower() in str(Path(exe).resolve()).lower()),
        "ghostscript": shutil.which("gswin64c") or shutil.which("gs"),
        "tessdata": os.environ.get("TESSDATA_PREFIX"),
        "idiomas": idiomas_disponiveis(),
    }

    modulos = {}
    for nome, rotulo in (
        ("fitz", "PyMuPDF"),
        ("pymupdf4llm", "pymupdf4llm"),
        ("pytesseract", "pytesseract"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
    ):
        try:
            mod = __import__(nome)
            ver = getattr(mod, "__version__", None) or getattr(mod, "VersionBind", "")
            modulos[rotulo] = str(ver) or "ok"
        except Exception as exc:
            # Guardar a MENSAGEM, e nao um None mudo: num executavel empacotado
            # a causa costuma ser uma dependencia que ficou de fora, e sem o
            # texto do erro nao ha como saber qual.
            modulos[rotulo] = None
            d.setdefault("erros_import", {})[rotulo] = "%s: %s" % (
                type(exc).__name__, exc)
    d["modulos"] = modulos

    faltas = [k for k, v in modulos.items() if v is None and k in ("PyMuPDF",)]
    if not d["tesseract"]:
        faltas.append("Tesseract (OCR indisponivel)")
    d["faltas"] = faltas
    return d


def texto_diagnostico() -> str:
    d = diagnostico()
    linhas = [
        "Modo          : %s" % ("executavel standalone" if d["empacotado"]
                                else "codigo-fonte (Python %s)" % d["python"]),
        "Tesseract     : %s%s" % (d["tesseract"] or "NAO ENCONTRADO",
                                  "  [embutido no pacote]"
                                  if d["tesseract_embutido"] else ""),
        "Ghostscript   : %s" % (d["ghostscript"] or "nao encontrado (opcional)"),
        "TESSDATA      : %s" % (d["tessdata"] or "-"),
        "Idiomas OCR   : %s" % (", ".join(d["idiomas"]) or "nenhum"),
        "",
        "Modulos Python:",
    ]
    erros = d.get("erros_import") or {}
    for k, v in d["modulos"].items():
        linhas.append("  %-14s %s" % (k, v or "AUSENTE"))
        if k in erros:
            linhas.append("  %-14s   ^ %s" % ("", erros[k]))
    if d["faltas"]:
        linhas += ["", "PENDENCIAS: " + "; ".join(d["faltas"])]
    return "\n".join(linhas)


# Prepara o ambiente ja no import — antes que ocrmypdf/pytesseract procurem
# os binarios no PATH.
preparar()
