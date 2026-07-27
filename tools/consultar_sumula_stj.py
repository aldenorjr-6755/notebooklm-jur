#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_sumula_stj.py — consulta as Súmulas do STJ (fonte canônica offline).

Fonte: STJ — "Inteiro Teor das Súmulas" (Secretaria de Jurisprudência, 16/11/2022),
extraído para tools/sumulas_stj.json por extrair_sumulas_stj.py. O inteiro teor
(precedentes originários) permanece em ~/.notebooklm/biblioteca/{pdf,md}/Sumulas_STJ_Inteiro_Teor_2022.*

Uso:
    python consultar_sumula_stj.py "reexame de prova"      # busca por palavra no enunciado/ramo
    python consultar_sumula_stj.py --numero 7              # súmula específica
    python consultar_sumula_stj.py "consumidor" --json
    python consultar_sumula_stj.py "banc" --so-vigentes    # exclui canceladas
    python consultar_sumula_stj.py --canceladas            # lista as canceladas

Opções:
    --numero N         súmula exata (número)
    --json             saída estruturada (JSON)
    --so-vigentes      oculta as canceladas
    --canceladas       lista só as canceladas
    --limite N         máximo de resultados (padrão 30)
"""
import sys, os, json, re, argparse, unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sumulas_stj.json")


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def carregar():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("termo", nargs="?", default="")
    ap.add_argument("--numero", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--so-vigentes", action="store_true")
    ap.add_argument("--canceladas", action="store_true")
    ap.add_argument("--limite", type=int, default=30)
    a = ap.parse_args()

    base = carregar()
    sums = base["sumulas"]

    if a.numero is not None:
        sums = [s for s in sums if s["numero"] == a.numero]
    if a.canceladas:
        sums = [s for s in sums if s["situacao"] == "CANCELADA"]
    elif a.so_vigentes:
        sums = [s for s in sums if s["situacao"] != "CANCELADA"]
    if a.termo:
        q = norm(a.termo)
        sums = [s for s in sums if q in norm(s["enunciado"]) or q in norm(s["ramo"])]

    sums = sums[: a.limite]

    if a.json:
        print(json.dumps({"fonte": base["fonte"], "total_base": base["total"],
                          "resultados": len(sums), "sumulas": sums},
                         ensure_ascii=False, indent=1))
        return

    if not sums:
        print("Nenhuma súmula encontrada. Fonte:", base["fonte"])
        return
    print(f"Fonte: {base['fonte']}  ·  {len(sums)} resultado(s)\n")
    for s in sums:
        flag = "  ⛔ CANCELADA" if s["situacao"] == "CANCELADA" else ""
        print(f"Súmula {s['numero']} STJ{flag}  [{s['ramo']}]")
        print(f"  {s['enunciado']}")
        meta = " · ".join(x for x in (s.get("orgao"), s.get("data")) if x)
        if meta:
            print(f"  ({meta})")
        print()


if __name__ == "__main__":
    main()
