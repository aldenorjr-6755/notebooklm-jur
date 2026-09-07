#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
buscar.py — recuperacao hibrida (espec §3.2.3):
  FTS5 (top N literal)  ∪  LanceDB/bge-m3 (top N semantico)  ->  dedup por chunk  ->
  reranker bge-reranker-v2-m3  ->  top K, cada um prefixado com [ID <id_pje> | <vol> p. <n> | <tipo> | <data>]

Esse prefixo e' o que o validador de fontes (§4) confere depois: a minuta so pode citar o que veio daqui.

Uso:
  .venv-rag314/Scripts/python tools/buscar.py casos "acordo de não persecução penal" --cnj 0801524-21.2024.8.10.0093
  .venv-rag314/Scripts/python tools/buscar.py casos "Num. 145636786" --so-fts
  .venv-rag314/Scripts/python tools/buscar.py vault "consentimento do morador" --colecao informativos_stj --json
Opcoes: --tipo DECISAO (filtra ato_tipo), -k 8, --n 15 (candidatos por via), --sem-reranker, --json
Custo (CPU, medido 2026-09-07): embedding da pergunta 0,2 s; FTS < 0,1 s; reranker ~1 s por par
(1.000 chars, 256 tokens; threads nao ajudam) + 9 s de carga por processo. Consulta tipica com
~25 candidatos: 30-35 s. Sem reranker (fusao RRF): < 2 s. Para uso interativo, --sem-reranker;
para o pipeline de minuta (Express), sempre com reranker.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rag_comum as R  # noqa: E402

_RERANKER = None

# Medido em 2026-09-07 (Core 7 150U): o reranker custa ~1-2 s por par a 512 tokens. Com 20-30
# candidatos, 1.000 chars e max_length 256 fica em ~10-15 s por consulta; 50 pares a 512 davam 100 s.
RERANK_CORTE_CHARS = 1000
RERANK_MAX_LEN = 256


def reranker():
    global _RERANKER
    if _RERANKER is None:
        import os
        import torch
        torch.set_num_threads(max(1, os.cpu_count() or 1))
        from sentence_transformers import CrossEncoder
        _RERANKER = CrossEncoder(R.MODELO_RERANK, max_length=RERANK_MAX_LEN)
    return _RERANKER


def via_fts(con, q: str, colecao: str | None, tipo: str | None, n: int) -> list[dict]:
    consulta = R.consulta_fts(q)
    sql = ("SELECT c.*, bm25(chunks_fts) AS score_fts FROM chunks_fts f JOIN chunks c ON c.rowid = f.rowid "
           "WHERE chunks_fts MATCH ?")
    args: list = [consulta]
    if colecao:
        sql += " AND c.colecao = ?"
        args.append(colecao)
    if tipo:
        sql += " AND c.ato_tipo = ?"
        args.append(tipo)
    sql += " ORDER BY score_fts LIMIT ?"
    args.append(n)
    try:
        rows = con.execute(sql, args).fetchall()
    except Exception as e:  # consulta malformada: tenta OR
        alt = consulta.replace(" AND ", " OR ")
        args[0] = alt
        try:
            rows = con.execute(sql, args).fetchall()
        except Exception:
            print(f"[fts] consulta invalida: {consulta} ({e})", file=sys.stderr)
            return []
    if not rows and " AND " in consulta:
        args[0] = consulta.replace(" AND ", " OR ")
        rows = con.execute(sql, args).fetchall()
    return [dict(r) | {"via": "fts"} for r in rows]


