# -*- coding: utf-8 -*-
"""Monitor DJEN (API oficial CNJ) — processo 0818241-62.2025.8.10.0000 (TJMA 2g).

Consulta as comunicacoes do processo na janela dos ultimos 10 dias, compara com o
estado salvo (hashes ja vistos) e imprime SOMENTE o que for novo. Exit code:
  0 = nada novo · 10 = ha comunicacao nova (detalhe no stdout) · 1 = erro de rede/API.
Estado: ~/.notebooklm/monitor_djen_0818241_state.json (criado na 1a execucao).
Uso:  py ~/.notebooklm/monitor_djen_0818241.py            # varre e atualiza o estado
      py ~/.notebooklm/monitor_djen_0818241.py --dry-run  # varre sem gravar estado
"""
import json, sys, urllib.request, urllib.parse
from datetime import date, timedelta
from pathlib import Path

PROCESSO = "08182416220258100000"
STATE = Path.home() / ".notebooklm" / "monitor_djen_0818241_state.json"
BASE = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"


def consulta():
    ini = (date.today() - timedelta(days=10)).isoformat()
    fim = date.today().isoformat()
    q = urllib.parse.urlencode({
        "numeroProcesso": PROCESSO,
        "dataDisponibilizacaoInicio": ini,
        "dataDisponibilizacaoFim": fim,
        "pagina": 1, "itensPorPagina": 100,
    })
    req = urllib.request.Request(BASE + "?" + q, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if d.get("status") != "success":
        raise RuntimeError("API status: %r" % d.get("status"))
    return d.get("items", [])


def main():
    dry = "--dry-run" in sys.argv
    vistos = set()
    if STATE.exists():
        vistos = set(json.loads(STATE.read_text(encoding="utf-8")).get("hashes", []))
    try:
        items = consulta()
    except Exception as e:
        print("ERRO na consulta DJEN:", e)
        sys.exit(1)
    novos = [i for i in items if i.get("hash") and i["hash"] not in vistos]
    if not novos:
        print("Nada novo (%d comunicacoes na janela, todas conhecidas)." % len(items))
        sys.exit(0)
    print("%d COMUNICACAO(OES) NOVA(S) no processo 0818241-62.2025.8.10.0000:" % len(novos))
    for i in novos:
        print("-" * 70)
        print("data:", i.get("datadisponibilizacao"), "| tipo:", i.get("tipoComunicacao"),
              "| orgao:", i.get("nomeOrgao"), "| tribunal:", i.get("siglaTribunal"))
        print("hash:", i.get("hash"))
        print("certidao: %s/%s/certidao" % (BASE, i.get("hash")))
        print("link:", i.get("link"))
        texto = (i.get("texto") or "").replace("\n", " ")
        print("teor:", texto[:600])
    if not dry:
        vistos |= {i["hash"] for i in novos}
        STATE.write_text(json.dumps({"hashes": sorted(vistos)}, indent=1), encoding="utf-8")
    sys.exit(10)


if __name__ == "__main__":
    main()
