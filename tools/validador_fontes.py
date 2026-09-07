#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validador_fontes.py — validador SINTATICO de citacoes de uma minuta (espec §4).

Para cada citacao encontrada na minuta, confere se ela existe (a) no contexto injetado
(atos do caso: `atos.jsonl`; chunks devolvidos pelo buscar.py --json) ou (b) numa fonte canonica
local (sumulas STJ/STF/vinculantes, temas de repercussao geral, artigos dos datasets
`<fonte>_artigos.json`, informativos e corpora de jurisprudencia por busca literal).

Tipos de citacao reconhecidos:
  SUMULA         "Súmula 7 do STJ", "Súmula 7/STJ", "Súmula n. 7 STJ", "Súmula Vinculante 14", "SV 14"
  TEMA           "Tema 1.100 do STJ", "Tema 280 STF", "Tema de Repercussão Geral 280"
  ARTIGO         "art. 41 do CPP", "art. 396-A do Código de Processo Penal", "art. 50 da Lei 9.605/98", "CPP, art. 157"
  PRECEDENTE     "REsp 1.234.567/SP", "HC 598.051/SP", "AgRg no AREsp 2.000.000", "RE 603.616", "RHC 12.345"
  ATO            "ID 136424905", "Num. 136424905", "fls. 45", "p. 4", "[ID 1364 | AUTOS_vol01 p. 4]"
  INFORMATIVO    "Informativo 687 do STJ", "Inf. 687/STJ"

Status por citacao: OK (achada), NAO_LOCALIZADA (nao achada em lugar nenhum: exige conferencia),
DIVERGENTE (artigo existe, mas o texto citado entre aspas nao bate com o dataset), CANCELADA
(sumula com situacao != vigente). "Nao localizada" NUNCA vira "nao existe": vira marcador na
minuta para o operador conferir (memoria informativo-nao-esgota-o-acordao).

Saida: <minuta>.validada.md (marcadores inline logo apos a citacao) + relatorio em Markdown/JSON.
Uso:
  python validador_fontes.py minuta.md --atos <extracted>/atos.jsonl [--contexto busca.json] [--json]
