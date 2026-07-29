#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
inbox_pdf2md.py — converte em Markdown os PDFs que caem no `00-Inbox` dos
vaults, usando o pdf2md como motor.

O que garante, por decisao de projeto:

  * O PDF ORIGINAL FICA. Nada e' movido, renomeado ou apagado — o `.md` nasce
    ao lado dele, dentro do proprio Inbox.
  * As imagens saem para `<nome>_imagens/` e sao REFERENCIADAS POR PAGINA,
    logo abaixo do respectivo `## [p. N]`, como
    `![Figura da p. 7](<nome>_imagens/p0007_img01.png)`. Como o `.md` e a
    pasta ficam lado a lado, o link resolve no Obsidian sem ajuste.
  * A perda e' MEDIDA e relatada por arquivo (paginas, caracteres, media por
    pagina) — a regra canonica manda conferir antes de destilar.

Uma volta (padrao):
    python inbox_pdf2md.py
    python inbox_pdf2md.py --vault Criminal --vault Familia
    python inbox_pdf2md.py --check          # so mede, nao escreve nada
    python inbox_pdf2md.py --refazer        # reconverte o que ja tem .md

Vigilancia continua (watchdog nas nove pastas):
    python inbox_pdf2md.py --watch

Codigo de saida (mesmo contrato do pdf2md):
    0  tudo convertido, nenhuma pagina por ler
    1  houve erro em algum arquivo
    3  sobrou pagina sem texto extraivel -> e' PDF-imagem, precisa de OCR
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

RAIZ = Path(r"C:\Users\alden\.notebooklm")
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from pdf2md import ambiente  # noqa: E402  (configura Tesseract/Ghostscript)
from pdf2md.nucleo import coletar_pdfs, converter_lote  # noqa: E402

# ---------------------------------------------------------------------------
# Onde ficam os cofres
# ---------------------------------------------------------------------------
VAULTS = Path(r"C:\Users\alden\OneDrive\0-Obsidian")
INBOX = "00-Inbox"
LOG_FILE = RAIZ / "inbox_pdf2md.log"

# Ficheiro ainda em transito (download do navegador, copia em andamento).
IGNORAR_SUFIXO = (".crdownload", ".part", ".partial", ".tmp", ".opdownload")

# Atributos NTFS de arquivo do OneDrive que ainda NAO desceu para o disco.
# Abrir um deles dispara download silencioso e pode travar por minutos — a
# escolha aqui e' pular e AVISAR, nao forcar a hidratacao pelas costas.
FILE_ATTRIBUTE_OFFLINE = 0x1000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
NA_NUVEM = (FILE_ATTRIBUTE_OFFLINE
            | FILE_ATTRIBUTE_RECALL_ON_OPEN
            | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)

ESTABILIDADE_LEITURAS = 3     # medicoes de tamanho iguais para considerar pronto
ESTABILIDADE_INTERVALO = 2.0  # segundos entre elas (OneDrive sincroniza em ondas)
ESPERA_TETO = 180             # segundos

log = logging.getLogger("inbox_pdf2md")


def montar_log(verboso: bool) -> None:
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if verboso and sys.stderr is not None:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(sh)


# ---------------------------------------------------------------------------
# Descoberta das pastas
# ---------------------------------------------------------------------------
def descobrir_inboxes(filtro: list[str] | None = None) -> list[tuple[str, Path]]:
    """Todos os `<Vault>/00-Inbox` existentes, em ordem alfabetica.

    Descobre por varredura em vez de lista fixa: quando nascer o decimo cofre
    ele entra sozinho, e um cofre renomeado nao vira entrada morta.
    """
    if not VAULTS.is_dir():
        log.error("Pasta dos vaults nao encontrada: %s", VAULTS)
        return []
    achados: list[tuple[str, Path]] = []
    for vault in sorted(p for p in VAULTS.iterdir() if p.is_dir()):
        inbox = vault / INBOX
        if not inbox.is_dir():
            continue
        if filtro and vault.name.lower() not in {f.lower() for f in filtro}:
            continue
        achados.append((vault.name, inbox))
    return achados


# ---------------------------------------------------------------------------
# Triagem de cada PDF
# ---------------------------------------------------------------------------
def esta_na_nuvem(pdf: Path) -> bool:
    try:
        attrs = getattr(pdf.stat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attrs & NA_NUVEM)


def esperar_estabilizar(pdf: Path) -> bool:
    """Espera o arquivo parar de crescer antes de abrir.

    Vale para download em curso e para a sincronizacao do OneDrive, que
    materializa o arquivo em partes. Converter no meio disso produz `.md`
    truncado — e truncado em silencio, que e' o pior modo de falhar.
    """
    ultimo, iguais = -1, 0
    limite = int(ESPERA_TETO / ESTABILIDADE_INTERVALO)
    for _ in range(limite):
        try:
            tam = pdf.stat().st_size
        except OSError:
            return False
        if tam == ultimo and tam > 0:
            iguais += 1
            if iguais >= ESTABILIDADE_LEITURAS:
                return True
        else:
            iguais = 0
            ultimo = tam
        time.sleep(ESTABILIDADE_INTERVALO)
    log.warning("Desisti de esperar estabilizar: %s", pdf.name)
    return False


