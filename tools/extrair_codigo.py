import sys,re,json
from html import unescape   # NAO usar `import html`: a variavel `html` guarda a pagina
# Extrator generico de CODIGO/LEI Planalto: cabecalho de artigo INICIA um <p>...> ("Art. N").
# Acumula paragrafos seguintes (incisos/paragrafos) ate o proximo "Art. N".
# Uso: python extrair_codigo.py <html> <out.json> "<fonte>" "<url>" <art_max>
#
# Cabecalhos reconhecidos: "Art. N", "Art. Nº", "Art. N-A", "Art. Nº-A", "Art. N o -A",
# "Art. N-M-A" (sufixo duplo) e "Art. NA" (sufixo colado, sem traco - erro do Planalto).
# CAPUT e SUFIXADOS sao entradas DISTINTAS: "Art. 3o" (CPP) e "Art. 3o-A".."3o-F" nunca
# colidem na mesma chave. O sufixo so e reconhecido com a letra COLADA ao traco
# ("Art. 3o-A."); traco seguido de espaco e separador de texto ("Art. 1o - Nao ha crime").
HDR=re.compile(r'Art\.\s*(\d[\d.]*)'
               r'(?:([A-Z])(?![a-zà-ÿ])'                       # sufixo colado: "Art. 10A"
               r'|\s*[ºo°]?\s*(?:-([A-Z](?:-[A-Z])*)(?![a-zà-ÿ]))?)')  # "Art. 3º-A", "Art. 359-M-A"
# "Art. 159. ........... Pena - reclusao..." dentro de lei que ALTERA outra norma nao e
# artigo desta lei: e transcricao do artigo alheio. Nao abre registro (vira continuacao).
CITA=re.compile(r'Art\.\s*[\d.]+\s*[ºo°]?\s*[-A-Z]*\s*\.?\s*\.{10,}')
# idem sem reticencias: o artigo em curso anuncia a alteracao ("passa a vigorar com a
# seguinte redacao:") e o cabecalho seguinte quebra a sequencia (ex.: Lei 12.850 art. 24
# transcreve o art. 288 do CP). Numeracao real avanca de 1 em 1 — nunca e suprimida.
ALTERA=re.compile(r'(?i)passa[m]? a vigorar|seguinte[s]? reda[çc][ãa]o|seguintes altera')
raw=open(sys.argv[1],"rb").read()
# Planalto serve pagina ora em cp1252/latin-1, ora em UTF-16 (ex.: Lei 11.340). Decodificar
# UTF-16 como latin-1 intercala NUL e o extrator acha ZERO artigo em silencio.
if raw[:2] in (b'\xff\xfe',b'\xfe\xff'): html=raw.decode("utf-16",errors="ignore")
elif raw[:3]==b'\xef\xbb\xbf': html=raw.decode("utf-8-sig")
else: html=raw.decode("latin-1")
# O Planalto serve um <script> de anti-bot (F5 CSPM) junto com o texto da lei. O strip de tags do
# clean() apaga a TAG e preserva o CONTEUDO, entao o JavaScript ia sendo acumulado no ultimo
# artigo em curso: o art. 12 da Lei 9.296 saiu com 780 caracteres de codigo colados na norma, e
# 32 dos 62 datasets carregavam o mesmo lixo no artigo final. Script, style e comentario sao
# ruido de pagina, nunca norma - caem aqui, antes do fatiamento por <p>.
html=re.sub(r'(?is)<script\b.*?</script>',' ',html)
html=re.sub(r'(?is)<style\b.*?</style>',' ',html)
html=re.sub(r'(?s)<!--.*?-->',' ',html)

fonte,url=sys.argv[3],sys.argv[4]; amax=int(sys.argv[5]) if len(sys.argv)>5 else 0
def clean(s):
    s=re.sub(r'<[^>]+>',' ',s)
    s=unescape(s)                     # cobre &nbsp; &quot; &amp; &ordm; e QUALQUER &#NNNN;
    s=s.replace('\xa0',' ')          # nbsp ja decodificado vira espaco de verdade
    s=re.sub(r'[ \t\r\n]+',' ',s).strip()
    s=re.sub(r'\bA\s?rt\s?\.\s*(?=\d)','Art. ',s)  # corrige cabeçalho quebrado "A rt." / "Ar t."
    s=re.sub(r'^Art\s+(?=\d)','Art. ',s)           # cabeçalho sem ponto: "Art 61." (Lei 9.504)
    m=re.match(r'(Art\.\s*)(\d[\d.]*(?:\s+\d+)+)',s)  # numero partido por markup: "Art. 5 7." -> 57
    if m: s=s[:m.start(2)]+re.sub(r'\s+','',m.group(2))+s[m.end(2):]
    return s
paras=re.split(r'(?i)<p\b[^>]*>', html)
ocor=[]; cur=None; ult=0; citados=[]   # ocorrencias em ordem de documento
for p in paras:
    t=clean(p)
    if not t: continue
    m=None if CITA.match(t) else HDR.match(t)
    if m:
        num=int(m.group(1).replace('.','')); suf=m.group(2) or m.group(3) or ''
        if cur is not None and ALTERA.search(cur["texto"]) and (num<=ult or num>ult+30):
            citados.append(f"{num}{'-'+suf if suf else ''}"); cur["texto"]+=" "+t; continue
        ult=num; cur={"key":(num,suf),"texto":t}; ocor.append(cur)
    elif cur is not None:
        cur["texto"]+=" "+t
M={}
for o in ocor:               # chave repetida no compilado: vence a ocorrencia mais completa
    k=o["key"]
    if k not in M or len(o["texto"])>len(M[k]["texto"]): M[k]=o
regs=[{"artigo":(f"{k[0]}-{k[1]}" if k[1] else str(k[0])),"texto":M[k]["texto"]} for k in sorted(M)]
json.dump({"fonte":fonte,"url":url,"total":len(regs),"artigos":regs},open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
nums=sorted(set(k[0] for k in M))
if not nums: print(f"{fonte}: 0 artigos — VERIFIQUE o HTML de origem"); sys.exit(3)
sufs=sum(1 for k in M if k[1])
gaps=[n for n in range(1,(amax or max(nums))+1) if n not in set(nums)]
print(f"{fonte}: {len(regs)} arts ({sufs} sufixados) | {min(nums)}-{max(nums)} | faltam(1..{amax or max(nums)}): {len(gaps)} {gaps[:15]}")
if citados: print(f"  transcricoes de norma alheia ignoradas: {', '.join(citados)}")
