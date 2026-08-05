#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""extrair_regimento.py <pdf> <json> <rotulo> — texto por artigo de Regimento Interno.

Gera o dataset consumido por consultar_regimento.py (--fonte stf|stj|tjma|tse).

Como funciona, e por que assim (o modo de falha aqui e' PERDA SILENCIOSA):

  1. UMA VARREDURA, DUAS PRIORIDADES. As fronteiras dos blocos saem de TODOS os
     cabecalhos (aceitando indentacao) — se saissem so' dos nao indentados, o bloco
     do art. 29 engoliria o art. 30 indentado. Ja' a DONO da chave e' o cabecalho
     NAO indentado, quando existe; o indentado so' entra se nenhum outro achou aquele
     artigo. E' isso que impede a leitura frouxa de degradar dataset bom.
     Motivo: no RISTJ, os arts. 30, 320 e 323 vinham indentados por um espaco e
     sumiam sem erro (2026-08-05).

  2. SUFIXO DE LETRA EM QUALQUER CAIXA. O RISTF escreve `Art. 354-a` em MINUSCULA no
     corpo; com `[A-Z]` no regex, 29 artigos do RISTF ficavam de fora — entre eles
     TODO o procedimento de sumula vinculante (354-A a 354-G) e a opiniao consultiva
     ao Tribunal Permanente de Revisao do Mercosul (354-H a 354-M). A chave e'
     normalizada para MAIUSCULA.

  3. FILTRO ANTI-FALSO-POSITIVO. Sumario e cabecalho de pagina tambem comecam por
     "Art. N" e, como vale a 1a ocorrencia, roubariam o lugar do texto real:
       - "Art. 2o a art. 4o ..... 21"  -> entrada de SUMARIO (intervalo)
       - "Art. 354-a, caput"           -> CABECALHO de pagina (virgula depois do numero)
       - "Art. 1o \x08\n 17"      -> linha de sumario com leader/pagina
     Sem esse filtro, a passada frouxa corrompeu 70 artigos do RISTF num teste.

  4. PRIMEIRA OCORRENCIA VENCE. Preserva o corpo vigente contra o anexo historico de
     emendas, que reproduz redacoes REVOGADAS dos mesmos artigos (RISTJ: corpo em
     [p. 21-172], anexo em [p. 173-390]).

Confira SEMPRE a linha `faltam 1..max:` impressa ao final — ela e' o detector de perda.
"""
import sys, re, json, fitz

# sem isto o print final estoura com UnicodeEncodeError no console cp1252 do Windows
# (o JSON ja' foi gravado, mas o exit code 1 engana quem le' so' o codigo de saida).
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

CABECALHO = r'\n([ \t]*)Art\.?\s*(\d+(?:-[A-Za-z])?)\s*[ºo°]?'
# mobilia de pagina que sobra DENTRO do bloco (cabecalho corrido, "Sumario", "— 23 —")
RUIDO = re.compile(r'^(Sum[áa]rio|[—–-]\s*\d+\s*[—–-]|Art\.?\s*\d+(?:-[A-Za-z])?\s*[ºo°]?\s*,.*)$')
# o que vem logo depois do numero e denuncia sumario/cabecalho em vez de artigo
LIXO = re.compile(r'^\s*(,|[ \x08\x07]|\.{3,}|_{3,}|(a|e|at[eé])\s+art\.)', re.I)


def limpa(txt):
    """Tira a mobilia de pagina que fica DENTRO do bloco (cabecalho corrido do RISTF:
    `Art. 4o, § 3o` / `Sumario` / `— 23 —`). Nao mexe em linha com frase."""
    return "\n".join(l for l in txt.split("\n") if not RUIDO.match(l.strip()))


def blocos(text):
    """Devolve (artigo, texto, indentado) na ordem do documento, ja' sem sumario."""
    heads = [m for m in re.finditer(CABECALHO, text)
             if not LIXO.match(text[m.end():m.end() + 40])]
    for k, m in enumerate(heads):
        fim = heads[k + 1].start() if k + 1 < len(heads) else len(text)
        txt = re.sub(r'[ \t]+', ' ', text[m.start() + 1:fim]).strip()
        txt = re.sub(r'\n{2,}', '\n', limpa(txt))
        if len(txt) > 5:
            # chave normalizada: 354-a -> 354-A
            yield m.group(2).upper(), txt, bool(m.group(1))


ANTERIOR = "[REDACAO ANTERIOR {i}/{n} — SUBSTITUIDA; NAO CITAR. A vigente vem abaixo.]"
VIGENTE = ("[REDACAO {n}/{n} — ULTIMA IMPRESSA NO PDF OFICIAL, e' a que se cita. "
           "Confira a nota '(Redacao dada por...)' e emenda posterior.]")


def juntar(textos):
    """Cola redacoes sucessivas do mesmo artigo com a placa que diz qual e' qual.

    Sem a placa, quem le' rapido cita a PRIMEIRA — que e' a revogada. Ja' aconteceu:
    em 05/08/2026 o art. 390 do RITJMA foi levado a peca com a redacao substituida
    pela Resolucao-GP 6/2023, poucos minutos depois de o dataset passar a trazer as
    duas. A ordem e' a do PDF oficial, que imprime da mais antiga para a vigente.
    """
    if len(textos) == 1:
        return textos[0]
    n = len(textos)
    partes = [ANTERIOR.format(i=i + 1, n=n) + "\n" + t for i, t in enumerate(textos[:-1])]
    partes.append(VIGENTE.format(n=n) + "\n" + textos[-1])
    return "\n".join(partes)


def kf(a):
    mm = re.match(r'(\d+)(?:-([A-Z]))?', a)
    return (int(mm.group(1)), mm.group(2) or "")


def main():
    pdf, out, fonte = sys.argv[1], sys.argv[2], sys.argv[3]
    doc = fitz.open(pdf)
    text = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    # Redacoes sucessivas do MESMO artigo aparecem como cabecalhos adjacentes iguais
    # (RITJMA art. 15: a redacao revogada vem primeiro e a vigente logo abaixo, com a
    # nota "(redacao dada pela Resolucao-GP 8/2023)"). Ficar so' com a 1a devolvia a
    # ementa revogada SEM os incisos. Junta-se a corrida inteira: nada se perde e as
    # notas de redacao ficam a' vista de quem cita. Nao alcanca o anexo historico de
    # emendas, que fica a centenas de artigos de distancia — la' a 1a ocorrencia vence.
    corridas = []
    for art, txt, ind in blocos(text):
        if corridas and corridas[-1][0] == art:
            corridas[-1][1].append(txt)
            corridas[-1][2] = corridas[-1][2] and ind
        else:
            corridas.append([art, [txt], ind])

    M, indentado, quantas = {}, {}, {}
    for art, textos, ind in corridas:
        # dono da chave: 1o cabecalho NAO indentado; indentado so' se nao houver outro
        if art in M and not (indentado.get(art) and not ind):
            continue
        M[art], indentado[art], quantas[art] = juntar(textos), ind, len(textos)

    regs = []
    for a in sorted(M, key=kf):
        r = {"artigo": a, "texto": M[a]}
        if quantas[a] > 1:
            r["redacoes"] = quantas[a]   # campo lido pelo consultar_regimento.py
        regs.append(r)
    json.dump({"fonte": fonte, "total": len(regs), "artigos": regs},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    nums = [kf(r["artigo"])[0] for r in regs]
    falta = [n for n in range(1, max(nums) + 1) if n not in nums]
    resgatados = sorted((a for a, ind in indentado.items() if ind), key=kf)
    print(f"{fonte}: {len(regs)} artigos | maior {max(nums)} | faltam 1..max ({len(falta)}): {falta[:15]}")
    print(f"  so' com cabecalho indentado ({len(resgatados)}): {resgatados[:15]}")
    print("  ex art 1:", regs[0]['texto'][:80].replace("\n", " "))


if __name__ == "__main__":
    main()
