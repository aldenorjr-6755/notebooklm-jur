#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_nuvem.py — cliente de LLM em nuvem por TIER (espec §5.3), com anonimizacao antes de sair e
reversao ao voltar (§5.4), politica ZDR e log SEM texto (§6).

Fluxo de uma chamada:
  texto -> Anonimizador(cnj).anonimizar -> [tier -> modelo 1, 2, ... ate um responder]
        -> resposta -> Anonimizador.reverter -> chamador
  log: ~/.notebooklm/relatorios/llm-log.jsonl {ts, cnj, tier, provedor, modelo, tokens_in/out, custo,
       sha256 do prompt ANONIMIZADO, seg} — nunca o texto.

Chaves so por variavel de ambiente (OPENROUTER_API_KEY, FCC_PROXY_TOKEN, MARITACA_API_KEY).
Sem chave, --dry-run mostra o prompt anonimizado, o modelo que seria usado e o custo estimado.

Uso:
  python llm_nuvem.py --tier barato --cnj <CNJ> --arquivo ato.md --instrucao "Extraia ..." [--schema schema.json] [--dry-run]
  python llm_nuvem.py --tier forte  --cnj <CNJ> --prompt "..." --dry-run
Como biblioteca: from llm_nuvem import chamar; chamar("barato", instrucao, texto, cnj=..., schema=...)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from anonimizar import Anonimizador  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

CONFIG = json.loads((Path(__file__).parent / "config_llm.json").read_text(encoding="utf-8"))
LOG = Path(os.path.expanduser(CONFIG.get("log", "~/.notebooklm/relatorios/llm-log.jsonl")))


class SemChave(RuntimeError):
    pass


