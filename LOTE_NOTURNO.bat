@echo off
rem Lote noturno do pipeline de autos (espec fase 10). Agendar so quando o usuario decidir:
rem   schtasks /Create /SC DAILY /ST 02:00 /TN "cerebro-lote-noturno" /TR "\"%USERPROFILE%\.notebooklm\LOTE_NOTURNO.bat\""
rem Janela de 6 h; etapas longas (indexar/distilar) param ao fim da janela e continuam na proxima noite (cache).
cd /d "%USERPROFILE%\.notebooklm"
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" tools\lote_noturno.py --janela-min 360 >> relatorios\lote-stdout.log 2>&1
