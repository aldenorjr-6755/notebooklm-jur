#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validador_processual.py — validador ESTRUTURAL da minuta (espec §4): pedidos x fundamentacao,
nulidade x pedido, rito da peca, tempestividade, prequestionamento.

Regras (todas heuristicas de texto; o relatorio diz o que conferiu e como):
  1. Toda NULIDADE alegada na fundamentacao precisa de PEDIDO correspondente (anulacao,
     desentranhamento, reconhecimento da nulidade).
  2. Todo PEDIDO precisa de gancho na fundamentacao (palavras-chave do pedido aparecem nas
     secoes anteriores). Pedido "orfao" = alerta.
  3. Rito por --peca:
       resposta-acusacao  rol de testemunhas <= 8 (CPP 401) ou <= 5 no JECrim (Lei 9.099 art. 34);
                          nao pedir condenacao/absolvicao de merito como principal (cabe absolvicao sumaria 397)
       memoriais          fundamentacao deve citar prova dos autos (ancora [ID|p.] ou fls.)
       apelacao           interposicao + razoes; pedido de reforma/anulacao; tempestividade (5 dias, CPP 593)
       hc                 paciente + autoridade coatora + pedido liminar/ordem; SEM pedido de honorarios
       rese               materia do rol do CPP 581 mencionada; pedido de retratacao (CPP 589)
       resp / re          secao de PREQUESTIONAMENTO; cada dispositivo violado (art. N) precisa aparecer
                          tambem no prequestionamento; RE precisa de secao de REPERCUSSAO GERAL
       execucao           numero do PEC/atestado de pena citado
     Em qualquer peca criminal: pedido de honorarios advocaticios = alerta (nao ha sucumbencia).
  4. Tempestividade: --intimacao AAAA-MM-DD [--dias N] (padrao: prazo da peca) -> prazo_cpp.calcular;
     compara com --hoje.
  5. Ancoras: contagem de afirmacoes de fato sem ancora [ID | p.]/fls. nas secoes de fatos.

Uso:
  python validador_processual.py minuta.md --peca resposta-acusacao [--rito jecrim] [--intimacao 2026-09-01] [--hoje ...]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

PRAZOS_PECA = {"resposta-acusacao": (10, "CPP 396"), "memoriais": (5, "CPP 403 §3º"), "apelacao": (5, "CPP 593"),
               "razoes-apelacao": (8, "CPP 600"), "rese": (5, "CPP 586"), "embargos": (2, "CPP 382/619"),
               "resp": (15, "CPC 1.003 §5º c/c CPP 798"), "re": (15, "CPC 1.003 §5º c/c CPP 798"), "hc": (0, "sem prazo"),
               "agravo-execucao": (5, "LEP 197; Súm. 700 STF"), "execucao": (0, "—"), "parecer": (0, "—"), "outra": (0, "—")}
PRAZOS_JECRIM = {"apelacao": (10, "Lei 9.099 art. 82 §1º"), "embargos": (5, "Lei 9.099 art. 83 §1º")}


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"\s+", " ", s)


RE_TITULO = re.compile(r"^\s*(?:#{1,4}\s*|\d+(?:\.\d+)*\s*[-.–)]?\s*|[IVX]+\s*[-.–)]\s*)?([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ\s\-–,:/()0-9ºª.]{4,90})\s*$")


def secoes(texto: str) -> list[tuple[str, str]]:
    """Divide por titulos em maiusculas / markdown. -> [(titulo, corpo)]"""
    out, tit, buf = [], "PREAMBULO", []
    for ln in texto.split("\n"):
        m = RE_TITULO.match(ln)
        if m and len(ln.strip()) < 100 and not re.search(r"[a-záéíóú]{3}", ln.replace("–", "")):
            out.append((tit, "\n".join(buf)))
            tit, buf = m.group(1).strip(), []
        else:
            buf.append(ln)
    out.append((tit, "\n".join(buf)))
    return out


def eh_pedidos(tit: str) -> bool:
    t = norm(tit)
    return any(k in t for k in ("pedido", "requer", "requerimento", "conclusao", "do pedido"))


def eh_fatos(tit: str) -> bool:
    t = norm(tit)
    return any(k in t for k in ("fato", "sintese", "breve relato", "relatorio", "historico"))


