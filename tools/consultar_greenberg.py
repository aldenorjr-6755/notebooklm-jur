#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_greenberg.py — Q&A ao vivo no notebook NotebookLM
"Leslie Greenberg — Emotion-Focused Therapy (EFT)" (id 49a3a3ff-640f-49f9-a539-6152e49c0575),
~93 fontes sobre Leslie Greenberg e a Terapia Focada na Emoção: biografia e trajetória
(engenharia -> psicologia, Laura Rice e a análise de tarefas, Harvey Friedman/Gestalt,
Pascual-Leone/neo-piagetiano, Clínica de EFT na York University), teoria (visão
construtivista dialética, emoção como sinal adaptativo, esquemas emocionais e seus cinco
elementos, emoções primárias adaptativas e mal-adaptativas, secundárias reativas e
instrumentais), tarefas guiadas por marcadores (duas cadeiras para splits/autocrítica,
cadeira vazia para unfinished business, focalização experiencial), pesquisa empírica
(RCTs, comparação com TCC e ACP na depressão, ativação emocional + processamento
reflexivo como preditor de mudança, meta-análises de Elliott com Hedges' g ~1,23,
"mudar emoção com emoção"/reconsolidação da memória), EFT de casal (formulação original
com Sue Johnson e a bifurcação posterior dos modelos) e EFT para trauma.

Não há corpus local espelhado (fontes são páginas web/PDFs externos) — a consulta
é feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado nas fontes
do notebook e cita a origem.

Uso:
    python consultar_greenberg.py "diferença entre emoção primária mal-adaptativa e secundária reativa"
    python consultar_greenberg.py "quando usar cadeira vazia em vez de duas cadeiras" --json
    python consultar_greenberg.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "49a3a3ff-640f-49f9-a539-6152e49c0575"

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
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre Greenberg e a EFT")
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
