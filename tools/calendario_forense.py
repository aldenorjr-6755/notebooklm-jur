# -*- coding: utf-8 -*-
"""
calendario_forense.py — feriados e dias sem expediente, partilhado por prazo_cpp.py e
prescricao_cp.py. Reaproveita a logica de ~/.claude/skills/contagem-prazos-cpc/scripts/prazo_cpc.py
(feriados nacionais fixos + moveis por Pascoa) e acrescenta o calendario LOCAL declarado.

Tudo que e' local (TJMA, comarca, ponto facultativo) entra por `LOCAIS` ou por arquivo JSON
(--feriados-locais caminho.json, formato {"2026-08-10": "Ponto facultativo — Dia do Advogado"}).
A regra e' a mesma do script do CPC: o dia pulado sai impresso com o motivo, para que o erro
apareca em vez de sumir.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


def pascoa(ano: int) -> date:
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


FIXOS = {
    (1, 1): "Confraternizacao Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independencia",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamacao da Republica",
    (11, 20): "Consciencia Negra (Lei 14.759/2023)",
    (12, 25): "Natal",
}

# Calendario LOCAL conhecido, com ESCOPO: "MA" (estadual) e "TJMA" (ato do tribunal, todas as
# comarcas) entram sempre; escopo de municipio so entra quando --comarca casa com ele. Feriado
# municipal de Sao Luis nao vale para Itinga do Maranhao. Fonte: memoria do ambiente; ampliar
# conforme portarias do TJMA. O que nao estiver aqui NAO e' considerado.
# (data, escopo, motivo)
LOCAIS: list[tuple[date, str, str]] = [
    (date(2026, 8, 10), "TJMA", "TJMA: ponto facultativo (segunda entre fim de semana e Dia do Advogado)"),
    (date(2026, 8, 11), "TJMA", "TJMA: Dia do Advogado, so plantao"),
    (date(2024, 7, 28), "MA", "MA: Adesao do Maranhao a Independencia (feriado estadual)"),
    (date(2025, 7, 28), "MA", "MA: Adesao do Maranhao a Independencia (feriado estadual)"),
    (date(2026, 7, 28), "MA", "MA: Adesao do Maranhao a Independencia (feriado estadual)"),
    (date(2024, 12, 8), "MA", "MA: Nossa Senhora da Conceicao (feriado estadual)"),
    (date(2025, 12, 8), "MA", "MA: Nossa Senhora da Conceicao (feriado estadual)"),
    (date(2026, 12, 8), "MA", "MA: Nossa Senhora da Conceicao (feriado estadual)"),
    (date(2025, 9, 8), "Sao Luis", "Sao Luis: aniversario da cidade (feriado municipal)"),
    (date(2026, 9, 8), "Sao Luis", "Sao Luis: aniversario da cidade (feriado municipal)"),
]
ESCOPOS_GERAIS = {"MA", "TJMA"}


def _norm(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower().strip()


def feriados(ano: int, locais: dict[date, str] | None = None) -> dict[date, str]:
    out = {date(ano, m, d): nome for (m, d), nome in FIXOS.items()}
    p = pascoa(ano)
    out[p - timedelta(days=48)] = "Carnaval (segunda)"
    out[p - timedelta(days=47)] = "Carnaval (terca)"
    out[p - timedelta(days=46)] = "Quarta-feira de Cinzas (expediente so a partir das 14h; conte como nao util)"
    out[p - timedelta(days=2)] = "Sexta-feira Santa"
    out[p + timedelta(days=60)] = "Corpus Christi"
    if locais is None:
        locais = carregar_locais(None, None)
    for d, nome in locais.items():
        if d.year == ano:
            out[d] = nome
    return out


def carregar_locais(caminho: str | None, comarca: str | None = None) -> dict[date, str]:
    """Feriados locais aplicaveis: estaduais + do tribunal sempre; municipais so da comarca dada.
    `caminho` e' um JSON {"AAAA-MM-DD": "motivo"} que entra por cima, sem escopo (vale para o caso)."""
    alvo = _norm(comarca) if comarca else None
    loc: dict[date, str] = {}
    for d, escopo, motivo in LOCAIS:
        if escopo in ESCOPOS_GERAIS or (alvo and _norm(escopo) == alvo):
            loc[d] = motivo
    if caminho:
        raw = json.loads(Path(caminho).read_text(encoding="utf-8"))
        for k, v in raw.items():
            loc[date.fromisoformat(k)] = v
    return loc


def em_recesso(d: date) -> bool:
    """20/12 a 20/01 (CPC 220). No processo penal NAO se aplica por padrao — ver prazo_cpp.py."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)


def motivo_nao_util(d: date, locais: dict[date, str] | None = None, recesso: bool = False) -> str | None:
    if d.weekday() == 5:
        return "sabado"
    if d.weekday() == 6:
        return "domingo"
    f = feriados(d.year, locais).get(d)
    if f:
        return f"feriado — {f}"
    if recesso and em_recesso(d):
        return "recesso forense (aplicado por opcao)"
    return None


def proximo_util(d: date, locais=None, recesso: bool = False) -> date:
    while motivo_nao_util(d, locais, recesso):
        d += timedelta(days=1)
    return d
