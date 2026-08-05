#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consultar_informativo_stf.py — busca full-text nos Informativos do STF.

Corpus dedicado: C:\\Users\\alden\\.notebooklm\\informativo_stf\\fontes\\ (13 arquivos).

DUAS FAMILIAS, de natureza e conversao diferentes:

  * 2014-2019 — "Informativos STF: teses e fundamentos", compilados POR MATERIA
    (informativos2014.md ... informativos2019.md). Conversao DOCX legada, herdada
    do clone_jurisprudencia, SEM paginacao. O numero da edicao so aparece no
    texto em 2017 e 2018 (marcador "Informativo STF NNN").
  * 2020-2026 — "Informativo Tematico", compilacao anual POR RAMO DO DIREITO
    (Informativo_tematico_*.md). Conversao PDF pelo pipeline canonico, COM
    paginacao "## [p. N]" — logo o trecho e conferivel contra a pagina do PDF.
    A edicao sai do marcador "(INF NNN)" ate 2022 e do bloco "Ultimas
    atualizacoes" de 2023 em diante.

COBERTURA: 2014-2026 (edicoes ~733 a 1220). O STF publica Informativo desde 1995
(n. 1) — 1995-2013 NAO esta no acervo. O helper avisa isso no rodape.

Uso:
    python consultar_informativo_stf.py "reserva de plenario"
    python consultar_informativo_stf.py "marco temporal" --ano 2023
    python consultar_informativo_stf.py "improbidade" --edicao 1141 --contexto 400
Opcoes:
    --ano YYYY        so o arquivo daquele ano (2014..2026)
    --edicao N        so o(s) arquivo(s) cuja faixa cobre a edicao N
    --limite N        max. de trechos (padrao 12)
    --contexto N      caracteres em torno do match (padrao 260)
    --por-fonte N     max. de trechos por arquivo (padrao 3)
    --incluir-sumario tambem devolve matches no sumario/indice (por padrao, nao)
