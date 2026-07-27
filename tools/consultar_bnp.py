#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_bnp.py — consulta o Banco Nacional de Precedentes (BNP/Pangea, CNJ).

Fonte de pesquisa de PRECEDENTES QUALIFICADOS (vinculantes/persuasivos) para os
vaults de direito: Repercussão Geral, Recurso Repetitivo, Súmula Vinculante,
Súmula, IAC, IRDR, ADI/ADPF/ADC/ADO e Controvérsia — de todos os tribunais
aderentes (STF, STJ, TST, STM, TNU, TJs, TRTs, TRFs).

API pública, sem autenticação:  POST https://pangeabnp.pdpj.jus.br/api/v1/precedentes

Uso:
    python consultar_bnp.py "prescrição tributária"
    python consultar_bnp.py "propaganda eleitoral" --orgaos STF,STJ,TSE
    python consultar_bnp.py "guarda compartilhada" --tipos RG,RR,SUM
    python consultar_bnp.py "cadeia de custódia" --tudo          # todos os órgãos
    python consultar_bnp.py "improbidade" --nr 843               # nº do tema/súmula
    python consultar_bnp.py "consumidor" --controle              # ADI/ADPF/ADC/ADO
    python consultar_bnp.py "dano moral" --limite 5 --json

Opções:
    --orgaos LISTA     órgãos por vírgula (padrão: STF,STJ)
    --tipos  LISTA     tipos por vírgula (padrão: RG,RR,SV,SUM,IAC,SIRDR)
    --tudo             usa todos os órgãos aderentes
    --controle         atalho de tipos p/ controle concentrado (ADI,ADPF,ADC,ADO)
    --nr N             filtra pelo número do tema/súmula
    --exato "TRECHO"   busca por trecho exato
    --desde AAAA-MM-DD --ate AAAA-MM-DD   intervalo de atualização
    --cancelados       inclui precedentes cancelados/superados
    --limite N         máx. de resultados (padrão 15, teto 50)
    --json             saída estruturada (JSON)
