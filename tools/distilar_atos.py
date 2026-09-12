#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distilar_atos.py — distiladores com LLM LOCAL, um ato por chamada (espec §3.3, fase 6).

Regras que vem do benchmark (Criminal/40-Recursos/benchmark-llm-local.md):
  * so atos ate --max-tokens (padrao 2.000; ~7k chars) vao ao modelo local; ate --ate (padrao 5.000)
    so com a opcao; acima disso o ato e' listado em `distill/para_nuvem.json` (fase 7).
  * temperatura 0, `think` desligado, saida JSON com schema imposto pelo Ollama (`format`).
  * a geracao e' o gargalo (~3 tok/s): trechos curtos e listas curtas; num_predict limitado.
  * o modelo NAO sabe direito: ele so copia e organiza o que esta no ato. Todo item tem `trecho`
    literal, e o script confere se o trecho existe no ato (`localizado`). Item nao localizado e'
    marcado, nunca apagado.
  * cache por hash do ato em distill/llm/<distilador>/<seq>.json — rerodar so refaz o que mudou.

Distiladores e atos que cada um le:
  controversia  DENUNCIA, ADITAMENTO, QUEIXA-CRIME (imputacao) · RESPOSTA A ACUSACAO, ALEGACOES FINAIS,
                HABEAS CORPUS, PEDIDO DE LIBERDADE, RAZOES DE APELACAO, APELACAO (teses)
  nulidades     DECISAO, DESPACHO, SENTENCA, ACORDAO, TERMO DE AUDIENCIA, AUDIENCIA DE CUSTODIA,
                AUTO DE PRISAO EM FLAGRANTE, MANDADO, CARTA PRECATORIA, LAUDO, AUTO DE EXIBICAO E APREENSAO,
                AUTO DE RECONHECIMENTO, INTIMACAO, CERTIDAO
  prisao        atos acima cujo texto fala em prisao/flagrante/preventiva/liberdade/cautelar
  dosimetria    SENTENCA, ACORDAO cujo texto tem "pena-base" ou "fixo a pena"

Uso:
  python distilar_atos.py <extracted>/atos.jsonl [--distiladores controversia,nulidades] [--modelo qwen3:8b]
                          [--max-tokens 2000] [--ate 5000] [--limite N] [--so-relatorio]
Saida: distill/llm/<distilador>/<seq>.json (bruto) e distill/{controversia,nulidades,prisao,dosimetria}.md
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

OLLAMA = "http://127.0.0.1:11434"
CHARS_POR_TOKEN = 3.0     # portugues com OCR: conservador

# --------------------------------------------------------------------------
# Schemas (curtos de proposito: a geracao custa ~3 tok/s)
# --------------------------------------------------------------------------
def _item(*campos: str, req: tuple[str, ...] = ()) -> dict:
    return {"type": "object", "properties": {c: {"type": "string"} for c in campos} | {"trecho": {"type": "string"}},
            "required": list(req) + ["trecho"]}


def _lista(item: dict, maximo: int = 8) -> dict:
    return {"type": "array", "items": item, "maxItems": maximo}