def via_vetor(con, q: str, colecao: str | None, tipo: str | None, n: int) -> list[dict]:
    db = R.abrir_lance("casos" if con_banco(con) == "casos" else "vault")
    tbl = R.tabela_lance(db, criar_se_faltar=False)
    if tbl is None:
        return []
    vec = R.embed([q])[0]
    qb = tbl.search(vec).metric("cosine").limit(n)
    filtros = []
    if colecao:
        filtros.append(f"colecao = '{colecao}'")
    if tipo:
        filtros.append(f"ato_tipo = '{tipo}'")
    if filtros:
        qb = qb.where(" AND ".join(filtros), prefilter=True)
    hits = qb.to_list()
    if not hits:
        return []
    ids = [h["chunk_id"] for h in hits]
    marcas = ",".join("?" * len(ids))
    rows = {r["chunk_id"]: dict(r) for r in con.execute(f"SELECT * FROM chunks WHERE chunk_id IN ({marcas})", ids)}
    out = []
    for h in hits:
        r = rows.get(h["chunk_id"])
        if r:
            r["score_vetor"] = 1.0 - float(h.get("_distance", 1.0))
            r["via"] = "vetor"
            out.append(r)
    return out


def con_banco(con) -> str:
    # o caminho do arquivo diz qual banco e'
    caminho = con.execute("PRAGMA database_list").fetchone()[2]
    return "casos" if caminho.endswith("casos.db") else "vault"


def buscar(banco: str, q: str, colecao: str | None = None, tipo: str | None = None, k: int = 8,
           n: int = 15, so_fts: bool = False, sem_reranker: bool = False) -> dict:
    t0 = time.time()
    con = R.abrir_sqlite(banco)
    cand: dict[str, dict] = {}
    for r in via_fts(con, q, colecao, tipo, n):
        cand[r["chunk_id"]] = r
    n_fts = len(cand)
    n_vet = 0
    if not so_fts:
        try:
            for r in via_vetor(con, q, colecao, tipo, n):
                n_vet += 1
                if r["chunk_id"] in cand:
                    cand[r["chunk_id"]]["via"] = "fts+vetor"
                    cand[r["chunk_id"]]["score_vetor"] = r["score_vetor"]
                else:
                    cand[r["chunk_id"]] = r
        except Exception as e:
            print(f"[vetor] indisponivel: {e}", file=sys.stderr)
    lista = list(cand.values())
    t1 = time.time()
    if lista and not sem_reranker:
        m = reranker()
        scores = m.predict([(q, c["texto"][:RERANK_CORTE_CHARS]) for c in lista])
        for c, s in zip(lista, scores):
            c["score_rerank"] = float(s)
        lista.sort(key=lambda c: -c["score_rerank"])
    else:
        # sem reranker: fusao simples por posicao (RRF) entre as duas vias
        def rrf(c):
            s = 0.0
            if "score_fts" in c:
                s += 1.0
            if "score_vetor" in c:
                s += c["score_vetor"]
            return -s
        lista.sort(key=rrf)
    # o mesmo texto aparece em varios atos (denuncia copiada na carta precatoria, na certidao...):
    # mostra uma vez, no ato mais antigo, e anota onde mais aparece
    vistos: dict[str, dict] = {}
    unicos = []
    for c in lista:
        h = _chave_dup(c["texto"])
        c["hash"] = h
        if h and h in vistos:
            vistos[h].setdefault("tambem_em", []).append(
                f"ID {c.get('id_pje') or '-'} {c.get('volume') or ''} p. {c.get('pagina')} ({c.get('ato_tipo')})")
            continue
        if h:
            vistos[h] = c
        unicos.append(c)
    # entre duplicatas, prefere o ato de menor seq (o original vem antes das copias)
    for c in unicos:
        if c.get("tambem_em"):
            todos = [c] + [x for x in lista if x.get("hash") == c.get("hash") and x is not c]
            orig = min(todos, key=lambda x: (x.get("ato_seq") or 0))
            if orig is not c:
                orig["tambem_em"] = [f"ID {x.get('id_pje') or '-'} {x.get('volume') or ''} p. {x.get('pagina')} ({x.get('ato_tipo')})"
                                     for x in todos if x is not orig]
                orig["score_rerank"] = c.get("score_rerank")
                unicos[unicos.index(c)] = orig
    top = unicos[:k]
    con.close()
    return {"consulta": q, "banco": banco, "colecao": colecao, "candidatos_fts": n_fts,
            "candidatos_vetor": n_vet, "unicos": len(lista), "seg_recuperacao": round(t1 - t0, 2),
            "seg_total": round(time.time() - t0, 2),
            "resultados": [_saida(c) for c in top]}


