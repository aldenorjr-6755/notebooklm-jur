#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
consultar_informativo_stj.py — busca full-text nos Informativos do STJ.

Corpus dedicado: ~/.notebooklm/informativo_stj/fontes  (835 arquivos, n. 1-853).

O QUE O HELPER RESOLVE, QUE O GREP CRU NAO RESOLVE
--------------------------------------------------
  * numero do informativo, ano e tipo (Regular / Extraordinaria)
  * ORGAO JULGADOR (Corte Especial, 1a-3a Secao, 1a-6a Turma) — o STJ decide por
    orgao fracionario, e tese de Turma nao vale o mesmo que tese de Secao
  * PROCESSO (REsp, EREsp, AgInt, AgRg, HC, RHC, CC, MS, RMS, Rcl, IAC...) e RELATOR
  * RAMO DO DIREITO e TEMA de repetitivo, quando o informativo os traz
  * busca INSENSIVEL A ACENTO nos dois sentidos: quem digita "competencia" acha
    "competência", e vice-versa

DUAS ERAS DE DIAGRAMACAO, no mesmo acervo:
  * ate ~2016 — corrido: "Primeira Secao" / TITULO EM CAIXA / texto / citacao final
  * de ~2017 — em campos: PROCESSO / RAMO DO DIREITO / TEMA / DESTAQUE /
    INFORMACOES DO INTEIRO TEOR
O helper le as duas.

LACUNA DECLARADA: o ano de 2019 INTEIRO esta fora do acervo (o zip de origem
InformativosSTJ_2019.zip tem 0 byte). O corpus salta de Inf0638 (2018) para
Inf0662 (2020) — faltam ~23 edicoes. Nao ha informativo de 2019 aqui, e
"nada encontrado" NUNCA prova que o STJ nao decidiu. O rodape avisa sempre.

PROVENIENCIA DO TEXTO: reconvertido dos RTF oficiais em 2026-08-05 por
rtf_stj_para_md.py. A conversao anterior perdia todo acento (gravava "compet?ncia")
porque descartava o escape \uNNNN do RTF e ficava com o fallback ASCII "?".

Uso:
    python consultar_informativo_stj.py "prescricao intercorrente"
    python consultar_informativo_stj.py "guarda compartilhada" --ano 2023
    python consultar_informativo_stj.py "dano moral" --orgao "Terceira Turma"
    python consultar_informativo_stj.py "usucapiao" --numero 700 --contexto 400
Opcoes:
    --ano YYYY        so os informativos daquele ano (1998..2025, sem 2019)
    --numero N        so o informativo n. N
    --de N --ate N    faixa de numeros
    --orgao TEXTO     filtra pelo orgao julgador do trecho
    --ramo TEXTO      filtra pelo RAMO DO DIREITO (formato novo)
    --limite N        max. de trechos (padrao 12)
    --contexto N      caracteres em torno do match (padrao 300)
    --por-fonte N     max. de trechos por informativo (padrao 2)
    --corpus DIR      aponta para outro espelho do corpus (ex.: dentro de um vault)
    --listar          so lista os informativos que casam, sem os trechos
