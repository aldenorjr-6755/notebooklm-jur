#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fatiar_atos.py — fatia autos do PJe (em Markdown) em UM arquivo por ATO PROCESSUAL.

Regra da espec (~/.notebooklm/ESPEC-INTELIGENCIA-JURIDICA-CRIMINAL.md, §3.1.2):
janela de N tokens e' proibida; a fronteira e' o ato. Camadas, nesta ordem:

  1. carimbo do PJe em cada pagina: `Num. <id> - Pág. <n>`  (fronteira primaria).
     Como o OCR corrompe digitos do <id> DENTRO do mesmo documento, a troca de id
     so abre ato novo quando a pagina e' `Pág. 1`, ou quando muda a assinatura
     eletronica (assinante + data + hora), ou quando o id novo nao se parece com o
     anterior. Pagina sem carimbo herda o ato pelo `Número do documento` (nd) ou,
     na falta, pelo ato vizinho.
  2. cabecalho tipologico (DENÚNCIA, DECISÃO, SENTENÇA, CERTIDÃO...) para dar o
     tipo quando o indice da capa nao traz, ou traz tipo generico.
  3. fallback: `INDETERMINADO`, com aviso para revisao ou classificacao por LLM local.

Varios volumes (AUTOS_vol01.md, vol02...) sao UM fluxo: documento que atravessa a
fronteira de volume vira um ato so.

Formatos de entrada aceitos:
  * saida do `pdf2md` perfil PJe: paginas em `## [p. N]`, blocos "### Documento `Num. X`"
  * exportacao com separador de 80 tracos entre paginas (NotebookLM / OCR externo)

Saida (em --saida, padrao <pasta do md>/extracted):
  atos/NNNN_TIPO_ID<id>_pAAA-BBB.md   um por ato, com frontmatter (§2.4 da espec)
  atos.jsonl                          indice dos atos (uma linha por ato)
  indice_pje.json                     tabela "Id. | Data | Documento | Tipo" lida da capa (se houver)
  relatorio_fatiamento.md             contagens, lacunas e o que precisa de revisao

Nunca infere data por heuristica de texto: data vem do carimbo de assinatura ou do
indice da capa; se faltar, fica null.

Uso:
  python fatiar_atos.py AUTOS_vol01.md AUTOS_vol02.md --cnj 0801524-21.2024.8.10.0093
  python fatiar_atos.py autos.md --cnj ... --saida 20-Casos/<CNJ>/extracted --manter-rodape
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path

# --------------------------------------------------------------------------
# Regexes do PJe
# --------------------------------------------------------------------------
RE_CARIMBO = re.compile(r"Num\.\s*(\d{5,})\s*-\s*P[áa]g\.\s*(\d+)", re.I)
RE_ASSINATURA = re.compile(
    r"Assinado\s+eletronicamente\s+por:\s*(.+?)\s*-\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}:\d{2})", re.I)
RE_ND = re.compile(r"N[uú]mero\s+do\s+documento:\s*(\d{10,})", re.I)
RE_PAG_PDF2MD = re.compile(r"^## \[p\. (\d+)\](.*)$", re.M)
RE_DOC_PDF2MD = re.compile(r"^### Documento `Num\.\s*(\d+)[^`]*`", re.M)
RE_SEP_TRACOS = re.compile(r"^-{40,}\s*$", re.M)
RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")

# linhas de rodape que NAO pertencem ao ato (a informacao vai para o frontmatter)
RE_RODAPE = [
    re.compile(r"^.{0,12}Assinado\s+eletronicamente\s+por[:\s].*$", re.I),
    re.compile(r"^.{0,12}https?://pje\S*.*$", re.I),
    re.compile(r"^.{0,20}N[uú]mero\s+do\s+documento\s*:\s*\d+\s*$", re.I),
    re.compile(r"^\s*Num\.\s*\d+\s*-\s*P[áa]g\.\s*\d+\s*$", re.I),
    re.compile(r"^\s*Documento\s+assinado\s+digitalmente.*$", re.I),
    re.compile(r"^\s*C[oó]digo\s+de\s+valida[cç][aã]o\s*:?\s*\S*\s*$", re.I),
]

