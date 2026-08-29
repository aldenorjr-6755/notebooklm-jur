#!/usr/bin/env python3
"""Converte DOCX/PPTX/XLSX/EPUB e afins em Markdown, com checagem de perda silenciosa.

Irmao de pdf_para_markdown.py: implementa a REGRA CANONICA de ~/.claude/CLAUDE.md
("Conversao de fontes para Markdown") para os formatos que o helper de PDF nao
cobre. Motor: markitdown (Microsoft) -- mammoth para DOCX, openpyxl para XLSX.

Uso:
    python doc_para_markdown.py ARQUIVO.docx [ARQUIVO2 ...]
    python doc_para_markdown.py -o DESTINO/ ARQUIVO.pptx
    python doc_para_markdown.py --check ARQUIVO.xlsx     # so mede, nao escreve

NAO converte:
    PDF  -> use pdf2md / pdf_para_markdown.py. O markitdown NAO pagina: junta as
            paginas com quebra dupla e destroi a convencao `## [p. N]`.
    HTML -> use html_para_markdown.py (as quatro travas do bake-off).
    RTF  -> ver tools/rtf_stj_para_md.py.

Codigo de saida 3 = SUSPEITA DE PERDA: o Markdown tem menos texto que o censo
independente feito no proprio arquivo. NAO destile antes de investigar --
perda de conversao e silenciosa (memoria: conversao-pdf-md-perda-silenciosa).

Chame sempre por `python arquivo.py`. O Smart App Control desta maquina
bloqueia os shims .exe que o pip gera.
"""
import argparse
import os
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

try:
    from markitdown import MarkItDown
except ImportError:
    sys.exit('markitdown ausente. Instale: '
             'python -m pip install "markitdown[docx,pptx,xlsx,xls,outlook]"')

# Em arquivo integro os dois lados batem EXATO (medido: 100.0% nos 4 .docx reais
# do acervo), porque ambos contam os mesmos nos de texto por caminhos diferentes.
# Entao a tolerancia e estreita de proposito: com 0.90 uma caixa de texto perdida
# valendo 10% do documento passava raspando (medido: 90.3%).
LIMIAR_PERDA = 0.98
DELTA_ABSOLUTO = 200  # ...e um piso absoluto, para perda pequena em arquivo grande

ACEITOS = {'.docx', '.pptx', '.xlsx', '.xls', '.epub',
           '.csv', '.json', '.xml', '.zip', '.msg'}

RECUSADOS = {
    '.pdf':  'PDF nao passa por aqui: o markitdown NAO pagina. '
             'Use: python ~/.notebooklm/pdf_para_markdown.py',
    '.html': 'HTML tem helper proprio (decodificacao + html5lib + regua). '
             'Use: python ~/.notebooklm/html_para_markdown.py',
    '.htm':  'HTML tem helper proprio (decodificacao + html5lib + regua). '
             'Use: python ~/.notebooklm/html_para_markdown.py',
    '.rtf':  'RTF tem helper proprio. '
             'Use: python ~/.notebooklm/tools/rtf_stj_para_md.py',
}


def alnum(s):
    """Conta so letras e digitos: imune ao ruido de sintaxe Markdown."""
    return sum(1 for c in s if c.isalnum())


def _coleta(el, saida):
    """Anda a arvore somando nos de texto, PULANDO o ramo mc:Fallback.

    Caixa de texto do Word 2013+ vem em mc:AlternateContent com o MESMO texto
    duas vezes (mc:Choice moderno + mc:Fallback em VML). Contar os dois dobra a
    regua e produz alarme falso. O conversor le so um; a regua tambem.
    """
    tag = el.tag.rsplit('}', 1)[-1]
    if tag == 'Fallback':
        return
    if tag == 't' and el.text:
        saida.append(el.text)
    for f in el:
        _coleta(f, saida)


def _texto_xml(zf, membros):
    """Junta todo no de texto (localname 't') dos membros XML do pacote OOXML.

    Censo independente do conversor: le o XML cru, entao enxerga tambem o texto
    dentro de caixas de texto (w:txbxContent) e de tabelas -- exatamente onde a
    perda silenciosa acontece.

    Devolve (texto, falhas). Falha de parse NAO pode virar zero silencioso: quem
    chama tem de saber que a regua nao mediu, em vez de ler isso como "integro".
    """
    saida, falhas = [], []
    for m in membros:
        try:
            raiz = ET.fromstring(zf.read(m))
        except (KeyError, ET.ParseError) as e:
            falhas.append('%s (%s)' % (m, type(e).__name__))
            continue
        _coleta(raiz, saida)
    return ''.join(saida), falhas


