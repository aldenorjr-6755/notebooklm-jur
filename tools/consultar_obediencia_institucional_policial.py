#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_obediencia_institucional_policial.py — Q&A ao vivo no notebook NotebookLM
"Obediencia Institucional e Conformidade Policial na Prova Penal"
(id bc44b655-5b7c-436e-8b06-fecef4943b35).

Milgram (obediencia a autoridade) e Asch (conformidade de grupo) aplicados a
hierarquia/corporacao policial; groupthink (Janis); "blue wall of silence"
(Skolnick, Reiner, Westmarland, Comissoes Christopher/Knapp); "testilying"
(perjurio policial sistemico, Slobogin); contaminacao de memoria entre
co-testemunhas policiais (memory conformity aplicada a relatorios conjuntos);
parametro CNJ/FBSP 2022 e doutrina brasileira sobre credibilidade do
testemunho policial.

Nao ha corpus local espelhado (fontes sao paginas web/PDFs/artigos academicos
externos) — a consulta e feita SEMPRE ao vivo via `notebooklm ask`, que responde
ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_obediencia_institucional_policial.py "o que e testilying"
    python consultar_obediencia_institucional_policial.py "blue wall of silence e Comissao Christopher" --json
    python consultar_obediencia_institucional_policial.py "" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "bc44b655-5b7c-436e-8b06-fecef4943b35"

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
