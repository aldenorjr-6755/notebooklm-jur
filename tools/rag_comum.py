# -*- coding: utf-8 -*-
"""
rag_comum.py — configuracao e utilitarios partilhados por indexar.py e buscar.py.

Dois bancos, por regra de sigilo (espec §3.2.2):
  * CASOS  -> atos processuais. Fica FORA do OneDrive: %LOCALAPPDATA%\\cerebro\\casos.{db,lance}
  * VAULT  -> corpora publicos (legislacao, jurisprudencia, doutrina, modelos anonimizados)
              %LOCALAPPDATA%\\cerebro\\vault.{db,lance}
Sobrescreva a pasta com a variavel de ambiente CEREBRO_DIR.

Executar SEMPRE com o venv `~/.notebooklm/.venv-rag314` (lancedb, torch CPU, sentence-transformers).
Embedding: bge-m3 via Ollama (http://127.0.0.1:11434), 1024 dims.
"""
from __future__ import annotations

import json
import os
import sys as _sys


def _garantir_venv() -> None:
    """indexar/buscar precisam de lancedb (+ torch para o reranker). Se o interprete atual nao
    os tem, reexecuta o MESMO script com o Python do venv RAG, para que o comando do vault possa
    ser `python .claude/tools/pipeline/buscar.py …` sem citar o venv (norma Classe A)."""
    try:
        import lancedb  # noqa: F401
        return
    except ImportError:
        pass
    cands = [os.environ.get("CEREBRO_PY", ""),
             os.path.join(os.path.expanduser("~"), ".notebooklm", ".venv-rag314", "Scripts", "python.exe"),
             os.path.join(os.path.expanduser("~"), ".notebooklm", ".venv-rag314", "bin", "python")]
    for py in cands:
        if py and os.path.isfile(py) and os.path.abspath(py) != os.path.abspath(_sys.executable):
            # subprocess, nao os.execv: no Windows o execv junta os argumentos sem aspas e
            # "acordo de nao persecucao penal" vira cinco argumentos
            import subprocess
            raise SystemExit(subprocess.run([py] + _sys.argv).returncode)
    raise SystemExit("lancedb nao instalado e venv RAG nao encontrado: crie ~/.notebooklm/.venv-rag314 "
                     "(python.org 3.14 + pip install lancedb sentence-transformers torch --index-url https://download.pytorch.org/whl/cpu) "
                     "ou aponte CEREBRO_PY para um Python que tenha lancedb")


_garantir_venv()
import re
import sqlite3
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA = os.environ.get("OLLAMA_HOST_URL", "http://127.0.0.1:11434")
MODELO_EMBED = os.environ.get("CEREBRO_EMBED", "bge-m3")
DIMS = 1024
MODELO_RERANK = os.environ.get("CEREBRO_RERANK", "BAAI/bge-reranker-v2-m3")

CEREBRO_DIR = Path(os.environ.get("CEREBRO_DIR") or
                   Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "cerebro")
BANCOS = {"casos": "casos", "vault": "vault"}

# chunk = pagina do ato; pagina muito longa e' repartida em blocos de ~MAX_CHARS
MAX_CHARS = 6000        # ~1.7k tokens; bge-m3 aceita 8k tokens, mas o reranker corta em 512
SOBREPOSICAO = 300


def caminhos(banco: str) -> tuple[Path, Path]:
    if banco not in BANCOS:
        raise ValueError(f"banco deve ser um de {sorted(BANCOS)}")
    CEREBRO_DIR.mkdir(parents=True, exist_ok=True)
    return CEREBRO_DIR / f"{banco}.db", CEREBRO_DIR / f"{banco}.lance"


# --------------------------------------------------------------------------
# SQLite: metadados + FTS5
# --------------------------------------------------------------------------
DDL = """
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id     TEXT PRIMARY KEY,
  colecao      TEXT NOT NULL,          -- cnj (casos) ou nome do corpus (vault)
  fonte        TEXT,                   -- arquivo de origem
  ato_seq      INTEGER,
  id_pje       TEXT,
  ato_tipo     TEXT,
  titulo       TEXT,
  data         TEXT,                   -- ISO
  volume       TEXT,
  pagina       INTEGER,
  parte        INTEGER DEFAULT 0,      -- 0 = pagina inteira; n>0 = bloco n da pagina
  chars        INTEGER,
  hash         TEXT,
  texto        TEXT NOT NULL,
  indexado_em  REAL
);
CREATE INDEX IF NOT EXISTS ix_chunks_colecao ON chunks(colecao);
CREATE INDEX IF NOT EXISTS ix_chunks_tipo ON chunks(colecao, ato_tipo);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  texto, titulo, chunk_id UNINDEXED,
  tokenize = 'unicode61 remove_diacritics 2',
  content = 'chunks', content_rowid = 'rowid'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, texto, titulo, chunk_id) VALUES (new.rowid, new.texto, new.titulo, new.chunk_id);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, texto, titulo, chunk_id) VALUES ('delete', old.rowid, old.texto, old.titulo, old.chunk_id);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, texto, titulo, chunk_id) VALUES ('delete', old.rowid, old.texto, old.titulo, old.chunk_id);
  INSERT INTO chunks_fts(rowid, texto, titulo, chunk_id) VALUES (new.rowid, new.texto, new.titulo, new.chunk_id);
END;
"""


