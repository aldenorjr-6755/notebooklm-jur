#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
consultar_rstj.py — busca full-text na Revista do STJ (RSTJ), 1989-2024.

Corpus dedicado: ~/.notebooklm/rstj/fontes  (303 volumes, v. 1-274,
182.325 paginas, ~389 milhoes de caracteres, ~19 mil acordaos).
Indice de volumes: ~/.notebooklm/rstj/rstj_volumes.tsv (gerar_indice_rstj.py).

PARA QUE SERVE
--------------
E' o acervo de INTEIRO TEOR do STJ desde a instalacao do Tribunal (1989) — a
unica fonte local que alcanca os anos 90. Os Informativos do STJ so comecam em
1998 e sao RESUMO; a RSTJ traz ementa, acordao, relatorio, votos e notas
taquigraficas. Serve a reconstrucao historica de entendimento, origem de sumula,
leading case antigo e demonstracao de virada jurisprudencial.

O QUE O HELPER RESOLVE, QUE O GREP CRU NAO RESOLVE
--------------------------------------------------
  * PAGINA do volume ("## [p. N]") — cada trecho fica conferivel contra a pagina
    do PDF oficial, que e' a fonte de verdade
  * ACORDAO a que o trecho pertence (classe + numero + UF + registro), ancorado
    no CABECALHO, nunca em numero de processo citado dentro da ementa
  * RELATOR e ORGAO JULGADOR (o STJ decide por orgao fracionario; tese de Turma
    nao vale o que vale tese de Secao)
  * busca insensivel a acento nos dois sentidos, e imune ao "**" que o conversor
    espalhou no meio das expressoes ("RECURSO ESPECIAL **N.** 656.990")

TRES DEFEITOS DO ACERVO, QUE O HELPER DECLARA EM VEZ DE ESCONDER
----------------------------------------------------------------
 1. ORDINAL CORROMPIDO (o mais grave). Em 204 dos 303 volumes — todos entre 1989
    e 2007 — a conversao destruiu o "º": gravou "art. 5º" como "art. 52",
    "art. 5<sup>2</sup>", "art. 5!!" ou "art. 5~". Onde o lixo tem forma
    ("<sup>2</sup>", "!!", "~") da' para reconhecer; onde virou digito puro
    ("art. 52") NAO HA COMO DISTINGUIR do artigo 52 de verdade. Por isso o
    helper marca o volume e proibe citacao literal de dispositivo sem conferir
    o PDF. Nao ha conserto possivel a partir do .md — so reconvertendo do PDF.
 2. PAGINAS NAO TRANSCRITAS. 202 volumes tem pelo menos uma pagina que chegou so
    como imagem (capa, folha de rosto, fac-simile). O cabecalho de cada .md lista
    quais. Ausencia de trecho nessas paginas nao prova ausencia de conteudo.
 3. PDF DE ORIGEM AUSENTE. Os PDFs nao estao nesta maquina — o aviso "consulte o
    PDF original" que o conversor deixou aponta para o portal do STJ
    (www.stj.jus.br), nao para disco local.

Uso:
    python consultar_rstj.py "denunciacao da lide"
    python consultar_rstj.py "boa-fe objetiva" --ano 1995
    python consultar_rstj.py "usucapiao" --volume 188 --contexto 500
    python consultar_rstj.py "dano moral" --de 1989 --ate 1995 --limite 30
    python consultar_rstj.py "prescricao" --classe "HABEAS CORPUS"
    python consultar_rstj.py --volumes                # so o mapa do acervo
Opcoes:
    --ano YYYY        so os volumes daquele ano (1989..2024)
    --volume N        so o volume N (1..274)
    --de A --ate B    faixa de ANOS
    --classe TEXTO    filtra pela classe do acordao do trecho
    --relator TEXTO   filtra pelo relator do acordao do trecho
    --limite N        max. de trechos (padrao 12)
    --contexto N      caracteres em torno do match (padrao 300)
    --por-volume N    max. de trechos por volume (padrao 2)
    --so-integros     ignora os volumes com ordinal corrompido (1989-2007)
    --corpus DIR      aponta para outro espelho do corpus
    --volumes         imprime o mapa do acervo e sai
"""
import argparse
import csv
import os
import re
import sys
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _resolver_corpus():
    r"""Descobre o corpus sem depender de caminho absoluto externo.

    Mesma ordem dos demais helpers do acervo: o exemplar copiado para dentro de
    um vault acha primeiro o espelho do PROPRIO vault — a norma de
    autossuficiencia proibe caminho externo executavel.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.normpath(os.path.join(aqui, "..", "corpora", "rstj", "fontes")),
        os.path.join(os.path.expanduser("~"), ".notebooklm", "rstj", "fontes"),
    ]


