#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_epistemologia_testemunho.py — Q&A ao vivo no notebook NotebookLM
"Epistemologia do Testemunho (Coady x Lackey) na Prova Penal" (id 2532e5f9-f47d-4ac4-9576-e7c0c23e8814).

Debate reducionismo x antirreducionismo sobre o testemunho como fonte de
conhecimento: Hume (reducionismo classico), Reid (antirreducionismo, principio
da credulidade), C.A.J. Coady ("Testimony: A Philosophical Study", 1992 —
defesa do antirreducionismo, testemunho como fonte epistemica basica),
Jennifer Lackey ("Learning from Words", 2008 — critica a ambos os extremos,
dualismo hibrido), Elizabeth Fricker (reducionismo local, monitoring view),
Sanford Goldberg, Peter Graham. Aplicacao a epistemologia juridica da prova:
fundamento do valor probatorio do testemunho, exigencia de corroboracao da
palavra da vitima e da confissao, credibilidade padrao x verificacao
independente.

Nao ha corpus local espelhado (fontes sao paginas web/PDFs externos) — a
consulta e feita SEMPRE ao vivo via `notebooklm ask`, que responde ancorado
nas fontes do notebook e cita a origem.

Uso:
    python consultar_epistemologia_testemunho.py "reducionismo x antirreducionismo em Coady"
    python consultar_epistemologia_testemunho.py "dualismo de Lackey" --json
    python consultar_epistemologia_testemunho.py "" --fontes
"""
import sys, os, subprocess, argparse, json

NOTEBOOK_ID = "2532e5f9-f47d-4ac4-9576-e7c0c23e8814"

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
