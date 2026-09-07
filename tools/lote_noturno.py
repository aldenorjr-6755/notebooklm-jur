#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lote_noturno.py — roda o pipeline de autos em LOTE para todos os casos da area de trabalho
(espec §7, fase 10), idempotente e dentro de uma janela de tempo, e emite o RELATORIO DE CUSTO
por caso (tempo por etapa, tokens do modelo local, custo em nuvem do llm-log.jsonl).

Area de trabalho: %LOCALAPPDATA%\\cerebro\\casos\\<CNJ>\\ (ou CEREBRO_DIR). Cada caso tem um
`caso.json`:
  {"cnj": "…", "dispositivo": "lei9605:50", "fato": "2023-07-21", "comarca": "Itinga do Maranhão",
   "rito": "auto", "nomes": ["NOME|PAPEL"], "termos": ["Fazenda X"],
   "vault": "C:/…/Criminal/20-Casos/<CNJ>", "ativo": true}
Autos: `raw/*.md` (saida do pdf2md) — o lote NAO converte PDF (pdf2md e' interativo por causa do
OCR); converta antes.

Ordem (barato primeiro, caro depois; cada etapa so roda se a entrada mudou ou a saida falta):
  1. fatiar      raw/*.md mais novo que extracted/atos.jsonl
  2. cronologia  atos.jsonl mais novo que linha-do-tempo.md
  3. prazos      sempre (o "hoje" muda todo dia; e' barato)
  4. prescricao  se caso.json tem dispositivo+fato
  5. anonimizar + copiar para o vault (se `vault` definido): saidas pseudonimizadas
  --- a partir daqui so dentro da janela (--janela-min) e sem --sem-llm ---
  6. indexar     atos.jsonl mais novo que extracted/.indexado
  7. distilar    controversia (--ate 7000) e nulidades/prisao/dosimetria (--ate 5000); cache por hash
  8. anonimizar de novo (controversia.md etc.) e copiar

Uso:
  python lote_noturno.py [--casos CNJ1,CNJ2] [--janela-min 480] [--sem-llm] [--sem-indexar] [--sem-distilar]
                         [--so-relatorio] [--dry-run]
Relatorio: ~/.notebooklm/relatorios/custo-<AAAA-MM-DD>.md (+ .json) e lote-<AAAA-MM-DD>.log
Agendar (Windows, 02:00, so quando o usuario decidir):
  schtasks /Create /SC DAILY /ST 02:00 /TN "cerebro-lote-noturno" /TR "\"%USERPROFILE%\\.notebooklm\\LOTE_NOTURNO.bat\""
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

TOOLS = Path(__file__).resolve().parent
CEREBRO = Path(os.environ.get("CEREBRO_DIR") or Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "cerebro")
CASOS = CEREBRO / "casos"
RELATORIOS = Path.home() / ".notebooklm" / "relatorios"
LLM_LOG = RELATORIOS / "llm-log.jsonl"
PY = sys.executable

SAIDAS_VAULT = ["linha-do-tempo.md", "distill/prazos.md", "distill/prescricao.md", "distill/controversia.md",
                "distill/nulidades.md", "distill/prisao.md", "distill/dosimetria.md"]


def log(msg: str, arq=None):
    linha = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(linha, flush=True)
    if arq:
        arq.write(linha + "\n")
        arq.flush()


def mtime(p: Path) -> float:
    return p.stat().st_mtime if p.exists() else 0.0


def rodar(cmd: list[str], arq, dry: bool, timeout: int = 6 * 3600) -> tuple[int, float]:
    log("$ " + " ".join(f'"{c}"' if " " in c else c for c in cmd), arq)
    if dry:
        return 0, 0.0
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.stdout.strip():
        arq.write(r.stdout[-4000:] + "\n")
    if r.returncode not in (0, 1):
        log(f"  exit={r.returncode} stderr={r.stderr[-600:]}", arq)
    return r.returncode, time.time() - t


def carregar_casos(filtro: list[str] | None) -> list[dict]:
    out = []
    for cj in sorted(CASOS.glob("*/caso.json")):
        try:
            c = json.loads(cj.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"caso.json inválido em {cj.parent.name}: {e}", file=sys.stderr)
            continue
        c["_dir"] = cj.parent
        c.setdefault("cnj", cj.parent.name)
        if c.get("ativo", True) and (not filtro or c["cnj"] in filtro):
            out.append(c)
    return out


