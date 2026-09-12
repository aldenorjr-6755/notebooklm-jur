#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nuvem_atos.py — consome `distill/para_nuvem.json` e distila na NUVEM os atos grandes demais para o
modelo local (espec §3.3, fase 7 — que estava especificada e nao implementada ate 09/09/2026).

Onde ele encaixa: `distilar_atos.py` separa a fila em locais (<= --ate tokens) e nuvem (o resto),
mas so ESCREVE a lista. Este script le essa lista, chama `llm_nuvem.chamar` com a MESMA instrucao e
o MESMO schema do distilador local, e grava o resultado no MESMO cache
(`distill/llm/<distilador>/<seq>.json`). Depois basta:

    python distilar_atos.py <atos.jsonl> --distiladores <...> --so-relatorio

para o relatorio .md sair com os atos locais E os de nuvem juntos.

Sigilo: `llm_nuvem.chamar` pseudonimiza ANTES de sair (nomes, CPF, telefone, placa, IMEI) e reverte
na volta; o log guarda hash, nunca texto. Pseudonimizar NAO e' anonimizar o conteudo: o teor do ato
sai da maquina. Autos sob segredo exigem decisao do advogado, nao do script.

Cada entrada de cache gravada aqui leva `"origem": "nuvem"` e o modelo real — o relatorio aceita a
entrada sem exigir que o modelo seja o local, e a proveniencia fica registrada.

Uso:
  python nuvem_atos.py <extracted>/atos.jsonl [--tier barato] [--limite N] [--so-distilador nulidades]
                       [--dry-run] [--refazer]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import distilar_atos as D  # noqa: E402
import llm_nuvem as N  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("atos")
    ap.add_argument("--tier", default="barato")
    ap.add_argument("--limite", type=int, help="processa so os N primeiros (teste)")
    ap.add_argument("--so-distilador", help="filtra por distilador (controversia, nulidades, prisao, dosimetria)")
    ap.add_argument("--dry-run", action="store_true", help="mostra o que sairia, sem chamar a API")
    ap.add_argument("--refazer", action="store_true", help="reprocessa mesmo se ja houver cache valido")
    a = ap.parse_args(argv)

    atos_p = Path(a.atos)
    extracted = atos_p.parent
    distill = extracted.parent / "distill"
    fila_p = distill / "para_nuvem.json"
    if not fila_p.is_file():
        print(f"ERRO: nao achei {fila_p}. Rode distilar_atos.py antes.", file=sys.stderr)
        return 2

    por_seq = {int(x["seq"]): x for x in (json.loads(l) for l in io.open(atos_p, encoding="utf-8"))}
    cnj = next(iter(por_seq.values())).get("cnj") if por_seq else None
    fila = json.loads(io.open(fila_p, encoding="utf-8").read())
    if a.so_distilador:
        fila = [i for i in fila if i.get("distilador") == a.so_distilador]
    if a.limite:
        fila = fila[:a.limite]
    if not fila:
        print("fila vazia — nada a fazer")
        return 0

    print(f"{cnj}: {len(fila)} ato(s) na fila de nuvem (tier={a.tier})", flush=True)
    feitos = pulados = falhos = 0
    custo = 0.0
    t_total = time.time()
    for i, item in enumerate(fila, 1):
        d, sk, seq = item["distilador"], item["schema"], int(item["seq"])
        ato = por_seq.get(seq)
        if not ato:
            print(f"  [{i}/{len(fila)}] seq {seq}: ato nao encontrado no jsonl — pulado", flush=True)
            falhos += 1
            continue
        pasta = distill / "llm" / d
        pasta.mkdir(parents=True, exist_ok=True)
        cache = pasta / f"{seq:04d}.json"
        if cache.is_file() and not a.refazer:
            try:
                prev = json.loads(io.open(cache, encoding="utf-8").read())
                if (prev.get("hash") == ato.get("hash_sha256")
                        and "saida" in prev and "_erro" not in prev["saida"]
                        and set(D.SCHEMAS[sk]["required"]) <= set(prev["saida"])):
                    pulados += 1
                    continue
            except Exception:
                pass
        texto = D.corpo_do_ato(extracted / ato["arquivo"])
        instrucao = D.PROMPT_BASE + D.INSTRUCOES[sk]
        t0 = time.time()
        try:
            r = N.chamar(a.tier, instrucao, texto, cnj=cnj, schema=D.SCHEMAS[sk], dry_run=a.dry_run)
        except Exception as e:
            print(f"  [{i}/{len(fila)}] {d}/{sk} seq {seq}: FALHOU — {type(e).__name__}: {str(e)[:120]}",
                  flush=True)
            falhos += 1
            continue
        seg = time.time() - t0
        if a.dry_run:
            print(f"  [{i}/{len(fila)}] {d}/{sk} seq {seq} ({ato.get('tipo')}): "
                  f"{item.get('tokens_estimados')} tok -> {r.get('modelo')} (dry-run)", flush=True)
            continue
        saida = r.get("resposta")
        if isinstance(saida, str):
            try:
                saida = json.loads(saida)
            except Exception:
                saida = {"_erro": "resposta nao e' JSON", "_bruto": saida[:2000]}
        ok = isinstance(saida, dict) and "_erro" not in saida and set(D.SCHEMAS[sk]["required"]) <= set(saida)
        io.open(cache, "w", encoding="utf-8", newline="\n").write(json.dumps({
            "hash": ato.get("hash_sha256"), "modelo": r.get("modelo"), "origem": "nuvem",
            "saida": saida,
            "metricas": {"seg": round(seg, 1), "tokens_in": r.get("tokens_in"),
                         "tokens_out": r.get("tokens_out"), "custo_usd": r.get("custo")},
        }, ensure_ascii=False, indent=1))
        custo += float(r.get("custo") or 0)
        feitos += 1 if ok else 0
        falhos += 0 if ok else 1
        print(f"  [{i}/{len(fila)}] {d}/{sk} seq {seq} ({ato.get('tipo')}): {seg:.1f}s "
              f"{r.get('tokens_in')}→{r.get('tokens_out')} tok US$ {r.get('custo') or 0:.4f}"
              f"{'' if ok else '  ⚠ saida fora do schema'}", flush=True)

    print(f"nuvem: {feitos} ok · {pulados} em cache · {falhos} falha(s) · "
          f"US$ {custo:.4f} · {(time.time() - t_total) / 60:.1f} min", flush=True)
    print("agora rode `distilar_atos.py ... --so-relatorio` para remontar os .md com local + nuvem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
