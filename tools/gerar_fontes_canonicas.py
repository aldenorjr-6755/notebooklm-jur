#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gera ~/.notebooklm/FONTES-CANONICAS.md — manual único de fontes canônicas.

Lê o estado REAL da máquina (registries dos helpers, datasets JSON, slash commands
de usuário, notebooks citados pelos agentes, corpora locais) e emite um documento
compacto. Rode depois de acrescentar qualquer fonte nova:

    python ~/.notebooklm/tools/gerar_fontes_canonicas.py
"""
import ast
import datetime
import json
import os
import pathlib
import re

HOME = pathlib.Path(os.path.expanduser("~"))
BASE = HOME / ".notebooklm"
TOOLS = BASE / "tools"
CMDS = HOME / ".claude" / "commands"
AGENTS = HOME / ".claude" / "agents"
SKILLS = HOME / ".claude" / "skills"
OUT = BASE / "FONTES-CANONICAS.md"

UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def reg_de(script):
    """Extrai o dict REG={...} de um helper sem importá-lo."""
    p = TOOLS / script
    if not p.exists():
        return {}
    txt = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^REG\s*=\s*(\{.*?\})\s*$", txt, re.S | re.M)
    if not m:
        return {}
    try:
        return ast.literal_eval(m.group(1))
    except Exception:
        return {}


def dataset(nome):
    p = TOOLS / nome
    if not p.exists():
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def conta(d, *chaves):
    if not isinstance(d, dict):
        return "?"
    for k in chaves:
        if isinstance(d.get(k), list):
            return len(d[k])
    for v in d.values():
        if isinstance(v, list):
            return len(v)
    return "?"


def frontmatter_desc(p):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        return ""
    d = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    return d.group(1).strip().strip("\"'") if d else ""


L = []
w = L.append

hoje = datetime.date.today().isoformat()
w("# Fontes canônicas — manual único")
w("")
w(f"> Gerado por `~/.notebooklm/tools/gerar_fontes_canonicas.py` em {hoje}. **Não edite à mão**:")
w("> acrescente a fonte (helper/dataset/agente/slash) e rode o gerador de novo.")
w("> Referenciado por uma linha em cada `CLAUDE.md` — este arquivo é a única fonte de verdade.")
w("")
w("## Regras de uso (valem para toda consulta)")
w("")
w("1. **Nunca cite norma, súmula, tese ou precedente de memória** — rode o helper e cite o retorno.")
w("2. Datasets são **snapshots**: confirme vigência (EC/lei alteradora/cancelamento) na fonte oficial.")
w("3. Notebook do NotebookLM é **doutrina ou acervo indexado** — cite título/autor/data/URL e confirme o inteiro teor.")
w("4. Falta de dado → escreva `[VERIFICAR]`. Não complete nem parafraseie dispositivo legal.")
w("")

# ---------------------------------------------------------------- slashes
w("## Slash commands (escopo de usuário — valem em qualquer vault)")
w("")
if CMDS.exists():
    cmds = sorted(CMDS.glob("*.md"))
    w(f"{len(cmds)} comandos em `~/.claude/commands/`. Um vault pode sombrear qualquer um deles com")
    w("uma versão local em `<vault>/.claude/commands/` (escopo de projeto vence).")
    w("")
    w("| Slash | O que faz |")
    w("|---|---|")
    for c in cmds:
        w(f"| `/{c.stem}` | {frontmatter_desc(c) or '—'} |")
else:
    w("`~/.claude/commands/` não existe.")
w("")

# ---------------------------------------------------------------- normas
w("## Normas — texto literal por artigo")
w("")
w("**Constituição, obras e tratados**")
w("")
w("| Fonte | Comando | Cobertura |")
w("|---|---|---|")
cf = dataset("cf_artigos.json")
if cf:
    w(f"| CF/1988 (texto Planalto) | `python $HOME/.notebooklm/tools/consultar_cf.py <art>` · `/cf` | {conta(cf,'artigos')} artigos (ADCT não indexado) |")
cs = dataset("constituicao_supremo.json")
if cs:
    w(f"| A Constituição e o Supremo (CF anotada pelo STF) | `consultar_constituicao_supremo.py <art>` · `/constituicao` | {conta(cs,'artigos')} artigos → página do PDF |")
for f, nome, slash in [("stf", "RISTF", "/ristf"), ("tjma", "RITJMA", "/ritjma"), ("tse", "RITSE", "/ritse")]:
    d = dataset(f"regimento_{f}.json")
    if d:
        w(f"| {nome} | `consultar_regimento.py --fonte {f} <art>` · `{slash}` | {conta(d,'artigos')} artigos |")
for k, arq in sorted(reg_de("consultar_tratado.py").items()):
    d = dataset(arq)
    if d:
        w(f"| {d.get('fonte', k)} | `consultar_tratado.py --fonte {k} <art>` · `/{k}` | {conta(d,'artigos')} artigos |")
w("")

codigos = reg_de("consultar_codigo.py")
w(f"**Códigos e leis** — helper único, {len(codigos)} fontes:")
w("")
w("```bash")
w("python $HOME/.notebooklm/tools/consultar_codigo.py --fonte <sigla> <artigo|palavra>")
w("```")
w("")
w("| `--fonte` | Norma | Registros |")
w("|---|---|---|")
for k, arq in sorted(codigos.items()):
    d = dataset(arq)
    if d:
        w(f"| `{k}` | {d.get('fonte', '—')} | {conta(d,'artigos')} |")
    else:
        w(f"| `{k}` | dataset ausente `[VERIFICAR]` | — |")
w("")
w("_\"Registros\" conta cada entrada do dataset — inclui variantes (`1.240-A`) e revogados em stub;")
w("não é o número nominal de artigos da lei. Nova norma = rodar `extrair_codigo.py` + 1 linha no REG + slash + rodar este gerador._")
w("")

# ---------------------------------------------------------------- jurisprudência
w("## Jurisprudência e súmulas")
w("")
w("| Fonte | Comando | Cobertura |")
w("|---|---|---|")
for arq, nome, helper, slash in [
    ("sumulas_stj.json", "Súmulas do STJ", "consultar_sumula_stj.py", "/sumula-stj"),
    ("sumulas_stf.json", "Súmulas do STF (comuns)", "consultar_sumula_stf.py", "/sumula-stf"),
    ("sumulas_vinculantes_stf.json", "Súmulas Vinculantes (CF 103-A)", "consultar_sumula_vinculante.py", "/sumula-vinculante"),
]:
    d = dataset(arq)
    if d:
        w(f"| {nome} | `{helper} \"<palavra>\"` · `{slash}` | {conta(d,'sumulas','sumulas_vinculantes')} verbetes |")
w("| Súmula do STF + aplicação (online, vigente) | `consultar_aplicacao_sumula.py --tipo sv\\|comum <n>` · `/aplicacao-sumula` | versão atual + precedentes |")
w("| Temas de Repercussão Geral | `consultar_repercussao_geral.py \"<palavra>\"` · `/tese-rg` | JSON oficial STF (com/sem RG) |")
w("| Precedentes qualificados (BNP/Pangea CNJ) | `consultar_bnp.py` · `/bnp` | RG/RR/SV/IAC/IRDR; não cobre TSE |")
w("| Corpus full-text STF·STJ·TRF1 | `consultar_jurisprudencia.py \"<termo>\"` · `/jurisprudencia` | Informativos, Teses, Repetitivos, BIJ, SV |")
w("")
w("**Vocabulário controlado** — `consultar_tesauro.py` (descritor STF, `/termo-juridico`) · ")
w("`consultar_glossario.py` (definições STF, `/glossario`) · `consultar_glossario_tse.py` (`/glossario-tse`).")
w("")
w("**Súmula comum ≠ vinculante.** A vinculante obriga Judiciário e Administração (reclamação ao STF).")
w("")

obras = reg_de("consultar_obra_tematica.py")
if obras:
    w("## Obras temáticas do STF (sumário tema → página)")
    w("")
    w("Devolvem a **página** do PDF; o teor exige abrir o PDF nela (`Read` com `pages:`).")
    w("")
    w("| `--fonte` | Obra | Slash |")
    w("|---|---|---|")
    for k in sorted(obras):
        d = dataset(obras[k])
        titulo = (d or {}).get("titulo") or (d or {}).get("fonte") or k
        w(f"| `{k}` | {titulo} | `/{k.replace('_','-')}` |")
    w("")
    w("_Comando: `consultar_obra_tematica.py --fonte <sigla> <tema>`._")
    w("")

# ---------------------------------------------------------------- notebooks
w("## Notebooks do NotebookLM (registry vivo)")
w("")
w("Extraído dos agentes que efetivamente os consultam — a fonte de verdade é o próprio agente.")
w("Consulta direta: `notebooklm ask \"<pergunta>\" -n <id> --json`.")
w("")
reg_nb = {}
if AGENTS.exists():
    for f in AGENTS.glob("*.md"):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for uid in set(UUID.findall(txt)):
            reg_nb.setdefault(f.stem, set()).add(uid)
mortos = set()
pmortos = BASE / "notebooks_mortos.txt"
if pmortos.exists():
    mortos = set(UUID.findall(pmortos.read_text(encoding="utf-8", errors="ignore")))
if mortos:
    w(f"Marcados **(apagado)** os {len(mortos)} notebooks já removidos da conta — registro em")
    w("`~/.notebooklm/notebooks_mortos.txt`. Não tente consultá-los.")
    w("")
w("| Agente | Notebooks |")
w("|---|---|")
for agente in sorted(reg_nb):
    ids = sorted(reg_nb[agente])
    fmt = [f"`{i}`" + (" **(apagado)**" if i in mortos else "") for i in ids]
    w(f"| `{agente}` | {' · '.join(fmt)} |")
w("")
extras = sorted(BASE.glob("*/notebooks_ids.txt"))
if extras:
    w("Acervos com vários notebooks por período (IDs no arquivo):")
    w("")
    for e in extras:
        w(f"- `{e.parent.name}` → `~/.notebooklm/{e.parent.name}/notebooks_ids.txt`")
    w("")

# ---------------------------------------------------------------- corpora
w("## Corpora locais (`~/.notebooklm/<acervo>/fontes/`)")
w("")
w("| Acervo | Arquivos |")
w("|---|---|")
for d in sorted(BASE.glob("*/fontes")):
    n = sum(1 for _ in d.rglob("*") if _.is_file())
    if n:
        w(f"| `{d.parent.name}` | {n} |")
w("")

# ---------------------------------------------------------------- pipelines
BIB = BASE / "biblioteca"
if BIB.exists():
    n_md = sum(1 for _ in (BIB / "md").rglob("*.md")) if (BIB / "md").exists() else 0
    n_pdf = sum(1 for sub in ("pdf", "html") if (BIB / sub).exists()
                for p in (BIB / sub).rglob("*") if p.is_file())
    w("## Biblioteca (obras em PDF/HTML e sua versão Markdown)")
    w("")
    w(f"`~/.notebooklm/biblioteca/` — **{n_pdf} originais** em `pdf/` e `html/`, **{n_md} convertidos** em `md/`.")
    w("Cada página do PDF vira `## [p. N]` no Markdown: a página devolvida por um helper")
    w("(`consultar_constituicao_supremo.py`, `consultar_cadh_stf.py`, `consultar_obra_tematica.py`)")
    w("resolve direto no `.md` — leia o Markdown em vez de abrir o PDF.")
    w("")
    w("| Grupo | Arquivos |")
    w("|---|---|")
    for d in sorted((BIB / "md").iterdir()) if (BIB / "md").exists() else []:
        if d.is_dir():
            w(f"| `md/{d.name}/` | {sum(1 for _ in d.rglob('*.md'))} |")
    raiz_md = len(list((BIB / 'md').glob('*.md'))) if (BIB / 'md').exists() else 0
    w(f"| `md/` (raiz — obras avulsas) | {raiz_md} |")
    w("")
    w("Verificação da conversão (páginas, chars/página, NUL, OCR pendente):")
    w("`~/.notebooklm/biblioteca/RELATORIO-CONVERSAO.md`. Reconverter:")
    w("`python ~/.notebooklm/tools/converter_biblioteca_md.py --origem <pasta>`.")
    w("")

w("## Pipelines")
w("")
w("- **Pesquisa pesada sem gastar contexto** — skill `notebooklm`: cria notebook, sobe fontes, pergunta, e só o destilado com citação volta para a Wiki. Slash `/pesquisar-notebooklm`.")
w("- **Dado recente ou disperso na web** — MCP `mcp__perplexity__*` (`_search` fatos/URLs · `_ask` resposta com citação · `_reason` raciocínio em etapas · `_research` multi-fonte). Slash `/pesquisa-perplexity`.")
w("- **PDF escaneado → Markdown** — watcher em `~/.notebooklm/` (Tesseract/Ghostscript) ou `converter_pdf_ocr.py`. Compare o tamanho antes de destilar: conversão perde conteúdo em silêncio.")
w("- **Saída .docx** — skill `docx-juridico-padrao` (Sitka Text 12, entrelinha 1,16, 6 pt depois, margens 2 cm; citação em bloco recuado 2 cm com Segoe UI 12/1,08). Só fuja do padrão a pedido explícito.")
w("- **Nota-tese** — slash `/tese`: cruza vocabulário → norma → jurisprudência → doutrina, cada camada com citação, e rotula norma × jurisprudência × doutrina.")
w("")

n_ag = len(list(AGENTS.glob("*.md"))) if AGENTS.exists() else 0
n_sk = len([p for p in SKILLS.iterdir() if p.is_dir()]) if SKILLS.exists() else 0
w("## Recursos globais do Claude Code")
w("")
w(f"- **{n_ag} agentes** em `~/.claude/agents/` — descobertos por intenção; a descrição de cada um já diz quando acioná-lo. Não replique catálogo de agente em `CLAUDE.md`.")
w(f"- **{n_sk} skills** em `~/.claude/skills/`.")
w(f"- **{len(list(CMDS.glob('*.md'))) if CMDS.exists() else 0} slash commands** em `~/.claude/commands/`.")
w("")

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"OK: {OUT} ({len(L)} linhas)")
