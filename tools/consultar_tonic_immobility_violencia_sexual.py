#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_tonic_immobility_violencia_sexual.py — Q&A ao vivo no notebook NotebookLM
"Resposta de Congelamento (Tonic Immobility) em Vitimas de Violencia Sexual na
Prova Penal" (id 29b37d18-e8bf-49e3-b246-c4a522f0ad49).

Neurobiologia da imobilidade tonica (Bracha - cascata de defesa; Marx et al.),
estudo empirico de referencia (Moller/Sondergaard/Helstrom 2017 - ~70% das
vitimas relatam imobilidade tonica significativa), mito da resistencia fisica
e rape myths (Burt, Estrich), cautela metodologica contra uso como "sindrome"
infalseavel, e a jurisprudencia brasileira sobre desnecessidade de resistencia
fisica para caracterizacao do estupro (CP 213).

Nao ha corpus local espelhado (fontes sao paginas web/PDFs/artigos academicos
externos) — a consulta e feita SEMPRE ao vivo via `notebooklm ask`, que responde
ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_tonic_immobility_violencia_sexual.py "o que e a cascata de defesa de Bracha"
    python consultar_tonic_immobility_violencia_sexual.py "estudo Moller Sondergaard Helstrom 2017" --json
    python consultar_tonic_immobility_violencia_sexual.py "" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "29b37d18-e8bf-49e3-b246-c4a522f0ad49"

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
    if args.json:
        print(out)
    else:
        print(out)
        if result.returncode != 0:
            print("\n[ERRO] notebooklm ask retornou erro:", result.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
