#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motor de conversao PDF -> Markdown paginado.

Principios (regra canonica de ~/.claude/CLAUDE.md):

1. O original NUNCA e' alterado nem apagado.
2. A paginacao vira `## [p. N]`, para que toda citacao seja verificavel
   contra a pagina do PDF.
3. A perda e' MEDIDA e declarada no cabecalho do .md — conversao PDF->MD
   perde conteudo em silencio, entao o relatorio e' parte do produto.
4. Pagina sem texto extraivel nao e' aceita calada: ou vai para OCR, ou o
   arquivo sai marcado com alerta e codigo de saida 3.

O OCR e' seletivo POR PAGINA (renderiza so a pagina sem texto e passa no
Tesseract), e nao pelo arquivo inteiro. Num processo do PJe com 1.800
paginas em que 300 sao digitalizadas, isso e' a diferenca entre minutos e
horas — e nao reescreve o PDF de origem.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import ambiente  # noqa: F401  (prepara PATH/TESSDATA no import)
from .perfis import Perfil, obter

import fitz  # PyMuPDF

LIMIAR_PAGINA_VAZIA = 20  # caracteres brutos; abaixo disso nem carimbo existe

# Caracteres RESTANTES depois de descontar o carimbo. E' este o limiar que
# decide se a pagina tem corpo de verdade.
#
# Contar caractere BRUTO nao serve em autos do PJe: o carimbo que o sistema
# imprime em toda pagina (`Num. 57493199 - Pag. 1`, assinatura eletronica) e'
# texto NATIVO, tem 20-70 caracteres e passa por cima de qualquer limiar
# ingenuo. Uma pagina digitalizada carimbada parece integra, o OCR nunca
# dispara e o relatorio jura que esta completo. Aconteceu de verdade: num
# processo de 365 paginas, 83 (23%) eram imagem sem OCR — inclusive a ata de
# audiencia, peca nuclear do caso — e a conversao declarou "nenhuma pagina
# sem texto".
LIMIAR_TEXTO_UTIL = 60

# Fracao da pagina coberta por imagem a partir da qual se assume que ha
# conteudo visual ali (ou seja: pouco texto + imagem grande = scan por ler,
# em vez de pagina genuinamente quase em branco).
FRACAO_PAGINA_DIGITALIZADA = 0.50

# --------------------------------------------------------------------------
# Boilerplate do PJe que se repete em toda pagina e polui o Markdown.
# Removido apenas com limpar_rodape=True, e SEMPRE contabilizado no relatorio.
# --------------------------------------------------------------------------
RE_RODAPE_PJE = [
    re.compile(r"^\s*Assinado\s+eletronicamente\s+por[:\s].*$", re.I),
    re.compile(r"^\s*https?://pje\S*", re.I),
    re.compile(r"^\s*N[uú]mero\s+do\s+documento\s*:\s*\S+\s*$", re.I),
    re.compile(r"^\s*Documento\s+assinado\s+digitalmente.*$", re.I),
    re.compile(r"^\s*Este\s+documento\s+(pode|foi)\s+.*(conferid|assinad).*$", re.I),
    re.compile(r"^\s*C[oó]digo\s+de\s+valida[cç][aã]o\s*:?\s*\S*\s*$", re.I),
]

# Marcadores que identificam o documento dentro dos autos do PJe.
RE_NUM_PAG_PJE = re.compile(r"Num\.\s*(\d{4,})\s*[-–]\s*P[aá]g\.\s*(\d+)", re.I)
RE_ID_PJE = re.compile(r"\bId\.?\s*([0-9a-f]{6,})\b", re.I)
RE_NUM_DOC_PJE = re.compile(r"N[uú]mero\s+do\s+documento\s*:\s*(\S+)", re.I)

# Tudo que e' CARIMBO, para efeito de MEDIR se a pagina tem corpo. Note que
# esta lista e' mais ampla que a do `limpar_rodape`: aqui entra tambem o
# `Num. X - Pag. N`, que na saida e' util (identifica o documento) mas que,
# na hora de decidir se a pagina foi lida, nao pode contar como conteudo.
RE_SO_CARIMBO = RE_RODAPE_PJE + [
    RE_NUM_PAG_PJE,
    re.compile(r"^\s*P[aá]g(?:ina)?\.?\s*\d+\s*(?:de\s*\d+)?\s*$", re.I),
    re.compile(r"^\s*\d{1,4}\s*$"),                      # numero de folha solto
    re.compile(r"^\s*f?ls?\.?\s*\d+\s*$", re.I),         # "fl. 12", "fls 12"
]


