#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_falsificacionismo.py — Q&A ao vivo no notebook NotebookLM
"Teoria da Corroboracao Falsificacionista" (id 92efec4d-de9b-48e9-bf3b-d8beba52d0e1),
~113 fontes sobre falsificacionismo de Popper, corroboracao de hipoteses, criticas
(Kuhn/Lakatos/Feyerabend), verossimilhanca/truthlikeness, epistemologia juridica da
prova (Ferrer Beltran, Gascon Abellan, Taruffo, Badaro), foundherentismo de Susan Haack,
standard Daubert/forensic science e abducao de Peirce aplicada ao direito.

Nao ha corpus local espelhado (fontes sao paginas web/PDFs externos) — a consulta
e feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado nas fontes do
notebook e cita a origem.

Uso:
    python consultar_falsificacionismo.py "criterio de demarcacao de Popper"
    python consultar_falsificacionismo.py "corroboracao x verificacionismo" --json
    python consultar_falsificacionismo.py "standard Daubert" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "92efec4d-de9b-48e9-bf3b-d8beba52d0e1"

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
