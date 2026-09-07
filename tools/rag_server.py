#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag_server.py — servidor HTTP local, so stdlib, que expoe o pipeline para uma interface de chat
(Open WebUI ou qualquer cliente) sem que ela precise do venv nem dos caminhos (espec §5, fase 11).

Endpoints (JSON; so 127.0.0.1; sem autenticacao porque nao sai da maquina):
  GET  /saude                              -> {"ok": true, "bancos": [...], "colecoes": {...}}
  GET  /buscar?q=…&banco=casos&cnj=…&k=8&reranker=0  -> saida do buscar.py (com prefixo [ID | vol p. N | tipo | data])
  GET  /casos                              -> casos da area de trabalho (caso.json) e o que cada um ja tem
  GET  /caso/<cnj>/<arquivo>               -> linha-do-tempo.md, distill/prazos.md, distill/controversia.md … (texto)
  POST /validar  {"minuta": "...", "cnj": "...", "peca": "resposta-acusacao", "rito": "jecrim"}  -> resumo do gate
  POST /anonimizar {"cnj": "...", "texto": "..."} / POST /reverter {...}

Uso: .venv-rag314/Scripts/python tools/rag_server.py [--porta 8765]
(ou `python` de qualquer versao: rag_comum reexecuta no venv sozinho)
Regra de sigilo: escuta so em 127.0.0.1; nada do que responde e' pseudonimizado por padrao — quem
consome (a UI) decide se aplica /anonimizar antes de mandar a nuvem.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rag_comum as R  # noqa: E402  (bootstrap do venv acontece aqui)
import buscar as B  # noqa: E402
from anonimizar import Anonimizador  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

CASOS = R.CEREBRO_DIR / "casos"
TOOLS = Path(__file__).parent


def _casos() -> list[dict]:
    out = []
    for cj in sorted(CASOS.glob("*/caso.json")):
        try:
            c = json.loads(cj.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        d = cj.parent
        out.append({"cnj": c.get("cnj", d.name), "comarca": c.get("comarca"), "dispositivo": c.get("dispositivo"),
                    "tem": [p for p in ("extracted/atos.jsonl", "linha-do-tempo.md", "distill/prazos.md", "distill/prescricao.md",
                                        "distill/controversia.md", "distill/nulidades.md", "extracted/.indexado") if (d / p).exists()]})
    return out


def _validar(body: dict) -> dict:
    import subprocess
    with tempfile.TemporaryDirectory() as td:
        m = Path(td) / "minuta.md"
        m.write_text(body.get("minuta", ""), encoding="utf-8")
        cmd = [sys.executable, str(TOOLS / "validar_minuta.py"), str(m), "--peca", body.get("peca", "outra"),
               "--rito", body.get("rito", "ordinario"), "--saida-dir", td]
        if body.get("rapido"):
            cmd.append("--sem-corpora")
        cnj = body.get("cnj")
        if cnj and (CASOS / cnj / "extracted" / "atos.jsonl").exists():
            cmd += ["--atos", str(CASOS / cnj / "extracted" / "atos.jsonl")]
        if body.get("intimacao"):
            cmd += ["--intimacao", body["intimacao"]]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        res = {"stdout": r.stdout[-3000:], "exit": r.returncode}
        for nome in ("minuta.validacao.json",):
            p = Path(td) / nome
            if p.exists():
                res["resumo"] = json.loads(p.read_text(encoding="utf-8"))
        for nome in ("minuta.validada.md", "minuta.validacao-fontes.md", "minuta.validacao-processual.md"):
            p = Path(td) / nome
            if p.exists():
                res[nome] = p.read_text(encoding="utf-8")
        return res


class H(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _texto(self, s: str, code=200):
        data = s.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # sem texto de consulta no log
        sys.stderr.write(f"{self.address_string()} {self.command} {self.path.split('?')[0]}\n")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/saude":
                bancos = [p.name for p in R.CEREBRO_DIR.glob("*.db")]
                col = {}
                for b in ("casos", "vault"):
                    try:
                        con = R.abrir_sqlite(b)
                        col[b] = {r[0]: r[1] for r in con.execute("SELECT colecao, COUNT(*) FROM chunks GROUP BY colecao")}
                        con.close()
                    except Exception as e:  # noqa: BLE001
                        col[b] = str(e)
                return self._json({"ok": True, "cerebro_dir": str(R.CEREBRO_DIR), "bancos": bancos, "colecoes": col})
            if u.path == "/buscar":
                if not q.get("q"):
                    return self._json({"erro": "faltou q"}, 400)
                res = B.buscar(q.get("banco", "casos"), q["q"], q.get("cnj") or q.get("colecao"), q.get("tipo"),
                               int(q.get("k", 8)), int(q.get("n", 15)), q.get("so_fts") == "1", q.get("reranker", "0") != "1")
                return self._json(res)
            if u.path == "/casos":
                return self._json(_casos())
            if u.path.startswith("/caso/"):
                partes = u.path.split("/", 3)
                if len(partes) < 4:
                    return self._json({"erro": "use /caso/<cnj>/<arquivo>"}, 400)
                cnj, arq = partes[2], urllib.parse.unquote(partes[3])
                p = (CASOS / cnj / arq).resolve()
                if not str(p).startswith(str((CASOS / cnj).resolve())) or not p.is_file():
                    return self._json({"erro": "arquivo não encontrado"}, 404)
                return self._texto(p.read_text(encoding="utf-8", errors="replace"))
            return self._json({"erro": "rota desconhecida", "rotas": ["/saude", "/buscar", "/casos", "/caso/<cnj>/<arquivo>", "POST /validar", "POST /anonimizar", "POST /reverter"]}, 404)
        except Exception as e:  # noqa: BLE001
            return self._json({"erro": str(e)}, 500)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        bruto = self.rfile.read(n) or b"{}"
        try:
            try:
                body = json.loads(bruto.decode("utf-8"))
            except UnicodeDecodeError:
                # cliente mandou no codepage do Windows (curl em Git Bash): aceita cp1252
                body = json.loads(bruto.decode("cp1252", errors="replace"))
        except ValueError as e:
            return self._json({"erro": f"JSON inválido: {e}"}, 400)
        try:
            if self.path == "/validar":
                return self._json(_validar(body))
            if self.path in ("/anonimizar", "/reverter"):
                if not body.get("cnj"):
                    return self._json({"erro": "faltou cnj"}, 400)
                an = Anonimizador(body["cnj"])
                out = an.anonimizar(body.get("texto", "")) if self.path == "/anonimizar" else an.reverter(body.get("texto", ""))
                an.salvar()
                return self._json({"texto": out, "mapa": an.resumo() if body.get("mapa") else None})
            return self._json({"erro": "rota desconhecida"}, 404)
        except Exception as e:  # noqa: BLE001
            return self._json({"erro": str(e)}, 500)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=8765)
    a = ap.parse_args(argv)
    srv = ThreadingHTTPServer(("127.0.0.1", a.porta), H)
    print(f"rag_server em http://127.0.0.1:{a.porta}  (cerebro_dir={R.CEREBRO_DIR})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