"""
from __future__ import annotations

import argparse
import difflib
import glob
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

def _layout():
    """Dois layouts: ~/.notebooklm/tools/<este>.py (datasets ao lado, corpora em ~/.notebooklm/<x>)
    ou <vault>/.claude/tools/pipeline/<este>.py (datasets em .., corpora em ../../corpora/<x>,
    cache de RG em ../../prazos). Devolve (TOOLS_datasets, BASE_corpora, PRAZOS)."""
    aqui = Path(__file__).resolve().parent
    tools = aqui if (aqui / "cp_artigos.json").exists() else aqui.parent
    claude = tools.parent
    if (claude / "corpora").is_dir():
        return tools, claude / "corpora", claude / "prazos"
    return tools, tools.parent, tools.parent / "prazos"


TOOLS, BASE, PRAZOS = _layout()
MARCA = "[VERIFICAÇÃO NECESSÁRIA: {motivo}]"

# --------------------------------------------------------------------------
# Normalizacao
# --------------------------------------------------------------------------
def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def so_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")


# --------------------------------------------------------------------------
# Fontes canonicas
# --------------------------------------------------------------------------
FONTES_ARTIGOS = {  # apelido na minuta -> arquivo do dataset
    "cpp": "cpp", "codigo de processo penal": "cpp",
    "cp": "cp", "codigo penal": "cp",
    "cpc": "cpc", "codigo de processo civil": "cpc",
    "cf": "cf", "constituicao federal": "cf", "constituicao": "cf", "crfb": "cf",
    "lep": "lep", "lei de execucao penal": "lep", "lei 7210": "lep", "lei 7.210": "lep",
    "cc": "cc", "codigo civil": "cc", "ctn": "ctn", "eaoab": "eaoab", "lindb": "lindb",
    "lei 9605": "lei9605", "lei 9.605": "lei9605", "lei 9099": "lei9099", "lei 9.099": "lei9099",
    "lei 11343": "lei11343", "lei 11.343": "lei11343", "lei 8072": "lei8072", "lei 8.072": "lei8072",
    "lei 9296": "lei9296", "lei 9.296": "lei9296", "lei 12850": "lei12850", "lei 12.850": "lei12850",
    "lei 9613": "lei9613", "lei 9.613": "lei9613", "lei 11340": "lei11340", "lei 11.340": "lei11340",
    "lei 13869": "lei13869", "lei 13.869": "lei13869", "lei 12965": "lei12965", "lei 12.965": "lei12965",
    "lei 13709": "lei13709", "lei 13.709": "lei13709", "lgpd": "lei13709", "lei 8137": "lei8137", "lei 8.137": "lei8137",
    "lei 13146": "lei13146", "lei 13.146": "lei13146", "lei 13431": "lei13431", "lei 13.431": "lei13431",
    "lei 12030": "lei12030", "lei 12.030": "lei12030", "lei 12830": "lei12830", "lei 12.830": "lei12830",
    "lei 9873": "lei9873", "lei 9.873": "lei9873", "cadh": "cadh", "pacto de sao jose": "cadh", "pidcp": "pidcp",
}
_cache: dict = {}


def dataset(nome: str):
    if nome not in _cache:
        p = TOOLS / f"{nome}_artigos.json"
        _cache[nome] = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    return _cache[nome]


def artigo_texto(fonte: str, numero: str) -> str | None:
    d = dataset(fonte)
    if not d:
        return None
    alvo = norm(numero).replace(" ", "")
    for a in d.get("artigos", []):
        if norm(str(a.get("artigo"))).replace(" ", "") == alvo:
            return a.get("texto", "")
    return None


def sumulas(tribunal: str) -> dict[int, dict]:
    k = f"sum_{tribunal}"
    if k not in _cache:
        arq = {"stj": "sumulas_stj.json", "stf": "sumulas_stf.json", "sv": "sumulas_vinculantes_stf.json"}[tribunal]
        d = json.loads((TOOLS / arq).read_text(encoding="utf-8"))
        lista = d.get("sumulas") or d.get("sumulas_vinculantes") or []
        if tribunal == "stf":
            lista = [s for s in lista if s.get("tipo", "sumula") == "sumula"]
        _cache[k] = {int(s["numero"]): s for s in lista}
    return _cache[k]


def temas_rg() -> dict[str, dict]:
    if "rg" not in _cache:
        out = {}
        for f in glob.glob(str(PRAZOS / "_cache_rg_*.json")):
            for t in json.loads(Path(f).read_text(encoding="utf-8")):
                out[str(t.get("numeroTema"))] = t
        _cache["rg"] = out
    return _cache["rg"]


CORPORA_GREP = [BASE / "informativo_stj" / "fontes", BASE / "informativo_stf" / "fontes", BASE / "clone_jurisprudencia",
                BASE / "boletins_precedentes_stj", BASE / "rstj", BASE / "criminal_player", BASE / "justo_processo"]


def grep_corpora(padroes: list[str], max_hits: int = 3) -> list[str]:
    """Busca literal (rg se houver, senao grep) de um numero de processo nos corpora locais."""
    import shutil
    import subprocess
    hits = []
    exe = shutil.which("rg")
    for pasta in CORPORA_GREP:
        if not pasta.exists():
            continue
        for pad in padroes:
            try:
                if exe:
                    cmd = [exe, "-l", "-i", "--max-count", "1", "-g", "*.md", "-g", "*.txt", pad, str(pasta)]
                else:
                    cmd = ["grep", "-rli", "--include=*.md", "--include=*.txt", pad, str(pasta)]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
                for ln in r.stdout.splitlines():
                    if ln.strip():
                        try:
                            hits.append(os.path.relpath(ln.strip(), BASE))
                        except ValueError:
                            hits.append(ln.strip())
                        if len(hits) >= max_hits:
                            return hits
            except (subprocess.TimeoutExpired, OSError):
                continue
    return hits


# --------------------------------------------------------------------------
# Contexto do caso
# --------------------------------------------------------------------------
class Contexto:
    def __init__(self, atos_jsonl: str | None, buscas: list[str]):
        self.ids: dict[str, list[dict]] = {}     # um id (ou variante de OCR) pode apontar para mais de um ato
        self.paginas: dict[tuple[str, int], dict] = {}
        self.chunks: list[dict] = []
        if atos_jsonl and Path(atos_jsonl).is_file():
            for l in io.open(atos_jsonl, encoding="utf-8"):
                a = json.loads(l)
                if a.get("id_pje"):
                    self.ids.setdefault(str(a["id_pje"]), []).insert(0, a)      # canonico na frente
                for i in a.get("id_variantes") or []:
                    self.ids.setdefault(str(i), []).append(a)
                for vol in {a.get("volume_ini"), a.get("volume_fim")}:
                    for p in range(int(a.get("pag_ini") or 0), int(a.get("pag_fim") or 0) + 1):
                        self.paginas[(vol, p)] = a
        for b in buscas:
            d = json.loads(Path(b).read_text(encoding="utf-8"))
            self.chunks += d.get("resultados", d if isinstance(d, list) else [])

    def tem_id(self, i: str, pagina: int | None = None) -> dict | None:
        """Ato do id; se varios atos partilham o id (variante de OCR), prefere o que contem a pagina."""
        i = so_digitos(i)
        cands = list(self.ids.get(i, []))
        if not cands:
            for k, v in self.ids.items():          # OCR: id parecido
                if difflib.SequenceMatcher(None, k, i).ratio() >= 0.9:
                    cands += v
        if not cands:
            return None
        if pagina is not None:
            for a in cands:
                if int(a.get("pag_ini") or 0) <= pagina <= int(a.get("pag_fim") or 0):
                    return a
        exatos = [a for a in cands if str(a.get("id_pje")) == i]
        return (exatos or cands)[0]

    def tem_pagina(self, vol: str | None, p: int) -> dict | None:
        if vol:
            for (v, pg), a in self.paginas.items():
                if pg == p and v and v.lower().endswith(vol.lower()):
                    return a
            return None
        cands = [a for (v, pg), a in self.paginas.items() if pg == p]
        return cands[0] if len(cands) == 1 else (cands[0] if cands else None)


# --------------------------------------------------------------------------
# Extracao de citacoes
# --------------------------------------------------------------------------
RX = {
    "SV": re.compile(r"\b(?:S[úu]mula\s+Vinculante|SV)\s*(?:n[º°o.]?\s*)?(\d{1,3})\b", re.I),
    "SUMULA": re.compile(r"\bS[úu]mula\s*(?:n[º°o.]?\s*)?(\d{1,4})\s*(?:/|do|da|de|-)?\s*(STJ|STF|TST|TSE)?\b(?!\s*Vinculante)", re.I),
    "SUMULA_PRE": re.compile(r"\b(STJ|STF)\s*,?\s*S[úu]mula\s*(?:n[º°o.]?\s*)?(\d{1,4})", re.I),
    "TEMA": re.compile(r"\bTema\s*(?:de\s+Repercuss[ãa]o\s+Geral\s*)?(?:n[º°o.]?\s*)?(\d{1,2}\.?\d{3}|\d{1,4})\s*(?:/|do|da|de|-)?\s*(STJ|STF)?", re.I),
    "ARTIGO": re.compile(r"\b(?:arts?\.?|artigos?)\s*(\d{1,4}(?:-[A-Z])?)\s*(?:,?\s*(?:§\s*\d+[ºo°]?|par[áa]grafo\s+[úu]nico|caput|inc(?:iso)?\.?\s*[IVXLC]+|[IVXLC]+|al[íi]nea\s+[a-z])\s*,?\s*){0,3}"
                         r"(?:,?\s*(?:d[oa]|do\s+|da\s+)?\s*(C[óo]digo\s+de\s+Processo\s+Penal|C[óo]digo\s+Penal|C[óo]digo\s+de\s+Processo\s+Civil|C[óo]digo\s+Civil|Constitui[çc][ãa]o(?:\s+Federal)?|Lei\s+de\s+Execu[çc][ãa]o\s+Penal|CPP|CPC|CP|CF|CRFB|LEP|CC|CTN|EAOAB|LINDB|LGPD|CADH|PIDCP|Lei\s*(?:n[º°o.]?\s*)?\d{1,2}\.?\d{3}(?:/\d{2,4})?))?", re.I),
    "ARTIGO_PRE": re.compile(r"\b(CPP|CPC|CP|CF|LEP|CC|CTN|Lei\s*(?:n[º°o.]?\s*)?\d{1,2}\.?\d{3}(?:/\d{2,4})?)\s*,\s*arts?\.?\s*(\d{1,4}(?:-[A-Z])?)", re.I),
    "PRECEDENTE": re.compile(r"\b((?:AgRg\s+n[oa]s?\s+|AgInt\s+n[oa]s?\s+|EDcl\s+n[oa]s?\s+)?(?:REsp|AREsp|HC|RHC|RE|ARE|RMS|MS|Rcl|ADI|ADPF|ADC|EREsp|AgRg|AgInt|RvCr|CC|ExtR|Pet|Inq|AP)\.?)\s*(?:n[º°o.]?\s*)?(\d{1,3}(?:\.\d{3})+|\d{4,7})(?:\s*/\s*([A-Z]{2}))?", re.I),
    "INFORMATIVO": re.compile(r"\bInf(?:ormativo)?\.?\s*(?:n[º°o.]?\s*)?(\d{1,4})\s*(?:/|do|da|de|-)?\s*(STJ|STF)?", re.I),
    "ATO_ID": re.compile(r"\b(?:ID|Id\.?|Num\.?)\s*(?:n[º°o.]?\s*)?(\d{6,12})\b"),
    "ATO_PAG": re.compile(r"\b(?:fls?\.|folhas?|p\.|p[áa]g\.?|p[áa]ginas?)\s*(\d{1,4})(?:\s*[-–/]\s*(\d{1,4}))?", re.I),
    "ANCORA": re.compile(r"\[ID\s*(\d+|-)\s*\|\s*([A-Za-z0-9_\-]+)?\s*p\.\s*(\d+)"),
}
CAPUT_APENAS = re.compile(r"^(\d{1,4}(?:-[A-Z])?)")


def fonte_artigo(rotulo: str | None) -> str | None:
    if not rotulo:
        return None
    r = norm(rotulo)
    r = re.sub(r"\bn\b|\bno\b", "", r).strip()
    r = re.sub(r"(lei) (\d{1,2}) ?(\d{3})", r"\1 \2\3", r)          # "lei 9 605" -> "lei 9605"
    r = re.sub(r"(lei \d{4,5}) \d{2,4}$", r"\1", r)                    # tira o ano
    return FONTES_ARTIGOS.get(r)


def citacoes(texto: str) -> list[dict]:
    out = []
    linhas = texto.split("\n")
    pos_linha = [0]
    for ln in linhas:
        pos_linha.append(pos_linha[-1] + len(ln) + 1)

    def linha_de(pos: int) -> int:
        import bisect
        return bisect.bisect_right(pos_linha, pos)

    def add(tipo, m, **kw):
        out.append({"tipo": tipo, "texto": m.group(0).strip(), "inicio": m.start(), "fim": m.end(), "linha": linha_de(m.start())} | kw)

    for m in RX["SV"].finditer(texto):
        add("SUMULA", m, tribunal="sv", numero=int(m.group(1)))
    for m in RX["SUMULA"].finditer(texto):
        if any(c["tipo"] == "SUMULA" and c["inicio"] <= m.start() < c["fim"] for c in out):
            continue
        add("SUMULA", m, tribunal=(m.group(2) or "").lower() or None, numero=int(m.group(1)))
    for m in RX["SUMULA_PRE"].finditer(texto):
        add("SUMULA", m, tribunal=m.group(1).lower(), numero=int(m.group(2)))
    for m in RX["TEMA"].finditer(texto):
        add("TEMA", m, tribunal=(m.group(2) or "").lower() or None, numero=so_digitos(m.group(1)))
    for m in RX["ARTIGO"].finditer(texto):
        add("ARTIGO", m, numero=m.group(1), rotulo=m.group(2))
    for m in RX["ARTIGO_PRE"].finditer(texto):
        add("ARTIGO", m, numero=m.group(2), rotulo=m.group(1))
    for m in RX["PRECEDENTE"].finditer(texto):
        add("PRECEDENTE", m, classe=m.group(1), numero=m.group(2), uf=m.group(3))
    for m in RX["INFORMATIVO"].finditer(texto):
        add("INFORMATIVO", m, tribunal=(m.group(2) or "").lower() or None, numero=int(m.group(1)))
    for m in RX["ANCORA"].finditer(texto):
        add("ANCORA", m, id_pje=m.group(1), volume=m.group(2), pagina=int(m.group(3)))
    for m in RX["ATO_ID"].finditer(texto):
        if any(c["tipo"] == "ANCORA" and c["inicio"] <= m.start() < c["fim"] for c in out):
            continue
        add("ATO_ID", m, id_pje=m.group(1))
    for m in RX["ATO_PAG"].finditer(texto):
        if any(c["tipo"] == "ANCORA" and c["inicio"] <= m.start() < c["fim"] for c in out):
            continue
        add("ATO_PAG", m, pagina=int(m.group(1)), pagina_fim=int(m.group(2)) if m.group(2) else None)
    out.sort(key=lambda c: c["inicio"])
    return out


# --------------------------------------------------------------------------
# Verificacao
# --------------------------------------------------------------------------
def aspas_proximas(texto: str, ini: int, fim: int) -> str | None:
    """Texto entre aspas ADJACENTE a citacao (comeca ate 160 chars depois dela, ou termina ate
    60 chars antes). Janela larga pegava a aspa do artigo vizinho e acusava divergencia falsa."""
    depois = texto[fim: fim + 800]
    m = re.match(r"[^“\"]{0,160}[“\"]([^”\"]{25,600})[”\"]", depois)
    if m:
        return m.group(1)
    antes = texto[max(0, ini - 700): ini]
    m = re.search(r"[“\"]([^”\"]{25,600})[”\"][^“\"]{0,60}$", antes)
    return m.group(1) if m else None


def verificar(c: dict, ctx: Contexto, texto: str, corpora: bool) -> dict:
    r = {"status": "NAO_LOCALIZADA", "fonte": None, "detalhe": None}
    t = c["tipo"]
    if t == "SUMULA":
        trib = c.get("tribunal")
        cands = [trib] if trib in ("stj", "stf", "sv") else ["stj", "stf"]
        achou = []
        for tr in cands:
            s = sumulas(tr).get(c["numero"])
            if s:
                achou.append((tr, s))
        if achou:
            if len(achou) > 1 and not trib:
                r |= {"status": "AMBIGUA", "detalhe": "existe no STJ e no STF; a minuta não diz o tribunal",
                      "fonte": " / ".join(f"Súmula {c['numero']} {tr.upper()}: {s['enunciado'][:90]}…" for tr, s in achou)}
            else:
                tr, s = achou[0]
                sit = (s.get("situacao") or "vigente").lower()
                r |= {"status": "OK" if sit.startswith("vigente") else "CANCELADA", "fonte": f"sumulas_{'vinculantes_stf' if tr == 'sv' else tr}.json",
                      "detalhe": f"{s['enunciado'][:160]}…" + ("" if sit.startswith("vigente") else f" [situação: {sit}]")}
        else:
            r["detalhe"] = f"Súmula {c['numero']} não consta em {', '.join(x.upper() for x in cands)} (dataset local)"
    elif t == "TEMA":
        tm = temas_rg().get(str(c["numero"]))
        if tm and c.get("tribunal") in (None, "stf"):
            r |= {"status": "OK", "fonte": "prazos/_cache_rg_*.json (STF)", "detalhe": f"{tm.get('siglaClasse')} {tm.get('numeroProcesso')}: {(tm.get('descricaoTese') or '')[:150]}…"}
        else:
            hits = grep_corpora([rf"Tema\s*(n[.º]?\s*)?{c['numero']}\b"]) if corpora else []
            if hits:
                r |= {"status": "OK", "fonte": "; ".join(hits), "detalhe": "tema citado nos corpora locais (conferir se é repetitivo STJ ou RG STF)"}
            else:
                r["detalhe"] = "tema não achado no cache de RG do STF nem nos corpora locais (repetitivos STJ não têm dataset próprio: conferir no BNP/`/bnp`)"
    elif t == "ARTIGO":
        fonte = fonte_artigo(c.get("rotulo"))
        if not fonte:
            r |= {"status": "SEM_FONTE", "detalhe": f"não identifiquei o diploma ({c.get('rotulo') or 'nenhum rótulo junto ao artigo'}); cite como 'art. N do CPP'"}
        else:
            txt = artigo_texto(fonte, c["numero"])
            if txt is None:
                r["detalhe"] = f"art. {c['numero']} não existe no dataset {fonte}_artigos.json (conferir: pode ser lacuna do dataset)"
            else:
                r |= {"status": "OK", "fonte": f"{fonte}_artigos.json", "detalhe": txt[:140].replace("\n", " ") + "…"}
                citado = aspas_proximas(texto, c["inicio"], c["fim"])
                if citado:
                    ratio = difflib.SequenceMatcher(None, norm(citado), norm(txt)).find_longest_match(0, len(norm(citado)), 0, len(norm(txt))).size / max(1, len(norm(citado)))
                    if ratio < 0.5:
                        r |= {"status": "DIVERGENTE", "detalhe": f"o texto entre aspas perto da citação não aparece na redação do art. {c['numero']} ({fonte}); conferir se é paráfrase ou artigo errado"}
    elif t == "PRECEDENTE":
        num = c["numero"]
        variantes = [re.escape(num), re.escape(so_digitos(num))]
        if "." not in num and len(num) > 3:
            variantes.append(re.escape(f"{int(num):,}".replace(",", ".")))
        hits = grep_corpora([rf"\b{c['classe'].split()[-1]}\.?\s*(n[.º]?\s*)?{v}" for v in variantes]) if corpora else []
        if hits:
            r |= {"status": "OK", "fonte": "; ".join(hits), "detalhe": "número consta nos corpora locais; a TESE atribuída ainda precisa do verificador-citacoes"}
        else:
            r["detalhe"] = "número não consta nos corpora locais (informativos, clone STF·STJ·TRF1, boletins, RSTJ). Não prova inexistência: conferir em scon.stj.jus.br / portal.stf.jus.br"
    elif t == "INFORMATIVO":
        trib = c.get("tribunal") or "stj"
        pasta = BASE / ("informativo_stj" if trib == "stj" else "informativo_stf") / "fontes"
        arqs = list(pasta.glob(f"Inf{int(c['numero']):04d}*.md")) if pasta.exists() else []
        if arqs:
            r |= {"status": "OK", "fonte": os.path.relpath(arqs[0], BASE)}
        else:
            r["detalhe"] = f"Informativo {c['numero']} {trib.upper()} não está no corpus local" + (" (2019 do STJ inteiro falta no acervo)" if trib == "stj" and 639 <= c["numero"] <= 661 else "")
    elif t in ("ATO_ID", "ANCORA"):
        i = c.get("id_pje")
        if i and i != "-":
            a = ctx.tem_id(i, c.get("pagina"))
            if a:
                r |= {"status": "OK", "fonte": f"atos.jsonl seq {a['seq']} ({a.get('tipo')}, {a.get('volume_ini')} p. {a.get('pag_ini')}-{a.get('pag_fim')})"}
                if t == "ANCORA" and not (int(a.get("pag_ini") or 0) <= c["pagina"] <= int(a.get("pag_fim") or 10**9)):
                    r |= {"status": "DIVERGENTE", "detalhe": f"ID existe, mas a página {c['pagina']} está fora do ato ({a.get('pag_ini')}-{a.get('pag_fim')})"}
            else:
                r["detalhe"] = "ID não consta nos atos fatiados deste caso"
        elif t == "ANCORA":
            a = ctx.tem_pagina(c.get("volume"), c["pagina"])
            r |= ({"status": "OK", "fonte": f"atos.jsonl seq {a['seq']}"} if a else {"detalhe": "página não consta nos atos fatiados"})
    elif t == "ATO_PAG":
        a = ctx.tem_pagina(None, c["pagina"])
        if a:
            r |= {"status": "OK", "fonte": f"atos.jsonl seq {a['seq']} ({a.get('tipo')})", "detalhe": "página existe; sem volume a conferência é fraca — prefira a âncora [ID | vol p. N]"}
        else:
            r["detalhe"] = "página não consta nos atos fatiados (ou o volume não foi indicado)"
    return c | r


def anotar(texto: str, resultados: list[dict]) -> str:
    """Insere o marcador logo apos cada citacao com problema (de tras para a frente)."""
    saida = texto
    for c in sorted(resultados, key=lambda x: -x["fim"]):
        if c["status"] in ("OK",):
            continue
        motivo = {"NAO_LOCALIZADA": "citação não localizada na base documental",
                  "DIVERGENTE": "citação diverge da fonte",
                  "CANCELADA": "súmula cancelada/superada",
                  "AMBIGUA": "tribunal não indicado (STJ ou STF)",
                  "SEM_FONTE": "diploma legal não identificado"}[c["status"]]
        saida = saida[:c["fim"]] + " " + MARCA.format(motivo=motivo) + saida[c["fim"]:]
    return saida


def relatorio(res: list[dict], minuta: str) -> str:
    n = len(res)
    ok = sum(r["status"] == "OK" for r in res)
    L = [f"# Validação de fontes — {Path(minuta).name}", "",
         f"- citações encontradas: **{n}** · OK: {ok} · com alerta: **{n - ok}**",
         f"- status: **{'APROVADO' if n == ok else 'ALERTA (' + str(n - ok) + ')'}**", "",
         "| linha | tipo | citação | status | fonte / detalhe |", "|---|---|---|---|---|"]
    for r in res:
        det = (r.get("fonte") or "") + ((" — " if r.get("fonte") and r.get("detalhe") else "") + (r.get("detalhe") or ""))
        L.append(f"| {r['linha']} | {r['tipo']} | {r['texto'][:60]} | {r['status']} | {det[:200]} |")
    L += ["", "> Sintático: confere existência e redação. Se a TESE atribuída ao precedente é a que ele firmou, é trabalho do agente `verificador-citacoes` (lista em `citacoes_para_verificar.json`).",
          "> 'Não localizada' nunca prova inexistência (memória `informativo-nao-esgota-o-acordao`): conferir na fonte oficial antes de excluir."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("minuta")
    ap.add_argument("--atos", help="atos.jsonl do caso")
    ap.add_argument("--contexto", action="append", default=[], help="JSON do buscar.py --json (pode repetir)")
    ap.add_argument("--sem-corpora", action="store_true", help="não faz grep nos corpora (mais rápido)")
    ap.add_argument("--saida-dir", help="pasta para .validada.md e relatório (padrão: ao lado da minuta)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    texto = io.open(a.minuta, encoding="utf-8").read()
    ctx = Contexto(a.atos, a.contexto)
    res = [verificar(c, ctx, texto, not a.sem_corpora) for c in citacoes(texto)]
    p = Path(a.minuta)
    dest = Path(a.saida_dir) if a.saida_dir else p.parent
    dest.mkdir(parents=True, exist_ok=True)
    io.open(dest / (p.stem + ".validada.md"), "w", encoding="utf-8", newline="\n").write(anotar(texto, res))
    io.open(dest / (p.stem + ".validacao-fontes.md"), "w", encoding="utf-8", newline="\n").write(relatorio(res, a.minuta))
    pend = [{"linha": r["linha"], "tipo": r["tipo"], "citacao": r["texto"], "status": r["status"], "detalhe": r.get("detalhe")}
            for r in res if r["tipo"] in ("PRECEDENTE", "SUMULA", "TEMA", "INFORMATIVO")]
    io.open(dest / (p.stem + ".citacoes_para_verificar.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(pend, ensure_ascii=False, indent=1))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(relatorio(res, a.minuta))
        print(f"-> {dest / (p.stem + '.validada.md')}")
    return 0 if all(r["status"] == "OK" for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
