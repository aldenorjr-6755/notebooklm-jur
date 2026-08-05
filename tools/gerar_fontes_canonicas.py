#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gera ~/.notebooklm/FONTES-CANONICAS.md — manual único de fontes canônicas.

Lê o estado REAL da máquina (registries dos helpers, datasets JSON, slash commands
de usuário, notebooks citados pelos agentes, corpora locais) e emite um documento
compacto. Rode depois de acrescentar qualquer fonte nova:

    python ~/.notebooklm/tools/gerar_fontes_canonicas.py

DOIS ESCOPOS, desde 2026-07-28. O gerador varre o escopo de usuário (`~/.claude/`)
E o `.claude/` de cada vault em `~/OneDrive/0-Obsidian/`. Antes varria só o global,
e por isso o registry de notebooks PERDIA o agente de todo vault Classe A — que, por
definição, guarda os próprios agentes dentro de si. Foi o que aconteceu quando o vault
Psicologia foi promovido a Classe A: os quatro agentes de autor saíram de
`~/.claude/agents/` e, na geração seguinte, o mapeamento notebook->agente sumiria em
silêncio. Um catálogo que só vê metade da máquina mente sobre a outra metade.
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
FONTES_STF = BASE / "informativo_stf" / "fontes"
FONTES_STJ = BASE / "informativo_stj" / "fontes"
CMDS = HOME / ".claude" / "commands"
AGENTS = HOME / ".claude" / "agents"
SKILLS = HOME / ".claude" / "skills"
VAULTS = HOME / "OneDrive" / "0-Obsidian"
OUT = BASE / "FONTES-CANONICAS.md"

UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
# Marcador FORMAL de classe (PADRAO-VAULT.md §1.1). Prosa solta do tipo "este vault é
# autossuficiente para leitura" NÃO é declaração e daria falso positivo em oito de oito.
CLASSE = re.compile(r"\*\*Classe\s+([AB])\b")


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


def cofres():
    """Vaults com `.claude/` próprio, com a classe declarada em REQUISITOS-EXTERNOS.md.

    Devolve lista de dicts: nome, caminho, classe ('A'/'B'/'?'), e a contagem de
    agentes, skills, slash commands e helpers locais.
    """
    out = []
    if not VAULTS.exists():
        return out
    for d in sorted(VAULTS.iterdir()):
        cl = d / ".claude"
        if not (d.is_dir() and cl.is_dir()):
            continue
        req = d / "REQUISITOS-EXTERNOS.md"
        m = CLASSE.search(req.read_text(encoding="utf-8", errors="ignore")) if req.exists() else None
        out.append({
            "nome": d.name,
            "path": d,
            "claude": cl,
            "classe": m.group(1) if m else "?",
            "agentes": sorted((cl / "agents").glob("*.md")) if (cl / "agents").is_dir() else [],
            "skills": sorted(p for p in (cl / "skills").iterdir() if p.is_dir()) if (cl / "skills").is_dir() else [],
            "cmds": sorted((cl / "commands").glob("*.md")) if (cl / "commands").is_dir() else [],
            "tools": sorted((cl / "tools").glob("*.py")) if (cl / "tools").is_dir() else [],
        })
    return out


def frontmatter_desc(p):
    txt = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        return ""
    d = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    return d.group(1).strip().strip("\"'") if d else ""


L = []
w = L.append

COFRES = cofres()
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
w("5. **\"Artigo não encontrado\" pode ser defeito do dataset, não erro da pergunta.** Em 2026-08-05,")
w("   o RISTF rodava havia meses **sem 29 artigos** — inclusive todo o rito da súmula vinculante —")
w("   porque o extrator só aceitava sufixo de letra maiúscula; e o RITJMA devolvia a redação")
w("   **revogada** do art. 390. Antes de concluir que a norma não existe, rode:")
w("   `python ~/.notebooklm/tools/lint_fontes_canonicas.py --so-suspeitos`")
w("   (LACUNA = artigo sumiu · MOJIBAKE = acento corrompido, busca falha em silêncio ·")
w("   REDACOES = redações sucessivas sem placa · ORFAO = dataset que helper nenhum consulta).")
w("")