SCHEMAS = {
    "imputacao": {"type": "object", "properties": {
        "tipos_penais_imputados": _lista(_item("dispositivo", req=("dispositivo",)), 6),
        "fatos_imputados": _lista(_item("fato", "data_ou_periodo", "local", req=("fato",)), 8),
        "qualificadoras_majorantes": _lista(_item("descricao", req=("descricao",)), 6),
        "provas_indicadas": _lista(_item("prova", req=("prova",)), 8),
        "acordos_negados_ou_propostos": _lista(_item("instituto", "motivo", req=("instituto",)), 4),
    }, "required": ["tipos_penais_imputados", "fatos_imputados", "qualificadoras_majorantes", "provas_indicadas", "acordos_negados_ou_propostos"]},
    "teses": {"type": "object", "properties": {
        "preliminares": _lista(_item("tese", "fundamento", req=("tese",)), 8),
        "merito": _lista(_item("tese", "fundamento", req=("tese",)), 8),
        "dosimetria_ou_subsidiarias": _lista(_item("tese", req=("tese",)), 6),
        "provas_requeridas_ou_invocadas": _lista(_item("prova", req=("prova",)), 8),
        "pedidos": _lista(_item("pedido", req=("pedido",)), 8),
    }, "required": ["preliminares", "merito", "dosimetria_ou_subsidiarias", "provas_requeridas_ou_invocadas", "pedidos"]},
    "nulidades": {"type": "object", "properties": {
        "o_que_o_ato_decide_ou_certifica": {"type": "string"},
        "fundamentacao": {"type": "string", "enum": ["concreta", "generica", "ausente", "nao_se_aplica"]},
        "intimacao_da_defesa_mencionada": {"type": "string", "enum": ["sim", "nao", "nao_se_aplica"]},
        "motivos_invocados": _lista(_item("motivo", req=("motivo",)), 6),
        "prazos_ou_datas_citados": _lista(_item("evento", "data", req=("evento",)), 6),
        "requerimentos_da_defesa_apreciados": _lista(_item("requerimento", "resultado", req=("requerimento",)), 6),
    }, "required": ["o_que_o_ato_decide_ou_certifica", "fundamentacao", "intimacao_da_defesa_mencionada", "motivos_invocados", "prazos_ou_datas_citados", "requerimentos_da_defesa_apreciados"]},
    "prisao": {"type": "object", "properties": {
        "medida": {"type": "string"},
        "situacao": {"type": "string", "enum": ["decretada", "mantida", "revogada", "substituida", "relaxada", "negada", "nao_se_aplica"]},
        "fundamentos": _lista(_item("fundamento", req=("fundamento",)), 6),
        "datas": _lista(_item("evento", "data", req=("evento",)), 6),
        "cautelares_alternativas": _lista(_item("medida", req=("medida",)), 6),
    }, "required": ["medida", "situacao", "fundamentos", "datas", "cautelares_alternativas"]},
    "dosimetria": {"type": "object", "properties": {
        "resultado": {"type": "string"},
        "pena_base": _lista(_item("circunstancia", "valoracao", "fracao", req=("circunstancia",)), 8),
        "segunda_fase": _lista(_item("circunstancia", "fracao", req=("circunstancia",)), 6),
        "terceira_fase": _lista(_item("causa", "fracao", req=("causa",)), 6),
        "pena_definitiva": {"type": "string"},
        "regime": {"type": "string"},
        "substituicao_ou_sursis": {"type": "string"},
    }, "required": ["resultado", "pena_base", "segunda_fase", "terceira_fase", "pena_definitiva", "regime", "substituicao_ou_sursis"]},
}

PROMPT_BASE = (
    "Você extrai dados de um ato processual penal brasileiro para um advogado de defesa. "
    "Use SOMENTE o texto do ato abaixo. Não use conhecimento externo, não complete lacunas, não interprete além do escrito. "
    "Se algo não constar, deixe a lista vazia ou o campo em branco. "
    "Cada item tem um campo 'trecho': copie LITERALMENTE de 4 a 12 palavras do texto que provam o item (sem parafrasear, sem reticências, NUNCA mais de 12 palavras). "
    "Seja econômico: campos curtos, no máximo 6 itens por lista, sem repetir itens. "
    "Datas no formato AAAA-MM-DD quando o texto permitir; senão copie como está. Responda só o JSON.\n"
)
INSTRUCOES = {
    "imputacao": "Tarefa: mapear a IMPUTAÇÃO: tipos penais imputados (só os que o acusador atribui ao réu; artigos processuais como CPP 28-A ou Lei 9.099 art. 76 vão em 'acordos_negados_ou_propostos'), fatos com data/período e local, qualificadoras/majorantes, provas indicadas.",
    "teses": "Tarefa: mapear as TESES DA DEFESA: preliminares (nulidades, incompetência, inépcia, prescrição), mérito (atipicidade, absolvição, excludentes, insuficiência de prova), subsidiárias de pena, provas requeridas ou invocadas, pedidos.",
    "nulidades": "Tarefa (só descrição, sem julgar): dizer o que o ato decide/certifica; classificar a fundamentação (concreta = cita fatos deste processo; genérica = só fórmulas; ausente = não motiva; nao_se_aplica = ato de mero expediente); dizer se o texto menciona intimação da defesa; listar os MOTIVOS que o próprio ato invoca; listar prazos e datas citados; listar requerimentos da defesa que o ato aprecia e o resultado (deferido/indeferido/não apreciado). Não aponte vícios nem nulidades.",
    "prisao": "Tarefa: identificar a medida cautelar pessoal tratada (flagrante, temporária, preventiva, domiciliar, cautelares do CPP 319), a situação, os fundamentos invocados, as datas e as cautelares alternativas mencionadas.",
    "dosimetria": "Tarefa: extrair a dosimetria: resultado (condenação/absolvição), circunstâncias da pena-base com a valoração e fração, agravantes/atenuantes, causas de aumento/diminuição, pena definitiva, regime, substituição ou sursis.",
}

