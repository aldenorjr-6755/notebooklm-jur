#!/usr/bin/env python3
"""Inventario estruturado do arsenal ~/.claude (skills, agents, commands, plugins).

Somente leitura. Gera CSVs + relatorio de anomalias.
Uso: python inventario.py [--out DIR]
"""
import csv, json, os, re, sys
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
OUT = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path.cwd()

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
# Caminhos absolutos citados dentro das skills (helpers, corpora).
# Aceita ESPACO no nome do arquivo ("CNJ Custodia - Algemas.md"): captura ate um
# delimitador de markdown/prosa, e o resolvedor depois apara o excesso.
PATHREF = re.compile(r"(?:~|\$HOME|C:\\Users\\[^\\\s\"']+)[/\\][^\n`\"'|)\]]{3,}")
TRAILING = ".,;:)`'\"* "
# Marcadores de que o "caminho" e molde/exemplo, nao referencia real
PLACEHOLDER = re.compile(r"(NNN|XXX|\{|\}|<|>|\$\{|my-project|exemplo|EXEMPLO|\.\.\.)")


def frontmatter(text):
    m = FM.match(text)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+", line) and key:            # continuacao
            out[key] += " " + line.strip()
        elif ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            out[key] = val.strip().strip("'\"")
    return out


def _sa(s):
    import unicodedata
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()


def dirsize(p):
    total = files = 0
    for root, _, fs in os.walk(p):
        for f in fs:
            try:
                total += (Path(root) / f).stat().st_size
                files += 1
            except OSError:
                pass
    return total, files


def refs(text):
    found = set()
    for r in PATHREF.findall(text):
        r = r.rstrip(TRAILING)
        # corta em marcador de prosa que nunca faz parte de caminho
        for corte in (" — ", " – ", ", ", "; ", " (", " e ", " ou "):
            if corte in r:
                r = r.split(corte)[0].rstrip(TRAILING)
        if len(r) > 6:
            found.add(r)
    return found


def resolve(ref):
    r = ref.replace("$HOME", str(HOME))
    if r.startswith("~"):
        r = str(HOME) + r[1:]
    return Path(r.replace("\\", "/"))


def _resolve_1(p):
    """Um candidato resolve? Aceita nome truncado no espaco."""
    if p.exists():
        return True
    try:
        if p.parent.is_dir() and any(q.name.startswith(p.name) for q in p.parent.iterdir()):
            return True                 # "…/fontes/CNJ" -> "CNJ Custodia….md"
    except OSError:
        pass
    return False


def existe(ref):
    """True se ALGUM prefixo por palavra da referencia resolve.

    O texto capturado pode arrastar argumentos de linha de comando
    ("consultar_codigo.py --fonte cp 42") ou o resto da frase; o caminho e o
    maior prefixo que existe em disco. Testa do mais longo ao mais curto.
    """
    if PLACEHOLDER.search(ref):
        return True                     # molde/exemplo, nao referencia real
    if any(ch in ref for ch in "*?"):
        return True                     # glob, nao caminho literal
    palavras = ref.split(" ")
    for i in range(len(palavras), 0, -1):
        cand = " ".join(palavras[:i]).rstrip(TRAILING)
        if len(cand) > 6 and _resolve_1(resolve(cand)):
            return True
    return False


# ---------- coleta ----------
skills, anomalias, allrefs = [], [], {}
skill_desc, agent_desc = {}, {}


