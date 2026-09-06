#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_neurodireito_responsabilidade_penal.py — Q&A ao vivo no notebook NotebookLM
"Neurodireito e Neurociencia Forense da Responsabilidade Penal na Prova Penal"
(id 32526abb-c2e8-4dcf-b46f-6a9759ebca9b).

Neurolaw / neurodireito (Owen Jones, Greene & Cohen), livre-arbitrio x determinismo
(Dennett, Caruso, Libet), neuroimagem como prova e admissibilidade (Daubert x Frye,
brain fingerprinting, US v. Semrau), casos-chave (Roper v. Simmons, Miller v. Alabama,
Phineas Gage), neurociencia da psicopatia e agressao (Kent Kiehl, Damasio, MAOA/gene
guerreiro), critica cetica (Stephen Morse "brain overclaim syndrome", Adina Roskies,
Nita Farahany) e imputabilidade no direito brasileiro (CP 26, CPP 149-154, medida de
seguranca CP 96-98).

Nao ha corpus local espelhado (fontes sao paginas web/PDFs/artigos academicos
externos) — a consulta e feita SEMPRE ao vivo via `nlm notebook query`, que responde
ancorado nas fontes do notebook e cita a origem.

Uso:
    python consultar_neurodireito_responsabilidade_penal.py "o que e o brain overclaim syndrome de Stephen Morse"
    python consultar_neurodireito_responsabilidade_penal.py "Roper v Simmons e o cortex pre-frontal adolescente" --json
    python consultar_neurodireito_responsabilidade_penal.py "" --fontes
"""
import sys, os, shutil, subprocess, argparse, json

NOTEBOOK_ID = "32526abb-c2e8-4dcf-b46f-6a9759ebca9b"

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