ATOS_POR_DISTILADOR = {
    "controversia": {"DENUNCIA", "ADITAMENTO DENUNCIA", "QUEIXA-CRIME", "RESPOSTA A ACUSACAO", "ALEGACOES FINAIS",
                     "HABEAS CORPUS", "PEDIDO DE LIBERDADE", "RAZOES DE APELACAO", "APELACAO", "CONTRARRAZOES"},
    "nulidades": {"DECISAO", "DESPACHO", "SENTENCA", "ACORDAO", "TERMO DE AUDIENCIA", "AUDIENCIA DE CUSTODIA",
                  "AUTO DE PRISAO EM FLAGRANTE", "MANDADO", "CARTA PRECATORIA", "LAUDO", "AUTO DE EXIBICAO E APREENSAO",
                  "AUTO DE RECONHECIMENTO", "INTIMACAO", "CERTIDAO", "PRONUNCIA", "RECEBIMENTO DENUNCIA"},
    "prisao": {"DECISAO", "SENTENCA", "ACORDAO", "TERMO DE AUDIENCIA", "AUDIENCIA DE CUSTODIA", "AUTO DE PRISAO EM FLAGRANTE",
               "PEDIDO DE LIBERDADE", "HABEAS CORPUS", "MANDADO"},
    "dosimetria": {"SENTENCA", "ACORDAO"},
}
ACUSACAO = {"DENUNCIA", "ADITAMENTO DENUNCIA", "QUEIXA-CRIME"}
RE_PRISAO = re.compile(r"pris[ãa]o|flagrante|preventiva|tempor[áa]ria|liberdade\s+provis[óo]ria|cautelar|custódia|custodia", re.I)
RE_DOSIMETRIA = re.compile(r"pena[- ]base|fixo\s+a\s+pena|circunst[âa]ncias\s+judiciais|art\.?\s*59", re.I)


# --------------------------------------------------------------------------
def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def localizar(trecho: str, texto_norm: str) -> bool:
    t = _norm(trecho or "")
    if len(t) < 8:
        return False
    if t in texto_norm:
        return True
    # OCR: aceita se 2 de 3 tercos do trecho aparecem
    palavras = t.split()
    if len(palavras) < 6:
        return False
    k = len(palavras) // 3
    partes = [" ".join(palavras[:k]), " ".join(palavras[k:2 * k]), " ".join(palavras[2 * k:])]
    return sum(p in texto_norm for p in partes if len(p) >= 8) >= 2


def conferir(obj, texto_norm: str) -> tuple[int, int]:
    """Marca `localizado` em todo dict com `trecho`. -> (ok, total)."""
    ok = tot = 0
    if isinstance(obj, dict):
        if "trecho" in obj:
            tot += 1
            obj["localizado"] = localizar(obj["trecho"], texto_norm)
            ok += obj["localizado"]
        for v in obj.values():
            a, b = conferir(v, texto_norm)
            ok, tot = ok + a, tot + b
    elif isinstance(obj, list):
        for v in obj:
            a, b = conferir(v, texto_norm)
            ok, tot = ok + a, tot + b
    return ok, tot


