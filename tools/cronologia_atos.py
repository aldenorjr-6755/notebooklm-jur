#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cronologia_atos.py — linha do tempo PROCESSUAL deterministica a partir do atos.jsonl.

Uma linha por ato, ordenada pela data de juntada (empate: ordem nos autos), cada uma com a
ancora [ID | vol p. N] que a minuta cita. Agrupa em fases pela sequencia de tipos (investigacao,
denuncia/recebimento, instrucao, sentenca, recurso, execucao) e separa os atos sem data.

Isto e' a cronologia dos ATOS; os fatos internos a cada ato (o que a testemunha disse, quando o
crime ocorreu) sao trabalho do distilador com LLM da fase 6, que acrescenta linhas a este
arquivo sem apagar as daqui. Tambem grava marcos.json (recebimento, audiencia, sentenca, acordao,
transito) para prazo_cpp.py e prescricao_cp.py.

Uso:
  python cronologia_atos.py <extracted>/atos.jsonl [--saida <extracted>/../cronologia.md]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from collections import Counter
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

FASE_POR_TIPO = {
    "investigação": {"AUTO DE PRISAO EM FLAGRANTE", "AUTO DE EXIBICAO E APREENSAO", "AUTO DE RECONHECIMENTO",
                     "TERMO DE INTERROGATORIO", "TERMO DE DECLARACOES", "BOLETIM DE OCORRENCIA", "RELATORIO FINAL IP",
                     "REPRESENTACAO", "PORTARIA", "LAUDO", "AUTO DE INFRACAO", "RELATORIO DE FISCALIZACAO",
                     "INFORMACAO TECNICA", "ANEXO PROCEDIMENTO EXTERNO"},
    "acusação": {"DENUNCIA", "ADITAMENTO DENUNCIA", "QUEIXA-CRIME", "RECEBIMENTO DENUNCIA"},
    "defesa": {"RESPOSTA A ACUSACAO", "PEDIDO DE LIBERDADE", "HABEAS CORPUS", "PROCURACAO"},
    "instrução": {"TERMO DE AUDIENCIA", "AUDIENCIA DE CUSTODIA", "CARTA PRECATORIA", "MANDADO", "OFICIO",
                  "INTIMACAO", "CERTIDAO", "CERTIDAO DE PUBLICACAO", "TERMO", "DESPACHO", "DECISAO", "PETICAO",
                  "PARECER MP", "COMUNICACAO ELETRONICA", "PROTOCOLO", "DOCUMENTO DIVERSO"},
    "julgamento": {"ALEGACOES FINAIS", "SENTENCA", "PRONUNCIA"},
    "recurso": {"APELACAO", "RAZOES DE APELACAO", "CONTRARRAZOES", "ACORDAO", "CERTIDAO DE TRANSITO"},
    "execução": {"GUIA DE EXECUCAO", "ATESTADO DE PENA"},
}
TIPO2FASE = {t: f for f, ts in FASE_POR_TIPO.items() for t in ts}
MARCOS = {"RECEBIMENTO DENUNCIA": "recebimento_denuncia", "TERMO DE AUDIENCIA": "audiencia", "SENTENCA": "sentenca",
          "ACORDAO": "acordao", "CERTIDAO DE TRANSITO": "transito_em_julgado", "PRONUNCIA": "pronuncia",
          "DENUNCIA": "denuncia", "RESPOSTA A ACUSACAO": "resposta_acusacao", "ALEGACOES FINAIS": "alegacoes_finais"}


import re

