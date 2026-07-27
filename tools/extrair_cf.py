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

# corta no ADCT p/ evitar colisao de numeracao
i = text.find("ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS")
main = text[:i] if i > 2000 else text

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

heads = list(ABERTURA.finditer(main))
M = {}
for k, m in enumerate(heads):
    art = m.group(1)
    start = m.start() + 1
    end = heads[k + 1].start() if k + 1 < len(heads) else len(main)
    txt = main[start:end]
    txt = TITULO_CORRENTE.sub("\n", txt)               # tira cabecalho de pagina
    txt = RODAPE.sub("\n", txt)                        # tira rodape "sumario <pag>"
    txt = re.sub(r'(\w)­\s*\n\s*(\w)', r'\1\2', txt)  # junta hifenizacao de quebra
    txt = re.sub(r'[ \t]+', ' ', txt).strip()
    txt = re.sub(r'\n{2,}', '\n', txt)
    # PRIMEIRA ocorrencia vence — e correto agora que o titulo corrente nao entra
    # mais na lista. Tentar "a maior vence" foi pior: uma remissao dentro de bloco
    # longo sequestrava o artigo (o art. 1o passou a devolver o § 2o do art. 17).
    if art not in M:
        M[art] = txt


def kf(a):
    mm = re.match(r'(\d+)(?:-([A-Z]))?', a)
    return (int(mm.group(1)), mm.group(2) or "")


regs = [{"artigo": a, "texto": M[a]} for a in sorted(M, key=kf)]
json.dump({"fonte": "Constituição Federal de 1988 (texto Planalto, atualizado até EC 139)",
           "total": len(regs), "artigos": regs},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

nums = [kf(r["artigo"])[0] for r in regs]
curtos = [r["artigo"] for r in regs if len(r["texto"]) < 160]
print("Artigos CF:", len(regs), "| maior:", max(nums),
      "| faltam 1..max:", [n for n in range(1, max(nums) + 1) if n not in nums][:20])
print("com texto < 160 chars:", len(curtos), curtos[:20])
print("ex art 1:", regs[0]["texto"][:90])
