#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_wigmore.py — Q&A ao vivo no notebook NotebookLM
"Método Analítico de Wigmore (Wigmorean Charting)" (id 6d255d90-1475-4a59-a582-ba0e13c98456),
~120+ fontes sobre o método de Wigmore (Wigmore charts/Wigmorean analysis), a tradição
neo-wigmoreana (Anderson, Twining, Schum — "Analysis of Evidence"), Peter Tillers
("Charting New Territory in Judicial Proof: Beyond Wigmore", marshalling evidence,
inference networks), David Schum (Evidential Foundations of Probabilistic Reasoning,
ciência da evidência, credibilidade/relevância/força probatória), comparações com
redes bayesianas e Chain Event Graphs, esquemas de argumentação (Prakken, Verheij,
Bex/Walton), teoria híbrida histórias x argumentos (Floris Bex), aplicações forenses
e em tribunais internacionais (ICTY/ICC), ensino jurídico e ferramentas computacionais
(MarshalPlan, Araucaria, Wigmore diagrams como information-flow network).

Não há corpus local espelhado (fontes são páginas web/PDFs/artigos acadêmicos
externos) — a consulta é feita SEMPRE ao vivo via `notebooklm ask`, que responde
ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_wigmore.py "estrutura do Wigmore chart: probandum, key list, trifles"
    python consultar_wigmore.py "diferenças entre Wigmore charts e redes bayesianas" --json
    python consultar_wigmore.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "6d255d90-1475-4a59-a582-ba0e13c98456"

# Invocar o MODULO, nao o atalho `notebooklm`: no Windows o shim de ~/.local/bin e um
# script de shell POSIX (+ um .cmd) e o subprocess esbarra na politica de Controle de
# Aplicativo (WinError 4551). `python -m notebooklm` roda a mesma CLI sem passar pelo shim.
CLI = [sys.executable, "-m", "notebooklm"]
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre o tema")
    ap.add_argument("--json", action="store_true", help="saida em JSON bruto da CLI notebooklm")
    ap.add_argument("--fontes", action="store_true", help="lista as fontes do notebook em vez de perguntar")
    args = ap.parse_args()

    if args.fontes:
        cmd = CLI + ["source", "list", "--notebook", NOTEBOOK_ID]
        if args.json:
            cmd.append("--json")
        subprocess.run(cmd)
        return

    cmd = CLI + ["ask", args.pergunta, "-n", NOTEBOOK_ID]
    if args.json:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = result.stdout.strip()
    print(out)
    if result.returncode != 0:
        print("\n[ERRO] notebooklm ask retornou erro:", result.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
