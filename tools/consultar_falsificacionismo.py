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
e feita SEMPRE ao vivo via `nlm notebook query`, que responde ancorado nas fontes do
notebook e cita a origem.

Uso:
    python consultar_falsificacionismo.py "criterio de demarcacao de Popper"
    python consultar_falsificacionismo.py "corroboracao x verificacionismo" --json
    python consultar_falsificacionismo.py "standard Daubert" --fontes
"""
import sys, os, shutil, subprocess, argparse, json

NOTEBOOK_ID = "92efec4d-de9b-48e9-bf3b-d8beba52d0e1"

# A CLI e o executavel `nlm`, resolvido pelo PATH — sem caminho absoluto. Duas
# armadilhas ja custaram caro (corrigido em 2026-08-30):
#   1. O modulo NAO se chama `notebooklm`. O pacote e `notebooklm-mcp-cli` e o modulo,
#      `notebooklm_tools` -- `-m notebooklm` estourava ModuleNotFoundError EM SILENCIO.
#   2. No Windows o `nlm` de ~/.local/bin e um script sh que o subprocess nao executa
#      (WinError 2). `shutil.which` devolve o `nlm.CMD` irmao, que roda.
NLM = shutil.which("nlm")
CLI = [NLM] if NLM else None

MSG_SEM_CLI = ("[ERRO] CLI `nlm` nao encontrada no PATH -- este helper nao consulta o "
               "notebook. Instale e autentique a CLI (`nlm login`).")


def _exigir_cli():
    if CLI is None:
        print(MSG_SEM_CLI, file=sys.stderr)
        raise SystemExit(2)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre o tema")
    ap.add_argument("--json", action="store_true", help="saida em JSON bruto da CLI nlm")
    ap.add_argument("--fontes", action="store_true", help="lista as fontes do notebook em vez de perguntar")
    args = ap.parse_args()

    _exigir_cli()

    if args.fontes:
        cmd = CLI + ["source", "list", NOTEBOOK_ID]
        if args.json:
            cmd.append("--json")
        subprocess.run(cmd)
        return

    cmd = CLI + ["notebook", "query", NOTEBOOK_ID, args.pergunta]
    if args.json:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = result.stdout.strip()
    if args.json:
        print(out)
    else:
        print(out)
        if result.returncode != 0:
            print("\n[ERRO] nlm notebook query retornou erro:", result.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
