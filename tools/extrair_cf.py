"""Extrai os artigos da CF a partir do PDF do Planalto para cf_artigos.json.

DEFEITO CORRIGIDO EM 2026-07-26 — cabecalho de pagina lido como inicio de artigo.

O PDF traz, no alto de cada pagina, um titulo corrente no formato `Art. 5o, VIII`
— o artigo mais o inciso em curso. O regex antigo (`\\nArt\\.?\\s*(\\d+)`) casava
esses titulos como se fossem aberturas de artigo. Duas consequencias, ambas
silenciosas:

  1. como a regra era "primeira ocorrencia vence", o artigo passava a ser o
     TITULO CORRENTE — o art. 5o virava a string "Art. 5o, VIII" (119 chars);
  2. o corpo verdadeiro era picado a cada quebra de pagina, porque o titulo
     seguinte encerrava o bloco.

Medido antes do conserto: 41 dos 276 artigos truncados, inclusive art. 5o, 12,
37 e 49 — e o `/cf` devolvia cabecalho no lugar da norma.

A correcao distingue os dois pelo que vem DEPOIS do numero: titulo corrente
sempre traz virgula (`Art. 5o, VIII`, `Art. 231, caput`); abertura de artigo
nunca traz (`Art. 5o Todos sao iguais...`). Os titulos correntes que sobram
dentro do corpo sao removidos como ruido de diagramacao.

Uso:  python extrair_cf.py <cf.pdf> <saida.json>
"""
import json
import re
import sys

import fitz

pdf, out = sys.argv[1], sys.argv[2]
doc = fitz.open(pdf)
text = "\n".join(doc[i].get_text() for i in range(doc.page_count))

# Separa corpo permanente do ADCT. A numeracao do ADCT reinicia em 1 e colidiria
# com a do corpo permanente num indice unico — por isso os dois blocos sao
# extraidos em separado e o ADCT vai para uma lista propria, com chave "ADCT-N".
# Ate 2026-07-26 o ADCT era simplesmente DESCARTADO aqui, e a nota de fonte
# canonica registrava a ausencia como se fosse limitacao inerente. Nao era:
# o PDF traz o ADCT inteiro (arts. 1o a 138), incluindo dispositivos muito
# citados — art. 68 (quilombolas), art. 95 (nacionalidade), art. 100 (idade da
# aposentadoria compulsoria no STF).
i = text.find("ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS")
main = text[:i] if i > 2000 else text
adct_raw = text[i:] if i > 2000 else ""

# Cada bloco termina na promulgacao; o que vem depois e a lista de constituintes
# (centenas de nomes). Sem este corte o ULTIMO artigo de cada bloco engole tudo:
# o art. 250 tinha 11.030 caracteres e o ADCT art. 138, 11.424 — quase todos de
# assinaturas. Defeito antigo, independente do ADCT, e silencioso: o artigo
# existia e respondia, so vinha com 11 KB de ruido colado.
PROMULGACAO = re.compile(r'\nBrasília,\s*5\s*de\s*outubro\s*de\s*1988')


def ate_promulgacao(bloco):
    m = PROMULGACAO.search(bloco)
    return bloco[:m.start()] if m else bloco


main = ate_promulgacao(main)
adct_raw = ate_promulgacao(adct_raw)

# Abertura de artigo: numero NAO seguido de virgula.
# O lookahead vem LOGO APOS o numero e absorve ele proprio o marcador ordinal.
# Se ficasse depois de `[ºo°]?`, o motor driblava por backtracking: casava
# "Art. 5" sem consumir o "º", via um "º" adiante em vez da virgula, e aprovava
# o titulo corrente "Art. 5º, VIII" assim mesmo.
# O `(?!\d)` trava o backtracking do `\d+`: sem ele, em "Art. 49, XVIII" o motor
# recuava para o "4", via um "9" no lugar da virgula, aprovava o lookahead e
# gravava o titulo corrente como se fosse abertura do art. 4. Era o que ainda
# decapitava os arts. 49 e 177, cujo caput termina em ":" e cujos incisos ficavam
# do outro lado da quebra de pagina.
ABERTURA = re.compile(r'\nArt\.?\s*(\d+(?:-[A-Z])?)(?!\d)(?!\s*[ºo°]?\s*,)\s*[ºo°]?')
# Titulo corrente de pagina, a remover de dentro do corpo.
TITULO_CORRENTE = re.compile(r'\n?Art\.?\s*\d+(?:-[A-Z])?\s*[ºo°]?\s*,[^\n]{0,40}\n')
# Rodape de pagina: a palavra "sumario" seguida do numero da pagina.
RODAPE = re.compile(r'\s*\bsum[áa]rio\s+\d+\s*', re.I)
# Rodape ORFAO: quando "sumario 244" e seguido do cabecalho corrente do ADCT, o
# TITULO_ADCT ja consumiu o numero e sobra um "sumario" sozinho — era o que
# restava no fim do art. 54-A do ADCT.
#
# ATENCAO: este padrao TEM de exigir linha propria (`^...$`). Tentar resolver
# tornando o digito opcional no RODAPE acima corrompeu texto normativo: o art.
# 184, § 3o, fala em "procedimento contraditorio especial, de rito sumario" —
# e a palavra foi apagada de dentro da norma, silenciosamente. O rodape esta
# sempre sozinho na linha; a palavra da lei, nunca.
RODAPE_ORFAO = re.compile(r'(?m)^[ \t]*sum[áa]rio[ \t]*$\n?', re.I)

