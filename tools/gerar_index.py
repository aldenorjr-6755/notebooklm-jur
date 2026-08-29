#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reconcilia os index.md dos vaults com o estado real das pastas.

    python ~/.notebooklm/tools/gerar_index.py            # relatorio de todos (dry-run)
    python ~/.notebooklm/tools/gerar_index.py Criminal   # so um vault
    python ~/.notebooklm/tools/gerar_index.py --apply    # grava
    python ~/.notebooklm/tools/gerar_index.py --podar --apply
    python ~/.notebooklm/tools/gerar_index.py --limpar-fantasmas --apply

POR QUE ELE NAO REGENERA O INDICE INTEIRO
-----------------------------------------
A tentacao obvia e varrer a pasta e reescrever o index.md do zero. Seria
destrutivo. Varios indices carregam CURADORIA de verdade: o
`Criminal/10-Wiki/Teses/index.md` tem secao de lote datada e ganchos autorais de
mil caracteres, com negrito, emoji, links embutidos e anotacao de `forca:` e
`status:`. Regenerar aquilo troca trabalho intelectual por resumo mecanico.

Entao a semantica aqui e de RECONCILIACAO, e casa com a definicao de defeito do
proprio lint (`lint_vault.py::index_enumera_tudo`): indice defeituoso e o que NAO
REFERENCIA alguma nota da pasta. Logo o gerador:

  - ACRESCENTA a nota ausente, com gancho derivado da primeira linha util;
  - APONTA (e so remove com --podar) a entrada que aponta para nota inexistente;
  - ATUALIZA as contagens, o bloco de subpastas e o `updated:`;
  - PRESERVA byte a byte todo o resto -- prosa, secoes, ganchos ja escritos.

Gancho ja escrito por humano NUNCA e reescrito: se a nota ja esta referenciada, a
linha dela nao e tocada.

