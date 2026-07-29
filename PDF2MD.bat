@echo off
REM ==========================================================================
REM  pdf2md — conversor de PDF para Markdown (processos PJe, livros,
REM  decisoes judiciais e laudos periciais com imagens).
REM
REM  Sem argumentos  -> abre a janela do aplicativo.
REM  Com argumentos  -> repassa para a linha de comando.
REM                     Ex.: PDF2MD.bat "C:\autos" -o "C:\saida" --perfil pje
REM ==========================================================================
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    start "" pythonw -m pdf2md --gui
    exit /b 0
)

python -m pdf2md %*
set CODIGO=%ERRORLEVEL%
if %CODIGO% EQU 3 (
    echo.
    echo [!] Sobraram paginas sem texto. Repita com:  --ocr sempre --dpi 400
)
endlocal & exit /b %CODIGO%
