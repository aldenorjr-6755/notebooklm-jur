#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Linha de comando do pdf2md.

    python -m pdf2md ARQUIVO.pdf
    python -m pdf2md PASTA/ -o saida/ --perfil pje
    python -m pdf2md laudo.pdf --perfil laudo --imagens
    python -m pdf2md autos.pdf --check          # so mede, nao escreve
    python -m pdf2md --diagnostico

Codigo de saida:
    0  tudo convertido, sem pagina vazia
    1  houve erro em algum arquivo
    2  cancelado
    3  sobrou pagina sem texto extraivel (rode com --ocr sempre / mais DPI)
"""
from __future__ import annotations

import argparse
import sys

from . import ambiente
from .nucleo import coletar_pdfs, converter, detectar_perfil
from .perfis import ORDEM, PERFIS, obter


def _barra(feito: int, total: int, largura: int = 28) -> str:
    if not total:
        return ""
    cheio = int(largura * feito / total)
    return "[%s%s] %3d%%" % ("#" * cheio, "." * (largura - cheio), 100 * feito / total)


def _console_tolerante() -> None:
    """Impede que um acento derrube a execucao.

    O console do Windows abre em cp1252, que nao representa travessao nem
    varios caracteres que aparecem em nome de arquivo e em texto de processo.
    Sem isto, um `print` de nome acentuado levanta UnicodeEncodeError e mata a
    conversao inteira — perder o trabalho por causa de um caractere no relatorio
    seria absurdo.
    """
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def montar_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pdf2md",
        description="Converte PDF em Markdown paginado (`## [p. N]`), com OCR "
                    "seletivo, extracao de imagens e medicao da perda.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Perfis:\n" + "\n".join(
            "  %-9s %s" % (n, PERFIS[n].descricao) for n in ORDEM),
    )
    ap.add_argument("entradas", nargs="*",
                    help="PDFs e/ou pastas com PDFs")
    ap.add_argument("-o", "--out", default=None,
                    help="pasta de saida (padrao: ao lado do original)")
    ap.add_argument("-p", "--perfil", default="auto", choices=ORDEM,
                    help="perfil de conversao (padrao: auto)")
    ap.add_argument("--ocr", default=None, choices=["auto", "sempre", "nunca"],
                    help="politica de OCR (sobrescreve a do perfil)")
    ap.add_argument("--idioma", default=None,
                    help="idioma(s) do Tesseract, ex.: por, por+eng")
    ap.add_argument("--dpi", type=int, default=None,
                    help="resolucao de renderizacao para OCR (padrao 300)")
    ap.add_argument("--preproc", action="store_true", default=None,
                    help="binariza a imagem antes do OCR (ajuda em scan ruim)")
    ap.add_argument("--imagens", action="store_true", default=None,
                    help="extrai as figuras para <nome>_imagens/")
    ap.add_argument("--sem-imagens", dest="imagens", action="store_false",
                    help="nao extrai figuras")
    ap.add_argument("--manter-mobiliario", dest="mobiliario",
                    action="store_false", default=None,
                    help="mantem timbre/brasao e QR do rodape como figura "
                         "(por padrao sao descartados)")
    ap.add_argument("--rapido", dest="estruturado", action="store_false", default=None,
                    help="pula a analise de estrutura (mais rapido, MD mais cru)")
    ap.add_argument("--limpar-rodape", action="store_true", default=None,
                    help="remove o boilerplate de assinatura do PJe")
    ap.add_argument("--paginas", default=None, metavar="INI-FIM",
                    help="converter apenas um intervalo, ex.: 1-50")
    ap.add_argument("-r", "--recursivo", action="store_true",
                    help="ao receber pasta, desce nas subpastas")
    ap.add_argument("--check", action="store_true",
                    help="so mede e relata; nao escreve o .md")
    ap.add_argument("-q", "--quieto", action="store_true",
                    help="sem barra de progresso por pagina")
    ap.add_argument("--diagnostico", action="store_true",
                    help="mostra o estado das dependencias e sai")
    ap.add_argument("--gui", action="store_true",
                    help="abre a interface grafica")
    ap.add_argument("--autoteste", action="store_true",
                    help="verifica o proprio pacote (monta a janela sem exibi-la "
                         "e confere as dependencias); usado apos empacotar")
    return ap


def _teste_carimbo() -> tuple[bool, str]:
    """Reproduz o defeito real e confere que ele nao voltou.

    Monta uma pagina DIGITALIZADA com o carimbo do PJe por cima em texto
    nativo — o arranjo que fazia a medicao por caracteres brutos concluir
    "pagina integra", pular o OCR e declarar a conversao completa. Num
    processo real de 365 paginas isso escondeu 83 delas, entre as quais a ata
    de audiencia.
    """
    import tempfile
    from pathlib import Path

    import fitz

    from .nucleo import converter

    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "carimbo.pdf"
        doc = fitz.open()
        pg = doc.new_page(width=595, height=842)
        # "digitalizacao": texto rasterizado, sem camada de texto
        aux = fitz.open()
        pa = aux.new_page(width=595, height=842)
        pa.insert_text((60, 120), "CERTIDAO DE AUDIENCIA", fontsize=20)
        pa.insert_text((60, 170), "Aos vinte dias do mes de marco compareceram as", fontsize=13)
        pa.insert_text((60, 195), "partes e suas testemunhas para a instrucao.", fontsize=13)
        pix = pa.get_pixmap(dpi=200)
        aux.close()
        pg.insert_image(pg.rect, stream=pix.tobytes("png"))
        # carimbo do PJe: texto NATIVO por cima
        pg.insert_text((40, 24), "Num. 57493199 - Pag. 1", fontsize=8)
        doc.save(str(pdf))
        doc.close()

        r = converter(pdf, destino=tmp, perfil="pje")
        if r.paginas_ocr < 1:
            return False, ("o OCR NAO disparou na pagina carimbada "
                           "(%d caracteres) — o defeito voltou" % r.chars)
        if r.paginas_ilegiveis:
            return False, "pagina continuou ilegivel apos o OCR"

        r2 = converter(pdf, destino=tmp, perfil="pje",
                       sobrescritas={"ocr": "nunca"}, escrever=False)
        if not r2.paginas_ilegiveis:
            return False, ("sem OCR, a pagina carimbada NAO foi acusada como "
                           "nao lida — o relatorio voltaria a mentir")
    return True, ("OCR dispara sobre o carimbo (%d car.) e, sem OCR, a pagina "
                  "e' acusada como nao lida" % r.chars)


def autoteste() -> int:
    """Confere se o pacote esta completo. Devolve 0 se tudo passou.

    Existe porque um build saiu com a JANELA quebrada e a linha de comando
    intacta: sem montar a janela de fato, o defeito passa despercebido.
    """
    falhas = []

    diag = ambiente.diagnostico()
    print("--- dependencias ---")
    for rotulo, versao in diag["modulos"].items():
        erro = (diag.get("erros_import") or {}).get(rotulo)
        print("  %-14s %s%s" % (rotulo, versao or "AUSENTE",
                                ("  <- %s" % erro) if erro else ""))
    for obrigatorio in ("PyMuPDF", "pymupdf4llm", "Pillow", "NumPy"):
        if not diag["modulos"].get(obrigatorio):
            falhas.append("modulo ausente: %s" % obrigatorio)

    print("--- OCR ---")
    print("  tesseract: %s" % (diag["tesseract"] or "AUSENTE"))
    print("  idiomas  : %s" % (", ".join(diag["idiomas"]) or "nenhum"))
    if not diag["tesseract"]:
        falhas.append("Tesseract nao encontrado")
    elif "por" not in diag["idiomas"]:
        falhas.append("idioma 'por' ausente — OCR em portugues indisponivel")

    print("--- carimbo do PJe sobre digitalizacao ---")
    if not diag["tesseract"]:
        print("  pulado (sem Tesseract)")
    else:
        try:
            ok_carimbo, detalhe = _teste_carimbo()
            print("  %s" % detalhe)
            if not ok_carimbo:
                falhas.append("regressao do carimbo: %s" % detalhe)
        except Exception as exc:
            print("  FALHOU: %s: %s" % (type(exc).__name__, exc))
            falhas.append("teste do carimbo: %s" % exc)

    print("--- janela ---")
    try:
        import tkinter as tk

        from .gui import App

        raiz = tk.Tk()
        raiz.withdraw()          # monta tudo, mas nao exibe
        app = App(raiz)
        for _ in range(3):
            raiz.update()
        app.cb_perfil.current(1)
        app._aplicar_perfil()
        raiz.destroy()
        print("  interface monta e responde: OK")
    except Exception as exc:
        print("  FALHOU: %s: %s" % (type(exc).__name__, exc))
        falhas.append("interface grafica: %s" % exc)

    print()
    if falhas:
        print("AUTOTESTE FALHOU:")
        for f in falhas:
            print("  - %s" % f)
        return 1
    print("AUTOTESTE OK — pacote completo.")
    return 0


def _intervalo(txt: str | None):
    if not txt:
        return None
    partes = txt.replace(":", "-").split("-")
    try:
        ini = int(partes[0])
        fim = int(partes[1]) if len(partes) > 1 and partes[1] else 0
    except (ValueError, IndexError):
        raise SystemExit("intervalo invalido: %r (use por exemplo 1-50)" % txt)
    return (ini, fim)


def main(argv=None) -> int:
    _console_tolerante()
    args = montar_parser().parse_args(argv)

    if args.diagnostico:
        print(ambiente.texto_diagnostico())
        return 0

    if args.autoteste:
        return autoteste()

    if args.gui:
        from .gui import main as gui_main

        return gui_main()

    if not args.entradas:
        montar_parser().print_help()
        return 0

    pdfs = coletar_pdfs(args.entradas, recursivo=args.recursivo)
    if not pdfs:
        print("Nenhum PDF encontrado em: %s" % ", ".join(args.entradas))
        return 1

    # Só o que o usuário passou explicitamente sobrescreve o perfil.
    sobrescritas = {
        k: v for k, v in (
            ("ocr", args.ocr),
            ("ocr_idioma", args.idioma),
            ("ocr_dpi", args.dpi),
            ("ocr_preproc", args.preproc),
            ("extrair_imagens", args.imagens),
            ("img_ignorar_mobiliario", args.mobiliario),
            ("estruturado", args.estruturado),
            ("limpar_rodape", args.limpar_rodape),
        ) if v is not None
    }
    base = obter(args.perfil)
    faixa = _intervalo(args.paginas)
    destino = args.out or None

    ocr_efetivo = sobrescritas.get("ocr", base.ocr)
    if not ambiente.diagnostico()["tesseract"] and ocr_efetivo != "nunca":
        print("AVISO: Tesseract nao encontrado — paginas digitalizadas ficarao vazias.\n")

    print("%d arquivo(s) | perfil: %s | OCR: %s | idioma: %s%s\n"
          % (len(pdfs), base.rotulo, ocr_efetivo,
             sobrescritas.get("ocr_idioma", base.ocr_idioma),
             "  [--check: nada sera gravado]" if args.check else ""))

    houve_erro = False
    houve_vazio = 0
    for i, pdf in enumerate(pdfs, start=1):
        rotulo_perfil = base.nome
        if base.nome == "auto":
            try:
                rotulo_perfil = detectar_perfil(pdf)
            except Exception:
                rotulo_perfil = "?"

        print("[%d/%d] %s  (%s)" % (i, len(pdfs), pdf.name, rotulo_perfil))

        def prog(feito, total, rotulo, _q=args.quieto):
            if _q:
                return
            sys.stdout.write("\r      %s %-16s" % (_barra(feito, total), rotulo))
            sys.stdout.flush()

        r = converter(pdf, destino=destino, perfil=args.perfil,
                      sobrescritas=sobrescritas, intervalo=faixa,
                      escrever=not args.check, progresso=prog)
        if not args.quieto:
            sys.stdout.write("\r" + " " * 60 + "\r")

        print("      " + r.resumo().replace("\n", "\n      "))
        if r.destino:
            print("      -> %s" % r.destino)
        if r.pasta_imagens:
            print("      -> %s/ (%d imagens)" % (r.pasta_imagens, r.imagens))
        print()

        houve_erro |= not r.ok
        houve_vazio += len(r.pendentes)

    if houve_erro:
        print("VEREDICTO: houve falha em pelo menos um arquivo.")
        return 1
    if houve_vazio:
        print("VEREDICTO: %d pagina(s) NAO FORAM LIDAS — conversao INCOMPLETA. "
              "Rode com --ocr sempre e/ou --dpi 400." % houve_vazio)
        return 3
    print("VEREDICTO: conversao completa — nenhuma pagina por ler "
          "(medido descontando o carimbo).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