def ja_convertido(pdf: Path) -> bool:
    md = pdf.with_suffix(".md")
    if not md.is_file():
        return False
    try:
        return md.stat().st_mtime >= pdf.stat().st_mtime
    except OSError:
        return False


def triar(pdfs: list[Path], refazer: bool) -> tuple[list[Path], list[str]]:
    """Separa o que converter do que pular, com o motivo de cada exclusao."""
    fila: list[Path] = []
    pulados: list[str] = []
    for pdf in pdfs:
        if pdf.name.lower().endswith(IGNORAR_SUFIXO):
            continue
        if "_imagens" in {p.name[-8:] for p in pdf.parents}:
            continue  # nao reprocessa nada dentro da pasta de figuras
        if esta_na_nuvem(pdf):
            pulados.append("%s — so na nuvem (OneDrive nao baixou)" % pdf.name)
            continue
        if not refazer and ja_convertido(pdf):
            continue
        fila.append(pdf)
    return fila, pulados


# ---------------------------------------------------------------------------
# Conversao
# ---------------------------------------------------------------------------
def converter_pasta(nome: str, inbox: Path, args) -> tuple[int, int, int]:
    """Converte os PDFs de um Inbox. Devolve (convertidos, erros, com_pendencia)."""
    pdfs = coletar_pdfs([inbox], recursivo=True)
    fila, pulados = triar(pdfs, args.refazer)

    for motivo in pulados:
        log.warning("  PULADO  %s", motivo)

    if not fila:
        log.info("%-16s nada a converter (%d PDF na pasta)", nome, len(pdfs))
        return 0, 0, 0

    log.info("%-16s %d PDF a converter", nome, len(fila))

    prontos = [p for p in fila if esperar_estabilizar(p)]

    resultados = converter_lote(
        prontos,
        destino=None,                 # `.md` e `<nome>_imagens/` ao lado do PDF
        perfil=args.perfil,
        sobrescritas={
            # As figuras sao o ponto do pedido: sempre extrair e sempre
            # referenciar por pagina, qualquer que seja o perfil detectado.
            "extrair_imagens": True,
            "ocr": args.ocr,
            "ocr_idioma": args.idioma,
        },
        escrever=not args.check,
        progresso_arquivo=lambda i, n, p: log.info("  [%d/%d] %s", i, n, p.name),
    )

    convertidos = erros = pendencia = 0
    for r in resultados:
        if r.erro:
            erros += 1
            log.error("  ERRO  %s -> %s", r.origem.name, r.erro)
            continue
        convertidos += 1
        log.info("  %s", r.resumo())
        if r.imagens:
            log.info("       %d figura(s) em %s/", r.imagens,
                     (r.pasta_imagens or Path("")).name)
        if r.precisa_ocr:
            pendencia += 1
            log.warning("       PENDENTE: pagina(s) sem texto -> %s",
                        _amostra(r.pendentes))
    return convertidos, erros, pendencia


def _amostra(nums: list[int], teto: int = 12) -> str:
    if len(nums) <= teto:
        return ", ".join(str(n) for n in nums)
    return "%s ... (+%d)" % (", ".join(str(n) for n in nums[:teto]), len(nums) - teto)


def varredura(args) -> int:
    inboxes = descobrir_inboxes(args.vault)
    if not inboxes:
        log.error("Nenhum 00-Inbox encontrado%s.",
                  " para o filtro pedido" if args.vault else "")
        return 1

    log.info("=" * 72)
    log.info("Varredura de %d Inbox%s%s", len(inboxes),
             "" if len(inboxes) == 1 else "es",
             "  [--check: nada sera escrito]" if args.check else "")

    tot_conv = tot_err = tot_pend = 0
    for nome, inbox in inboxes:
        c, e, p = converter_pasta(nome, inbox, args)
        tot_conv, tot_err, tot_pend = tot_conv + c, tot_err + e, tot_pend + p

    log.info("-" * 72)
    log.info("TOTAL: %d convertido(s) | %d erro(s) | %d com pagina por ler",
             tot_conv, tot_err, tot_pend)
    if tot_pend:
        log.warning("Ha PDF-imagem na fila. Reconverta com --ocr sempre, ou use "
                    "a skill pdf-ocr-to-markdown.")
    if tot_err:
        return 1
    if tot_pend:
        return 3
    return 0