# --------------------------------------------------------------------------
# Vocabulario fechado de tipos de ato (§3.1.2 da espec) — ordem importa:
# padroes mais especificos antes dos genericos.
# --------------------------------------------------------------------------
TIPOS: list[tuple[str, str]] = [
    # investigacao
    ("AUTO DE PRISAO EM FLAGRANTE", r"AUTO\s+DE\s+PRIS[ÃA]O\s+EM\s+FLAGRANTE"),
    ("AUTO DE EXIBICAO E APREENSAO", r"AUTO\s+DE\s+(EXIBI[ÇC][ÃA]O\s+E\s+)?APREENS[ÃA]O"),
    ("AUTO DE RECONHECIMENTO", r"AUTO\s+DE\s+RECONHECIMENTO"),
    ("AUTO DE INFRACAO", r"AUTO\s+DE\s+INFRA[ÇC][ÃA]O"),
    ("TERMO DE INTERROGATORIO", r"TERMO\s+DE\s+INTERROGAT[ÓO]RIO"),
    ("TERMO DE DECLARACOES", r"TERMO\s+DE\s+DECLARA[ÇC][ÕO]ES"),
    ("BOLETIM DE OCORRENCIA", r"BOLETIM\s+DE\s+OCORR[ÊE]NCIA"),
    ("RELATORIO FINAL IP", r"RELAT[ÓO]RIO\s+(FINAL|DE\s+INQU[ÉE]RITO)"),
    ("RELATORIO DE FISCALIZACAO", r"RELAT[ÓO]RIO\s+DE\s+FISCALIZA[ÇC][ÃA]O"),
    ("INFORMACAO TECNICA", r"INFORMA[ÇC][ÃA]O\s+T[ÉE]CNICA|NOTA\s+T[ÉE]CNICA"),
    ("REPRESENTACAO", r"REPRESENTA[ÇC][ÃA]O\s+(POR|PELA|DA\s+AUTORIDADE)"),
    ("PORTARIA", r"^PORTARIA\b"),
    # pericia
    ("LAUDO", r"^(LAUDO|EXAME)\b|LAUDO\s+(PERICIAL|DE\s+CONSTATA[ÇC][ÃA]O|TOXICOL[ÓO]GICO)|EXAME\s+(DE\s+CORPO\s+DE\s+DELITO|NECROSC[ÓO]PICO)"),
    # acusacao
    ("ADITAMENTO DENUNCIA", r"ADITAMENTO\s+[ÀA]\s+DEN[ÚU]NCIA"),
    ("DENUNCIA", r"^DEN[ÚU]NCIA\b|DEN[ÚU]NCIA\s+OU\s+QUEIXA"),
    ("QUEIXA-CRIME", r"QUEIXA[\s-]CRIME"),
    ("ALEGACOES FINAIS", r"ALEGA[ÇC][ÕO]ES\s+FINAIS|MEMORIAIS"),
    ("CONTRARRAZOES", r"CONTRARRAZ[ÕO]ES"),
    ("PARECER MP", r"^PARECER\b"),
    # defesa
    ("RESPOSTA A ACUSACAO", r"RESPOSTA\s+[ÀA]\s+ACUSA[ÇC][ÃA]O|DEFESA\s+PR[ÉE]VIA"),
    ("RAZOES DE APELACAO", r"RAZ[ÕO]ES\s+(DE|DO)\s+(RECURSO\s+DE\s+)?APELA[ÇC][ÃA]O"),
    ("APELACAO", r"^(RECURSO\s+DE\s+)?APELA[ÇC][ÃA]O\b"),
    ("HABEAS CORPUS", r"HABEAS\s+CORPUS"),
    ("PEDIDO DE LIBERDADE", r"PEDIDO\s+DE\s+(LIBERDADE|REVOGA[ÇC][ÃA]O|RELAXAMENTO)|REVOGA[ÇC][ÃA]O\s+DA\s+PRIS[ÃA]O"),
    ("PROCURACAO", r"^PROCURA[ÇC][ÃA]O\b"),
    ("PETICAO", r"^PETI[ÇC][ÃA]O\b|CIENTE\s+MP|^REQUERIMENTO\b"),
    # juizo
    ("SENTENCA", r"^SENTEN[ÇC]A\b"),
    ("ACORDAO", r"^AC[ÓO]RD[ÃA]O\b"),
    ("PRONUNCIA", r"^PRON[ÚU]NCIA\b|DECIS[ÃA]O\s+DE\s+PRON[ÚU]NCIA"),
    ("AUDIENCIA DE CUSTODIA", r"AUDI[ÊE]NCIA\s+DE\s+CUST[ÓO]DIA"),
    ("TERMO DE AUDIENCIA", r"(TERMO|ATA)\s+DE\s+AUDI[ÊE]NCIA"),
    ("RECEBIMENTO DENUNCIA", r"RECEB(O|IMENTO\s+D[AE])\s+(A\s+)?DEN[ÚU]NCIA"),
    ("DECISAO", r"^DECIS[ÃA]O\b"),
    ("DESPACHO", r"^DESPACHO\b"),
    # cartorio
    ("CERTIDAO DE PUBLICACAO", r"CERTID[ÃA]O\s+DE\s+PUBLICA[ÇC][ÃA]O"),
    ("CERTIDAO DE TRANSITO", r"CERTID[ÃA]O\s+DE\s+TR[ÂA]NSITO"),
    ("CERTIDAO", r"^CERTID[ÃA]O\b|^CERTIFICO\b"),
    ("CARTA PRECATORIA", r"CARTA\s+PRECAT[ÓO]RIA"),
    ("MANDADO", r"^MANDADO\b"),
    ("OFICIO", r"^OF[ÍI]CIO\b"),
    ("INTIMACAO", r"^INTIMA[ÇC][ÃA]O\b"),
    ("GUIA DE EXECUCAO", r"GUIA\s+DE\s+(EXECU[ÇC][ÃA]O|RECOLHIMENTO)"),
    ("ATESTADO DE PENA", r"ATESTADO\s+DE\s+PENA"),
    ("COMUNICACAO ELETRONICA", r"WhatsApp|web\.whatsapp|E-?mail\b.*(De|Para):|Mensagem\s+encaminhada"),
    ("ANEXO PROCEDIMENTO EXTERNO", r"^Procedimento\s+[\d.]+/\d{4}-\d{2},\s*Documento\s+\d+"),
    ("TERMO", r"^TERMO\b"),
    ("PROTOCOLO", r"^PROTOCOLO\b"),
    ("DOCUMENTO DIVERSO", r"DOCUMENTO\s+DIVERSO"),
]
TIPOS_RX = [(nome, re.compile(rx, re.I | re.M)) for nome, rx in TIPOS]
TIPOS_GENERICOS = {"DOCUMENTO DIVERSO", "DOCUMENTOS DIVERSOS", "TERMO", "PETICAO", "PETICAO INICIAL",
                   "PETICAO CRIMINAL", "PROTOCOLO", "DILIGENCIA", "ANEXO PROCEDIMENTO EXTERNO"}

