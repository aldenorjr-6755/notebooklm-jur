#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_argumentacao_defeasivel.py — Q&A ao vivo no notebook NotebookLM
"Teoria da Argumentacao Juridica e Esquemas Defeasiveis (Walton Prakken Sartor)
na Prova Penal" (id aefebf29-2f9c-4aa4-bc02-b7109f7a8f44).

Esquemas argumentativos de Douglas Walton (padroes de raciocinio presuntivo/
defeasivel, cada um com um conjunto de PERGUNTAS CRITICAS que testam a
inferencia — argumento de opiniao de especialista, de testemunho, de sinal,
de correlacao para causa, de posicao para saber, de analogia, de precedente,
de consequencias) e o aparato formal de Henry Prakken e Giovanni Sartor
(ASPIC+, rebutting x undercutting defeaters, onus da prova dialetico).

Nao ha corpus local espelhado (fontes sao paginas web/PDFs externos) — a
consulta e feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado
nas fontes do notebook e cita a origem.

Uso:
    python consultar_argumentacao_defeasivel.py "perguntas criticas do argumento de opiniao de especialista"
    python consultar_argumentacao_defeasivel.py "rebutting x undercutting defeater" --json
    python consultar_argumentacao_defeasivel.py "" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "aefebf29-2f9c-4aa4-bc02-b7109f7a8f44"

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
