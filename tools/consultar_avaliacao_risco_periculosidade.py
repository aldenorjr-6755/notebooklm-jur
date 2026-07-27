#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_avaliacao_risco_periculosidade.py — Q&A ao vivo no notebook NotebookLM
"Avaliacao Atuarial de Risco e Periculosidade (HCR-20, PCL-R, COMPAS) na Prova Penal"
(id b3335faf-d51c-4f2f-b3de-1a5ba34310b5).

Instrumentos atuariais e estruturados de avaliacao de risco (HCR-20, PCL-R, VRAG,
LSI-R/LS-CMI, COMPAS), critica cientifica e metodologica (Angwin/ProPublica "Machine
Bias", Dressel & Farid, teorema da impossibilidade de Kleinberg/Chouldechova),
literatura de referencia (Harcourt "Against Prediction", Skeem & Slobogin, Sonja
Starr, Kehl/Guo/Kessler, State v. Loomis) e aplicacao ao direito brasileiro
(periculosidade no CPP 312, medida de seguranca CP 96-98, Sumula 527 STJ, critica de
Zaffaroni/Nilo Batista/Vera Regina Pereira de Andrade).

Nao ha corpus local espelhado (fontes sao paginas web/PDFs/artigos academicos
externos) — a consulta e feita SEMPRE ao vivo via `notebooklm ask`, que responde
ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_avaliacao_risco_periculosidade.py "o que e o teorema da impossibilidade de Kleinberg"
    python consultar_avaliacao_risco_periculosidade.py "PCL-R como preditor de reincidencia" --json
    python consultar_avaliacao_risco_periculosidade.py "" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "b3335faf-d51c-4f2f-b3de-1a5ba34310b5"

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
