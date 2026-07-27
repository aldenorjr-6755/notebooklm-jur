#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_cf.py — texto literal de artigo da Constituicao (Planalto, ate EC 139).

Fonte: tools/cf_artigos.json, que traz DOIS blocos:
  - "artigos" — corpo permanente (arts. 1o a 250 + variantes com letra);
  - "adct"    — Ato das Disposicoes Constitucionais Transitorias (arts. 1o a 138).

A numeracao do ADCT reinicia em 1 e colide com a do corpo permanente, por isso os
blocos sao separados e a consulta precisa dizer qual deles quer. Ate 2026-07-26 o
ADCT nao era sequer extraido, e este helper respondia "ADCT nao indexado" a quem
perguntasse pelo art. 68 (quilombolas) ou pelo art. 100 (aposentadoria compulsoria
no STF).

Uso:
  python consultar_cf.py 5
  python consultar_cf.py 103-A --json
  python consultar_cf.py "ADCT 68"      # ou: --adct 68  |  adct-68
"""
import sys, os, json, re, argparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf_artigos.json")

# "ADCT 68", "adct-68", "ADCT art. 68" — o prefixo pode vir colado, com hifen ou solto.
PREFIXO_ADCT = re.compile(r'^\s*ADCT\b[\s\-–.]*(?:art\.?)?\s*', re.I)


def norm(s):
    """Normaliza '5o', '5º', '103-a' -> '5', '103-A'."""
    s = s.strip().upper().replace("º", "").replace("°", "")
    m = re.match(r'(\d+)\s*-?\s*([A-Z])?', s)
    return None if not m else m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")


ap = argparse.ArgumentParser()
ap.add_argument("artigo")
ap.add_argument("--adct", action="store_true", help="consulta o ADCT")
ap.add_argument("--json", action="store_true")
a = ap.parse_args()

base = json.load(open(DATA, encoding="utf-8"))

# O prefixo no proprio argumento vale tanto quanto a flag.
alvo = a.artigo
no_adct = a.adct
if PREFIXO_ADCT.match(alvo):
    no_adct = True
    alvo = PREFIXO_ADCT.sub("", alvo)

bloco = base.get("adct", []) if no_adct else base.get("artigos", [])
rotulo = "ADCT" if no_adct else "CF"
idx = {r["artigo"]: r for r in bloco}
r = idx.get(norm(alvo))

if not r:
    onde = "ADCT (arts. 1o a 138)" if no_adct else "corpo permanente (arts. 1o a 250)"
    m = f"Art. {alvo} nao encontrado no {onde}."
    # O erro mais comum e procurar no bloco errado — avise se existe no outro.
    outro = base.get("artigos", []) if no_adct else base.get("adct", [])
    if norm(alvo) in {x["artigo"] for x in outro}:
        m += ("  Existe no corpo permanente — consulte sem o prefixo ADCT."
              if no_adct else
              f'  Existe no ADCT — use: /cf "ADCT {alvo}"')
    print(json.dumps({"erro": m}, ensure_ascii=False) if a.json else m)
    sys.exit()

if a.json:
    print(json.dumps({"fonte": base["fonte"], "bloco": rotulo, **r},
                     ensure_ascii=False, indent=1))
    sys.exit()

print(f"=== {rotulo}, Art. {r['artigo']} ===  (fonte: {base['fonte']})\n")
print(r["texto"])
print("\n⚠️ Confira vigência/EC posterior no Planalto. "
      "Para a leitura do STF: /constituicao " + r["artigo"])
