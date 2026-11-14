@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONNOUSERSITE=1"
"runtime\youtube\python.exe" -m pip install --upgrade -r requirements-youtube.txt
if errorlevel 1 (
  echo No se pudo completar la actualizacion. Revisa la conexion.
) else (
  echo Componente actualizado. Reinicia Karaoke Studio.
)
pause