def anon_e_copiar(c: dict, arq, dry: bool, quais: list[str]) -> int:
    """Pseudonimiza as saidas e copia para 20-Casos/<CNJ>/ do vault (se definido)."""
    d = c["_dir"]
    if not c.get("vault"):
        return 0
    dest = Path(c["vault"])
    dest.mkdir(parents=True, exist_ok=True)
    base = [PY, str(TOOLS / "anonimizar.py"), "--cnj", c["cnj"]]
    capa = sorted((d / "extracted" / "atos").glob("0001_CAPA*.md"))
    den = sorted((d / "extracted" / "atos").glob("*_DENUNCIA*.md"))
    cad = base + (["--capa", str(capa[0])] if capa else []) + (["--denuncia", str(den[0])] if den else [])
    tmpn = tmpt = None
    if c.get("nomes"):
        tmpn = d / ".nomes.txt"
        tmpn.write_text("\n".join(c["nomes"]), encoding="utf-8")
        cad += ["--nomes", str(tmpn)]
    if c.get("termos"):
        tmpt = d / ".termos.txt"
        tmpt.write_text("\n".join(c["termos"]), encoding="utf-8")
        cad += ["--termos", str(tmpt)]
    rodar(cad, arq, dry)
    n = 0
    for rel in quais:
        src = d / rel
        if not src.exists():
            continue
        rodar(base + [str(src)], arq, dry)
        anon = src.with_suffix(".anon.md")
        if anon.exists() and not dry:
            shutil.copy2(anon, dest / Path(rel).name)
            n += 1
    return n


def processar(c: dict, a, arq, fim_janela: float) -> dict:
    d = c["_dir"]
    ext = d / "extracted"
    atos = ext / "atos.jsonl"
    met = {"cnj": c["cnj"], "etapas": {}, "avisos": []}

    def etapa(nome, cmd, cond=True, longa=False):
        if not cond:
            met["etapas"][nome] = {"pulada": True}
            return
        if longa and time.time() > fim_janela:
            met["etapas"][nome] = {"pulada": True, "motivo": "fora da janela"}
            met["avisos"].append(f"{nome}: fora da janela de tempo")
            return
        rc, seg = rodar(cmd, arq, a.dry_run)
        met["etapas"][nome] = {"exit": rc, "seg": round(seg)}

    raws = sorted((d / "raw").glob("*.md"))
    etapa("fatiar", [PY, str(TOOLS / "fatiar_atos.py")] + [str(r) for r in raws] + ["--cnj", c["cnj"], "--saida", str(ext), "--quiet"],
          cond=bool(raws) and max(mtime(r) for r in raws) > mtime(atos))
    if not atos.exists():
        met["avisos"].append("sem extracted/atos.jsonl (e sem raw/*.md para fatiar)")
        return met
    etapa("cronologia", [PY, str(TOOLS / "cronologia_atos.py"), str(atos), "--saida", str(d / "linha-do-tempo.md")],
          cond=mtime(atos) > mtime(d / "linha-do-tempo.md"))
    cmd = [PY, str(TOOLS / "prazo_cpp.py"), "--atos", str(atos), "--rito", c.get("rito", "auto")]
    if c.get("comarca"):
        cmd += ["--comarca", c["comarca"]]
    etapa("prazos", cmd)
    if c.get("dispositivo") and c.get("fato"):
        etapa("prescricao", [PY, str(TOOLS / "prescricao_cp.py"), "--dispositivo", c["dispositivo"], "--fato", c["fato"], "--atos", str(atos)])
    else:
        met["avisos"].append("prescrição não calculada: caso.json sem dispositivo/fato")
    met["etapas"]["copiar_vault_1"] = {"arquivos": anon_e_copiar(c, arq, a.dry_run, SAIDAS_VAULT[:3])}

    if a.sem_llm:
        # saidas dos distiladores ja existentes (rodada anterior) tambem vao para o vault
        met["etapas"]["copiar_vault_2"] = {"arquivos": anon_e_copiar(c, arq, a.dry_run, SAIDAS_VAULT[3:])}
        return met
    carimbo = ext / ".indexado"
    etapa("indexar", [PY, str(TOOLS / "indexar.py"), "casos", "--extracted", str(ext), "--quiet"],
          cond=not a.sem_indexar and mtime(atos) > mtime(carimbo), longa=True)
    if met["etapas"].get("indexar", {}).get("exit") == 0 and not a.dry_run:
        carimbo.write_text(datetime.now().isoformat(), encoding="utf-8")
    if not a.sem_distilar:
        etapa("distilar_controversia", [PY, str(TOOLS / "distilar_atos.py"), str(atos), "--distiladores", "controversia", "--ate", "7000"], longa=True)
        etapa("distilar_inventario", [PY, str(TOOLS / "distilar_atos.py"), str(atos), "--distiladores", "nulidades,prisao,dosimetria", "--ate", "5000",
                                      "--excluir-tipos", "CERTIDAO,CARTA PRECATORIA,INTIMACAO,MANDADO,CERTIDAO DE PUBLICACAO"], longa=True)
        met["etapas"]["copiar_vault_2"] = {"arquivos": anon_e_copiar(c, arq, a.dry_run, SAIDAS_VAULT[3:])}
    return met


