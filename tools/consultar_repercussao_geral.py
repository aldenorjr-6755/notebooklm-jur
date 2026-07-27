#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_repercussao_geral.py — pesquisa os Temas de Repercussao Geral do STF.

Endpoint (descoberto em /scripts/tesesrepercussaogeral.js):
    POST https://portal.stf.jus.br/repercussaogeral/retornartesesrepercussaogeral.asp
         body: tipo=com  -> temas COM tese fixada
               tipo=sem  -> temas SEM tese (afetados / pendentes de julgamento)
    Retorna JSON (UTF-8). Cada item:
       numeroTema, incidente, siglaClasse, numeroProcesso, descricaoTese, dataAndamento
    A pesquisa por texto do site e' filtro CLIENT-SIDE sobre essa lista — fazemos igual aqui.

PAGINA CANONICA DE BUSCA (oficial, referencia):
    https://portal.stf.jus.br/jurisprudenciaRepercussao/pesquisarProcesso.asp
    Busca RICA por baixo: GET https://portal.stf.jus.br/jurisprudenciaRepercussao/listarProcesso.asp
    (retorna HTML; filtros: txtTituloTema, numeroTemaInicial, tipoComRG/tipoSemRG/tipoSemRGQC,
     situacaoRG, situacaoAtual, classeProcesso, numeroProcesso, ministro, txtRamoDireito,
     dataInicialJulgPV, dataFinalJulgPV, ordenacao). Este helper usa o endpoint JSON p/
     numero/palavra/tese; p/ filtros avancados (ministro/classe/ramo/data) usar listarProcesso.asp.
     WAF do STF exige User-Agent de navegador + Referer.

Uso:
    python consultar_repercussao_geral.py "concurso publico"      # busca por palavra
    python consultar_repercussao_geral.py --tema 69               # tema especifico
    python consultar_repercussao_geral.py "icms" --tipo com       # so com tese fixada
    python consultar_repercussao_geral.py "saude" --json
    python consultar_repercussao_geral.py --tema 1234 --tipo sem  # pendentes

Opcoes:
    --tipo com|sem|todos   (padrao: todos)
    --tema N               filtra pelo numero exato do Tema
    --json                 saida estruturada
    --no-cache             ignora o cache local (TTL 12h em prazos/)
    --limite N             maximo de resultados exibidos (padrao 40)
"""
import sys
import os
import json
import time
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

URL = "https://portal.stf.jus.br/repercussaogeral/retornartesesrepercussaogeral.asp"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
ANDAMENTO = ("https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp"
             "?incidente={incidente}&numeroProcesso={numeroProcesso}"
             "&classeProcesso={siglaClasse}&numeroTema={numeroTema}")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prazos")
CACHE_TTL = 12 * 3600  # 12 horas


def _cache_path(tipo):
    return os.path.join(CACHE_DIR, f"_cache_rg_{tipo}.json")


def baixar(tipo, usar_cache=True):
    cache = _cache_path(tipo)
    if usar_cache and os.path.exists(cache) and (time.time() - os.path.getmtime(cache) < CACHE_TTL):
        try:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    dados = urllib.parse.urlencode({"tipo": tipo}).encode("ascii")
    req = urllib.request.Request(URL, data=dados, method="POST",
                                 headers={"User-Agent": UA,
                                          "X-Requested-With": "XMLHttpRequest",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        lista = json.loads(resp.read().decode("utf-8", errors="replace"))
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False)
    except Exception:
        pass
    return lista


def coletar(tipos, usar_cache=True):
    saida = []
    for t in tipos:
        for item in baixar(t, usar_cache):
            item = dict(item)
            item["statusTese"] = "COM tese fixada" if t == "com" else "SEM tese (afetado/pendente)"
            saida.append(item)
    return saida


def filtrar(itens, termo=None, tema=None):
    if tema is not None:
        alvo = str(tema).lstrip("0") or "0"
        return [i for i in itens if str(i.get("numeroTema", "")).lstrip("0") == alvo]
    if termo:
        t = termo.lower()
        return [i for i in itens
                if t in i.get("descricaoTese", "").lower()
                or t in str(i.get("numeroTema", ""))]
    return itens


def imprimir(itens, alvo, limite):
    if not itens:
        print(f"Nenhum Tema de Repercussao Geral encontrado para: {alvo!r}")
        return
    total = len(itens)
    itens = sorted(itens, key=lambda i: int(i.get("numeroTema", "0") or 0))
    print(f"Repercussao Geral (STF) — {total} resultado(s) para: {alvo!r}"
          + (f" (exibindo {limite})" if total > limite else "") + "\n")
    for i in itens[:limite]:
        n = i.get("numeroTema", "?")
        print(f"== Tema {n} — {i.get('siglaClasse','')} {i.get('numeroProcesso','')} "
              f"[{i['statusTese']}] — {i.get('dataAndamento','')} ==")
        print("  " + (i.get("descricaoTese") or "(sem tese fixada)").strip())
        print("  Andamento: " + ANDAMENTO.format(**i))
        print()
    print("Fonte: STF — Teses de Repercussao Geral "
          "(https://portal.stf.jus.br/repercussaogeral/teses.asp)")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    tipo = "todos"
    tema = None
    como_json = False
    usar_cache = True
    limite = 40
    termos = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--tipo" and i + 1 < len(args):
            tipo = args[i + 1].lower(); i += 2; continue
        if a == "--tema" and i + 1 < len(args):
            tema = args[i + 1]; i += 2; continue
        if a == "--limite" and i + 1 < len(args):
            limite = int(args[i + 1]); i += 2; continue
        if a == "--json":
            como_json = True; i += 1; continue
        if a == "--no-cache":
            usar_cache = False; i += 1; continue
        termos.append(a); i += 1

    tipos = ["com", "sem"] if tipo == "todos" else [tipo]
    if any(t not in ("com", "sem") for t in tipos):
        print("--tipo deve ser: com | sem | todos"); return 2

    termo = " ".join(termos).strip() or None
    alvo = (f"Tema {tema}" if tema else termo) or "(todos)"

    try:
        itens = coletar(tipos, usar_cache)
    except Exception as e:
        print(f"Erro ao consultar a Repercussao Geral do STF: {e}")
        return 1

    res = filtrar(itens, termo=termo, tema=tema)
    if como_json:
        print(json.dumps({"consulta": alvo, "total": len(res), "temas": res},
                         ensure_ascii=False, indent=2))
    else:
        imprimir(res, alvo, limite)
    return 0


if __name__ == "__main__":
    sys.exit(main())
