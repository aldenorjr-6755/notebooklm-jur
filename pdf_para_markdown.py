#!/usr/bin/env python3
"""Converte PDF em Markdown paginado, com checagem de perda silenciosa.

Implementa a REGRA CANONICA de ~/.claude/CLAUDE.md ("Conversao de fontes para
Markdown"): PyMuPDF, paginacao `## [p. N]`, e medicao ANTES de destilar.

Uso:
    python pdf_para_markdown.py ARQUIVO.pdf [ARQUIVO2.pdf ...]
    python pdf_para_markdown.py -o DESTINO/ ARQUIVO.pdf
    python pdf_para_markdown.py --check ARQUIVO.pdf     # so mede, nao escreve

Saida: ARQUIVO.md ao lado do original (ou em DESTINO/), com cabecalho de
proveniencia. O original NUNCA e apagado nem alterado.

Codigo de saida 3 = ha paginas sem texto extraivel (provavel PDF-imagem):
rode OCR (skill pdf-ocr-to-markdown) em vez de confiar nesta conversao.
"""
import argparse
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit('PyMuPDF ausente. Instale: python -m pip install pymupdf')

LIMIAR_PAGINA_VAZIA = 20  # caracteres


def converter(caminho, destino=None, escrever=True):
    doc = fitz.open(caminho)
    nome = os.path.basename(caminho)
    stem = os.path.splitext(nome)[0]

    partes, por_pagina = [], []
    for i, page in enumerate(doc, start=1):
        t = (page.get_text('text') or '').replace('\r\n', '\n').strip()
        por_pagina.append(len(t))
        partes.append('## [p. %d]\n\n%s' % (
            i, t if t else '_[pagina sem texto extraivel]_'))

    total = sum(por_pagina)
    vazias = [i + 1 for i, n in enumerate(por_pagina) if n < LIMIAR_PAGINA_VAZIA]
    media = (total / len(por_pagina)) if por_pagina else 0
    tam_pdf = os.path.getsize(caminho)

    print('%-40s %4d pag | %8d chars | media %5.0f/pag | vazias %3d | pdf %6.1f KB'
          % (nome[:40], doc.page_count, total, media, len(vazias), tam_pdf / 1024))

    if vazias:
        amostra = ', '.join(str(p) for p in vazias[:20])
        extra = ' ...' if len(vazias) > 20 else ''
        print('   ATENCAO: %d pagina(s) sem texto -> provavel PDF-imagem. Paginas: %s%s'
              % (len(vazias), amostra, extra))
        print('   Use OCR (skill pdf-ocr-to-markdown); NAO confie nesta conversao.')

    if escrever:
        out_dir = destino or os.path.dirname(os.path.abspath(caminho))
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, stem + '.md')
        cab = ('# %s\n\n'
               '> Convertido de `%s` (%d paginas, %.1f KB) com PyMuPDF %s.\n'
               '> Paginacao preservada em `## [p. N]` para citacao verificavel.\n'
               '> Extraidos %d caracteres (media %.0f/pagina); paginas sem texto: %d.\n'
               % (stem, nome, doc.page_count, tam_pdf / 1024, fitz.VersionBind,
                  total, media, len(vazias)))
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(cab + '\n' + '\n\n'.join(partes) + '\n')
        print('   -> %s' % out)

    doc.close()
    return len(vazias)


def main():
    ap = argparse.ArgumentParser(description='PDF -> Markdown paginado (regra canonica).')
    ap.add_argument('pdfs', nargs='+')
    ap.add_argument('-o', '--out', default=None, help='diretorio de destino')
    ap.add_argument('--check', action='store_true', help='so medir, nao escrever')
    a = ap.parse_args()

    alerta = 0
    for p in a.pdfs:
        if not os.path.isfile(p):
            print('ausente: %s' % p)
            continue
        alerta += converter(p, a.out, escrever=not a.check)

    if alerta:
        print('\nVEREDICTO: OCR NECESSARIO (%d pagina[s] sem texto).' % alerta)
        return 3
    print('\nVEREDICTO: texto nativo, OCR dispensavel.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