def abrir_sqlite(banco: str) -> sqlite3.Connection:
    db, _ = caminhos(banco)
    con = sqlite3.connect(str(db))
    con.executescript(DDL)
    con.row_factory = sqlite3.Row
    return con


# --------------------------------------------------------------------------
# LanceDB: vetores
# --------------------------------------------------------------------------
def abrir_lance(banco: str):
    import lancedb  # importado aqui para que buscar --so-fts funcione sem lancedb
    _, lance = caminhos(banco)
    return lancedb.connect(str(lance))


def tabela_lance(db, criar_se_faltar: bool = True):
    import pyarrow as pa
    nome = "chunks"
    if nome in db.table_names():
        return db.open_table(nome)
    if not criar_se_faltar:
        return None
    schema = pa.schema([
        pa.field("chunk_id", pa.string()),
        pa.field("colecao", pa.string()),
        pa.field("ato_seq", pa.int32()),
        pa.field("id_pje", pa.string()),
        pa.field("ato_tipo", pa.string()),
        pa.field("data", pa.string()),
        pa.field("volume", pa.string()),
        pa.field("pagina", pa.int32()),
        pa.field("parte", pa.int32()),
        pa.field("vector", pa.list_(pa.float32(), DIMS)),
    ])
    return db.create_table(nome, schema=schema)


# --------------------------------------------------------------------------
# Embedding via Ollama
# --------------------------------------------------------------------------
def embed(textos: list[str], tentativas: int = 3, timeout: int = 600) -> list[list[float]]:
    body = json.dumps({"model": MODELO_EMBED, "input": textos, "truncate": True}).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/embed", data=body,
                                 headers={"Content-Type": "application/json"})
    erro = None
    for _ in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            vecs = d["embeddings"]
            if len(vecs) != len(textos) or (vecs and len(vecs[0]) != DIMS):
                raise RuntimeError(f"embedding com forma inesperada: {len(vecs)}x{len(vecs[0]) if vecs else 0}")
            return vecs
        except (urllib.error.URLError, RuntimeError, KeyError) as e:
            erro = e
            time.sleep(2)
    raise RuntimeError(f"Ollama /api/embed falhou ({MODELO_EMBED}): {erro}")


# --------------------------------------------------------------------------
# Texto
# --------------------------------------------------------------------------
def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def repartir(texto: str, max_chars: int = MAX_CHARS, sobre: int = SOBREPOSICAO) -> list[str]:
    """Reparte uma pagina longa em blocos por paragrafo (so quando passa de max_chars)."""
    if len(texto) <= max_chars:
        return [texto]
    blocos, atual = [], ""
    for par in re.split(r"\n\s*\n", texto):
        if len(atual) + len(par) + 2 > max_chars and atual:
            blocos.append(atual.strip())
            atual = atual[-sobre:] + "\n\n" + par
        else:
            atual = (atual + "\n\n" + par) if atual else par
    if atual.strip():
        blocos.append(atual.strip())
    return blocos


def consulta_fts(q: str) -> str:
    """Transforma a pergunta em consulta FTS5 segura: frases entre aspas viram frases;
    o resto vira termos AND. Numeros com pontos (Num., CNJ, artigo) viram frase."""
    frases = re.findall(r'"([^"]+)"', q)
    resto = re.sub(r'"[^"]+"', " ", q)
    termos = []
    for f in frases:
        termos.append('"' + f.replace('"', "") + '"')
    for tok in re.findall(r"[\w\.\-º°ª/]+", resto, flags=re.UNICODE):
        t = tok.strip(".-/")
        if len(t) < 2 or t.lower() in STOP:
            continue
        if re.search(r"\d", t):
            termos.append('"' + t + '"')
        else:
            termos.append('"' + t + '"')
    return " AND ".join(termos) if termos else '""'


STOP = {"de", "da", "do", "das", "dos", "a", "o", "as", "os", "e", "em", "no", "na", "nos", "nas",
        "um", "uma", "por", "para", "com", "sem", "que", "se", "ao", "à", "às", "aos", "ou", "sobre",
        "qual", "quais", "foi", "ser", "há", "ha"}
