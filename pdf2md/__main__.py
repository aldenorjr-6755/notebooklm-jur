#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ponto de entrada: `python -m pdf2md`.

Sem argumentos e com terminal disponivel, mostra a ajuda. Para abrir a
janela do aplicativo, use `python -m pdf2md --gui` (ou o PDF2MD.bat).
"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
