#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_validade_pericial.py — Q&A ao vivo no notebook NotebookLM
"Validade Cientifica do Metodo Pericial (Foundational Validity) na Prova Judicial"
(id 130f97d7-bb0e-46cd-a762-f436b09da632).

Camada que fica ACIMA da conformidade ao protocolo (POP/manuais, ja cobertos pelo
corpus ~/.notebooklm/manuais_pericia/) e ABAIXO da valoracao do conjunto: o metodo
mede o que diz medir? Conformidade nao e validade.

Cobre: validade fundacional x validade aplicada (PCAST 2016 e Addendum 2017);
black-box studies e taxas de erro medidas; NAS/NRC 2009; relatorio evaluativo e razao
de verossimilhanca (ENFSI 2015); a resposta critica do FBI ao PCAST; a recepcao
brasileira (colunistas do Criminal Player/ConJur — Rachel Herdy, Janaina Matida e
outros: controle judicial da pseudociencia, provas periciais de baixa fiabilidade,
filtragem epistemica, ciencia das armas de fogo); e a jurisprudencia do STJ
(HC 740.431/DF — autopsia psicologica, criterios de verificabilidade; REsp 1.931.969/SP
— art. 473, III, do CPC e o obice da Sumula 7).

ATENCAO ao usar as respostas:
  * a camada de VALIDADE APLICADA (execucao, POP, alcada declarada) NAO esta aqui —
    esta no corpus local ~/.notebooklm/manuais_pericia/fontes/;
  * ementa de acordao veio de agregador (Jusbrasil): confirmar inteiro teor no STJ;
  * numero de taxa de erro so sai com o estudo e o denominador identificados —
    a taxa muda conforme se incluam ou nao os exames inconclusivos.

Uso:
    python consultar_validade_pericial.py "o que e foundational validity"
    python consultar_validade_pericial.py "taxa de erro do confronto balistico" --json
    python consultar_validade_pericial.py "" --fontes
"""
import sys, subprocess, argparse

NOTEBOOK_ID = "130f97d7-bb0e-46cd-a762-f436b09da632"

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
    ap.add_argument("pergunta", help="pergunta em linguagem natural sobre validade do metodo pericial")
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
