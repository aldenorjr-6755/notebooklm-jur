#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_obra_tematica.py — índice tema -> página de obras STF organizadas por sumário temático
(Coletânea Temática de Jurisprudência / Coleção Supremo Contemporâneo). Localiza a PÁGINA do tema;
o teor só lendo o PDF na página indicada (Read com pages:) — não citar de memória.
Uso: python consultar_obra_tematica.py --fonte ctj_penal "insignificância" [--json] [--limite N]"""
import sys, os, json, re, argparse, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
BASE = os.path.dirname(os.path.abspath(__file__))
REG = {
    "ctj_penal": "ctj_penal_sumario.json",
    "ctj_eleitoral": "ctj_eleitoral_sumario.json",
    "ctj_dh": "ctj_dh_sumario.json",
    "ctj_controle_constitucionalidade": "ctj_controle_constitucionalidade_sumario.json",
    "ctj_advocacia_oab": "ctj_advocacia_oab_sumario.json",
    "sc_liberdade_expressao": "sc_liberdade_expressao_sumario.json",
    "sc_direito_ambiental": "sc_direito_ambiental_sumario.json",
}


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


ap = argparse.ArgumentParser()
ap.add_argument("--fonte", required=True, choices=list(REG))
ap.add_argument("consulta")
ap.add_argument("--json", action="store_true")
ap.add_argument("--limite", type=int, default=15)
a = ap.parse_args()
base = json.load(open(os.path.join(BASE, REG[a.fonte]), encoding="utf-8"))
itens = base["sumario"]
q = norm(a.consulta)
res = [r for r in itens if q in norm(r["tema"])][: a.limite]

if a.json:
    print(json.dumps({"titulo": base["titulo"], "serie": base["serie"], "resultados": len(res), "sumario": res},
                      ensure_ascii=False, indent=1))
    sys.exit()
print(base["titulo"], f"({base['serie']})\n")
if not res:
    print("Nenhum tópico encontrado.")
    sys.exit()
for r in res:
    print(("  " * r["nivel"]) + f"{r['tema']} — p. {r['pagina']}")
print(f"\n⚠️ Índice de SUMÁRIO (tema→página); abra o PDF original na página indicada para o teor. Fonte: {base['fonte']}")
