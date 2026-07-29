import os,sys,subprocess,json,time
BASE=os.path.expanduser('~/.notebooklm')
NB='17081d6b-8875-42ff-93d4-b2ce3f08371e'
paths=[l.strip() for l in open(os.path.join(BASE,'_fontes_decisao_pressao.txt'),encoding='utf-8') if l.strip()]
log=open(os.path.join(BASE,'_subir_decisao_pressao.log'),'w',encoding='utf-8')
ok=err=0
for i,p in enumerate(paths,1):
    name=os.path.basename(p)
    try:
        r=subprocess.run([sys.executable,'-m','notebooklm','source','add',p,'--notebook',NB,'--json'],
                         capture_output=True,text=True,timeout=300)
        if r.returncode==0:
            ok+=1; msg=f'[{i}/{len(paths)}] OK   {name}'
        else:
            err+=1; msg=f'[{i}/{len(paths)}] ERRO {name} :: rc={r.returncode} :: {(r.stderr or r.stdout).strip()[:300]}'
    except Exception as e:
        err+=1; msg=f'[{i}/{len(paths)}] EXC  {name} :: {e}'
    print(msg); log.write(msg+'\n'); log.flush()
    time.sleep(1)
fim=f'FIM  ok={ok}  erro={err}  total={len(paths)}'
print(fim); log.write(fim+'\n'); log.close()
