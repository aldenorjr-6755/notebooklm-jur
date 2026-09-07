#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prazo_cpp.py — prazo PENAL por script deterministico (nunca de cabeca).

Regime (CPP art. 798): prazos CONTINUOS e PEREMPTORIOS, em DIAS CORRIDOS; nao se interrompem
por ferias, domingo ou feriado (caput); exclui-se o dia do comeco e inclui-se o do vencimento
(§ 1o); se o vencimento cai em dia sem expediente, prorroga-se ao primeiro dia util seguinte
(§ 3o). Sumula 310 STF: intimacao na sexta-feira (ou publicacao com efeito de intimacao nesse
dia) -> prazo comeca na segunda-feira imediata, salvo se nao houver expediente. Sumula 710 STF:
no processo penal o prazo conta da INTIMACAO, nao da juntada do mandado/carta aos autos.
Recesso de 20/12 a 20/01 (CPC 220): NAO aplicado por padrao no processo penal (entendimento
dominante do STJ: art. 798 CPP afasta a suspensao do CPC); use --recesso se o tribunal local
suspender prazos por ato proprio, e diga qual.

Dois modos:
  1) CALCULO de um prazo:
     python prazo_cpp.py --intimacao 2026-09-04 --dias 5 [--recesso] [--feriados-locais x.json]
  2) RADAR a partir dos atos fatiados (fatiar_atos.py):
     python prazo_cpp.py --atos <extracted>/atos.jsonl [--rito auto|ordinario|sumario|jecrim] [--hoje AAAA-MM-DD]
     -> lista os atos que costumam abrir prazo para a DEFESA, com o prazo-padrao da peca e o
        vencimento presumido (dies a quo = data de juntada, que NAO e' a intimacao: conferir).
        Grava <extracted>/../distill/prazos.md quando --saida nao e' dado.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import calendario_forense as CF  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


# --------------------------------------------------------------------------
# Calculo
# --------------------------------------------------------------------------
def calcular(intimacao: date, dias: int, locais=None, recesso: bool = False) -> dict:
    trilha = []
    # Sumula 310 STF: intimacao na sexta -> comeca na segunda (ou proximo dia util)
    inicio = intimacao + timedelta(days=1)          # CPP 798 §1o: exclui o dia do comeco
    motivo_ini = CF.motivo_nao_util(inicio, locais, recesso)
    if motivo_ini:
        novo = CF.proximo_util(inicio, locais, recesso)
        trilha.append(f"inicio {inicio.isoformat()} nao e' util ({motivo_ini}) -> comeca em {novo.isoformat()} (Sum. 310 STF / CPP 798 §3o)")
        inicio = novo
    fim = inicio + timedelta(days=dias - 1)           # dias corridos, inclusive o do vencimento
    d = inicio
    while d <= fim:
        m = CF.motivo_nao_util(d, locais, recesso)
        trilha.append(f"{d.isoformat()} {'(' + m + ') CONTA MESMO ASSIM — dias corridos' if m else 'dia corrido'}")
        d += timedelta(days=1)
    motivo_fim = CF.motivo_nao_util(fim, locais, recesso)
    prorrogado = None
    if motivo_fim:
        prorrogado = CF.proximo_util(fim, locais, recesso)
        trilha.append(f"vencimento {fim.isoformat()} cai em {motivo_fim} -> prorroga para {prorrogado.isoformat()} (CPP 798 §3o)")
    return {"intimacao": intimacao.isoformat(), "dias": dias, "inicio": inicio.isoformat(),
            "vencimento_nominal": fim.isoformat(), "vencimento": (prorrogado or fim).isoformat(),
            "prorrogado": bool(prorrogado), "trilha": trilha}


# --------------------------------------------------------------------------
# Radar: que ato abre que prazo para a defesa
# --------------------------------------------------------------------------
# (tipo do ato, rito) -> lista de (peca, dias, fundamento, observacao)
PRAZOS_DEFESA = {
    "DENUNCIA": [("resposta à acusação", 10, "CPP 396/396-A", "conta da CITAÇÃO (Súm. 710 STF), não da juntada da denúncia"),
                 ("resposta à acusação (Lei 11.343/06 — defesa prévia)", 10, "Lei 11.343 art. 55", "só em tráfico: antes do recebimento")],
    "RECEBIMENTO DENUNCIA": [("resposta à acusação", 10, "CPP 396", "conta da citação")],
    "DECISAO": [("recurso em sentido estrito", 5, "CPP 581/586", "só se a decisão estiver no rol do art. 581"),
                ("embargos de declaração", 2, "CPP 382 (por analogia) / 619", ""),
                ("habeas corpus", 0, "CF 5º LXVIII", "sem prazo")],
    "PRONUNCIA": [("recurso em sentido estrito", 5, "CPP 581 IV / 586", "")],
    "SENTENCA": [("apelação", 5, "CPP 593/600", "razões em 8 dias após a intimação para arrazoar (CPP 600)"),
                 ("embargos de declaração", 2, "CPP 382", "")],
    "ACORDAO": [("embargos de declaração", 2, "CPP 619", ""),
                ("embargos infringentes e de nulidade", 10, "CPP 609 p.u.", "só acórdão não unânime desfavorável"),
                ("recurso especial / extraordinário", 15, "CPC 1.003 §5º c/c CPP 798 (dias corridos)", ""),
                ("recurso ordinário em HC", 5, "CPP 30 c/c RISTJ", "")],
    "INTIMACAO": [("manifestação (prazo do próprio ato)", 5, "conferir o mandado", "o prazo é o que consta da intimação")],
    "TERMO DE AUDIENCIA": [("memoriais / alegações finais escritas", 5, "CPP 403 §3º", "só quando o juiz converter os debates em memoriais")],
    "ALEGACOES FINAIS": [("memoriais da defesa", 5, "CPP 403 §3º", "após os memoriais do MP; conta da intimação")],
    "CERTIDAO DE PUBLICACAO": [("(prazo do ato publicado)", 0, "—", "a certidão fixa o dies a quo do ato publicado")],
}
# JECrim (Lei 9.099/95) substitui os prazos da sentenca/acordao
PRAZOS_JECRIM = {
    "SENTENCA": [("apelação (JECrim)", 10, "Lei 9.099 art. 82 §1º", "razões junto com a interposição"),
                 ("embargos de declaração (JECrim)", 5, "Lei 9.099 art. 83 §1º", "")],
    "ACORDAO": [("embargos de declaração (JECrim)", 5, "Lei 9.099 art. 83 §1º", ""),
                ("recurso extraordinário", 15, "CF 102 III; não cabe REsp de Turma Recursal (Súm. 203 STJ)", "")],
    "DENUNCIA": [("defesa oral na audiência preliminar/instrução", 0, "Lei 9.099 art. 81", "sem prazo escrito: resposta é oral, antes do recebimento")],
}
TIPOS_QUE_ABREM_PRAZO = set(PRAZOS_DEFESA) | set(PRAZOS_JECRIM)


def detectar_rito(atos: list[dict], extracted: Path) -> str:
    """Le a capa (ato 1) atras de 'SUMARÍSSIMO' / 'JUIZADO ESPECIAL' / 'SUMÁRIO'."""
    try:
        capa = [a for a in atos if a.get("tipo") == "CAPA INDICE"][0]
        txt = io.open(extracted / capa["arquivo"], encoding="utf-8").read()[:4000].upper()
    except (IndexError, OSError):
        return "ordinario"
    if "SUMAR" in txt and ("ÍSSIMO" in txt or "ISSIMO" in txt) or "JUIZADO ESPECIAL" in txt:
        return "jecrim"
    if re.search(r"PROCEDIMENTO\s+SUM[ÁA]RIO\b", txt):
        return "sumario"
    return "ordinario"


def radar(atos: list[dict], rito: str, hoje: date, locais, recesso: bool) -> list[dict]:
    linhas = []
    for a in atos:
        tipo = a.get("tipo")
        if tipo not in TIPOS_QUE_ABREM_PRAZO:
            continue
        regras = (PRAZOS_JECRIM.get(tipo) if rito == "jecrim" else None) or PRAZOS_DEFESA.get(tipo, [])
        d = a.get("data_juntada")
        for peca, dias, fund, obs in regras:
            item = {"seq": a["seq"], "id_pje": a.get("id_pje"), "ato": tipo, "titulo": a.get("titulo"),
                    "data_juntada": d, "peca": peca, "dias": dias, "fundamento": fund, "obs": obs,
                    "vencimento_presumido": None, "status": None}
            if d and dias:
                try:
                    c = calcular(date.fromisoformat(d), dias, locais, recesso)
                    v = date.fromisoformat(c["vencimento"])
                    item["vencimento_presumido"] = c["vencimento"]
                    item["status"] = "VENCIDO" if v < hoje else f"faltam {(v - hoje).days} d"
                except ValueError:
                    item["status"] = "data ilegível"
            elif not d:
                item["status"] = "sem data de juntada"
            linhas.append(item)
    return linhas


def md_radar(cnj: str | None, rito: str, hoje: date, linhas: list[dict], recesso: bool) -> str:
    L = [f"# Radar de prazos — {cnj or 'sem CNJ'}", "",
         f"> Gerado em {hoje.isoformat()} por `prazo_cpp.py` (dias corridos, CPP 798; Súm. 310 e 710 STF). "
         f"Rito detectado: **{rito}**. Recesso 20/12–20/01: {'aplicado por opção' if recesso else 'NÃO aplicado (CPP 798)'}.",
         ">",
         "> **O dies a quo abaixo é a DATA DE JUNTADA do ato, não a intimação.** No processo penal o prazo",
         "> corre da intimação (Súm. 710 STF); a intimação da defesa pelo DJEN/portal costuma ocorrer dias",
         "> depois da juntada. Cada linha é um alerta para conferir a intimação real, não uma data fatal.", "",
         "| seq | ID PJe | ato | juntada | peça da defesa | dias | vencimento presumido | situação | fundamento | obs |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for x in linhas:
        L.append(f"| {x['seq']} | {x['id_pje'] or '-'} | {x['ato']} | {x['data_juntada'] or '-'} | {x['peca']} | "
                 f"{x['dias'] or '—'} | {x['vencimento_presumido'] or '-'} | {x['status'] or '-'} | {x['fundamento']} | {x['obs']} |")
    pend = [x for x in linhas if x["status"] and x["status"].startswith("faltam")]
    L += ["", "## Em aberto (pela juntada)", ""]
    L += [f"- **{x['peca']}** contra o ato {x['ato']} (ID {x['id_pje']}, juntado em {x['data_juntada']}): "
          f"vence {x['vencimento_presumido']} ({x['status']}) — conferir intimação" for x in pend] or ["(nenhum)"]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intimacao", help="data da intimação (AAAA-MM-DD) — modo cálculo")
    ap.add_argument("--dias", type=int, help="prazo em dias corridos — modo cálculo")
    ap.add_argument("--atos", help="atos.jsonl do fatiar_atos.py — modo radar")
    ap.add_argument("--rito", default="auto", choices=["auto", "ordinario", "sumario", "jecrim"])
    ap.add_argument("--hoje", help="AAAA-MM-DD (padrão: hoje)")
    ap.add_argument("--recesso", action="store_true", help="aplicar suspensão 20/12–20/01 (só se o tribunal local o fizer)")
    ap.add_argument("--feriados-locais", help="JSON {data: motivo} com feriados locais além dos embutidos")
    ap.add_argument("--comarca", help="comarca do juízo (liga os feriados MUNICIPAIS conhecidos, ex.: 'São Luís'); "
                                      "sem ela só entram os estaduais e os do TJMA")
    ap.add_argument("--saida", help="arquivo .md do radar (padrão: <extracted>/../distill/prazos.md)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    locais = CF.carregar_locais(a.feriados_locais, a.comarca)
    hoje = date.fromisoformat(a.hoje) if a.hoje else date.today()
    if not a.json:
        print(f"feriados locais em vigor: {len(locais)} (comarca: {a.comarca or 'não informada — só estaduais/TJMA'})")

    if a.intimacao and a.dias:
        r = calcular(date.fromisoformat(a.intimacao), a.dias, locais, a.recesso)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=1))
        else:
            print(f"intimação {r['intimacao']} · {r['dias']} dias corridos (CPP 798) · início {r['inicio']}")
            for t in r["trilha"]:
                print("  ", t)
            print(f"VENCIMENTO: {r['vencimento']}" + (" (prorrogado, CPP 798 §3º)" if r["prorrogado"] else ""))
        return 0
    if a.atos:
        jp = Path(a.atos)
        atos = [json.loads(l) for l in io.open(jp, encoding="utf-8")]
        rito = detectar_rito(atos, jp.parent) if a.rito == "auto" else a.rito
        linhas = radar(atos, rito, hoje, locais, a.recesso)
        cnj = atos[0].get("cnj") if atos else None
        if a.json:
            print(json.dumps({"cnj": cnj, "rito": rito, "hoje": hoje.isoformat(), "prazos": linhas}, ensure_ascii=False, indent=1))
            return 0
        md = md_radar(cnj, rito, hoje, linhas, a.recesso)
        saida = Path(a.saida) if a.saida else jp.parent.parent / "distill" / "prazos.md"
        saida.parent.mkdir(parents=True, exist_ok=True)
        io.open(saida, "w", encoding="utf-8", newline="\n").write(md)
        print(f"rito={rito} atos_com_prazo={len(linhas)} -> {saida}")
        return 0
    ap.error("use --intimacao + --dias (cálculo) ou --atos (radar)")


if __name__ == "__main__":
    sys.exit(main())
