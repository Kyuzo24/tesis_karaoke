@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH="
set "PYTHONHOME="
if not exist ".youtube-env\Scripts\python.exe" (
    py -3 -m venv .youtube-env
    if errorlevel 1 exit /b 1
)
.youtube-env\Scripts\python.exe -m pip install --upgrade -r requirements-youtube.txt
if errorlevel 1 exit /b 1
echo Componente de YouTube instalado. Reinicia la aplicacion.
