#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prescricao_cp.py — prescricao da pretensao punitiva (PPP) por script, com cada marco e sua fonte.

O que calcula (CP arts. 109-119):
  * prazo prescricional pela PENA MAXIMA em abstrato (CP 109): >12a -> 20a; >8 a 12 -> 16a;
    >4 a 8 -> 12a; >2 a 4 -> 8a; 1 a 2 -> 4a; <1a -> 3a (Lei 12.234/2010; para fato anterior a
    06/05/2010 o prazo minimo era 2a). Multa isolada: 2a (CP 114 I).
  * reducao pela metade (CP 115): agente menor de 21 na data do fato, ou maior de 70 na data da
    sentenca (--nascimento; --data-sentenca).
  * marcos interruptivos (CP 117): recebimento da denuncia (I), pronuncia (II), decisao
    confirmatoria da pronuncia (III), sentenca ou acordao condenatorio recorrivel (IV) e, na
    execucao, inicio/continuacao do cumprimento e reincidencia (V, VI). A interrupcao reinicia a
    contagem do zero (CP 117 §2o).
  * intervalos: fato -> recebimento; recebimento -> sentenca; sentenca -> hoje/transito. Para cada
    um, tempo corrido, prazo aplicavel e data em que prescreve(ria).
  * apos a sentenca condenatoria com transito para a acusacao, a PPP retroativa/superveniente usa
    a PENA CONCRETA (CP 110 §1o); a retroativa NAO alcanca periodo anterior a denuncia para fato
    posterior a 06/05/2010. Informe --pena-concreta para esse calculo.
  * causas suspensivas (CP 116; CPP 366 — reu citado por edital; Lei 9.099 art. 89 §6o — sursis
    processual; CPP 28-A §10 — ANPP em cumprimento): so entram por --suspensao INI FIM MOTIVO,
    porque nao sao derivaveis dos atos com seguranca.

Pena maxima: --pena-max "3a" | "2a6m" | "6m", ou --dispositivo cp:155 / lei9605:38 (le a pena
no texto do dataset canonico ~/.notebooklm/tools/<fonte>_artigos.json e mostra o trecho lido).
Marcos: --atos <extracted>/atos.jsonl (le RECEBIMENTO DENUNCIA, PRONUNCIA, SENTENCA, ACORDAO com
data) e/ou --marco AAAA-MM-DD "descricao". Data do fato: --fato AAAA-MM-DD (crime permanente:
--fato = cessacao da permanencia, CP 111 III).

Tudo que o script NAO souber fica marcado [CONFERIR]. Ele nao decide: expoe a conta.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

TOOLS = Path(__file__).resolve().parent
if not (TOOLS / "cp_artigos.json").exists() and (TOOLS.parent / "cp_artigos.json").exists():
    TOOLS = TOOLS.parent          # layout de vault: .claude/tools/pipeline/<este>.py, datasets em ..
LEI_12234 = date(2010, 5, 6)     # vigencia da Lei 12.234/2010 (publicada em 06/05/2010)


# --------------------------------------------------------------------------
# Pena
# --------------------------------------------------------------------------
def parse_pena(s: str) -> int:
    """'3a' | '2a6m' | '6m' | '1 ano' | '2 anos e 6 meses' -> meses."""
    s = s.lower().replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)a(?:nos?)?)?(?:e?(\d+)m(?:es(?:es)?)?)?", s)
    if not m or not (m.group(1) or m.group(2)):
        raise ValueError(f"pena ilegível: {s!r} (use 3a, 2a6m, 6m)")
    return int(m.group(1) or 0) * 12 + int(m.group(2) or 0)


def fmt_meses(m: int) -> str:
    a, r = divmod(m, 12)
    return " e ".join(x for x in [f"{a} ano{'s' if a != 1 else ''}" if a else "", f"{r} mes{'es' if r != 1 else ''}" if r else ""] if x) or "0"


EXTENSO = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6,
           "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12, "quinze": 15, "vinte": 20, "trinta": 30}


def _num(s: str) -> int:
    s = s.strip().lower()
    return int(s) if s.isdigit() else EXTENSO.get(s, 0)


