#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_minuta.py — gate pos-inferencia da espec (§4): roda o validador de FONTES e o validador
PROCESSUAL e emite o status unico. So APROVADO segue para o .docx.

  minuta.md ──► validador_fontes.py ──► minuta.validada.md (marcadores inline)
            ├─► validador_processual.py
            └─► citacoes_para_verificar.json ──► agente `verificador-citacoes` (semantico; roda no
                Claude Code, em contexto isolado — este script so prepara a lista)

Uso:
  python validar_minuta.py minuta.md --atos <extracted>/atos.jsonl --peca resposta-acusacao [--rito jecrim]
                           [--intimacao AAAA-MM-DD] [--contexto busca.json] [--saida-dir pasta]
Codigo de saida: 0 APROVADO, 1 ALERTA.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validador_fontes as VF  # noqa: E402
import validador_processual as VP  # noqa: E402
from datetime import date  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("minuta")
    ap.add_argument("--atos")
    ap.add_argument("--contexto", action="append", default=[])
    ap.add_argument("--peca", default="outra", choices=sorted(VP.PRAZOS_PECA))
    ap.add_argument("--rito", default="ordinario", choices=["ordinario", "sumario", "jecrim"])
    ap.add_argument("--intimacao")
    ap.add_argument("--dias", type=int)
    ap.add_argument("--hoje")
    ap.add_argument("--sem-corpora", action="store_true")
    ap.add_argument("--saida-dir")
    a = ap.parse_args(argv)
    p = Path(a.minuta)
    dest = Path(a.saida_dir) if a.saida_dir else p.parent
    dest.mkdir(parents=True, exist_ok=True)
    texto = io.open(p, encoding="utf-8").read()

    ctx = VF.Contexto(a.atos, a.contexto)
    fontes = [VF.verificar(c, ctx, texto, not a.sem_corpora) for c in VF.citacoes(texto)]
    io.open(dest / (p.stem + ".validada.md"), "w", encoding="utf-8", newline="\n").write(VF.anotar(texto, fontes))
    io.open(dest / (p.stem + ".validacao-fontes.md"), "w", encoding="utf-8", newline="\n").write(VF.relatorio(fontes, a.minuta))
    pend = [{"linha": r["linha"], "tipo": r["tipo"], "citacao": r["texto"], "status": r["status"], "detalhe": r.get("detalhe")}
            for r in fontes if r["tipo"] in ("PRECEDENTE", "SUMULA", "TEMA", "INFORMATIVO")]
    io.open(dest / (p.stem + ".citacoes_para_verificar.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(pend, ensure_ascii=False, indent=1))

    proc = VP.validar(texto, a.peca, a.rito, a.intimacao, a.dias, date.fromisoformat(a.hoje) if a.hoje else date.today())
    io.open(dest / (p.stem + ".validacao-processual.md"), "w", encoding="utf-8", newline="\n").write(VP.relatorio(proc, a.minuta))

    n_f = sum(1 for r in fontes if r["status"] != "OK")
    n_p = sum(1 for x in proc["alertas"] if x["grau"] == "alto")
    status = "APROVADO" if n_f == 0 and n_p == 0 else f"ALERTA (fontes: {n_f}; processual alto: {n_p})"
    resumo = {"minuta": str(p), "status": status, "fontes": {"citacoes": len(fontes), "alertas": n_f},
              "processual": {"status": proc["status"], "alertas_alto": n_p, "alertas": len(proc["alertas"])},
              "para_verificador_citacoes": len(pend),
              "arquivos": [str(dest / (p.stem + s)) for s in (".validada.md", ".validacao-fontes.md", ".validacao-processual.md", ".citacoes_para_verificar.json")]}
    io.open(dest / (p.stem + ".validacao.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(resumo, ensure_ascii=False, indent=1))
    print(f"STATUS: {status}")
    print(f"  fontes: {len(fontes)} citações, {n_f} com alerta → {dest / (p.stem + '.validacao-fontes.md')}")
    print(f"  processual: {proc['status']} ({len(proc['alertas'])} alertas) → {dest / (p.stem + '.validacao-processual.md')}")
    print(f"  para o verificador-citacoes: {len(pend)} citações → {dest / (p.stem + '.citacoes_para_verificar.json')}")
    print(f"  minuta anotada: {dest / (p.stem + '.validada.md')}")
    return 0 if status == "APROVADO" else 1


if __name__ == "__main__":
    sys.exit(main())