# ---------------------------------------------------------------------------
# Vigilancia continua
# ---------------------------------------------------------------------------
def vigiar(args) -> int:
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        log.error("watchdog nao instalado. Rode: python -m pip install watchdog")
        return 1

    inboxes = descobrir_inboxes(args.vault)
    if not inboxes:
        log.error("Nenhum 00-Inbox para vigiar.")
        return 1

    class Gatilho(FileSystemEventHandler):
        def __init__(self, nome: str, inbox: Path) -> None:
            self.nome, self.inbox = nome, inbox
            self.em_curso: set[str] = set()

        def _tratar(self, caminho: str) -> None:
            pdf = Path(caminho)
            if pdf.suffix.lower() != ".pdf" or not pdf.is_file():
                return
            chave = str(pdf).lower()
            if chave in self.em_curso:
                return
            # O OneDrive emite varios eventos pelo mesmo arquivo enquanto
            # sincroniza; sem esta trava o mesmo PDF seria convertido em
            # paralelo consigo mesmo.
            self.em_curso.add(chave)
            try:
                fila, pulados = triar([pdf], args.refazer)
                for motivo in pulados:
                    log.warning("  PULADO  %s", motivo)
                if not fila or not esperar_estabilizar(pdf):
                    return
                log.info("%-16s novo: %s", self.nome, pdf.name)
                for r in converter_lote(
                    fila, destino=None, perfil=args.perfil,
                    sobrescritas={"extrair_imagens": True,
                                  "ocr": args.ocr,
                                  "ocr_idioma": args.idioma},
                    escrever=not args.check,
                ):
                    if r.erro:
                        log.error("  ERRO  %s -> %s", r.origem.name, r.erro)
                    else:
                        log.info("  %s", r.resumo())
                        if r.precisa_ocr:
                            log.warning("       PENDENTE: pagina(s) sem texto -> %s",
                                        _amostra(r.pendentes))
            finally:
                self.em_curso.discard(chave)

        def on_created(self, event):
            if not event.is_directory:
                self._tratar(event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                self._tratar(event.dest_path)

    # Varre ANTES de vigiar: o que caiu no Inbox com o vigia desligado (ou
    # entre o logoff e o login) nunca geraria evento e ficaria por converter
    # para sempre. Num autostart isso e' a diferenca entre a automacao valer
    # e a automacao mentir.
    if not args.sem_varredura_inicial:
        log.info("Varredura inicial antes de vigiar.")
        varredura(args)

    obs = Observer()
    for nome, inbox in inboxes:
        obs.schedule(Gatilho(nome, inbox), str(inbox), recursive=True)
        log.info("Vigiando %-16s %s", nome, inbox)
    obs.start()
    log.info("Watchdog ativo em %d pasta(s). Ctrl+C para parar.", len(inboxes))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Encerrando a vigilancia.")
    finally:
        obs.stop()
        obs.join()
    return 0


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="inbox_pdf2md",
        description="Converte em Markdown paginado os PDFs dos 00-Inbox dos "
                    "vaults, preservando o PDF e referenciando as figuras "
                    "por pagina.",
    )
    ap.add_argument("--vault", action="append", default=None, metavar="NOME",
                    help="restringe a um cofre (repetivel); padrao: todos")
    ap.add_argument("--watch", action="store_true",
                    help="vigia as pastas em vez de fazer uma volta so")
    ap.add_argument("--sem-varredura-inicial", action="store_true",
                    help="com --watch, nao converte o que ja estava na pasta")
    ap.add_argument("--check", action="store_true",
                    help="so mede a perda; nao escreve .md nem imagens")
    ap.add_argument("--refazer", action="store_true",
                    help="reconverte mesmo que ja exista .md atualizado")
    ap.add_argument("-p", "--perfil", default="auto",
                    help="perfil do pdf2md (auto|pje|livro|decisao|laudo)")
    ap.add_argument("--ocr", default="auto", choices=["auto", "sempre", "nunca"],
                    help="politica de OCR (padrao: auto)")
    ap.add_argument("--idioma", default="por",
                    help="idioma(s) do Tesseract (padrao: por)")
    ap.add_argument("-q", "--quieto", action="store_true",
                    help="so grava no log, sem imprimir no console")
    ap.add_argument("--listar", action="store_true",
                    help="mostra as pastas que seriam processadas e sai")
    args = ap.parse_args(argv)

    montar_log(verboso=not args.quieto)

    if args.listar:
        for nome, inbox in descobrir_inboxes(args.vault):
            pdfs = coletar_pdfs([inbox], recursivo=True)
            print("%-16s %-58s %d PDF" % (nome, str(inbox), len(pdfs)))
        return 0

    # Prepara PATH/TESSDATA e denuncia o que falta — OCR indisponivel muda o
    # resultado em silencio (pagina digitalizada sai vazia), entao tem de ser
    # dito antes, e nao descoberto depois no `.md`.
    diag = ambiente.diagnostico()
    if args.ocr != "nunca":
        if not diag.get("tesseract"):
            log.warning("Tesseract nao localizado — PDF-imagem sairá sem texto.")
        elif args.idioma.split("+")[0] not in (diag.get("idiomas") or []):
            log.warning("Idioma '%s' ausente no tessdata (disponiveis: %s).",
                        args.idioma, ", ".join(diag.get("idiomas") or []) or "nenhum")

    return vigiar(args) if args.watch else varredura(args)


if __name__ == "__main__":
    sys.exit(main())