# Marcos que ficam DENTRO de outro ato (no JECrim o recebimento da denuncia sai num despacho ou na
# propria ata; o transito em julgado numa certidao generica). Varre o texto dos atos destes tipos.
MARCOS_NO_TEXTO = [
    # so a forma AFIRMATIVA: "recebo a (presente) denuncia", "a denuncia e recebida". O texto-padrao
    # dos despachos do JECrim diz "eventual recebimento da denuncia" (nao e' marco) e a ata diz
    # "RECEBIMENTO DA DENUNCIA: ... recebo a presente denuncia" (e' marco pelo "recebo").
    ("recebimento_denuncia", {"DECISAO", "DESPACHO", "TERMO DE AUDIENCIA", "SENTENCA", "TERMO"},
     re.compile(r"(?<!N[ÃA]O\s)(?<!DEIXO\sDE\s)\bRECEB[OE]\s+(A\s+|A\s+PRESENTE\s+)?DEN[ÚU]NCIA|"
                r"\bDEN[ÚU]NCIA\s+(É|E|FOI)\s+RECEBIDA|\bRECEBIDA\s+A\s+DEN[ÚU]NCIA", re.I)),
    ("sentenca", {"TERMO DE AUDIENCIA", "DECISAO"},
     re.compile(r"\bJULGO\s+(PROCEDENTE|IMPROCEDENTE|PARCIALMENTE)|\bCONDENO\b|\bABSOLVO\b", re.I)),
    ("transito_em_julgado", {"CERTIDAO", "TERMO", "DESPACHO"},
     re.compile(r"TRANSITOU\s+EM\s+JULGADO|TR[ÂA]NSITO\s+EM\s+JULGADO\s+(EM|OCORRIDO|CERTIFICADO)", re.I)),
    ("citacao", {"CERTIDAO", "MANDADO", "CARTA PRECATORIA", "TERMO"},
     re.compile(r"\bCITEI\b|\bDEVIDAMENTE\s+CITAD[OA]|\bCITAÇÃO\s+(PESSOAL\s+)?(REALIZADA|EFETIVADA|CUMPRIDA)|CIT[OA][UE]\s+O\s+(R[ÉE]U|ACUSADO|DENUNCIADO)", re.I)),
    # causas suspensivas: so quando ACEITA/HOMOLOGADA/DEFERIDA. "deixou de ofertar a proposta" nao e'.
    ("suspensao_condicional_processo", {"TERMO DE AUDIENCIA", "DECISAO", "TERMO"},
     re.compile(r"(ACEIT[AO]U?|HOMOLOG[OA]D?[AO]?|DEFIRO|DEFERID[AO]|CONCED[OI]D?[AO]?)\s+(A\s+)?(PROPOSTA\s+DE\s+)?SUSPENS[ÃA]O\s+CONDICIONAL|"
                r"SUSPENS[ÃA]O\s+CONDICIONAL\s+DO\s+PROCESSO[^.]{0,80}\b(ACEIT|HOMOLOG|DEFERID)|"
                r"\bSUSPENDO\s+O\s+(PROCESSO|FEITO)\b", re.I)),
    ("transacao_penal", {"TERMO DE AUDIENCIA", "DECISAO", "TERMO"},
     re.compile(r"TRANSA[ÇC][ÃA]O\s+PENAL[^.]{0,60}\b(ACEIT|HOMOLOG)|HOMOLOGO\s+A\s+TRANSA[ÇC][ÃA]O", re.I)),
]


def marcos_no_texto(atos: list[dict], extracted: Path) -> dict[str, list]:
    out: dict[str, list] = {}
    for a in atos:
        tipos = {a.get("tipo")}
        alvo = [(k, rx) for k, ts, rx in MARCOS_NO_TEXTO if tipos & ts]
        if not alvo:
            continue
        try:
            txt = io.open(extracted / a["arquivo"], encoding="utf-8").read()
        except OSError:
            continue
        corpo = txt.split("\n---\n", 1)[-1]
        for k, rx in alvo:
            m = rx.search(corpo)
            if m:
                trecho = " ".join(corpo[max(0, m.start() - 80):m.end() + 80].split())
                out.setdefault(k, []).append({"data": a.get("data_juntada"), "id_pje": a.get("id_pje"),
                                              "ancora": ancora(a), "titulo": a.get("titulo"),
                                              "origem": "texto do ato", "trecho": trecho[:240]})
    return out


