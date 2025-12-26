@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."
set "ROOT=%cd%"
set "SRC=%ROOT%\src"
set "SCRIPTS=%ROOT%\scripts"

set "PYTHONPATH=%SRC%"

if "%~1"=="" (
  echo Usage:
  echo   run_script.bat step2_p05_make_site_stub.py
  echo   run_script.bat step2_p05_make_site_stub.py --quiet
  pause
  exit /b 1
)

set "FILE=%~1"
shift

set "FULL=%SCRIPTS%\%FILE%"
if not exist "%FULL%" (
  echo [ERR] not found: "%FULL%"
  pause
  exit /b 1
)

echo [RUN] %FILE%
py "%FULL%" %*
set "EC=%errorlevel%"
echo [EXIT] %EC%
pause
exit /b %EC%