"""
import argparse
import glob
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

    O MESMO arquivo serve ao escopo global (~/.notebooklm/tools) e a copia dentro
    de cada vault (<vault>/.claude/tools). A ordem abaixo faz o exemplar do vault
    achar o espelho do PROPRIO vault primeiro — que e o que a norma de
    autossuficiencia exige: nada de caminho externo executavel.

      1. --corpus DIR
      2. variavel de ambiente INFORMATIVO_STJ_DIR
      3. espelho irmao do script: <script>/../corpora/informativo_stj/fontes
      4. acervo global ~/.notebooklm/informativo_stj/fontes
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.normpath(os.path.join(aqui, "..", "corpora", "informativo_stj", "fontes")),
        os.path.join(os.path.expanduser("~"), ".notebooklm", "informativo_stj", "fontes"),
    ]


CANDIDATOS = _resolver_corpus()
DIR_PADRAO = next((d for d in CANDIDATOS if os.path.isdir(d)), CANDIDATOS[-1])

ANO_AUSENTE = 2019

RE_NUM_ARQ = re.compile(r"^Inf(\d{4})(E?)$", re.I)
RE_FRONT_ANO = re.compile(r"^ano:\s*(\d{4})", re.M)
RE_FRONT_NUM = re.compile(r"^numero:\s*(\d+)", re.M)

ORGAOS = [
    "Corte Especial", "Primeira Seção", "Segunda Seção", "Terceira Seção",
    "Primeira Turma", "Segunda Turma", "Terceira Turma", "Quarta Turma",
    "Quinta Turma", "Sexta Turma", "Plenário",
]
RE_ORGAO = re.compile("|".join(ORGAOS), re.I)

# re.I e obrigatorio: o acervo grava "EREsp" e tambem "ERESP", "Resp", "REsp".
# O numero exige 2+ caracteres para nao casar com "art. 5" e afins.
RE_PROC = re.compile(
    r"\b(EREsp|AgInt no REsp|AgInt|AgRg|REsp|RHC|RMS|HC|MS|CC|Rcl|IAC|ProAfR|"
    r"Pet|SEC|HDE|APn|AR|MC|SLS|SS|QO|EDcl|ExeAP|RvCr)"
    r"\s*n?\.?\s*(\d[\d.]+(?:-[A-Za-z]{2})?)", re.I
)
# "Precedente(s) citado(s):" abre uma lista de julgados de OUTROS processos. Quem
# le a linha de tras para frente e pega o primeiro numero cai justamente ai —
# atribuindo a tese ao processo CITADO em vez do processo JULGADO.
RE_PRECEDENTE = re.compile(r"Precedentes?\s+citados?\s*:", re.I)
RE_RELATOR = re.compile(
    r"(?:Rel(?:\.|ator[a]?)|Rel\. p/ ac[oó]rd[aã]o|Red\.)[^,;\n]{0,40}?"
    r"Min(?:\.|istr[oa])\s*([^,;\n()]{3,48})", re.I)
RE_TEMA = re.compile(r"\(?\s*Tema\s*(\d{1,4})\s*\)?", re.I)
RE_DATA_JULG = re.compile(r"julgad[oa] em\s*(\d{1,2}/\d{1,2}/\d{2,4})", re.I)

# Era nova (~2017 em diante): a entrada e um bloco de campos, cada rotulo sozinho
# na sua linha e o valor na linha seguinte. O rotulo "Processo" ABRE a entrada —
# e por isso a citacao correta e a do ULTIMO "Processo" ANTES do trecho.
RE_CAMPO_PROC = re.compile(r"^[ \t]*PROCESSO[ \t]*$", re.M | re.I)
RE_CAMPO_RAMO = re.compile(r"^[ \t]*RAMO DO DIREITO[ \t]*$", re.M | re.I)
# Era antiga (ate ~2016): a citacao FECHA a entrada, no fim do paragrafo.
RE_MARCA_ERA_NOVA = re.compile(r"^[ \t]*DESTAQUE[ \t]*$", re.M | re.I)
RE_SEGREDO = re.compile(r"[Pp]rocesso\s+em\s+segredo\s+de\s+justi[çc]a", re.I)

RE_ESPACO = re.compile(r"\s+")


def desacentuar(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def limpar(s):
    return RE_ESPACO.sub(" ", s or "").strip()


def valor_do_campo(txt, pos, maxlin=6):
    """Primeira linha nao vazia depois do rotulo do campo."""
    for linha in txt[pos:pos + 1200].split("\n")[:maxlin]:
        s = limpar(linha)
        if s and s != "*":
            return s
    return ""


def carregar(diretorio):
    fontes = []
    for path in sorted(glob.glob(os.path.join(diretorio, "*.md"))):
        base = os.path.basename(path)[:-3]
        m = RE_NUM_ARQ.match(base)
        try:
            txt = open(path, encoding="utf-8", errors="ignore").read().replace("\x00", "")
        except Exception:
            continue
        cab = txt[:800]
        m_ano = RE_FRONT_ANO.search(cab)
        m_num = RE_FRONT_NUM.search(cab)
        numero = int(m_num.group(1)) if m_num else (int(m.group(1)) if m else 0)
        fontes.append({
            "arquivo": base,
            "texto": txt,
            "norm": desacentuar(txt),
            "numero": numero,
            "ano": int(m_ano.group(1)) if m_ano else None,
            "extraordinaria": bool(m and m.group(2)),
            "orgaos": [(mo.start(), mo.group(0)) for mo in RE_ORGAO.finditer(txt)],
            "ramos": [(m2.start(), valor_do_campo(txt, m2.end()))
                      for m2 in RE_CAMPO_RAMO.finditer(txt)],
            "procs": [(m2.start(), valor_do_campo(txt, m2.end()))
                      for m2 in RE_CAMPO_PROC.finditer(txt)],
            "era_nova": bool(RE_MARCA_ERA_NOVA.search(txt)),
        })
    return fontes


def anterior(lista, pos, janela=4000):
    """Ultimo marcador que aparece ANTES da posicao (dentro de uma janela)."""
    achado = None
    for off, val in lista:
        if off > pos:
            break
        if pos - off <= janela:
            achado = val
        else:
            achado = val if achado is None else achado
    if achado is None:
        return None
    # so aceita se estiver razoavelmente perto
    for off, val in reversed(lista):
        if off <= pos:
            return val if pos - off <= janela else None
    return None


def decompor(linha):
    """Extrai processo, relator e tema de UMA linha de citacao ja delimitada.

    O processo do JULGADO e o que vem imediatamente ANTES do "Rel." — tudo que
    aparece depois de "Precedentes citados:" e processo de OUTRO julgado e nao
    pode ser atribuido a esta tese.
    """
    if not linha:
        return None, None, None
    mr = RE_RELATOR.search(linha)
    rel = limpar(mr.group(1)) if mr else None

    if RE_SEGREDO.search(linha):
        proc = "em segredo de justiça (sem numero divulgado)"
    else:
        mprec = RE_PRECEDENTE.search(linha)
        candidatos = [
            m for m in RE_PROC.finditer(linha)
            if (not mr or m.start() < mr.start())
            and not (mprec and mprec.start() < m.start() < (mr.start() if mr else len(linha)))
        ]
        if not candidatos:
            candidatos = [m for m in RE_PROC.finditer(linha)
                          if not (mprec and m.start() > mprec.start())]
        mp = candidatos[-1] if candidatos else None
        proc = "{} {}".format(mp.group(1), mp.group(2).rstrip(".")) if mp else None

    mt = RE_TEMA.search(linha)
    return proc, rel, (mt.group(1) if mt else None)


def citacao(fonte, pos, janela=6000):
    r"""Linha de citacao do julgado A QUE O TRECHO PERTENCE.

    O erro que esta funcao existe para evitar e o de CAMADA: pescar numero de
    processo de uma entrada VIZINHA e atribui-lo a tese do trecho. Isso acontece
    sobretudo quando a propria entrada corre EM SEGREDO DE JUSTICA e portanto nao
    tem numero — a varredura ingenua para tras acha o REsp da entrada anterior e
    troca um julgado por outro.

    Por isso a busca e ancorada na FRONTEIRA DA ENTRADA, e nao numa janela:

      * era nova (~2017+): o rotulo "PROCESSO" sozinho na linha ABRE a entrada,
        logo vale o ULTIMO rotulo antes do trecho, e a citacao e a linha seguinte;
      * era antiga (ate ~2016): a citacao FECHA a entrada, logo vale a PRIMEIRA
        linha depois do trecho que traga processo + relator.
    """
    txt = fonte["texto"]

    if fonte["era_nova"]:
        linha = None
        for off, val in fonte["procs"]:
            if off > pos:
                break
            linha = val
        if linha is None:
            return None, None, None, None
        proc, rel, tema = decompor(linha)
        return linha, proc, rel, tema

    fim = min(len(txt), pos + janela)
    ini_linha = txt.rfind("\n", 0, pos) + 1
    for bruta in txt[ini_linha:fim].split("\n"):
        mr = RE_RELATOR.search(bruta)
        if not mr:
            continue
        if not (RE_PROC.search(bruta) or RE_SEGREDO.search(bruta)):
            continue
        # a entrada pode ocupar um paragrafo longo com a citacao colada no fim:
        # corta no ultimo processo ANTES do "Rel.", que e o do julgado
        antes = [m for m in RE_PROC.finditer(bruta) if m.start() < mr.start()]
        corte = bruta[antes[-1].start():] if antes else bruta
        linha = limpar(corte)[:400]
        proc, rel, tema = decompor(linha)
        return linha, proc, rel, tema
    return None, None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("termo")
    ap.add_argument("--ano", type=int)
    ap.add_argument("--numero", type=int)
    ap.add_argument("--de", type=int)
    ap.add_argument("--ate", type=int)
    ap.add_argument("--orgao")
    ap.add_argument("--ramo")
    ap.add_argument("--limite", type=int, default=12)
    ap.add_argument("--contexto", type=int, default=300)
    ap.add_argument("--por-fonte", type=int, default=2, dest="por_fonte")
    ap.add_argument("--corpus", default=None)
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()

    diretorio = a.corpus or os.environ.get("INFORMATIVO_STJ_DIR") or DIR_PADRAO
    diretorio = os.path.expanduser(diretorio)
    fontes = carregar(diretorio)
    if not fontes:
        print("Corpus de Informativos do STJ nao localizado em {}".format(diretorio))
        print("Aponte outro espelho com --corpus DIR ou INFORMATIVO_STJ_DIR.")
        return 1

    if a.ano:
        fontes = [f for f in fontes if f["ano"] == a.ano]
    if a.numero:
        fontes = [f for f in fontes if f["numero"] == a.numero]
    if a.de:
        fontes = [f for f in fontes if f["numero"] >= a.de]
    if a.ate:
        fontes = [f for f in fontes if f["numero"] <= a.ate]
    if not fontes:
        print("Nenhum informativo atende ao filtro. Cobertura: 1998-2025 "
              "(n. 1-853), SEM o ano de {}.".format(ANO_AUSENTE))
        return 0

    q = desacentuar(a.termo)
    q_orgao = desacentuar(a.orgao) if a.orgao else None
    q_ramo = desacentuar(a.ramo) if a.ramo else None
    hits = []

    for f in sorted(fontes, key=lambda x: -(x["numero"] or 0)):
        start, got = 0, 0
        while len(hits) < a.limite and got < a.por_fonte:
            i = f["norm"].find(q, start)
            if i < 0:
                break
            start = i + len(q)
            orgao = anterior(f["orgaos"], i)
            ramo = anterior(f["ramos"], i)
            if q_orgao and (not orgao or q_orgao not in desacentuar(orgao)):
                continue
            if q_ramo and (not ramo or q_ramo not in desacentuar(ramo)):
                continue
            ini = max(0, i - a.contexto // 2)
            fim = min(len(f["texto"]), i + len(a.termo) + a.contexto // 2)
            cit, proc, rel, tema = citacao(f, i)
            hits.append({
                "f": f, "orgao": orgao, "ramo": ramo, "cit": cit,
                "proc": proc, "rel": rel, "tema": tema,
                "snip": limpar(f["texto"][ini:fim]),
            })
            got += 1
        if len(hits) >= a.limite:
            break

    if not hits:
        print('Nada encontrado para "{}" nos Informativos do STJ.'.format(a.termo))
        print("LACUNA: o ano de {} INTEIRO esta fora do acervo (~23 edicoes, "
              "n. 639-661). Ausencia aqui NAO prova que o STJ nao decidiu — "
              "confirme em scon.stj.jus.br.".format(ANO_AUSENTE))
        return 0

    nf = len(set(h["f"]["arquivo"] for h in hits))
    print('Informativos do STJ · "{}" · {} trecho(s) em {} informativo(s)\n'
          .format(a.termo, len(hits), nf))

    if a.listar:
        vistos = []
        for h in hits:
            f = h["f"]
            chave = f["arquivo"]
            if chave in vistos:
                continue
            vistos.append(chave)
            print("  Informativo {} ({}){}  — {}".format(
                f["numero"], f["ano"],
                " [extraordinaria]" if f["extraordinaria"] else "",
                h["orgao"] or "orgao nao identificado"))
    else:
        for h in hits:
            f = h["f"]
            cab = "Informativo STJ n. {} ({})".format(f["numero"], f["ano"])
            if f["extraordinaria"]:
                cab += " [edicao extraordinaria]"
            print(cab)
            print("  Orgao: {}".format(h["orgao"] or "NAO identificado no trecho"))
            if h["ramo"]:
                print("  Ramo: {}".format(h["ramo"]))
            if h["proc"]:
                print("  Processo: {}{}".format(
                    h["proc"], "  (Tema {})".format(h["tema"]) if h["tema"] else ""))
            if h["rel"]:
                print("  Relator: Min. {}".format(h["rel"]))
            print("  …{}…".format(h["snip"]))
            print("  (fonte: {}.md)\n".format(f["arquivo"]))

    print("Acervo: {} · 835 informativos, n. 1-853 (1998-2025).".format(diretorio))
    print("LACUNA DECLARADA: o ano de {} INTEIRO esta fora do acervo "
          "(~23 edicoes, n. 639-661) — o zip de origem veio vazio.".format(ANO_AUSENTE))
    print("ANTI-INVENCAO: o informativo NAO e repositorio oficial e nao esgota o "
          "acordao. 'Processo', 'Relator' e 'Orgao' vem da entrada mais proxima do "
          "trecho — confira se correspondem. Confirme inteiro teor e atualidade em "
          "scon.stj.jus.br antes de citar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