"""
import sys, os, re, argparse, unicodedata, glob

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DIR = r"C:\Users\alden\.notebooklm\informativo_stf\fontes"

RE_TESES = re.compile(r"^informativos(20\d\d)$", re.I)
RE_TEMATICO = re.compile(r"^Informativo_tematico_(20\d\d)", re.I)
RE_FAIXA = re.compile(r"Informativos?\s+STF\s+(\d{3,4})\s+a[o]?\s+(\d{3,4})", re.I)
RE_ED_INLINE = re.compile(r"Informativo\s+STF\s+(\d{3,4})")
RE_ED_INF = re.compile(r"\(\s*INF\s*(\d{3,4})\s*\)", re.I)
RE_ED_QUALQUER = re.compile(r"Informativo\s+(\d{3,4})")
RE_PAGINA = re.compile(r"^##\s*\[p\.\s*(\d+)\]", re.M)
RE_LINHA_SUMARIO = re.compile(r"\t\s*\d+\s*$")
RE_PRIMEIRO_RESUMO = re.compile(r"^[#*\s]*Resumo\s*:", re.M)
RE_PROC = re.compile(
    r"\b(ADPF|ADI|ADC|ADO|ARE|RHC|RMS|ACO|RE|HC|MS|MI|Rcl|AP|INQ|Pet|AC|AO|SS|SL|STA|EXT|AR|PSV|CC)"
    r"\s*\.?\s*(\d[\d.]*)"
)
# cobre "rel. min. X", "relator Min. X", "relatora Min. X", "relator Ministro X",
# "redator do acordao Min. X" e "red. p/ o ac. Min. X" — a abreviacao varia por ano.
RE_RELATOR = re.compile(r"(?:rel\.|relator[a]?|red\.|redator[a]?)[^,;\n]{0,32}?\bMin(?:\.|istr[oa])", re.I)
# ruido de conversao: marcacao markdown/HTML que o PDF->MD deixa no texto
RE_RUIDO = re.compile(r"(<u>|</u>|<mark>|</mark>|`o`|`|\*\*|__|#####|^#+\s*)", re.M)


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def limpar(s):
    return re.sub(r"\s+", " ", RE_RUIDO.sub(" ", s)).strip()


def proc_key(classe, numero):
    return classe.upper() + re.sub(r"\D", "", numero)


def fim_do_indice(txt, tipo):
    """Offset onde o corpo comeca — depois do sumario / bloco de atualizacoes.

    Match dentro do indice nao e conteudo: e so titulo com numero de pagina, e
    atribuir a ele o processo vizinho troca um julgado por outro.
    """
    if tipo == "tematico":
        m = RE_PRIMEIRO_RESUMO.search(txt)
        if m:
            return m.start()
    pos, fim = 0, 0
    for linha in txt.split("\n"):
        pos += len(linha) + 1
        if RE_LINHA_SUMARIO.search(linha):
            fim = pos
    return fim


def indice_edicoes(txt, corpo_ini):
    """Mapeia processo -> edicao a partir do bloco 'Ultimas atualizacoes'.

    Le em ORDEM DE DOCUMENTO: cada processo pertence a ultima edicao vista antes
    dele. Isso cobre os dois layouts — edicao numa linha e processos nas linhas
    seguintes (2023), e edicao + processos na MESMA linha (2024-2026) — e a
    decoracao markdown que a conversao de PDF deixa (**_Informativo 1121_**,
    <u>ADI 3.516/CE</u>).
    """
    idx = {}
    ed = None
    cabecalho = txt[:corpo_ini] if corpo_ini else txt[:120000]
    for m in re.finditer(r"Informativo\s+(\d{3,4})|" + RE_PROC.pattern, cabecalho):
        if m.group(1):
            ed = int(m.group(1))
        elif ed:
            idx.setdefault(proc_key(m.group(2), m.group(3)), ed)
    return idx


def carregar():
    fontes = []
    for path in sorted(glob.glob(os.path.join(DIR, "*.md"))):
        base = os.path.basename(path)[:-3]
        m_t = RE_TESES.match(base)
        m_m = RE_TEMATICO.match(base)
        if not (m_t or m_m):
            continue
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        tipo = "teses" if m_t else "tematico"
        # a faixa fica depois do cabecalho de medicao da conversao — janela larga
        mf = RE_FAIXA.search(txt[:80000])
        corpo_ini = fim_do_indice(txt, tipo)
        fontes.append({
            "arquivo": base, "texto": txt, "norm": norm(txt),
            "ano": int((m_t or m_m).group(1)), "tipo": tipo,
            "faixa": (int(mf.group(1)), int(mf.group(2))) if mf else None,
            "corpo_ini": corpo_ini,
            "indice": indice_edicoes(txt, corpo_ini) if tipo == "tematico" else {},
            "paginas": [(m.start(), int(m.group(1))) for m in RE_PAGINA.finditer(txt)],
        })
    return fontes


def pagina_de(fonte, pos):
    """Numero da pagina do PDF em que o trecho esta (so na familia paginada)."""
    atual = None
    for off, num in fonte["paginas"]:
        if off > pos:
            break
        atual = num
    return atual


def linha_de_fecho(txt, pos, fim, ano):
    """Primeira linha de citacao (processo + relator) DEPOIS do trecho.

    Nas duas familias o bloco de citacao fecha a entrada, entao a linha que vem
    logo apos o match e a que descreve o julgado do proprio trecho. Pegar a
    anterior trocaria um julgado por outro.
    """
    ini_linha = txt.rfind("\n", 0, pos) + 1
    candidatos = []
    for ordem, linha in enumerate(txt[ini_linha:fim].split("\n")):
        mr = RE_RELATOR.search(linha)
        if not mr:
            continue
        # exigir processo na mesma linha descarta prosa do tipo "o relator votou"
        procs = [m for m in RE_PROC.finditer(linha) if m.start() < mr.end()]
        if not procs:
            continue
        # em 2022 a citacao vem colada ao fim de um paragrafo longo: corta no processo
        texto = limpar(linha[procs[-1].start():])[:300]
        # a entrada tambem CITA precedentes antigos em nota; o fecho da propria
        # entrada e o que traz (INF n) ou a data do ano do arquivo.
        score = 0
        if RE_ED_INF.search(linha):
            score += 3
        if str(ano) in linha:
            score += 2
        if re.search(r"julgamento", linha, re.I):
            score += 1
        candidatos.append((-score, ordem, texto))
    if not candidatos:
        return None
    return sorted(candidatos)[0][2]


def referencia(fonte, pos, janela=6000):
    """Resolve edicao, processo e relator, tudo ancorado na MESMA linha de fecho."""
    txt = fonte["texto"]
    fim = min(len(txt), pos + janela)
    fecho = linha_de_fecho(txt, pos, fim, fonte["ano"])
    edicao, origem, processo = None, None, None

    if fecho:
        m = RE_PROC.search(fecho)
        if m:
            processo = "{} {}".format(m.group(1).upper(), m.group(2).rstrip("."))
        m = RE_ED_INF.search(fecho) or RE_ED_INLINE.search(fecho)
        if m:
            edicao, origem = int(m.group(1)), "marcador na linha de citacao"

    if not edicao:
        alvo = RE_ED_INF if fonte["tipo"] == "tematico" else RE_ED_INLINE
        m = alvo.search(txt, pos, fim)
        if m:
            edicao, origem = int(m.group(1)), "marcador no texto"

    if not edicao and fonte["tipo"] == "tematico" and processo:
        m = RE_PROC.search(processo)
        ed = fonte["indice"].get(proc_key(m.group(1), m.group(2))) if m else None
        if ed:
            edicao, origem = ed, "bloco 'Ultimas atualizacoes'"

    return edicao, origem, processo, fecho


def rotulo(fonte, edicao, origem):
    if edicao:
        return "Informativo STF {} ({})".format(edicao, origem)
    if fonte["faixa"]:
        return ("edicao NAO identificada no texto — arquivo cobre os Informativos "
                "STF {}-{}".format(*fonte["faixa"]))
    return "edicao NAO identificada no texto — compilacao por materia do ano {}".format(fonte["ano"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("termo")
    ap.add_argument("--ano", type=int)
    ap.add_argument("--edicao", type=int)
    ap.add_argument("--limite", type=int, default=12)
    ap.add_argument("--contexto", type=int, default=260)
    ap.add_argument("--por-fonte", type=int, default=3, dest="por_fonte")
    ap.add_argument("--incluir-sumario", action="store_true", dest="incluir_sumario")
    a = ap.parse_args()

    fontes = carregar()
    if not fontes:
        print("Corpus de Informativos do STF nao localizado em {}".format(DIR))
        return 1
    if a.ano:
        fontes = [f for f in fontes if f["ano"] == a.ano]
    if a.edicao:
        fontes = [f for f in fontes if f["faixa"] and f["faixa"][0] <= a.edicao <= f["faixa"][1]]
    if not fontes:
        print("Nenhum arquivo do acervo atende ao filtro (--ano/--edicao). "
              "Cobertura do acervo: 2014-2026.")
        return 0

    q = norm(a.termo)
    hits = []
    for f in fontes:
        start, got = 0, 0
        while len(hits) < a.limite and got < a.por_fonte:
            i = f["norm"].find(q, start)
            if i < 0:
                break
            start = i + len(q)
            if not a.incluir_sumario and i < f["corpo_ini"]:
                continue
            ini = max(0, i - a.contexto // 2)
            fim = min(len(f["texto"]), i + len(a.termo) + a.contexto // 2)
            ed, origem, proc, rel = referencia(f, i)
            if a.edicao and ed and ed != a.edicao:
                continue
            hits.append((f, ed, origem, proc, rel, limpar(f["texto"][ini:fim]), pagina_de(f, i)))
            got += 1
        if len(hits) >= a.limite:
            break

    if not hits:
        print('Nada encontrado para "{}" nos Informativos do STF (2014-2026).'.format(a.termo))
        print("Lacuna conhecida: 1995-2013 (edicoes 1 a ~732) NAO estao no acervo — "
              "pesquise em portal.stf.jus.br antes de concluir que o STF nao decidiu.")
        return 0

    nf = len(set(h[0]["arquivo"] for h in hits))
    print('Informativos do STF · "{}" · {} trecho(s) em {} fonte(s)\n'.format(a.termo, len(hits), nf))
    for f, ed, origem, proc, rel, snip, pag in hits:
        tipo = "Teses e Fundamentos" if f["tipo"] == "teses" else "Informativo Tematico"
        cab = "[{}] {}".format(f["ano"], tipo)
        if pag:
            cab += " · p. {} do PDF".format(pag)
        print(cab)
        print("  Edicao: {}".format(rotulo(f, ed, origem)))
        if proc:
            print("  Processo: {}".format(proc))
        if rel:
            print("  Ref.: {}".format(rel))
        print("  …{}…".format(snip))
        print("  (fonte: {}.md)\n".format(f["arquivo"]))

    print("Acervo: ~/.notebooklm/informativo_stf/fontes · cobertura 2014-2026 (ed. ~733-1220).")
    print("LACUNA: Informativos 1995-2013 (n. 1 a ~732) nao estao no acervo.")
    print("ANTI-INVENCAO: texto convertido. Confirme numero da edicao, inteiro teor e "
          "atualidade em portal.stf.jus.br antes de citar. 'Processo' e 'Ref.' vem da "
          "entrada mais proxima do trecho — confira se correspondem ao trecho citado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
