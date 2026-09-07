#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_ops.py — operacoes de PAGINA em PDF (juntar, dividir, comprimir, redigir, girar, extrair, PDF/A).

Existe porque o ecossistema so LIA PDF (pdf2md, pdf_para_markdown.py): nao havia como dividir autos
para o limite de upload do PJe, comprimir digitalizacao, nem tarjar de verdade um PDF que sai da
maquina (anonimizar.py so cobre Markdown). Avaliou-se o Stirling-PDF e descartou-se (memoria
`stirling-pdf-avaliado-nao-adotar`): tudo isto cabe em PyMuPDF, que ja e' dependencia de tudo.

Regras:
  * NUNCA sobrescreve a entrada. Sem -o, a saida vai para <nome>.<operacao>.pdf ao lado do original.
  * Redacao e' QUEIMA (apply_redactions): o texto sob a tarja e' removido do arquivo e a imagem e'
    apagada nos pixels. Nao e' caixa preta por cima. Confira a saida antes de enviar.
  * PDF digitalizado NAO tem camada de texto (o pdf2md nao reescreve o PDF): `redigir` sem --ocr nao
    acha nada nele. Com --ocr, o Tesseract (por) localiza as palavras na imagem e a tarja cai na caixa.
  * Paginas sao 1-based na CLI ("1-5,8,12-"); intervalo aberto vai ate o fim.

Uso:
  python pdf_ops.py info autos.pdf
  python pdf_ops.py juntar a.pdf b.pdf c.pdf -o tudo.pdf
  python pdf_ops.py dividir autos.pdf --tamanho 10MB -o partes/      # limite do PJe
  python pdf_ops.py dividir autos.pdf --cada 100 -o partes/
  python pdf_ops.py dividir autos.pdf --paginas 1-50,51-120 -o partes/
  python pdf_ops.py comprimir scan.pdf --dpi 150 --qualidade 60 -o scan.leve.pdf
  python pdf_ops.py redigir peca.pdf --termos "FULANO DE TAL" "Rua X" --identificadores -o peca.tarjada.pdf
  python pdf_ops.py redigir scan.pdf --termos-arquivo nomes.txt --ocr -o scan.tarjada.pdf
  python pdf_ops.py girar doc.pdf --graus 90 --paginas 3,7
  python pdf_ops.py extrair autos.pdf --paginas 10-25,40 -o trecho.pdf
  python pdf_ops.py pdfa peca.pdf -o peca.pdfa.pdf

Codigos de saida: 0 ok; 1 erro; 3 = algo ficou por fazer (termo nao encontrado, pagina sem texto
sem --ocr, parte que nao coube no tamanho) — leia o relatorio.
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

# Reusa a localizacao do Ghostscript/Tesseract do pdf2md (ambos fora do PATH nesta maquina).
# Carrega pdf2md/ambiente.py pelo caminho, e nao `from pdf2md import ambiente`: o __init__ do pacote
# puxa o nucleo inteiro (e o `fitz`, que imprime aviso de depreciacao) so para publicar dois binarios.
def _preparar_ambiente() -> None:
    arq = Path(__file__).resolve().parent.parent / "pdf2md" / "ambiente.py"
    if not arq.is_file():
        return
    try:
        spec = spec_from_file_location("pdf2md_ambiente", arq)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)  # o proprio modulo chama preparar() no import
    except Exception as exc:
        print("aviso: nao preparei Tesseract/Ghostscript (%s)" % exc, file=sys.stderr)


_preparar_ambiente()

import pymupdf  # PyMuPDF >= 1.24 (rewrite_images / subset_fonts)

# Identificadores (mesma familia do anonimizar.py). Uma palavra: CPF, CNPJ, e-mail, telefone com DDD
# colado. Duas palavras adjacentes: "(98)" + "99999-1234". Para CPF/CNPJ conta-se DIGITOS com
# separadores, porque o OCR le "123.456.7/789-09" e a regex exata perderia.
RE_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
RE_TEL = re.compile(r"^\(?\d{2}\)?\s?9?\d{4}-?\d{4}$")
RE_DDD = re.compile(r"^\(?\d{2}\)?$")
RE_TEL_SEM_DDD = re.compile(r"^9?\d{4}-\d{4}$")
PONTUACAO = ".,;:()[]"