"""
import sys, re, html, json, argparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import requests
except ImportError:
    print("Requer o pacote 'requests' (pip install requests).")
    sys.exit(1)

API_URL = "https://pangeabnp.pdpj.jus.br/api/v1/precedentes"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json",
           "User-Agent": "Mozilla/5.0 ConsultarBNP/1.0"}

TIPOS_NOME = {
    "RG": "Repercussão Geral", "RR": "Recurso Repetitivo",
    "SV": "Súmula Vinculante", "SUM": "Súmula",
    "IAC": "Incidente de Assunção de Competência",
    "SIRDR": "IRDR/Suspensão", "ADI": "ADI", "ADPF": "ADPF", "ADC": "ADC",
    "ADO": "ADI por Omissão", "CT": "Controvérsia",
}
TIPOS_PADRAO = ["RG", "RR", "SV", "SUM", "IAC", "SIRDR"]
TIPOS_CONTROLE = ["ADI", "ADPF", "ADC", "ADO"]
ORGAOS_PADRAO = ["STF", "STJ"]
ORGAOS_TODOS = [
    "STF", "STJ", "TST", "STM", "TNU",
    "TJSP", "TJMG", "TJRJ", "TJRS", "TJPR", "TJSC", "TJBA", "TJPE", "TJGO",
    "TJES", "TJPA", "TJAM", "TJDF", "TJMT", "TJMS", "TJRN", "TJPB", "TJPI",
    "TJCE", "TJMA", "TJSE", "TJAL", "TJRO", "TJRR", "TJAP", "TJAC", "TJTO",
    "TRF01", "TRF02", "TRF03", "TRF04", "TRF05", "TRF06",
] + [f"TRT{i:02d}" for i in range(1, 25)]


def limpa(s):
    if not s:
        return ""
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def buscar(busca, orgaos, tipos, limite, nr, exato, desde, ate, cancelados):
    filtro = {
        "buscaGeral": busca or "", "todasPalavras": "", "quaisquerPalavras": "",
        "semPalavras": "", "trechoExato": exato or "", "atualizacaoDesde": desde or "",
        "atualizacaoAte": ate or "", "cancelados": bool(cancelados),
        "ordenacao": "Text", "nr": str(nr or ""), "pagina": 1,
        "tamanhoPagina": min(int(limite), 50), "orgaos": orgaos, "tipos": tipos,
    }
    r = requests.post(API_URL, json={"filtro": filtro}, headers=HEADERS, timeout=45)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("termo", nargs="?", default="")
    ap.add_argument("--orgaos", default="")
    ap.add_argument("--tipos", default="")
    ap.add_argument("--tudo", action="store_true")
    ap.add_argument("--controle", action="store_true")
    ap.add_argument("--nr", default="")
    ap.add_argument("--exato", default="")
    ap.add_argument("--desde", default="")
    ap.add_argument("--ate", default="")
    ap.add_argument("--cancelados", action="store_true")
    ap.add_argument("--limite", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    orgaos = ([o.strip().upper() for o in a.orgaos.split(",") if o.strip()]
              or (ORGAOS_TODOS if a.tudo else ORGAOS_PADRAO))
    if a.tudo and not a.orgaos:
        orgaos = ORGAOS_TODOS
    tipos = [t.strip().upper() for t in a.tipos.split(",") if t.strip()]
    if not tipos:
        tipos = TIPOS_CONTROLE if a.controle else TIPOS_PADRAO

    if not (a.termo or a.exato or a.nr):
        print("Informe um termo de busca. Ex.: consultar_bnp.py \"prescrição\"")
        sys.exit(1)

    try:
        d = buscar(a.termo, orgaos, tipos, a.limite, a.nr, a.exato,
                   a.desde, a.ate, a.cancelados)
    except Exception as e:
        print(f"Falha ao consultar o BNP (fonte online): {e}")
        sys.exit(2)

    res = d.get("resultados", []) or []
    total = d.get("total", 0)

    if a.json:
        enxuto = [{
            "tipo": r.get("tipo"), "nr": r.get("nr"), "orgao": r.get("orgao"),
            "situacao": limpa(r.get("situacao")), "atualizacao": r.get("ultimaAtualizacao"),
            "questao": limpa(r.get("questao")), "tese": limpa(r.get("tese")),
            "paradigmas": [p.get("numero") for p in (r.get("processosParadigma") or [])],
            "link": next((p.get("link") for p in (r.get("processosParadigma") or [])
                          if p.get("link")), ""),
        } for r in res]
        print(json.dumps({"fonte": "BNP/Pangea (CNJ)", "total": total,
                          "orgaos": orgaos, "tipos": tipos, "resultados": enxuto},
                         ensure_ascii=False, indent=1))
        return

    if not res:
        print(f"Nenhum precedente para «{a.termo or a.exato or a.nr}» "
              f"(órgãos {','.join(orgaos)} · tipos {','.join(tipos)}).")
        return

    print(f"Fonte: BNP/Pangea (CNJ) · {total} precedente(s), exibindo {len(res)} "
          f"· órgãos {','.join(orgaos)} · tipos {','.join(tipos)}\n")
    for r in res:
        tipo = r.get("tipo", "")
        nome = TIPOS_NOME.get(tipo, tipo)
        link = next((p.get("link") for p in (r.get("processosParadigma") or [])
                     if p.get("link")), "")
        paras = ", ".join(p.get("numero", "") for p in
                          (r.get("processosParadigma") or []) if p.get("numero"))
        print(f"● {nome} nº {r.get('nr','')} — {r.get('orgao','')}"
              f"  ({limpa(r.get('situacao'))} · atual. {r.get('ultimaAtualizacao','')})")
        if r.get("questao"):
            print(f"   Questão: {limpa(r.get('questao'))}")
        if r.get("tese"):
            print(f"   Tese: {limpa(r.get('tese'))}")
        if paras:
            print(f"   Paradigma(s): {paras}")
        if link:
            print(f"   Fonte: {link}")
        print()
    print("⚠ Confirme o inteiro teor e a vigência da tese na fonte oficial "
          "(portal do tribunal / pangeabnp.pdpj.jus.br) antes de citar.")


if __name__ == "__main__":
    main()