ESCOPO (PADRAO-VAULT.md 6C)
---------------------------
A norma lista os vaults em que a convencao de index.md esta em uso. Dissertacao,
MestradoCeuma, JuntaMedica e Longevidade ficam FORA por decisao registrada --
exigem nomeacao explicita mais --force.
"""
import argparse
import datetime
import os
import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

RAIZ = pathlib.Path(os.path.expanduser("~")) / "OneDrive" / "0-Obsidian"

VAULTS_PADRAO = [
    "Ambiental", "Constitucional", "Criminal", "Eleitoral", "ExecucaoPenal",
    "Familia", "ProcessoCivil", "Psicologia", "Trabalhista",
]
VAULTS_FORA = ["Dissertacao", "MestradoCeuma", "JuntaMedica", "Longevidade"]

# Espelha lint_vault.py::DEFAULT_SKIP_DIRS. Copia deliberada: os scripts sao
# autonomos por desenho e importar um do outro acoplaria as duas skills.
SKIP_DIRS = {
    "graphify-out", "_grafo", "00-Grafo", "Anexos", ".obsidian", ".git",
    ".claude", "_Templates", "99-Templates", "_processados", "node_modules",
    "_build", "__pycache__", "prazos",
}

# PADRAO-VAULT 6C: "pastas geradas por pipeline nao tem indice". Sao despejos de
# conversao em lote -- imagens de PDF, backup de original, handoff de sessao,
# recorte de informativo. Indexa-las produziria centenas de ganchos mecanicos
# que ninguem le, dentro de indices que existem para ECONOMIZAR leitura.
SKIP_NOME_RE = re.compile(
    r"(_imagens$|-backup$|_backup$|^_pdf|^_stubs|^_handoff|^_build|^_modelo"
    r"|-PDF-original$|^Informativos-)"
)

# Camada RAW (metodo Karpathy). Fora por padrao; --incluir-raw traz de volta.
RAW_DIRS = {"90-Arquivo"}

WIKILINK_RE = re.compile(r"\[\[([^\]\|#\^\\]+?)(?:\\?\|[^\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
LINHA_NOTA_RE = re.compile(r"^- \[\[")
CABEC_NOTAS_RE = re.compile(r"^Notas \((\d+)\):\s*$")
CABEC_SUB_RE = re.compile(r"^Subpastas:\s*$")

GANCHO_MAX = 120  # medido nos indices existentes: corte duro em 120, sem reticencia


def ler(fp):
    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return fp.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def tem_controle(nome):
    """Nome com caractere de controle. No Windows o \\r do caminho vira U+F00D."""
    return any(ord(c) < 32 or 0xF000 <= ord(c) <= 0xF01F for c in nome)


def gancho_de(fp):
    """Primeira linha util do corpo, sem marcacao, cortada em GANCHO_MAX."""
    txt = ler(fp)
    if txt is None:
        return ""
    corpo = txt
    m = FRONTMATTER_RE.match(txt)
    if m:
        corpo = txt[m.end():]
    for linha in corpo.splitlines():
        s = linha.strip()
        if not s or s.startswith(("#", ">", "|", "---", "<!--", "![[")):
            continue
        s = re.sub(r"\*\*|\*|`|__", "", s)
        s = re.sub(r"^[-*+]\s+", "", s)
        s = re.sub(r"^\[[ xX]\]\s*", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            return s[:GANCHO_MAX]
    return ""


def ignorar(nome, incluir_raw):
    if nome in SKIP_DIRS or nome.startswith("."):
        return True
    if SKIP_NOME_RE.search(nome):
        return True
    if nome in RAW_DIRS and not incluir_raw:
        return True
    return False


def pastas_de_conteudo(raiz_vault, incluir_raw=False, puladas=None):
    """Pastas que devem ter index.md: as com .md proprio e suas ancestrais."""
    com_md = set()
    for dp, dns, fns in os.walk(raiz_vault):
        manter = []
        for d in dns:
            if ignorar(d, incluir_raw):
                if puladas is not None and any(
                    f.endswith(".md") for _, _, fs in os.walk(os.path.join(dp, d)) for f in fs
                ):
                    puladas.append(os.path.relpath(os.path.join(dp, d), raiz_vault))
            else:
                manter.append(d)
        dns[:] = manter
        if any(f.endswith(".md") and f.lower() != "index.md" and not tem_controle(f)
               for f in fns):
            com_md.add(pathlib.Path(dp))
    todas = set(com_md)
    for p in com_md:
        q = p
        while q != raiz_vault and raiz_vault in q.parents:
            q = q.parent
            todas.add(q)
    todas.add(raiz_vault)
    return sorted(todas)


def notas_da_pasta(pasta):
    return sorted(
        f for f in os.listdir(pasta)
        if f.endswith(".md") and f.lower() != "index.md"
        and not tem_controle(f) and (pasta / f).is_file()
    )


def subpastas_com_conteudo(pasta, todas):
    filhas = []
    for d in sorted(os.listdir(pasta)):
        alvo = pasta / d
        if not alvo.is_dir() or ignorar(d, True):
            continue
        if alvo in todas:
            filhas.append(d)
    return filhas


def conta_notas_recursivo(pasta, incluir_raw=False):
    n = 0
    for dp, dns, fns in os.walk(pasta):
        dns[:] = [d for d in dns if not ignorar(d, incluir_raw)]
        n += sum(1 for f in fns if f.endswith(".md") and f.lower() != "index.md"
                 and not tem_controle(f))
    return n


SUB_LINHA_RE = re.compile(r"^- \[\[([^\]\|]+?)/index\|([^\]]+)\]\] — (.*)$")
SO_CONTAGEM_RE = re.compile(r"^\d+ notas?$")


def linha_subpasta(prefixo, d, n):
    plural = "nota" if n == 1 else "notas"
    return "- [[%s%s/index|%s]] — %d %s" % (prefixo, d, d, n, plural)


def reconciliar_subpastas(pasta, filhas, linhas, rel):
    """Atualiza o bloco 'Subpastas:' SEM destruir anotacao editorial.

    O indice raiz de varios vaults tem linha escrita a mao -- "00-Inbox — vazia
    de captura pendente (estado saudavel)", "`Anexos/` — vazia". Reescrever o
    bloco inteiro apagaria isso. Entao: linha cujo complemento e apenas "N notas"
    tem o numero atualizado; qualquer outro complemento fica intacto; subpasta
    nao listada e acrescentada; linha que nao casa o padrao nunca e tocada.

    A forma do link segue a que o arquivo ja usa (raiz do vault ou relativa) --
    trocar a forma geraria diff em 243 arquivos sem ganho nenhum.
    """
    i = next((k for k, l in enumerate(linhas) if CABEC_SUB_RE.match(l)), None)
    prefixo = "" if rel == "." else rel + "/"
    if i is None:
        if not filhas:
            return linhas, []
        novas = ["Subpastas:"] + [
            linha_subpasta(prefixo, d, conta_notas_recursivo(pasta / d)) for d in filhas
        ]
        h1 = next((k for k, l in enumerate(linhas) if l.startswith("# ")), 0)
        return linhas[:h1 + 1] + [""] + novas + linhas[h1 + 1:], []

    j = i + 1
    while j < len(linhas) and linhas[j].startswith("- "):
        j += 1
    bloco, vistas, mortas = [], set(), []
    for l in linhas[i + 1:j]:
        m = SUB_LINHA_RE.match(l)
        if not m:
            bloco.append(l)          # linha editorial: intocada
            continue
        alvo, label, resto = m.group(1), m.group(2), m.group(3)
        nome = alvo.split("/")[-1]
        vistas.add(nome)
        if not (pasta / nome).is_dir():
            mortas.append(nome)
            bloco.append(l)
            continue
        if SO_CONTAGEM_RE.match(resto.strip()):
            n = conta_notas_recursivo(pasta / nome)
            plural = "nota" if n == 1 else "notas"
            bloco.append("- [[%s/index|%s]] — %d %s" % (alvo, label, n, plural))
        else:
            bloco.append(l)          # complemento editorial: intocado
    for d in filhas:
        if d not in vistas:
            bloco.append(linha_subpasta(prefixo, d, conta_notas_recursivo(pasta / d)))
    return linhas[:i + 1] + bloco + linhas[j:], mortas


def titulo_padrao(vault, rel):
    if rel in (".", ""):
        return "# Índice — %s" % vault
    return "# Índice — %s (%s)" % (rel, vault)


def processar_pasta(pasta, raiz_vault, vault, todas, hoje, podar, nomes_vault=None):
    rel = os.path.relpath(pasta, raiz_vault).replace("\\", "/")
    notas = notas_da_pasta(pasta)
    filhas = subpastas_com_conteudo(pasta, todas)
    idx = pasta / "index.md"
    rel_idx = "index.md" if rel == "." else rel + "/index.md"

    if not idx.exists():
        corpo = ["---", "type: index", "updated: %s" % hoje, "---", "",
                 titulo_padrao(vault, rel), ""]
        if filhas:
            corpo += bloco_subpastas(pasta, filhas) + [""]
        if notas:
            corpo.append("Notas (%d):" % len(notas))
            for n in notas:
                corpo.append("- [[%s]] — %s" % (n[:-3], gancho_de(pasta / n)))
        return {"index": rel_idx, "acao": "criar", "faltando": [n[:-3] for n in notas],
                "mortas": [], "texto": "\n".join(corpo) + "\n"}

    raw = idx.read_bytes()
    crlf = b"\r\n" in raw
    txt = ler(idx)
    if txt is None:
        return {"index": rel_idx, "acao": "ilegivel", "faltando": [], "mortas": [],
                "texto": None}

    alvos = {m.split("/")[-1].strip().lower() for m in WIKILINK_RE.findall(txt)}
    baixo = txt.lower()
    faltando = [n[:-3] for n in notas
                if n[:-3].lower() not in alvos and n[:-3].lower() not in baixo]

    # Entrada morta e a que aponta para nota inexistente NO VAULT INTEIRO -- nao
    # basta faltar na pasta. Indice de caso referencia legitimamente checklist de
    # 50-Checklist e tese de 10-Wiki/Teses; a primeira versao deste detector
    # marcou 18 dessas como mortas e o --podar teria apagado link valido.
    universo = nomes_vault if nomes_vault is not None else {n[:-3].lower() for n in notas}
    mortas = []
    for linha in txt.splitlines():
        if not LINHA_NOTA_RE.match(linha):
            continue
        m = WIKILINK_RE.search(linha)
        if not m:
            continue
        alvo = m.group(1).split("/")[-1].strip()
        if alvo.lower() == "index":
            continue
        if alvo.lower() not in universo:
            mortas.append((alvo, linha))

    linhas = txt.replace("\r\n", "\n").split("\n")

    if podar and mortas:
        mortos = {l for _, l in mortas}
        linhas = [l for l in linhas if l not in mortos]

    for nome in faltando:
        nova = "- [[%s]] — %s" % (nome, gancho_de(pasta / (nome + ".md")))
        pos = None
        for i, l in enumerate(linhas):
            if CABEC_NOTAS_RE.match(l):
                j = i + 1
                while j < len(linhas) and linhas[j].startswith("- "):
                    j += 1
                pos = j
        if pos is None:
            h1 = next((i for i, l in enumerate(linhas) if l.startswith("# ")), len(linhas) - 1)
            linhas = linhas[:h1 + 1] + ["", "Notas (0):"] + linhas[h1 + 1:]
            pos = h1 + 3
        linhas.insert(pos, nova)

    linhas, sub_mortas = reconciliar_subpastas(pasta, filhas, linhas, rel)

    linhas = ["Notas (%d):" % len(notas) if CABEC_NOTAS_RE.match(l) else l for l in linhas]

    # `updated:` so muda quando o CORPO muda. Sem isto o gerador reescreveria os
    # 243 indices a cada execucao so para carimbar a data -- ruido no git e
    # mtime novo que faz o lint acusar "carimbo" em indice integro.
    corpo_novo = "\n".join(l for l in linhas if not l.startswith("updated:"))
    corpo_velho = "\n".join(l for l in txt.replace("\r\n", "\n").split("\n")
                            if not l.startswith("updated:"))
    if corpo_novo != corpo_velho:
        linhas = ["updated: %s" % hoje if l.startswith("updated:") else l for l in linhas]

    novo = "\n".join(linhas)
    if not novo.endswith("\n"):
        novo += "\n"
    if crlf:
        novo = novo.replace("\n", "\r\n")

    mudou = novo.encode("utf-8") != raw
    return {"index": rel_idx, "acao": "atualizar" if mudou else "ok",
            "faltando": faltando, "mortas": [a for a, _ in mortas] + sub_mortas,
            "texto": novo if mudou else None}


def fantasmas(raiz_vault):
    achados = []
    for dp, dns, fns in os.walk(raiz_vault):
        dns[:] = [d for d in dns if d not in {".git", ".obsidian"}]
        for f in fns:
            if tem_controle(f):
                achados.append(pathlib.Path(dp) / f)
    return achados


def main():
    ap = argparse.ArgumentParser(description="Reconcilia os index.md dos vaults.")
    ap.add_argument("vaults", nargs="*", help="nomes de vault (padrao: os da 6C)")
    ap.add_argument("--apply", action="store_true", help="grava (padrao: dry-run)")
    ap.add_argument("--podar", action="store_true", help="remove entrada de nota inexistente")
    ap.add_argument("--limpar-fantasmas", dest="limpar_fantasmas", action="store_true",
                    help="apaga arquivo de 0 byte com caractere de controle no nome")
    ap.add_argument("--incluir-raw", dest="incluir_raw", action="store_true",
                    help="indexa tambem 90-Arquivo e pastas de pipeline")
    ap.add_argument("--force", action="store_true", help="permite vault fora da 6C")
    ap.add_argument("--raiz", default=str(RAIZ))
    args = ap.parse_args()

    raiz = pathlib.Path(args.raiz)
    alvos = args.vaults or VAULTS_PADRAO
    for v in alvos:
        if v in VAULTS_FORA and not args.force:
            print("! %s esta fora da 6C (PADRAO-VAULT) — use --force para incluir." % v)
    alvos = [v for v in alvos if v not in VAULTS_FORA or args.force]

    hoje = datetime.date.today().isoformat()
    tot = {"criar": 0, "atualizar": 0, "ok": 0, "ilegivel": 0}
    tot_faltando = tot_mortas = tot_fant = 0

    for v in alvos:
        rv = raiz / v
        if not rv.is_dir():
            print("! vault inexistente: %s" % v)
            continue
        puladas = []
        todas = set(pastas_de_conteudo(rv, args.incluir_raw, puladas))
        nomes_vault = {q.stem.lower() for q in rv.rglob("*.md")
                       if ".git" not in q.parts and not tem_controle(q.name)}
        res = [processar_pasta(p, rv, v, todas, hoje, args.podar, nomes_vault)
               for p in sorted(todas)]
        fant = fantasmas(rv)
        pend = [r for r in res if r["acao"] in ("criar", "atualizar")]
        print("\n=== %s — %d pastas | %d indice(s) a mexer | %d fantasma(s)"
              % (v, len(todas), len(pend), len(fant)))
        for r in res:
            tot[r["acao"]] = tot.get(r["acao"], 0) + 1
            tot_faltando += len(r["faltando"])
            tot_mortas += len(r["mortas"])
            if r["acao"] in ("criar", "atualizar"):
                det = []
                if r["faltando"]:
                    det.append("+%d nota(s): %s" % (len(r["faltando"]), ", ".join(r["faltando"][:3])))
                if r["mortas"]:
                    det.append("%d morta(s): %s" % (len(r["mortas"]), ", ".join(r["mortas"][:3])))
                print("  [%s] %s%s" % (r["acao"], r["index"],
                                       ("  — " + " | ".join(det)) if det else ""))
                if args.apply and r["texto"] is not None:
                    (rv / r["index"]).write_bytes(r["texto"].encode("utf-8"))
            elif r["acao"] == "ilegivel":
                print("  [ilegivel] %s" % r["index"])
        tot_fant += len(fant)
        for f in fant[:5]:
            print("  [fantasma] %s (%d bytes)" % (f.relative_to(rv), f.stat().st_size))
        if len(fant) > 5:
            print("  [fantasma] ... +%d" % (len(fant) - 5))
        if fant and args.limpar_fantasmas and args.apply:
            n = 0
            for f in fant:
                if f.stat().st_size == 0:
                    f.unlink()
                    n += 1
            print("  -> %d fantasma(s) removido(s)" % n)

    print("\n--- TOTAL: criar %d | atualizar %d | ok %d | ilegivel %d"
          % (tot["criar"], tot["atualizar"], tot["ok"], tot["ilegivel"]))
    print("--- notas ausentes do indice: %d | entradas mortas: %d | fantasmas: %d"
          % (tot_faltando, tot_mortas, tot_fant))
    if not args.apply:
        print("\n(dry-run — nada foi gravado. Use --apply para gravar.)")


if __name__ == "__main__":
    main()