# No ADCT o titulo corrente tem forma propria — `ADCT – Art. 55, caput` —, as
# vezes precedido do numero da pagina em linha isolada. Sem remove-lo, o
# cabecalho da pagina seguinte gruda no fim do artigo anterior (era o que
# acontecia com o art. 54-A, que terminava com "ADCT – Art. 55, caput").
# O `(?:\n|$)` no fim e essencial: quando o cabecalho e a ULTIMA linha do bloco
# — caso do art. 54-A, cujo texto terminava em "ADCT – Art. 55, caput" — nao ha
# quebra de linha apos ele, e uma regex que exigisse `\n` simplesmente nao casava.
TITULO_ADCT = re.compile(
    r'(?m)^[ \t]*\d{0,3}[ \t]*\n?[ \t]*ADCT\s*[–\-]\s*Art\.?[^\n]*(?:\n|$)')


def blocos(bruto):
    """Divide um bloco de texto em artigos. Devolve {numero: texto}."""
    heads = list(ABERTURA.finditer(bruto))
    M = {}
    for k, m in enumerate(heads):
        art = m.group(1)
        start = m.start() + 1
        end = heads[k + 1].start() if k + 1 < len(heads) else len(bruto)
        txt = bruto[start:end]
        txt = TITULO_ADCT.sub("\n", txt)                   # cabecalho corrente do ADCT
        txt = TITULO_CORRENTE.sub("\n", txt)               # tira cabecalho de pagina
        txt = RODAPE.sub("\n", txt)                        # tira rodape "sumario <pag>"
        txt = RODAPE_ORFAO.sub("", txt)                    # e o "sumario" sem numero
        txt = re.sub(r'(\w)­\s*\n\s*(\w)', r'\1\2', txt)  # junta hifenizacao de quebra
        txt = re.sub(r'[ \t]+', ' ', txt).strip()
        txt = re.sub(r'\n{2,}', '\n', txt)
        # PRIMEIRA ocorrencia vence — e correto agora que o titulo corrente nao entra
        # mais na lista. Tentar "a maior vence" foi pior: uma remissao dentro de bloco
        # longo sequestrava o artigo (o art. 1o passou a devolver o § 2o do art. 17).
        if art not in M:
            M[art] = txt
    return M


M = blocos(main)
A = blocos(adct_raw)


def kf(a):
    mm = re.match(r'(\d+)(?:-([A-Z]))?', a)
    return (int(mm.group(1)), mm.group(2) or "")


regs = [{"artigo": a, "texto": M[a]} for a in sorted(M, key=kf)]
adct = [{"artigo": a, "texto": A[a]} for a in sorted(A, key=kf)]

# `total` e `artigos` seguem significando o CORPO PERMANENTE, como antes — ha
# notas e indices que citam "276 artigos", e mudar o sentido da chave quebraria
# a conferencia deles. O ADCT entra em lista propria.
json.dump({"fonte": "Constituição Federal de 1988 (texto Planalto, atualizado até EC 139)",
           "total": len(regs), "artigos": regs,
           "total_adct": len(adct), "adct": adct},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def relatorio(nome, rs):
    if not rs:
        print(nome, ": vazio")
        return
    nums = [kf(r["artigo"])[0] for r in rs]
    curtos = [r["artigo"] for r in rs if len(r["texto"]) < 160]
    faltam = [n for n in range(1, max(nums) + 1) if n not in nums]
    print(f"{nome}: {len(rs)} | maior: {max(nums)} | faltam 1..max: {faltam[:20]}")
    print(f"  < 160 chars: {len(curtos)} {curtos[:20]}")
    # Guarda contra a regressao do cabecalho de pagina: se um artigo virou titulo
    # corrente, o texto casa com o proprio padrao de cabecalho.
    sujos = [r["artigo"] for r in rs
             if re.match(r'Art\.?\s*\d+(?:-[A-Z])?\s*[ºo°]?\s*,', r["texto"])
             or re.search(r'ADCT\s*[–\-]\s*Art', r["texto"])
             or re.search(r'sum[áa]rio\s*\n?\s*\d+\s*$', r["texto"].strip())]
    print(f"  com residuo de cabecalho/rodape: {len(sujos)} {sujos[:20]}")


relatorio("Corpo permanente", regs)
relatorio("ADCT           ", adct)
print("ex art 1:", regs[0]["texto"][:90])
