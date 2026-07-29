#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gera o executavel standalone do pdf2md (PyInstaller).

    python -m pdf2md.empacotar                 # pasta com os 2 .exe (recomendado)
    python -m pdf2md.empacotar --onefile       # arquivo unico, parte mais devagar
    python -m pdf2md.empacotar --sem-tesseract # pacote leve, exige Tesseract na maquina
    python -m pdf2md.empacotar --idiomas por,eng

Produz, em `dist/pdf2md/`:
    pdf2md.exe        -> abre a janela (sem console atras)
    pdf2md-cli.exe    -> linha de comando

O Tesseract vai DENTRO do pacote: so o `tesseract.exe`, as DLLs e os idiomas
pedidos. As ferramentas de TREINAMENTO do Tesseract (lstmtraining, text2image
e companhia, ~60 MB de executaveis que o OCR nao usa) ficam de fora.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import ambiente

RAIZ = Path(__file__).resolve().parent
PROJETO = RAIZ.parent

# Executaveis do Tesseract que servem para TREINAR modelo, nao para reconhecer
# texto. Sao ~60 MB que nunca seriam chamados.
EXES_DE_TREINO = {
    "ambiguous_words.exe", "classifier_tester.exe", "cntraining.exe",
    "combine_lang_model.exe", "combine_tessdata.exe", "dawg2wordlist.exe",
    "lstmeval.exe", "lstmtraining.exe", "merge_unicharsets.exe",
    "mftraining.exe", "set_unicharset_properties.exe", "shapeclustering.exe",
    "text2image.exe", "unicharset_extractor.exe", "wordlist2dawg.exe",
}

# Pacotes grandes que o pdf2md nao usa e que o PyInstaller pode arrastar junto.
#
# `onnxruntime` NAO entra nesta lista de proposito: o `pymupdf4llm` importa
# `helpers.document_layout` ja no seu `__init__`, e isso puxa `pymupdf.layout`,
# que precisa do onnxruntime. Excluindo-o, o `import pymupdf4llm` falha DENTRO
# do executavel e a analise de estrutura sai calada — o .exe passaria a gerar
# um Markdown diferente do que o mesmo PDF gera rodando do fonte.
#
# `rapidocr*` continua fora: so serve ao OCR interno do pymupdf4llm, que este
# app desliga (ele ignora o idioma e estraga os acentos do portugues).
EXCLUIR = [
    "cv2", "matplotlib", "scipy", "pandas", "IPython", "jupyter", "notebook",
    "pytest", "setuptools", "pip", "wheel", "tornado", "zmq", "sqlalchemy",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "docutils", "lxml",
    "ocrmypdf", "pikepdf", "watchdog", "fastapi", "starlette", "pydantic",
    "rapidocr", "rapidocr_onnxruntime", "torch", "transformers",
]


def remover_pasta(alvo: Path, tentativas: int = 5) -> bool:
    """Apaga uma pasta insistindo um pouco.

    No Windows, o antivirus costuma manter um handle aberto nos .exe recem
    gerados por alguns segundos, e o `rmtree` falha com "acesso negado". Se
    mesmo assim nao sair, a pasta e' movida para o lado (com sufixo `.antigo`)
    em vez de abortar o empacotamento.
    """
    if not alvo.exists():
        return True
    for i in range(tentativas):
        try:
            shutil.rmtree(alvo)
            return True
        except OSError:
            if i < tentativas - 1:
                time.sleep(1.0 + i)
    reserva = alvo.with_name(alvo.name + ".antigo-%d" % int(time.time()))
    try:
        alvo.rename(reserva)
        print("  ! %s estava em uso; movida para %s" % (alvo.name, reserva.name))
        return True
    except OSError as exc:
        print("  ! nao consegui remover %s: %s" % (alvo, exc))
        return False


def _mb(caminho: Path) -> float:
    if caminho.is_file():
        return caminho.stat().st_size / 1048576
    return sum(f.stat().st_size for f in caminho.rglob("*") if f.is_file()) / 1048576