def _classifica(token: str, tolerante: bool = False) -> str | None:
    """tolerante=True (via OCR): aceita um digito a mais ou a menos, porque o Tesseract le
    '123.456.7/789-09' (12 digitos) onde esta 123.456.789-09. Na camada de texto e' exato."""
    t = token.strip(PONTUACAO)
    if not t:
        return None
    if RE_EMAIL.match(t):
        return "EMAIL"
    if RE_TEL.match(t):
        return "TELEFONE"
    if any(c.isdigit() for c in t):
        digitos = re.sub(r"\D", "", t)
        separadores = len(t) - len(digitos)
        folga = 1 if tolerante else 0
        if abs(len(digitos) - 11) <= folga and separadores >= 2:
            return "CPF"
        if abs(len(digitos) - 14) <= folga and separadores >= 3:
            return "CNPJ"
    return None


def _identificadores(palavras: list, contagem: dict, tolerante: bool = False) -> list:
    """palavras = [(texto, Rect)] na ordem de leitura -> lista de Rect a tarjar."""
    rects = []
    for i, (txt, r) in enumerate(palavras):
        rot = _classifica(txt, tolerante)
        if rot:
            rects.append(r)
        elif RE_DDD.match(txt.strip(PONTUACAO)) and i + 1 < len(palavras)                 and RE_TEL_SEM_DDD.match(palavras[i + 1][0].strip(PONTUACAO)):
            rot = "TELEFONE"
            rects.append(pymupdf.Rect(r) | palavras[i + 1][1])
        if rot:
            contagem["<%s>" % rot] = contagem.get("<%s>" % rot, 0) + 1
    return rects
COBERTURA_DIGITALIZADA = 0.85  # imagem cobrindo >85% da pagina = digitalizacao (mesmo criterio do pdf2md)


# --------------------------------------------------------------------------
# utilitarios
# --------------------------------------------------------------------------
def _tamanho(txt: str) -> int:
    """'10MB', '900KB', '5000000' -> bytes."""
    m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*([kKmMgG]?)[bB]?\s*", txt)
    if not m:
        raise argparse.ArgumentTypeError("tamanho invalido: %r (ex.: 10MB, 900KB)" % txt)
    n = float(m.group(1).replace(",", "."))
    mult = {"": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}[m.group(2).lower()]
    return int(n * mult)