# tipos como aparecem na coluna "Tipo" do indice da capa do PJe (mais longos primeiro)
TIPOS_INDICE = sorted([
    "Denúncia ou Queixa", "Documento Diverso", "Carta Precatória", "Alegações Finais",
    "Resposta à Acusação", "Termo de Audiência", "Ata de Audiência", "Certidão", "Despacho",
    "Decisão", "Sentença", "Acórdão", "Intimação", "Ofício", "Petição", "Protocolo", "Termo",
    "Mandado", "Laudo", "Parecer", "Apelação", "Contrarrazões", "Recurso", "Habeas Corpus",
    "Auto de Prisão em Flagrante", "Relatório", "Portaria", "Citação", "Notificação", "Procuração",
    "Petição Inicial", "Petição Criminal", "Diligência", "Ato Ordinatório", "Documentos Diversos",
    "Certidão de cumprimento de Carta", "Sentença Criminal", "Decisão Interlocutória",
], key=len, reverse=True)
TIPOS_GENERICOS_INDICE = {"Petição Inicial", "Petição Criminal", "Documentos Diversos", "Documento Diverso",
                          "Termo", "Petição", "Protocolo", "Diligência"}


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _slug_tipo(t: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", _sem_acento(t).upper()).strip("-")


def _ids_parecidos(a: str, b: str, minimo: float = 0.70) -> bool:
    """OCR troca/insere digitos; ids do MESMO documento ficam parecidos (>= 70%)."""
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= minimo


# --------------------------------------------------------------------------
# 1) Paginas
# --------------------------------------------------------------------------
@dataclass
class Pagina:
    volume: str
    numero: int                # numero da pagina no arquivo (pdf2md) ou sequencial
    texto: str
    id_pje: str | None = None
    pag_doc: int | None = None # "Pág. N" dentro do documento
    nd: str | None = None      # "Número do documento"
    assinante: str | None = None
    data_assin: str | None = None   # dd/mm/aaaa
    hora_assin: str | None = None
    ocr: bool = False
    doc_pdf2md: str | None = None   # id vindo de "### Documento `Num. X`"
    id_herdado: bool = False        # id preenchido por nd/vizinhanca, nao lido do carimbo

    @property
    def assinatura(self) -> tuple | None:
        if self.data_assin:
            return (self.assinante, self.data_assin, self.hora_assin)
        return None


def paginar(texto: str, volume: str) -> list[Pagina]:
    """Divide o markdown em paginas, aceitando os dois formatos."""
    paginas: list[Pagina] = []
    marcas = list(RE_PAG_PDF2MD.finditer(texto))
    if len(marcas) >= 2:
        doc_atual = None
        for i, m in enumerate(marcas):
            ini = m.end()
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            corpo = texto[ini:fim]
            trecho_antes = texto[(marcas[i - 1].end() if i else 0):m.start()]
            md = RE_DOC_PDF2MD.findall(trecho_antes)
            if md:
                doc_atual = md[-1]
            md2 = RE_DOC_PDF2MD.findall(corpo)
            if md2:
                doc_atual = md2[-1]
                corpo = RE_DOC_PDF2MD.sub("", corpo)
            paginas.append(Pagina(volume=volume, numero=int(m.group(1)), texto=corpo,
                                  ocr="`OCR`" in m.group(2), doc_pdf2md=doc_atual))
    else:
        for i, corpo in enumerate(RE_SEP_TRACOS.split(texto), start=1):
            if corpo.strip():
                paginas.append(Pagina(volume=volume, numero=i, texto=corpo))
    for p in paginas:
        _ler_carimbos(p)
    return paginas


def _ler_carimbos(p: Pagina) -> None:
    ms = RE_CARIMBO.findall(p.texto)
    if ms:
        # o carimbo da propria pagina e' o ULTIMO (rodape); citacoes a outros Num. ficam no corpo
        p.id_pje, pag = ms[-1]
        p.pag_doc = int(pag)
    elif p.doc_pdf2md:
        p.id_pje = p.doc_pdf2md
    ma = RE_ASSINATURA.findall(p.texto)
    if ma:
        p.assinante, p.data_assin, p.hora_assin = ma[-1]
        p.assinante = p.assinante.strip()
    mn = RE_ND.findall(p.texto)
    if mn:
        p.nd = mn[-1]


def preencher_ids_por_nd(paginas: list[Pagina]) -> int:
    """Pagina sem `Num.` mas com `Número do documento` igual ao de uma pagina com
    carimbo recebe o mesmo id (o nd e' a chave do documento no PJe)."""
    nd2id: dict[str, str] = {}
    for p in paginas:
        if p.id_pje and p.nd and not p.id_herdado:
            nd2id.setdefault(p.nd, p.id_pje)
    n = 0
    for p in paginas:
        if p.id_pje is None and p.nd and p.nd in nd2id:
            p.id_pje, p.id_herdado = nd2id[p.nd], True
            n += 1
    return n


# --------------------------------------------------------------------------
# 2) Indice da capa ("Id. | Data da Assinatura | Documento | Tipo")
# --------------------------------------------------------------------------
RE_IDX_LINHA = re.compile(
    r"^\s*(\d{4,6})\s*[\[\|/l]*\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s*[\[\|/l]*\s*(.+?)\s*$")
RE_IDX_SUFIXO = re.compile(r"^\s*(\d{3,5})\b")


def ler_indice_capa(texto: str, origem: str = "") -> dict[str, dict]:
    """Reconstroi id -> {data, hora, documento, tipo} a partir da tabela da capa.

    O OCR da capa quebra o Id em duas linhas (prefixo na linha da data, sufixo na
    linha seguinte). Junta os dois; se nao houver sufixo, guarda so o prefixo com
    flag `parcial`.
    """
    idx: dict[str, dict] = {}
    linhas = texto.split("\n")
    n = len(linhas)
    for i, ln in enumerate(linhas):
        m = RE_IDX_LINHA.match(ln)
        if not m:
            continue
        pref, data, hora, resto = m.groups()
        sufixo = None
        for j in range(i + 1, min(i + 4, n)):
            cand = linhas[j].strip()
            if not cand:
                continue
            if RE_IDX_LINHA.match(cand):
                break
            ms = RE_IDX_SUFIXO.match(cand)
            if ms:
                sufixo = ms.group(1)
            break
        resto = re.sub(r"^[\[\|/l\s]+", "", resto)
        tipo, documento = None, resto
        for t in TIPOS_INDICE:
            if resto.lower().endswith(t.lower()):
                tipo = t
                documento = resto[: -len(t)].strip(" |[]/-") or t
                break
        chave = pref + sufixo if sufixo else pref
        idx[chave] = {"id": chave, "parcial": sufixo is None, "data": data, "hora": hora,
                      "documento": documento, "tipo": tipo, "lido_em": origem}
    return idx


def _casar_indice(id_pje: str | None, variantes: list[str], indice: dict[str, dict]) -> dict | None:
    if not id_pje:
        return None
    for cand in [id_pje] + variantes:
        if cand in indice:
            return indice[cand]
    parciais = [v for k, v in indice.items() if v.get("parcial") and id_pje.startswith(k)]
    if len(parciais) == 1:
        return parciais[0]
    # ultimo recurso: id do indice parecido com o id lido (OCR de um lado ou de outro)
    prox = [v for k, v in indice.items() if not v.get("parcial") and _ids_parecidos(k, id_pje, 0.85)]
    return prox[0] if len(prox) == 1 else None


# --------------------------------------------------------------------------
# 3) Atos
# --------------------------------------------------------------------------
@dataclass
class Ato:
    seq: int
    id_pje: str | None
    id_variantes: list[str]
    tipo: str
    tipo_origem: str            # indice | cabecalho | indice+cabecalho | posicao | indeterminado
    titulo: str | None
    volume_ini: str
    volume_fim: str
    pag_ini: int
    pag_fim: int
    n_paginas: int
    data_juntada: str | None    # ISO
    hora_juntada: str | None
    assinante: str | None
    nd: str | None
    ocr: bool
    carimbo_ausente: bool
    texto: str = field(repr=False, default="")
    hash_sha256: str = ""
    origem_arquivos: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _linhas_uteis(texto: str, max_linhas: int) -> list[str]:
    """Primeiras linhas com conteudo real (pula lixo de OCR de papel timbrado)."""
    out = []
    for l in texto.split("\n"):
        s = l.strip()
        if not s or s.startswith("## [") or len(s) < 4:
            continue
        letras = sum(c.isalpha() for c in s)
        if letras < max(3, len(s) * 0.5):
            continue
        out.append(s)
        if len(out) >= max_linhas:
            break
    return out


def _eh_titulo(l: str) -> bool:
    """Linha curta e majoritariamente em maiusculas: cabecalho de peca, nao prosa."""
    s = l.strip()
    letras = [c for c in s if c.isalpha()]
    if not (4 <= len(s) <= 80) or len(letras) < 4:
        return False
    return sum(c.isupper() for c in letras) / len(letras) >= 0.8


# tipos que podem ser reconhecidos fora de linha-titulo (na prosa inicial), sempre no
# inicio de linha; os demais (ex.: AUTO DE INFRACAO, LAUDO) so valem como titulo, porque
# a prosa de uma denuncia ambiental CITA o auto de infracao sem SER um auto de infracao.
TIPOS_NA_PROSA = {
    "DENUNCIA", "ADITAMENTO DENUNCIA", "QUEIXA-CRIME", "SENTENCA", "ACORDAO", "ALEGACOES FINAIS",
    "RESPOSTA A ACUSACAO", "HABEAS CORPUS", "CARTA PRECATORIA", "CERTIDAO", "DESPACHO", "DECISAO",
    "TERMO DE AUDIENCIA", "RECEBIMENTO DENUNCIA", "COMUNICACAO ELETRONICA", "ANEXO PROCEDIMENTO EXTERNO",
    "RELATORIO DE FISCALIZACAO", "INFORMACAO TECNICA", "PROCURACAO", "INTIMACAO", "MANDADO", "OFICIO",
    "PORTARIA", "PETICAO", "TERMO", "PROTOCOLO",
}
RE_OFERECE_DENUNCIA = re.compile(r"oferec\w*\s+(a\s+presente\s+)?DEN[ÚU]NCIA", re.I)


def classificar_por_cabecalho(texto: str, max_linhas: int = 60) -> tuple[str | None, str | None]:
    """Camada A: linhas-titulo (curtas, maiusculas) contra todo o vocabulario.
    Camada B: prosa das primeiras linhas, so para tipos de TIPOS_NA_PROSA e so em inicio de linha."""
    linhas = _linhas_uteis(texto, max_linhas)
    titulos = [l for l in linhas if _eh_titulo(l)]
    for nome, rx in TIPOS_RX:
        for l in titulos:
            if rx.search(l):
                return nome, l[:120], "titulo"
    prosa = "\n".join(linhas[:30])
    if RE_OFERECE_DENUNCIA.search(prosa):
        return "DENUNCIA", None, "prosa"
    for nome, rx in TIPOS_RX:
        if nome in TIPOS_NA_PROSA and rx.search(prosa):
            return nome, None, "prosa"
    return None, None, None


def _tipo_do_indice(entrada: dict) -> tuple[str | None, str | None]:
    """Tipo a partir da linha do indice da capa: o campo 'documento' (ex.: 'Denúncia MPE (70)')
    e' mais especifico que a coluna 'tipo' (ex.: 'Petição Inicial')."""
    doc = (entrada.get("documento") or "").strip()
    for nome, rx in TIPOS_RX:
        if doc and rx.search(doc) and nome not in TIPOS_GENERICOS:
            return nome, doc
    if entrada.get("tipo"):
        return _slug_tipo(entrada["tipo"]).replace("-", " "), doc or None
    return None, doc or None


def _iso(data_br: str | None) -> str | None:
    """dd/mm/aaaa -> aaaa-mm-dd; data impossivel (OCR: dia 98, mes 13) vira None."""
    if not data_br:
        return None
    try:
        d, m, a = (int(x) for x in data_br.split("/"))
        import datetime
        datetime.date(a, m, d)
    except (ValueError, TypeError):
        return None
    return f"{a:04d}-{m:02d}-{d:02d}"


def _limpar(texto: str, manter_rodape: bool) -> str:
    if manter_rodape:
        return texto.strip()
    saida = [ln for ln in texto.split("\n") if not any(rx.match(ln) for rx in RE_RODAPE)]
    t = "\n".join(saida)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _abre_ato_novo(prev: Pagina | None, p: Pagina) -> bool:
    """Decide se `p` inicia um documento novo em relacao a `prev`."""
    if prev is None:
        return True
    if p.id_pje is None:
        return False                       # sem carimbo: herda
    if prev.id_pje is None:
        return True                        # anterior era capa/sem id
    if p.id_pje == prev.id_pje:
        return False
    # ids diferentes: OCR ou documento novo?
    if p.pag_doc == 1:
        return True                        # `Pág. 1` e' o sinal mais confiavel de documento novo
    if p.assinatura and prev.assinatura and p.assinatura != prev.assinatura:
        return True                        # assinatura mudou: documento novo
    if not _ids_parecidos(p.id_pje, prev.id_pje):
        return True
    return False                           # id parecido, mesma assinatura, nao e' Pág. 1: OCR


def agrupar(paginas: list[Pagina], indice: dict[str, dict], multi_volume: bool,
            manter_rodape: bool) -> list[Ato]:
    atos: list[Ato] = []
    grupo: list[Pagina] = []
    prev: Pagina | None = None
    for p in paginas:
        if grupo and _abre_ato_novo(prev, p):
            atos.append(_montar_ato(len(atos) + 1, grupo, indice, multi_volume, manter_rodape))
            grupo = []
        grupo.append(p)
        if p.id_pje is not None:
            prev = p
        elif prev is None:
            prev = p
    if grupo:
        atos.append(_montar_ato(len(atos) + 1, grupo, indice, multi_volume, manter_rodape))
    return atos


def _moda(valores):
    vals = [v for v in valores if v]
    return Counter(vals).most_common(1)[0][0] if vals else None


def _montar_ato(seq: int, grupo: list[Pagina], indice: dict[str, dict], multi_volume: bool,
                manter_rodape: bool) -> Ato:
    ids_lidos = [p.id_pje for p in grupo if p.id_pje and not p.id_herdado]
    ids_todos = [p.id_pje for p in grupo if p.id_pje]
    id_pje = _moda(ids_lidos) or _moda(ids_todos)
    variantes = sorted({i for i in ids_todos if i != id_pje})

    corpo = []
    for p in grupo:
        marca = f"## [{p.volume} p. {p.numero}]" if multi_volume else f"## [p. {p.numero}]"
        if p.ocr:
            marca += "  `OCR`"
        corpo.append(marca + "\n\n" + _limpar(p.texto, manter_rodape))
    texto = "\n\n".join(corpo).strip()

    data_br = _moda(p.data_assin for p in grupo)
    hora = None
    assinante = None
    for p in grupo:
        if p.data_assin == data_br:
            hora, assinante = p.hora_assin, p.assinante
            break
    nd = _moda(p.nd for p in grupo)
    avisos: list[str] = []
    entrada = _casar_indice(id_pje, variantes, indice)

    tipo, tipo_origem, titulo = None, "indeterminado", None
    if id_pje is None and seq == 1:
        tipo, tipo_origem, titulo = "CAPA INDICE", "posicao", "Capa e indice dos autos"
    if tipo is None and entrada:
        t_idx, tit_idx = _tipo_do_indice(entrada)
        if t_idx:
            tipo, tipo_origem, titulo = t_idx, "indice", tit_idx
    if tipo_origem != "posicao" and (tipo is None or tipo in TIPOS_GENERICOS):
        t2, tit2, camada = classificar_por_cabecalho(texto)
        if t2 and (tipo is None or t2 not in TIPOS_GENERICOS):
            # "cabecalho-titulo" = linha-titulo em maiusculas (forte); "cabecalho-prosa" = achado na
            # prosa inicial (fraco: uma certidao que CITA a resposta a acusacao cai aqui — conferir)
            tipo_origem = f"cabecalho-{camada}" if tipo is None else f"indice+cabecalho-{camada}"
            tipo = t2
            titulo = titulo or tit2
            if camada == "prosa":
                avisos.append("tipo inferido da prosa inicial, nao de linha-titulo: conferir")
    if tipo is None:
        tipo = "INDETERMINADO"
        avisos.append("tipo nao identificado: revisar ou classificar pelo LLM local")

    data = _iso(data_br) if data_br else (_iso(entrada["data"]) if entrada else None)
    if data_br and data is None:
        avisos.append(f"data de assinatura ilegivel no OCR ('{data_br}'): campo deixado nulo")
    if hora is None and entrada and entrada.get("hora"):
        hora = entrada["hora"] + ":00"
    if data is None and id_pje:
        avisos.append("sem data de juntada (nem carimbo de assinatura nem indice)")
    datas = {p.data_assin for p in grupo if p.data_assin}
    if len(datas) > 1:
        avisos.append(f"datas de assinatura divergentes nas paginas: {sorted(datas)} (usada a mais frequente)")
    if variantes:
        avisos.append(f"id lido com variantes de OCR: {variantes} (canonico {id_pje})")
    carimbo_ausente = any(p.id_pje is None or p.id_herdado for p in grupo)
    if carimbo_ausente and id_pje:
        avisos.append("ha pagina sem carimbo dentro do ato (OCR): conferir se e' o mesmo documento")
    if id_pje is None and seq > 1:
        avisos.append("paginas sem carimbo Num. e sem vizinho: indeterminadas")

    ato = Ato(seq=seq, id_pje=id_pje, id_variantes=variantes, tipo=tipo, tipo_origem=tipo_origem,
              titulo=titulo, volume_ini=grupo[0].volume, volume_fim=grupo[-1].volume,
              pag_ini=grupo[0].numero, pag_fim=grupo[-1].numero, n_paginas=len(grupo),
              data_juntada=data, hora_juntada=hora, assinante=assinante, nd=nd,
              ocr=any(p.ocr for p in grupo), carimbo_ausente=carimbo_ausente, texto=texto,
              origem_arquivos=sorted({p.volume for p in grupo}), avisos=avisos)
    ato.hash_sha256 = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    return ato


# --------------------------------------------------------------------------
# 4) Saida
# --------------------------------------------------------------------------
def _yaml(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_yaml(x) for x in v) + "]"
    return '"' + str(v).replace('"', "'") + '"'


def frontmatter(a: Ato, cnj: str | None) -> str:
    campos = [
        ("tipo", "ato_processual"), ("cnj", cnj), ("ato_seq", a.seq), ("ato_tipo", a.tipo),
        ("ato_tipo_origem", a.tipo_origem), ("titulo", a.titulo), ("id_pje", a.id_pje),
        ("id_variantes", a.id_variantes), ("numero_documento", a.nd),
        ("volume_ini", a.volume_ini), ("volume_fim", a.volume_fim),
        ("pag_ini", a.pag_ini), ("pag_fim", a.pag_fim), ("n_paginas", a.n_paginas),
        ("data_juntada", a.data_juntada), ("hora_juntada", a.hora_juntada), ("assinante", a.assinante),
        ("hash_sha256", a.hash_sha256), ("origem_arquivos", a.origem_arquivos), ("ocr", a.ocr),
        ("carimbo_ausente", a.carimbo_ausente),
    ]
    linhas = ["---"] + [f"{k}: {_yaml(v)}" for k, v in campos]
    if a.avisos:
        linhas.append("avisos:")
        linhas += [f"  - {_yaml(x)}" for x in a.avisos]
    linhas.append("---")
    return "\n".join(linhas)


def nome_arquivo(a: Ato) -> str:
    tipo = _slug_tipo(a.tipo)[:28]
    idp = f"_ID{a.id_pje}" if a.id_pje else ""
    return f"{a.seq:04d}_{tipo}{idp}_p{a.pag_ini:03d}-{a.pag_fim:03d}.md"


def escrever(atos: list[Ato], saida: Path, cnj: str | None, indices: dict[str, dict]) -> dict:
    pasta = saida / "atos"
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in pasta.glob("*.md"):
        velho.unlink()
    stats = {"atos": 0, "paginas": 0, "sem_id": 0, "indeterminados": 0, "sem_data": 0,
             "com_variantes": 0, "multi_volume": 0, "tipos": {}, "avisos": 0}
    with io.open(saida / "atos.jsonl", "w", encoding="utf-8", newline="\n") as jsonl:
        for a in atos:
            nome = nome_arquivo(a)
            with io.open(pasta / nome, "w", encoding="utf-8", newline="\n") as f:
                f.write(frontmatter(a, cnj) + "\n\n" + a.texto + "\n")
            reg = {k: v for k, v in asdict(a).items() if k != "texto"}
            reg.update({"cnj": cnj, "arquivo": f"atos/{nome}", "chars": len(a.texto)})
            jsonl.write(json.dumps(reg, ensure_ascii=False) + "\n")
            stats["atos"] += 1
            stats["paginas"] += a.n_paginas
            stats["sem_id"] += a.id_pje is None
            stats["indeterminados"] += a.tipo == "INDETERMINADO"
            stats["sem_data"] += a.data_juntada is None
            stats["com_variantes"] += bool(a.id_variantes)
            stats["multi_volume"] += a.volume_ini != a.volume_fim
            stats["avisos"] += len(a.avisos)
            stats["tipos"][a.tipo] = stats["tipos"].get(a.tipo, 0) + 1
    with io.open(saida / "indice_pje.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(indices, f, ensure_ascii=False, indent=1)
    return stats


def relatorio(stats: dict, atos: list[Ato], indices: dict, cnj: str | None) -> str:
    L = [f"# Relatorio de fatiamento — {cnj or 'sem CNJ'}", "",
         f"- atos: **{stats['atos']}** em {stats['paginas']} paginas",
         f"- atos sem `Num.` (capa/indice ou OCR falho): {stats['sem_id']}",
         f"- tipo INDETERMINADO: {stats['indeterminados']}",
         f"- sem data de juntada: {stats['sem_data']}",
         f"- id com variantes de OCR (unificados): {stats['com_variantes']}",
         f"- atos que atravessam volume: {stats['multi_volume']}",
         f"- avisos: {stats['avisos']}",
         f"- entradas lidas do indice da capa: {len(indices)} "
         f"(parciais: {sum(1 for v in indices.values() if v.get('parcial'))})", "",
         "## Tipos", "", "| tipo | n |", "|---|---|"]
    for t, n in sorted(stats["tipos"].items(), key=lambda x: -x[1]):
        L.append(f"| {t} | {n} |")
    L += ["", "## Atos com aviso", "", "| seq | id | tipo | pags | aviso |", "|---|---|---|---|---|"]
    for a in atos:
        for av in a.avisos:
            L.append(f"| {a.seq} | {a.id_pje or '-'} | {a.tipo} | {a.volume_ini} {a.pag_ini}-{a.volume_fim} {a.pag_fim} | {av} |")
    L += ["", "## Ids do indice da capa sem ato correspondente", "",
          "> Pode ser (a) documento cujo carimbo o OCR destruiu, ou (b) capa de OUTRO processo "
          "embutida nos autos (ex.: carta precatoria devolvida com a capa do juizo deprecado). "
          "A coluna `lido em` diz de qual volume veio a tabela.", ""]
    vistos = {a.id_pje for a in atos if a.id_pje} | {v for a in atos for v in a.id_variantes}
    faltam = [v for k, v in indices.items() if not v.get("parcial") and k not in vistos
              and not any(_ids_parecidos(k, x, 0.85) for x in vistos)]
    if faltam:
        L += ["| id | data | documento | tipo | lido em |", "|---|---|---|---|---|"]
        L += [f"| {v['id']} | {v['data']} | {v['documento']} | {v['tipo'] or '-'} | {v.get('lido_em','')} |"
              for v in faltam]
    else:
        L.append("(nenhum — ou o indice nao foi lido)")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", help=".md dos autos (um por volume, em ordem)")
    ap.add_argument("--cnj", help="numero CNJ; se omitido, tenta ler do texto")
    ap.add_argument("--saida", help="pasta de saida (padrao: <pasta do 1o md>/extracted)")
    ap.add_argument("--manter-rodape", action="store_true", help="nao remove as linhas de carimbo do corpo")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    arquivos = [Path(a) for a in args.arquivos]
    for a in arquivos:
        if not a.is_file():
            print(f"ERRO: nao achei {a}", file=sys.stderr)
            return 2
    saida = Path(args.saida) if args.saida else arquivos[0].parent / "extracted"
    cnj = args.cnj
    indices: dict[str, dict] = {}
    paginas: list[Pagina] = []
    for a in arquivos:
        texto = io.open(a, encoding="utf-8", errors="replace").read()
        if not cnj:
            m = RE_CNJ.search(texto[:5000])
            cnj = m.group(0) if m else None
        idx = ler_indice_capa(texto[:60000], a.stem)
        indices.update(idx)
        ps = paginar(texto, a.stem)
        paginas += ps
        if not args.quiet:
            print(f"{a.name}: {len(ps)} paginas (indice da capa: {len(idx)} entradas)")
    n_nd = preencher_ids_por_nd(paginas)
    atos = agrupar(paginas, indices, multi_volume=len(arquivos) > 1, manter_rodape=args.manter_rodape)
    stats = escrever(atos, saida, cnj, indices)
    rel = relatorio(stats, atos, indices, cnj)
    io.open(saida / "relatorio_fatiamento.md", "w", encoding="utf-8", newline="\n").write(rel)
    if not args.quiet:
        print(f"\nsaida: {saida}  (ids preenchidos por 'Número do documento': {n_nd})")
        print(f"atos={stats['atos']} paginas={stats['paginas']} sem_id={stats['sem_id']} "
              f"indeterminados={stats['indeterminados']} sem_data={stats['sem_data']} "
              f"variantes={stats['com_variantes']} multi_volume={stats['multi_volume']} avisos={stats['avisos']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
