import os,sys,subprocess
BASE=os.path.expanduser('~/.notebooklm'); OUT=os.path.join(BASE,'_primarias')
os.makedirs(OUT,exist_ok=True)
alvos=[('HC-598051-SP','https://www.jusbrasil.com.br/jurisprudencia/stj/3331411987',None),
       ('AREsp-2123334-MG',None,'AREsp 2123334 confissao extrajudicial informal Ribeiro Dantas')]
for nome,url,busca in alvos:
    ref=url
    if ref is None:
        b=subprocess.run([sys.executable,'jusbrasil/jusbrasil_cli.py','buscar',busca,'--tribunal','STJ','--paginas','1'],
                         capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=BASE,timeout=400)
        open(os.path.join(OUT,f'_busca_{nome}.md'),'w',encoding='utf-8').write(b.stdout or '')
        import re
        m=re.findall(r'https://www\.jusbrasil\.com\.br/jurisprudencia/stj/\d+', b.stdout or '')
        # prefere o resultado marcado ACORDAO
        blocos=(b.stdout or '').split('## ')
        ref=None
        for bl in blocos:
            if 'ACORDAO' in bl:
                mm=re.search(r'https://www\.jusbrasil\.com\.br/jurisprudencia/stj/\d+', bl)
                if mm: ref=mm.group(0); break
        if ref is None and m: ref=m[0]
        print(nome,'-> ref:',ref)
    if not ref:
        print(nome,'SEM REFERENCIA'); continue
    dest=os.path.join(OUT,f'{nome}-inteiro-teor.txt')
    r=subprocess.run([sys.executable,'jusbrasil/jusbrasil_cli.py','teor',ref,'--txt',dest],
                     capture_output=True,text=True,encoding='utf-8',errors='replace',cwd=BASE,timeout=500)
    sz=os.path.getsize(dest) if os.path.exists(dest) else 0
    print(f'{nome}: rc={r.returncode} bytes={sz}')
    if sz==0: print('   stderr:',(r.stderr or r.stdout or '')[:300])
print('FIM')
