import sys,re,json
html=open(sys.argv[1],"rb").read().decode("latin-1")
fonte,url=sys.argv[3],sys.argv[4]
txt=re.sub(r'<[^>]+>',' ',html); txt=re.sub(r'&nbsp;|&#160;',' ',txt); txt=re.sub(r'[ \t]+',' ',txt)
heads=list(re.finditer(r'(?:ARTIGO|Artigo)\s*(\d+)', txt)); M={}  # capital A; nao a ref minuscula "artigo"
for k,m in enumerate(heads):
    n=int(m.group(1)); s=m.end(); e=heads[k+1].start() if k+1<len(heads) else len(txt)
    body=re.sub(r'\s+',' ',txt[s:e]).strip()
    if n not in M: M[n]={"artigo":n,"texto":body}
regs=[M[n] for n in sorted(M)]
json.dump({"fonte":fonte,"url":url,"total":len(regs),"artigos":regs},open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=[r["artigo"] for r in regs]
print(f"{fonte}: {len(regs)} arts | {min(nums)}-{max(nums)} | faltam {[n for n in range(1,max(nums)+1) if n not in nums]}")
