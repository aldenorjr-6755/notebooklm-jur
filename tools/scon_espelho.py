# -*- coding: utf-8 -*-
import sys, re, html, subprocess, os, urllib.parse, hashlib
SC = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
def busca(livre, base="ACOR"):
    q = urllib.parse.quote(livre, safe="")
    url = f"https://processo.stj.jus.br/SCON/pesquisar.jsp?b={base}&O=JT&livre={q}"
    out = os.path.join(SC, "r_"+hashlib.md5((base+livre).encode()).hexdigest()[:10]+".html")
    subprocess.run(["curl","-s","-A",UA,"-L","-c",os.path.join(SC,"cookies.txt"),
                    "-b",os.path.join(SC,"cookies.txt"),url,"-o",out],check=True)
    s = open(out,"rb").read().decode("latin-1")
    i = s.find("listadocumentos")
    if i < 0:
        return "SEM BLOCO DE RESULTADOS (0 documentos)", 0
    seg = s[i:]
    t = re.sub(r"<[^>]+>","\n",seg); t = html.unescape(t)
    linhas = [l.strip() for l in t.split("\n") if l.strip()]
    txt = "\n".join(linhas)
    m = re.search(r"Documento 1 de (\d+)", txt)
    n = int(m.group(1)) if m else 0
    # citacoes ABNT (Classe n. X/UF, relator ..., julgado em ..., DJ...)
    cits = re.findall(r"\(([A-Za-zÁ-ú]{2,7}[^()]{0,220}?julgad[oa] em \d{1,2}/\d{1,2}/\d{4}[^()]{0,80}?)\)", txt)
    vistos = []
    for c in cits:
        c = re.sub(r"\s+"," ",c).strip()
        if c not in vistos: vistos.append(c)
    return txt, n, vistos
if __name__ == "__main__":
    base = "ACOR"
    args = sys.argv[1:]
    if args and args[0] in ("ACOR","SUMU","INFJ","TEMA"):
        base = args.pop(0)
    for termo in args:
        r = busca(termo, base)
        print("="*90)
        print(f"[{base}] livre = {termo}")
        if isinstance(r, tuple) and len(r)==3:
            txt,n,cits = r
            print(f"--> {n} documento(s)")
            for c in cits: print("   *", c)
            if n==0: print(txt[:400])
        else:
            print("-->", r[0])
