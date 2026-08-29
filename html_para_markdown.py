#!/usr/bin/env python3
"""Converte HTML em Markdown com as quatro travas medidas no bake-off de 2026-08-29.

Terceiro helper da REGRA CANONICA de ~/.claude/CLAUDE.md, ao lado de
pdf_para_markdown.py (PDF) e doc_para_markdown.py (Office). Motor: markitdown
(markdownify), que preserva tabela, link, negrito e hierarquia de titulo -- tudo
que o html_para_md() de tools/converter_biblioteca_md.py descarta.

Uso:
    python html_para_markdown.py ARQUIVO.html [ARQUIVO2 ...]
    python html_para_markdown.py -o DESTINO/ *.html
    python html_para_markdown.py --check ARQUIVO.html    # so mede, nao escreve

AS QUATRO TRAVAS (nenhuma e opcional; sem elas o markitdown destroi em silencio):

 1. DECODIFICAR NOS MESMOS  utf-8 -> cp1252 -> latin-1. Entregue os bytes crus e
    o charset-normalizer detecta cp1250: 0xBA deixa de ser "o" masculino e vira
    "s", entao "Art. 3o-A" some da busca. Medido: 19.711 caracteres corrompidos
    nos 16 HTMLs do Planalto.

 2. NORMALIZAR COM html5lib  O markitdown converte SO o <body>
    (soup.find("body") com html.parser). Os HTMLs do Planalto sao do Microsoft
    FrontPage e fecham o body cedo: no Codigo Civil sobram 600 caracteres dentro
    dele e a lei inteira fica fora. Saida: 797 caracteres, 0 artigos, sem erro.
    html5lib reconstroi a arvore como o navegador. lxml NAO serve (643 chars).

 3. DESDOBRAR AS QUEBRAS MOLES  O markdownify preserva as quebras de linha do
    HTML e parte a frase no meio ("Art. 3o-C. A" / "competencia do juiz..."),
    o que quebra qualquer grep. Juntar linhas de um mesmo bloco e NEUTRO na
    renderizacao (quebra simples em Markdown ja vira espaco) e devolve o texto
    a busca. Tabela, titulo, lista e citacao sao preservados.

 4. REGUA  Conta caracteres e artigos no HTML de origem e na saida. Exit 3 se
    cair. Sem isso o colapso do Codigo Civil passa de novo, calado.

Codigo de saida 3 = SUSPEITA DE PERDA. NAO destile antes de investigar.
"""
import argparse
import os
import re
import sys
import unicodedata

try:
    from markitdown import MarkItDown
except ImportError:
    sys.exit('markitdown ausente. Instale: python -m pip install markitdown')
try:
    from bs4 import BeautifulSoup
    import html5lib  # noqa: F401  -- exigido pela trava 2
except ImportError:
    sys.exit('trava 2 exige beautifulsoup4 e html5lib. '
             'Instale: python -m pip install beautifulsoup4 html5lib')

LIMIAR_PERDA = 0.98
ACEITOS = {'.html', '.htm', '.xhtml'}

# Simetrico: aplicado igual nos dois lados, um falso positivo ("Art. 338 - Reingressar")
# aparece nos dois e se cancela. A regua e comparacao, nao verdade absoluta.
RE_ARTIGO = re.compile(r'Art\.?\s*(\d+)\s*(?:[ºo°]\s*)?(?:-\s*([A-Z])(?![a-zà-ú]))?')
RE_BLOCO = re.compile(r'^(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|>|\||---|\*\*\*|___)')
# Bloco que SEMPRE interrompe o paragrafo.
RE_BLOCO_FORTE = re.compile(r'^(?:[-*+]\s|#{1,6}\s|>|\||---|\*\*\*|___)')
# Lista numerada so vale quando NAO estamos no meio de um paragrafo: em lei, a
# continuacao de "Art." e "257. Ao Ministerio Publico cabe:", que e identica a um
# item de lista. O CommonMark concorda -- lista so interrompe paragrafo em "1.".
RE_LISTA_NUM = re.compile(r'^\d+[.)]\s')


def alnum(s):
    return sum(1 for c in s if c.isalnum())


def artigos(texto):
    """Conjunto de rotulos de artigo ('157', '3-A'), para comparar origem x saida."""
    return {n + ('-' + s if s else '') for n, s in RE_ARTIGO.findall(texto)}


def decodifica(caminho):
    """TRAVA 1 -- nos, nao o detector automatico."""
    bruto = open(caminho, 'rb').read()
    for enc in ('utf-8', 'cp1252', 'latin-1'):
        try:
            return bruto.decode(enc), enc, len(bruto)
        except UnicodeDecodeError:
            continue
    raise ValueError('nao decodificou em utf-8, cp1252 nem latin-1')