class ReguaQuebrada(Exception):
    """A regua nao conseguiu medir. NUNCA pode ser lido como 'conversao integra'."""


def censo(caminho, ext):
    """Regua independente. Devolve (chars_alnum, rotulo, nota) ou (None, None, motivo).

    Levanta ReguaQuebrada se o XML nao parseou: sem medicao nao ha veredicto.
    """
    if ext == '.docx':
        with zipfile.ZipFile(caminho) as zf:
            nomes = zf.namelist()
            corpo = [n for n in nomes if n in (
                'word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml')]
            mob = [n for n in nomes
                   if re.match(r'word/(header|footer)\d*\.xml$', n)]
            if 'word/document.xml' not in nomes:
                raise ReguaQuebrada('word/document.xml ausente do pacote')
            t_corpo, falhas = _texto_xml(zf, corpo)
            t_mob, _ = _texto_xml(zf, mob)
        if falhas:
            raise ReguaQuebrada('XML ilegivel: ' + '; '.join(falhas))
        nota = ('cabecalho/rodape com %d chars, fora da comparacao' % alnum(t_mob)
                ) if alnum(t_mob) else ''
        return alnum(t_corpo), 'XML cru w:t (corpo+notas)', nota

    if ext == '.pptx':
        with zipfile.ZipFile(caminho) as zf:
            nomes = zf.namelist()
            slides = [n for n in nomes
                      if re.match(r'ppt/slides/slide\d+\.xml$', n)]
            notas = [n for n in nomes
                     if re.match(r'ppt/notesSlides/notesSlide\d+\.xml$', n)]
            if not slides:
                raise ReguaQuebrada('nenhum ppt/slides/slideN.xml no pacote')
            t_sl, falhas = _texto_xml(zf, slides)
            t_nt, _ = _texto_xml(zf, notas)
        if falhas:
            raise ReguaQuebrada('XML ilegivel: ' + '; '.join(falhas))
        if alnum(t_nt):
            nota = ('%d slides; notas do orador com %d chars, fora da comparacao'
                    % (len(slides), alnum(t_nt)))
        else:
            nota = '%d slides' % len(slides)
        return alnum(t_sl), 'XML cru a:t (slides)', nota

    if ext == '.xlsx':
        try:
            import openpyxl
        except ImportError:
            raise ReguaQuebrada('openpyxl ausente: nao ha como medir .xlsx')
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        total, celulas = 0, 0
        for ws in wb.worksheets:
            for linha in ws.iter_rows(values_only=True):
                for v in linha:
                    if v is not None and str(v).strip():
                        celulas += 1
                        total += alnum(str(v))
        wb.close()
        return total, 'openpyxl (celulas nao vazias)', '%d celulas' % celulas

    return None, None, 'sem regua independente para %s' % ext


def _pistas(caminho, ext):
    """Causas conhecidas de perda, para o alerta dizer o que investigar."""
    achados = []
    if ext not in ('.docx', '.pptx'):
        return achados
    try:
        with zipfile.ZipFile(caminho) as zf:
            bruto = zf.read('word/document.xml' if ext == '.docx'
                            else 'ppt/slides/slide1.xml').decode('utf-8', 'replace')
    except Exception:
        return achados
    if 'wps:txbx' in bruto and 'mc:Fallback' not in bruto:
        achados.append('ha caixa de texto DrawingML (wps:txbx) SEM fallback VML; '
                       'o mammoth nao le esse formato e descarta o conteudo.')
    if '<w:object' in bruto or 'oleObject' in bruto:
        achados.append('ha objeto OLE embutido; o texto dele nao e convertido.')
    if 'w:instrText' in bruto:
        achados.append('ha campo automatico (w:instrText); confira sumario/refs.')
    return achados


def limpa(txt):
    """Remove NUL (quebram o grep em silencio) e normaliza em NFC."""
    nuls = txt.count('\x00')
    txt = unicodedata.normalize('NFC', txt.replace('\x00', ''))
    return txt, nuls


def _versao():
    try:
        import importlib.metadata as m
        return m.version('markitdown')
    except Exception:
        return '?'


