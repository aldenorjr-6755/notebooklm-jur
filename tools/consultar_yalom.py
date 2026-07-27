#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_yalom.py — Q&A ao vivo no notebook NotebookLM
"Irvin Yalom — Psicoterapia Existencial" (id f5509d65-2531-4922-8d7c-2b374a6f79ae),
~255 fontes sobre Irvin Yalom: biografia e trajetória, os quatro dados últimos da
existência (morte, liberdade/responsabilidade, isolamento existencial, falta de sentido)
e as defesas contra a angústia deles decorrente, psicoterapia de grupo (os 11 fatores
terapêuticos de "The Theory and Practice of Group Psychotherapy", com a coesão grupal
como equivalente grupal da relação terapêutica), aqui-e-agora e o grupo/sessão como
microcosmo social (imersão + iluminação processual), autorrevelação do terapeuta contra
o modelo da "tela em branco" e o terapeuta como companheiro de viagem, os romances e
livros de ensino (Love's Executioner, Momma and the Meaning of Life, Creatures of a Day,
When Nietzsche Wept, The Schopenhauer Cure, The Spinoza Problem) e a pesquisa empírica
(Q-sort, Therapeutic Factors Inventory, meta-análises sobre angústia existencial).

Não há corpus local espelhado (fontes são páginas web/PDFs externos) — a consulta
é feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado nas fontes
do notebook e cita a origem.

Uso:
    python consultar_yalom.py "quais são os 11 fatores terapêuticos de grupo"
    python consultar_yalom.py "limites da autorrevelação do terapeuta em Yalom" --json
    python consultar_yalom.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "f5509d65-2531-4922-8d7c-2b374a6f79ae"

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
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre Yalom e a psicoterapia existencial")
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
