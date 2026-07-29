#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Perfis de conversao por tipo de documento.

Cada tipo de PDF que passa por aqui tem um comportamento otimo diferente:
o processo do PJe e' enorme, misto (peticoes com texto + digitalizacoes) e
poluido por rodape de assinatura; o livro tem sumario e hierarquia de
titulos; o laudo pericial vale pelas imagens.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass
class Perfil:
    """Configuracao de conversao. Todos os campos sao sobrescreviveis."""

    nome: str
    rotulo: str
    descricao: str

    # --- extracao de texto -------------------------------------------------
    estruturado: bool = True
    """Usa pymupdf4llm (titulos, negrito, tabelas em Markdown). Mais lento.
    Desligado = get_text puro do PyMuPDF, varias vezes mais rapido."""

    # --- OCR ---------------------------------------------------------------
    ocr: str = "auto"          # auto | sempre | nunca
    ocr_dpi: int = 300
    ocr_idioma: str = "por"
    ocr_preproc: bool = False  # binarizacao Otsu antes do OCR
    ocr_config: str = ""
    """Config extra do Tesseract. Vazio = segmentacao automatica (psm 3), que
    lida melhor com pagina de layout desconhecido. O `--psm 6` so entra no
    perfil PJe, onde foi comprovado em autos reais; generalizar a partir de um
    unico tipo de documento arriscaria piorar livro em colunas."""

    # --- imagens -----------------------------------------------------------
    extrair_imagens: bool = False
    img_min_px: int = 120      # ignora icone/logo abaixo disso
    img_dedup: bool = True     # nao repete a mesma imagem em varias paginas

    # --- limpeza / estrutura ----------------------------------------------
    limpar_rodape: bool = False
    """Remove o boilerplate do PJe (assinatura eletronica, URL de validacao,
    numero do documento) que se repete em toda pagina."""
    indice_pje: bool = False   # detecta os documentos do processo e indexa
    sumario_toc: bool = False  # transcreve os bookmarks do PDF como sumario

    extras: dict = field(default_factory=dict)

    def com(self, **kw) -> "Perfil":
        """Copia o perfil trocando campos (nao muta o original)."""
        validos = {k: v for k, v in kw.items() if v is not None}
        return replace(self, **validos)


PERFIS: dict[str, Perfil] = {
    # O perfil "auto" e' um DESPACHANTE: ele nao converte com os proprios
    # campos, delega para o perfil detectado em cada arquivo. Os valores
    # abaixo servem so como referencia visual na interface.
    "auto": Perfil(
        nome="auto",
        rotulo="Automatico",
        descricao=(
            "Inspeciona cada PDF e escolhe o perfil sozinho: rodape do PJe -> PJe; "
            "muitas imagens grandes -> Laudo; sumario/bookmarks e muitas paginas "
            "-> Livro; caso contrario -> Decisao."
        ),
        estruturado=True,
        ocr="auto",
        extrair_imagens=True,
    ),
    "pje": Perfil(
        nome="pje",
        rotulo="Processo PJe",
        descricao=(
            "Autos digitais: paginacao fiel, OCR so nas paginas digitalizadas, "
            "remocao do rodape de assinatura eletronica e indice dos documentos "
            "do processo (Num. / Id.)."
        ),
        estruturado=False,      # autos gigantes: velocidade importa mais
        ocr="auto",
        ocr_preproc=True,
        ocr_config="--oem 1 --psm 6",   # validado em autos digitalizados reais
        extrair_imagens=False,
        limpar_rodape=True,
        indice_pje=True,
    ),
    "livro": Perfil(
        nome="livro",
        rotulo="Livro / doutrina",
        descricao=(
            "Obra longa com texto nativo: hierarquia de titulos, tabelas, "
            "sumario a partir dos bookmarks do PDF e paginacao para citacao."
        ),
        estruturado=True,
        ocr="auto",
        extrair_imagens=False,
        sumario_toc=True,
    ),
    "decisao": Perfil(
        nome="decisao",
        rotulo="Decisao judicial",
        descricao=(
            "Sentenca, acordao, despacho: texto nativo com estrutura preservada "
            "e paginacao. Peca curta, conversao integral."
        ),
        estruturado=True,
        ocr="auto",
        extrair_imagens=False,
    ),
    "laudo": Perfil(
        nome="laudo",
        rotulo="Laudo pericial (com imagens)",
        descricao=(
            "Laudo/relatorio tecnico: extrai as figuras para uma pasta ao lado "
            "e as referencia no ponto exato da pagina, com OCR agressivo nas "
            "paginas digitalizadas."
        ),
        estruturado=True,
        ocr="auto",
        ocr_dpi=400,
        ocr_preproc=True,
        extrair_imagens=True,
        img_min_px=100,
    ),
}

ORDEM = ["auto", "pje", "livro", "decisao", "laudo"]


def obter(nome: str) -> Perfil:
    chave = (nome or "auto").strip().lower()
    if chave not in PERFIS:
        raise KeyError(
            "perfil desconhecido: %r (use um de: %s)" % (nome, ", ".join(ORDEM))
        )
    return PERFIS[chave]
