#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""lint_fontes_canonicas.py — caça perda silenciosa nos datasets de fonte canônica.

Nasceu em 2026-08-05, depois de o extrator de regimentos revelar QUATRO modos de perda
que não davam erro nenhum — o dataset do RISTF rodava havia meses com 29 artigos que
nunca existiram, entre eles todo o rito da súmula vinculante. O ponto do lint é que
fonte canônica falha em silêncio: ninguém percebe que um artigo sumiu, porque a
resposta é "não encontrado" e isso parece erro de quem perguntou.

Os quatro sinais que ele procura (cada um vindo de um estrago real):

  LACUNA      numeração com buraco (1..máx) — artigo que sumiu inteiro.
  MINUSCULA   chave com sufixo de letra minúscula, ou nenhuma variante `-A` num texto
              grande — assinatura do regex que só aceitava `[A-Z]` (RISTF, 29 artigos).
  MOBILIA     texto com sumário/cabeçalho de página dentro (`\\x08`, "Sumário",
              linha de pontilhado) — o parser pegou índice em vez de dispositivo.
  REDACOES    o mesmo "Art. N." aparece duas vezes no texto e o registro NÃO traz o
              campo `redacoes` — redações sucessivas coladas sem a placa que diz qual
              é a vigente. Foi assim que a redação revogada do art. 390 do RITJMA
              quase foi a uma sustentação oral.

Também lista texto curto demais (possível truncamento), poupando o que é revogação
declarada — "(Revogado pela ...)" é curto de direito.

Uso:
    python lint_fontes_canonicas.py                # varre ~/.notebooklm/tools/*.json
    python lint_fontes_canonicas.py --detalhe cpp  # abre os achados de um dataset
    python lint_fontes_canonicas.py --so-suspeitos # só o que tem sinal

