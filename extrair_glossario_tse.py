"""
Extrai o Glossário Eleitoral do TSE e salva em JSON.
URL: https://www.tse.jus.br/servicos-eleitorais/glossario/glossario-eleitoral
Estrutura: uma página por letra com anchors <a name="slug">
"""

import re
import json
import time
import urllib.request
import string
from html import unescape

BASE = "https://www.tse.jus.br/servicos-eleitorais/glossario/termos-iniciados-com-a-letra-"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; pesquisa-academica)",
    "Accept": "text/html,*/*",
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def strip_tags(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def parse_letter(html):
    """Extrai lista de (slug, termo, definição, ver_também, referência) de uma página."""
    # Encontra todos os blocos entre âncoras
    # Padrão: <a name="slug" ...></a> TERMO </strong></h3> ... até próximo <h3>
    anchors = list(re.finditer(r'<a\s+name="([^"]+)"[^>]*></a>\s*(.*?)\s*</strong></h3>', html))
    if not anchors:
        return []

    results = []
    for i, m in enumerate(anchors):
        slug = m.group(1)
        termo = strip_tags(m.group(2))

        # Conteúdo até próxima âncora/h3 ou fim
        start = m.end()
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(html)
        bloco = html[start:end]

        # Separar parágrafos
        paragraphs = re.findall(r"<p>(.*?)</p>", bloco, re.DOTALL)
        paras_text = [strip_tags(p) for p in paragraphs if strip_tags(p)]

        # Identificar seções
        definicao_parts = []
        ver_tambem = ""
        referencia = ""
        mode = "def"
        for pt in paras_text:
            pt_lower = pt.lower()
            if pt_lower.startswith("ver também") or pt_lower.startswith("ver tambem"):
                mode = "ver"
                continue
            if pt_lower.startswith("referência") or pt_lower.startswith("referencia"):
                mode = "ref"
                continue
            if mode == "def":
                definicao_parts.append(pt)
            elif mode == "ver":
                ver_tambem = pt
            elif mode == "ref":
                referencia = pt

        definicao = " ".join(definicao_parts).strip()
        results.append({
            "slug": slug,
            "termo": termo,
            "definicao": definicao,
            "ver_tambem": ver_tambem,
            "referencia": referencia,
        })

    return results

def main():
    letras = list(string.ascii_lowercase)
    todos = []
    erros = []

    for letra in letras:
        url = BASE + letra
        print(f"[{letra.upper()}] {url}", end=" ... ", flush=True)
        try:
            html = fetch(url)
            termos = parse_letter(html)
            print(f"{len(termos)} termos")
            todos.extend(termos)
        except Exception as e:
            print(f"ERRO: {e}")
            erros.append(letra)
        time.sleep(0.5)

    out = {
        "fonte": "Glossário Eleitoral TSE",
        "url": "https://www.tse.jus.br/servicos-eleitorais/glossario/glossario-eleitoral",
        "total": len(todos),
        "termos": todos,
    }
    with open("glossario_tse.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nTotal: {len(todos)} termos → glossario_tse.json")
    if erros:
        print(f"Erros nas letras: {erros}")

if __name__ == "__main__":
    main()
