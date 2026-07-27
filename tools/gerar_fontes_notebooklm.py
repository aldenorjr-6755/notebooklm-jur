#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gerar_fontes_notebooklm.py — gera 2 arquivos Markdown para adicionar como FONTE no NotebookLM:

  1) prazos/fontes-notebooklm/tesauro-stf-completo.md
     Vocabulario controlado INTEIRO do Tesauro Juridico do STF (navega ?letra=A..Z,0-9),
     um bloco compacto por descritor (USE/UP/TG/TE/TR/NE/CATEGORIA).

  2) prazos/fontes-notebooklm/temas-repercussao-geral-stf.md
     TODOS os Temas de Repercussao Geral (tipo=com tese fixada + tipo=sem tese), um por bloco.

Reaproveita os helpers irmaos (mesmo diretorio):
  consultar_tesauro.py            -> parse() do XML
  consultar_repercussao_geral.py  -> coletar() do JSON

Uso:
    python gerar_fontes_notebooklm.py            # gera os dois
    python gerar_fontes_notebooklm.py tesauro    # so o Tesauro
    python gerar_fontes_notebooklm.py temas      # so os Temas RG
"""
import sys
import os
import time
import datetime
import string
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import consultar_tesauro as ct                 # noqa: E402
import consultar_repercussao_geral as rg       # noqa: E402

SAIDA = os.path.normpath(os.path.join(AQUI, "..", "prazos", "fontes-notebooklm"))
CACHE = os.path.join(SAIDA, "_cache")
UA = ct.UA
HOJE = datetime.date.today().isoformat()

ROTULO = {
    "USE": "USE (preferido)", "UP": "UP (sinônimos)", "TG": "TG (genérico)",
    "TE": "TE (específico)", "TR": "TR (relacionado)", "NE": "Nota",
    "CATEGORIA": "Categoria",
}
ORDEM = ["NE", "CATEGORIA", "USE", "UP", "TG", "TE", "TR"]


def _baixar_letra(letra):
    cache = os.path.join(CACHE, f"tesauro_{letra}.xml")
    if os.path.exists(cache) and (time.time() - os.path.getmtime(cache) < 7 * 86400):
        with open(cache, encoding="utf-8") as f:
            return f.read()
    url = ct.BASE + "?" + urllib.parse.urlencode({"letra": letra})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        texto = resp.read().decode("utf-8", errors="replace")
    import re
    texto = re.sub(r"^\s*<\?xml[^>]*\?>", "", texto).strip()
    os.makedirs(CACHE, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


def gerar_tesauro():
    os.makedirs(SAIDA, exist_ok=True)
    letras = list(string.ascii_uppercase) + list("0123456789")
    vistos = {}
    print("Baixando o Tesauro por letra (A-Z, 0-9)...")
    for L in letras:
        try:
            termos = ct.parse(_baixar_letra(L))
        except Exception as e:
            print(f"  [!] letra {L}: {e}")
            continue
        novos = 0
        for t in termos:
            chave = t["termo"].upper()
            if chave not in vistos:
                vistos[chave] = t
                novos += 1
        print(f"  {L}: {len(termos):>5} termos ({novos} novos)  | total {len(vistos)}")
        time.sleep(0.3)

    termos = sorted(vistos.values(), key=lambda t: t["termo"])
    destino = os.path.join(SAIDA, "tesauro-stf-completo.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("# Tesauro Jurídico do STF — vocabulário controlado (completo)\n\n")
        f.write(f"> Fonte: https://portal.stf.jus.br/jurisprudencia/tesauro/pesquisa.asp  \n")
        f.write(f"> Extraído em {HOJE}. {len(termos)} descritores.  \n")
        f.write("> Legenda: **USE** termo preferido · **UP** sinônimos · **TG** termo genérico · "
                "**TE** termo específico · **TR** termo relacionado · **NE** nota explicativa · "
                "**Categoria** ramo do direito.\n\n---\n\n")
        for t in termos:
            f.write(f"## {t['termo']}\n")
            rels = t["relacoes"]
            for cod in ORDEM:
                if cod in rels:
                    if cod == "NE":
                        for v in rels[cod]:
                            f.write(f"- **{ROTULO[cod]}:** {v}\n")
                    else:
                        f.write(f"- **{ROTULO[cod]}:** " + "; ".join(rels[cod]) + "\n")
            f.write("\n")
    _relatorio(destino, len(termos), "descritores")
    return destino


def gerar_temas_rg():
    os.makedirs(SAIDA, exist_ok=True)
    print("Baixando os Temas de Repercussão Geral (com + sem tese)...")
    itens = rg.coletar(["com", "sem"], usar_cache=True)
    itens = sorted(itens, key=lambda i: int(i.get("numeroTema", "0") or 0))
    n_com = sum(1 for i in itens if i["statusTese"].startswith("COM"))
    n_sem = len(itens) - n_com
    destino = os.path.join(SAIDA, "temas-repercussao-geral-stf.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("# Temas de Repercussão Geral do STF (completo)\n\n")
        f.write("> Fonte: https://portal.stf.jus.br/repercussaogeral/teses.asp  \n")
        f.write(f"> Extraído em {HOJE}. {len(itens)} temas "
                f"({n_com} com tese fixada · {n_sem} afetados/sem tese).  \n")
        f.write("> COM tese fixada = precedente vinculante (CPC 927). "
                "SEM tese = afetado/pendente (suspensão, CPC 1.037 II).\n\n---\n\n")
        for i in itens:
            n = i.get("numeroTema", "?")
            f.write(f"## Tema {n} — {i.get('siglaClasse','')} {i.get('numeroProcesso','')}\n")
            f.write(f"- **Status:** {i['statusTese']}\n")
            f.write(f"- **Último andamento:** {i.get('dataAndamento','')}\n")
            tese = (i.get("descricaoTese") or "").strip() or "(sem tese fixada)"
            f.write(f"- **Tese:** {tese}\n\n")
    _relatorio(destino, len(itens), "temas")
    return destino


def _relatorio(destino, n, unidade):
    tam = os.path.getsize(destino)
    with open(destino, encoding="utf-8") as f:
        palavras = sum(len(l.split()) for l in f)
    print(f"  -> {destino}")
    print(f"     {n} {unidade} | {tam/1024:.1f} KB | ~{palavras:,} palavras".replace(",", "."))


def main():
    alvo = sys.argv[1].lower() if len(sys.argv) > 1 else "ambos"
    if alvo in ("tesauro", "ambos"):
        gerar_tesauro()
    if alvo in ("temas", "rg", "ambos"):
        gerar_temas_rg()
    print("\nPronto. Adicione os .md em prazos/fontes-notebooklm/ como FONTE no NotebookLM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
