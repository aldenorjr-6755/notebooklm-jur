#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
rtf_stj_para_md.py — reconverte os Informativos do STJ de RTF para Markdown.

POR QUE ESTE SCRIPT EXISTE
--------------------------
A conversao anterior do acervo (2026-06-27, arquivos Inf*.md) perdeu TODOS os
acentos: 795 dos 835 arquivos tem "compet?ncia", "obten??o", "?rg?o". Nao foi
perda de informacao — foi bug de conversao.

Nos RTF de origem o STJ grava caractere acentuado como escape Unicode do RTF:

    \u231?\u227?o      ->  c + a + o  = "cao"  (ç ã)
    \u237?             ->  i                    (í)

O "?" ali NAO e o caractere: e o *fallback ASCII* que o proprio RTF carrega para
leitores antigos (RTF spec, controle \ucN). O conversor anterior descartou o
escape "\uNNNN" e preservou o fallback "?". Dai o estrago sistematico.

Neste acervo ha 0 escapes "\'hh" e ~2.100 escapes "\uNNNN" por arquivo — logo o
acento e 100% recuperavel a partir do RTF original.

O striprtf (instalado) devolve 1 caractere nestes arquivos: engasga com os grupos
de imagem embutida ({\pict ...}), que aqui sao enormes (PNG + perfil ICC). Dai o
parser proprio abaixo, que descarta grupo de destino antes de qualquer coisa.

O QUE ESTE SCRIPT FAZ
---------------------
  * decodifica \uNNNN (honrando \ucN) e \'hh (cp1252)
  * descarta grupos de destino: \pict, \fonttbl, \colortbl, \stylesheet, \info,
    \*\qualquercoisa, \bin — que e de onde vinha o lixo binario ("iText",
    "PNG", "IHDR", perfil ICC) no acervo antigo
  * traduz \par \line \tab e mantem o frontmatter YAML do acervo antigo
  * grava UTF-8 sem BOM, sem byte NUL

MEDICAO OBRIGATORIA: ao fim, compara com o .md antigo e reporta acentos
recuperados e lixo removido. Conversao que nao mede engana em silencio.

Uso:
    python rtf_stj_para_md.py --check                # so mede, nao grava
    python rtf_stj_para_md.py                        # converte tudo
    python rtf_stj_para_md.py --zip InformativosSTJ_2020.zip
    python rtf_stj_para_md.py -o <dir>               # destino alternativo
