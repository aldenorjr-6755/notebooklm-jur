#!/usr/bin/env python3
"""
Consulta o índice local da Jurisprudência em Teses do STJ.

Fontes:
  Índice JSON : ~/.notebooklm/tools/jurisprudencia_teses_stj.json  (279 edições)
  PDF/MD completo: ~/.notebooklm/biblioteca/{pdf,md}/JTSelecao_JurisprudenciaTeses_STJ.* (1.515 pp.)
  Fonte online: scon.stj.jus.br/SCON/jt/

Uso:
  python consultar_jurisprudencia_teses.py --busca "execucao penal"
  python consultar_jurisprudencia_teses.py --edicao 45
  python consultar_jurisprudencia_teses.py --listar
"""

import argparse, json, unicodedata, sys
from pathlib import Path

INDICE = Path(__file__).parent / "jurisprudencia_teses_stj.json"


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()


def carregar() -> list[dict]:
    with open(INDICE, encoding="utf-8") as f:
        return json.load(f)


def buscar(query: str) -> list[dict]:
    dados = carregar()
    q = normalizar(query)
    return [e for e in dados if q in normalizar(e["titulo"])]


def por_edicao(num: int) -> dict | None:
    dados = carregar()
    for e in dados:
        if e["edicao"] == num:
            return e
    return None


def formatar(e: dict) -> str:
    pagina = f"p. {e['pagina']}" if e["pagina"] else "p. (N/D)"
    url = f"https://scon.stj.jus.br/SCON/jt/doc.jsp?livre=edicao+{e['edicao']}"
    return f"  Edição {e['edicao']:>3} [{pagina:>8}] — {e['titulo']}\n            URL: {url}"


def main():
    parser = argparse.ArgumentParser(description="Jurisprudência em Teses do STJ")
    parser.add_argument("--busca", help="Palavra-chave no título da edição")
    parser.add_argument("--edicao", type=int, help="Número da edição")
    parser.add_argument("--listar", action="store_true", help="Listar todas as edições")
    args = parser.parse_args()

    if args.edicao:
        e = por_edicao(args.edicao)
        if e:
            print(formatar(e))
        else:
            print(f"Edição {args.edicao} não encontrada.")
        return

    if args.busca:
        resultados = buscar(args.busca)
        if resultados:
            print(f"{len(resultados)} edição(ões) encontrada(s) para '{args.busca}':\n")
            for e in resultados:
                print(formatar(e))
        else:
            print(f"Nenhuma edição encontrada para '{args.busca}'.")
        return

    if args.listar:
        dados = carregar()
        print(f"Jurisprudência em Teses do STJ — {len(dados)} edições\n")
        for e in dados:
            print(formatar(e))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
