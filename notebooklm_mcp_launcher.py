# Launcher do MCP notebooklm-mcp-cli (jacob-bd) sob o venv do Python 3.14 do
# python.org. E o servidor que o Claude Desktop sobe.
#
# Por que existe: o Smart App Control (SAC) esta em modo de IMPOSICAO nesta
# maquina e recusa binario sem assinatura. O Python gerenciado pelo uv e
# NotSigned — em 2026-08-03 o SAC bloqueou o proprio python313.dll e o
# _overlapped.pyd (modulo do asyncio no Windows) do interpretador-base do uv,
# desmentindo a hipotese de que ele estaria liberado por reputacao. Sem
# _overlapped nao ha ProactorEventLoop, e o servidor MCP nao sobe. O venv
# criado a partir do Python314 do python.org herda a assinatura
# CN=Python Software Foundation (Authenticode e embutido e sobrevive a copia),
# e o SAC o aceita.
#
# PEGADINHA DE IDENTIDADE: ha DOIS pacotes com entry "notebooklm-mcp" nesta
# maquina. O que o Claude Desktop usa (e este launcher reproduz) e o do
# notebooklm-mcp-cli (notebooklm_tools.mcp.server:main — API, mesma auth do
# nlm), NAO o pacote antigo notebooklm-mcp v2 (notebooklm_mcp.cli — GUI/selenium).
#
# ATENCAO: os shims .exe que o pip gera dentro do venv continuam NotSigned.
# Nunca chame o .exe — sempre este launcher ou "python.exe -m".
import os
import sys

VENV_PYTHON = r"C:\Users\alden\.notebooklm\.venv-nlm314\Scripts\python.exe"

# Se foi invocado por outro interpretador, re-executa no python do venv.
if os.path.normcase(sys.executable) != os.path.normcase(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__)] + sys.argv[1:])

from notebooklm_tools.mcp.server import main

if __name__ == "__main__":
    sys.argv = ["notebooklm-mcp"] + sys.argv[1:]
    main()