def pena_do_dispositivo(fonte: str, artigo: str) -> tuple[int | None, str]:
    """Le 'reclusão/detenção, de X (mês/ano) a Y (mês/ano)' no caput do artigo do dataset."""
    arq = TOOLS / f"{fonte}_artigos.json"
    if not arq.is_file():
        return None, f"dataset {arq.name} não existe"
    d = json.loads(arq.read_text(encoding="utf-8"))
    arts = d.get("artigos") or []
    alvo = next((x for x in arts if str(x.get("artigo")) == str(artigo)), None)
    if not alvo:
        return None, f"art. {artigo} não está em {arq.name}"
    txt = alvo.get("texto", "")
    # so o caput: corta no primeiro paragrafo/inciso
    caput = re.split(r"\n\s*(?:§|Par[áa]grafo|I\s*[-–]|Pena\s*[-–]\s*multa)", txt, maxsplit=1)[0]
    m = re.search(r"(reclus[ãa]o|deten[çc][ãa]o)\s*,?\s*de\s+([\w]+)\s*\(?(\d*)\)?\s*(m[êe]s(?:es)?|anos?)"
                  r"\s*(?:a|e)\s+([\w]+)\s*\(?(\d*)\)?\s*(m[êe]s(?:es)?|anos?)", caput, re.I)
    if not m:
        return None, f"não achei 'reclusão/detenção, de X a Y' no caput do art. {artigo} ({fonte}); trecho: {caput[:160]!r}"
    maxi = int(m.group(6)) if m.group(6) else _num(m.group(5))
    meses = maxi * (12 if m.group(7).lower().startswith("ano") else 1)
    return meses, m.group(0)


def prazo_cp109(pena_max_meses: int, fato: date | None) -> tuple[int, str]:
    """-> (meses de prescricao, fundamento)."""
    a = pena_max_meses / 12
    if a > 12:
        return 240, "CP 109 I (pena máxima > 12 anos): 20 anos"
    if a > 8:
        return 192, "CP 109 II (> 8 e ≤ 12): 16 anos"
    if a > 4:
        return 144, "CP 109 III (> 4 e ≤ 8): 12 anos"
    if a > 2:
        return 96, "CP 109 IV (> 2 e ≤ 4): 8 anos"
    if a >= 1:
        return 48, "CP 109 V (≥ 1 e ≤ 2): 4 anos"
    if fato and fato < LEI_12234:
        return 24, "CP 109 VI, redação anterior à Lei 12.234/2010 (fato antes de 06/05/2010): 2 anos"
    return 36, "CP 109 VI (< 1 ano; Lei 12.234/2010): 3 anos"


