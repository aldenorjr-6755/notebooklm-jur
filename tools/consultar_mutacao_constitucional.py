#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_mutacao_constitucional.py — Q&A ao vivo no notebook NotebookLM
"Mutacao Constitucional e Interpretacao" (id 6295ec8e-1a3f-49d7-996b-4215a00b3894),
211 fontes sobre mutacao constitucional (conceito, limites, mutacao inconstitucional),
interpretacao conforme a Constituicao, declaracao parcial de nulidade sem reducao de
texto, art. 52 X/abstrativizacao do controle difuso (Rcl 4335, ADIs 3406/3470),
ADI 4277/ADPF 132, hermeneutica constitucional e ativismo judicial.
Dominios: stf.jus.br, stj.jus.br, conjur.com.br (incl. Senso Incomum/Direitos
Fundamentais), migalhas.com.br, dizerodireito.com.br, editoras (JusPodivm, GEN,
Forum, RT) e periodicos (RIL/Senado, SciELO, FGV, USP).

Nao ha corpus local espelhado — a consulta e feita SEMPRE ao vivo via
`notebooklm ask`, que responde ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_mutacao_constitucional.py "limites da mutacao constitucional"
    python consultar_mutacao_constitucional.py "interpretacao conforme x nulidade parcial" --json
    python consultar_mutacao_constitucional.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "6295ec8e-1a3f-49d7-996b-4215a00b3894"

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
    print(result.stdout.strip())
    if result.returncode != 0:
        print("\n[ERRO] notebooklm ask retornou erro:", result.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