def reparar_json(bruto: str):
    """Saida truncada pelo num_predict: corta no ultimo item completo e fecha as estruturas.
    Salva o que ja foi extraido em vez de perder o ato inteiro."""
    s = bruto.rstrip()
    # recua ate o ultimo '}' que fecha um item (ou ']' que fecha uma lista)
    for corte in range(len(s), 0, -1):
        if s[corte - 1] not in "}]":
            continue
        cand = s[:corte]
        pilha = []
        dentro, esc = False, False
        for ch in cand:
            if dentro:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    dentro = False
                continue
            if ch == '"':
                dentro = True
            elif ch in "{[":
                pilha.append("}" if ch == "{" else "]")
            elif ch in "}]":
                if pilha and pilha[-1] == ch:
                    pilha.pop()
                else:
                    break
        else:
            if dentro:
                continue
            tent = cand.rstrip().rstrip(",") + "".join(reversed(pilha))
            try:
                return json.loads(tent)
            except json.JSONDecodeError:
                continue
    return None


def chamar(modelo: str, prompt: str, schema: dict, num_ctx: int, num_predict: int) -> tuple[dict, dict]:
    body = {"model": modelo, "prompt": prompt, "stream": False, "think": False, "format": schema,
            "options": {"temperature": 0, "num_ctx": num_ctx, "num_predict": num_predict}}
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        d = json.loads(r.read())
    bruto = d.get("response") or "{}"
    try:
        out = json.loads(bruto)
    except json.JSONDecodeError:
        out = reparar_json(bruto)
        if out is None:
            out = {"_erro": "JSON inválido", "_bruto": bruto[:500]}
        else:
            out["_reparado"] = True
    met = {"prompt_tokens": d.get("prompt_eval_count"), "gerados": d.get("eval_count"),
           "seg_prompt": round((d.get("prompt_eval_duration") or 0) / 1e9, 1),
           "seg_geracao": round((d.get("eval_duration") or 0) / 1e9, 1), "truncado": d.get("done_reason") == "length"}
    return out, met


def corpo_do_ato(caminho: Path) -> str:
    md = io.open(caminho, encoding="utf-8").read()
    corpo = md.split("\n---\n", 1)[-1]
    corpo = re.sub(r"^## \[[^\]]+\].*$", "", corpo, flags=re.M)     # marcas de pagina fora do prompt
    return re.sub(r"\n{3,}", "\n\n", corpo).strip()


def tarefas(atos: list[dict], extracted: Path, distiladores: list[str]) -> list[tuple[str, str, dict]]:
    """-> [(distilador, schema_key, ato)]"""
    out = []
    for a in atos:
        t = a.get("tipo")
        for d in distiladores:
            if t not in ATOS_POR_DISTILADOR[d]:
                continue
            if d == "controversia":
                out.append((d, "imputacao" if t in ACUSACAO else "teses", a))
            elif d == "nulidades":
                out.append((d, "nulidades", a))
            elif d in ("prisao", "dosimetria"):
                try:
                    txt = corpo_do_ato(extracted / a["arquivo"])
                except OSError:
                    continue
                if (RE_PRISAO if d == "prisao" else RE_DOSIMETRIA).search(txt):
                    out.append((d, d, a))
    return out


# --------------------------------------------------------------------------
# Relatorios
# --------------------------------------------------------------------------
def _anc(a: dict) -> str:
    return f"[ID {a.get('id_pje') or '-'} | {a.get('volume_ini')} p. {a.get('pag_ini')}" + \
           (f"–{a.get('pag_fim')}" if a.get("pag_fim") != a.get("pag_ini") else "") + f" | {a.get('tipo')} | {a.get('data_juntada') or 'sem data'}]"


def _mark(it: dict) -> str:
    return "" if it.get("localizado") else " **[TRECHO NÃO LOCALIZADO NO ATO]**"


