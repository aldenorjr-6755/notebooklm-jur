#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
indexar.py — indexa atos fatiados (atos.jsonl + atos/*.md) no banco CASOS
(SQLite FTS5 + LanceDB/bge-m3), ou notas Markdown de um corpus no banco VAULT.

Chunk = pagina do ato (marca `## [p. N]` / `## [vol p. N]` gravada pelo fatiar_atos.py), para
que toda recuperacao devolva folha citavel. Pagina acima de ~6k chars e' repartida em blocos.

Uso:
  # autos de um caso (pasta extracted/ do fatiar_atos.py)
  .venv-rag314/Scripts/python tools/indexar.py casos --extracted 20-Casos/<CNJ>/extracted [--cnj <CNJ>]
  # corpus publico (uma pasta de .md): cada arquivo vira chunks por `## [p. N]` ou por blocos
  .venv-rag314/Scripts/python tools/indexar.py vault --pasta ~/.notebooklm/informativo_stj/fontes --colecao informativos_stj
  # so FTS (sem embeddings), para testar rapido
  ... --sem-vetor
Reindexar uma colecao apaga o que havia dela antes (por colecao, nao o banco inteiro).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rag_comum as R  # noqa: E402

RE_MARCA = re.compile(r"^## \[(?:(?P<vol>[^\]]+?) )?p\. (?P<pag>\d+)\](?P<extra>.*)$", re.M)


def _frontmatter(md: str) -> tuple[dict, str]:
    if not md.startswith("---"):
        return {}, md
    fim = md.find("\n---", 3)
    if fim < 0:
        return {}, md
    fm = {}
    for ln in md[3:fim].split("\n"):
        m = re.match(r"^(\w+):\s*(.*)$", ln.strip())
        if m:
            k, v = m.groups()
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = None if v == "null" else v
    return fm, md[fim + 4:]


def chunks_de_ato(md: str, meta: dict, colecao: str, fonte: str) -> list[dict]:
    fm, corpo = _frontmatter(md)
    marcas = list(RE_MARCA.finditer(corpo))
    paginas = []
    if marcas:
        for i, m in enumerate(marcas):
            ini, fim = m.end(), (marcas[i + 1].start() if i + 1 < len(marcas) else len(corpo))
            paginas.append((m.group("vol") or fm.get("volume_ini") or "", int(m.group("pag")), corpo[ini:fim].strip()))
    else:
        paginas.append((fm.get("volume_ini") or "", int(fm.get("pag_ini") or 0), corpo.strip()))
    out = []
    for vol, pag, texto in paginas:
        if not texto:
            continue
        for parte, bloco in enumerate(R.repartir(texto)):
            h = hashlib.sha256(bloco.encode("utf-8")).hexdigest()[:16]
            cid = f"{colecao}|{meta.get('seq', 0)}|{vol}|{pag}|{parte}|{h}"
            out.append({
                "chunk_id": cid, "colecao": colecao, "fonte": fonte,
                "ato_seq": int(meta.get("seq") or 0), "id_pje": meta.get("id_pje") or "",
                "ato_tipo": meta.get("tipo") or fm.get("ato_tipo") or "",
                "titulo": meta.get("titulo") or fm.get("titulo") or "",
                "data": meta.get("data_juntada") or fm.get("data_juntada") or "",
                "volume": vol, "pagina": pag, "parte": parte, "chars": len(bloco), "hash": h,
                "texto": bloco,
            })
    return out


def chunks_de_nota(md: str, colecao: str, fonte: str) -> list[dict]:
    """Corpus publico: nota .md paginada (`## [p. N]`) ou nao (blocos de ~MAX_CHARS)."""
    fm, corpo = _frontmatter(md)
    titulo = fm.get("title") or fm.get("titulo") or Path(fonte).stem
    marcas = list(RE_MARCA.finditer(corpo))
    partes = []
    if marcas:
        for i, m in enumerate(marcas):
            ini, fim = m.end(), (marcas[i + 1].start() if i + 1 < len(marcas) else len(corpo))
            partes.append((int(m.group("pag")), corpo[ini:fim].strip()))
    else:
        partes.append((0, corpo.strip()))
    out = []
    for pag, texto in partes:
        for parte, bloco in enumerate(R.repartir(texto)):
            if len(bloco) < 40:
                continue
            h = hashlib.sha256(bloco.encode("utf-8")).hexdigest()[:16]
            out.append({
                "chunk_id": f"{colecao}|{Path(fonte).stem}|{pag}|{parte}|{h}", "colecao": colecao,
                "fonte": fonte, "ato_seq": 0, "id_pje": "", "ato_tipo": fm.get("tipo") or "nota",
                "titulo": titulo, "data": fm.get("data_julgamento") or fm.get("data") or "",
                "volume": Path(fonte).stem, "pagina": pag, "parte": parte, "chars": len(bloco),
                "hash": h, "texto": bloco,
            })
    return out


def gravar(banco: str, colecao: str, chunks: list[dict], sem_vetor: bool, lote: int = 16,
           quiet: bool = False) -> dict:
    con = R.abrir_sqlite(banco)
    con.execute("DELETE FROM chunks WHERE colecao = ?", (colecao,))
    agora = time.time()
    con.executemany(
        "INSERT INTO chunks (chunk_id, colecao, fonte, ato_seq, id_pje, ato_tipo, titulo, data, volume, "
        "pagina, parte, chars, hash, texto, indexado_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(c["chunk_id"], c["colecao"], c["fonte"], c["ato_seq"], c["id_pje"], c["ato_tipo"], c["titulo"],
          c["data"], c["volume"], c["pagina"], c["parte"], c["chars"], c["hash"], c["texto"], agora)
         for c in chunks])
    con.commit()
    stats = {"chunks": len(chunks), "vetores": 0, "seg_embed": 0.0}
    if sem_vetor:
        con.close()
        return stats
    db = R.abrir_lance(banco)
    tbl = R.tabela_lance(db)
    try:
        tbl.delete(f"colecao = '{colecao}'")
    except Exception:
        pass
    t0 = time.time()
    for i in range(0, len(chunks), lote):
        grupo = chunks[i:i + lote]
        vecs = R.embed([c["texto"] for c in grupo])
        tbl.add([{
            "chunk_id": c["chunk_id"], "colecao": c["colecao"], "ato_seq": c["ato_seq"],
            "id_pje": c["id_pje"], "ato_tipo": c["ato_tipo"], "data": c["data"], "volume": c["volume"],
            "pagina": c["pagina"], "parte": c["parte"], "vector": v,
        } for c, v in zip(grupo, vecs)])
        stats["vetores"] += len(grupo)
        if not quiet and (i // lote) % 10 == 0:
            el = time.time() - t0
            rate = stats["vetores"] / el if el else 0
            print(f"  embed {stats['vetores']}/{len(chunks)}  {rate:.1f} chunks/s  "
                  f"faltam ~{(len(chunks) - stats['vetores']) / rate / 60 if rate else 0:.0f} min", flush=True)
    stats["seg_embed"] = time.time() - t0
    con.close()
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("banco", choices=sorted(R.BANCOS))
    ap.add_argument("--extracted", help="pasta extracted/ do fatiar_atos.py (banco casos)")
    ap.add_argument("--cnj", help="colecao = CNJ (padrao: le do atos.jsonl)")
    ap.add_argument("--pasta", help="pasta de .md de um corpus publico (banco vault)")
    ap.add_argument("--colecao", help="nome da colecao no banco vault")
    ap.add_argument("--sem-vetor", action="store_true", help="so FTS5, sem embeddings")
    ap.add_argument("--lote", type=int, default=16)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    chunks: list[dict] = []
    if a.banco == "casos":
        if not a.extracted:
            ap.error("--extracted e' obrigatorio para o banco casos")
        ext = Path(a.extracted)
        jsonl = ext / "atos.jsonl"
        if not jsonl.is_file():
            print(f"ERRO: nao achei {jsonl}", file=sys.stderr)
            return 2
        atos = [json.loads(l) for l in io.open(jsonl, encoding="utf-8")]
        colecao = a.cnj or (atos[0].get("cnj") if atos else None)
        if not colecao:
            ap.error("nao consegui descobrir o CNJ; passe --cnj")
        for meta in atos:
            md = io.open(ext / meta["arquivo"], encoding="utf-8").read()
            chunks += chunks_de_ato(md, meta, colecao, meta["arquivo"])
    else:
        if not (a.pasta and a.colecao):
            ap.error("--pasta e --colecao sao obrigatorios para o banco vault")
        colecao = a.colecao
        arquivos = sorted(Path(a.pasta).rglob("*.md"))
        for f in arquivos:
            md = io.open(f, encoding="utf-8", errors="replace").read()
            chunks += chunks_de_nota(md, colecao, str(f))
    if not a.quiet:
        print(f"{a.banco}/{colecao}: {len(chunks)} chunks ({sum(c['chars'] for c in chunks):,} chars) -> {R.CEREBRO_DIR}")
    st = gravar(a.banco, colecao, chunks, a.sem_vetor, a.lote, a.quiet)
    if not a.quiet:
        print(f"gravado: chunks={st['chunks']} vetores={st['vetores']} embed={st['seg_embed']:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
