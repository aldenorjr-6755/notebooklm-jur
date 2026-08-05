#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
gerar_indice_rstj.py — monta o indice de volumes da Revista do STJ (RSTJ).

Le ~/.notebooklm/rstj/fontes/*.md e grava ~/.notebooklm/rstj/rstj_volumes.tsv,
uma linha por volume, com a medicao de conversao que o proprio cabecalho do .md
carrega — mais a contagem de acordaos localizados no corpo.

POR QUE O INDICE EXISTE
-----------------------
A RSTJ e' acervo HISTORICO e volumoso (303 arquivos, ~389 milhoes de caracteres,
1989-2024). Sem indice, tres perguntas ficam sem resposta barata:

  * o volume N existe no acervo, ou a busca voltou vazia por lacuna?
  * este volume esta integro, ou tem pagina que nenhuma passagem transcreveu?
  * quantos acordaos ha aqui — isto e' volume de jurisprudencia ou de indice?

A terceira importa porque o acervo NAO e' homogeneo: ha volumes que sao quase so
ementario/indice remissivo, e volume assim nao sustenta citacao de inteiro teor.

O QUE ESTE SCRIPT NAO FAZ
-------------------------
Nao corrige nada e nao converte nada. So le o que ja esta gravado no cabecalho
gerado pelo pdf2md e conta ocorrencia no corpo. Se a medicao do cabecalho estiver
errada, o indice repete o erro — a fonte de verdade e' o PDF do STJ.

Uso:
    python gerar_indice_rstj.py
    python gerar_indice_rstj.py --corpus DIR --saida ARQUIVO.tsv
"""
import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.join(os.path.expanduser("~"), ".notebooklm", "rstj")
CORPUS_PADRAO = os.path.join(RAIZ, "fontes")
SAIDA_PADRAO = os.path.join(RAIZ, "rstj_volumes.tsv")

# stj-revista-eletronica-2024_274_2.md -> ano 2024, volume 274, tomo 2
RE_ARQ = re.compile(r"^stj-revista-eletronica-(\d{4})_(\d+)(?:_(\d+))?$", re.I)

RE_PAGS = re.compile(r"Convertido de\*\*.*?—\s*(\d+)\s*pagina\(s\),\s*([\d.]+)\s*KB")
RE_CHARS = re.compile(r"Caracteres extraidos:\s*\*\*(\d+)\*\*")
RE_OCR = re.compile(r"Texto nativo:\s*(\d+)\s*car\.\s*\|\s*via OCR:\s*(\d+)\s*car\.\s*em\s*(\d+)\s*pagina")
RE_NAOLIDA = re.compile(r"ATENCAO:\s*(\d+)\s*pagina\(s\)\s*tem IMAGEM QUE NAO FOI LIDA")

# "R. Sup. Trib. Just., Brasília, v. 1, n. 1, p. 1-229, set. 1989."
# E' a referencia oficial do proprio periodico — a unica forma de citacao que o
# STJ reconhece. Vale mais que o nome do arquivo, que e' convencao nossa.
RE_REF = re.compile(
    r"R\.\s*Sup\.\s*Trib\.\s*Just\.,\s*Bras[ií]lia,\s*v\.\s*(\d+)"
    r"(?:,\s*n\.\s*(\d+))?(?:,\s*p\.\s*([\d\-]+))?(?:,\s*([^\.\n]{3,30}\.?\s*\d{4}))?", re.I)

# Classes processuais que abrem um acordao na RSTJ.
CLASSES = (
    r"RECURSO ESPECIAL|RECURSO EM MANDADO DE SEGURAN[CÇ]A|RECURSO ORDIN[AÁ]RIO"
    r"(?: EM (?:MANDADO DE SEGURAN[CÇ]A|HABEAS CORPUS))?|"
    r"EMBARGOS DE DIVERG[EÊ]NCIA|EMBARGOS DE DECLARA[CÇ][AÃ]O|EMBARGOS INFRINGENTES|"
    r"AGRAVO REGIMENTAL|AGRAVO DE INSTRUMENTO|AGRAVO INTERNO|"
    r"HABEAS CORPUS|HABEAS DATA|MANDADO DE SEGURAN[CÇ]A|MANDADO DE INJUN[CÇ][AÃ]O|"
    r"CONFLITO DE COMPET[EÊ]NCIA|CONFLITO DE ATRIBUI[CÇ][OÕ]ES|"
    r"A[CÇ][AÃ]O RESCIS[OÓ]RIA|A[CÇ][AÃ]O PENAL|INQU[EÉ]RITO|"
    r"MEDIDA CAUTELAR|RECLAMA[CÇ][AÃ]O|REVIS[AÃ]O CRIMINAL|"
    r"SENTEN[CÇ]A ESTRANGEIRA(?: CONTESTADA)?|CARTA ROGAT[OÓ]RIA|"
    r"EXCE[CÇ][AÃ]O DE (?:SUSPEI[CÇ][AÃ]O|IMPEDIMENTO)|PETI[CÇ][AÃ]O"
)

# Cabecalho de acordao. Tres armadilhas ja custaram contagem errada aqui:
#
#   1. o cabecalho vem MUITAS vezes como titulo markdown ("###### RECURSO
#      ESPECIAL N. ..."), nao como linha nua — ignorar "#" perdia ~2/3 deles;
#   2. a classe e' COMPOSTA ("EMBARGOS DE DECLARACAO NO RECURSO ESPECIAL",
#      "AGRAVO REGIMENTAL NO AGRAVO DE INSTRUMENTO");
#   3. nos volumes antigos o ordinal "º" virou lixo na conversao ("Nº 56.666"
#      gravado como "N2 56.666", "N!!", "N~", "N<sup>2</sup>"). Quem le o
#      primeiro digito depois do "N" extrai o numero de processo "2".
#
# Por isso a linha inteira e' capturada aqui e o numero e' escolhido depois, por
# FORMA (ver numero_do_processo). Ancorado em inicio de linha de proposito:
# processo CITADO dentro da ementa nao pode virar cabecalho de acordao.
RE_ACORDAO = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*"
    r"((?:" + CLASSES + r")(?:[ \t]+(?:N[OA]S?|EM|DE)[ \t]+(?:" + CLASSES + r"))*)"
    r"[ \t]*(?:\*\*)?[ \t]*N[^\n\d]{0,12}?([\d][^\n]{0,60})", re.M | re.I)

# Numero de processo da RSTJ: "56.666-3", "1.828.993", "185". O "-3" e' digito
# verificador; a UF vem depois, apos travessao.
RE_NUM_PROC = re.compile(r"\d{1,3}(?:\.\d{3})+(?:-\d)?|\d{2,}(?:-\d)?|\d")
RE_UF = re.compile(r"-\s*([A-Z]{2})\b")
RE_REGISTRO = re.compile(r"\((?:Registro\s*n?[^\d]{0,6})?(\d{2,4}[/.]\d{4,}-?\d?)\)", re.I)

# Ordinal corrompido pela conversao dos volumes antigos. NAO ha como distinguir
# com seguranca "art. 52" (ordinal sujo) de "art. 52" (artigo 52 mesmo) depois do
# estrago — por isso o indice CONTA a sujeira em vez de tentar consertar.
RE_ORDINAL_SUJO = re.compile(
    r"(?:art(?:igo)?s?\.?|§{1,2}|n)\s*\d+\s*(?:<sup>[^<]{0,4}</sup>|!!|~|e:!|'[º°])", re.I)
RE_ORDINAL_LIMPO = re.compile(r"(?:art(?:igo)?s?\.?|§{1,2}|n)\s*\d+\s*[º°]", re.I)


def numero_do_processo(resto):
    """Escolhe, na cauda do cabecalho, o token que TEM FORMA de numero de processo.

    Existe por causa do ordinal corrompido: em "N2 56.666-3 - SP" o primeiro
    digito e' o lixo do "º", nao o processo. Prefere o token pontuado ou longo;
    so aceita numero de 1-2 digitos quando nao ha outro candidato (os processos
    de 1989-1990 sao mesmo curtos — "REsp n. 2" existe).
    """
    cauda = resto.split("(")[0]
    cands = RE_NUM_PROC.findall(cauda)
    if not cands:
        return None
    pontuados = [c for c in cands if "." in c]
    if pontuados:
        return pontuados[0]
    longos = [c for c in cands if len(c.replace("-", "")) >= 3]
    if longos:
        return longos[0]
    return cands[-1] if len(cands) > 1 else cands[0]


def medir(path):
    base = os.path.basename(path)[:-3]
    m = RE_ARQ.match(base)
    ano = int(m.group(1)) if m else None
    volume = int(m.group(2)) if m else None
    tomo = int(m.group(3)) if (m and m.group(3)) else 1

    with open(path, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    cab = txt[:4000]

    pags = kb = chars = ocr_car = ocr_pags = naolida = 0
    mp = RE_PAGS.search(cab)
    if mp:
        pags = int(mp.group(1))
        kb = float(mp.group(2).replace(".", "") or 0) if mp.group(2).count(".") > 1 else float(mp.group(2))
    mc = RE_CHARS.search(cab)
    if mc:
        chars = int(mc.group(1))
    mo = RE_OCR.search(cab)
    if mo:
        ocr_car, ocr_pags = int(mo.group(2)), int(mo.group(3))
    mn = RE_NAOLIDA.search(cab)
    if mn:
        naolida = int(mn.group(1))

    ref_v = ref_n = ref_p = ref_per = ""
    mr = RE_REF.search(txt[:120000])
    if mr:
        ref_v = mr.group(1) or ""
        ref_n = mr.group(2) or ""
        ref_p = mr.group(3) or ""
        ref_per = (mr.group(4) or "").strip().rstrip(".")

    vistos = set()
    for m2 in RE_ACORDAO.finditer(txt):
        num = numero_do_processo(m2.group(2))
        if num:
            vistos.add((re.sub(r"\s+", " ", m2.group(1).upper()), num))
    acordaos = len(vistos)

    ord_sujo = len(RE_ORDINAL_SUJO.findall(txt))
    ord_limpo = len(RE_ORDINAL_LIMPO.findall(txt))
    total_ord = ord_sujo + ord_limpo
    # >20% de ordinal corrompido = o volume nao sustenta citacao literal de
    # dispositivo ("art. 5º" lido como "art. 52"). O limiar e' arbitrario e
    # deliberadamente baixo: aqui o falso negativo custa mais que o falso positivo.
    ordinal_ok = "sim" if total_ord and ord_sujo / total_ord <= 0.20 else (
        "NAO" if total_ord else "sem_ordinal")

    return {
        "arquivo": base + ".md",
        "ano": ano or "",
        "volume": volume or "",
        "tomo": tomo,
        "ref_volume": ref_v,
        "ref_numero": ref_n,
        "ref_paginas": ref_p,
        "ref_periodo": ref_per,
        "paginas": pags,
        "caracteres": chars,
        "car_por_pagina": round(chars / pags) if pags else 0,
        "ocr_caracteres": ocr_car,
        "ocr_paginas": ocr_pags,
        "paginas_nao_lidas": naolida,
        "acordaos": acordaos,
        "ordinal_sujo": ord_sujo,
        "ordinal_limpo": ord_limpo,
        "ordinal_ok": ordinal_ok,
        "kb_pdf": kb,
    }


COLUNAS = ["arquivo", "ano", "volume", "tomo", "ref_volume", "ref_numero",
           "ref_paginas", "ref_periodo", "paginas", "caracteres", "car_por_pagina",
           "ocr_caracteres", "ocr_paginas", "paginas_nao_lidas", "acordaos",
           "ordinal_sujo", "ordinal_limpo", "ordinal_ok", "kb_pdf"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS_PADRAO)
    ap.add_argument("--saida", default=SAIDA_PADRAO)
    a = ap.parse_args()

    corpus = os.path.expanduser(a.corpus)
    if not os.path.isdir(corpus):
        print("Corpus nao localizado em {}".format(corpus))
        return 1

    arquivos = sorted(f for f in os.listdir(corpus) if f.lower().endswith(".md"))
    if not arquivos:
        print("Nenhum .md em {}".format(corpus))
        return 1

    linhas = []
    for i, nome in enumerate(arquivos, 1):
        linhas.append(medir(os.path.join(corpus, nome)))
        if i % 25 == 0:
            print("  ... {}/{}".format(i, len(arquivos)), file=sys.stderr)

    linhas.sort(key=lambda r: (r["ano"] or 0, r["volume"] or 0, r["tomo"]))

    with open(a.saida, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(COLUNAS) + "\n")
        for r in linhas:
            fh.write("\t".join(str(r[c]) for c in COLUNAS) + "\n")

    anos = [r["ano"] for r in linhas if r["ano"]]
    vols = [r["volume"] for r in linhas if r["volume"]]
    tot_c = sum(r["caracteres"] for r in linhas)
    tot_p = sum(r["paginas"] for r in linhas)
    tot_a = sum(r["acordaos"] for r in linhas)
    com_falha = [r for r in linhas if r["paginas_nao_lidas"]]
    com_ocr = [r for r in linhas if r["ocr_paginas"]]
    magros = [r for r in linhas if r["car_por_pagina"] and r["car_por_pagina"] < 800]

    print("indice gravado: {}".format(a.saida))
    print("  volumes ..........: {} (v. {}-{}, {}-{})".format(
        len(linhas), min(vols), max(vols), min(anos), max(anos)))
    print("  paginas ..........: {:,}".format(tot_p))
    print("  caracteres .......: {:,}".format(tot_c))
    print("  acordaos .........: {:,} (cabecalho unico por volume)".format(tot_a))
    print("  com pagina nao lida: {} volume(s)".format(len(com_falha)))
    print("  com OCR aplicado ..: {} volume(s)".format(len(com_ocr)))

    ruins = [r for r in linhas if r["ordinal_ok"] == "NAO"]
    if ruins:
        anos_ruins = sorted(set(r["ano"] for r in ruins if r["ano"]))
        print("  ORDINAL CORROMPIDO : {} volume(s) — o 'º' virou 2/!!/~/<sup>2</sup>, "
              "logo 'art. 5º' le-se 'art. 52'.".format(len(ruins)))
        print("                       anos afetados: {}-{} ({} anos)".format(
            min(anos_ruins), max(anos_ruins), len(anos_ruins)))
        print("                       NAO cite dispositivo literal desses volumes "
              "sem conferir no PDF do STJ.")
    print("  suspeitos (<800 car/pagina): {}".format(
        ", ".join(r["arquivo"] for r in magros) if magros else "nenhum"))

    faltando = sorted(set(range(min(vols), max(vols) + 1)) - set(vols))
    if faltando:
        print("  LACUNA — volumes ausentes ({}): {}".format(
            len(faltando),
            ", ".join(str(v) for v in faltando[:40]) + (" ..." if len(faltando) > 40 else "")))
    else:
        print("  sem lacuna de volume na faixa {}-{}".format(min(vols), max(vols)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
