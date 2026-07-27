import sys, re, json
# Extrator GENERICO de SUMARIO TEMATICO (obras STF: Coletanea Tematica de Jurisprudencia /
# Colecao Supremo Contemporaneo) -> indice tema -> pagina (como consultar_constituicao_supremo.py).
# Dois formatos de sumario: "Tema\nNUM" (tabs = nivel hierarquico) e "Tema......NUM" (dot leaders).
# Uso: python extrair_sumario_tematico.py <pdf> <pag_ini_0based> <pag_fim_0based_incl> <out.json> "<titulo>" "<serie>"
import fitz

pdf, p0, p1, out, titulo, serie = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
d = fitz.open(pdf)
raw = "\n".join(d[i].get_text() for i in range(p0, p1 + 1))
lines = raw.split("\n")

itens = []
pendente = None
pend_nivel = 0


def nivel(line):
    return len(line) - len(line.lstrip("\t"))


for ln in lines:
    if not ln.strip():
        continue
    s = ln.strip().replace("\x08", "").strip()
    if not s:
        continue
    if s.upper() in ("SUMÁRIO", "SUMARIO"):
        continue
    m = re.match(r'^(.+?)\.{3,}\s*(\d+)\s*$', s)
    if m:
        tema = m.group(1).strip()
        pag = int(m.group(2))
        itens.append({"tema": tema, "pagina": pag, "nivel": 0})
        pendente = None
        continue
    if re.fullmatch(r'\d+', s):
        if pendente:
            itens.append({"tema": pendente, "pagina": int(s), "nivel": pend_nivel})
            pendente = None
        continue
    pendente = s
    pend_nivel = nivel(ln)

json.dump({"titulo": titulo, "serie": serie, "fonte": pdf, "total": len(itens), "sumario": itens},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{titulo}: {len(itens)} tópicos extraídos do sumário")