# ---------------------------------------------------------------- slashes
w("## Slash commands (escopo de usuário — valem em qualquer vault)")
w("")
if CMDS.exists():
    cmds = sorted(CMDS.glob("*.md"))
    n_loc = sum(len(c["cmds"]) for c in COFRES)
    w(f"{len(cmds)} comandos em `~/.claude/commands/`. Um vault pode sombrear qualquer um deles com")
    w("uma versão local em `<vault>/.claude/commands/` (escopo de projeto vence).")
    if n_loc:
        w(f"Há hoje **{n_loc} slash commands locais** distribuídos por {len(COFRES)} cofres — a tabela")
        w("por vault está no fim deste documento, em *Recursos do Claude Code*.")
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
for f, nome, slash in [("stf", "RISTF", "/ristf"), ("stj", "RISTJ", "/ristj"),
                       ("tjma", "RITJMA", "/ritjma"), ("tse", "RITSE", "/ritse")]:
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
w(f"| Informativos do **STF** | `consultar_informativo_stf.py \"<termo>\"` · `/consulta-informativo-stf` | {len(list(FONTES_STF.glob('*.md')))} arquivos, **2014–2026** (ed. ~733–1220) |")
w(f"| Informativos do **STJ** | `consultar_informativo_stj.py \"<termo>\"` · `/consulta-informativo-stj` | {len(list(FONTES_STJ.glob('*.md')))} arquivos, nº 1–853 (1998–2025) — **sem 2019** |")
w("")
w("**Informativo do STF — o que o helper resolve e o que não resolve.** O corpus tem duas")
w("famílias: 2014–2019 (*Teses e Fundamentos*, por matéria, conversão DOCX legada) e 2020–2026")
w("(*Informativo Temático*, por ramo, conversão PDF paginada — o helper cita a **página do PDF**).")
w("O **número da edição** sai resolvido em ~90% dos trechos dos temáticos e ~94% em 2017–2018,")
w("mas é **estruturalmente irrecuperável em 2014, 2015, 2016 e 2019**, onde não existe marcador")
w("no texto: ali cite processo + relator e declare a edição como não identificada — nunca a")
w("deduza pela faixa do arquivo.")
w("")
w("**Lacuna declarada — Informativo do STF.** O acervo começa em **2014**; as edições **1 a ~732")
w("(1995–2013) não estão nele**. Nada encontrado ali não é achado negativo: para o período")
w("anterior use o agente `rtj-stf` (RTJ, 1957–2017) ou o portal do STF.")
w("")
w("**Informativo do STJ — o que o helper resolve.** Para cada trecho devolve **nº da edição,")
w("ano, órgão julgador, ramo do direito, processo, relator e tema de repetitivo**, lendo as duas")
w("diagramações do acervo (até ~2016, texto corrido com a citação fechando a entrada; de ~2017,")
w("campos `PROCESSO / RAMO DO DIREITO / TEMA / DESTAQUE`). A busca é **insensível a acento**.")
w("O helper **se autolocaliza**: dentro de um vault com espelho próprio, o mesmo arquivo em")
w("`.claude/tools/` lê `.claude/corpora/informativo_stj/fontes` — não há caminho externo.")
w("Ele também separa o processo **julgado** do processo **citado como precedente**, e nomeia a")
w("entrada **em segredo de justiça** em vez de lhe emprestar o número da entrada vizinha.")
w("")
w("**Lacuna declarada — Informativo do STJ.** O **ano de 2019 inteiro está fora do acervo**")
w("(~23 edições, nº 639–661): o ZIP de origem tem 0 byte e o corpus salta de `Inf0638` para")
w("`Inf0662`. Nada encontrado ali não é achado negativo — para 2019 use o corpus full-text")
w("STF·STJ·TRF1 (de 2015 em diante) ou `scon.stj.jus.br`.")
w("")
w("**Proveniência — Informativo do STJ (2026-08-05).** O corpus foi **reconvertido dos RTF**")
w("oficiais por `rtf_stj_para_md.py`. A conversão anterior descartava o escape `\\uNNNN` do RTF")
w("e preservava o fallback ASCII, trocando **todo acento por `?`** (`compet?ncia`) em 795 dos 835")
w("arquivos, e deixando vazar lixo binário das imagens embutidas. Busca por \"competência\" achava")
w("**29** arquivos; hoje acha **684**. Espelhos com `?` no lugar de acento estão desatualizados:")
w("reponha com `implantar_informativo_stj.py --vault <NOME>`. Os 3 notebooks do NotebookLM que")
w("indexavam a conversão velha foram **apagados em 2026-08-05** — a consulta é só local.")
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
w("A varredura cobre **os dois escopos**: `~/.claude/agents/` e o `.claude/agents/` de cada vault.")
w("A coluna **Onde** diz em qual deles o agente vive — num cofre Classe A ele mora dentro do vault,")
w("e só é acionável com o Claude Code iniciado na raiz dele.")
w("")
reg_nb = {}   # (onde, agente) -> set(ids)
if AGENTS.exists():
    for f in AGENTS.glob("*.md"):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for uid in set(UUID.findall(txt)):
            reg_nb.setdefault(("global", f.stem), set()).add(uid)
