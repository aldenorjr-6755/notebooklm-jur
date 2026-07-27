import sys,re,json,fitz
pdf,out,fonte=sys.argv[1],sys.argv[2],sys.argv[3]
doc=fitz.open(pdf); text="\n".join(doc[i].get_text() for i in range(doc.page_count))
heads=list(re.finditer(r'\nArt\.?\s*(\d+(?:-[A-Z])?)\s*[ºo°]?',text))
M={}
for k,m in enumerate(heads):
    art=m.group(1); start=m.start()+1
    end=heads[k+1].start() if k+1<len(heads) else len(text)
    txt=re.sub(r'[ \t]+',' ',text[start:end]).strip(); txt=re.sub(r'\n{2,}','\n',txt)
    if art not in M and len(txt)>5: M[art]=txt
def kf(a):
    mm=re.match(r'(\d+)(?:-([A-Z]))?',a); return (int(mm.group(1)),mm.group(2) or "")
regs=[{"artigo":a,"texto":M[a]} for a in sorted(M,key=kf)]
json.dump({"fonte":fonte,"total":len(regs),"artigos":regs},open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=[kf(r["artigo"])[0] for r in regs]
print(f"{fonte}: {len(regs)} artigos | maior {max(nums)} | faltam 1..max: {[n for n in range(1,max(nums)+1) if n not in nums][:15]}")
print("  ex art 1:", regs[0]['texto'][:80])