# ==========================================================================
# Estruturas de resultado
# ==========================================================================
@dataclass
class Pagina:
    numero: int
    texto: str = ""
    chars: int = 0
    util: int = 0
    """Caracteres DESCONTADO o carimbo — a medida que diz se a pagina foi lida."""
    ocr: bool = False
    ilegivel: bool = False
    """Sobrou conteudo visual que nenhuma passagem conseguiu ler."""
    imagens: list[str] = field(default_factory=list)
    doc_pje: str | None = None
    linhas_removidas: int = 0


@dataclass
class Resultado:
    origem: Path
    destino: Path | None = None
    paginas: int = 0
    chars: int = 0
    chars_nativos: int = 0
    chars_ocr: int = 0
    paginas_ocr: int = 0
    paginas_vazias: list[int] = field(default_factory=list)
    paginas_ilegiveis: list[int] = field(default_factory=list)
    """Paginas com conteudo visual que continuou sem ser lido — o carimbo do
    PJe fazia estas passarem por integras."""
    paginas_carimbo: int = 0
    """Quantas chegaram tendo apenas carimbo (antes do OCR)."""
    imagens: int = 0
    pasta_imagens: Path | None = None
    docs_pje: list[tuple[str, int, int]] = field(default_factory=list)
    rodapes_removidos: int = 0
    controles_removidos: int = 0
    perfil: str = ""
    perfil_detectado: str | None = None
    duracao: float = 0.0
    erro: str | None = None
    cancelado: bool = False
    aviso_estrutura: str | None = None
    """Preenchido quando a analise de estrutura foi pedida mas nao rodou. O
    Markdown sai mais cru (sem titulos/tabelas) — e isso precisa ser dito, nao
    engolido."""

    @property
    def ok(self) -> bool:
        return self.erro is None and not self.cancelado

    @property
    def media_chars(self) -> float:
        return (self.chars / self.paginas) if self.paginas else 0.0

    @property
    def precisa_ocr(self) -> bool:
        """Sobrou pagina por ler — a conversao esta incompleta.

        Inclui a pagina que so tem carimbo sobre uma digitalizacao: ela NAO
        esta vazia (o carimbo e' texto), mas tambem nao foi lida.
        """
        return bool(self.paginas_vazias or self.paginas_ilegiveis)

    @property
    def pendentes(self) -> list[int]:
        return sorted(set(self.paginas_vazias) | set(self.paginas_ilegiveis))

    def resumo(self) -> str:
        if self.erro:
            return "ERRO  %s  ->  %s" % (self.origem.name, self.erro)
        if self.cancelado:
            return "CANCELADO  %s" % self.origem.name
        s = "%-42s %4d pag | %8d chars | media %5.0f | OCR %3d pag | img %3d | %5.1fs" % (
            self.origem.name[:42], self.paginas, self.chars, self.media_chars,
            self.paginas_ocr, self.imagens, self.duracao,
        )
        if self.aviso_estrutura:
            s += "\n   AVISO: analise de estrutura indisponivel (%s) — Markdown mais cru." \
                 % self.aviso_estrutura
        if self.paginas_ilegiveis:
            s += ("\n   ALERTA: %d pagina(s) com imagem NAO LIDA (so carimbo/sem texto): %s"
                  % (len(self.paginas_ilegiveis), _amostra(self.paginas_ilegiveis)))
        vazias_so = [n for n in self.paginas_vazias if n not in set(self.paginas_ilegiveis)]
        if vazias_so:
            s += "\n   ALERTA: %d pagina(s) sem texto algum: %s" % (
                len(vazias_so), _amostra(vazias_so))
        return s


def _amostra(nums: list[int], n: int = 20) -> str:
    txt = ", ".join(str(x) for x in nums[:n])
    return txt + (" ..." if len(nums) > n else "")


@contextlib.contextmanager
def _silencio():
    """Cala a tagarelice do parser (PyMuPDF e pymupdf4llm) durante a extracao.

    O PyMuPDF escreve suas mensagens fora do `sys.stdout` do Python, entao
    redirecionar os streams nao basta: e' preciso `set_messages`.
    """
    sink = io.StringIO()
    try:
        fitz.set_messages(stream=sink)
    except Exception:
        pass
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            yield sink
    finally:
        try:
            fitz.set_messages(fd=2)  # devolve para o stderr
        except Exception:
            pass


