#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_tesauro.py — consulta o Tesauro Juridico do STF (vocabulario controlado).

Endpoint (descoberto em /scripts/tesauro.js):
    GET https://portal.stf.jus.br/jurisprudencia/tesauro/tesauro-service.asp?termo=<termo>
    GET .../tesauro-service.asp?letra=<A..Z>     (navega por letra inicial)

Retorna XML. ATENCAO: o prologo declara ISO-8859-1, mas os bytes reais sao UTF-8
(o header HTTP Content-Type confirma UTF-8). Por isso decodificamos como UTF-8 e
removemos o prologo antes de dar parse (ElementTree recusa string unicode com
declaracao de encoding).

Uso:
    python consultar_tesauro.py "usucapiao"
    python consultar_tesauro.py "habeas corpus" --json
    python consultar_tesauro.py --letra A

Codigos de relacao do Tesauro STF:
    USE        -> termo PREFERIDO a ser usado (descritor)
    UP         -> Usado Para (sinonimos nao preferidos)
    TG         -> Termo Generico (mais amplo / broader)
    TE         -> Termo Especifico (mais restrito / narrower)
    TR         -> Termo Relacionado (related)
    NE         -> Nota Explicativa (definicao / scope note)
    CATEGORIA  -> area/ramo do direito
"""
import sys
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Windows: o console costuma ser cp1252; forca UTF-8 para nao mojibar a saida.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://portal.stf.jus.br/jurisprudencia/tesauro/tesauro-service.asp"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

ROTULOS = {
    "USE": "USE (termo preferido)",
    "UP":  "UP  (usado para / sinonimos)",
    "TG":  "TG  (termo generico)",
    "TE":  "TE  (termo especifico)",
    "TR":  "TR  (termo relacionado)",
    "NE":  "NE  (nota explicativa)",
    "CATEGORIA": "CATEGORIA",
}
ORDEM = ["NE", "USE", "UP", "TG", "TE", "TR", "CATEGORIA"]


def buscar(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        bruto = resp.read()
    texto = bruto.decode("utf-8", errors="replace")
    # remove o prologo mentiroso <?xml ... ?>
    texto = re.sub(r"^\s*<\?xml[^>]*\?>", "", texto).strip()
    return texto


_XML_INVALIDO = re.compile(
    r"[^\x09\x0A\x0D\x20-퟿-�\U00010000-\U0010FFFF]")


def _sanear(xml_texto):
    # A base do STF tem lixo: chars de controle (ex.: \x02 dentro de palavra) e
    # & soltos, ambos invalidos em XML 1.0. Limpa antes do parse.
    xml_texto = _XML_INVALIDO.sub("", xml_texto)
    xml_texto = re.sub(
        r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)", "&amp;", xml_texto)
    return xml_texto


def parse(xml_texto):
    if not xml_texto:
        return []
    try:
        root = ET.fromstring(xml_texto)
    except ET.ParseError:
        root = ET.fromstring(_sanear(xml_texto))
    termos = []
    for t in root.findall(".//TERMO"):
        # so os TERMO de 1o nivel tem o atributo dsc (descritor)
        dsc = t.get("dsc")
        if dsc is None:
            continue
        item = {"termo": dsc.strip(), "relacoes": {}}
        for rel in t.findall("REL"):
            codigo = (rel.get("DSC") or "").strip()
            if codigo == "NE":
                # nota explicativa fica no texto do proprio REL
                valor = (rel.text or "").strip()
                if valor:
                    item["relacoes"].setdefault("NE", []).append(valor)
            else:
                for sub in rel.findall("TERMO"):
                    valor = (sub.text or "").strip()
                    if valor:
                        item["relacoes"].setdefault(codigo, []).append(valor)
        termos.append(item)
    return termos


def imprimir(termos, alvo):
    if not termos:
        print(f"Nenhum termo encontrado no Tesauro do STF para: {alvo!r}")
        return
    print(f"Tesauro Juridico do STF — resultados para: {alvo!r}\n")
    for item in termos:
        print(f"== {item['termo']} ==")
        rels = item["relacoes"]
        for codigo in ORDEM:
            if codigo in rels:
                rotulo = ROTULOS.get(codigo, codigo)
                if codigo == "NE":
                    for v in rels[codigo]:
                        print(f"  {rotulo}: {v}")
                else:
                    print(f"  {rotulo}: " + "; ".join(rels[codigo]))
        # demais codigos nao previstos
        for codigo, vals in rels.items():
            if codigo not in ORDEM:
                print(f"  {codigo}: " + "; ".join(vals))
        print()
    print("Fonte: Tesauro Juridico do STF — "
          "https://portal.stf.jus.br/jurisprudencia/tesauro/pesquisa.asp")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    como_json = "--json" in args
    args = [a for a in args if a != "--json"]

    if args and args[0] == "--letra":
        if len(args) < 2:
            print("Informe a letra. Ex.: python consultar_tesauro.py --letra A")
            return 2
        params = {"letra": args[1][:1].upper()}
        alvo = f"letra {params['letra']}"
    else:
        termo = " ".join(args).strip()
        params = {"termo": termo}
        alvo = termo

    try:
        xml_texto = buscar(params)
    except Exception as e:
        print(f"Erro ao consultar o Tesauro do STF: {e}")
        return 1

    termos = parse(xml_texto)
    if como_json:
        print(json.dumps({"consulta": alvo, "termos": termos},
                         ensure_ascii=False, indent=2))
    else:
        imprimir(termos, alvo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
