# Launcher do nlm (notebooklm-mcp-cli) sob o venv do Python 3.14 do python.org.
#
# Por que existe: o Smart App Control (SAC) esta em modo de IMPOSICAO nesta
# maquina e recusa binario sem assinatura. O Python gerenciado pelo uv e
# NotSigned — em 2026-08-03 o SAC bloqueou o proprio python313.dll e o
# _overlapped.pyd (modulo do asyncio no Windows) do interpretador-base do uv,
# desmentindo a hipotese de que ele estaria liberado por reputacao. O venv
# criado a partir do Python314 do python.org COPIA o python.exe base, e a
# assinatura Authenticode e embutida — logo o venv HERDA a assinatura
# CN=Python Software Foundation e o SAC o aceita.
#
# ATENCAO: os shims .exe que o pip gera dentro do venv (nlm.exe, pip.exe)
# continuam NotSigned. Nunca chame o .exe — sempre este launcher ou
# "python.exe -m".
import os
import sys

VENV_PYTHON = r"C:\Users\alden\.notebooklm\.venv-nlm314\Scripts\python.exe"

# Se foi invocado por outro interpretador, re-executa no python do venv.
if os.path.normcase(sys.executable) != os.path.normcase(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__)] + sys.argv[1:])

from notebooklm_tools.cli.main import cli_main

if __name__ == "__main__":
    sys.argv = ["nlm"] + sys.argv[1:]
    cli_main()
