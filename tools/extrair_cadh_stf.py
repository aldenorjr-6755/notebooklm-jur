import sys,re,json,fitz
# Índice artigo->página da obra STF "Convenção Americana sobre DH" (CADH anotada).
# Cabeçalho: "ARTIGO N. TÍTULO" em DanteMTStd ~12pt (maiúsculo).
pdf,out=sys.argv[1],sys.argv[2]
d=fitz.open(pdf); M={}
for pno in range(d.page_count):
    for b in d[pno].get_text("dict")["blocks"]:
        for l in b.get("lines",[]):
            sp=l.get("spans",[])
            if not sp: continue
            txt=re.sub(r'\s+',' ',"".join(s["text"] for s in sp)).strip()
            m=re.match(r'^ARTIGO\s+(\d+)\.\s*(.*)', txt)
            if m and round(sp[0]["size"])==12 and len(txt)<70:
                n=int(m.group(1))
                if n not in M: M[n]={"artigo":n,"pagina_pdf":pno+1,"titulo":m.group(2).strip().title()}
regs=[M[k] for k in sorted(M)]
json.dump({"fonte":"STF — Convenção Americana sobre Direitos Humanos, 2ª ed. (CADH anotada com jurisprudência do STF)",
           "obs":"pagina_pdf = página física do PDF (Anexos/CADH_STF_anotada_2ed.pdf); cobre arts. 1–32 (direitos)",
           "total":len(regs),"artigos":regs},open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=[r["artigo"] for r in regs]
print("artigos indexados:",len(regs),"| faixa",min(nums),"-",max(nums),"| faltam:",[n for n in range(1,max(nums)+1) if n not in nums])