def preparar_tesseract(destino: Path, idiomas: list[str]) -> Path | None:
    """Copia o minimo necessario do Tesseract para dentro do pacote."""
    diag = ambiente.diagnostico()
    exe = diag.get("tesseract")
    if not exe or not os.path.isfile(exe):
        print("  ! Tesseract nao encontrado — o pacote sairá SEM OCR embutido.")
        return None

    origem = Path(exe).parent
    tessdata_origem = Path(diag.get("tessdata") or (origem / "tessdata"))

    remover_pasta(destino)
    (destino / "tessdata").mkdir(parents=True)

    copiados = 0
    for f in origem.iterdir():
        if not f.is_file():
            continue
        if f.name.lower() in EXES_DE_TREINO:
            continue
        if f.suffix.lower() in (".exe", ".dll"):
            shutil.copy2(f, destino / f.name)
            copiados += 1

    faltando = []
    for lang in idiomas:
        achou = False
        for base in (tessdata_origem, origem / "tessdata"):
            td = base / ("%s.traineddata" % lang)
            if td.is_file():
                shutil.copy2(td, destino / "tessdata" / td.name)
                achou = True
                break
        if not achou:
            faltando.append(lang)
    if faltando:
        print("  ! idioma(s) sem .traineddata, ignorado(s): %s" % ", ".join(faltando))

    print("  Tesseract embutido: %d binario(s) + %d idioma(s) — %.0f MB"
          % (copiados, len(idiomas) - len(faltando), _mb(destino)))
    return destino


def escrever_lancadores(destino: Path) -> None:
    """Scripts de entrada: um para a janela, outro para a linha de comando."""
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "entrada_gui.py").write_text(
        "import multiprocessing, sys\n"
        "multiprocessing.freeze_support()\n"
        "from pdf2md.gui import main\n"
        "sys.exit(main())\n", encoding="utf-8")
    (destino / "entrada_cli.py").write_text(
        "import multiprocessing, sys\n"
        "multiprocessing.freeze_support()\n"
        "from pdf2md.cli import main\n"
        "sys.exit(main())\n", encoding="utf-8")