def ancora(a: dict) -> str:
    return f"[ID {a.get('id_pje') or '-'} | {a.get('volume_ini')} p. {a.get('pag_ini')}" + \
           (f"–{a.get('volume_fim')} p. {a.get('pag_fim')}" if a.get("pag_fim") != a.get("pag_ini") else "") + "]"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("atos")
    ap.add_argument("--saida")
    ap.add_argument("--marcos", help="marcos.json (padrão: ao lado da saída)")
    a = ap.parse_args(argv)
    jp = Path(a.atos)
    atos = [json.loads(l) for l in io.open(jp, encoding="utf-8")]
    cnj = atos[0].get("cnj") if atos else None
    com_data = sorted([x for x in atos if x.get("data_juntada")], key=lambda x: (x["data_juntada"], x["seq"]))
    sem_data = [x for x in atos if not x.get("data_juntada") and x.get("tipo") != "CAPA INDICE"]

    L = [f"# Cronologia dos atos — {cnj or 'sem CNJ'}", "",
         f"> {len(atos)} atos fatiados; {len(com_data)} com data de juntada, {len(sem_data)} sem. Gerado por `cronologia_atos.py`.",
         "> Cada linha é um ATO (o que foi juntado e quando). Fatos internos aos atos entram pelo distilador da fase 6.",
         "", "| data | âncora | fase | tipo | título | avisos |", "|---|---|---|---|---|---|"]
    marcos: dict[str, list] = {}
    for x in com_data:
        t = x.get("tipo") or "?"
        fase = TIPO2FASE.get(t, "outros")
        av = "; ".join(x.get("avisos") or [])
        L.append(f"| {x['data_juntada']} | {ancora(x)} | {fase} | {t} | {(x.get('titulo') or '')[:70]} | {av[:90]} |")
        if t in MARCOS:
            marcos.setdefault(MARCOS[t], []).append({"data": x["data_juntada"], "id_pje": x.get("id_pje"),
                                                     "ancora": ancora(x), "titulo": x.get("titulo")})
    if sem_data:
        L += ["", "## Atos sem data de juntada (posição nos autos)", "", "| seq | âncora | tipo | título | avisos |", "|---|---|---|---|---|"]
        for x in sem_data:
            L.append(f"| {x['seq']} | {ancora(x)} | {x.get('tipo')} | {(x.get('titulo') or '')[:70]} | {'; '.join(x.get('avisos') or [])[:90]} |")
    for m in marcos.values():
        for x in m:
            x["origem"] = "tipo do ato"
    for k, v in marcos_no_texto(atos, jp.parent).items():
        ja = {(x.get("id_pje"), x.get("data")) for x in marcos.get(k, [])}
        marcos.setdefault(k, []).extend(x for x in v if (x.get("id_pje"), x.get("data")) not in ja)
    L += ["", "## Marcos detectados (pelo tipo do ato e pelo texto)", "",
          "> Marco lido do TEXTO traz o trecho: conferir antes de usar em prazo ou prescrição.", ""]
    for k, v in marcos.items():
        L.append(f"- **{k}**:")
        for m in sorted(v, key=lambda x: x.get("data") or "9999"):
            L.append(f"  - {m.get('data') or 'sem data'} {m['ancora']} ({m['origem']})" + (f" — “{m['trecho']}”" if m.get("trecho") else ""))
    if not marcos:
        L.append("(nenhum)")
    fases = Counter(TIPO2FASE.get(x.get("tipo"), "outros") for x in atos)
    L += ["", "## Contagem por fase", "", "| fase | atos |", "|---|---|"] + [f"| {f} | {n} |" for f, n in fases.most_common()]

    saida = Path(a.saida) if a.saida else jp.parent.parent / "cronologia.md"
    saida.parent.mkdir(parents=True, exist_ok=True)
    io.open(saida, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    mp = Path(a.marcos) if a.marcos else saida.parent / "distill" / "marcos.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    io.open(mp, "w", encoding="utf-8", newline="\n").write(json.dumps({"cnj": cnj, "marcos": marcos}, ensure_ascii=False, indent=1))
    print(f"atos={len(atos)} com_data={len(com_data)} sem_data={len(sem_data)} marcos={list(marcos)} -> {saida}, {mp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