def _linhas(itens: list[dict], campo: str, extra: tuple[str, ...] = ()) -> list[str]:
    out = []
    for it in itens or []:
        ex = " · ".join(f"{e}: {it[e]}" for e in extra if it.get(e))
        out.append(f"  - {it.get(campo, '')}" + (f" ({ex})" if ex else "") + f" — “{(it.get('trecho') or '')[:140]}”{_mark(it)}")
    return out


def relatorio_controversia(res: list[tuple[dict, dict, dict]], cnj) -> str:
    L = [f"# Quadro de controvérsia — {cnj}", "", "> Extraído por LLM local (temperatura 0) de cada ato, item a item com trecho literal conferido. "
         "Hipótese de trabalho, não conclusão: conferir cada linha no ato antes de usar.", ""]
    # decide pelo que foi extraido (schema), nao pelo tipo do ato: razoes do MP classificadas como
    # DENUNCIA pela prosa foram extraidas com --schema-de 83=teses e devem aparecer como teses
    imp = [(a, o) for a, o, m in res if "tipos_penais_imputados" in o]
    tes = [(a, o) for a, o, m in res if "preliminares" in o]
    L += ["## Imputação (acusação)", ""]
    for a, o in imp:
        L += [f"### {_anc(a)}", "", "- **Tipos penais imputados:**"] + _linhas(o.get("tipos_penais_imputados"), "dispositivo")
        L += ["- **Fatos imputados:**"] + _linhas(o.get("fatos_imputados"), "fato", ("data_ou_periodo", "local"))
        L += ["- **Qualificadoras / majorantes:**"] + (_linhas(o.get("qualificadoras_majorantes"), "descricao") or ["  - (nenhuma extraída)"])
        L += ["- **Provas indicadas:**"] + _linhas(o.get("provas_indicadas"), "prova")
        L += ["- **Acordos (ANPP, transação, sursis processual):**"] + (_linhas(o.get("acordos_negados_ou_propostos"), "instituto", ("motivo",)) or ["  - (nada)"]) + [""]
    L += ["## Teses (defesa, e acusação quando extraída como teses — ex.: razões de recurso do MP)", ""]
    for a, o in tes:
        L += [f"### {_anc(a)}", "", "- **Preliminares:**"] + (_linhas(o.get("preliminares"), "tese", ("fundamento",)) or ["  - (nenhuma)"])
        L += ["- **Mérito:**"] + (_linhas(o.get("merito"), "tese", ("fundamento",)) or ["  - (nenhuma)"])
        L += ["- **Subsidiárias / pena:**"] + (_linhas(o.get("dosimetria_ou_subsidiarias"), "tese") or ["  - (nenhuma)"])
        L += ["- **Provas:**"] + (_linhas(o.get("provas_requeridas_ou_invocadas"), "prova") or ["  - (nenhuma)"])
        L += ["- **Pedidos:**"] + (_linhas(o.get("pedidos"), "pedido") or ["  - (nenhum)"]) + [""]
    return "\n".join(L) + "\n"