def scan_skills(root: Path, origem: str):
    if not root.is_dir():
        return
    for entry in sorted(root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file() and entry.suffix == ".md":
            anomalias.append((".md solto em skills/ (nao e skill valida)", origem, entry.name, str(entry)))
            continue
        if not entry.is_dir():
            continue
        sk = entry / "SKILL.md"
        if not sk.exists():
            nested = list(entry.glob("*/SKILL.md"))
            anomalias.append(("pasta sem SKILL.md" + (" (aninhado: %d)" % len(nested) if nested else ""),
                              origem, entry.name, str(entry)))
            continue
        text = sk.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        size, nfiles = dirsize(entry)
        rs = refs(text)
        if rs:
            allrefs["%s:%s" % (origem, entry.name)] = rs
        nome_fm = fm.get("name", "")
        desc = fm.get("description", "")
        if not desc:
            anomalias.append(("sem description no frontmatter", origem, entry.name, str(sk)))
        if nome_fm and nome_fm != entry.name:
            anomalias.append(("name do frontmatter ('%s') != nome da pasta" % nome_fm, origem, entry.name, str(sk)))
        # Gordura e a PROSA, nao a lista de gatilho: "Aciona com: a, b, c" e o que
        # faz a skill disparar e nao deve ser cortado. Mede-se so o que vem antes.
        prosa = desc.split("Aciona com:")[0]
        if len(prosa) > 700:
            anomalias.append(("prosa da description inchada (%d chars antes de 'Aciona com:')" % len(prosa),
                              origem, entry.name, str(sk)))
        skill_desc[entry.name] = desc
        skills.append(dict(
            nome=entry.name, origem=origem, name_fm=nome_fm, desc_chars=len(desc),
            prosa_chars=len(prosa),
            skill_md_chars=len(text), arquivos=nfiles, kb=round(size / 1024, 1),
            tem_scripts=int((entry / "scripts").is_dir()),
            tem_references=int((entry / "references").is_dir()),
            refs_externas=len(rs), caminho=str(entry),
        ))


scan_skills(CLAUDE / "skills", "user")
for sd in sorted((CLAUDE / "plugins" / "marketplaces").glob("*/*/skills")):
    scan_skills(sd, "plugin:%s/%s" % (sd.parent.parent.name, sd.parent.name))
for sd in sorted((CLAUDE / "plugins" / "marketplaces").glob("*/skills")):
    scan_skills(sd, "plugin:%s" % sd.parent.name)

# agents
agents = []
adir = CLAUDE / "agents"
if adir.is_dir():
    for f in sorted(adir.glob("*.md")):
        if f.name == "README.md":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        desc = fm.get("description", "")
        if not desc:
            anomalias.append(("agente sem description", "agents", f.stem, str(f)))
        if fm.get("name") and fm["name"] != f.stem:
            anomalias.append(("name ('%s') != arquivo" % fm["name"], "agents", f.stem, str(f)))
        agent_desc[f.stem] = desc
        agents.append(dict(nome=f.stem, name_fm=fm.get("name", ""), desc_chars=len(desc),
                           corpo_chars=len(text), tools=fm.get("tools", ""), model=fm.get("model", ""),
                           caminho=str(f)))

# commands
commands = []
cdir = CLAUDE / "commands"
if cdir.is_dir():
    for f in sorted(cdir.rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        commands.append(dict(nome=f.stem, desc_chars=len(fm.get("description", "")),
                             corpo_chars=len(text), caminho=str(f)))

# ---------- colisoes de nome ----------
byname = defaultdict(list)
for s in skills:
    byname[s["nome"]].append(s["origem"])
for n, orgs in sorted(byname.items()):
    if len(orgs) > 1:
        anomalias.append(("nome de skill duplicado em %d origens (%s) - uma sombreia a outra"
                          % (len(orgs), ", ".join(orgs)), "colisao", n, ""))
skillnames = set(byname)
for a in agents:
    if a["nome"] in skillnames:
        # Par homonimo E deliberado quando os DOIS lados declaram a divisao de
        # trabalho: renomear custaria reescrever as referencias cruzadas.
        dois_declaram = ("PAR HOMONIMO" in _sa(agent_desc.get(a["nome"], ""))
                         and "PAR HOMONIMO" in _sa(skill_desc.get(a["nome"], "")))
        if dois_declaram:
            continue
        anomalias.append(("nome existe como agente E como skill - ambiguidade ao invocar",
                          "colisao", a["nome"], a["caminho"]))
cmdnames = {c["nome"] for c in commands}
for n in sorted(cmdnames & skillnames):
    anomalias.append(("nome existe como command E como skill", "colisao", n, ""))

# ---------- referencias externas quebradas ----------
quebradas = []
for owner, rs in sorted(allrefs.items()):
    for r in sorted(rs):
        if existe(r):
            continue
        # separa o que e seu do que e de plugin de terceiro
        origem = "plugin" if owner.startswith("plugin:") else "user"
        quebradas.append((owner, r, str(resolve(r)), origem))

# ---------- saida ----------
OUT.mkdir(parents=True, exist_ok=True)


def dump(name, rows):
    if not rows:
        return
    with open(OUT / name, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


dump("inventario_skills.csv", skills)
dump("inventario_agents.csv", agents)
dump("inventario_commands.csv", commands)
dump("inventario_anomalias.csv", [dict(tipo=t, origem=o, item=i, caminho=c) for t, o, i, c in anomalias])
dump("inventario_refs_quebradas.csv", [dict(skill=o, origem=g, referencia=r, resolvido=p) for o, r, p, g in quebradas])

resumo = dict(
    skills_total=len(skills),
    skills_user=sum(1 for s in skills if s["origem"] == "user"),
    skills_plugin=sum(1 for s in skills if s["origem"] != "user"),
    agents=len(agents), commands=len(commands),
    kb_skills=round(sum(s["kb"] for s in skills), 1),
    desc_chars_total=sum(s["desc_chars"] for s in skills) + sum(a["desc_chars"] for a in agents),
    anomalias=len(anomalias),
    refs_quebradas=len(quebradas),
    refs_quebradas_suas=sum(1 for q in quebradas if q[3] == "user"),
)
(OUT / "inventario_resumo.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(resumo, indent=2, ensure_ascii=False))
print("\n== TOP 15 descriptions mais pesadas (skills) ==")
for s in sorted(skills, key=lambda x: -x["desc_chars"])[:15]:
    print("%6d  %-28s %s" % (s["desc_chars"], s["origem"], s["nome"]))
print("\n== TOP 15 descriptions mais pesadas (agents) ==")
for a in sorted(agents, key=lambda x: -x["desc_chars"])[:15]:
    print("%6d  %s" % (a["desc_chars"], a["nome"]))
print("\n== ANOMALIAS por tipo ==")
tipos = defaultdict(int)
for t, *_ in anomalias:
    tipos[re.sub(r"\(.*?\)", "(...)", t)] += 1
for t, n in sorted(tipos.items(), key=lambda x: -x[1]):
    print("%4d  %s" % (n, t))
print("\n== REFERENCIAS EXTERNAS QUEBRADAS: %d ==" % len(quebradas))
for o, r, p, g in quebradas[:25]:
    print("  [%s] %s  ->  %s" % (g, o, r))