def itens_pedidos(corpo: str) -> list[str]:
    itens = []
    for ln in corpo.split("\n"):
        s = ln.strip()
        if re.match(r"^(?:[a-z]\)|[ivx]+\)|\d+[.)]|[-•*]|\(?[a-z0-9]\))\s+", s, re.I) or re.match(r"^(?:requer|pede|pugna|seja|a\s+(?:absolvi|rejei|anula|conce|decreta|revoga|expedi|intima|oitiva|produ|realiza))", s, re.I):
            if len(s) > 12:
                itens.append(s)
    if not itens:
        for frase in re.split(r"(?<=[.;])\s+", corpo):
            if re.search(r"\b(requer|pugna|pede|seja\s+\w+)", frase, re.I) and len(frase) > 20:
                itens.append(frase.strip())
    return itens


PALAVRAS_VAZIAS = set("de da do das dos a o as os e em no na nos nas um uma por para com sem que se ao à aos às ou sob sobre como bem assim ainda seja sejam ser foi sua seu suas seus este esta esse essa isto isso ante diante nos termos art arts inciso inc caput par termos requer pede pugna seja deferido deferida determinada determinado".split())


def chaves(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{4,}", norm(s)) if w not in PALAVRAS_VAZIAS}


def validar(texto: str, peca: str, rito: str, intimacao: str | None, dias: int | None, hoje: date) -> dict:
    alertas: list[dict] = []
    infos: list[str] = []
    secs = secoes(texto)
    # titulo entra na fundamentacao: "DA INEPCIA", "DA ATIPICIDADE" carregam a palavra-chave do pedido
    fund = "\n".join(t + "\n" + c for t, c in secs if not eh_pedidos(t))
    ped_corpo = "\n".join(c for t, c in secs if eh_pedidos(t))
    pedidos = itens_pedidos(ped_corpo) if ped_corpo else []
    if not ped_corpo:
        alertas.append({"regra": "estrutura", "grau": "alto", "msg": "não achei seção de PEDIDOS (título com 'pedidos'/'requer')"})
    infos.append(f"seções: {len(secs)} · pedidos identificados: {len(pedidos)}")

    # 1. nulidade alegada -> pedido correspondente
    nul = re.findall(r"\b(nulidade|nul[oa]s?\b|anula[çc][ãa]o|desentranhamento|il[íi]cit[ao])", fund, re.I)
    if nul and not re.search(r"\b(nulidade|anula|desentranh|il[íi]cit|reconhec\w+\s+a\s+nulidade)", ped_corpo, re.I):
        alertas.append({"regra": "nulidade→pedido", "grau": "alto", "msg": f"a fundamentação fala em nulidade/ilicitude ({len(nul)} menções) mas nenhum pedido pede o reconhecimento/anulação/desentranhamento"})

    # 2. pedido -> gancho na fundamentacao
    kf = chaves(fund)
    for p in pedidos:
        kp = chaves(p)
        if not kp:
            continue
        cobertura = len(kp & kf) / len(kp)
        if cobertura < 0.34:
            alertas.append({"regra": "pedido→fundamentação", "grau": "medio", "msg": f"pedido sem gancho claro na fundamentação (só {cobertura:.0%} das palavras-chave aparecem antes): “{p[:110]}”"})

    # 3. rito
    tn = norm(texto)
    if re.search(r"honorari", tn) and re.search(r"(condena|fixa|arbitr)\w*\s+.{0,40}honorari", tn):
        alertas.append({"regra": "rito", "grau": "alto", "msg": "pedido de honorários advocatícios em peça criminal: não há sucumbência (Súm. 512 STF por analogia; CPP não a prevê)"})
    if peca == "resposta-acusacao":
        rol = re.search(r"rol\s+de\s+testemunhas(.{0,2500})", texto, re.I | re.S)
        if rol:
            n = len(re.findall(r"^\s*(?:\d+[.)]|[-•*])\s*[A-ZÁÉÍÓÚ]", rol.group(1), re.M))
            lim = 5 if rito == "jecrim" else 8
            if n > lim:
                alertas.append({"regra": "rito", "grau": "alto", "msg": f"rol com {n} testemunhas; limite {lim} ({'Lei 9.099 art. 34' if rito == 'jecrim' else 'CPP 401'})"})
            infos.append(f"rol de testemunhas: {n} nome(s) contado(s)")
        else:
            alertas.append({"regra": "rito", "grau": "baixo", "msg": "não achei 'rol de testemunhas' (CPP 396-A: é o momento de arrolar; silêncio = preclusão)"})
        if not re.search(r"absolvi[çc][ãa]o\s+sum[áa]ria|art\.?\s*397", tn):
            infos.append("sem pedido de absolvição sumária (CPP 397): opcional, mas é o pedido próprio desta fase")
    if peca == "memoriais" and not re.search(r"\[id\s*\d+|\bfls?\.\s*\d|\bid\.?\s*\d{6,}", tn):
        alertas.append({"regra": "rito", "grau": "alto", "msg": "memoriais sem nenhuma referência a folha/ID dos autos: a prova precisa ser apontada"})
    if peca in ("apelacao", "razoes-apelacao"):
        if not re.search(r"interp[oõ]e|interposi[çc][ãa]o", tn):
            alertas.append({"regra": "rito", "grau": "medio", "msg": "não achei a petição de interposição (apelação = interposição ao juízo a quo + razões)"})
        if not re.search(r"reform|anul|absolv|redu[çc]|provimento", tn):
            alertas.append({"regra": "rito", "grau": "alto", "msg": "pedido de provimento sem indicar o resultado (reforma/anulação/absolvição/redução)"})
    if peca == "hc":
        if not re.search(r"paciente", tn):
            alertas.append({"regra": "rito", "grau": "alto", "msg": "HC sem indicação do PACIENTE"})
        if not re.search(r"autoridade\s+coatora|coator", tn):
            alertas.append({"regra": "rito", "grau": "alto", "msg": "HC sem indicação da AUTORIDADE COATORA"})
        if not re.search(r"liminar|ordem", tn):
            alertas.append({"regra": "rito", "grau": "medio", "msg": "HC sem pedido de liminar/ordem"})
    if peca == "rese":
        if not re.search(r"art\.?\s*581", tn):
            alertas.append({"regra": "rito", "grau": "alto", "msg": "RESE sem indicar o inciso do CPP 581 (rol taxativo)"})
        if not re.search(r"retrata", tn):
            alertas.append({"regra": "rito", "grau": "medio", "msg": "RESE sem pedido de retratação (CPP 589)"})
    if peca in ("resp", "re"):
        preq = [c for t, c in secs if "prequestion" in norm(t)]
        if not preq:
            alertas.append({"regra": "rito", "grau": "alto", "msg": "sem seção de PREQUESTIONAMENTO (Súm. 211 STJ / 282 e 356 STF)"})
        else:
            arts = set(re.findall(r"art\.?\s*(\d{1,4}(?:-[A-Z])?)", fund, re.I))
            faltam = [x for x in arts if not re.search(rf"art\.?\s*{re.escape(x)}\b", preq[0], re.I)]
            if faltam:
                alertas.append({"regra": "rito", "grau": "medio", "msg": f"dispositivos citados na fundamentação e ausentes do prequestionamento: art. {', '.join(sorted(faltam)[:12])}"})
        if peca == "re" and not any("repercuss" in norm(t) for t, c in secs):
            alertas.append({"regra": "rito", "grau": "alto", "msg": "RE sem tópico autônomo de REPERCUSSÃO GERAL (CPC 1.035 §2º)"})
        if re.search(r"reexame|revalora|conjunto\s+probat", tn) and not re.search(r"s[úu]mula\s*(7|279)", tn):
            infos.append("a peça fala em prova/reexame: antecipar a Súm. 7 STJ / 279 STF")
    if peca in ("agravo-execucao", "execucao") and not re.search(r"pec\b|execu[çc][ãa]o\s+penal\s+n|atestado\s+de\s+pena", tn):
        alertas.append({"regra": "rito", "grau": "medio", "msg": "sem número do PEC/atestado de pena"})

    # 4. tempestividade
    temp = None
    if intimacao:
        import prazo_cpp
        import calendario_forense as CF
        d = dias or (PRAZOS_JECRIM.get(peca, PRAZOS_PECA.get(peca, (0, "")))[0] if rito == "jecrim" else PRAZOS_PECA.get(peca, (0, ""))[0])
        fund_p = (PRAZOS_JECRIM.get(peca) if rito == "jecrim" else None) or PRAZOS_PECA.get(peca, (0, "—"))
        if d:
            c = prazo_cpp.calcular(date.fromisoformat(intimacao), d, CF.carregar_locais(None, None), False)
            venc = date.fromisoformat(c["vencimento"])
            temp = {"intimacao": intimacao, "dias": d, "fundamento": fund_p[1], "vencimento": c["vencimento"], "hoje": hoje.isoformat(),
                    "tempestivo_se_protocolada_hoje": hoje <= venc}
            if hoje > venc:
                alertas.append({"regra": "tempestividade", "grau": "alto", "msg": f"prazo de {d} dias ({fund_p[1]}) contado da intimação em {intimacao} venceu em {c['vencimento']}"})
            else:
                infos.append(f"tempestividade: vence {c['vencimento']} ({(venc - hoje).days} dia(s) de folga)")

    # 5. ancoras nos fatos
    fatos = "\n".join(c for t, c in secs if eh_fatos(t))
    if fatos:
        frases = [f for f in re.split(r"(?<=[.!?])\s+", fatos) if len(f) > 60]
        sem = [f for f in frases if not re.search(r"\[id\s*\d|\bfls?\.\s*\d|\bid\.?\s*\d{6,}|\bp\.\s*\d|num\.\s*\d", f, re.I)]
        infos.append(f"fatos: {len(frases)} frase(s) longas, {len(sem)} sem âncora [ID | p.]/fls.")
        if frases and len(sem) / len(frases) > 0.5:
            alertas.append({"regra": "âncoras", "grau": "medio", "msg": f"{len(sem)} de {len(frases)} frases dos fatos sem âncora nos autos (Etapa A da espec exige âncora por frase)"})
    status = "APROVADO" if not [x for x in alertas if x["grau"] == "alto"] else f"ALERTA ({sum(1 for x in alertas if x['grau'] == 'alto')} alto)"
    return {"peca": peca, "rito": rito, "status": status, "alertas": alertas, "infos": infos, "tempestividade": temp, "pedidos": pedidos}


def relatorio(r: dict, minuta: str) -> str:
    L = [f"# Validação processual — {Path(minuta).name}", "", f"- peça: **{r['peca']}** · rito: {r['rito']} · status: **{r['status']}**", ""]
    if r["tempestividade"]:
        t = r["tempestividade"]
        L.append(f"- tempestividade: intimação {t['intimacao']} + {t['dias']} dias ({t['fundamento']}) → vence **{t['vencimento']}**; hoje {t['hoje']}: {'tempestiva' if t['tempestivo_se_protocolada_hoje'] else 'INTEMPESTIVA'}")
    L += ["", "## Alertas", ""] + ([f"- **[{a['grau']}] {a['regra']}** — {a['msg']}" for a in r["alertas"]] or ["(nenhum)"])
    L += ["", "## Conferências", ""] + [f"- {i}" for i in r["infos"]]
    L += ["", "## Pedidos identificados", ""] + ([f"- {p[:160]}" for p in r["pedidos"]] or ["(nenhum)"])
    L += ["", "> Heurísticas de texto: títulos em maiúsculas delimitam seções; pedidos são itens enumerados ou frases com 'requer/pugna'. Conferir o que o validador não viu."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("minuta")
    ap.add_argument("--peca", default="outra", choices=sorted(PRAZOS_PECA))
    ap.add_argument("--rito", default="ordinario", choices=["ordinario", "sumario", "jecrim"])
    ap.add_argument("--intimacao")
    ap.add_argument("--dias", type=int)
    ap.add_argument("--hoje")
    ap.add_argument("--saida-dir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    texto = io.open(a.minuta, encoding="utf-8").read()
    r = validar(texto, a.peca, a.rito, a.intimacao, a.dias, date.fromisoformat(a.hoje) if a.hoje else date.today())
    p = Path(a.minuta)
    dest = Path(a.saida_dir) if a.saida_dir else p.parent
    dest.mkdir(parents=True, exist_ok=True)
    io.open(dest / (p.stem + ".validacao-processual.md"), "w", encoding="utf-8", newline="\n").write(relatorio(r, a.minuta))
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else relatorio(r, a.minuta))
    return 0 if r["status"] == "APROVADO" else 1


if __name__ == "__main__":
    sys.exit(main())
