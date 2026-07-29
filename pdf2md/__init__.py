#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pdf2md — conversor de PDF para Markdown paginado.

Feito para os quatro tipos de documento que passam por aqui: processos do
PJe, livros, decisoes judiciais e laudos periciais com imagens.

    from pdf2md import converter, converter_lote, coletar_pdfs
    r = converter("laudo.pdf", perfil="laudo")
    print(r.resumo())

Linha de comando:  python -m pdf2md --ajuda
Interface grafica: python -m pdf2md --gui   (ou PDF2MD.bat)
"""
from .ambiente import diagnostico, texto_diagnostico, idiomas_disponiveis
from .perfis import Perfil, PERFIS, ORDEM, obter
from .nucleo import (
    Pagina,
    Resultado,
    coletar_pdfs,
    converter,
    converter_lote,
    detectar_perfil,
)

__version__ = "1.0.0"

__all__ = [
    "Pagina",
    "Perfil",
    "Resultado",
    "PERFIS",
    "ORDEM",
    "coletar_pdfs",
    "converter",
    "converter_lote",
    "detectar_perfil",
    "diagnostico",
    "idiomas_disponiveis",
    "obter",
    "texto_diagnostico",
    "__version__",
]
