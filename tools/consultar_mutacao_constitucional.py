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
`nlm notebook query`, que responde ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_mutacao_constitucional.py "limites da mutacao constitucional"
    python consultar_mutacao_constitucional.py "interpretacao conforme x nulidade parcial" --json
    python consultar_mutacao_constitucional.py "" --fontes
"""
import sys, shutil, subprocess, argparse

NOTEBOOK_ID = "6295ec8e-1a3f-49d7-996b-4215a00b3894"

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
    print(result.stdout.strip())
    if result.returncode != 0:
        print("\n[ERRO] nlm notebook query retornou erro:", result.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    main()