# --------------------------------------------------------------------------
# Relatorio de custo
# --------------------------------------------------------------------------
def custo_local(d: Path) -> dict:
    tot = {"atos": 0, "prompt_tok": 0, "gerados": 0, "seg": 0, "trechos_ok": 0, "trechos": 0}
    for f in glob.glob(str(d / "distill" / "llm" / "*" / "*.json")):
        try:
            m = json.loads(Path(f).read_text(encoding="utf-8")).get("metricas", {})
        except json.JSONDecodeError:
            continue
        tot["atos"] += 1
        tot["prompt_tok"] += m.get("prompt_tokens") or 0
        tot["gerados"] += m.get("gerados") or 0
        tot["seg"] += m.get("seg_wall") or 0
        tot["trechos_ok"] += m.get("trechos_localizados") or 0
        tot["trechos"] += m.get("trechos_total") or 0
    return tot


def custo_nuvem(cnj: str, desde: str | None) -> dict:
    tot = {"chamadas": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0, "modelos": {}}
    if not LLM_LOG.exists():
        return tot
    for l in io.open(LLM_LOG, encoding="utf-8"):
        try:
            r = json.loads(l)
        except json.JSONDecodeError:
            continue
        if r.get("cnj") != cnj or (desde and (r.get("ts") or "") < desde):
            continue
        tot["chamadas"] += 1
        tot["tokens_in"] += r.get("tokens_in") or 0
        tot["tokens_out"] += r.get("tokens_out") or 0
        tot["usd"] += float(r.get("custo_usd") or 0)
        tot["modelos"][r.get("modelo")] = tot["modelos"].get(r.get("modelo"), 0) + 1
    tot["usd"] = round(tot["usd"], 4)
    return tot