def relatorio_nulidades(res, cnj) -> str:
    L = [f"# Inventário das decisões e atos do juízo — {cnj}", "",
         "> Extração DESCRITIVA por LLM local (o que cada ato decide, motivos que invoca, requerimentos da defesa "
         "apreciados, datas). **Não aponta vícios**: em teste (2026-09-07) o modelo de 8B copiava os exemplos do prompt "
         "como se fossem nulidades. A varredura de nulidades (CPP 563-573, 157, 158-A a F) é do agente "
         "`auditoria-nulidades-criminal`, alimentado por este inventário e pelo `buscar.py`.", "",
         "| ato | decide/certifica | fundamentação (classe dada pelo modelo) | menciona intimação da defesa | motivos invocados | requerimentos da defesa apreciados |", "|---|---|---|---|---|---|"]
    for a, o, m in res:
        mot = "; ".join(f"{x.get('motivo')}" + ("" if x.get("localizado") else " [trecho não localizado]") for x in o.get("motivos_invocados") or []) or "—"
        req = "; ".join(f"{x.get('requerimento')} → {x.get('resultado') or '?'}" + ("" if x.get("localizado") else " [trecho não localizado]")
                        for x in o.get("requerimentos_da_defesa_apreciados") or []) or "—"
        L.append(f"| {_anc(a)} | {(o.get('o_que_o_ato_decide_ou_certifica') or '')[:160]} | {o.get('fundamentacao')} | {o.get('intimacao_da_defesa_mencionada')} | {mot[:220]} | {req[:220]} |")
    gen = [(a, o) for a, o, m in res if o.get("fundamentacao") in ("generica", "ausente") and a.get("tipo") in ("DECISAO", "SENTENCA", "ACORDAO", "PRONUNCIA", "TERMO DE AUDIENCIA")]
    L += ["", "## Decisões que o modelo classificou como fundamentação genérica ou ausente (conferir; CF 93 IX, CPP 315 §2º)", ""]
    L += [f"- {_anc(a)}: {(o.get('o_que_o_ato_decide_ou_certifica') or '')[:200]}" for a, o in gen] or ["(nenhuma)"]
    ind = [(a, x) for a, o, m in res for x in (o.get("requerimentos_da_defesa_apreciados") or []) if "indefer" in (x.get("resultado") or "").lower()]
    L += ["", "## Requerimentos da defesa indeferidos (candidatos a preliminar / prequestionamento)", ""]
    L += [f"- {_anc(a)}: {x.get('requerimento')} — “{(x.get('trecho') or '')[:140]}”{_mark(x)}" for a, x in ind] or ["(nenhum extraído)"]
    return "\n".join(L) + "\n"


def relatorio_prisao(res, cnj) -> str:
    L = [f"# Cautelares pessoais — {cnj}", "", "> Só atos cujo texto fala em prisão/cautelar. Extração por LLM local com trecho conferido.", ""]
    if not res:
        L.append("(nenhum ato tratou de prisão ou cautelar pessoal)")
    for a, o, m in res:
        L += [f"## {_anc(a)}", "", f"- Medida: {o.get('medida')} — situação: **{o.get('situacao')}**", "- Fundamentos:"] + (_linhas(o.get("fundamentos"), "fundamento") or ["  - (nenhum)"])
        L += ["- Datas:"] + (_linhas(o.get("datas"), "evento", ("data",)) or ["  - (nenhuma)"])
        L += ["- Cautelares alternativas mencionadas:"] + (_linhas(o.get("cautelares_alternativas"), "medida") or ["  - (nenhuma)"]) + [""]
    L += ["", "> Reavaliação obrigatória a cada 90 dias (CPP 316 p.u.) é conta do `prazo_cpp.py` a partir da data da decretação."]
    return "\n".join(L) + "\n"


def relatorio_dosimetria(res, cnj) -> str:
    L = [f"# Dosimetria — {cnj}", "", "> Extração por LLM local da sentença/acórdão, trecho a trecho. Conferir bis in idem e fundamentação de cada vetor.", ""]
    if not res:
        L.append("(nenhuma sentença/acórdão com dosimetria nos autos fatiados)")
    for a, o, m in res:
        L += [f"## {_anc(a)}", "", f"- Resultado: {o.get('resultado')}", "- Pena-base (CP 59):"] + (_linhas(o.get("pena_base"), "circunstancia", ("valoracao", "fracao")) or ["  - (nada)"])
        L += ["- 2ª fase (agravantes/atenuantes):"] + (_linhas(o.get("segunda_fase"), "circunstancia", ("fracao",)) or ["  - (nada)"])
        L += ["- 3ª fase (aumento/diminuição):"] + (_linhas(o.get("terceira_fase"), "causa", ("fracao",)) or ["  - (nada)"])
        L += [f"- Pena definitiva: {o.get('pena_definitiva')} · regime: {o.get('regime')} · substituição/sursis: {o.get('substituicao_ou_sursis')}", ""]
    return "\n".join(L) + "\n"


