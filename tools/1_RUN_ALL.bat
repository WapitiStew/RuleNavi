@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\.."
set "ROOT=%cd%"

echo [RUN_ALL] ROOT=%ROOT%
echo.

rem --- editable install (依存が足りない場合もここで出る) ---
py -m pip install -e "%ROOT%"
if errorlevel 1 (
  echo [ERR] pip install -e failed
  pause
  exit /b 1
)

echo.
echo [RUN_ALL] rulenavi all
echo.

py -m rulenavi all
set "EC=%errorlevel%"

echo.
echo [RUN_ALL] EXIT=%EC%
pause
exit /b %EC%