def _chave_dup(texto: str) -> str:
    """Copias do mesmo documento (denuncia dentro da precatoria) nao sao paginas identicas: o
    rodape e a vizinhanca mudam. A chave e' o inicio normalizado do texto (200 chars sem
    acento, sem espacos, minusculo), suficiente para pegar a copia e nao juntar textos distintos."""
    t = R.sem_acento(" ".join(texto.split())).lower()
    t = "".join(ch for ch in t if ch.isalnum())
    return t[:200]


def _saida(c: dict) -> dict:
    bloco = f" bloco {c['parte']}" if c.get("parte") else ""
    if c.get("id_pje") or c.get("ato_seq"):
        # ato processual: a referencia e' o que a minuta cita e o validador confere
        ref = (f"[ID {c.get('id_pje') or '-'} | {c.get('volume') or ''} p. {c.get('pagina')}{bloco}"
               f" | {c.get('ato_tipo') or '-'} | {c.get('data') or 'sem data'}]")
    else:
        # nota de corpus publico: colecao + titulo + pagina (se paginada) + data
        pag = f" | p. {c.get('pagina')}{bloco}" if c.get("pagina") else (f" |{bloco}" if bloco else "")
        ref = f"[{c.get('colecao')} | {c.get('titulo') or c.get('volume')}{pag} | {c.get('data') or 'sem data'}]"
    return {"ref": ref, "chunk_id": c["chunk_id"], "ato_seq": c.get("ato_seq"), "id_pje": c.get("id_pje"),
            "ato_tipo": c.get("ato_tipo"), "titulo": c.get("titulo"), "data": c.get("data"),
            "volume": c.get("volume"), "pagina": c.get("pagina"), "parte": c.get("parte"),
            "via": c.get("via"), "score_rerank": c.get("score_rerank"), "score_vetor": c.get("score_vetor"),
            "score_fts": c.get("score_fts"), "fonte": c.get("fonte"), "tambem_em": c.get("tambem_em"),
            "texto": c["texto"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("banco", choices=sorted(R.BANCOS))
    ap.add_argument("consulta")
    ap.add_argument("--cnj", "--colecao", dest="colecao")
    ap.add_argument("--tipo")
    ap.add_argument("-k", type=int, default=8)
    ap.add_argument("--n", type=int, default=15, help="candidatos por via (FTS e vetor); 15 → ~25 pares no reranker")
    ap.add_argument("--so-fts", action="store_true")
    ap.add_argument("--sem-reranker", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--trecho", type=int, default=400, help="chars do trecho na saida legivel")
    a = ap.parse_args(argv)
    res = buscar(a.banco, a.consulta, a.colecao, a.tipo, a.k, a.n, a.so_fts, a.sem_reranker)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return 0
    print(f"# {res['consulta']}  ({res['banco']}/{res['colecao'] or '*'}; fts={res['candidatos_fts']} "
          f"vetor={res['candidatos_vetor']} unicos={res['unicos']}; {res['seg_total']}s)\n")
    for i, r in enumerate(res["resultados"], 1):
        sc = f"rerank={r['score_rerank']:.3f}" if r.get("score_rerank") is not None else ""
        print(f"{i}. {r['ref']}  via={r['via']} {sc}")
        if r.get("titulo"):
            print(f"   titulo: {r['titulo']}")
        if r.get("tambem_em"):
            print(f"   mesmo texto tambem em: {'; '.join(r['tambem_em'])}")
        t = " ".join(r["texto"].split())
        print(f"   {t[:a.trecho]}{'…' if len(t) > a.trecho else ''}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
