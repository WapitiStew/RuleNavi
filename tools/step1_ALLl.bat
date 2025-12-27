@echo off
setlocal
cd /d "%~dp0\.."
set "ROOT=%cd%"

py -m pip install -e "%ROOT%"
if errorlevel 1 (
  echo [ERR] pip install -e failed
  pause
  exit /b 1
)

py -m rulenavi step1
set "EC=%errorlevel%"
echo [EXIT] %EC%
pause
exit /b %EC%