def _tokens(s: str) -> int:
    return max(1, len(s) // 3)


def _custo(modelo: str, tin: int, tout: int) -> float | None:
    p = CONFIG["precos_usd_por_milhao_tokens_estimados"].get(modelo)
    return round((tin * p["in"] + tout * p["out"]) / 1e6, 4) if p else None


def _registrar(reg: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


def _post(provedor: dict, chave: str, body: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(provedor["base_url"].rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {chave}"} | provedor.get("headers", {}))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def chamar(tier: str, instrucao: str, texto: str, cnj: str | None = None, schema: dict | None = None,
           dry_run: bool = False, anonimizar: bool = True, max_tokens: int | None = None) -> dict:
    """-> {"resposta": str|dict, "modelo": ..., "tokens_in": ..., "tokens_out": ..., "custo": ..., "dry_run": bool}"""
    t = CONFIG["tiers"][tier]
    an = Anonimizador(cnj) if (cnj and anonimizar) else None
    texto_env = an.anonimizar(texto) if an else texto
    if an:
        an.salvar()
    sistema = ("Você é assistente de um advogado criminalista brasileiro. Use somente o material fornecido; não invente fato, "
               "norma, precedente ou data; marque [VERIFICAR] o que não puder sustentar no material. Os tokens PESSOA_n, CPF_n, "
               "LOCAL_n são pseudônimos: mantenha-os exatamente como estão na resposta.")
    mensagens = [{"role": "system", "content": sistema},
                 {"role": "user", "content": instrucao.strip() + "\n\n=== MATERIAL ===\n" + texto_env + "\n=== FIM ==="}]
    h = hashlib.sha256((instrucao + "\n" + texto_env).encode("utf-8")).hexdigest()[:24]
    tin = _tokens(instrucao) + _tokens(texto_env) + 120
    erros = []
    for m in t["modelos"]:
        prov = CONFIG["provedores"][m["provedor"]]
        chave = os.environ.get(prov["chave_env"], "")
        modelo = m["modelo"]
        if dry_run:
            est_out = min(max_tokens or t["max_tokens"], 1500)
            return {"dry_run": True, "modelo": modelo, "provedor": m["provedor"], "tem_chave": bool(chave),
                    "tokens_in_estimados": tin, "custo_estimado_usd": _custo(modelo, tin, est_out),
                    "prompt_anonimizado": mensagens[1]["content"], "hash": h,
                    "mapa": an.resumo() if an else "(sem anonimização)"}
        if not chave:
            erros.append(f"{m['provedor']}: sem {prov['chave_env']} no ambiente")
            continue
        body = {"model": modelo, "messages": mensagens, "temperature": t["temperatura"],
                "max_tokens": max_tokens or t["max_tokens"]} | prov.get("politica", {})
        if schema:
            # Nem todo provedor aceita structured output por json_schema. A API direta da DeepSeek,
            # por exemplo, so tem {"type": "json_object"} — mandar json_schema devolve HTTP 400.
            # Quando o provedor nao suporta, o schema vai NO PROMPT e o parse fica por conta do
            # chamador (que ja valida required antes de aceitar a saida).
            if prov.get("suporta_json_schema", True):
                body["response_format"] = {"type": "json_schema",
                                           "json_schema": {"name": "saida", "strict": True, "schema": schema}}
            else:
                body["response_format"] = {"type": "json_object"}
                body["messages"] = [mensagens[0], {
                    "role": "user",
                    "content": mensagens[1]["content"] +
                    "\n\n=== FORMATO OBRIGATORIO DA RESPOSTA ===\nResponda SOMENTE com um objeto JSON "
                    "valido que obedeca exatamente a este JSON Schema, sem texto fora do JSON:\n"
                    + json.dumps(schema, ensure_ascii=False)}]
        if m["provedor"] == "openrouter":
            body["usage"] = {"include": True}
        t0 = time.time()
        try:
            d = _post(prov, chave, body)
        except urllib.error.HTTPError as e:
            erros.append(f"{modelo}: HTTP {e.code} {e.read()[:200]!r}")
            continue
        except (urllib.error.URLError, TimeoutError) as e:
            erros.append(f"{modelo}: {e}")
            continue
        conteudo = (d.get("choices") or [{}])[0].get("message", {}).get("content")
        if not conteudo:
            # modelo devolveu content vazio/null (acontece em recusa, corte por filtro ou tool_call
            # inesperado). Sem esta guarda o None chegava ao reverter() e virava
            # "TypeError: expected string or bytes-like object" — visto em 09/09/2026.
            erros.append(f"{modelo}: resposta sem conteudo (finish_reason="
                         f"{(d.get('choices') or [{}])[0].get('finish_reason')})")
            continue
        uso = d.get("usage", {}) or {}
        reg = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "cnj": cnj, "tier": tier, "provedor": m["provedor"], "modelo": modelo,
               "tokens_in": uso.get("prompt_tokens"), "tokens_out": uso.get("completion_tokens"),
               "custo_usd": uso.get("cost") or _custo(modelo, uso.get("prompt_tokens") or tin, uso.get("completion_tokens") or 0),
               "hash_prompt_anon": h, "seg": round(time.time() - t0, 1), "anonimizado": bool(an)}
        _registrar(reg)
        resposta = an.reverter(conteudo) if an else conteudo
        if schema:
            try:
                resposta = json.loads(resposta)
            except json.JSONDecodeError:
                resposta = {"_erro": "JSON inválido", "_bruto": resposta[:800]}
        return {"resposta": resposta, "dry_run": False} | reg
    if all("sem " in e for e in erros):
        raise SemChave("nenhum provedor do tier tem chave no ambiente: " + "; ".join(erros))
    raise RuntimeError("todos os modelos do tier falharam: " + "; ".join(erros))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", required=True, choices=sorted(CONFIG["tiers"]))
    ap.add_argument("--cnj")
    ap.add_argument("--arquivo", help="texto/ato a enviar (corpo após o frontmatter)")
    ap.add_argument("--prompt", help="texto direto em vez de --arquivo")
    ap.add_argument("--instrucao", default="Resuma o material em até 10 linhas, com as âncoras [ID | p.] de cada afirmação.")
    ap.add_argument("--schema", help="JSON schema para resposta estruturada")
    ap.add_argument("--sem-anonimizar", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mostrar-prompt", action="store_true")
    a = ap.parse_args(argv)
    if a.arquivo:
        md = io.open(a.arquivo, encoding="utf-8", errors="replace").read()
        texto = md.split("\n---\n", 1)[-1] if md.startswith("---") else md
    elif a.prompt:
        texto = a.prompt
    else:
        ap.error("--arquivo ou --prompt")
    schema = json.loads(Path(a.schema).read_text(encoding="utf-8")) if a.schema else None
    try:
        r = chamar(a.tier, a.instrucao, texto, a.cnj, schema, a.dry_run, not a.sem_anonimizar)
    except SemChave as e:
        print(f"SEM CHAVE: {e}\nUse --dry-run para ver o prompt anonimizado, ou defina a variável de ambiente.", file=sys.stderr)
        return 3
    if r.get("dry_run"):
        print(f"[dry-run] tier={a.tier} modelo={r['modelo']} ({r['provedor']}, chave {'presente' if r['tem_chave'] else 'AUSENTE'}) "
              f"tokens_in≈{r['tokens_in_estimados']} custo≈US$ {r['custo_estimado_usd']} hash={r['hash']}")
        print("--- mapa de pseudônimos ---\n" + r["mapa"])
        if a.mostrar_prompt:
            print("--- prompt anonimizado ---\n" + r["prompt_anonimizado"])
        else:
            print(f"--- prompt anonimizado ({len(r['prompt_anonimizado'])} chars; --mostrar-prompt para ver) ---\n" + r["prompt_anonimizado"][:600] + "…")
        return 0
    print(json.dumps(r, ensure_ascii=False, indent=1) if isinstance(r.get("resposta"), dict) else r["resposta"])
    print(f"\n[{r['modelo']} · in {r['tokens_in']} · out {r['tokens_out']} · US$ {r['custo_usd']} · {r['seg']}s · log {LOG}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
