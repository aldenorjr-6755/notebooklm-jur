#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_maslow.py — Q&A ao vivo no notebook NotebookLM
"Abraham Maslow — Psicologia Humanista" (id a7969675-a508-49d6-ab00-8b8e4cf774dd),
~200 fontes sobre Abraham Maslow e a psicologia humanista/transpessoal: biografia,
hierarquia das necessidades (5 níveis, D-needs × B-needs, mito da pirâmide/McDermid),
autorrealização (<2%, 12 características), experiências de pico (peak experiences,
B-values, metamotivação), autotranscendência (sexto nível, Farther Reaches 1971),
Psicologia Transpessoal (Quarta Força, cofundação com Sutich 1969), Old Saybrook 1964,
aplicações (gestão, educação) e críticas transculturais (Wahba & Bridwell, Tay & Diener,
Kenrick, Ubuntu, ERG/Alderfer).

Não há corpus local espelhado (fontes são páginas web/PDFs externos) — a consulta
é feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado nas fontes
do notebook e cita a origem.

Uso:
    python consultar_maslow.py "o que Maslow entende por B-needs"
    python consultar_maslow.py "diferença entre autorrealização e autotranscendência" --json
    python consultar_maslow.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "a7969675-a508-49d6-ab00-8b8e4cf774dd"

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
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre Abraham Maslow e a psicologia humanista")
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