RELATORIOS = {"controversia": relatorio_controversia, "nulidades": relatorio_nulidades, "prisao": relatorio_prisao, "dosimetria": relatorio_dosimetria}


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("atos")
    ap.add_argument("--distiladores", default="controversia,nulidades,prisao,dosimetria")
    ap.add_argument("--modelo", default="qwen3:8b")
    ap.add_argument("--max-tokens", type=int, default=2000, help="teto do ato para o modelo local")
    ap.add_argument("--ate", type=int, default=5000, help="teto estendido (atos entre max-tokens e ate tambem rodam)")
    ap.add_argument("--num-predict", type=int, default=700)
    ap.add_argument("--limite", type=int, help="processar so as N primeiras tarefas (teste)")
    ap.add_argument("--excluir-tipos", default="", help="tipos de ato a pular, separados por virgula (ex.: CERTIDAO,CARTA PRECATORIA)")
    ap.add_argument("--so-tipos", default="", help="se dado, processa so estes tipos")
    ap.add_argument("--so-seqs", default="", help="se dado, processa so estes seq (ex.: 2,83)")
    ap.add_argument("--schema-de", default="", help="forca o schema por seq: '83=teses,2=imputacao' (ato mal classificado)")
    ap.add_argument("--so-relatorio", action="store_true", help="nao chama o modelo; so monta os .md do cache")
    a = ap.parse_args(argv)

    jp = Path(a.atos)
    extracted = jp.parent
    distill = extracted.parent / "distill"
    atos = [json.loads(l) for l in io.open(jp, encoding="utf-8")]
    cnj = atos[0].get("cnj") if atos else "?"
    dists = [d.strip() for d in a.distiladores.split(",") if d.strip() in ATOS_POR_DISTILADOR]
    fila = tarefas(atos, extracted, dists)
    excl = {t.strip().upper() for t in a.excluir_tipos.split(",") if t.strip()}
    so = {t.strip().upper() for t in a.so_tipos.split(",") if t.strip()}
    fila = [(d, sk, ato) for d, sk, ato in fila if ato.get("tipo") not in excl and (not so or ato.get("tipo") in so)]
    if a.so_seqs:
        seqs = {int(x) for x in a.so_seqs.split(",") if x.strip()}
        fila = [(d, sk, ato) for d, sk, ato in fila if ato["seq"] in seqs]
    if a.schema_de:
        forcados = {int(k): v for k, v in (p.split("=") for p in a.schema_de.split(",") if "=" in p)}
        fila = [(d, forcados.get(ato["seq"], sk), ato) for d, sk, ato in fila]
    teto = a.ate
    locais, nuvem = [], []
    for d, sk, ato in fila:
        tok = int(ato.get("chars", 0) / CHARS_POR_TOKEN)
        (locais if tok <= teto else nuvem).append((d, sk, ato, tok))
    (distill).mkdir(parents=True, exist_ok=True)
    # para_nuvem.json ACUMULA entre invocacoes: rodar os distiladores em duas chamadas (controversia
    # primeiro, depois nulidades/prisao/dosimetria) e' o uso normal, e sobrescrever perderia a fila
    # da chamada anterior — visto em 09/09/2026, quando a lista da controversia sumiu ao rodar a 2a.
    alvo = distill / "para_nuvem.json"
    novos = [{"distilador": d, "schema": sk, "seq": ato["seq"], "tipo": ato.get("tipo"),
              "id_pje": ato.get("id_pje"), "tokens_estimados": tok, "arquivo": ato["arquivo"]}
             for d, sk, ato, tok in nuvem]
    antigos = []
    if alvo.is_file():
        try:
            antigos = json.loads(io.open(alvo, encoding="utf-8").read())
        except Exception:
            antigos = []
    # a chave e' (distilador, seq): a mesma peca pode ir a nuvem por distiladores diferentes
    juntos = {(i.get("distilador"), i.get("seq")): i for i in antigos}
    juntos.update({(i["distilador"], i["seq"]): i for i in novos})
    io.open(alvo, "w", encoding="utf-8", newline="\n").write(
        json.dumps(sorted(juntos.values(), key=lambda i: (i.get("distilador") or "", i.get("seq") or 0)),
                   ensure_ascii=False, indent=1))
    print(f"{cnj}: {len(fila)} tarefas → {len(locais)} locais (≤{teto} tok) · {len(nuvem)} para nuvem (distill/para_nuvem.json)", flush=True)
    if a.limite:
        locais = locais[:a.limite]

    resultados: dict[str, list] = {d: [] for d in dists}
    t_total = time.time()
    for i, (d, sk, ato, tok) in enumerate(locais, 1):
        pasta = distill / "llm" / d
        pasta.mkdir(parents=True, exist_ok=True)
        cache = pasta / f"{ato['seq']:04d}.json"
        if cache.is_file():
            prev = json.loads(io.open(cache, encoding="utf-8").read())
            valido = "saida" in prev and "_erro" not in prev["saida"] and set(SCHEMAS[sk]["required"]) <= set(prev["saida"])
            if prev.get("hash") == ato.get("hash_sha256") and prev.get("modelo") == a.modelo and valido:
                resultados[d].append((ato, prev["saida"], prev.get("metricas", {})))
                continue
        if a.so_relatorio:
            continue
        texto = corpo_do_ato(extracted / ato["arquivo"])
        prompt = PROMPT_BASE + INSTRUCOES[sk] + f"\n\n=== ATO ({ato.get('tipo')}, {_anc(ato)}) ===\n{texto}\n=== FIM DO ATO ==="
        num_ctx = min(16384, max(4096, int(tok * 1.3) + a.num_predict + 800))
        t0 = time.time()
        try:
            saida, met = chamar(a.modelo, prompt, SCHEMAS[sk], num_ctx, a.num_predict)
        except Exception as e:  # noqa: BLE001
            print(f"  [{i}/{len(locais)}] {d} seq {ato['seq']} ERRO: {e}", flush=True)
            continue
        ok, tot = conferir(saida, _norm(texto))
        met |= {"trechos_localizados": ok, "trechos_total": tot, "seg_wall": round(time.time() - t0)}
        io.open(cache, "w", encoding="utf-8", newline="\n").write(json.dumps(
            {"cnj": cnj, "seq": ato["seq"], "tipo": ato.get("tipo"), "id_pje": ato.get("id_pje"), "distilador": d, "schema": sk,
             "modelo": a.modelo, "hash": ato.get("hash_sha256"), "tokens_estimados": tok, "metricas": met, "saida": saida},
            ensure_ascii=False, indent=1))
        resultados[d].append((ato, saida, met))
        print(f"  [{i}/{len(locais)}] {d}/{sk} seq {ato['seq']} {ato.get('tipo')} ~{tok} tok: {met['seg_wall']}s "
              f"(prompt {met['seg_prompt']}s, geração {met['seg_geracao']}s, {met['gerados']} tok{', TRUNCADO' if met['truncado'] else ''}) "
              f"trechos {ok}/{tot}", flush=True)
    # relatorio = TUDO que ha no cache do distilador (nao so a rodada atual): uma rodada filtrada por
    # --so-tipos/--so-seqs nao pode apagar do .md os atos das rodadas anteriores
    por_seq = {ato["seq"]: ato for ato in atos}
    for d in dists:
        vistos = {ato["seq"] for ato, _, _ in resultados[d]}
        for cache in sorted((distill / "llm" / d).glob("*.json")):
            try:
                prev = json.loads(io.open(cache, encoding="utf-8").read())
            except json.JSONDecodeError:
                continue
            ato = por_seq.get(prev.get("seq"))
            if not ato or ato["seq"] in vistos or "saida" not in prev or "_erro" in prev["saida"]:
                continue
            if prev.get("hash") != ato.get("hash_sha256"):
                continue     # o ato mudou desde a extracao: nao misturar
            resultados[d].append((ato, prev["saida"], prev.get("metricas", {})))
        resultados[d].sort(key=lambda t: t[0]["seq"])
        md = RELATORIOS[d](resultados[d], cnj)
        io.open(distill / f"{d}.md", "w", encoding="utf-8", newline="\n").write(md)
    print(f"concluído em {(time.time() - t_total) / 60:.0f} min → " + ", ".join(f"distill/{d}.md ({len(resultados[d])} atos)" for d in dists), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