NÃO conserta nada: relata. O conserto é no extrator de cada fonte.
"""
import argparse
import glob
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))

CAMPOS_ID = ("artigo", "numero", "verbete", "tema", "edicao", "sumula", "termo")
CAMPOS_TEXTO = ("texto", "enunciado", "caput", "descricao", "conteudo", "titulo", "tese")

# o pontilhado so' denuncia sumario quando a linha termina em numero de pagina:
# nos codigos ele e' tecnica legislativa legitima ("Art. 14. ......" = trecho omitido).
MOBILIA = re.compile(r'[ ]|Sum[áa]rio|^.*\.{5,}\s*\d{1,4}\s*$|_{8,}', re.M)
REVOGADO = re.compile(r'\(\s*Revogad', re.I)
CURTO = 60
# entidade HTML nao decodificada: guarda &#8220; em vez de aspa. Nao apaga conteudo,
# mas suja citacao colada em peca e atrapalha busca literal.
ENTIDADE = re.compile(r'&#\d{2,5};|&(quot|amp|lt|gt|nbsp|ldquo|rdquo|aacute|ccedil);')
# UTF-8 lido como latin-1: "sera'" com acento vira "serA-a". Quebra busca por acento
# EM SILENCIO — o grep por "nao" com til nao acha o texto, e o dataset parece apenas
# nao ter o termo. Mesmo estrago ja' visto no corpus STJ do vault Familia.
MOJIBAKE = re.compile('Ã[-¿]|Â[§ºª°]')


def registros(d):
    """Acha a lista de registros e o nome do campo, seja qual for o formato."""
    if isinstance(d, list):
        return d, "(raiz)"
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v, k
    return [], ""


def campo(reg, candidatos):
    for c in candidatos:
        if c in reg:
            return c
    return None


def num(k):
    m = re.match(r'^(\d+)', str(k))
    return int(m.group(1)) if m else None


def analisa(path):
    nome = os.path.basename(path)
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return {"arquivo": nome, "erro": str(e)[:60]}

    regs, chave_lista = registros(d)
    if not regs:
        return {"arquivo": nome, "erro": "sem lista de registros"}

    cid = campo(regs[0], CAMPOS_ID)
    ctxt = campo(regs[0], CAMPOS_TEXTO)
    r = {"arquivo": nome, "n": len(regs), "campo_id": cid, "campo_texto": ctxt,
         "lacunas": [], "minusculas": [], "mobilia": [], "redacoes_sem_placa": [],
         "curtos": [], "duplicados": [], "variantes": 0, "com_placa": 0,
         "mojibake": [], "entidades": [], "orfao": False}
    if not cid:
        r["erro"] = f"sem campo de identificacao (lista '{chave_lista}')"
        return r

    ids = [str(x.get(cid)) for x in regs]
    vistos = set()
    for i in ids:
        if i in vistos:
            r["duplicados"].append(i)
        vistos.add(i)

    nums = [n for n in (num(i) for i in ids) if n is not None]
    if nums and len(nums) > 5:
        faltam = set(range(1, max(nums) + 1)) - set(nums)
        # revogacao EM BLOCO nao e' lacuna: o Codigo Eleitoral traz "Arts. 62 a 65.
        # (Revogados pelo art. 14 da Lei 8.868/1994)" dentro do bloco do art. 61.
        corpo = " ".join(str(x.get(ctxt) or "") for x in regs) if ctxt else ""
        for a, b in re.findall(r'Arts?\.\s*(\d+)\s*a\s*(\d+)\.?\s*\(\s*Revogad', corpo):
            bloco = set(range(int(a), int(b) + 1))
            r["revogados_em_bloco"] = sorted(set(r.get("revogados_em_bloco", [])) | (faltam & bloco))
            faltam -= bloco
        r["lacunas"] = sorted(faltam)

    r["variantes"] = sum(1 for i in ids if "-" in i)
    r["minusculas"] = [i for i in ids if re.search(r'-[a-z]$', i)]

    if not ctxt:
        return r

    for x in regs:
        i, t = str(x.get(cid)), str(x.get(ctxt) or "")
        if x.get("redacoes"):
            r["com_placa"] += 1
        if MOBILIA.search(t):
            r["mobilia"].append(i)
        if MOJIBAKE.search(t):
            r["mojibake"].append(i)
        if ENTIDADE.search(t):
            r["entidades"].append(i)
        if len(t) < CURTO and not REVOGADO.search(t):
            r["curtos"].append(i)
        # mesmo dispositivo repetido no corpo, sem a placa de redacoes sucessivas
        if not x.get("redacoes"):
            cabec = re.findall(r'(?m)^\s*Art\.?\s*' + re.escape(i.split("-")[0]) + r'\b', t)
            if len(cabec) > 1:
                r["redacoes_sem_placa"].append(i)
    return r


def sinais(r):
    s = []
    if r.get("erro"):
        s.append("ERRO")
    if r.get("lacunas"):
        s.append(f"LACUNA×{len(r['lacunas'])}")
    if r.get("minusculas"):
        s.append(f"MINUSCULA×{len(r['minusculas'])}")
    if r.get("mobilia"):
        s.append(f"MOBILIA×{len(r['mobilia'])}")
    if r.get("redacoes_sem_placa"):
        s.append(f"REDACOES×{len(r['redacoes_sem_placa'])}")
    if r.get("duplicados"):
        s.append(f"DUPLICADO×{len(r['duplicados'])}")
    if r.get("mojibake"):
        s.append(f"MOJIBAKE×{len(r['mojibake'])}")
    if r.get("entidades"):
        s.append(f"ENTIDADE×{len(r['entidades'])}")
    if r.get("orfao"):
        s.append("ORFAO")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalhe", help="abre os achados dos datasets cujo nome contenha isto")
    ap.add_argument("--so-suspeitos", action="store_true")
    a = ap.parse_args()

    # dataset que nenhum helper .py menciona nao e' consultavel pelo caminho normal:
    # so' aparece por Grep, e a' revelia do aviso de vigencia. Costuma ser sobra de
    # extracao antiga — foi assim que o codigo_eleitoral.json ficou orfao e mojibake.
    codigo = ""
    for py in glob.glob(os.path.join(BASE, "consultar_*.py")):
        try:
            codigo += open(py, encoding="utf-8", errors="ignore").read()
        except Exception:
            pass

    res = [analisa(p) for p in sorted(glob.glob(os.path.join(BASE, "*.json")))]
    for r in res:
        r["orfao"] = r["arquivo"] not in codigo
    print(f"# Lint de fontes canônicas — {len(res)} datasets em {BASE}\n")
    print(f"{'dataset':34} {'regs':>5} {'var-A':>6} {'placa':>6}  sinais")
    print("-" * 96)
    suspeitos = 0
    for r in res:
        s = sinais(r)
        if s:
            suspeitos += 1
        if a.so_suspeitos and not s:
            continue
        print(f"{r['arquivo'][:34]:34} {r.get('n', 0):5} {r.get('variantes', 0):6} "
              f"{r.get('com_placa', 0):6}  {' '.join(s) or 'ok'}")

    print(f"\n{suspeitos} de {len(res)} datasets com algum sinal. "
          "Sinal não é defeito provado — é onde olhar.")
    print("LACUNA=artigo sumiu · MINUSCULA=regex de sufixo · MOBILIA=sumário no texto · "
          "REDACOES=redações coladas sem placa")
    print("MOJIBAKE=acento corrompido (busca falha em silêncio) · "
          "ORFAO=dataset que helper nenhum consulta")

    if a.detalhe:
        for r in res:
            if a.detalhe.lower() not in r["arquivo"].lower():
                continue
            print(f"\n{'=' * 70}\n{r['arquivo']}  (id={r.get('campo_id')}, texto={r.get('campo_texto')})")
            for k, rot in (("lacunas", "numeração faltando"), ("minusculas", "chave minúscula"),
                           ("mobilia", "mobília de página no texto"),
                           ("redacoes_sem_placa", "redações sucessivas sem placa"),
                           ("revogados_em_bloco", "revogados em bloco (não é lacuna)"),
                           ("duplicados", "id duplicado"), ("mojibake", "acento corrompido (mojibake)"),
                           ("entidades", "entidade HTML não decodificada"),
                           ("curtos", "texto < 60 car. (não revogado)")):
                v = r.get(k) or []
                if v:
                    print(f"  {rot} ({len(v)}): {v[:40]}")


if __name__ == "__main__":
    main()
