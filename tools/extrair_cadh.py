import sys,re,json
html=open(sys.argv[1],"rb").read().decode("latin-1")
txt=re.sub(r'<[^>]+>',' ',html); txt=re.sub(r'&nbsp;|&#160;',' ',txt); txt=re.sub(r'[ \t]+',' ',txt)
heads=list(re.finditer(r'ARTIGO\s*(\d+)', txt))
M={}
for k,m in enumerate(heads):
    n=int(m.group(1)); start=m.end()
    end=heads[k+1].start() if k+1<len(heads) else len(txt)
    body=re.sub(r'\s+',' ',txt[start:end]).strip()
    if n not in M: M[n]={"artigo":n,"texto":body}
regs=[M[n] for n in sorted(M)]
json.dump({"fonte":"Convenção Americana sobre Direitos Humanos (Pacto de São José da Costa Rica) — Decreto 678/1992","url":"https://www.planalto.gov.br/ccivil_03/decreto/d0678.htm","total":len(regs),"artigos":regs},
          open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=[r["artigo"] for r in regs]
print("CADH artigos:",len(regs),"| faixa",min(nums),"-",max(nums),"| faltam:",[n for n in range(1,max(nums)+1) if n not in nums])