"""
import argparse
import glob
import os
import re
import sys
import unicodedata
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = r"C:\Users\alden\.notebooklm\informativo_stj"
DIR_ZIPS = os.path.join(BASE, "zips")
DIR_FONTES = os.path.join(BASE, "fontes")

# grupos cujo CONTEUDO INTEIRO se descarta (nao e texto do informativo)
DESTINOS = {
    "pict", "fonttbl", "colortbl", "stylesheet", "info", "shppict",
    "nonshppict", "header", "footer", "headerl", "headerr", "footerl",
    "footerr", "footnote", "generator", "themedata", "colorschememapping",
    "latentstyles", "datastore", "xmlnstbl", "listtable", "listoverridetable",
    "rsidtbl", "mmathPr", "objdata", "bkmkstart", "bkmkend",
}

# controles que viram espaco em branco tipografico
QUEBRA = {"par", "line", "sect", "page", "row", "cell", "nestcell", "nestrow"}

RE_CTRL = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?")

# O RTF e lido em latin-1, e nao em cp1252, porque latin-1 e BIJETIVO: 1 byte = 1
# caractere. cp1252 deixa 5 bytes indefinidos (0x81 0x8D 0x8F 0x90 0x9D) que o
# decodificador descarta, e ai o indice da string deixa de casar com o indice do
# byte — o que estraga o pulo de "\binN", medido em BYTES. O preco e que byte
# literal na faixa 0x80-0x9F sai como caractere de controle: e o que a tabela
# abaixo devolve a cp1252, que e a pagina declarada no \ansicpg1252 destes RTF.
CP1252_ALTO = {i: bytes([i]).decode("cp1252", errors="ignore") for i in range(0x80, 0xA0)}
RE_LIXO_RTF = re.compile(r"\b(pard|plain|par|tab|cell|row|trowd|intbl|ql|qj|qc|qr)\b")
RE_MULTI_NL = re.compile(r"\n{3,}")
RE_ESPACO = re.compile(r"[ \t]{2,}")
RE_FRONT = re.compile(r"\A---\n.*?\n---\n", re.S)


def rtf_para_texto(rtf):
    r"""Converte a string RTF em texto puro, recuperando \uNNNN e \'hh."""
    out = []
    i = 0
    n = len(rtf)
    depth = 0
    # pilha: profundidade em que cada destino ignorado comecou
    ignorar_ate = None
    uc = 1  # quantos caracteres de fallback pular apos \uNNNN

    while i < n:
        c = rtf[i]

        if c == "{":
            depth += 1
            i += 1
            continue

        if c == "}":
            if ignorar_ate is not None and depth <= ignorar_ate:
                ignorar_ate = None
            depth -= 1
            i += 1
            continue

        if c == "\\":
            # escape hexadecimal \'hh (cp1252)
            if i + 3 < n and rtf[i + 1] == "'":
                hx = rtf[i + 2:i + 4]
                i += 4
                if ignorar_ate is None:
                    try:
                        out.append(bytes([int(hx, 16)]).decode("cp1252", errors="ignore"))
                    except ValueError:
                        pass
                continue

            # caractere escapado literal: \{ \} \\
            if i + 1 < n and rtf[i + 1] in "{}\\":
                if ignorar_ate is None:
                    out.append(rtf[i + 1])
                i += 2
                continue

            m = RE_CTRL.match(rtf, i)
            if not m:
                i += 1
                continue

            palavra, arg = m.group(1), m.group(2)
            i = m.end()

            # \*\destino  -> grupo inteiro descartado
            if palavra == "*":
                if ignorar_ate is None:
                    ignorar_ate = depth
                continue

            if palavra in DESTINOS:
                if ignorar_ate is None:
                    ignorar_ate = depth
                continue

            # \binN vem ANTES do descarte de destino: os bytes crus da imagem
            # contem { e } nao escapados, e deixar de pular esses N bytes
            # destroi a contagem de grupos — foi assim que o lixo binario
            # (JPEG/PNG/ICC) vazou para o acervo antigo.
            if palavra == "bin" and arg:
                i += max(0, int(arg))
                continue

            if ignorar_ate is not None:
                continue

            if palavra == "uc":
                uc = int(arg) if arg else 1
                continue

            if palavra == "u" and arg is not None:
                cp = int(arg)
                if cp < 0:              # RTF grava >32767 como negativo
                    cp += 65536
                if 0 < cp < 0x110000:
                    out.append(chr(cp))
                # pular os caracteres de fallback ASCII (normalmente "?")
                pulados = 0
                while pulados < uc and i < n:
                    if rtf[i] == "\\":  # fallback pode ser ele proprio um escape
                        m2 = RE_CTRL.match(rtf, i)
                        i = m2.end() if m2 else i + 2
                    elif rtf[i] in "{}":
                        break
                    else:
                        i += 1
                    pulados += 1
                continue

            if palavra in QUEBRA:
                out.append("\n")
                continue

            if palavra == "tab":
                out.append("\t")
                continue

            continue

        # caractere comum
        if ignorar_ate is None and c not in "\r\n":
            out.append(CP1252_ALTO.get(ord(c), c) if 0x80 <= ord(c) < 0xA0 else c)
        i += 1

    return "".join(out)