def relatorio(mets: list[dict], casos: list[dict], hoje: str, desde: str | None) -> tuple[str, dict]:
    por_cnj = {m["cnj"]: m for m in mets}
    L = [f"# Custo por caso — lote de {hoje}", "",
         f"> Tempo por etapa medido nesta rodada; tokens do modelo local somados do cache `distill/llm/`; "
         f"custo em nuvem lido de `relatorios/llm-log.jsonl`{' desde ' + desde if desde else ''}.", "",
         "| caso | atos | etapas rodadas (seg) | LLM local: atos · tokens in/out · min · trechos ok | nuvem: chamadas · tokens · US$ | avisos |",
         "|---|---|---|---|---|---|"]
    tot_local_min = tot_usd = 0.0
    dados = []
    for c in casos:
        d = c["_dir"]
        m = por_cnj.get(c["cnj"], {"etapas": {}, "avisos": []})
        n_atos = sum(1 for _ in io.open(d / "extracted" / "atos.jsonl", encoding="utf-8")) if (d / "extracted" / "atos.jsonl").exists() else 0
        et = "; ".join(f"{k} {v.get('seg', '-')}s" for k, v in m["etapas"].items() if not v.get("pulada") and "seg" in v) or "—"
        loc = custo_local(d)
        nuv = custo_nuvem(c["cnj"], desde)
        tot_local_min += loc["seg"] / 60
        tot_usd += nuv["usd"]
        L.append(f"| {c['cnj']} | {n_atos} | {et} | {loc['atos']} · {loc['prompt_tok']}/{loc['gerados']} · {loc['seg'] / 60:.0f} · "
                 f"{loc['trechos_ok']}/{loc['trechos']} | {nuv['chamadas']} · {nuv['tokens_in']}/{nuv['tokens_out']} · {nuv['usd']} | {'; '.join(m['avisos']) or '—'} |")
        dados.append({"cnj": c["cnj"], "atos": n_atos, "etapas": m["etapas"], "local": loc, "nuvem": nuv, "avisos": m["avisos"]})
    L += ["", f"**Total:** {len(casos)} caso(s) · modelo local acumulado {tot_local_min:.0f} min · nuvem US$ {tot_usd:.4f}", "",
          "> Custo de eletricidade do modelo local não medido; a referência é o tempo de CPU. Para a nuvem, `custo_usd` vem do OpenRouter quando ele devolve `usage.cost`, senão da tabela estimada em `config_llm.json`."]
    return "\n".join(L) + "\n", {"data": hoje, "casos": dados, "total_local_min": round(tot_local_min), "total_usd": round(tot_usd, 4)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--casos", help="CNJs separados por vírgula (padrão: todos com caso.json ativo)")
    ap.add_argument("--janela-min", type=int, default=480, help="minutos para etapas longas (indexar/distilar)")
    ap.add_argument("--sem-llm", action="store_true", help="só etapas determinísticas")
    ap.add_argument("--sem-indexar", action="store_true")
    ap.add_argument("--sem-distilar", action="store_true")
    ap.add_argument("--so-relatorio", action="store_true")
    ap.add_argument("--desde", help="custo em nuvem só a partir desta data ISO (padrão: hoje)")
    ap.add_argument("--dry-run", action="store_true", help="mostra os comandos sem rodar")
    a = ap.parse_args(argv)
    hoje = date.today().isoformat()
    RELATORIOS.mkdir(parents=True, exist_ok=True)
    CASOS.mkdir(parents=True, exist_ok=True)
    casos = carregar_casos([x.strip() for x in a.casos.split(",")] if a.casos else None)
    if not casos:
        print(f"nenhum caso com caso.json em {CASOS}")
        return 2
    mets = []
    with io.open(RELATORIOS / f"lote-{hoje}.log", "a", encoding="utf-8", newline="\n") as arq:
        log(f"lote: {len(casos)} caso(s) · janela {a.janela_min} min · sem_llm={a.sem_llm} · dry_run={a.dry_run}", arq)
        fim = time.time() + a.janela_min * 60
        if not a.so_relatorio:
            for c in casos:
                log(f"== {c['cnj']} ({c['_dir']})", arq)
                try:
                    mets.append(processar(c, a, arq, fim))
                except Exception as e:  # noqa: BLE001
                    log(f"  ERRO: {e}", arq)
                    mets.append({"cnj": c["cnj"], "etapas": {}, "avisos": [f"erro: {e}"]})
        md, js = relatorio(mets, casos, hoje, a.desde or hoje)
        io.open(RELATORIOS / f"custo-{hoje}.md", "w", encoding="utf-8", newline="\n").write(md)
        io.open(RELATORIOS / f"custo-{hoje}.json", "w", encoding="utf-8", newline="\n").write(json.dumps(js, ensure_ascii=False, indent=1))
        log(f"relatório: {RELATORIOS / f'custo-{hoje}.md'}", arq)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
