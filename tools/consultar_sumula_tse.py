#!/usr/bin/env python3
"""
Consulta as Súmulas do TSE (Tribunal Superior Eleitoral).

Fontes:
  Índice JSON : ~/.notebooklm/tools/sumulas_tse.json  (73 súmulas)
  PDF/MD local: ~/.notebooklm/biblioteca/{pdf,md}/TSE-Sumulas-TSE.*
  Fonte online: https://www.tse.jus.br/legislacao/compilada/sumulas

Uso:
  python consultar_sumula_tse.py --numero 6
  python consultar_sumula_tse.py --busca "filiação partidária"
  python consultar_sumula_tse.py --listar
  python consultar_sumula_tse.py --listar --canceladas
"""

import argparse, json, unicodedata, sys
from pathlib import Path

INDICE = Path(__file__).parent / "sumulas_tse.json"


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()


def carregar(incluir_canceladas: bool = True) -> list[dict]:
    with open(INDICE, encoding="utf-8") as f:
        dados = json.load(f)
    if not incluir_canceladas:
        dados = [s for s in dados if not s["cancelada"]]
    return dados


def buscar(query: str, incluir_canceladas: bool = False) -> list[dict]:
    dados = carregar(incluir_canceladas)
    q = normalizar(query)
    return [s for s in dados if q in normalizar(s["verbete"])]


def por_numero(num: int) -> dict | None:
    for s in carregar():
        if s["numero"] == num:
            return s
    return None


def formatar(s: dict) -> str:
    status = " [CANCELADA]" if s["cancelada"] else ""
    return f"  Súm.-TSE {s['numero']:>3}{status} — {s['verbete']}"


def main():
    parser = argparse.ArgumentParser(description="Súmulas do TSE")
    parser.add_argument("--numero", type=int, help="Número da súmula")
    parser.add_argument("--busca", help="Palavra-chave no verbete")
    parser.add_argument("--listar", action="store_true", help="Listar todas")
    parser.add_argument("--canceladas", action="store_true", help="Incluir canceladas")
    args = parser.parse_args()

    if args.numero:
        s = por_numero(args.numero)
        if s:
            print(formatar(s))
        else:
            print(f"Súmula-TSE {args.numero} não encontrada.")
        return

    if args.busca:
        resultados = buscar(args.busca, args.canceladas)
        if resultados:
            print(f"{len(resultados)} súmula(s) encontrada(s) para '{args.busca}':\n")
            for s in resultados:
                print(formatar(s))
        else:
            print(f"Nenhuma súmula encontrada para '{args.busca}'.")
        return

    if args.listar:
        dados = carregar(args.canceladas)
        total = len(dados)
        ativas = sum(1 for s in dados if not s["cancelada"])
        print(f"Súmulas do TSE — {total} total ({ativas} ativas)\n")
        for s in dados:
            print(formatar(s))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