def converter(caminho, destino=None, escrever=True):
    """Devolve 0 (integro), 3 (suspeita de perda) ou 1 (erro)."""
    nome = os.path.basename(caminho)
    stem, ext = os.path.splitext(nome)
    ext = ext.lower()

    if ext in RECUSADOS:
        print('%-40s RECUSADO' % nome[:40])
        print('   %s' % RECUSADOS[ext])
        return 1
    if ext not in ACEITOS:
        print('%-40s formato nao suportado (%s)' % (nome[:40], ext))
        return 1

    tam = os.path.getsize(caminho)
    try:
        md = MarkItDown(enable_plugins=False).convert(caminho).text_content
    except Exception as e:
        print('%-40s ERRO: %s' % (nome[:40], type(e).__name__))
        print('   %s' % str(e).split('\n')[0][:200])
        return 1

    md, nuls = limpa(md)
    md_alnum = alnum(md)

    quebrada = None
    try:
        ref, rotulo, nota = censo(caminho, ext)
    except ReguaQuebrada as e:
        ref, rotulo, nota, quebrada = None, None, '', str(e)
    except Exception as e:
        ref, rotulo, nota = None, None, '',
        quebrada = '%s: %s' % (type(e).__name__, str(e)[:120])

    if ref:
        pct = 100.0 * md_alnum / ref
        print('%-40s %8d chars md | regua %8d | %5.1f%% | %-4s %6.1f KB'
              % (nome[:40], len(md), ref, pct, ext[1:], tam / 1024))
    else:
        pct = None
        print('%-40s %8d chars md | regua    ---- |   --   | %-4s %6.1f KB'
              % (nome[:40], len(md), ext[1:], tam / 1024))

    if nota:
        print('   nota: %s' % nota)
    if nuls:
        print('   %d byte(s) NUL removido(s).' % nuls)

    perda = False
    if quebrada:
        perda = True
        print('   ATENCAO: a REGUA QUEBROU -- %s' % quebrada)
        print('   Sem medicao nao ha veredicto de integridade. NAO destile.')
    elif ref and (pct < LIMIAR_PERDA * 100 or (ref - md_alnum) > DELTA_ABSOLUTO):
        perda = True
        print('   ATENCAO: o Markdown tem %.1f%% do texto que existe no arquivo '
              '(regua: %s).' % (pct, rotulo))
        print('   Faltam ~%d caracteres. Provavel perda em caixa de texto, tabela '
              'ou objeto embutido.' % (ref - md_alnum))
        for pista in _pistas(caminho, ext):
            print('   PISTA: %s' % pista)
        print('   NAO destile antes de investigar.')
    elif ref is None:
        print('   AVISO: sem regua independente (%s). A integridade NAO foi '
              'verificada.' % nota)

    if escrever:
        out_dir = destino or os.path.dirname(os.path.abspath(caminho))
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, stem + '.md')
        if ref:
            linha_regua = ('> Extraidos %d caracteres alfanumericos; regua independente '
                           '(%s): %d (%.1f%%).\n' % (md_alnum, rotulo, ref, pct))
        else:
            linha_regua = ('> Extraidos %d caracteres alfanumericos; SEM regua '
                           'independente (%s) -- integridade nao verificada.\n'
                           % (md_alnum, nota))
        cab = ('# %s\n\n'
               '> Convertido de `%s` (%.1f KB) com markitdown %s.\n'
               '%s'
               '> Formato sem paginacao: NAO ha ancora `## [p. N]` neste arquivo.\n'
               '> Original preservado.\n'
               % (stem, nome, tam / 1024, _versao(), linha_regua))
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(cab + '\n' + md.strip() + '\n')
        print('   -> %s' % out)

    return 3 if perda else 0


def main():
    ap = argparse.ArgumentParser(
        description='DOCX/PPTX/XLSX/EPUB -> Markdown medido (regra canonica). '
                    'PDF NAO passa por aqui: use pdf_para_markdown.py.')
    ap.add_argument('arquivos', nargs='+')
    ap.add_argument('-o', '--out', default=None, help='diretorio de destino')
    ap.add_argument('--check', action='store_true', help='so medir, nao escrever')
    a = ap.parse_args()

    suspeitos, erros = 0, 0
    for p in a.arquivos:
        if not os.path.isfile(p):
            print('ausente: %s' % p)
            erros += 1
            continue
        r = converter(p, a.out, escrever=not a.check)
        if r == 3:
            suspeitos += 1
        elif r == 1:
            erros += 1

    if suspeitos:
        print('\nVEREDICTO: SUSPEITA DE PERDA em %d arquivo(s). NAO destile ainda.'
              % suspeitos)
        return 3
    if erros:
        print('\nVEREDICTO: %d arquivo(s) nao convertido(s).' % erros)
        return 1
    print('\nVEREDICTO: conversao integra.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