def limpar(txt):
    """Higiene final: sem NUL, sem residuo de controle, sem espaco duplo."""
    txt = txt.replace("\x00", "")
    txt = "".join(ch for ch in txt if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")
    txt = RE_ESPACO.sub(" ", txt)
    txt = "\n".join(l.rstrip() for l in txt.split("\n"))
    txt = RE_MULTI_NL.sub("\n\n", txt)
    return txt.strip() + "\n"


def frontmatter_antigo(md_path):
    """Reaproveita o frontmatter YAML do acervo antigo (ele esta intacto)."""
    if not os.path.exists(md_path):
        return None
    try:
        cab = open(md_path, encoding="utf-8", errors="ignore").read(2000).replace("\x00", "")
    except Exception:
        return None
    m = RE_FRONT.match(cab)
    return m.group(0) if m else None


def frontmatter_novo(nome, ano):
    num = re.sub(r"\D", "", nome) or "0"
    extra = "Extraordinaria" if nome.upper().endswith("E") else "Regular"
    return (
        "---\n"
        "titulo: Informativo STJ n. {}\n"
        "ano: {}\n"
        "numero: {}\n"
        "tipo: {}\n"
        "tribunal: STJ\n"
        "fonte: Informativo de Jurisprudencia do STJ\n"
        "arquivo_origem: {}.rtf\n"
        "---\n".format(int(num), ano, int(num), extra, nome)
    )


def conta_acentos(s):
    return len(re.findall(r"[áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ]", s))


def conta_degradado(s):
    return len(re.findall(r"\?[a-zç]|[a-z]\?[a-z]", s, re.I))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="so mede, nao grava")
    ap.add_argument("--zip", help="processar apenas um zip")
    ap.add_argument("-o", "--out", default=DIR_FONTES)
    ap.add_argument("--limite", type=int, help="processar so os N primeiros (teste)")
    a = ap.parse_args()

    zips = sorted(glob.glob(os.path.join(DIR_ZIPS, "*.zip")))
    if a.zip:
        zips = [z for z in zips if os.path.basename(z) == a.zip or z == a.zip]
    if not zips:
        print("Nenhum zip encontrado em {}".format(DIR_ZIPS))
        return 1

    if not a.check:
        os.makedirs(a.out, exist_ok=True)

    tot = ok = vazio = 0
    ac_novo = ac_velho = deg_novo = deg_velho = 0
    ch_novo = ch_velho = 0
    problemas = []

    for zp in zips:
        ano = re.findall(r"(\d{4})", os.path.basename(zp))
        ano = ano[0] if ano else "?"
        try:
            zf = zipfile.ZipFile(zp)
        except Exception as e:
            problemas.append((os.path.basename(zp), "zip ilegivel: {}".format(e)))
            continue
        with zf as z:
            for nome in sorted(z.namelist()):
                if not nome.lower().endswith(".rtf"):
                    continue
                if a.limite and tot >= a.limite:
                    break
                tot += 1
                base = os.path.splitext(os.path.basename(nome))[0]
                try:
                    rtf = z.read(nome).decode("latin-1")
                except Exception as e:
                    problemas.append((base, "leitura: {}".format(e)))
                    continue

                corpo = limpar(rtf_para_texto(rtf))
                if len(corpo) < 400:
                    vazio += 1
                    problemas.append((base, "corpo com {} caracteres".format(len(corpo))))

                md_antigo = os.path.join(DIR_FONTES, base + ".md")
                velho = ""
                if os.path.exists(md_antigo):
                    velho = open(md_antigo, encoding="utf-8", errors="ignore").read().replace("\x00", "")

                ac_novo += conta_acentos(corpo)
                ac_velho += conta_acentos(velho)
                deg_novo += conta_degradado(corpo)
                deg_velho += conta_degradado(velho)
                ch_novo += len(corpo)
                ch_velho += len(velho)

                if not a.check:
                    front = frontmatter_antigo(md_antigo) or frontmatter_novo(base, ano)
                    dest = os.path.join(a.out, base + ".md")
                    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(front)
                        fh.write("\n# Informativo STJ n. {}\n\n".format(re.sub(r"\D", "", base) or base))
                        fh.write(corpo)
                ok += 1

    print("Informativos STJ — RTF -> Markdown")
    print("  arquivos ................ {}".format(tot))
    print("  convertidos ............. {}".format(ok))
    print("  corpo suspeito (<400 ch)  {}".format(vazio))
    print()
    print("  {:<26} {:>14} {:>14}".format("", "ACERVO ANTIGO", "RECONVERTIDO"))
    print("  {:<26} {:>14,} {:>14,}".format("caracteres", ch_velho, ch_novo))
    print("  {:<26} {:>14,} {:>14,}".format("acentos", ac_velho, ac_novo))
    print("  {:<26} {:>14,} {:>14,}".format("marcas '?' de degradacao", deg_velho, deg_novo))
    if problemas:
        print("\n  ATENCAO — {} arquivo(s) com ressalva:".format(len(problemas)))
        for b, m in problemas[:15]:
            print("    {} — {}".format(b, m))
        if len(problemas) > 15:
            print("    ... e mais {}".format(len(problemas) - 15))
    if a.check:
        print("\n  (--check: nada foi gravado)")
    else:
        print("\n  gravado em: {}".format(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