def montar_spec(spec: Path, trabalho: Path, tess: Path | None,
                onefile: bool, icone: Path | None) -> None:
    # `repr` ja produz um literal Python valido e escapado. Prefixar com `r`
    # (raw) sobre um repr escapado DOBRA as barras invertidas do caminho — a
    # armadilha classica de gerar codigo Python com caminhos do Windows.
    datas = []
    if tess:
        datas.append((str(tess), "tesseract"))
    datas_txt = "[%s]" % ", ".join("(%r, %r)" % (a, b) for a, b in datas)
    icone_txt = repr(str(icone)) if icone else "None"
    staged_txt = repr(str(tess)) if tess else "None"

    if onefile:
        corpo = """
exe_gui = EXE(pyz_gui, a_gui.scripts, a_gui.binaries, a_gui.datas, [],
              name='pdf2md', console=False, icon=ICONE, upx=False)
exe_cli = EXE(pyz_cli, a_cli.scripts, a_cli.binaries, a_cli.datas, [],
              name='pdf2md-cli', console=True, icon=ICONE, upx=False)
"""
    else:
        corpo = """
exe_gui = EXE(pyz_gui, a_gui.scripts, [], exclude_binaries=True,
              name='pdf2md', console=False, icon=ICONE, upx=False)
exe_cli = EXE(pyz_cli, a_cli.scripts, [], exclude_binaries=True,
              name='pdf2md-cli', console=True, icon=ICONE, upx=False)
COLLECT(exe_gui, exe_cli, a_gui.binaries, a_gui.datas,
        a_cli.binaries, a_cli.datas, strip=False, upx=False, name='pdf2md')
"""

    # Cabecalho GERADO (so valores) e corpo ESTATICO, concatenados. Nada de
    # `.format()` sobre o corpo: ele contem literais de conjunto e de dict, e
    # as chaves seriam lidas como marcadores de formatacao.
    cabecalho = (
        "# -*- mode: python ; coding: utf-8 -*-\n"
        "# Gerado por pdf2md/empacotar.py — nao editar a mao.\n"
        "import os\n"
        "from PyInstaller.utils.hooks import collect_all\n\n"
        "ICONE = %s\n"
        "EXCLUIR = %r\n"
        "TESS_STAGED = %s\n"
        "DADOS_FIXOS = %s\n"
        "ENTRADA_GUI = %r\n"
        "ENTRADA_CLI = %r\n"
        "PROJETO = %r\n"
    ) % (icone_txt, EXCLUIR, staged_txt, datas_txt,
         str(trabalho / "entrada_gui.py"), str(trabalho / "entrada_cli.py"),
         str(PROJETO))

    spec.write_text(cabecalho + '''
# O pymupdf4llm tem subpacotes SEM __init__.py (helpers/, llama/) e um modelo
# .onnx em ocr/. Listar o nome do pacote nao basta: sem collect_all ele entra
# no bundle pela metade e falha a importar em silencio.
datas_x, bin_x, ocultos_x = [], [], []
for _pkg in ('pymupdf4llm', 'pymupdf', 'fitz', 'pytesseract'):
    try:
        _d, _b, _h = collect_all(_pkg)
        datas_x += _d; bin_x += _b; ocultos_x += _h
    except Exception as _e:
        print('[pdf2md] collect_all(%s) falhou: %s' % (_pkg, _e))

DADOS = DADOS_FIXOS + datas_x
OCULTOS = ['pdf2md', 'pdf2md.gui', 'pdf2md.cli', 'pdf2md.nucleo',
           'pdf2md.perfis', 'pdf2md.ambiente',
           'pymupdf4llm.helpers.pymupdf_rag',
           'pymupdf4llm.helpers.document_layout',
           'pymupdf4llm.helpers.multi_column',
           'pymupdf4llm.helpers.get_text_lines',
           'pymupdf4llm.helpers.progress',
           'pymupdf4llm.helpers.utils',
           'PIL.Image', 'PIL.ImageFilter', 'numpy'] + ocultos_x


# Bibliotecas que SO o Tesseract usa — e que por isso podem ser removidas da
# raiz do bundle, onde o PyInstaller as duplica. Sao justamente as duas
# maiores (97 MB + 30 MB).
#
# A lista e' explicita de proposito. Uma tentativa anterior removia da raiz
# TUDO que viesse da pasta do Tesseract, e isso levou junto o `zlib1.dll` —
# do qual o `tcl86t.dll` depende. Resultado: o pacote continuava convertendo
# pela linha de comando, mas a JANELA nao abria mais. DLL pequena e de nome
# generico e' compartilhada; nao presuma que so o Tesseract a usa.
SO_DO_TESSERACT = {'libtesseract-5.dll', 'libicudt75.dll'}


def sem_copia_solta(toc):
    """Remove a copia que o PyInstaller HASTEIA do Tesseract para a raiz.

    As DLLs do Tesseract entram deliberadamente como `datas`, com destino
    `tesseract/`. So que o PyInstaller reclassifica DLL que chega por `datas`
    como BINARY e a duplica na RAIZ do bundle. Mantem-se a copia de dentro de
    `tesseract/` e descarta-se a da raiz — apenas para as bibliotecas da lista
    acima.
    """
    if not TESS_STAGED:
        return toc
    alvo = os.path.normcase(os.path.abspath(TESS_STAGED))
    prefixo = 'tesseract' + os.sep
    mantidos, cortados, bytes_ = [], 0, 0
    for item in toc:
        dest, origem = str(item[0]), os.path.normcase(os.path.abspath(str(item[1])))
        nome = os.path.basename(dest).lower()
        if (origem.startswith(alvo + os.sep)
                and not os.path.normcase(dest).startswith(prefixo)
                and nome in SO_DO_TESSERACT):
            cortados += 1
            try:
                bytes_ += os.path.getsize(item[1])
            except OSError:
                pass
            continue
        mantidos.append(item)
    if cortados:
        print('[pdf2md] %d duplicata(s) do Tesseract removida(s) da raiz (%.0f MB).'
              % (cortados, bytes_ / 1048576))
    return mantidos


a_gui = Analysis([ENTRADA_GUI], pathex=[PROJETO], datas=DADOS, binaries=bin_x,
                 hiddenimports=OCULTOS, excludes=EXCLUIR, noarchive=False)
a_cli = Analysis([ENTRADA_CLI], pathex=[PROJETO], datas=DADOS, binaries=bin_x,
                 hiddenimports=OCULTOS, excludes=EXCLUIR, noarchive=False)
a_gui.binaries = sem_copia_solta(a_gui.binaries)
a_cli.binaries = sem_copia_solta(a_cli.binaries)
pyz_gui = PYZ(a_gui.pure)
pyz_cli = PYZ(a_cli.pure)
''' + corpo, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="pdf2md.empacotar",
        description="Gera o executavel standalone do pdf2md.")
    ap.add_argument("--onefile", action="store_true",
                    help="um unico .exe (parte mais devagar: descompacta a cada uso)")
    ap.add_argument("--sem-tesseract", action="store_true",
                    help="nao embute o Tesseract (pacote leve, exige instalado)")
    ap.add_argument("--idiomas", default="por,eng",
                    help="idiomas de OCR a embutir (padrao: por,eng)")
    ap.add_argument("--saida", default=str(PROJETO / "dist"),
                    help="pasta de saida (padrao: <projeto>/dist)")
    ap.add_argument("--limpar", action="store_true",
                    help="apaga build/ e dist/ antes de comecar")
    ap.add_argument("--pular-teste", action="store_true",
                    help="nao roda o autoteste no pacote gerado (nao recomendado)")
    a = ap.parse_args(argv)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller ausente. Instale com:  python -m pip install pyinstaller")
        return 1

    t0 = time.time()
    trabalho = PROJETO / "build" / "pdf2md_empacotamento"
    dist = Path(a.saida)
    if a.limpar:
        for d in (PROJETO / "build", dist):
            if d.exists() and remover_pasta(d):
                print("limpo: %s" % d)

    print("1. Preparando lancadores...")
    escrever_lancadores(trabalho)

    print("2. Preparando o Tesseract...")
    tess = None
    if a.sem_tesseract:
        print("  (pulado por --sem-tesseract; o app usara o Tesseract da maquina)")
    else:
        tess = preparar_tesseract(
            trabalho / "tesseract",
            [s.strip() for s in a.idiomas.split(",") if s.strip()])

    icone = None
    for cand in (PROJETO / "pdf2md.ico", RAIZ / "pdf2md.ico"):
        if cand.is_file():
            icone = cand
            break

    print("3. Gerando o .spec...")
    spec = trabalho / "pdf2md.spec"
    montar_spec(spec, trabalho, tess, a.onefile, icone)

    print("4. Rodando o PyInstaller (leva alguns minutos)...\n")
    cmd = [sys.executable, "-m", "PyInstaller", str(spec),
           "--noconfirm", "--distpath", str(dist),
           "--workpath", str(PROJETO / "build" / "pyinstaller")]
    proc = subprocess.run(cmd, cwd=str(PROJETO))
    if proc.returncode != 0:
        print("\nPyInstaller falhou (codigo %d)." % proc.returncode)
        return proc.returncode

    alvo = dist / "pdf2md"
    if a.onefile:
        alvo = dist
    print("\n%s" % ("=" * 62))
    print("Empacotado em %.0fs — %s" % (time.time() - t0, alvo))
    for exe in sorted(dist.rglob("pdf2md*.exe")):
        print("  %-16s %7.1f MB" % (exe.name, _mb(exe)))
    if not a.onefile and alvo.is_dir():
        print("  %-16s %7.1f MB  (pasta inteira)" % ("TOTAL", _mb(alvo)))

    print("\n5. Verificando o pacote gerado...\n")
    if a.pular_teste:
        print("  (pulado por --pular-teste)")
        return 0
    return verificar(alvo)


def verificar(pasta: Path) -> int:
    """Roda o autoteste DENTRO do executavel recem-gerado.

    Sem isto, um pacote em que a janela nao abre passa por bom: a linha de
    comando continua funcionando e o defeito so aparece no primeiro clique.
    """
    cli = pasta / "pdf2md-cli.exe"
    if not cli.is_file():
        print("  ! %s nao encontrado — nao consegui verificar." % cli.name)
        return 1

    proc = subprocess.run([str(cli), "--autoteste"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")

    def eco(linhas, marca="  "):
        # O console de quem empacota tambem pode ser cp1252: o texto vai
        # adaptado ao que ele consegue representar, em vez de estourar.
        cod = getattr(sys.stdout, "encoding", None) or "utf-8"
        for linha in linhas:
            print(marca + linha.encode(cod, "replace").decode(cod, "replace"))

    eco((proc.stdout or "").splitlines())
    if (proc.stderr or "").strip():
        eco(proc.stderr.splitlines()[:10], "  ! ")

    if proc.returncode != 0:
        print("\n  PACOTE COM DEFEITO — nao distribua ainda.")
        return proc.returncode
    print("\n  Pacote verificado. Atalho: %s" % (pasta / "pdf2md.exe"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