def add_meses(d: date, meses: int) -> date:
    m = d.month - 1 + meses
    ano, mes = d.year + m // 12, m % 12 + 1
    dia = min(d.day, [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return date(ano, mes, dia)


def idade_em(nasc: date, d: date) -> int:
    return d.year - nasc.year - ((d.month, d.day) < (nasc.month, nasc.day))


# --------------------------------------------------------------------------
# Marcos
# --------------------------------------------------------------------------
MARCOS_ATOS = {"RECEBIMENTO DENUNCIA": "recebimento da denúncia (CP 117 I)",
               "PRONUNCIA": "pronúncia (CP 117 II)",
               "SENTENCA": "sentença condenatória recorrível (CP 117 IV) [CONFERIR: se absolutória, NÃO interrompe]",
               "ACORDAO": "acórdão condenatório recorrível (CP 117 IV) [CONFERIR: se confirmatório ou absolutório, ver Tema 1.100 STJ / HC 176.473 STF]"}


MARCOS_JSON = {"recebimento_denuncia": "recebimento da denúncia (CP 117 I)", "pronuncia": "pronúncia (CP 117 II)",
               "sentenca": "sentença condenatória recorrível (CP 117 IV) [CONFERIR: se absolutória, NÃO interrompe]",
               "acordao": "acórdão condenatório recorrível (CP 117 IV) [CONFERIR]"}


def marcos_do_json(caminho: str) -> tuple[list[tuple[date, str, str]], list[str]]:
    """Le o marcos.json do cronologia_atos.py (inclui marcos achados no TEXTO dos atos)."""
    d = json.loads(io.open(caminho, encoding="utf-8").read())
    out, avisos = [], []
    for k, desc in MARCOS_JSON.items():
        for m in d.get("marcos", {}).get(k, []):
            if not m.get("data"):
                continue
            try:
                out.append((date.fromisoformat(m["data"]), desc + (f" — lido do texto: “{m['trecho'][:120]}…”" if m.get("trecho") else ""), m.get("ancora", "")))
            except ValueError:
                pass
    susp = [k for k in ("suspensao_condicional_processo", "transacao_penal") if d.get("marcos", {}).get(k)]
    if susp:
        avisos.append(f"marcos.json indica {', '.join(susp)}: há causa SUSPENSIVA provável (Lei 9.099 art. 89 §6º / CP 116) — informe --suspensao INI FIM MOTIVO")
    return out, avisos


def marcos_dos_atos(caminho: str) -> list[tuple[date, str, str]]:
    out = []
    for l in io.open(caminho, encoding="utf-8"):
        a = json.loads(l)
        t = a.get("tipo")
        if t in MARCOS_ATOS and a.get("data_juntada"):
            try:
                out.append((date.fromisoformat(a["data_juntada"]), MARCOS_ATOS[t], f"ID {a.get('id_pje')} {a.get('volume_ini')} p. {a.get('pag_ini')}"))
            except ValueError:
                pass
    return out


# --------------------------------------------------------------------------
def calcular(pena_max: int, fato: date | None, marcos: list[tuple[date, str, str]], hoje: date,
             nascimento: date | None, data_sentenca: date | None, pena_concreta: int | None,
             suspensoes: list[tuple[date, date, str]]) -> dict:
    avisos = []
    prazo, fund = prazo_cp109(pena_max, fato)
    reduz = False
    if nascimento:
        if fato and idade_em(nascimento, fato) < 21:
            reduz, avisos = True, avisos + ["CP 115: agente menor de 21 anos na data do fato → prazo pela metade"]
        if data_sentenca and idade_em(nascimento, data_sentenca) > 70:
            reduz, avisos = True, avisos + ["CP 115: agente maior de 70 anos na data da sentença → prazo pela metade"]
    prazo_ef = prazo // 2 if reduz else prazo
    susp_total = sum((f - i).days for i, f, _ in suspensoes)

    pontos = [(fato, "fato (CP 111 I) — crime permanente: cessação (CP 111 III)", "informado")] if fato else []
    pontos += sorted(marcos)
    if not fato:
        avisos.append("sem --fato: o primeiro intervalo (fato → recebimento) não foi calculado")
    intervalos = []
    for i in range(len(pontos)):
        ini, desc_ini, fonte = pontos[i]
        fim = pontos[i + 1][0] if i + 1 < len(pontos) else hoje
        desc_fim = pontos[i + 1][1] if i + 1 < len(pontos) else "hoje (em curso)"
        limite = add_meses(ini, prazo_ef)
        if susp_total:
            from datetime import timedelta
            limite = limite + timedelta(days=susp_total)
        intervalos.append({"de": ini.isoformat(), "de_desc": desc_ini, "fonte": fonte, "ate": fim.isoformat(),
                           "ate_desc": desc_fim, "dias": (fim - ini).days,
                           "prescreve_em": limite.isoformat(),
                           "prescrito": fim > limite, "em_curso": i + 1 >= len(pontos)})
    concreta = None
    if pena_concreta:
        p2, f2 = prazo_cp109(pena_concreta, fato)
        p2 = p2 // 2 if reduz else p2
        concreta = {"pena_concreta": fmt_meses(pena_concreta), "prazo": fmt_meses(p2), "fundamento": f2 + " (CP 110 §1º, pena concreta)",
                    "nota": "vale para a PPP retroativa (entre recebimento da denúncia e sentença) e superveniente (após a sentença), depois do trânsito para a acusação; não alcança período anterior à denúncia (fato pós-2010)"}
        # recalcula intervalos apos o recebimento com a pena concreta
        for it in intervalos:
            if "recebimento" in it["de_desc"] or "sentença" in it["de_desc"] or "acórdão" in it["de_desc"] or "pronúncia" in it["de_desc"]:
                lim = add_meses(date.fromisoformat(it["de"]), p2)
                it["prescreve_em_pena_concreta"] = lim.isoformat()
                it["prescrito_pena_concreta"] = date.fromisoformat(it["ate"]) > lim
    return {"pena_maxima": fmt_meses(pena_max), "prazo_abstrato": fmt_meses(prazo), "fundamento": fund,
            "reducao_cp115": reduz, "prazo_efetivo": fmt_meses(prazo_ef),
            "suspensoes_dias": susp_total, "intervalos": intervalos, "pena_concreta": concreta, "avisos": avisos}


def md(r: dict, cnj: str | None, hoje: date, origem_pena: str) -> str:
    L = [f"# Prescrição — {cnj or 'sem CNJ'}", "",
         f"> Gerado em {hoje.isoformat()} por `prescricao_cp.py`. Conta exposta, não decisão. Tudo marcado [CONFERIR] exige leitura do ato.", "",
         f"- Pena máxima em abstrato: **{r['pena_maxima']}** ({origem_pena})",
         f"- Prazo prescricional: **{r['prazo_abstrato']}** — {r['fundamento']}" + (f"; reduzido à metade (CP 115): **{r['prazo_efetivo']}**" if r["reducao_cp115"] else ""),
         f"- Suspensões informadas (CP 116 etc.): {r['suspensoes_dias']} dias" if r["suspensoes_dias"] else "- Suspensões (CP 116; CPP 366; Lei 9.099 art. 89 §6º; CPP 28-A §10): nenhuma informada [CONFERIR nos autos]",
         "", "## Intervalos (a interrupção reinicia a contagem — CP 117 §2º)", "",
         "| de | marco inicial | fonte | até | marco final | dias corridos | prescreve(ria) em | situação |",
         "|---|---|---|---|---|---|---|---|"]
    for it in r["intervalos"]:
        sit = "**PRESCRITO**" if it["prescrito"] else ("em curso" if it["em_curso"] else "interrompido antes do prazo")
        L.append(f"| {it['de']} | {it['de_desc']} | {it['fonte']} | {it['ate']} | {it['ate_desc']} | {it['dias']} | {it['prescreve_em']} | {sit} |")
    if r["pena_concreta"]:
        pc = r["pena_concreta"]
        L += ["", "## Pena concreta (CP 110 §1º)", "", f"- Pena aplicada: **{pc['pena_concreta']}** → prazo **{pc['prazo']}** ({pc['fundamento']})", f"- {pc['nota']}", ""]
        for it in r["intervalos"]:
            if "prescreve_em_pena_concreta" in it:
                L.append(f"- {it['de_desc']} → {it['ate_desc']}: prescreve(ria) em {it['prescreve_em_pena_concreta']} → "
                         f"{'**PRESCRITO pela pena concreta**' if it['prescrito_pena_concreta'] else 'não prescrito'}")
    if r["avisos"]:
        L += ["", "## Avisos", ""] + [f"- {a}" for a in r["avisos"]]
    L += ["", "## Regras aplicadas", "",
          "- CP 109 (prazos pela pena máxima); CP 110 §1º (pena concreta após trânsito para a acusação; sem retroação anterior à denúncia — Lei 12.234/2010);",
          "- CP 111 (termo inicial: consumação; permanente: cessação); CP 115 (metade: < 21 no fato, > 70 na sentença); CP 117 (interrupções); CP 116 (suspensões);",
          "- JECrim: a transação/suspensão condicional suspendem (Lei 9.099 art. 89 §6º); ANPP em cumprimento suspende (CPP 28-A §10).",
          "- Multa isolada: 2 anos (CP 114 I); cumulada, segue a pena privativa (CP 114 II)."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pena-max", help="pena máxima em abstrato: 3a, 2a6m, 6m")
    ap.add_argument("--dispositivo", help="fonte:artigo para ler a pena do dataset (cp:155, lei9605:38)")
    ap.add_argument("--pena-concreta", help="pena aplicada na sentença (para CP 110 §1º)")
    ap.add_argument("--fato", help="data do fato / cessação da permanência (AAAA-MM-DD)")
    ap.add_argument("--nascimento", help="nascimento do acusado (CP 115)")
    ap.add_argument("--data-sentenca", help="data da sentença (CP 115, > 70 anos)")
    ap.add_argument("--atos", help="atos.jsonl para ler marcos (recebimento, pronúncia, sentença, acórdão)")
    ap.add_argument("--marcos-json", help="marcos.json do cronologia_atos.py (padrão: <extracted>/../distill/marcos.json se existir)")
    ap.add_argument("--marco", nargs=2, action="append", metavar=("DATA", "DESCRICAO"), default=[])
    ap.add_argument("--ignorar", action="append", default=[], metavar="PALAVRA",
                    help="descarta marcos cuja descrição contém a palavra (ex.: --ignorar recebimento, quando a decisão de recebimento foi anulada)")
    ap.add_argument("--suspensao", nargs=3, action="append", metavar=("INI", "FIM", "MOTIVO"), default=[])
    ap.add_argument("--hoje")
    ap.add_argument("--cnj")
    ap.add_argument("--saida", help=".md (padrão: <extracted>/../distill/prescricao.md quando --atos)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.dispositivo:
        fonte, art = a.dispositivo.split(":", 1)
        meses, trecho = pena_do_dispositivo(fonte, art)
        if meses is None:
            print(f"ERRO: {trecho}", file=sys.stderr)
            return 2
        pena_max, origem = meses, f"{fonte} art. {art}: “{trecho}”"
    elif a.pena_max:
        pena_max, origem = parse_pena(a.pena_max), "informada na linha de comando"
    else:
        ap.error("informe --pena-max ou --dispositivo")
    hoje = date.fromisoformat(a.hoje) if a.hoje else date.today()
    fato = date.fromisoformat(a.fato) if a.fato else None
    marcos = marcos_dos_atos(a.atos) if a.atos else []
    avisos_extra: list[str] = []
    mj = a.marcos_json or (str(Path(a.atos).parent.parent / "distill" / "marcos.json") if a.atos else None)
    if mj and Path(mj).is_file():
        m2, avisos_extra = marcos_do_json(mj)
        marcos += m2
    marcos += [(date.fromisoformat(d), desc, "linha de comando") for d, desc in a.marco]
    # dedup: mesmo dia + mesmo tipo de marco (o texto da fonte varia entre atos.jsonl e marcos.json)
    vistos, unicos = set(), []
    for d, desc, f in marcos:
        chave = (d, desc.split("(")[0].strip().lower()[:24])
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append((d, desc, f))
    marcos = unicos
    if a.ignorar:
        antes = len(marcos)
        marcos = [m for m in marcos if not any(p.lower() in m[1].lower() for p in a.ignorar)]
        avisos_extra.append(f"marcos ignorados por --ignorar {a.ignorar}: {antes - len(marcos)} (cenário em que o ato interruptivo é nulo)")
    susp = [(date.fromisoformat(i), date.fromisoformat(f), m) for i, f, m in a.suspensao]
    r = calcular(pena_max, fato, marcos, hoje, date.fromisoformat(a.nascimento) if a.nascimento else None,
                 date.fromisoformat(a.data_sentenca) if a.data_sentenca else None,
                 parse_pena(a.pena_concreta) if a.pena_concreta else None, susp)
    r["avisos"] = avisos_extra + r["avisos"]
    cnj = a.cnj
    if not cnj and a.atos:
        try:
            cnj = json.loads(io.open(a.atos, encoding="utf-8").readline()).get("cnj")
        except Exception:
            pass
    if a.json:
        print(json.dumps(r | {"cnj": cnj, "origem_pena": origem}, ensure_ascii=False, indent=1))
        return 0
    texto = md(r, cnj, hoje, origem)
    if a.saida or a.atos:
        saida = Path(a.saida) if a.saida else Path(a.atos).parent.parent / "distill" / "prescricao.md"
        saida.parent.mkdir(parents=True, exist_ok=True)
        io.open(saida, "w", encoding="utf-8", newline="\n").write(texto)
        print(f"-> {saida}")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
