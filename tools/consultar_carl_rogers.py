#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_carl_rogers.py — Q&A ao vivo no notebook NotebookLM
"Carl Rogers & Person-Centered Approach" (id 8c715fc1-e83a-4a6a-8f07-9fac510385a8),
~128 fontes sobre Carl Rogers e o ecossistema humanista-experiencial: biografia,
teoria central da ACP (condições facilitadoras, tendência atualizante, campo
fenomenológico, self/self ideal, congruência/empatia/CPU, não-diretividade,
presença terapêutica), pesquisa empírica (meta-análises Elliott, projeto Wisconsin,
Wampold, APA Div. 32), extensões (Gendlin/Focusing/felt sense, Pré-Terapia/Prouty,
TFE/Greenberg, Profundidade Relacional/Mearns-Cooper, Terapia Pluralista/Cooper-McLeod,
Artes Expressivas/Natalie Rogers) e tradições adjacentes (psicologia humanista/Maslow,
psicologia existencial/May-Yalom, grupos de encontro, educação humanista).

Não há corpus local espelhado (fontes são páginas web/PDFs externos) — a consulta
é feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado nas fontes
do notebook e cita a origem.

Uso:
    python consultar_carl_rogers.py "o que Rogers entende por tendência atualizante"
    python consultar_carl_rogers.py "diferença entre empatia e simpatia na ACP" --json
    python consultar_carl_rogers.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "8c715fc1-e83a-4a6a-8f07-9fac510385a8"

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
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre Carl Rogers e a ACP")
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