def desdobra(md):
    """TRAVA 3 -- junta as linhas de um mesmo bloco; preserva tabela/titulo/lista/citacao.

    Quebra simples dentro de paragrafo ja renderiza como espaco em Markdown, entao
    juntar nao muda o documento -- so devolve a frase inteira ao grep.
    """
    saida, buf, prefixo = [], [], ''

    def fecha():
        if buf:
            saida.append((prefixo + ' '.join(buf)).rstrip())
            buf.clear()

    for linha in md.split('\n'):
        s = linha.strip()
        if not s:                                   # separador de bloco
            fecha()
            prefixo = ''
            saida.append('')
            continue
        if s.startswith('|') or re.match(r'^(#{1,6}\s|---|\*\*\*|___)', s):
            fecha()
            prefixo = ''
            saida.append(s)                          # tabela, titulo, regra: intocados
            continue
        if s.startswith('>'):
            conteudo = s.lstrip('>').strip()
            continua = (prefixo == '> ' and conteudo and buf
                        and not RE_BLOCO_FORTE.match(conteudo))
            if continua:
                buf.append(conteudo)                 # continuacao da citacao
            else:
                fecha()
                prefixo = '> '
                if conteudo:
                    buf.append(conteudo)
                else:
                    saida.append('>')
                    prefixo = ''
            continue
        if RE_BLOCO_FORTE.match(s) or (RE_LISTA_NUM.match(s) and not buf):
            fecha()
            prefixo = ''
            buf.append(s)
            continue
        if prefixo == '> ':                          # saiu da citacao
            fecha()
            prefixo = ''
        buf.append(s)                                # continuacao de paragrafo
    fecha()

    texto = '\n'.join(saida)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # NBSP -> espaco, e runs de espaco colapsados (a indentacao inicial fica).
    # O Planalto escreve "Art. 397.\xa0 Apos...", e sem isso um grep normal nao
    # acha a frase. O conversor antigo fazia isso sem querer, porque str.split()
    # trata \xa0 como espaco -- as notas e helpers ja existentes contam com isso.
    limpas = []
    for linha in texto.split('\n'):
        recuo = linha[:len(linha) - len(linha.lstrip())]
        corpo = re.sub(r'[ \t\xa0]{2,}', ' ', linha.strip().replace('\xa0', ' '))
        limpas.append(recuo + corpo)
    return '\n'.join(limpas)


def converter(caminho, destino=None, escrever=True):
    """Devolve 0 (integro), 3 (suspeita de perda) ou 1 (erro)."""
    nome = os.path.basename(caminho)
    stem, ext = os.path.splitext(nome)
    if ext.lower() not in ACEITOS:
        print('%-40s nao e HTML (%s)' % (nome[:40], ext))
        return 1

    try:
        html, enc, tam = decodifica(caminho)          # TRAVA 1
        sopa = BeautifulSoup(html, 'html5lib')        # TRAVA 2
        for t in sopa(['script', 'style']):
            t.decompose()
        texto_origem = sopa.get_text(' ')
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        try:
            with open(tmp, 'w', encoding='utf-8') as fh:
                fh.write(str(sopa))
            md = MarkItDown(enable_plugins=False).convert(tmp).text_content
        finally:
            os.unlink(tmp)
    except Exception as e:
        print('%-40s ERRO: %s' % (nome[:40], type(e).__name__))
        print('   %s' % str(e).split('\n')[0][:200])
        return 1

    md = unicodedata.normalize('NFC', md.replace('\x00', ''))
    md = desdobra(md)                                 # TRAVA 3

    # TRAVA 4 -- regua
    src_a, md_a = alnum(texto_origem), alnum(md)
    art_src, art_md = artigos(texto_origem), artigos(md)
    perdidos = sorted(art_src - art_md, key=lambda x: (len(x), x))
    pct = (100.0 * md_a / src_a) if src_a else 0.0

    print('%-40s %8d chars md | origem %8d | %5.1f%% | Art. %4d->%-4d | %s %5.1f KB'
          % (nome[:40], len(md), src_a, pct, len(art_src), len(art_md), enc, tam / 1024))

    perda = False
    if src_a and pct < LIMIAR_PERDA * 100:
        perda = True
        print('   ATENCAO: a saida tem %.1f%% do texto do HTML (faltam ~%d caracteres).'
              % (pct, src_a - md_a))
        if len(md) < 2000 and src_a > 20000:
            print('   PISTA: saida minuscula para um HTML grande -- e o caso do <body> '
                  'fechado cedo. Confirme que a trava 2 (html5lib) rodou.')
    if perdidos:
        perda = True
        amostra = ', '.join(perdidos[:15]) + (' ...' if len(perdidos) > 15 else '')
        print('   ATENCAO: %d artigo(s) sumiram na conversao: %s'
              % (len(perdidos), amostra))
    if perda:
        print('   NAO destile antes de investigar.')

    if escrever:
        out_dir = destino or os.path.dirname(os.path.abspath(caminho))
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, stem + '.md')
        cab = ('# %s\n\n'
               '> Convertido de `%s` (%.1f KB, decodificado em %s) com markitdown %s\n'
               '> + html5lib, quebras moles desdobradas.\n'
               '> Regua: %d caracteres na origem, %d na saida (%.1f%%); '
               'artigos %d -> %d%s.\n'
               '> Formato sem paginacao: NAO ha ancora `## [p. N]` neste arquivo.\n'
               '> Original preservado.\n'
               % (stem, nome, tam / 1024, enc, _versao(),
                  src_a, md_a, pct, len(art_src), len(art_md),
                  '' if not perdidos else ' -- PERDIDOS: ' + ', '.join(perdidos[:15])))
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(cab + '\n' + md.strip() + '\n')
        print('   -> %s' % out)

    return 3 if perda else 0


def _versao():
    try:
        import importlib.metadata as m
        return m.version('markitdown')
    except Exception:
        return '?'


def main():
    ap = argparse.ArgumentParser(
        description='HTML -> Markdown com as quatro travas (regra canonica).')
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
