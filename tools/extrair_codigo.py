import sys,re,json
# Extrator generico de CODIGO/LEI Planalto: cabecalho de artigo INICIA um <p>...> ("Art. N").
# Acumula paragrafos seguintes (incisos/paragrafos) ate o proximo "Art. N".
# Uso: python extrair_codigo.py <html> <out.json> "<fonte>" "<url>" <art_max>
html=open(sys.argv[1],"rb").read().decode("latin-1")
fonte,url=sys.argv[3],sys.argv[4]; amax=int(sys.argv[5]) if len(sys.argv)>5 else 0
def clean(s):
    s=re.sub(r'<[^>]+>',' ',s)
    s=s.replace('&nbsp;',' ').replace('&#160;',' ').replace('&quot;','"').replace('&amp;','&').replace('&ordm;','º').replace('&deg;','º')
    s=re.sub(r'[ \t\r\n]+',' ',s).strip()
    s=re.sub(r'\bA\s?rt\s?\.\s*(?=\d)','Art. ',s)  # corrige cabeçalho quebrado "A rt." / "Ar t."
    return s
paras=re.split(r'(?i)<p\b[^>]*>', html)
order=[]; M={}
cur=None
for p in paras:
    t=clean(p)
    if not t: continue
    m=re.match(r'Art\.\s*([\d.]+)(?:-([A-Z]))?\s*[ºo°]?', t)
    if m:
        num=int(m.group(1).replace('.','')); suf=m.group(2) or ''
        cur={"num":num,"suf":suf,"texto":t}
        key=(num,suf)
        if key not in M or len(t)>=len(M[key]["texto"]):
            M[key]=cur
    elif cur is not None:
        cur["texto"]+=" "+t
regs=[{"artigo":(f"{k[0]}-{k[1]}" if k[1] else str(k[0])),"texto":M[k]["texto"]} for k in sorted(M)]
json.dump({"fonte":fonte,"url":url,"total":len(regs),"artigos":regs},open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=sorted(set(k[0] for k in M))
gaps=[n for n in range(1,(amax or max(nums))+1) if n not in set(nums)]
print(f"{fonte}: {len(regs)} arts | {min(nums)}-{max(nums)} | faltam(1..{amax or max(nums)}): {len(gaps)} {gaps[:15]}")