CANDIDATOS = _resolver_corpus()
DIR_PADRAO = next((d for d in CANDIDATOS if os.path.isdir(d)), CANDIDATOS[-1])

RE_ARQ = re.compile(r"^stj-revista-eletronica-(\d{4})_(\d+)(?:_(\d+))?$", re.I)
RE_PAGINA = re.compile(r"^##\s*\[p\.\s*(\d+)\]", re.M)

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
RE_ACORDAO = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*"
    r"((?:" + CLASSES + r")(?:[ \t]+(?:N[OA]S?|EM|DE)[ \t]+(?:" + CLASSES + r"))*)"
    r"[ \t]*(?:\*\*)?[ \t]*N[^\n\d]{0,12}?([\d][^\n]{0,60})", re.M | re.I)
RE_NUM_PROC = re.compile(r"\d{1,3}(?:\.\d{3})+(?:-\d)?|\d{2,}(?:-\d)?|\d")
RE_UF = re.compile(r"-\s*([A-Z]{2})\b")
RE_REGISTRO = re.compile(r"\((?:Registro\s*n?[^\d]{0,6})?(\d{2,4}[/.]\d{4,}-?\d?)\)", re.I)

# "Relator: Ministro Luiz Fux" / "Relator: Min. X" / "Relatora: Ministra Y"
RE_RELATOR = re.compile(
    r"Relator[a]?(?:\s*p/\s*(?:o\s*)?ac[oó]rd[aã]o)?\s*:?\s*"
    r"Min(?:\.|istr[oa])\s*([^\n,;(]{3,48})", re.I)
# Titulo corrente das paginas de jurisprudencia: "JURISPRUDENCIA DA PRIMEIRA TURMA"
RE_ORGAO = re.compile(
    r"(CORTE ESPECIAL|PRIMEIRA SE[CÇ][AÃ]O|SEGUNDA SE[CÇ][AÃ]O|TERCEIRA SE[CÇ][AÃ]O|"
    r"PRIMEIRA TURMA|SEGUNDA TURMA|TERCEIRA TURMA|QUARTA TURMA|QUINTA TURMA|"
    r"SEXTA TURMA|PLEN[AÁ]RIO)", re.I)

RE_ESPACO = re.compile(r"\s+")
# Lixo do ordinal: so as formas RECONHECIVEIS. "art. 52" (digito puro) e'
# irrecuperavel e por isso nao entra aqui — fingir que entra seria pior.
RE_ORD_LIXO = re.compile(r"(?<=\d)(?:<sup>[^<]{0,4}</sup>|!!|~|e:!|'[º°])")
RE_BOLD = re.compile(r"\*\*")

# Tradutor de acento 1 para 1. NFKD + encode('ascii','ignore') seria mais curto,
# mas MUDA O COMPRIMENTO da string — e todo este helper depende de o texto
# normalizado ter os MESMOS offsets do texto original, senao a pagina, o acordao
# e o relator informados passam a ser os do trecho vizinho. Citacao com a pagina
# errada e' pior que citacao nenhuma.
_DE = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑº°"
_PARA = "aaaaaeeeeiiiiooooouuuucnAAAAAEEEEIIIIOOOOOUUUUCNoo"
TAB_ACENTO = str.maketrans(_DE, _PARA)


def desacentuar(s):
    """Versao livre para comparar rotulos curtos (classe, relator) — pode encolher."""
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def normalizar_busca(s):
    """Indice de busca SEM alterar offsets: cada substituicao repoe o comprimento.

      * acento -> letra base, caractere a caractere (1:1)
      * "**" (ruido do conversor) -> dois espacos
      * ordinal corrompido reconhecivel -> "o" + espacos ate completar o tamanho

    Assim quem digita "art. 5º" tambem acha "art. 5<sup>2</sup>", e a posicao do
    match continua valendo no texto original.
    """
    s = (s or "").translate(TAB_ACENTO).lower()
    s = RE_BOLD.sub("  ", s)
    s = RE_ORD_LIXO.sub(lambda m: "o" + " " * (len(m.group(0)) - 1), s)
    return s


def compilar_consulta(termo):
    """Consulta tolerante a espaco, quebra de linha e ao '**' virado espaco.

    Busca por substring cru falharia em "RECURSO ESPECIAL **N.** 656.990" e em
    toda expressao partida por quebra de linha — que na RSTJ e' a regra, porque o
    texto vem de PDF diagramado em duas colunas.
    """
    partes = [re.escape(p) for p in normalizar_busca(termo).split()]
    if not partes:
        return None
    return re.compile(r"\s*".join(partes) if len(partes) > 1 else partes[0])


def limpar(s):
    return RE_ESPACO.sub(" ", (s or "").replace("**", "")).strip()