for c in COFRES:
    for f in c["agentes"]:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for uid in set(UUID.findall(txt)):
            reg_nb.setdefault((c["nome"], f.stem), set()).add(uid)
mortos = set()
pmortos = BASE / "notebooks_mortos.txt"
if pmortos.exists():
    mortos = set(UUID.findall(pmortos.read_text(encoding="utf-8", errors="ignore")))
if mortos:
    w(f"Marcados **(apagado)** os {len(mortos)} notebooks já removidos da conta — registro em")
    w("`~/.notebooklm/notebooks_mortos.txt`. Não tente consultá-los.")
    w("")
w("| Agente | Onde | Notebooks |")
w("|---|---|---|")
for onde, agente in sorted(reg_nb, key=lambda t: (t[1], t[0])):
    ids = sorted(reg_nb[(onde, agente)])
    fmt = [f"`{i}`" + (" **(apagado)**" if i in mortos else "") for i in ids]
    label = "`~/.claude/`" if onde == "global" else f"vault **{onde}**"
    w(f"| `{agente}` | {label} | {' · '.join(fmt)} |")
w("")
dup = {}
for onde, agente in reg_nb:
    dup.setdefault(agente, []).append(onde)
dobrados = {a: sorted(o for o in ondes) for a, ondes in dup.items() if len(ondes) > 1}
if dobrados:
    com_global = sorted(a for a, ondes in dobrados.items() if "global" in ondes)
    entre_cofres = sorted(a for a, ondes in dobrados.items() if len([o for o in ondes if o != "global"]) > 1)
    w(f"> **{len(dobrados)} agentes do registry existem em mais de um escopo.** Duplicata **diverge em")
    w("> silêncio** quando editada de um lado só — e nada avisa, porque as duas resolvem.")
    w(">")
    w("> **Não conclua daqui que é resíduo a apagar.** Auditoria de 2026-07-28 comparou os 269 pares")
    w("> de agente e skill dos cofres Classe A: **106 eram cópia morta** (idêntica ou divergindo só em")
    w("> linha de caminho), mas **99 eram fork de domínio** — o `jurisprudencia-stj-stf` do Eleitoral,")
    w("> por exemplo, tem um bloco inteiro de matéria eleitoral que a global não tem — e **28 são")
    w("> compartilhados** entre dois cofres, de modo que apagar do global os desliga de ambos. Pior:")
    w("> em **96 dos 99 forks a cópia GLOBAL estava mais nova**, o que inverte o diagnóstico — ali o")
    w("> defasado é o cofre. Antes de remover qualquer par, classifique: idêntico × só-caminho ×")
    w("> substantivo, e confira a data dos dois lados.")
    w(">")
    if com_global:
        por_cofre = {}
        for a in com_global:
            for o in dobrados[a]:
                if o != "global":
                    por_cofre.setdefault(o, []).append(a)
        w(f"> **Vault × `~/.claude/` ({len(com_global)}):** "
          + " · ".join(f"**{v}** {len(por_cofre[v])}" for v in sorted(por_cofre))
          + ". Num cofre Classe A isto é **resíduo de promoção**, salvo se o recurso for")
        w("> transversal (norma §1.2), caso em que a duplicata é deliberada.")
        if entre_cofres:
            w(">")
    if entre_cofres:
        w(f"> **Entre cofres, sem passar pelo global ({len(entre_cofres)}):** "
          + " · ".join(f"`{a}`" for a in entre_cofres)
          + ". Aqui é compartilhamento entre domínios — legítimo, mas cada cópia envelhece sozinha.")
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
w("## Recursos do Claude Code — os dois escopos")
w("")
w("**Escopo de usuário (`~/.claude/`) — vale em qualquer vault:**")
w("")
w(f"- **{n_ag} agentes** em `~/.claude/agents/` — descobertos por intenção; a descrição de cada um já diz quando acioná-lo. Não replique catálogo de agente em `CLAUDE.md`.")
w(f"- **{n_sk} skills** em `~/.claude/skills/`.")
w(f"- **{len(list(CMDS.glob('*.md'))) if CMDS.exists() else 0} slash commands** em `~/.claude/commands/`.")
w("")
if COFRES:
    w(f"**Escopo de vault (`<vault>/.claude/`) — {len(COFRES)} cofres com infra própria.**")
    w("Só acionável com o Claude Code iniciado **na raiz do vault**; o que é local sombreia o global")
    w("de mesmo nome. Classe **A** guarda tudo dentro de si e sobrevive a um `git clone` sozinho;")
    w("classe **B** é casca em torno do global e declara as dependências em `REQUISITOS-EXTERNOS.md`")
    w("(norma: `~/.notebooklm/PADRAO-VAULT.md` §1).")
    w("")
    w("| Vault | Classe | Agentes | Skills | Slashes | Helpers |")
    w("|---|---|---|---|---|---|")
    for c in COFRES:
        cl = c["classe"]
        marca = {"A": "**A** — autossuficiente", "B": "B — leve"}.get(cl, "`?` — **não declarada**")
        w(f"| {c['nome']} | {marca} | {len(c['agentes'])} | {len(c['skills'])} | {len(c['cmds'])} | {len(c['tools'])} |")
    w("")
    sem = [c["nome"] for c in COFRES if c["classe"] == "?"]
    if sem:
        w(f"> **Classe não declarada em {len(sem)} cofre(s):** " + " · ".join(f"**{n}**" for n in sem) + ".")
        w("> A norma §1.1 exige o marcador formal `**Classe A` ou `**Classe B` na primeira linha útil de")
        w("> `REQUISITOS-EXTERNOS.md`. Sem ele não há como auditar coerência: o vault não diz em que classe está.")
        w("")
    incoerentes = [c["nome"] for c in COFRES if c["classe"] == "A" and not c["agentes"] and not c["skills"]]
    if incoerentes:
        w("> **Declara Classe A e não tem agente nem skill local:** " + " · ".join(f"**{n}**" for n in incoerentes) + ".")
        w("> Ou o vault não usa nenhum dos dois (legítimo), ou a declaração não bate com o conteúdo (defeito §1.1).")
        w("")

OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"OK: {OUT} ({len(L)} linhas)")
