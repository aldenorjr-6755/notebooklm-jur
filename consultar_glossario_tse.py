"""
Consulta o Glossário Eleitoral do TSE (glossario_tse.json).
Uso: python consultar_glossario_tse.py <termo_ou_slug>
     python consultar_glossario_tse.py --lista
"""

import sys
import io
import json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import re
import os

DATA = os.path.join(os.path.dirname(__file__), "glossario_tse.json")


def normalizar(s):
    s = s.lower()
    s = re.sub(r"[áàãâä]", "a", s)
    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s)
    s = re.sub(r"[óòõôö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    return s


def buscar(termos, query):
    q = normalizar(query)
    exatos = [t for t in termos if normalizar(t["slug"]) == q or normalizar(t["termo"]) == q]
    if exatos:
        return exatos
    parciais = [t for t in termos if q in normalizar(t["slug"]) or q in normalizar(t["termo"])]
    return parciais


def formatar(t):
    linhas = [f"TERMO: {t['termo']}", f"SLUG:  {t['slug']}"]
    if t["definicao"]:
        linhas.append(f"\nDEFINICAO:\n{t['definicao']}")
    if t["ver_tambem"]:
        linhas.append(f"\nVER TAMBEM: {t['ver_tambem']}")
    if t["referencia"]:
        linhas.append(f"\nREFERENCIA: {t['referencia']}")
    linhas.append(f"\nFonte: Glossario Eleitoral TSE")
    linhas.append(f"URL: https://www.tse.jus.br/servicos-eleitorais/glossario/termos-iniciados-com-a-letra-{t['slug'][0]}#{t['slug']}")
    return "\n".join(linhas)


def main():
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    termos = d["termos"]

    if len(sys.argv) < 2 or sys.argv[1] == "--lista":
        print(f"Glossario Eleitoral TSE — {d['total']} termos\n")
        for t in termos:
            print(f"  {t['termo']}  [{t['slug']}]")
        return

    query = " ".join(sys.argv[1:])
    resultados = buscar(termos, query)
    if not resultados:
        print(f"Nenhum termo encontrado para: {query}")
        return
    for r in resultados:
        print(formatar(r))
        print("=" * 60)


if __name__ == "__main__":
    main()
