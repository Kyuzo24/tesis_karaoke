@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\venv\Lib\site-packages"
py -3.10 desktop_live.py