def _fmt(n: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return "%.1f %s" % (n, u) if u != "B" else "%d B" % n
        n /= 1024
    return "%d" % n


def _intervalos(spec: str | None, total: int) -> list[int]:
    """'1-5,8,12-' -> indices 0-based, na ordem dada (sem dedup: reordenar e' legitimo)."""
    if not spec:
        return list(range(total))
    out: list[int] = []
    for parte in spec.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            a, b = parte.split("-", 1)
            ini = int(a) if a.strip() else 1
            fim = int(b) if b.strip() else total
        else:
            ini = fim = int(parte)
        if ini < 1 or fim > total or ini > fim:
            raise SystemExit("intervalo fora do documento (%d paginas): %s" % (total, parte))
        out.extend(range(ini - 1, fim))
    return out


def _grupos(spec: str, total: int) -> list[list[int]]:
    """'1-50,51-120' -> um grupo por virgula (para dividir)."""
    return [_intervalos(p, total) for p in spec.split(",") if p.strip()]


def _saida(entrada: Path, op: str, dado: str | None) -> Path:
    if dado:
        p = Path(dado)
    else:
        p = entrada.with_name(entrada.stem + "." + op + ".pdf")
    if p.resolve() == entrada.resolve():
        raise SystemExit("recusado: a saida e' o proprio arquivo de entrada (%s)" % p)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _normaliza(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _digitalizada(pagina: pymupdf.Page) -> bool:
    """Ha uma imagem cobrindo quase a pagina toda. Contar caracteres nao serve: o carimbo do PJe
    sozinho da ~255 chars numa pagina que e' pura imagem (ver pdf2md/README)."""
    area = abs(pagina.rect)
    if not area:
        return False
    for info in pagina.get_image_info():
        r = pymupdf.Rect(info["bbox"]) & pagina.rect
        if abs(r) / area >= COBERTURA_DIGITALIZADA:
            return True
    return False


def _salvar(doc: pymupdf.Document, destino: Path, **extra) -> int:
    opts = dict(garbage=4, deflate=True, clean=True)
    opts.update(extra)
    doc.save(str(destino), **opts)
    return destino.stat().st_size


# --------------------------------------------------------------------------
# info
# --------------------------------------------------------------------------
def cmd_info(a) -> int:
    for arq in a.entradas:
        p = Path(arq)
        doc = pymupdf.open(p)
        digit = sum(1 for pg in doc if _digitalizada(pg))
        sem_texto = sum(1 for pg in doc if not pg.get_text("text").strip())
        meta = doc.metadata or {}
        print("%s" % p)
        print("  paginas      : %d  (digitalizadas: %d; sem nenhum texto: %d)" % (len(doc), digit, sem_texto))
        print("  tamanho      : %s  (%s por pagina)" % (_fmt(p.stat().st_size), _fmt(p.stat().st_size // max(1, len(doc)))))
        print("  cifrado      : %s" % ("sim" if doc.is_encrypted else "nao"))
        print("  produtor     : %s" % (meta.get("producer") or "-"))
        print("  marcadores   : %d" % len(doc.get_toc()))
        if digit:
            print("  aviso        : digitalizacao -> `redigir` so a alcanca com --ocr; o conteudo nao e' pesquisavel")
        doc.close()
    return 0


# --------------------------------------------------------------------------
# juntar
# --------------------------------------------------------------------------
def cmd_juntar(a) -> int:
    if len(a.entradas) < 2:
        raise SystemExit("juntar exige ao menos 2 arquivos")
    destino = _saida(Path(a.entradas[0]), "juntado", a.saida)
    out = pymupdf.open()
    toc: list = []
    for arq in a.entradas:
        src = pymupdf.open(arq)
        ini = len(out)
        out.insert_pdf(src)
        # um marcador de nivel 1 por arquivo, e os marcadores originais um nivel abaixo
        toc.append([1, Path(arq).stem, ini + 1])
        for nivel, titulo, pag in src.get_toc():
            toc.append([nivel + 1, titulo, ini + pag])
        print("  + %-50s %4d pag." % (Path(arq).name, len(src)))
        src.close()
    out.set_toc(toc)
    n = _salvar(out, destino)
    print("-> %s  (%d paginas, %s)" % (destino, len(out), _fmt(n)))
    return 0


# --------------------------------------------------------------------------
# dividir
# --------------------------------------------------------------------------
def _peso_paginas(doc: pymupdf.Document) -> list[int]:
    """Bytes de cada pagina salva SOZINHA. Superestima (recursos compartilhados contam em cada
    pagina), o que e' o lado seguro para um limite de upload."""
    pesos = []
    for i in range(len(doc)):
        tmp = pymupdf.open()
        tmp.insert_pdf(doc, from_page=i, to_page=i)
        pesos.append(len(tmp.tobytes(garbage=3, deflate=True)))
        tmp.close()
    return pesos


def _grupos_por_tamanho(doc: pymupdf.Document, limite: int) -> list[list[int]]:
    pesos = _peso_paginas(doc)
    folga = int(limite * 0.97)
    grupos: list[list[int]] = [[]]
    acum = 0
    for i, w in enumerate(pesos):
        if grupos[-1] and acum + w > folga:
            grupos.append([])
            acum = 0
        grupos[-1].append(i)
        acum += w
    return grupos


def _gravar_parte(doc: pymupdf.Document, paginas: list[int], destino: Path) -> int:
    parte = pymupdf.open()
    for i in paginas:
        parte.insert_pdf(doc, from_page=i, to_page=i)
    n = _salvar(parte, destino)
    parte.close()
    return n


def cmd_dividir(a) -> int:
    entrada = Path(a.entrada)
    doc = pymupdf.open(entrada)
    total = len(doc)
    modos = [m for m in (a.paginas, a.cada, a.tamanho) if m]
    if len(modos) != 1:
        raise SystemExit("escolha exatamente um: --paginas, --cada ou --tamanho")

    if a.paginas:
        grupos = _grupos(a.paginas, total)
    elif a.cada:
        grupos = [list(range(i, min(i + a.cada, total))) for i in range(0, total, a.cada)]
    else:
        grupos = _grupos_por_tamanho(doc, a.tamanho)

    pasta = Path(a.saida) if a.saida else entrada.with_name(entrada.stem + "_partes")
    pasta.mkdir(parents=True, exist_ok=True)
    largura = len(str(len(grupos)))
    pendentes = 0
    fila = list(enumerate(grupos, 1))
    resultados = []
    while fila:
        k, pags = fila.pop(0)
        nome = "%s_parte%s_p%03d-%03d.pdf" % (entrada.stem, str(k).zfill(largura), pags[0] + 1, pags[-1] + 1)
        destino = pasta / nome
        n = _gravar_parte(doc, pags, destino)
        # a estimativa e' por pagina isolada; se mesmo assim estourou, parte ao meio e tenta de novo
        if a.tamanho and n > a.tamanho and len(pags) > 1:
            destino.unlink()
            meio = len(pags) // 2
            fila[:0] = [(k, pags[:meio]), ("%s%s" % (k, "b"), pags[meio:])]
            continue
        flag = ""
        if a.tamanho and n > a.tamanho:
            flag = "   <- NAO COUBE (pagina unica maior que o limite; use `comprimir` antes)"
            pendentes += 1
        resultados.append((destino, len(pags), n))
        print("  %-55s %4d pag.  %9s%s" % (destino.name, len(pags), _fmt(n), flag))
    print("-> %d partes em %s" % (len(resultados), pasta))
    doc.close()
    return 3 if pendentes else 0


# --------------------------------------------------------------------------
# comprimir
# --------------------------------------------------------------------------
def cmd_comprimir(a) -> int:
    entrada = Path(a.entrada)
    destino = _saida(entrada, "comprimido", a.saida)
    antes = entrada.stat().st_size
    doc = pymupdf.open(entrada)
    if doc.is_encrypted:
        raise SystemExit("PDF cifrado: abra a senha antes")
    try:
        doc.rewrite_images(dpi_threshold=a.dpi + 1, dpi_target=a.dpi, quality=a.qualidade,
                           lossy=True, lossless=True, set_to_gray=a.cinza)
    except Exception as exc:  # versao antiga do PyMuPDF
        print("aviso: rewrite_images indisponivel (%s); so deflate/garbage" % exc, file=sys.stderr)
    try:
        doc.subset_fonts()
    except Exception:
        pass
    depois = _salvar(doc, destino)
    doc.close()
    print("%s -> %s   %s -> %s  (%.0f%%)" % (entrada.name, destino, _fmt(antes), _fmt(depois),
                                            100.0 * depois / max(1, antes)))
    if depois >= antes:
        print("aviso: nao encolheu; o PDF ja estava comprimido ou e' vetorial/texto")
    return 0


# --------------------------------------------------------------------------
# redigir (tarja queimada)
# --------------------------------------------------------------------------
def _termos(a) -> list[str]:
    termos = list(a.termos or [])
    if a.termos_arquivo:
        for linha in Path(a.termos_arquivo).read_text(encoding="utf-8", errors="replace").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                termos.append(linha)
    return [t for t in termos if t]


def _redigir_texto(pagina: pymupdf.Page, termos: list[str], identificadores: bool,
                   contagem: dict) -> int:
    n = 0
    for t in termos:
        # search_for e' insensivel a caixa; para acento, tenta a forma dada e a sem acento
        vistos = set()
        for forma in {t, unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()}:
            for r in pagina.search_for(forma, quads=False):
                chave = (round(r.x0), round(r.y0), round(r.x1), round(r.y1))
                if chave in vistos:
                    continue
                vistos.add(chave)
                pagina.add_redact_annot(r, fill=(0, 0, 0))
                contagem[t] = contagem.get(t, 0) + 1
                n += 1
    if identificadores:
        palavras = [(w[4], pymupdf.Rect(w[:4])) for w in pagina.get_text("words", sort=True)]
        for r in _identificadores(palavras, contagem):
            pagina.add_redact_annot(r, fill=(0, 0, 0))
            n += 1
    return n


def _redigir_ocr(pagina: pymupdf.Page, termos: list[str], identificadores: bool,
                 contagem: dict, dpi: int, idioma: str) -> int:
    import pytesseract
    from PIL import Image

    pix = pagina.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    dados = pytesseract.image_to_data(img, lang=idioma, output_type=pytesseract.Output.DICT)
    escala = 72.0 / dpi
    palavras = []
    for i, txt in enumerate(dados["text"]):
        txt = (txt or "").strip()
        if not txt:
            continue
        r = pymupdf.Rect(dados["left"][i] * escala, dados["top"][i] * escala,
                         (dados["left"][i] + dados["width"][i]) * escala,
                         (dados["top"][i] + dados["height"][i]) * escala)
        palavras.append((txt, _normaliza(txt), r))

    n = 0
    tokens_pag = [p[1] for p in palavras]
    for t in termos:
        alvo = _normaliza(t).split()
        if not alvo:
            continue
        L = len(alvo)
        for i in range(len(tokens_pag) - L + 1):
            if tokens_pag[i:i + L] == alvo:
                r = pymupdf.Rect(palavras[i][2])
                for j in range(i + 1, i + L):
                    r |= palavras[j][2]
                pagina.add_redact_annot(r + (-1, -1, 1, 1), fill=(0, 0, 0))
                contagem[t] = contagem.get(t, 0) + 1
                n += 1
    if identificadores:
        for r in _identificadores([(t, r) for t, _, r in palavras], contagem, tolerante=True):
            pagina.add_redact_annot(r + (-1, -1, 1, 1), fill=(0, 0, 0))
            n += 1
    return n


def cmd_redigir(a) -> int:
    entrada = Path(a.entrada)
    destino = _saida(entrada, "tarjado", a.saida)
    termos = _termos(a)
    if not termos and not a.identificadores:
        raise SystemExit("nada a tarjar: informe --termos, --termos-arquivo ou --identificadores")
    doc = pymupdf.open(entrada)
    if doc.is_encrypted:
        raise SystemExit("PDF cifrado: abra a senha antes")
    contagem: dict[str, int] = {}
    sem_texto = 0
    total_tarjas = 0
    paginas = _intervalos(a.paginas, len(doc))
    for i in paginas:
        pg = doc[i]
        # a camada de texto e' sempre varrida (numa digitalizacao ela tem ao menos o carimbo do PJe)
        total_tarjas += _redigir_texto(pg, termos, a.identificadores, contagem)
        if a.ocr_sempre or (a.ocr and _digitalizada(pg)):
            total_tarjas += _redigir_ocr(pg, termos, a.identificadores, contagem, a.dpi, a.idioma)
        elif _digitalizada(pg):
            sem_texto += 1
        if pg.annots(types=[pymupdf.PDF_ANNOT_REDACT]):
            pg.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_PIXELS,
                                graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    # metadados tambem vazam nome (Author/Title): zera
    doc.set_metadata({k: "" for k in ("author", "title", "subject", "keywords", "creator")})
    n = _salvar(doc, destino)
    doc.close()

    print("tarjas aplicadas: %d  -> %s (%s)" % (total_tarjas, destino, _fmt(n)))
    faltaram = [t for t in termos if t not in contagem]
    for t, c in sorted(contagem.items(), key=lambda kv: -kv[1]):
        print("  %4d  %s" % (c, t))
    pendente = False
    if faltaram:
        pendente = True
        print("NAO ENCONTRADOS (%d): %s" % (len(faltaram), "; ".join(faltaram)))
        print("  -> variacao de grafia/OCR? Confira o texto com `pdf2md` ou use --ocr.")
    if sem_texto:
        pendente = True
        print("PAGINAS DIGITALIZADAS SEM OCR: %d -> repita com --ocr para tarjar pela imagem" % sem_texto)
    return 3 if pendente else 0


# --------------------------------------------------------------------------
# girar / extrair
# --------------------------------------------------------------------------
def cmd_girar(a) -> int:
    entrada = Path(a.entrada)
    destino = _saida(entrada, "girado", a.saida)
    doc = pymupdf.open(entrada)
    for i in _intervalos(a.paginas, len(doc)):
        pg = doc[i]
        pg.set_rotation((pg.rotation + a.graus) % 360)
    n = _salvar(doc, destino)
    print("-> %s (%s)" % (destino, _fmt(n)))
    return 0


def cmd_extrair(a) -> int:
    entrada = Path(a.entrada)
    destino = _saida(entrada, "extraido", a.saida)
    doc = pymupdf.open(entrada)
    doc.select(_intervalos(a.paginas, len(doc)))  # tambem reordena e apaga
    n = _salvar(doc, destino)
    print("-> %s (%d paginas, %s)" % (destino, len(doc), _fmt(n)))
    return 0


# --------------------------------------------------------------------------
# pdfa (Ghostscript do PDF24)
# --------------------------------------------------------------------------
def _ghostscript() -> str:
    exe = shutil.which("gswin64c") or shutil.which("gs")
    if not exe:
        raise SystemExit("Ghostscript nao encontrado (vem com o PDF24: C:\\Program Files\\PDF24\\gs\\bin)")
    return exe


def cmd_pdfa(a) -> int:
    entrada = Path(a.entrada)
    destino = _saida(entrada, "pdfa", a.saida)
    gs = _ghostscript()
    raiz = Path(gs).resolve().parent.parent
    icc = raiz / "iccprofiles" / "default_rgb.icc"
    modelo = raiz / "lib" / "PDFA_def.ps"
    if not (icc.is_file() and modelo.is_file()):
        raise SystemExit("faltam %s ou %s" % (icc, modelo))
    # o PDFA_def.ps de fabrica aponta para um ICC generico: gera uma copia com o caminho real
    texto = modelo.read_text(encoding="latin-1")
    texto = re.sub(r"/ICCProfile \([^)]*\)", "/ICCProfile (%s)" % icc.as_posix(), texto)
    texto = texto.replace("(Title)", "(%s)" % entrada.stem.replace("(", "").replace(")", ""))
    with tempfile.NamedTemporaryFile("w", suffix="_PDFA_def.ps", delete=False, encoding="latin-1") as f:
        f.write(texto)
        def_ps = f.name
    cmd = [gs, "-dBATCH", "-dNOPAUSE", "-dNOOUTERSAVE", "-dQUIET",
           "-dPDFA=%d" % a.nivel, "-dPDFACompatibilityPolicy=1",
           "-sColorConversionStrategy=RGB", "-sDEVICE=pdfwrite",
           "-sOutputFile=%s" % destino, def_ps, str(entrada)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout)
    finally:
        os.unlink(def_ps)
    if r.returncode != 0 or not destino.is_file():
        print(r.stderr or r.stdout, file=sys.stderr)
        raise SystemExit("ghostscript falhou (codigo %d)" % r.returncode)
    print("-> %s (PDF/A-%db, %s)" % (destino, a.nivel, _fmt(destino.stat().st_size)))
    if r.stderr.strip():
        print("avisos do Ghostscript:\n" + r.stderr.strip(), file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="paginas, tamanho, quantas paginas tem texto")
    p.add_argument("entradas", nargs="+")
    p.set_defaults(fn=cmd_info)

    p = sub.add_parser("juntar", help="concatena PDFs (marcador por arquivo)")
    p.add_argument("entradas", nargs="+")
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_juntar)

    p = sub.add_parser("dividir", help="por intervalos, a cada N paginas ou por tamanho maximo")
    p.add_argument("entrada")
    p.add_argument("--paginas", help="grupos separados por virgula: 1-50,51-120")
    p.add_argument("--cada", type=int, help="N paginas por parte")
    p.add_argument("--tamanho", type=_tamanho, help="limite por parte, ex.: 10MB (upload do PJe)")
    p.add_argument("-o", "--saida", help="pasta de destino")
    p.set_defaults(fn=cmd_dividir)

    p = sub.add_parser("comprimir", help="reamostra imagens + deflate + subset de fontes")
    p.add_argument("entrada")
    p.add_argument("--dpi", type=int, default=150, help="dpi alvo das imagens (padrao 150)")
    p.add_argument("--qualidade", type=int, default=65, help="JPEG 1-100 (padrao 65)")
    p.add_argument("--cinza", action="store_true", help="converte imagens para tons de cinza")
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_comprimir)

    p = sub.add_parser("redigir", help="tarja QUEIMADA de termos/identificadores")
    p.add_argument("entrada")
    p.add_argument("--termos", nargs="*", help="strings a tarjar (insensivel a caixa e acento)")
    p.add_argument("--termos-arquivo", help="um termo por linha; # comenta")
    p.add_argument("--identificadores", action="store_true", help="CPF, CNPJ, e-mail, telefone por regex")
    p.add_argument("--paginas", help="restringe: 1-5,8")
    p.add_argument("--ocr", action="store_true", help="em pagina sem texto, localiza pelo Tesseract")
    p.add_argument("--ocr-sempre", action="store_true", help="OCR em todas as paginas (ignora a camada de texto)")
    p.add_argument("--dpi", type=int, default=200, help="dpi do render para OCR (padrao 200)")
    p.add_argument("--idioma", default="por", help="idioma Tesseract (padrao por)")
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_redigir)

    p = sub.add_parser("girar", help="gira paginas em multiplos de 90")
    p.add_argument("entrada")
    p.add_argument("--graus", type=int, choices=(90, 180, 270, -90), required=True)
    p.add_argument("--paginas")
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_girar)

    p = sub.add_parser("extrair", help="mantem so as paginas dadas, na ordem dada (reordena/apaga)")
    p.add_argument("entrada")
    p.add_argument("--paginas", required=True)
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_extrair)

    p = sub.add_parser("pdfa", help="converte para PDF/A via Ghostscript do PDF24")
    p.add_argument("entrada")
    p.add_argument("--nivel", type=int, choices=(1, 2, 3), default=2)
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("-o", "--saida")
    p.set_defaults(fn=cmd_pdfa)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
