#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""consultar_cadh_stf.py — localiza, na obra STF "Convenção Americana sobre DH" (2ª ed., CADH
anotada com jurisprudência do STF), a PÁGINA onde começa a leitura de cada artigo (1–32).
Fonte: tools/cadh_stf_indice.json. PDF/MD: ~/.notebooklm/biblioteca/{pdf,md}/CADH_STF_anotada_2ed.*
Uso: python consultar_cadh_stf.py 8 [--json]"""
import sys,os,json,re,argparse
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
DATA=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cadh_stf_indice.json")
PDF=r"C:\Users\alden\.notebooklm\biblioteca\pdf\CADH_STF_anotada_2ed.pdf"
MD =r"C:\Users\alden\.notebooklm\biblioteca\md\CADH_STF_anotada_2ed.md"  # Markdown paginado ("## [p. N]")
ap=argparse.ArgumentParser(); ap.add_argument("artigo"); ap.add_argument("--json",action="store_true")
a=ap.parse_args(); base=json.load(open(DATA,encoding="utf-8"))
idx={r["artigo"]:r for r in base["artigos"]}
m=re.match(r'(\d+)',a.artigo.strip()); r=idx.get(int(m.group(1))) if m else None
if not r:
    msg=f"Art. {a.artigo} não indexado (a obra cobre arts. 1–32 da CADH — os direitos)."
    print(json.dumps({"erro":msg},ensure_ascii=False) if a.json else msg); sys.exit()
if a.json: print(json.dumps({"fonte":base["fonte"],"pdf":PDF,**r},ensure_ascii=False,indent=1)); sys.exit()
print(f"CADH Art. {r['artigo']} — {r['titulo']}  (leitura do STF)")
print(f"  Página do PDF: {r['pagina_pdf']}  →  abra {PDF}")
print(f"  Texto da norma: /cadh {r['artigo']} · Casos da Corte IDH: agente corte-idh-brasil.")
