import sys, re, json, fitz
LAB = ["Precedente","Legisla","Fonte","Data de","Vide","Doutrina","Observa"]
pdf,out=sys.argv[1],sys.argv[2]
doc=fitz.open(pdf); text="\n".join(doc[i].get_text() for i in range(doc.page_count))
heads=list(re.finditer(r'\nS[ÚU]MULA\s+VINCULANTE\s+(\d+)\s*\n', text))
M={}
for k,m in enumerate(heads):
    num=int(m.group(1)); start=m.end()
    end=heads[k+1].start() if k+1<len(heads) else len(text)
    blk=text[start:end]
    cut=len(blk)
    for lab in LAB:
        j=blk.find(lab)
        if j!=-1 and j<cut: cut=j
    enun=re.sub(r'\s+',' ',blk[:cut]).strip()
    if not enun or enun.isdigit() or len(enun)<15: continue  # entrada de sumário
    canc="CANCELAD" in enun.upper() or "REVOGAD" in enun.upper()
    if num not in M or len(enun)>len(M[num]["enunciado"]):
        M[num]={"numero":num,"enunciado":enun,"situacao":"CANCELADA" if canc else "vigente"}
regs=[M[n] for n in sorted(M)]
json.dump({"fonte":"STF — Súmulas Vinculantes (compilação oficial, SV 1 a 58)","total":len(regs),"sumulas_vinculantes":regs},
          open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("SV extraídas:",len(regs),"| faixa",regs[0]["numero"],"a",regs[-1]["numero"])
print("nº presentes:",[r["numero"] for r in regs])
for r in regs[:2]: print(f"  [SV {r['numero']}] {r['enunciado'][:120]}")