def carregar_indice(raiz):
    """Metadados por volume, do TSV. Sem ele o helper roda, mas cego a qualidade."""
    tsv = os.path.join(raiz, "rstj_volumes.tsv")
    if not os.path.isfile(tsv):
        return {}
    idx = {}
    with open(tsv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            idx[r["arquivo"]] = r
    return idx


def numero_do_processo(resto):
    """Token com FORMA de numero de processo (ver gerar_indice_rstj.py).

    Nos volumes antigos "Nº 56.666-3" foi gravado "N2 56.666-3": ler o primeiro
    digito depois do "N" devolveria o processo "2".
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


def marcadores(txt, rx, func=None):
    """[(posicao, valor)] de um marcador, em ordem — para resolver 'o ultimo antes'."""
    saida = []
    for m in rx.finditer(txt):
        val = func(m) if func else m.group(1)
        if val:
            saida.append((m.start(), val))
    return saida


def anterior(lista, pos, janela=None):
    """Ultimo marcador ANTES da posicao. E' assim que se evita erro de CAMADA:
    atribuir o trecho ao acordao vizinho porque a varredura foi longe demais."""
    achado = None
    for off, val in lista:
        if off > pos:
            break
        achado = (off, val)
    if not achado:
        return None
    if janela is not None and pos - achado[0] > janela:
        return None
    return achado[1]


def descrever_acordao(m):
    classe = limpar(m.group(1)).upper()
    resto = m.group(2)
    num = numero_do_processo(resto)
    if not num:
        return None
    uf = RE_UF.search(resto.split("(")[0])
    reg = RE_REGISTRO.search(resto)
    saida = "{} n. {}".format(classe, num)
    if uf:
        saida += " - {}".format(uf.group(1).upper())
    if reg:
        saida += " (Registro {})".format(reg.group(1))
    return saida


def varrer(path, meta, q, a):
    """Le UM volume, devolve os trechos e descarta o texto.

    De proposito nao ha cache do corpus inteiro em memoria: sao ~389 MB de texto,
    e a busca tipica toca poucos volumes.
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            txt = fh.read().replace("\x00", "")
    except OSError:
        return []
    norm = normalizar_busca(txt)
    if not q.search(norm):
        return []

    pags = marcadores(txt, RE_PAGINA)
    acs = marcadores(txt, RE_ACORDAO, descrever_acordao)
    rels = marcadores(txt, RE_RELATOR, lambda m: limpar(m.group(1)))
    orgs = marcadores(txt, RE_ORGAO, lambda m: limpar(m.group(1)).title())

    q_classe = desacentuar(a.classe) if a.classe else None
    q_rel = desacentuar(a.relator) if a.relator else None

    hits = []
    for m in q.finditer(norm):
        if len(hits) >= a.por_volume:
            break
        i = m.start()
        ac = anterior(acs, i)
        rel = anterior(rels, i, janela=20000)
        org = anterior(orgs, i, janela=40000)
        if q_classe and (not ac or q_classe not in desacentuar(ac)):
            continue
        if q_rel and (not rel or q_rel not in desacentuar(rel)):
            continue
        # norm preserva offsets de txt (ver normalizar_busca), logo a pagina, o
        # acordao e o relator resolvidos aqui sao os do PROPRIO trecho — e o
        # recorte pode sair do texto ORIGINAL, com acento e grafia de verdade.
        ini = max(0, i - a.contexto // 2)
        fim = min(len(txt), m.end() + a.contexto // 2)
        hits.append({
            "meta": meta, "pagina": anterior(pags, i),
            "acordao": ac, "relator": rel, "orgao": org,
            "snip": limpar(txt[ini:fim]),
        })
    return hits


def mapa(idx):
    print("RSTJ — Revista do Superior Tribunal de Justica · mapa do acervo\n")
    por_ano = {}
    for r in idx.values():
        por_ano.setdefault(r["ano"], []).append(r)
    print("{:>6}  {:>4}  {:>9}  {:>8}  {:>9}  {}".format(
        "ano", "vols", "paginas", "acordaos", "ordinal", "volumes"))
    for ano in sorted(por_ano):
        rs = por_ano[ano]
        ruins = sum(1 for r in rs if r["ordinal_ok"] == "NAO")
        vols = sorted(set(int(r["volume"]) for r in rs if r["volume"]))
        faixa = "{}-{}".format(vols[0], vols[-1]) if len(vols) > 1 else str(vols[0]) if vols else "?"
        print("{:>6}  {:>4}  {:>9,}  {:>8,}  {:>9}  {}".format(
            ano, len(rs), sum(int(r["paginas"]) for r in rs),
            sum(int(r["acordaos"]) for r in rs),
            "{}/{} sujo".format(ruins, len(rs)) if ruins else "ok", faixa))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("termo", nargs="?")
    ap.add_argument("--ano", type=int)
    ap.add_argument("--volume", type=int)
    ap.add_argument("--de", type=int)
    ap.add_argument("--ate", type=int)
    ap.add_argument("--classe")
    ap.add_argument("--relator")
    ap.add_argument("--limite", type=int, default=12)
    ap.add_argument("--contexto", type=int, default=300)
    ap.add_argument("--por-volume", type=int, default=2, dest="por_volume")
    ap.add_argument("--so-integros", action="store_true", dest="so_integros")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--volumes", action="store_true")
    a = ap.parse_args()

    diretorio = os.path.expanduser(a.corpus or os.environ.get("RSTJ_DIR") or DIR_PADRAO)
    if not os.path.isdir(diretorio):
        print("Corpus da RSTJ nao localizado em {}".format(diretorio))
        print("Aponte outro espelho com --corpus DIR ou RSTJ_DIR.")
        return 1
    idx = carregar_indice(os.path.dirname(diretorio.rstrip("\\/")))

    if a.volumes:
        if not idx:
            print("Indice ausente. Rode: python gerar_indice_rstj.py")
            return 1
        mapa(idx)
        return 0
    if not a.termo:
        ap.error("informe o termo de busca (ou --volumes para o mapa do acervo)")

    arquivos = []
    for nome in sorted(os.listdir(diretorio)):
        if not nome.lower().endswith(".md"):
            continue
        m = RE_ARQ.match(nome[:-3])
        ano = int(m.group(1)) if m else None
        vol = int(m.group(2)) if m else None
        meta = idx.get(nome, {"ano": ano, "volume": vol, "ordinal_ok": "?",
                              "paginas_nao_lidas": "?", "arquivo": nome})
        if a.ano and ano != a.ano:
            continue
        if a.volume and vol != a.volume:
            continue
        if a.de and ano and ano < a.de:
            continue
        if a.ate and ano and ano > a.ate:
            continue
        if a.so_integros and meta.get("ordinal_ok") == "NAO":
            continue
        arquivos.append((nome, meta))

    if not arquivos:
        print("Nenhum volume atende ao filtro. Cobertura: 1989-2024, v. 1-274 "
              "(303 arquivos).")
        return 0

    q = compilar_consulta(a.termo)
    if q is None:
        ap.error("termo de busca vazio")
    hits = []
    for nome, meta in arquivos:
        hits.extend(varrer(os.path.join(diretorio, nome), meta, q, a))
        if len(hits) >= a.limite:
            hits = hits[:a.limite]
            break

    if not hits:
        print('Nada encontrado para "{}" na RSTJ.'.format(a.termo))
        print("ATENCAO: 204 volumes (1989-2007) tem o ordinal corrompido — busca "
              "por 'art. 5º' pode falhar se o original virou 'art. 52'. Tente sem "
              "o ordinal. E ausencia aqui NAO prova que o STJ nao decidiu.")
        return 0

    nvol = len(set(h["meta"]["arquivo"] for h in hits))
    print('RSTJ · "{}" · {} trecho(s) em {} volume(s)\n'.format(a.termo, len(hits), nvol))

    sujos = set()
    for h in hits:
        m = h["meta"]
        print("RSTJ v. {} ({}){}".format(
            m.get("volume"), m.get("ano"),
            ", p. {}".format(h["pagina"]) if h["pagina"] else ""))
        if h["acordao"]:
            print("  Acordao: {}".format(h["acordao"]))
        if h["relator"]:
            print("  Relator: Min. {}".format(h["relator"]))
        if h["orgao"]:
            print("  Orgao: {}".format(h["orgao"]))
        print("  …{}…".format(h["snip"]))
        if m.get("ordinal_ok") == "NAO":
            sujos.add("{} ({})".format(m.get("volume"), m.get("ano")))
            print("  [!] ORDINAL CORROMPIDO neste volume — 'art. 5º' pode aparecer "
                  "como 'art. 52'. NAO cite dispositivo sem conferir o PDF.")
        print("  (fonte: {})\n".format(m.get("arquivo")))

    print("Acervo: {} · 303 volumes, v. 1-274 (1989-2024), ~19 mil acordaos."
          .format(diretorio))
    if sujos:
        print("VOLUMES COM ORDINAL CORROMPIDO neste resultado: {}".format(
            ", ".join(sorted(sujos))))
    print("ANTI-INVENCAO: 'Acordao', 'Relator' e 'Orgao' vem do marcador mais "
          "proximo ANTES do trecho — confira se correspondem. A RSTJ e' registro "
          "HISTORICO: o julgado pode estar superado por lei, emenda, sumula ou "
          "virada da Corte. Confirme inteiro teor, pagina e vigencia no PDF "
          "oficial em www.stj.jus.br antes de citar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