# ==========================================================================
# Deteccao automatica de perfil
# ==========================================================================
def detectar_perfil(caminho: str | Path, amostra: int = 12) -> str:
    """Adivinha o tipo do documento lendo uma amostra das paginas."""
    doc = fitz.open(str(caminho))
    try:
        n = doc.page_count
        if n == 0:
            return "decisao"
        idx = sorted({int(i * (n - 1) / max(amostra - 1, 1)) for i in range(min(amostra, n))})

        texto_amostra = []
        img_grandes = 0
        vazias = 0
        for i in idx:
            page = doc[i]
            t = page.get_text("text") or ""
            texto_amostra.append(t)
            if len(t.strip()) < LIMIAR_PAGINA_VAZIA:
                vazias += 1
            area_pag = abs(page.rect.width * page.rect.height) or 1
            for bloco in page.get_image_info():
                bb = bloco.get("bbox")
                if not bb:
                    continue
                area = abs((bb[2] - bb[0]) * (bb[3] - bb[1]))
                # figura de verdade: nem icone, nem a digitalizacao da pagina toda
                if 0.02 < area / area_pag < 0.85:
                    img_grandes += 1

        junto = "\n".join(texto_amostra)
        tem_pje = bool(
            RE_NUM_PAG_PJE.search(junto)
            or re.search(r"pje\.\w+\.jus\.br", junto, re.I)
            or (re.search(r"Assinado eletronicamente por", junto, re.I) and n > 20)
        )
        if tem_pje:
            return "pje"
        if img_grandes >= max(2, len(idx) // 3):
            return "laudo"
        if n >= 80 and (doc.get_toc() or vazias == 0):
            return "livro"
        return "decisao"
    finally:
        doc.close()


# ==========================================================================
# OCR seletivo por pagina
# ==========================================================================
def _limiar_otsu(hist) -> int:
    """Limiar de Otsu a partir do histograma de 256 niveis.

    Feito em NumPy de proposito: o OpenCV traria 112 MB so para esta conta,
    o que dobraria o tamanho do executavel standalone.
    """
    import numpy as np

    hist = hist.astype(float)
    total = hist.sum()
    if total <= 0:
        return 128
    niveis = np.arange(256)
    peso_bg = np.cumsum(hist)
    peso_fg = total - peso_bg
    validos = (peso_bg > 0) & (peso_fg > 0)
    if not validos.any():
        return 128
    soma_total = (niveis * hist).sum()
    soma_bg = np.cumsum(niveis * hist)
    media_bg = np.divide(soma_bg, peso_bg, out=np.zeros(256), where=peso_bg > 0)
    media_fg = np.divide(soma_total - soma_bg, peso_fg, out=np.zeros(256),
                         where=peso_fg > 0)
    variancia = peso_bg * peso_fg * (media_bg - media_fg) ** 2
    variancia[~validos] = -1
    return int(np.argmax(variancia))


def _realcar(img):
    """Mediana 3x3 + binarizacao de Otsu. So com Pillow e NumPy."""
    try:
        import numpy as np
        from PIL import ImageFilter
    except ImportError:
        return img
    try:
        suave = img.convert("L").filter(ImageFilter.MedianFilter(3))
        arr = np.asarray(suave)
        limiar = _limiar_otsu(np.bincount(arr.ravel(), minlength=256))
        return suave.point(lambda v, _t=limiar: 255 if v > _t else 0, mode="L")
    except Exception:
        return img  # realce e' melhoria, nao requisito


def _ocr_pagina(page, perfil: Perfil) -> str:
    """Renderiza a pagina e passa no Tesseract. Devolve '' se OCR indisponivel."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""

    pix = page.get_pixmap(dpi=perfil.ocr_dpi, colorspace=fitz.csGRAY)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    if perfil.ocr_preproc:
        img = _realcar(img)

    try:
        bruto = pytesseract.image_to_string(
            img, lang=perfil.ocr_idioma, config=perfil.ocr_config) or ""
    except Exception:
        return ""
    # NFC: o OCR devolve acento DECOMPOSTO ("a"+"~"), e nesse estado o `grep`
    # por "não" nao casa com o que esta no arquivo.
    return unicodedata.normalize("NFC", bruto).strip()


# ==========================================================================
# Extracao de imagens
# ==========================================================================
LADO_MINIMO = 8      # px: abaixo disso e' filete/regua, nao figura
AREA_MINIMA = 2000   # px2: mata espacadores (o 2x2 tem area 4)


def _figura_relevante(larg: int, alt: int, minimo: int) -> bool:
    """Distingue figura de enfeite.

    Exigir `minimo` nas DUAS dimensoes descartaria um banner legitimo de
    623x79. O criterio e', entao: o maior lado passa do minimo, nenhum lado
    e' degenerado, e a area nao e' de espacador.
    """
    if larg <= 0 or alt <= 0:
        return False
    return (max(larg, alt) >= minimo
            and min(larg, alt) >= LADO_MINIMO
            and larg * alt >= AREA_MINIMA)
def _extrair_imagens(doc, page, num: int, perfil: Perfil, pasta: Path,
                     vistos: set[str], pagina_e_scan: bool) -> list[str]:
    salvos: list[str] = []
    area_pag = abs(page.rect.width * page.rect.height) or 1

    # bbox por xref, para saber o tamanho relativo de cada figura na pagina
    bbox_por_xref: dict[int, float] = {}
    for info in page.get_image_info(xrefs=True):
        xr = info.get("xref")
        bb = info.get("bbox")
        if xr and bb:
            bbox_por_xref[xr] = abs((bb[2] - bb[0]) * (bb[3] - bb[1])) / area_pag

    for k, info in enumerate(page.get_images(full=True), start=1):
        xref = info[0]
        fracao = bbox_por_xref.get(xref, 0.0)
        # A digitalizacao da propria pagina nao e' uma figura do laudo.
        if pagina_e_scan and fracao > 0.85:
            continue
        try:
            base = doc.extract_image(xref)
        except Exception:
            continue

        dados = base.get("image")
        if not dados:
            continue
        larg, alt = base.get("width", 0), base.get("height", 0)
        if not _figura_relevante(larg, alt, perfil.img_min_px):
            continue  # espacador, filete ou icone

        digest = hashlib.md5(dados).hexdigest()
        if perfil.img_dedup and digest in vistos:
            continue
        vistos.add(digest)

        ext = (base.get("ext") or "png").lower()
        pasta.mkdir(parents=True, exist_ok=True)
        nome = "p%04d_img%02d.%s" % (num, k, ext)
        (pasta / nome).write_bytes(dados)
        salvos.append("%s/%s" % (pasta.name, nome))

    return salvos


# ==========================================================================
# Saneamento de caracteres de controle
# ==========================================================================
# Bastam alguns bytes NUL para o `grep` passar a tratar o .md como binario e
# SUPRIMIR o conteudo sem avisar (o `grep -c` nem denuncia). Extracao de PDF
# produz esses bytes com alguma frequencia — entao eles saem aqui, contados.
RE_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _texto_util(texto: str) -> str:
    """O que sobra da pagina depois de descontar o carimbo.

    E' esta medida — e nao a contagem bruta — que diz se a pagina foi lida.
    """
    if not texto:
        return ""
    t = RE_NUM_PAG_PJE.sub(" ", texto)
    t = RE_NUM_DOC_PJE.sub(" ", t)
    sobrou = [ln for ln in t.split("\n")
              if not any(rx.match(ln) for rx in RE_SO_CARIMBO)]
    return re.sub(r"\s+", " ", " ".join(sobrou)).strip()


def _cobertura_imagem(page) -> float:
    """Fracao da pagina ocupada por imagem (0 a 1).

    Distingue pagina QUASE EM BRANCO (legitimamente curta) de DIGITALIZACAO
    NAO LIDA (tem conteudo visual que o texto nao reflete).
    """
    area = abs(page.rect.width * page.rect.height) or 1
    total = 0.0
    try:
        for info in page.get_image_info():
            bb = info.get("bbox")
            if bb:
                total += abs((bb[2] - bb[0]) * (bb[3] - bb[1]))
    except Exception:
        return 0.0
    return min(total / area, 1.0)


def _sanear(texto: str) -> tuple[str, int]:
    if not texto:
        return texto, 0
    achados = len(RE_CONTROLE.findall(texto))
    if not achados:
        return texto, 0
    return RE_CONTROLE.sub("", texto), achados


# ==========================================================================
# Limpeza de rodape
# ==========================================================================
def _limpar_rodape(texto: str) -> tuple[str, int]:
    saida, removidas = [], 0
    for linha in texto.split("\n"):
        if any(rx.match(linha) for rx in RE_RODAPE_PJE):
            removidas += 1
            continue
        saida.append(linha)
    # colapsa as linhas em branco que a remocao deixou para tras
    txt = re.sub(r"\n{3,}", "\n\n", "\n".join(saida)).strip()
    return txt, removidas


# ==========================================================================
# Conversao
# ==========================================================================
def _resolver_perfil(caminho: Path, perfil, sobrescritas, res: Resultado) -> Perfil:
    """Decide a configuracao efetiva deste arquivo.

    `perfil` pode ser o nome ("auto", "pje", ...) ou um Perfil pronto. Com
    "auto", o tipo e' detectado por arquivo. `sobrescritas` sao as escolhas
    EXPLICITAS do usuario e vencem o que o perfil traz.
    """
    if isinstance(perfil, Perfil):
        cfg = perfil
        if cfg.nome != "auto":
            return cfg.com(**(sobrescritas or {}))
    try:
        nome = perfil if isinstance(perfil, str) else perfil.nome
    except AttributeError:
        nome = "auto"

    if (nome or "auto").strip().lower() != "auto":
        return obter(nome).com(**(sobrescritas or {}))

    try:
        detectado = detectar_perfil(caminho)
    except Exception:
        detectado = "decisao"
    res.perfil_detectado = detectado
    return obter(detectado).com(**(sobrescritas or {}))


def converter(
    caminho: str | Path,
    destino: str | Path | None = None,
    perfil: Perfil | str = "auto",
    sobrescritas: dict | None = None,
    intervalo: tuple[int, int] | None = None,
    escrever: bool = True,
    progresso=None,
    cancelar=None,
) -> Resultado:
    """Converte UM pdf. `progresso(feito, total, rotulo)`; `cancelar` = Event.

    Com `escrever=False` a conversao roda inteira e MEDE o resultado, mas nao
    grava nada em disco — e' o modo de conferencia previsto pela regra
    canonica ("confira a perda ANTES de destilar").
    """
    t0 = time.time()
    caminho = Path(caminho)
    res = Resultado(origem=caminho)

    try:
        cfg = _resolver_perfil(caminho, perfil, sobrescritas, res)
    except KeyError as exc:
        res.erro = str(exc)
        res.duracao = time.time() - t0
        return res
    res.perfil = cfg.nome

    try:
        doc = fitz.open(str(caminho))
    except Exception as exc:
        res.erro = "nao foi possivel abrir: %s" % exc
        res.duracao = time.time() - t0
        return res

    try:
        total = doc.page_count
        ini, fim = (1, total)
        if intervalo:
            ini = max(1, intervalo[0])
            fim = min(total, intervalo[1] or total)
        alvos = list(range(ini - 1, fim))
        if not alvos:
            res.erro = "intervalo de paginas vazio (%d-%d de %d)" % (ini, fim, total)
            return res

        # ---- passo 1: censo da camada de texto ---------------------------
        # Precisa vir ANTES de qualquer outra coisa: a extracao estruturada
        # MUTA o documento em memoria (injeta o texto que ela mesma OCRa), e
        # depois disso `get_text` deixa de distinguir pagina digitalizada de
        # pagina nativa.
        if progresso:
            progresso(0, len(alvos), "inspecionando")
        sem_camada: dict[int, bool] = {}      # nem carimbo tem
        so_carimbo: dict[int, bool] = {}      # tem carimbo, mas nao tem corpo
        tem_imagem: dict[int, bool] = {}      # ha conteudo visual na pagina
        for idx in alvos:
            pg = doc[idx]
            bruto = (pg.get_text("text") or "").strip()
            util = _texto_util(bruto)
            num = idx + 1
            sem_camada[num] = len(bruto) < LIMIAR_PAGINA_VAZIA
            so_carimbo[num] = len(util) < LIMIAR_TEXTO_UTIL
            tem_imagem[num] = _cobertura_imagem(pg) >= FRACAO_PAGINA_DIGITALIZADA
        # Ambas as situacoes exigem OCR: a pagina sem nada e a pagina que so
        # tem carimbo. Ignorar a segunda foi exatamente o defeito que fazia o
        # conversor declarar "completo" sobre autos digitalizados.
        qtd_scan = sum(1 for n in sem_camada if so_carimbo[n])

        # ---- passo 2: extracao estruturada (opcional, mais lenta) --------
        # O OCR interno do pymupdf4llm fica DESLIGADO de proposito: ele usa
        # RapidOCR e ignora o parametro `ocr_language`, devolvendo portugues
        # sem acento ("RELATORIO", "Contradicao", "Obito") — a degradacao
        # silenciosa que esta ferramenta existe para evitar. O OCR aqui e'
        # sempre o Tesseract com o idioma do perfil (passo 3).
        estruturado: dict[int, str] = {}
        vale_estruturar = cfg.estruturado and qtd_scan < len(alvos)
        if vale_estruturar:
            if progresso:
                progresso(0, len(alvos), "lendo estrutura")
            try:
                import pymupdf4llm

                base_kw = dict(pages=alvos, page_chunks=True, show_progress=False)
                with _silencio():
                    try:
                        chunks = pymupdf4llm.to_markdown(
                            doc, **base_kw, use_ocr=False, force_ocr=False)
                    except TypeError:
                        # versao antiga: nao tem o caminho de layout nem OCR
                        chunks = pymupdf4llm.to_markdown(doc, **base_kw)
                for ch in chunks:
                    n = ch.get("metadata", {}).get("page_number")
                    if n:
                        estruturado[int(n)] = (ch.get("text") or "").strip()
            except Exception as exc:
                # Degrada para get_text puro em vez de quebrar — mas DECLARA,
                # porque a diferenca aparece no Markdown (sem titulos, sem
                # tabelas) e o usuario precisa saber por que.
                estruturado = {}
                res.aviso_estrutura = "%s: %s" % (type(exc).__name__, exc)

        # ---- passo 3: pagina a pagina -----------------------------------
        pasta_img = caminho.parent if destino is None else Path(destino)
        pasta_img = pasta_img / (caminho.stem + "_imagens")
        vistos: set[str] = set()
        paginas: list[Pagina] = []
        doc_atual: str | None = None

        for i, idx in enumerate(alvos, start=1):
            if cancelar is not None and cancelar.is_set():
                res.cancelado = True
                return res

            page = doc[idx]
            num = idx + 1
            p = Pagina(numero=num)

            # Vem do censo do passo 1, feito antes de a extracao estruturada
            # mexer no documento.
            e_scan = sem_camada.get(num, False)
            carimbada = so_carimbo.get(num, False)
            texto = estruturado.get(num) or ("" if e_scan
                                             else (page.get_text("text") or "").strip())

            if progresso:
                progresso(i, len(alvos), "p. %d/%d" % (num, total))

            # OCR nas paginas sem corpo de texto — inclusive as que trazem
            # SO O CARIMBO do PJe sobre uma digitalizacao.
            precisa = carimbada or e_scan
            if cfg.ocr == "sempre" or (cfg.ocr == "auto" and precisa):
                ocr_txt = _ocr_pagina(page, cfg)
                if len(_texto_util(ocr_txt)) > len(_texto_util(texto)):
                    texto = ocr_txt
                    p.ocr = True
            if precisa and len(_texto_util(texto)) >= LIMIAR_TEXTO_UTIL:
                p.ocr = True  # veio de OCR, seja qual for o motor

            p.util = len(_texto_util(texto))
            # Continua ilegivel: pouco texto E conteudo visual na pagina.
            # Pagina genuinamente quase em branco (sem imagem) nao entra aqui.
            p.ilegivel = p.util < LIMIAR_TEXTO_UTIL and tem_imagem.get(num, False)

            # marcador do documento dentro dos autos do PJe
            if cfg.indice_pje:
                m = RE_NUM_PAG_PJE.search(texto) or RE_NUM_DOC_PJE.search(texto) \
                    or RE_ID_PJE.search(texto)
                if m:
                    p.doc_pje = m.group(1)
                    doc_atual = p.doc_pje
                elif doc_atual:
                    p.doc_pje = doc_atual

            texto, controles = _sanear(texto)
            res.controles_removidos += controles

            if cfg.limpar_rodape and texto:
                texto, removidas = _limpar_rodape(texto)
                p.linhas_removidas = removidas
                res.rodapes_removidos += removidas

            if cfg.extrair_imagens and escrever:
                try:
                    p.imagens = _extrair_imagens(
                        doc, page, num, cfg, pasta_img, vistos, e_scan)
                except Exception:
                    p.imagens = []

            p.texto = texto
            p.chars = len(texto)
            if p.ocr:
                res.paginas_ocr += 1
                res.chars_ocr += p.chars
            else:
                res.chars_nativos += p.chars
            if p.chars < LIMIAR_PAGINA_VAZIA:
                res.paginas_vazias.append(num)
            if p.ilegivel:
                res.paginas_ilegiveis.append(num)
            if carimbada:
                res.paginas_carimbo += 1

            paginas.append(p)

        res.paginas = len(paginas)
        res.chars = sum(p.chars for p in paginas)
        res.imagens = sum(len(p.imagens) for p in paginas)
        if res.imagens:
            res.pasta_imagens = pasta_img
        res.docs_pje = _resumir_docs_pje(paginas)

        # ---- passo 4: escrita -------------------------------------------
        markdown = _montar_markdown(caminho, doc, paginas, res, cfg, (ini, fim, total))
        if escrever:
            if destino is not None:
                out_dir = Path(destino)
                out_dir.mkdir(parents=True, exist_ok=True)
            else:
                out_dir = caminho.parent
            saida = out_dir / (caminho.stem + ".md")
            saida.write_text(markdown, encoding="utf-8")
            res.destino = saida

    except Exception as exc:
        res.erro = "%s: %s" % (type(exc).__name__, exc)
    finally:
        with contextlib.suppress(Exception):
            doc.close()
        res.duracao = time.time() - t0

    return res


def _resumir_docs_pje(paginas: list[Pagina]) -> list[tuple[str, int, int]]:
    """[(id_documento, primeira_pagina, ultima_pagina), ...]"""
    out: list[list] = []
    for p in paginas:
        if not p.doc_pje:
            continue
        if out and out[-1][0] == p.doc_pje:
            out[-1][2] = p.numero
        else:
            out.append([p.doc_pje, p.numero, p.numero])
    return [(a, b, c) for a, b, c in out]


def _montar_markdown(caminho: Path, doc, paginas: list[Pagina],
                     res: Resultado, cfg: Perfil, faixa: tuple) -> str:
    ini, fim, total = faixa
    tam = caminho.stat().st_size / 1024
    meta = doc.metadata or {}

    cab = [
        "# %s" % caminho.stem,
        "",
        "> **Convertido de** `%s` — %d pagina(s), %.1f KB." % (caminho.name, total, tam),
        "> **Perfil:** %s%s | **PyMuPDF** %s | **conversao** %s"
        % (cfg.rotulo,
           " (detectado automaticamente)" if res.perfil_detectado else "",
           fitz.VersionBind, time.strftime("%Y-%m-%d %H:%M")),
    ]
    if (ini, fim) != (1, total):
        cab.append("> **Intervalo convertido:** p. %d a %d (de %d)." % (ini, fim, total))
    if meta.get("title"):
        cab.append("> **Titulo no PDF:** %s" % meta["title"])
    if meta.get("author"):
        cab.append("> **Autor no PDF:** %s" % meta["author"])

    cab += [
        ">",
        "> **Medicao da conversao** (perda de PDF->MD e' silenciosa; confira antes de destilar):",
        "> - Caracteres extraidos: **%d** (media de %.0f por pagina)." % (res.chars, res.media_chars),
        "> - Texto nativo: %d car. | via OCR: %d car. em %d pagina(s)."
        % (res.chars_nativos, res.chars_ocr, res.paginas_ocr),
    ]
    if res.imagens:
        cab.append("> - Imagens extraidas: **%d** em `%s/`."
                   % (res.imagens, (res.pasta_imagens or Path("")).name))
    if res.rodapes_removidos:
        cab.append("> - Linhas de rodape do PJe removidas: %d (assinatura/URL/numero do documento)."
                   % res.rodapes_removidos)
    if res.aviso_estrutura:
        cab.append("> - **Analise de estrutura indisponivel** (%s) — o texto saiu sem "
                   "titulos, negrito e tabelas em Markdown. O CONTEUDO esta completo; "
                   "so a formatacao e' mais crua." % res.aviso_estrutura)
    if res.controles_removidos:
        cab.append("> - Caracteres de controle (incl. bytes NUL) removidos: %d — "
                   "sem isso o `grep` trata este arquivo como binario e suprime o conteudo."
                   % res.controles_removidos)
    if res.paginas_carimbo:
        cab.append("> - Paginas que chegaram so com carimbo do PJe sobre digitalizacao: %d "
                   "(a contagem bruta de caracteres nao as denuncia)." % res.paginas_carimbo)
    if res.paginas_ilegiveis:
        cab.append("> - **ATENCAO: %d pagina(s) tem IMAGEM QUE NAO FOI LIDA** — %s."
                   % (len(res.paginas_ilegiveis), _amostra(res.paginas_ilegiveis)))
        cab.append(">   Elas contem conteudo visual que nenhuma passagem conseguiu "
                   "transcrever. NAO afirme nada sobre o que esta nelas: o texto "
                   "presente e' so o carimbo. Rode com OCR ligado e DPI maior.")
    vazias_so = [n for n in res.paginas_vazias if n not in set(res.paginas_ilegiveis)]
    if vazias_so:
        cab.append("> - %d pagina(s) sem texto algum (e sem imagem): %s — provavelmente "
                   "folhas em branco." % (len(vazias_so), _amostra(vazias_so)))
    if not res.paginas_ilegiveis and not vazias_so:
        cab.append("> - Nenhuma pagina ficou por ler (medido DESCONTANDO o carimbo).")
    cab.append(">")
    cab.append("> Paginacao preservada em `## [p. N]` — cada trecho e' conferivel "
               "contra a pagina do PDF original, que nao foi alterado.")
    cab.append("")

    corpo: list[str] = []

    # Sumario a partir dos bookmarks do PDF (perfil livro)
    if cfg.sumario_toc:
        try:
            toc = doc.get_toc() or []
        except Exception:
            toc = []
        if toc:
            corpo += ["## Sumario (bookmarks do PDF)", ""]
            for nivel, titulo, pag in toc:
                corpo.append("%s- %s — [p. %d]" % ("  " * max(nivel - 1, 0), titulo.strip(), pag))
            corpo += ["", "---", ""]

    # Indice dos documentos dos autos (perfil PJe)
    if cfg.indice_pje and res.docs_pje:
        corpo += ["## Documentos identificados nos autos", "",
                  "| Documento (Num./Id.) | Paginas do PDF |", "|---|---|"]
        for ident, a, b in res.docs_pje:
            corpo.append("| `%s` | p. %d–%d |" % (ident, a, b))
        corpo += ["",
                  "> Identificacao lida do proprio carimbo das paginas; confira contra "
                  "o indice oficial dos autos antes de citar.",
                  "", "---", ""]

    doc_anterior = None
    for p in paginas:
        if cfg.indice_pje and p.doc_pje and p.doc_pje != doc_anterior:
            corpo += ["", "### Documento `%s`" % p.doc_pje, ""]
            doc_anterior = p.doc_pje

        marca = "## [p. %d]" % p.numero
        if p.ocr:
            marca += "  `OCR`"
        if p.ilegivel:
            marca += "  `IMAGEM NAO LIDA`"
        corpo += [marca, ""]
        if p.ilegivel:
            corpo += ["> **Esta pagina tem imagem que nao foi transcrita.** O texto "
                      "abaixo e' apenas o carimbo — nao representa o conteudo da "
                      "pagina. Consulte o PDF original.", ""]
        corpo.append(p.texto if p.texto else "_[pagina sem texto extraivel]_")
        for img in p.imagens:
            corpo += ["", "![Figura da p. %d](%s)" % (p.numero, img.replace(" ", "%20"))]
        corpo.append("")

    return "\n".join(cab) + "\n" + "\n".join(corpo).rstrip() + "\n"


# ==========================================================================
# Lote
# ==========================================================================
def converter_lote(
    arquivos,
    destino=None,
    perfil="auto",
    sobrescritas=None,
    intervalo=None,
    escrever=True,
    progresso=None,
    progresso_arquivo=None,
    cancelar=None,
) -> list[Resultado]:
    """Converte varios PDFs. `progresso_arquivo(i, n, Path)` antes de cada um."""
    arquivos = [Path(a) for a in arquivos]
    resultados: list[Resultado] = []
    for i, pdf in enumerate(arquivos, start=1):
        if cancelar is not None and cancelar.is_set():
            break
        if progresso_arquivo:
            progresso_arquivo(i, len(arquivos), pdf)
        if not pdf.is_file():
            r = Resultado(origem=pdf, erro="arquivo nao encontrado")
            resultados.append(r)
            continue
        resultados.append(
            converter(pdf, destino=destino, perfil=perfil,
                      sobrescritas=sobrescritas, intervalo=intervalo,
                      escrever=escrever, progresso=progresso, cancelar=cancelar)
        )
    return resultados


def coletar_pdfs(caminhos, recursivo: bool = True) -> list[Path]:
    """Expande arquivos e pastas numa lista de PDFs, sem repetir."""
    achados: list[Path] = []
    for c in caminhos:
        p = Path(c)
        if p.is_dir():
            padrao = "**/*.pdf" if recursivo else "*.pdf"
            achados += sorted(x for x in p.glob(padrao) if x.is_file())
        elif p.suffix.lower() == ".pdf" and p.is_file():
            achados.append(p)
    vistos, saida = set(), []
    for p in achados:
        chave = str(p.resolve()).lower()
        if chave not in vistos:
            vistos.add(chave)
            saida.append(p)
    return saida
